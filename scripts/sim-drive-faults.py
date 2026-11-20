#!/usr/bin/env python3
"""Exercise the drive_commit.py CLI with disposable, synthetic files only."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from threading import Barrier

CLI = Path(__file__).with_name("drive_commit.py").resolve()


def verify(condition, detail):
    if not condition:
        raise AssertionError(detail)


def publish(stage, target, expected, *, replace=False, error=None):
    command = [sys.executable, CLI, stage, target, hashlib.sha256(expected).hexdigest()]
    if replace:
        command.append("--replace")
    result = subprocess.run(command, text=True, capture_output=True, timeout=30,
                            env={**os.environ, "LC_ALL": "C"})
    if error:
        verify(result.returncode != 0 and error in result.stderr, str(result))
        return None
    verify(result.returncode == 0, str(result))
    published = Path(result.stdout.rstrip("\n"))
    verify(published.parent == target.parent, f"Unexpected publication path: {published}")
    verify(published.read_bytes() == expected, f"Publication mismatch: {published}")
    return published


def stages_with_timestamps(directory):
    # Same-sized distinct revisions with equal mtimes; one identical-content
    # duplicate at a different timestamp. All three must be decided by bytes.
    revisions = [b"A" * 65536, b"B" * 65536, b"A" * 65536]
    stages = []
    for i, payload in enumerate(revisions):
        path = directory / f"stage-{i}"
        path.write_bytes(payload)
        stamp = 1700000000 + (i == 2)
        os.utime(path, (stamp, stamp))
        stages.append(path)
    return stages, revisions


def simulate(root):
    uploads, published = root / "uploads", root / "drive"
    uploads.mkdir()
    published.mkdir()
    files, payloads = stages_with_timestamps(uploads)
    target = published / "archive.zip"
    numbered = published / "archive (2).zip"
    participants = [0, 2, 1, 0, 1, 2]
    gate = Barrier(len(participants))

    def compete(i):
        gate.wait(timeout=15)
        return publish(files[i], target, payloads[i])

    with ThreadPoolExecutor(max_workers=len(participants)) as pool:
        results = list(pool.map(compete, participants))
    verify(set(results) == {target, numbered}, "Expected canonical and one numbered path")
    verify(set(published.iterdir()) == set(results), "Leaked or duplicated publication")
    for i, actual in zip(participants, results):
        verify(actual.read_bytes() == payloads[i], "Concurrent publication lost content")
        verify(publish(files[i], target, payloads[i]) == actual, "Retry changed result")
        verify(files[i].read_bytes() == payloads[i], "Publication changed staged input")
    print("PASS six concurrent CLI uploads, distinct mtimes, equal-size revisions, idempotent retries")

    before = {path: path.read_bytes() for path in published.iterdir()}
    other = b"C" * len(payloads[0])
    pending = uploads / "replacement"
    for broken in (other[:-10], b"D" * len(other)):
        pending.write_bytes(broken)
        publish(pending, target, other, replace=True, error="SHA-256 mismatch")
        verify({p: p.read_bytes() for p in published.iterdir()} == before,
               "Corrupt or truncated replacement changed the destination directory")
        verify(pending.read_bytes() == broken, "Failed verification changed staging")
    pending.write_bytes(other)
    for _ in range(2):
        verify(publish(pending, target, other, replace=True) == target, "Unexpected replacement")
    verify(numbered.read_bytes() == before[numbered], "Replacement changed numbered copy")
    verify(set(published.iterdir()) == set(before), "Retry left extra files")
    print("PASS corrupt and truncated replacements, verified retry and canonical-only replacement")


def simulate_full(source_root, volume):
    # Do not fill a shared filesystem. The caller supplies a dedicated, small mount.
    verify(volume.is_mount() and not any(volume.iterdir()), "Expected an empty dedicated mount")
    stats = os.statvfs(volume)
    verify(0 < stats.f_blocks * stats.f_frsize <= 8 * 1024 * 1024,
           "Expected a private mount of at most 8 MiB")
    with tempfile.TemporaryDirectory(dir=volume) as drive:
        target = Path(drive) / "archive.zip"
        original = b"previously committed bytes"
        target.write_bytes(original)
        incoming = b"X" * (stats.f_blocks * stats.f_frsize + 65536)
        stage = source_root / "large"
        stage.write_bytes(incoming)
        publish(stage, target, incoming, replace=True, error="[Errno 28]")
        verify(target.read_bytes() == original, "ENOSPC damaged original")
        verify(set(Path(drive).iterdir()) == {target}, "ENOSPC leaked publication files")
        verify(stage.read_bytes() == incoming, "ENOSPC damaged staging")
        small = b"verified smaller replacement"
        stage.write_bytes(small)
        publish(stage, target, small, replace=True)
    print("PASS real ENOSPC on private volume, original preservation, staging cleanup and retry")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full-volume", type=Path, help="empty private mount of at most 8 MiB")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="pocket-nas-faults-") as directory:
        root = Path(directory)
        simulate(root)
        if args.full_volume:
            simulate_full(root, args.full_volume.resolve())
        else:
            print("SKIP real ENOSPC (no --full-volume supplied)")
