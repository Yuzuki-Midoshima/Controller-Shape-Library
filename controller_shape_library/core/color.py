"""Drawing override colors for curve shapes."""

from __future__ import annotations

from maya import cmds

from .shape_utils import curve_shapes, require_editable


def set_color(node, color):
    require_editable(node)
    shapes = curve_shapes(node)
    if isinstance(color, int):
        if not 0 <= color <= 31:
            raise ValueError("Maya index color must be between 0 and 31")
        for shape in shapes:
            cmds.setAttr(shape + ".overrideEnabled", True)
            cmds.setAttr(shape + ".overrideRGBColors", False)
            cmds.setAttr(shape + ".overrideColor", color)
    else:
        rgb = tuple(color)
        if len(rgb) != 3:
            raise ValueError("RGB color requires three values")
        for shape in shapes:
            cmds.setAttr(shape + ".overrideEnabled", True)
            cmds.setAttr(shape + ".overrideRGBColors", True)
            cmds.setAttr(shape + ".overrideColorRGB", *rgb)
    return node
