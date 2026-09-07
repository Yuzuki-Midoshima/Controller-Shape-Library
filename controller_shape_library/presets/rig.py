"""Rig-purpose controller presets built from simple curve generators."""

from .generators import arrow_head, circle, curve, gear, polygon


SHAPES = {
    "pole_vector": {"label": "Pole Vector", "category": "Basic", "curves": [
        polygon(4, .28, offset_degrees=0), curve([(.28, 0, 0), (.82, 0, 0)]),
        arrow_head((1, 0, 0), direction=(-1, 0, 0), width=.18, length=.28)]},
    "root": {"label": "Root", "category": "Basic", "curves": [
        polygon(4, 1.0, offset_degrees=0),
        curve([(-1.25, 0, 0), (1.25, 0, 0)]),
        curve([(0, 0, -1.25), (0, 0, 1.25)])]},
    "ik": {"label": "IK", "category": "Basic", "curves": [
        curve([(-1,0,-.75),(1,0,-.75),(1,0,.75),(-1,0,.75),(-1,0,-.75)]),
        curve([(0,0,-.35),(0,0,.35)]), curve([(-.18,0,.35),(.18,0,.35)]),
        curve([(-.18,0,-.35),(.18,0,-.35)])]},
    "fk": {"label": "FK", "category": "Basic", "curves": [
        circle(.9), curve([(.9,0,0),(1.25,0,0)]),
        arrow_head((1.35,0,0), direction=(-1,0,0), width=.13, length=.25)]},
    "settings": {"label": "Settings", "category": "Basic",
                 "curves": [gear(), circle(.35, 20)]},
    "world": {"label": "World", "category": "Basic", "curves": [
        circle(1.0), curve([(-1.35,0,0),(1.35,0,0)]),
        curve([(0,0,-1.35),(0,0,1.35)])]},
}
