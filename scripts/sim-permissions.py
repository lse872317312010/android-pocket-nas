"""Exercise the split SFTP exports with a single trusted writer and synthetic files."""

from contextlib import ExitStack
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time


SCRIPTS = Path(__file__).resolve().parent


def start(stack, command):
    process = subprocess.Popen(command, stdin=subprocess.DEVNULL)

    def stop():
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

    stack.callback(stop)
    return process


def serve(stack, share, host_key, client_key, config, *, readonly):
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    args = ["rclone", "--config", config, "serve", "sftp", share,
            "--addr", f"127.0.0.1:{port}", "--key", host_key,
            "--authorized-keys", client_key.with_suffix(".pub"),
            "--dir-cache-time", "0s"]
    if readonly:
        args.append("--read-only")
    process = start(stack, args)
    for _ in range(100):
        if process.poll() is not None:
            raise RuntimeError("SFTP export failed to start")
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                return port
        except OSError:
            time.sleep(0.05)
    raise TimeoutError("SFTP export did not become ready")


def simulate(temp):
    root = temp / "drive"
    worker = [sys.executable, SCRIPTS / "drive_inbox.py", root]
    subprocess.run([*worker, "--once"], check=True)
    host_key, client_key = temp / "host", temp / "client"
    for key in (host_key, client_key):
        subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", key], check=True)

    config = temp / "client.conf"
    server_config = temp / "server.conf"
    server_config.write_text("[public]\ntype = combine\n"
                             f'upstreams = "files=:local:{root}/files" '
                             f'"receipts=:local:{root}/receipts"\n')
    known = temp / "known_hosts"
    host_public = " ".join(host_key.with_suffix(".pub").read_text().split()[:2])
    with ExitStack() as stack:
        for alias, share, readonly in [("stage", root / "incoming", False),
                                       ("view", "public:", True)]:
            port = serve(stack, share, host_key, client_key, server_config, readonly=readonly)
            with known.open("a") as f:
                f.write(f"[127.0.0.1]:{port} {host_public}\n")
            with config.open("a") as f:
                f.write(f"[{alias}]\ntype = sftp\nhost = 127.0.0.1\nport = {port}\n"
                        f"user = client\nkey_file = {client_key}\nknown_hosts_file = {known}\n"
                        "disable_hashcheck = true\nshell_type = none\n")
        with config.open("a") as f:
            f.write("[drive]\ntype = combine\n"
                    "upstreams = incoming=stage: files=view:files receipts=view:receipts\n")

        cli = ["rclone", "--config", config, "--retries", "1", "--low-level-retries", "1"]

        def remote(*args, check=True):
            return subprocess.run([*cli, *args], capture_output=True, timeout=15, check=check)

        start(stack, [*worker, "--interval", "0.1"])
        source = temp / "sample.bin"
        source.write_bytes(b"published bytes")
        upload = subprocess.run([sys.executable, SCRIPTS / "drive_upload.py", source, "drive:",
                                 "--config", config, "--timeout", "30"],
                                check=True, capture_output=True, text=True, timeout=35)
        assert upload.stdout.strip() == source.name
        receipt, = (root / "receipts").glob("*.json")
        original = receipt.read_bytes()
        assert json.loads(original)["name"] == source.name
        assert remote("cat", f"drive:files/{source.name}").stdout == source.read_bytes()
        assert remote("cat", f"drive:receipts/{receipt.name}").stdout == original
        assert set(remote("lsf", "view:").stdout.splitlines()) == {b"files/", b"receipts/"}

        # Address the server directly as well, independent of the client's combine config.
        probe = temp / "probe"
        probe.write_bytes(b"distinct test data")
        for directory, filename in [("files", source.name), ("receipts", receipt.name)]:
            target = f"view:{directory}/{filename}"
            for args in [("copyto", "--ignore-times", probe, target),
                         ("deletefile", target), ("moveto", target, f"view:{directory}/moved"),
                         ("copyto", probe, f"view:{directory}/new")]:
                result = remote(*args, check=False)
                if result.returncode == 0:
                    raise AssertionError(f"Public export accepted {args}")
            assert set(remote("lsf", f"view:{directory}").stdout.splitlines()) == {filename.encode()}
        remote("copyto", probe, "stage:probe")
        assert (root / "incoming/probe").read_bytes() == probe.read_bytes()
        remote("deletefile", "stage:probe")
        assert remote("cat", f"view:files/{source.name}").stdout == source.read_bytes()
        assert remote("cat", f"view:receipts/{receipt.name}").stdout == original
        print("PASS: inbox upload, published reads, and server-enforced read-only files and receipts")


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="pocket-nas-permissions-") as temp:
        simulate(Path(temp))
