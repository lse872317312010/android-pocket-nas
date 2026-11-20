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
import zipfile


def make_key(path):
    subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", path],
                   check=True)


def check_drive(server, client, rclone):
    """Exercise user-visible file operations with the same SFTP configuration."""
    def create_archive(path, contents):
        # Fixed ZIP metadata lets the collision case hold size and mtime constant.
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr(zipfile.ZipInfo("sample.txt"), contents)

    def verify(actual, expected, label):
        if actual != expected:
            raise RuntimeError(f"{label}: byte comparison failed")
        print(f"PASS: {label}")

    apk = server / "example.apk"
    create_archive(apk, b"synthetic transfer fixture, not an installable application")
    rclone("copyto", f"home:{apk}", "downloaded.apk")
    verify((client / "downloaded.apk").read_bytes(), apk.read_bytes(), "APK fixture download")

    source = client / "upload.zip"
    destination = f"home:{server}/archive.zip"
    create_archive(source, b"revision A")
    first = source.read_bytes()
    rclone("copyto", source, destination)
    verify(rclone("cat", destination), first, "ZIP upload")
    rclone("copyto", source, destination)
    verify(rclone("cat", destination), first, "repeat copy of identical ZIP")

    # SFTP exposes second-resolution modification times. A distinct ZIP with
    # matching size and timestamp can compare equal under rclone defaults.
    stamp = int((server / "archive.zip").stat().st_mtime)
    create_archive(source, b"revision B")
    os.utime(source, (stamp, stamp))
    if source.read_bytes() == first or source.stat().st_size != len(first):
        raise RuntimeError("invalid same-size collision fixture")
    rclone("copyto", source, destination)
    verify(rclone("cat", destination), first, "default copy skips same-size/same-mtime collision")

    create_archive(source, b"revision C with a larger payload")
    replacement = source.read_bytes()
    rclone("copyto", "--ignore-existing", source, destination)
    verify(rclone("cat", destination), first, "ignore-existing preserves changed-size collision")

    # Model a truncated staging object. Promote only verified bytes. This
    # exercises the failed verification path, not an actual network outage.
    stage = f"home:{server}/archive.zip.pending"
    incomplete = client / "incomplete.zip"
    incomplete.write_bytes(replacement[:-11])
    rclone("copyto", incomplete, stage)
    if rclone("cat", stage) == replacement:
        raise RuntimeError("incomplete staging file passed verification")
    rclone("deletefile", stage)
    verify(rclone("cat", destination), first, "failed staging verification preserves original")
    if "archive.zip.pending" in rclone("lsf", f"home:{server}").decode().splitlines():
        raise RuntimeError("failed staging object survived cleanup")

    rclone("copyto", source, destination)
    verify(rclone("cat", destination), replacement, "default copy replaces changed-size ZIP")


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
            check_drive(server, client, rclone)
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
