"""Check worker restarts at staging, publication, and receipt boundaries."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

WORKER = Path(__file__).with_name("drive_inbox.py")


def scan(root):
    return subprocess.run([sys.executable, WORKER, root, "--once"], check=False)


def simulate(root):
    assert scan(root).returncode == 0
    name = "game.zip"
    data = b"new contents"
    digest = hashlib.sha256(data).hexdigest()
    original = root / "files" / name
    original.write_bytes(b"original")
    expected = root / "files" / "game (2).zip"
    job = root / "incoming" / ("a" * 32)
    receipt = root / "receipts" / (job.name + ".json")
    job.mkdir()
    (job / "payload").write_bytes(data)
    record = json.dumps({"name": name, "sha256": digest})
    (job / "request.tmp").write_text(record)
    assert scan(root).returncode == 0 and not receipt.exists() and not expected.exists()
    (job / "request.tmp").rename(job / "request.json")

    # Reconstruct the durable state after publication but before receipt creation.
    expected.write_bytes(data)
    assert scan(root).returncode == 0
    assert json.loads(receipt.read_bytes()) == {"name": expected.name, "sha256": digest}
    assert not job.exists()
    # Reconstruct receipt written, staging cleanup pending.
    job.mkdir()
    (job / "payload").write_bytes(data)
    (job / "request.json").write_text(record)
    assert scan(root).returncode == 0 and not job.exists()
    assert set(original.parent.iterdir()) == {original, expected}

    bad = root / "incoming" / ("b" * 32)
    bad.mkdir()
    (bad / "payload").write_bytes(b"truncated")
    (bad / "request.json").write_text(record)
    scan(root)
    error = root / "receipts" / (bad.name + ".json")
    assert json.loads(error.read_bytes()).get("error")
    assert original.read_bytes() == b"original" and expected.read_bytes() == data
    assert set(original.parent.iterdir()) == {original, expected}
    print("PASS: readiness marker, publication replay, cleanup replay, rejection receipt")


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as temp:
        simulate(Path(temp))
