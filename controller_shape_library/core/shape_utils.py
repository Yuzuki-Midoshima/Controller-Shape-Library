"""Curve-shape queries and safe transfer operations."""

from __future__ import annotations

import json

from maya import cmds

CLIPBOARD_OPTION = "controllerShapeToolkitClipboard"


def curve_shapes(node, full_path=True):
    """Return non-intermediate NURBS curve shapes below *node*."""
    if not node or not cmds.objExists(node):
        raise ValueError("Node does not exist: {!r}".format(node))
    if cmds.nodeType(node) == "nurbsCurve":
        return [cmds.ls(node, long=full_path)[0]]
    shapes = cmds.listRelatives(node, shapes=True, noIntermediate=True,
                               fullPath=full_path) or []
    return [shape for shape in shapes if cmds.nodeType(shape) == "nurbsCurve"]


def require_editable(node):
    if cmds.referenceQuery(node, isNodeReferenced=True):
        raise RuntimeError("Referenced nodes cannot be edited: {}".format(node))


def serialize(node):
    curves = []
    for shape in curve_shapes(node):
        degree = cmds.getAttr(shape + ".degree")
        form = cmds.getAttr(shape + ".form")
        points = cmds.xform(shape + ".cv[*]", query=True, objectSpace=True, translation=True)
        triples = [points[index:index + 3] for index in range(0, len(points), 3)]
        curves.append({"degree": degree, "form": form, "points": triples})
    if not curves:
        raise ValueError("Node has no NURBS curve shapes: {}".format(node))
    return {"curves": curves}


def copy_to_clipboard(node):
    payload = json.dumps(serialize(node), separators=(",", ":"))
    cmds.optionVar(stringValue=(CLIPBOARD_OPTION, payload))
    return payload


def clipboard_data():
    if not cmds.optionVar(exists=CLIPBOARD_OPTION):
        raise RuntimeError("Controller shape clipboard is empty")
    return json.loads(cmds.optionVar(query=CLIPBOARD_OPTION))


def parent_shapes(source, target):
    require_editable(target)
    moved = []
    for shape in curve_shapes(source, full_path=False):
        moved.extend(cmds.parent(shape, target, shape=True, relative=True) or [])
    if cmds.objExists(source):
        cmds.delete(source)
    rename_shapes(target)
    return moved


def delete_shapes(node):
    require_editable(node)
    shapes = curve_shapes(node)
    if shapes:
        cmds.delete(shapes)


def rename_shapes(node):
    short = node.rsplit("|", 1)[-1].rsplit(":", 1)[-1]
    result = []
    for index, shape in enumerate(curve_shapes(node, full_path=False), 1):
        suffix = "Shape" if index == 1 else "Shape{}".format(index)
        result.append(cmds.rename(shape, short + suffix))
    return result
