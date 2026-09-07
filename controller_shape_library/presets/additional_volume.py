"""New volume controller presets."""

import math

from .generators import circle, curve


def _hemisphere():
    curves = [circle(1.0, 32, "XZ")]
    for plane in ("XY", "YZ"):
        points = []
        for index in range(17):
            angle = math.pi * index / 16
            if plane == "XY":
                points.append((math.cos(angle), math.sin(angle), 0))
            else:
                points.append((0, math.sin(angle), math.cos(angle)))
        curves.append(curve(points))
    return curves


def _capsule():
    points = []
    for index in range(9):
        angle = math.pi * index / 8
        points.append((.5 * math.cos(angle), 0, .6 + .5 * math.sin(angle)))
    for index in range(9):
        angle = math.pi + math.pi * index / 8
        points.append((.5 * math.cos(angle), 0, -.6 + .5 * math.sin(angle)))
    points.append(points[0])
    return [curve(points)]


SHAPES = {
    "hemisphere": {"label": "Hemisphere", "category": "Solid",
                   "curves": _hemisphere()},
    "pyramid": {"label": "Pyramid", "category": "Solid", "curves": [curve([
        (-.8,-.6,-.8),(.8,-.6,-.8),(.8,-.6,.8),(-.8,-.6,.8),
        (-.8,-.6,-.8),(0,1,0),(.8,-.6,-.8),(0,1,0),(.8,-.6,.8),
        (0,1,0),(-.8,-.6,.8),(0,1,0)])]},
    "capsule": {"label": "Capsule", "category": "Solid",
                "curves": _capsule()},
}
