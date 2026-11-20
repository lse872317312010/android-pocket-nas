#!/usr/bin/env python3
"""Exercise a temporary rclone SFTP client and loopback OpenSSH home node."""
import pwd
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import sys
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
        deadline = time.monotonic() + 5
        while any((root / "incoming").iterdir()) and time.monotonic() < deadline:
            time.sleep(0.05)
        if any((root / "incoming").iterdir()) or len(list(published.iterdir())) != 2:
            raise RuntimeError("unexpected staging or published files after receipt")
        print("PASS: one-command SFTP upload, receipts, retry, collision and cleanup")
    finally:
        worker.terminate()
        worker.wait(timeout=5)


def check_existing_number_one(server, client, config):
    root = server / "preexisting-drive"
    scripts = Path(__file__).resolve().parent
    worker = [sys.executable, scripts / "drive_inbox.py", root]
    subprocess.run([*worker, "--once"], check=True)
    source = client / "归档[1].tar.gz"
    source.write_bytes(b"existing content")
    canonical = root / "files" / source.name
    canonical.write_bytes(b"original")
    existing = canonical.with_name(f"{canonical.stem} (1){canonical.suffix}")
    existing.write_bytes(source.read_bytes())
    daemon = subprocess.Popen([*worker, "--interval", "0.1"])
    try:
        result = subprocess.run([sys.executable, scripts / "drive_upload.py", source,
                                 f"home:{root}", "--config", config, "--timeout", "20"],
                                capture_output=True, text=True, timeout=30)
        if result.returncode or result.stdout.strip() != existing.name:
            raise RuntimeError(f"existing (1) receipt failed: {result}")
    finally:
        daemon.terminate()
        daemon.wait(timeout=5)

    # Replay the submitted request after the worker wrote its receipt.
    receipt, = (root / "receipts").glob("*.json")
    job = root / "incoming" / receipt.stem
    job.mkdir(exist_ok=True)
    (job / "payload").write_bytes(source.read_bytes())
    (job / "request.json").write_text(json.dumps({
        "name": source.name, "sha256": hashlib.sha256(source.read_bytes()).hexdigest()
    }))
    prior = receipt.read_bytes()
    subprocess.run([*worker, "--once"], check=True)
    if job.exists() or receipt.read_bytes() != prior:
        raise RuntimeError("worker failed to reconcile the existing (1) receipt")
    if (set(canonical.parent.iterdir()) != {canonical, existing} or
            canonical.read_bytes() != b"original" or existing.read_bytes() != source.read_bytes()):
        raise RuntimeError("reusing (1) changed published files")
    print("PASS: existing (1) over SFTP and restart with a persisted receipt")


def check_long_collision(server, client, config):
    scripts = Path(__file__).resolve().parent
    root = server / "long-drive"
    worker = [sys.executable, scripts / "drive_inbox.py", root]
    subprocess.run([*worker, "--once"], check=True)
    source = client / ("档" * 83 + "ab.zip")
    assert len(source.name.encode("utf-8")) == 255
    source.write_bytes(b"revision")
    published = root / "files"
    original = published / source.name
    original.write_bytes(b"original")
    daemon = subprocess.Popen([*worker, "--interval", "0.1"])
    try:
        names = []
        for _ in range(2):
            result = subprocess.run([sys.executable, scripts / "drive_upload.py", source,
                                     f"home:{root}", "--config", config, "--timeout", "20"],
                                    capture_output=True, text=True, timeout=30, check=True)
            names.append(result.stdout.rstrip("\n"))
    finally:
        daemon.terminate()
        daemon.wait(timeout=5)
    chosen = published / names[0]
    assert names[0] == names[1] and chosen != original and chosen.suffix == ".zip"
    assert original.read_bytes() == b"original" and chosen.read_bytes() == source.read_bytes()
    assert set(published.iterdir()) == {original, chosen}
    receipts = list((root / "receipts").iterdir())
    assert len(receipts) == 2
    receipt = receipts[0]
    prior = receipt.read_bytes()
    job = root / "incoming" / receipt.stem
    job.mkdir(exist_ok=True)
    (job / "request.json").write_text(json.dumps({
        "name": source.name, "sha256": hashlib.sha256(source.read_bytes()).hexdigest()
    }))
    subprocess.run([*worker, "--once"], check=True)
    assert not job.exists() and prior == receipt.read_bytes()
    print("PASS: 255-byte UTF-8 collision, SFTP retry and worker receipt replay")


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
            check_drive(server, client, rclone)
            check_interrupted_upload(server, client, rclone, command)
            check_receipts(server, client, rclone_conf, rclone)
            check_existing_number_one(server, client, rclone_conf)
            check_long_collision(server, client, rclone_conf)
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
