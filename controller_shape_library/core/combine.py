"""Combine controller transforms while preserving world-space curve geometry."""

from __future__ import annotations

from maya import cmds
from . import shape_utils

_POSITION_TOLERANCE = 1.0e-5


def _world_cv_positions(shape):
    """Return CV positions before a shape is moved below another transform."""
    values = cmds.xform(
        shape + ".cv[*]", query=True, worldSpace=True, translation=True)
    return [values[index:index + 3] for index in range(0, len(values), 3)]


def _restore_world_cv_positions(shape, positions):
    """Bake captured world positions into a reparented curve shape."""
    for index, position in enumerate(positions):
        cmds.xform(
            "{}.cv[{}]".format(shape, index), worldSpace=True,
            translation=position)


def _positions_match(actual, expected):
    if len(actual) != len(expected):
        return False
    return all(
        abs(actual_axis - expected_axis) <= _POSITION_TOLERANCE
        for actual_point, expected_point in zip(actual, expected)
        for actual_axis, expected_axis in zip(actual_point, expected_point)
    )


def _copy_shapes(source, target):
    """Copy all source shapes to target without rebuilding their topology."""
    source_shapes = shape_utils.curve_shapes(source)
    world_positions = [_world_cv_positions(shape) for shape in source_shapes]
    duplicate = cmds.duplicate(
        source, returnRootsOnly=True, inputConnections=False)[0]
    copied_shapes = shape_utils.curve_shapes(duplicate)
    if len(copied_shapes) != len(source_shapes):
        cmds.delete(duplicate)
        raise RuntimeError("Failed to duplicate all controller shapes")
    records = list(zip(copied_shapes, world_positions))
    moved_shapes = []
    try:
        for shape, positions in records:
            moved = cmds.parent(
                shape, target, shape=True, relative=True) or []
            if not moved:
                raise RuntimeError("Failed to transfer a controller shape")
            moved_shape = cmds.ls(moved[0], long=True)[0]
            _restore_world_cv_positions(moved_shape, positions)
            actual = _world_cv_positions(moved_shape)
            if not _positions_match(actual, positions):
                raise RuntimeError(
                    "Failed to preserve controller shape position: {}".format(
                        source))
            moved_shapes.append(moved_shape)
    finally:
        if cmds.objExists(duplicate):
            cmds.delete(duplicate)
    return moved_shapes


def combine(controllers, target=None, delete_sources=True):
    """Move all source curve shapes under *target*, preserving their appearance."""
    nodes = list(dict.fromkeys(controllers))
    if len(nodes) < 2:
        raise ValueError("Select at least two controller transforms")
    target = target or nodes[-1]
    if target not in nodes:
        raise ValueError("target must be one of the supplied controllers")
    shape_utils.require_editable(target)
    for source in nodes:
        if source == target:
            continue
        shape_utils.require_editable(source)
        if not shape_utils.curve_shapes(source):
            continue
        _copy_shapes(source, target)
        if delete_sources and cmds.objExists(source):
            cmds.delete(source)
    shape_utils.rename_shapes(target)
    return target
