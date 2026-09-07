"""Special-purpose controller presets."""

import math

from .generators import circle, curve


def _smooth_closed(points, iterations=2, ratio=.20):
    """Round a closed polyline without changing its overall silhouette."""
    result = list(points[:-1] if points[0] == points[-1] else points)
    for _ in range(iterations):
        rounded = []
        for index, point in enumerate(result):
            following = result[(index + 1) % len(result)]
            rounded.append(tuple(
                point[axis] * (1.0 - ratio) + following[axis] * ratio
                for axis in range(3)))
            rounded.append(tuple(
                point[axis] * ratio + following[axis] * (1.0 - ratio)
                for axis in range(3)))
        result = rounded
    return result + [result[0]]


def _eye():
    top = [(-1 + 2*i/12, 0, .48*math.sin(math.pi*i/12)) for i in range(13)]
    bottom = [(1 - 2*i/12, 0, -.48*math.sin(math.pi*i/12)) for i in range(13)]
    return [curve(top + bottom + [top[0]]), circle(.24, 20)]


SHAPES = {
    "eye": {"label": "Eye", "category": "Basic", "curves": _eye()},
    "foot": {"label": "Foot", "category": "Basic", "curves": [curve([
        (-.34,0,-1),(.34,0,-1),(.5,0,-.55),(.62,0,.25),(.48,0,.9),
        (0,0,1.15),(-.48,0,.9),(-.62,0,.25),(-.5,0,-.55),(-.34,0,-1)])]},
    "hand": {"label": "Hand", "category": "Basic", "curves": [curve([
        # Wrist and outside of the thumb.
        (-.38,0,-1.02),(-.62,0,-.88),(-.86,0,-.62),(-1.12,0,-.38),
        (-1.34,0,-.25),(-1.48,0,-.08),(-1.45,0,.08),(-1.32,0,.16),
        (-1.12,0,.12),(-.88,0,-.02),(-.65,0,-.16),(-.48,0,-.12),
        (-.42,0,.02),(-.44,0,.35),(-.55,0,.72),(-.68,0,1.08),
        (-.69,0,1.30),(-.60,0,1.43),(-.47,0,1.42),(-.37,0,1.27),
        (-.25,0,.91),(-.12,0,.52),(-.04,0,.38),
        # Index finger.
        (-.08,0,.76),(-.13,0,1.30),(-.12,0,1.70),(-.04,0,1.86),
        (.08,0,1.88),(.18,0,1.75),(.22,0,1.34),(.25,0,.80),
        # Middle finger.
        (.29,0,.65),(.31,0,1.22),(.34,0,1.68),(.42,0,1.86),
        (.54,0,1.87),(.63,0,1.70),(.63,0,1.22),(.61,0,.72),
        # Ring finger.
        (.66,0,.60),(.70,0,1.08),(.75,0,1.57),(.84,0,1.76),
        (.96,0,1.75),(1.02,0,1.58),(.98,0,1.08),(.93,0,.48),
        # Little finger and outer palm.
        (.98,0,.35),(1.04,0,.78),(1.13,0,1.34),(1.24,0,1.58),
        (1.35,0,1.57),(1.39,0,1.40),(1.33,0,.86),(1.29,0,.06),
        (1.32,0,-.32),(1.24,0,-.67),(1.04,0,-.92),(.72,0,-1.05),
        (.32,0,-1.10),(-.08,0,-1.08),(-.38,0,-1.02),
    ])]},
}

# A slightly narrower, taller silhouette reads more clearly at icon size.
SHAPES["hand"]["curves"][0]["points"] = _smooth_closed([
    (x * .80, y, z * 1.08)
    for x, y, z in SHAPES["hand"]["curves"][0]["points"]
])
