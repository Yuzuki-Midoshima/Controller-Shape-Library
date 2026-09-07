"""Additional CV presets converted from the user's legacy MOX library."""

from __future__ import annotations

import json
from pathlib import Path


PRESET_MAP = {
    "circle_smooth": ("mox_circle_2", "Circle Smooth", "Basic"),
    "circle_linear": ("mox_circle_l", "Circle Linear", "Basic"),
    "half_triangular": ("mox_half_triangular", "Half Triangular", "Solid"),
    "triangular_3d": ("mox_triangular", "Triangular 3D", "Solid"),
    "half_spear": ("mox_half_spear", "Half Spear", "Solid"),
    "spear": ("mox_spear", "Spear", "Solid"),
    "hexagon_3d": ("mox_hexagon2", "Hexagon 3D", "Solid"),
    "diamond_3d": ("mox_dia", "Diamond 3D", "Solid"),
    "diamond_3d_alt": ("mox_dia2", "Diamond 3D Alt", "Solid"),
    "arrows_on_ball": ("mox_arrows_on_ball", "Arrows On Ball", "Solid"),
    "cog": ("mox_cog", "Cog", "Basic"),
    "sun": ("mox_sun", "Sun", "Basic"),
    "pin": ("mox_pin", "Pin", "Basic"),
    "double_pin": ("mox_2_pin", "Double Pin", "Basic"),
    "four_pin": ("mox_4_pin", "Four Pin", "Basic"),
    "dumbbell": ("mox_dumbell", "Dumbbell", "Basic"),
    "single_arrow_line": ("mox_single_line", "Single Line", "Arrow"),
    "single_arrow_fat": ("mox_single_fat", "Single Fat", "Arrow"),
    "double_arrow_line": ("mox_double_line", "Double Line", "Arrow"),
    "double_arrow_fat": ("mox_double_fat", "Double Fat", "Arrow"),
    "four_arrow_line": ("mox_four_line", "Four Line", "Arrow"),
    "four_arrow_fat": ("mox_four_fat", "Four Fat", "Arrow"),
    "eight_arrow": ("mox_eight", "Eight Arrow", "Arrow"),
    "rotation_90_line": ("mox_rot90_line", "Rotation 90 Line", "Arrow"),
    "rotation_90_fat": ("mox_rot90_fat", "Rotation 90 Fat", "Arrow"),
    "rotation_180_line": ("mox_rot180_line", "Rotation 180 Line", "Arrow"),
    "rotation_180_fat": ("mox_rot180_fat", "Rotation 180 Fat", "Arrow"),
}


def _load_shapes():
    path = Path(__file__).with_name("mox_shapes.json")
    with path.open("r", encoding="utf-8") as stream:
        source = json.load(stream)["shapes"]
    result = {}
    for shape_id, (source_id, label, category) in PRESET_MAP.items():
        record = source[source_id]
        components = record.get("components") or [record]
        result[shape_id] = {
            "label": label,
            "category": category,
            "source": source_id,
            "curves": [
                {"degree": int(component.get("degree", 1)),
                 "points": component["points"]}
                for component in components
            ],
        }
    return result


SHAPES = _load_shapes()
