"""New rotation controller presets."""

import math

from .generators import arc, arrow_head


def _rotation(label, start, end):
    end_angle = math.radians(end)
    tip = (.9 * math.cos(end_angle), 0, .9 * math.sin(end_angle))
    tangent_back = (math.sin(end_angle), 0, -math.cos(end_angle))
    return {"label": label, "category": "Arrow",
            "curves": [arc(.9, start, end, 32),
                       arrow_head(tip, tangent_back, .16, .28)]}


def _xyz():
    curves = []
    for plane in ("XY", "YZ", "XZ"):
        segment = arc(.9, 20, 315, 28, plane)
        curves.append(segment)
        tip = segment["points"][-1]
        previous = segment["points"][-2]
        back = tuple(previous[axis] - tip[axis] for axis in range(3))
        length = math.sqrt(sum(value * value for value in back)) or 1.0
        back = tuple(value / length for value in back)
        normal = {"XY": (-back[1], back[0], 0),
                  "YZ": (0, -back[2], back[1]),
                  "XZ": (-back[2], 0, back[0])}[plane]
        base = tuple(tip[axis] + back[axis] * .22 for axis in range(3))
        curves.append({"degree": 1, "points": [
            tuple(base[axis] + normal[axis] * .12 for axis in range(3)),
            tip,
            tuple(base[axis] - normal[axis] * .12 for axis in range(3)),
        ]})
    return curves


SHAPES = {
    "rotate_360": _rotation("Rotate 360", 10, 335),
    "rotate_cw": _rotation("Rotate CW", 20, 320),
    "rotate_ccw": _rotation("Rotate CCW", 340, 40),
    "rotate_xyz": {"label": "Rotate XYZ", "category": "Arrow",
                   "curves": _xyz()},
}
