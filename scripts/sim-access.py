#!/usr/bin/env python3
"""Exercise a temporary rclone SFTP client and loopback OpenSSH home node."""
import pwd
import hashlib
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import time


def make_key(path):
    subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", path],
                   check=True)


def simulate(root):
    server = root / "home-node"
    client = root / "primary-phone"
    server.mkdir()
    client.mkdir()
    host_key = root / "host-key"
    key = client / "identity"
    make_key(host_key)
    make_key(key)
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]

    user = pwd.getpwuid(os.getuid()).pw_name
    config = root / "sshd.conf"
    config.write_text(f"""ListenAddress 127.0.0.1
Port {port}
HostKey "{host_key}"
PidFile "{root}/sshd.pid"
AuthorizedKeysFile "{key}.pub"
AllowUsers {user}
AuthenticationMethods publickey
PasswordAuthentication no
KbdInteractiveAuthentication no
DisableForwarding yes
PermitTTY no
Subsystem sftp internal-sftp
ForceCommand internal-sftp
""")
    host_public = host_key.with_suffix(".pub").read_text().split()
    known_hosts = client / "known_hosts"
    known_hosts.write_text(f"[127.0.0.1]:{port} {host_public[0]} {host_public[1]}\n")
    rclone_conf = client / "rclone.conf"
    rclone_conf.write_text(f"""[home]
type = sftp
host = 127.0.0.1
port = {port}
user = {user}
key_file = {key}
known_hosts_file = {known_hosts}
shell_type = none
disable_hashcheck = true
""")

    def rclone(*args):
        return subprocess.run(["rclone", "--config", rclone_conf, "--retries", "1",
                               "--low-level-retries", "1", *args],
                              cwd=client, check=True, stdout=subprocess.PIPE,
                              timeout=30).stdout

    # All fixtures are synthetic. The rclone client reads selected slices.
    payload = os.urandom(4 * 1024 * 1024 + 173)
    name = "video-sample.bin"
    (server / name).write_bytes(payload)
    sshd = shutil.which("sshd") or "/usr/sbin/sshd"
    with (root / "server.log").open("w+") as log:
        daemon = subprocess.Popen([sshd, "-D", "-e", "-f", config], stderr=log)
        try:
            for _ in range(100):
                if daemon.poll() is not None:
                    raise RuntimeError("sshd exited during startup")
                try:
                    with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                        break
                except OSError:
                    time.sleep(0.05)
            else:
                raise RuntimeError("sshd did not become reachable")
            if name not in rclone("lsf", f"home:{server}").decode().splitlines():
                raise RuntimeError("server fixture missing from client listing")
            for start, count in [(0, 4096), (3_100_007, 8192), (65_531, 4096),
                                 (len(payload) - 173, 4096)]:
                actual = rclone("cat", "--offset", str(start), "--count", str(count),
                                f"home:{server}/{name}")
                if actual != payload[start:start + count]:
                    raise RuntimeError(f"range mismatch at byte {start}")
                print(f"offset={start} bytes={len(actual)} sha256={hashlib.sha256(actual).hexdigest()}")
            print("PASS: pinned host key, authenticated SFTP listing and four byte ranges")
        except Exception:
            log.flush()
            log.seek(0)
            print(log.read())
            raise
        finally:
            if daemon.poll() is None:
                daemon.terminate()
                try:
                    daemon.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    daemon.kill()
                    daemon.wait()


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix=".pocket-nas-access-", dir=Path.home()) as temp:
        simulate(Path(temp))
