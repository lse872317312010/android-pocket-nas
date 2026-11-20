#!/usr/bin/env python3
"""Stage one file with rclone and wait for the home publisher's verified receipt."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import uuid

from drive_names import copy_number


def remaining(deadline):
    seconds = deadline - time.monotonic()
    if seconds <= 0:
        raise TimeoutError("Upload confirmation timed out")
    return seconds


def upload(source, remote_root, config, timeout, check_attempt=None):
    if not source.is_file() or source.is_symlink():
        raise ValueError("Source must be a regular file")
    if not remote_root:
        raise ValueError("Specify an rclone remote root")
    if check_attempt is not None and not re.fullmatch(r"[0-9a-f]{32}", check_attempt):
        raise ValueError("Expected a 32-character lowercase hex upload attempt ID")
    name = source.name
    if "\\" in name or any(ord(c) < 32 or ord(c) == 127 for c in name):
        raise ValueError("Choose a filename without control characters or backslashes")
    source = source.absolute()
    deadline = time.monotonic() + timeout
    digest = hashlib.sha256()
    with source.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            remaining(deadline)
            digest.update(chunk)
    expected = digest.hexdigest()

    base = remote_root if remote_root.endswith((":", "/")) else remote_root + "/"
    attempt = check_attempt or uuid.uuid4().hex
    directory = f"{base}incoming/{attempt}"
    receipt = f"{base}receipts/{attempt}.json"
    print(f"Upload attempt: {attempt}", file=sys.stderr, flush=True)
    command = ["rclone", "--retries", "1", "--low-level-retries", "1"]
    if config is not None:
        command += ["--config", str(config)]

    def rclone(action, *args, missing_ok=False):
        result = subprocess.run([*command, action, *args], capture_output=True,
                                timeout=remaining(deadline), stdin=subprocess.DEVNULL)
        if missing_ok and result.returncode in (3, 4):
            return None
        if result.returncode:
            detail = result.stderr.decode(errors="replace").strip()
            raise RuntimeError(f"rclone {action} exited {result.returncode}: {detail}")
        return result.stdout

    if check_attempt is None:
        # Only the owner of a fresh attempt can know submission has not begun.
        try:
            rclone("copyto", "--", str(source), directory + "/payload")
            with tempfile.TemporaryDirectory(prefix="pocket-nas-request-") as temp:
                request = Path(temp) / "request.json"
                request.write_text(json.dumps({"name": name, "sha256": expected}), encoding="utf-8")
                rclone("copyto", "--", str(request), directory + "/request.tmp")
        except (OSError, RuntimeError, subprocess.TimeoutExpired, KeyboardInterrupt):
            # The transfer subprocess has exited. Use a short, separate deadline
            # because the original timeout may have triggered this cleanup.
            try:
                result = subprocess.run([*command, "purge", "--", directory],
                                        capture_output=True, timeout=5, stdin=subprocess.DEVNULL)
                if result.returncode not in (0, 3, 4):
                    print(f"Staging cleanup unconfirmed for {attempt} (rclone {result.returncode})",
                          file=sys.stderr)
            except (OSError, subprocess.TimeoutExpired) as error:
                print(f"Staging cleanup unconfirmed for {attempt}: {error}", file=sys.stderr)
            raise

        # Even a failed rename reply can mean request.json is already live.
        rclone("moveto", "--", directory + "/request.tmp", directory + "/request.json")

    while True:
        raw = rclone("cat", "--head", "8193", "--", receipt, missing_ok=True)
        if raw is not None:
            if len(raw) > 8192:
                raise ValueError("Oversized receipt")
            answer = json.loads(raw)
            if not isinstance(answer, dict):
                raise ValueError("Malformed receipt")
            if "error" in answer:
                raise RuntimeError(f"Publisher rejected upload: {answer['error']!r}")
            chosen = answer.get("name")
            if answer.get("sha256") != expected or not isinstance(chosen, str):
                raise ValueError("Receipt digest or filename does not match upload")
            if chosen != name and copy_number(source, chosen) is None:
                raise ValueError("Unexpected destination filename in receipt")
            return chosen
        time.sleep(min(0.5, remaining(deadline)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, metavar="SOURCE")
    parser.add_argument("remote_root", metavar="REMOTE_ROOT",
                        help="rclone root with incoming/ and receipts/, e.g. home:drive")
    parser.add_argument("--config", type=Path, help="private rclone configuration")
    parser.add_argument("--timeout", type=float, default=300, metavar="SECONDS",
                        help="total time allowed for hashing, transfer, and receipt (default: 300)")
    parser.add_argument("--check-attempt", metavar="ID",
                        help="only wait for an existing receipt and verify it against SOURCE")
    args = parser.parse_args()
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("--timeout must be finite and positive")
    try:
        print(upload(args.source, args.remote_root, args.config, args.timeout, args.check_attempt))
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
