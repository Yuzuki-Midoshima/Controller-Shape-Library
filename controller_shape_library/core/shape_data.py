"""Shape registry and JSON-ready schema validation."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from ..presets import SHAPES


class ShapeDataError(ValueError):
    pass


def validate_shape(name, data):
    if not isinstance(data, dict) or not isinstance(data.get("curves"), list):
        raise ShapeDataError("Shape {!r} must contain a curves list".format(name))
    if not data["curves"]:
        raise ShapeDataError("Shape {!r} has no curves".format(name))
    for curve in data["curves"]:
        degree = curve.get("degree", 1)
        points = curve.get("points", [])
        if degree not in (1, 2, 3) or len(points) < degree + 1:
            raise ShapeDataError("Invalid curve in shape {!r}".format(name))
        if any(len(point) != 3 for point in points):
            raise ShapeDataError("Every CV must be an xyz triplet")
    return True


def shape_names(category=None):
    return [name for name, data in SHAPES.items()
            if category is None or data.get("category") == category]


def get_shape(name):
    key = str(name).strip().lower().replace(" ", "_")
    if key not in SHAPES:
        raise ShapeDataError("Unknown controller shape: {!r}".format(name))
    validate_shape(key, SHAPES[key])
    return copy.deepcopy(SHAPES[key])


def load_json(path):
    """Load one shape or a ``{name: shape}`` mapping without mutating built-ins."""
    with Path(path).open("r", encoding="utf-8") as stream:
        payload = json.load(stream)
    records = payload.get("shapes", payload)
    if "curves" in records:
        records = {Path(path).stem: records}
    for name, data in records.items():
        validate_shape(name, data)
    return copy.deepcopy(records)


def save_json(path, shapes):
    for name, data in shapes.items():
        validate_shape(name, data)
    with Path(path).open("w", encoding="utf-8") as stream:
        json.dump({"version": 1, "shapes": shapes}, stream, indent=2)
