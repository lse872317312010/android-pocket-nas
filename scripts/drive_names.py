"""Numbered destination names shared by publication and receipt validation."""

import hashlib
import os
import re


def numbered_name(requested, number):
    marker = f" ({number})"
    suffix = requested.suffix
    name = requested.stem + marker + suffix
    if len(os.fsencode(name)) <= 255:
        return name

    # Bind the short name to the entire requested basename, including its suffix.
    digest = hashlib.sha256(os.fsencode(requested.name)).hexdigest()
    compact = "copy-" + digest + marker
    if len(os.fsencode(compact + suffix)) <= 255:
        return compact + suffix
    return compact


def copy_number(requested, candidate):
    if len(os.fsencode(candidate)) > 255:
        return None
    # A pathlib suffix can itself contain a marker. Verify each possible split.
    for match in re.finditer(r" \(([1-9][0-9]*)\)", candidate):
        number = int(match[1])
        if numbered_name(requested, number) == candidate:
            return number
    return None
