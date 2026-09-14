"""Combine controller transforms while preserving world-space curve geometry."""

from __future__ import annotations

from maya import cmds
from maya.api import OpenMaya as om

from . import shape_utils


def _shape_in_target_space(shape, target_inverse):
    values = cmds.xform(shape + ".cv[*]", query=True, worldSpace=True, translation=True)
    points = []
    for index in range(0, len(values), 3):
        point = om.MPoint(*values[index:index + 3]) * target_inverse
        points.append((point.x, point.y, point.z))
    return {"degree": cmds.getAttr(shape + ".degree"), "points": points}


def _override_state(shape):
    """Capture the per-shape drawing override used for controller colors."""
    rgb = cmds.getAttr(shape + ".overrideColorRGB")
    if isinstance(rgb, list):
        rgb = rgb[0]
    return {
        "enabled": cmds.getAttr(shape + ".overrideEnabled"),
        "rgb_mode": cmds.getAttr(shape + ".overrideRGBColors"),
        "index": cmds.getAttr(shape + ".overrideColor"),
        "rgb": tuple(rgb),
    }


def _apply_override(shape, state):
    cmds.setAttr(shape + ".overrideEnabled", state["enabled"])
    cmds.setAttr(shape + ".overrideRGBColors", state["rgb_mode"])
    cmds.setAttr(shape + ".overrideColor", state["index"])
    cmds.setAttr(shape + ".overrideColorRGB", *state["rgb"])


def combine(controllers, target=None, delete_sources=True):
    """Move all source curve shapes under *target*, preserving their appearance."""
    nodes = list(dict.fromkeys(controllers))
    if len(nodes) < 2:
        raise ValueError("Select at least two controller transforms")
    target = target or nodes[-1]
    if target not in nodes:
        raise ValueError("target must be one of the supplied controllers")
    shape_utils.require_editable(target)
    target_matrix = om.MMatrix(cmds.xform(target, query=True, worldSpace=True, matrix=True))
    target_inverse = target_matrix.inverse()
    for source in nodes:
        if source == target:
            continue
        shape_utils.require_editable(source)
        source_shapes = shape_utils.curve_shapes(source)
        records = [(_shape_in_target_space(shape, target_inverse),
                    _override_state(shape)) for shape in source_shapes]
        if not records:
            continue
        # Build and transfer one curve at a time. A compound temporary transform
        # caused Maya to invalidate a shape name while its siblings were being
        # reparented (for example ``combinedShapeTemp_Shape``).
        for curve, color in records:
            temporary = cmds.curve(
                degree=int(curve["degree"]), point=curve["points"])
            temporary_shape = cmds.listRelatives(
                temporary, shapes=True, noIntermediate=True,
                fullPath=True)[0]
            moved = cmds.parent(
                temporary_shape, target, shape=True, relative=True) or []
            if cmds.objExists(temporary):
                cmds.delete(temporary)
            if not moved:
                raise RuntimeError("Failed to transfer a controller shape")
            moved_shape = cmds.ls(moved[0], long=True)[0]
            _apply_override(moved_shape, color)
        if delete_sources and cmds.objExists(source):
            cmds.delete(source)
    shape_utils.rename_shapes(target)
    return target
