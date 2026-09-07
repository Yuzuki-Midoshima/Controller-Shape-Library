"""Panel-style controller presets."""


def _curve(points):
    return {"degree": 1, "points": points}


SHAPES = {
    "panel_horizontal": {
        "label": "Horizontal Panel", "category": "Panel", "curves": [
            _curve([(-1, 0, -.35), (1, 0, -.35), (1, 0, .35),
                    (-1, 0, .35), (-1, 0, -.35)]),
            _curve([(-.7, 0, 0), (.7, 0, 0)]),
        ],
    },
    "panel_vertical": {
        "label": "Vertical Panel", "category": "Panel", "curves": [
            _curve([(-.35, 0, -1), (.35, 0, -1), (.35, 0, 1),
                    (-.35, 0, 1), (-.35, 0, -1)]),
            _curve([(0, 0, -.7), (0, 0, .7)]),
        ],
    },
    "panel_square": {
        "label": "Square Panel", "category": "Panel", "curves": [
            _curve([(-1, 0, -1), (1, 0, -1), (1, 0, 1),
                    (-1, 0, 1), (-1, 0, -1)]),
            _curve([(-.65, 0, 0), (.65, 0, 0)]),
            _curve([(0, 0, -.65), (0, 0, .65)]),
        ],
    },
}
