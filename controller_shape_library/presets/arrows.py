"""Arrow controller CV presets."""

from __future__ import annotations

import math


def _shape(points, label):
    return {"label": label, "category": "Arrow",
            "curves": [{"degree": 1, "points": points}]}


def _rotation(arc_degrees, start_degrees=15):
    """Return one closed outline for a curved rotation arrow."""
    count = max(8, int(arc_degrees / 10))
    angles = [math.radians(start_degrees + arc_degrees * i / count)
              for i in range(count + 1)]
    outer_radius = 1.06
    inner_radius = .88
    center_radius = (outer_radius + inner_radius) * .5
    points = [(math.cos(a) * outer_radius, 0, math.sin(a) * outer_radius)
              for a in angles]

    end_angle = angles[-1]
    radial = (math.cos(end_angle), math.sin(end_angle))
    tangent = (-math.sin(end_angle), math.cos(end_angle))
    center = (radial[0] * center_radius, radial[1] * center_radius)
    wing_outer = (center[0] + radial[0] * .31 - tangent[0] * .14,
                  center[1] + radial[1] * .31 - tangent[1] * .14)
    tip = (center[0] + tangent[0] * .40, center[1] + tangent[1] * .40)
    wing_inner = (center[0] - radial[0] * .31 - tangent[0] * .14,
                  center[1] - radial[1] * .31 - tangent[1] * .14)
    points.extend([(wing_outer[0], 0, wing_outer[1]),
                   (tip[0], 0, tip[1]),
                   (wing_inner[0], 0, wing_inner[1])])
    points.extend((math.cos(a) * inner_radius, 0, math.sin(a) * inner_radius)
                  for a in reversed(angles))
    points.append(points[0])
    return points


def _circle_four_arrow():
    """Four arrows connected to a circle, with clean gaps at each stem."""
    curves = []
    for center in (45, 135, 225, 315):
        start = math.radians(center - 36)
        end = math.radians(center + 36)
        points = [
            (math.cos(start + (end - start) * i / 8), 0.0,
             math.sin(start + (end - start) * i / 8))
            for i in range(9)
        ]
        curves.append({"degree": 1, "points": points})

    arrows = (
        [(-.12,0,.99),(-.12,0,1.48),(-.36,0,1.48),(0,0,1.88),
         (.36,0,1.48),(.12,0,1.48),(.12,0,.99)],
        [(.99,0,.12),(1.48,0,.12),(1.48,0,.36),(1.88,0,0),
         (1.48,0,-.36),(1.48,0,-.12),(.99,0,-.12)],
        [(.12,0,-.99),(.12,0,-1.48),(.36,0,-1.48),(0,0,-1.88),
         (-.36,0,-1.48),(-.12,0,-1.48),(-.12,0,-.99)],
        [(-.99,0,-.12),(-1.48,0,-.12),(-1.48,0,-.36),(-1.88,0,0),
         (-1.48,0,.36),(-1.48,0,.12),(-.99,0,.12)],
    )
    curves.extend({"degree": 1, "points": points} for points in arrows)
    return {"label": "Circle Four Arrow", "category": "Arrow", "curves": curves}


# Exact CV values used by FK-Builder's mox_rot90 / mox_rot180 presets.
FK_ROTATION_90 = [
    (-1.0,0.0,0.0),(-1.0,0.0,0.0),(-.87617,0.0,0.0),
    (-.833322,0.0,.250229),(-.705841,0.0,.487587),
    (-.505639,0.0,.685338),(-.330804,0.0,.784899),
    (-.237568,0.0,.823871),(-.296069,0.0,.542222),(0.0,0.0,1.0),
    (-.583238,0.0,1.0),(-.294309,0.0,.910589),
    (-.397384,0.0,.867509),(-.589755,0.0,.75828),
    (-.812182,0.0,.538365),(-.952203,0.0,.279747),(-1.0,0.0,0.0),
]

FK_ROTATION_180 = [
    (0.0,0.0,-1.0),(-.307891,0.0,-.558828),(-.236291,0.0,-.828651),
    (-.325683,0.0,-.79092),(-.48885,0.0,-.6979),
    (-.698405,0.0,-.494718),(-.829207,0.0,-.254562),
    (-.872375,0.0,0.0),(-.829207,0.0,.254562),
    (-.702717,0.0,.490416),(-.5026,0.0,.690017),
    (-.3303,0.0,.788798),(-.236291,0.0,.828651),
    (-.307891,0.0,.558828),(-.00561428,0.0,.999873),
    (-.628521,0.0,.964327),(-.292809,0.0,.915872),
    (-.393368,0.0,.873432),(-.587089,0.0,.762679),
    (-.808356,0.0,.542017),(-.948108,0.0,.28137),(-.995857,0.0,0.0),
    (-.948108,0.0,-.28137),(-.808356,0.0,-.542017),
    (-.58759,0.0,-.76218),(-.395477,0.0,-.872542),
    (-.292809,0.0,-.915872),(-.628521,0.0,-.964327),(0.0,0.0,-1.0),
]


SHAPES = {
    "single_arrow": _shape([(0,0,-1),(.75,0,0),(.3,0,0),(.3,0,1),
                              (-.3,0,1),(-.3,0,0),(-.75,0,0),(0,0,-1)],
                             "Single Arrow"),
    "double_arrow": _shape([(0,0,-1),(.65,0,-.3),(.25,0,-.3),(.25,0,.3),
                              (.65,0,.3),(0,0,1),(-.65,0,.3),(-.25,0,.3),
                              (-.25,0,-.3),(-.65,0,-.3),(0,0,-1)], "Double Arrow"),
    "four_arrow": _shape([(0,0,-1),(.28,0,-.65),(.12,0,-.65),(.12,0,-.12),
                            (.65,0,-.12),(.65,0,-.28),(1,0,0),(.65,0,.28),
                            (.65,0,.12),(.12,0,.12),(.12,0,.65),(.28,0,.65),
                            (0,0,1),(-.28,0,.65),(-.12,0,.65),(-.12,0,.12),
                            (-.65,0,.12),(-.65,0,.28),(-1,0,0),(-.65,0,-.28),
                            (-.65,0,-.12),(-.12,0,-.12),(-.12,0,-.65),
                            (-.28,0,-.65),(0,0,-1)], "Four Arrow"),
    "circle_four_arrow": _circle_four_arrow(),
    "rotation_90": _shape(FK_ROTATION_90, "Rotation 90"),
    "rotation_180": _shape(FK_ROTATION_180, "Rotation 180"),
}
