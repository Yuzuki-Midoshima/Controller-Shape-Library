"""Namespace-safe controller naming helpers."""

from __future__ import annotations

import re


def sanitized(name):
    if not name:
        return "controller_CTRL"
    parts = str(name).split(":")
    parts = [re.sub(r"[^A-Za-z0-9_]", "_", part) or "node" for part in parts]
    return ":".join(parts)


def unique(name):
    """Return ``name``, ``name1``, ``name2`` ... using the first free name."""
    from maya import cmds

    base = sanitized(name)
    if not cmds.objExists(base):
        return base
    index = 1
    while cmds.objExists("{}{}".format(base, index)):
        index += 1
    return "{}{}".format(base, index)


def derived(node, affix, position="suffix"):
    """Build a related name while preserving a user-supplied separator.

    ``_ZERO`` and ``-ZERO`` can be appended verbatim, while ``ZERO_`` and
    ``ZERO-`` can be prepended verbatim. Bare values retain the historical
    underscore separator.
    """
    leaf = node.rsplit("|", 1)[-1]
    namespace, separator, short = leaf.rpartition(":")
    base = short if separator else leaf
    if base.endswith("_CTRL"):
        base = base[:-5]
    affix = str(affix).strip()
    if not affix:
        raise ValueError("Name part must not be empty")
    if position == "prefix":
        result = affix + base if affix.endswith(("_", "-")) else affix + "_" + base
    elif position == "suffix":
        result = base + affix if affix.startswith(("_", "-")) else base + "_" + affix
    else:
        raise ValueError("position must be 'prefix' or 'suffix'")
    return "{}: {}".format(namespace, result).replace(": ", ":") if separator else result
