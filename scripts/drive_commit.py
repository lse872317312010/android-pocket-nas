#!/usr/bin/env python3
"""Publish a verified upload on a trusted local Linux/POSIX filesystem.

运行账户须独占管理目标目录，所有提交进程都必须遵守同一把目录锁。
All publishers must use this directory lock. Use trusted paths and a filesystem
supporting directory flock, hard links, atomic rename and directory fsync.
Keep uploads in a separate private staging area. The staged source is retained.
The expected digest must come from the intended original file. Budget temporary
space for one complete destination-side copy per concurrent invocation, including
duplicates. A killed process may leave a private .drive-commit-* file.
The canonical name is copy 1; the first distinct collision is numbered (2).
"""

import argparse
import fcntl
import hashlib
import os
from pathlib import Path
import re
import sys
import tempfile

from drive_names import copy_number, numbered_name


def copy_digest(source, output=None):
    digest = hashlib.sha256()
    for chunk in iter(lambda: source.read(1024 * 1024), b""):
        digest.update(chunk)
        if output is not None:
            output.write(chunk)
    return digest.hexdigest()


def existing_digest(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"destination candidate is not a regular file: {path}")
    with path.open("rb") as source:
        return copy_digest(source)


def select_destination(destination, expected, replace):
    # Check previous numbered copies too, so retrying the upload is idempotent.
    if os.path.lexists(destination):
        if existing_digest(destination) == expected:
            return destination, False
        if replace:
            return destination, True

    numbered = {}
    for path in destination.parent.iterdir():
        number = copy_number(destination, path.name)
        if number is not None:
            numbered[number] = path
    if not replace:
        for number in sorted(numbered):
            if existing_digest(numbered[number]) == expected:
                return numbered[number], False
    if not os.path.lexists(destination):
        return destination, True
    number = 2
    while number in numbered:
        number += 1
    return destination.with_name(numbered_name(destination, number)), True


def publish(staged, destination, expected, replace=False):
    expected = expected.lower()
    if not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise ValueError("expected SHA-256 must be 64 hexadecimal characters")
    if staged.is_symlink() or not staged.is_file():
        raise ValueError("staged upload must be a regular file")
    if os.path.abspath(staged) == os.path.abspath(destination):
        raise ValueError("use separate staging and destination paths")
    parent = destination.parent
    temp_name = None
    try:
        # Verify the exact bytes in our private, same-filesystem publish copy.
        with tempfile.NamedTemporaryFile(dir=parent, prefix=".drive-commit-",
                                         delete=False) as temp:
            temp_name = temp.name
            with staged.open("rb") as source:
                actual = copy_digest(source, temp)
            if actual != expected:
                raise ValueError(f"SHA-256 mismatch: obtained {actual}")
            temp.flush()
            os.fsync(temp.fileno())

        directory = os.open(parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            fcntl.flock(directory, fcntl.LOCK_EX)
            target, publish_copy = select_destination(destination, expected, replace)
            if publish_copy:
                if replace:
                    os.replace(temp_name, target)
                    temp_name = None
                else:
                    # No overwrite even if an uncooperative writer just created it.
                    os.link(temp_name, target)
                os.fsync(directory)
            return target
        finally:
            os.close(directory)
    finally:
        if temp_name is not None:
            os.unlink(temp_name)


def main():
    parser = argparse.ArgumentParser(description="Verify and publish a staged upload")
    parser.add_argument("staged", type=Path, metavar="STAGED")
    parser.add_argument("destination", type=Path, metavar="DESTINATION")
    parser.add_argument("sha256", metavar="SHA256")
    parser.add_argument("--replace", action="store_true", help="replace destination after verification")
    args = parser.parse_args()
    try:
        path = publish(args.staged, args.destination, args.sha256, args.replace)
    except (ValueError, OSError) as error:
        print(error, file=sys.stderr)
        return 1
    print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
