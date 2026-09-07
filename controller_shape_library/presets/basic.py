"""Basic and solid CV presets. Coordinates lie around the origin."""

from __future__ import annotations

import math


def _closed(points, degree=1):
    points = [tuple(map(float, point)) for point in points]
    return {"curves": [{"degree": degree, "points": points + points[:1]}]}


def _circle(segments):
    return _closed(
        [(math.cos(i * math.tau / segments), 0.0, math.sin(i * math.tau / segments))
         for i in range(segments)]
    )


def _polygon(sides, offset=math.pi / 2.0):
    return _closed(
        [(math.cos(offset + i * math.tau / sides), 0.0,
          math.sin(offset + i * math.tau / sides)) for i in range(sides)]
    )


def _multi(*curves):
    return {"curves": [{"degree": 1, "points": list(points)} for points in curves]}


SHAPES = {
    "circle": {**_circle(32), "label": "Circle", "category": "Basic"},
    "circle_low": {**_circle(8), "label": "Circle Low", "category": "Basic"},
    "triangle": {**_polygon(3), "label": "Triangle", "category": "Basic"},
    "square": {**_closed([(-1, 0, -1), (-1, 0, 1), (1, 0, 1), (1, 0, -1)]),
               "label": "Square", "category": "Basic"},
    "cross": {**_closed([(-1, 0, -.25), (-.25, 0, -.25), (-.25, 0, -1),
                           (.25, 0, -1), (.25, 0, -.25), (1, 0, -.25),
                           (1, 0, .25), (.25, 0, .25), (.25, 0, 1),
                           (-.25, 0, 1), (-.25, 0, .25), (-1, 0, .25)]),
              "label": "Cross", "category": "Basic"},
    "fat_cross": {**_closed([(-1, 0, -.5), (-.5, 0, -.5), (-.5, 0, -1),
                               (.5, 0, -1), (.5, 0, -.5), (1, 0, -.5),
                               (1, 0, .5), (.5, 0, .5), (.5, 0, 1),
                               (-.5, 0, 1), (-.5, 0, .5), (-1, 0, .5)]),
                  "label": "Fat Cross", "category": "Basic"},
    "pentagon": {**_polygon(5), "label": "Pentagon", "category": "Basic"},
    "hexagon": {**_polygon(6), "label": "Hexagon", "category": "Basic"},
    "diamond": {**_closed([(0, 0, 1), (1, 0, 0), (0, 0, -1), (-1, 0, 0)]),
                "label": "Diamond", "category": "Basic"},
    "cube": {**_multi(
        [(-1,-1,-1),(-1,-1,1),(-1,1,1),(-1,1,-1),(-1,-1,-1),
         (1,-1,-1),(1,-1,1),(1,1,1),(1,1,-1),(1,-1,-1)],
        [(-1,-1,1),(1,-1,1)], [(-1,1,1),(1,1,1)], [(-1,1,-1),(1,1,-1)]),
             "label": "Cube", "category": "Solid"},
    "sphere": {**_multi(
        [(math.cos(i*math.tau/32), math.sin(i*math.tau/32), 0) for i in range(33)],
        [(math.cos(i*math.tau/32), 0, math.sin(i*math.tau/32)) for i in range(33)],
        [(0, math.cos(i*math.tau/32), math.sin(i*math.tau/32)) for i in range(33)]),
               "label": "Sphere", "category": "Solid"},
    "cone": {**_multi(
        [(math.cos(i*math.tau/16), -.75, math.sin(i*math.tau/16)) for i in range(17)],
        [(0,1.25,0), (1,-.75,0)], [(0,1.25,0),(-1,-.75,0)],
        [(0,1.25,0),(0,-.75,1)], [(0,1.25,0),(0,-.75,-1)]),
             "label": "Cone", "category": "Solid"},
    "aim": {**_multi(
        [(-1,0,0),(1,0,0)], [(0,-1,0),(0,1,0)], [(0,0,-1),(0,0,1)],
        [(1,0,0),(.65,.18,0),(.65,-.18,0),(1,0,0)]),
            "label": "Aim", "category": "Solid"},
}
