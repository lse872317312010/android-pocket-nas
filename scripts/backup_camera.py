"""Capture settled camera files to a dedicated local POSIX backup directory."""
import argparse
from datetime import datetime, timezone
import fcntl
import os
from pathlib import Path
import subprocess
import tempfile


def capture(source, vault):
    source = source.resolve(strict=True)
    vault = vault.resolve(strict=True)
    if not source.is_dir() or not vault.is_dir():
        raise ValueError("Select two existing directories")
    if source == vault or source in vault.parents or vault in source.parents:
        raise ValueError("Camera and backup directories must be disjoint")
    current = vault / "current"
    history = vault / "history"
    fd = os.open(vault, os.O_RDONLY | os.O_DIRECTORY)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        for folder in (current, history):
            if folder.is_symlink():
                raise ValueError(f"Backup directory is a symbolic link: {folder}")
            folder.mkdir(exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-")
        previous = Path(tempfile.mkdtemp(prefix=stamp, dir=history))
        subprocess.run(["rclone", "copy", "--checksum", "--retries", "1",
                        "--backup-dir", previous, "--exclude", "/.stfolder/**",
                        "--exclude", "/.stignore", "--exclude", "/.stversions/**",
                        "--exclude", ".syncthing.*.tmp", "--", source, current], check=True)
        if any(previous.iterdir()):
            print(previous)
        else:
            previous.rmdir()
    finally:
        os.close(fd)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("camera", type=Path)
    parser.add_argument("vault", type=Path)
    args = parser.parse_args()
    try:
        capture(args.camera, args.vault)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"{error}\n")
