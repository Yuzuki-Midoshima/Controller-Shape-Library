"""Curve-shape queries and safe transfer operations."""

from __future__ import annotations

import copy
import json

from maya import cmds

CLIPBOARD_OPTION = "controllerShapeToolkitClipboard"


def normalized_data(data):
    """Return library curve data centered at the origin and sized to one unit.

    User-authored controls often have transforms frozen after being positioned
    or scaled.  In that case their CV values contain scene-sized offsets even
    though the visible controller looked correct when it was registered.  A
    library shape is a reusable template, so store/use it in a predictable
    local space: bounding-box center at zero and largest half-extent at one.
    """
    result = copy.deepcopy(data)
    points = [point for curve in result.get("curves", [])
              for point in curve.get("points", [])]
    if not points:
        return result

    minimum = [min(float(point[axis]) for point in points) for axis in range(3)]
    maximum = [max(float(point[axis]) for point in points) for axis in range(3)]
    center = [(minimum[axis] + maximum[axis]) * 0.5 for axis in range(3)]
    radius = max((maximum[axis] - minimum[axis]) * 0.5 for axis in range(3))
    if radius <= 1.0e-12:
        radius = 1.0

    for curve in result["curves"]:
        curve["points"] = [
            [(float(point[axis]) - center[axis]) / radius for axis in range(3)]
            for point in curve.get("points", [])
        ]
    return result


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


def parent_shapes(source, target, rename=True):
    require_editable(target)
    moved = []
    # Keep full DAG paths while moving compound shapes. Short shape names can
    # become stale or ambiguous as Maya reparents sibling shapes.
    for shape in curve_shapes(source, full_path=True):
        moved.extend(cmds.parent(shape, target, shape=True, relative=True) or [])
    if cmds.objExists(source):
        cmds.delete(source)
    if rename:
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
