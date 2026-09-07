"""Build controller transforms from validated curve data."""

from __future__ import annotations

from maya import cmds

from . import naming, shape_data, shape_utils


def _curve(curve_data):
    points = curve_data["points"]
    degree = int(curve_data.get("degree", 1))
    kwargs = {"degree": degree, "point": points}
    if curve_data.get("periodic"):
        kwargs["periodic"] = True
        kwargs["knot"] = list(range(len(points) + degree - 1))
    return cmds.curve(**kwargs)


def create_from_data(data, name="controller_CTRL", size=1.0, color=None,
                     parent=None, matrix=None, apply_orientation=True):
    shape_data.validate_shape(name, data)
    if size <= 0:
        raise ValueError("size must be greater than zero")
    controller = cmds.createNode("transform", name=naming.unique(name), parent=parent)
    try:
        for curve_data in data["curves"]:
            scaled = dict(curve_data)
            # Maya controllers in this toolkit face the opposite Y orientation
            # from the source/library coordinate convention. Bake the 180-degree
            # Y correction into CVs so the transform channels remain zeroed.
            orientation = (-1.0, 1.0, -1.0) if apply_orientation else (1.0, 1.0, 1.0)
            scaled["points"] = [
                [point[axis] * orientation[axis] * float(size) for axis in range(3)]
                for point in curve_data["points"]
            ]
            temporary = _curve(scaled)
            shape_utils.parent_shapes(temporary, controller)
        if matrix is not None:
            cmds.xform(controller, worldSpace=True, matrix=matrix)
        shape_utils.rename_shapes(controller)
        if color is not None:
            from .color import set_color
            set_color(controller, color)
        return controller
    except Exception:
        if cmds.objExists(controller):
            cmds.delete(controller)
        raise


def create(shape="circle", **kwargs):
    return create_from_data(shape_data.get_shape(shape), **kwargs)
