"""CV-only controller shape transforms."""

from __future__ import annotations

from maya import cmds

from .shape_utils import curve_shapes, require_editable


def _components(node):
    require_editable(node)
    shapes = curve_shapes(node)
    if not shapes:
        raise ValueError("Node has no curve shapes: {}".format(node))
    return [shape + ".cv[*]" for shape in shapes]


def scale(node, value, relative=True):
    values = (value, value, value) if isinstance(value, (int, float)) else tuple(value)
    if len(values) != 3:
        raise ValueError("scale requires a number or xyz sequence")
    cmds.scale(*values, _components(node), relative=relative, objectSpace=True)
    return node


def rotate(node, value, relative=True):
    values = tuple(value)
    if len(values) != 3:
        raise ValueError("rotate requires xyz degrees")
    cmds.rotate(*values, _components(node), relative=relative, objectSpace=True,
                forceOrderXYZ=True)
    return node


def move(node, value, relative=True):
    values = tuple(value)
    if len(values) != 3:
        raise ValueError("move requires xyz values")
    cmds.move(*values, _components(node), relative=relative, objectSpace=True)
    return node
