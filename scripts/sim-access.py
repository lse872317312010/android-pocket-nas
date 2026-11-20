#!/usr/bin/env python3
"""Exercise a temporary rclone SFTP client and loopback OpenSSH home node."""
import re
import pwd
import hashlib
import os
from pathlib import Path
import shutil
import socket
import sys
import subprocess
import tempfile
import time
import zipfile
from unittest.mock import patch

from drive_upload import upload


def make_key(path):
    subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", path],
                   check=True)


def check_aborted_attempts(server, client, config):
    root = server / "abort-drive"
    worker = [sys.executable, Path(__file__).with_name("drive_inbox.py"), root, "--once"]
    subprocess.run(worker, check=True)
    incoming = root / "incoming"
    active = incoming / ("a" * 32)
    active.mkdir()
    (active / "payload").write_bytes(b"another transfer")
    source = client / "interrupted.bin"
    source.write_bytes(b"synthetic upload")
    run = subprocess.run

    # Perform each SFTP operation, then lose its acknowledgement on the client.
    for action, filename in [("copyto", "payload"), ("copyto", "request.tmp"),
                             ("moveto", "request.json")]:
        def lose_reply(command, **kwargs):
            result = run(command, **kwargs)
            if action in command and command[-1].endswith("/" + filename):
                assert result.returncode == 0, result.stderr
                raise subprocess.TimeoutExpired(command, 20)
            return result

        with patch("drive_upload.subprocess.run", side_effect=lose_reply):
            try:
                upload(source, f"home:{root}", config, 20)
            except subprocess.TimeoutExpired:
                pass
            else:
                raise AssertionError("fault injection did not interrupt the client")
        assert (active / "payload").read_bytes() == b"another transfer"
        if action == "copyto":
            assert set(incoming.iterdir()) == {active}, "aborted staging remains"
        else:
            job, = set(incoming.iterdir()) - {active}
            assert (job / "request.json").is_file()
            run(worker, check=True)
            assert (root / "receipts" / (job.name + ".json")).is_file()
            assert (root / "files" / source.name).read_bytes() == source.read_bytes()
    # A disconnected client may lose both the copy reply and its cleanup path.
    def disconnected(command, **kwargs):
        if "purge" in command:
            raise OSError("simulated connection loss during cleanup")
        result = run(command, **kwargs)
        if "copyto" in command:
            assert result.returncode == 0
            raise subprocess.TimeoutExpired(command, 20)
        return result

    with patch("drive_upload.subprocess.run", side_effect=disconnected):
        try:
            upload(source, f"home:{root}", config, 20)
        except subprocess.TimeoutExpired:
            pass
        else:
            raise AssertionError("cleanup masked the original transfer failure")
    leftover, = set(incoming.iterdir()) - {active}
    assert (leftover / "payload").is_file() and not (leftover / "request.json").exists()
    assert (active / "payload").read_bytes() == b"another transfer"
    print("PASS: pre-submit cleanup, independent active attempt and lost submission reply")


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


def check_interrupted_upload(server, client, rclone, command):
    target = server / "payload"
    target.write_bytes(b"previous version")
    source = client / "payload"
    source.write_bytes(os.urandom(2 * 1024 * 1024))
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    staging = server / "incoming"
    staging.mkdir()
    partial = staging / "transfer-1"
    remote = f"home:{partial}"
    # Terminate the actual uploading process after observing bytes on the server.
    with subprocess.Popen([*command, "copyto", "--bwlimit", "256k", source, remote],
                          cwd=client) as uploader:
        try:
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                if any(0 < f.stat().st_size < source.stat().st_size for f in staging.iterdir()):
                    break
                if uploader.poll() is not None:
                    raise RuntimeError("upload finished before interruption")
                time.sleep(0.025)
            else:
                raise RuntimeError("no partial SFTP write observed")
        finally:
            uploader.kill()
            uploader.wait()
    if target.read_bytes() != b"previous version":
        raise RuntimeError("interrupted upload modified the published object")
    # Retry into a fresh private staging name; validate before publication.
    retry = staging / "transfer-2"
    rclone("copyto", source, f"home:{retry}")
    subprocess.run([sys.executable, Path(__file__).with_name("drive_commit.py"),
                    retry, target, digest, "--replace"], check=True)
    if rclone("cat", f"home:{target}") != source.read_bytes():
        raise RuntimeError("download after verified replacement differs")
    print("PASS: interrupted SFTP upload preserved original; verified retry published")


def check_receipts(server, client, config, rclone):
    scripts = Path(__file__).resolve().parent
    root = server / "drive"
    source = client / "游戏 包.zip"
    published = root / "files"
    worker = subprocess.Popen([sys.executable, scripts / "drive_inbox.py", root,
                               "--interval", "0.1"])
    try:
        for data, expected in [(b"first", source.name), (b"first", source.name),
                               (b"other", "游戏 包 (2).zip")]:
            source.write_bytes(data)
            result = subprocess.run([sys.executable, scripts / "drive_upload.py",
                                     source, f"home:{root}", "--config", config,
                                     "--timeout", "20"], capture_output=True, text=True,
                                    timeout=35)
            if result.returncode or result.stdout.strip() != expected:
                raise RuntimeError(f"unexpected upload result: {result}")
            if rclone("cat", f"home:{published}/{expected}") != data:
                raise RuntimeError("receipt does not match downloaded bytes")
        attempt = re.search(r"^Upload attempt: ([0-9a-f]{32})$", result.stderr, re.MULTILINE)[1]
        receipts = set((root / "receipts").iterdir())
        check = [sys.executable, scripts / "drive_upload.py", source, f"home:{root}",
                 "--config", config, "--timeout", "10", "--check-attempt", attempt]
        # Discard the previous stdout, as if the client lost the acknowledgement.
        replay = subprocess.run(check, capture_output=True, text=True, timeout=15)
        if replay.returncode or replay.stdout.strip() != expected:
            raise RuntimeError(f"unable to reconcile collision receipt: {replay}")
        source.write_bytes(b"changed after upload")
        mismatch = subprocess.run(check, capture_output=True, text=True, timeout=15)
        if mismatch.returncode == 0 or "does not match upload" not in mismatch.stderr:
            raise RuntimeError(f"unexpected changed-source result: {mismatch}")
        if set((root / "receipts").iterdir()) != receipts:
            raise RuntimeError("receipt lookup created a new attempt")
        missing = [*check[:-1], "0" * 32]
        missing[missing.index("--timeout") + 1] = "1"
        pending = subprocess.run(missing, capture_output=True, text=True, timeout=5)
        if pending.returncode == 0 or "timed out" not in pending.stderr.lower():
            raise RuntimeError(f"missing receipt was not reported as unconfirmed: {pending}")
        print("PASS: original receipt lookup, changed-source rejection and missing-receipt timeout")
        deadline = time.monotonic() + 5
        while any((root / "incoming").iterdir()) and time.monotonic() < deadline:
            time.sleep(0.05)
        if any((root / "incoming").iterdir()) or len(list(published.iterdir())) != 2:
            raise RuntimeError("unexpected staging or published files after receipt")
        print("PASS: one-command SFTP upload, receipts, retry, collision and cleanup")
    finally:
        worker.terminate()
        worker.wait(timeout=5)


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

    command = ["rclone", "--config", rclone_conf, "--retries", "1", "--low-level-retries", "1"]

    def rclone(*args):
        return subprocess.run([*command, *args],
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
            check_aborted_attempts(server, client, rclone_conf)
            check_drive(server, client, rclone)
            check_interrupted_upload(server, client, rclone, command)
            check_receipts(server, client, rclone_conf, rclone)
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
