"""Numbered destination names shared by publication and receipt validation."""

import re


def numbered_pattern(requested):
    return re.escape(requested.stem) + r" \(([1-9][0-9]*)\)" + re.escape(requested.suffix)
