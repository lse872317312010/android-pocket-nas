#!/usr/bin/env python3
"""Publish completed SFTP uploads for cooperating clients on a trusted local filesystem.

Clients own unique request IDs and stop writing after renaming request.json into
place. Only the worker may write files/ and receipts/. Keep completed receipts.
"""

import argparse
from contextlib import contextmanager
import fcntl
import json
import math
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
import time

from drive_commit import publish
from drive_names import copy_number


@contextmanager
def directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        yield fd
    finally:
        os.close(fd)


def validate_record(record):
    if not isinstance(record, dict) or set(record) != {"name", "sha256"}:
        raise ValueError("record must contain exactly name and sha256")
    name = record["name"]
    if (not isinstance(name, str) or not name or name in (".", "..") or
            "/" in name or "\\" in name or name.startswith(".drive-commit-") or
            any(ord(char) < 32 or ord(char) == 127 for char in name)):
        raise ValueError("invalid destination filename")
    # Let platform encoding and path length errors surface before copying a payload.
    if len(os.fsencode(name)) > 255:
        raise ValueError("destination filename too long")
    digest = record["sha256"]
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
        raise ValueError("invalid SHA-256")
    return name, digest.lower()


def read_json(path):
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError("record must be a regular file")
        content = stream.read(8193)
    if len(content) > 8192:
        raise ValueError("record exceeds 8 KiB")
    return json.loads(content.decode("utf-8"))


def write_receipt(path, record):
    # Write under a private temporary name, sync bytes, then expose a complete JSON.
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".receipt-", mode="w",
                                     encoding="utf-8", delete=False) as temp:
        temp_path = Path(temp.name)
        try:
            json.dump(record, temp, ensure_ascii=False)
            temp.write("\n")
            temp.flush()
            os.fsync(temp.fileno())
            os.link(temp_path, path)
        finally:
            temp_path.unlink()
    with directory(path.parent) as fd:
        os.fsync(fd)


def process_job(root, job):
    receipt = root / "receipts" / (job.name + ".json")
    request = job / "request.json"
    payload = job / "payload"
    if os.path.lexists(receipt):
        record = read_json(receipt)
        if isinstance(record, dict) and set(record) == {"error"} and isinstance(record["error"], str):
            raise ValueError(record["error"])
        actual_name, digest = validate_record(record)
        if os.path.lexists(request):
            requested, expected = validate_record(read_json(request))
            if digest != expected or (requested != actual_name and
                                      copy_number(Path(requested), actual_name) is None):
                raise ValueError("request ID already has a different receipt")
        elif os.path.lexists(payload):
            # Could be a client uploading; requests become actionable only on rename.
            return
    elif os.path.lexists(request):
        try:
            name, digest = validate_record(read_json(request))
            target = publish(payload, root / "files" / name, digest)
        except (ValueError, RecursionError) as error:
            write_receipt(receipt, {"error": str(error)})
            raise
        # A retry may reuse an object linked immediately before a previous crash.
        with directory(target.parent) as files_fd:
            os.fsync(files_fd)
        write_receipt(receipt, {"name": target.name, "sha256": digest})
    else:
        return

    # Always establish receipt durability before removing either staging object.
    with directory(receipt.parent) as receipts_fd:
        os.fsync(receipts_fd)
    payload.unlink(missing_ok=True)
    request.unlink(missing_ok=True)
    job.rmdir()
    with directory(job.parent) as incoming_fd:
        os.fsync(incoming_fd)


def scan(root):
    incoming = root / "incoming"
    ok = True
    # Shared directory inode is a stable lock across job cleanup and worker restarts.
    with directory(incoming) as fd:
        fcntl.flock(fd, fcntl.LOCK_EX)
        for job in sorted(incoming.iterdir()):
            if not re.fullmatch(r"[0-9a-f]{32}", job.name):
                continue
            try:
                if job.is_symlink() or not job.is_dir():
                    raise ValueError("job must be a real directory")
                process_job(root, job)
            except (OSError, ValueError, RecursionError) as error:
                print(f"{job.name}: {error}", file=sys.stderr, flush=True)
                ok = False
    return ok


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, metavar="ROOT")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval", type=float, default=2, metavar="SECONDS")
    args = parser.parse_args()
    if not math.isfinite(args.interval) or args.interval <= 0:
        parser.error("interval must be a positive, finite number")
    root = args.root
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    with directory(root) as root_fd:
        for name in ("incoming", "files", "receipts"):
            path = root / name
            path.mkdir(mode=0o700, exist_ok=True)
            with directory(path):
                pass
        os.fsync(root_fd)
    while True:
        ok = scan(root)
        if args.once:
            return 0 if ok else 1
        time.sleep(args.interval)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except OSError as error:
        sys.exit(str(error))
    except KeyboardInterrupt:
        sys.exit(0)
