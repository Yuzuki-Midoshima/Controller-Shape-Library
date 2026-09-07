"""Public, UI-free API for controller creation and editing in Maya."""

from __future__ import annotations

from contextlib import contextmanager


@contextmanager
def _undo_chunk(label):
    from maya import cmds
    cmds.undoInfo(openChunk=True, chunkName=label)
    try:
        yield
    finally:
        cmds.undoInfo(closeChunk=True)


def available_shapes(category=None):
    """Return built-in shape ids. This query is safe outside Maya."""
    from .core.shape_data import shape_names
    return shape_names(category)


def create_controller(shape="circle", name="controller_CTRL", size=1.0, color=None,
                      parent=None, target=None):
    """Create a controller and optionally snap its transform to *target*."""
    from .core.creator import create
    with _undo_chunk("Create Controller"):
        controller = create(shape=shape, name=name, size=size, color=color, parent=parent)
        if target:
            from .core.snap import snap_to as _snap
            _snap(controller, target)
        return controller


def create_text_controller(text, name="text_CTRL", size=1.0, color=None,
                           font_family="Arial", parent=None, target=None):
    """Create detached NURBS outlines for arbitrary displayable text."""
    from .core.creator import create_from_data
    from .core.text_shape import outline_data
    with _undo_chunk("Create Text Controller"):
        controller = create_from_data(
            outline_data(text, font_family), name=name, size=size,
            color=color, parent=parent)
        if target:
            from .core.snap import snap_to as _snap
            _snap(controller, target)
        return controller


def combine_controllers(controllers, target=None, delete_sources=True):
    """Combine curve shapes under one transform, preserving world appearance."""
    from .core.combine import combine
    with _undo_chunk("Combine Controller Shapes"):
        return combine(controllers, target=target, delete_sources=delete_sources)


def replace_shape(target, shape="circle", size=1.0, color=None):
    from .core import shape_utils
    from .core.creator import create
    with _undo_chunk("Replace Controller Shape"):
        temporary = create(shape=shape, name="controllerShapeTemp#", size=size, color=color)
        shape_utils.delete_shapes(target)
        shape_utils.parent_shapes(temporary, target)
        return target


def add_shape(target, shape="circle", size=1.0, color=None):
    from .core import shape_utils
    from .core.creator import create
    with _undo_chunk("Add Controller Shape"):
        temporary = create(shape=shape, name="controllerShapeTemp#", size=size, color=color)
        shape_utils.parent_shapes(temporary, target)
        return target


def copy_shape(source):
    from .core.shape_utils import copy_to_clipboard
    return copy_to_clipboard(source)


def paste_shape(target, replace=True):
    from .core import shape_utils
    from .core.creator import create_from_data
    with _undo_chunk("Paste Controller Shape"):
        temporary = create_from_data(shape_utils.clipboard_data(), name="controllerShapeTemp#")
        if replace:
            shape_utils.delete_shapes(target)
        shape_utils.parent_shapes(temporary, target)
        return target


def scale_shape(target, scale):
    from .core.transform import scale as _scale
    with _undo_chunk("Scale Controller Shape"):
        return _scale(target, scale)


def rotate_shape(target, rotation):
    from .core.transform import rotate as _rotate
    with _undo_chunk("Rotate Controller Shape"):
        return _rotate(target, rotation)


def move_shape(target, translation):
    from .core.transform import move as _move
    with _undo_chunk("Move Controller Shape"):
        return _move(target, translation)


def set_color(target, color):
    from .core.color import set_color as _set_color
    with _undo_chunk("Set Controller Color"):
        return _set_color(target, color)


def snap_to(target, destination, translate=True, rotate=True, scale=False):
    from .core.snap import snap_to as _snap
    with _undo_chunk("Snap Controller"):
        return _snap(target, destination, translate, rotate, scale)


def create_zero_group(target, name_part="ZERO", position="suffix"):
    from .core.grouping import create_group
    with _undo_chunk("Create Zero Group"):
        return create_group(target, name_part, position)


def create_offset_group(target, name_part="OFFSET", position="suffix"):
    from .core.grouping import create_group
    with _undo_chunk("Create Offset Group"):
        return create_group(target, name_part, position)


def export_shape(source, path, name=None):
    from .core.shape_data import save_json
    from .core.shape_utils import serialize
    record_name = name or source.rsplit("|", 1)[-1].rsplit(":", 1)[-1]
    save_json(path, {record_name: serialize(source)})
    return path


def import_shape(path, name=None, controller_name=None, size=1.0, color=None):
    from .core.creator import create_from_data
    from .core.shape_data import load_json
    records = load_json(path)
    key = name or next(iter(records))
    if key not in records:
        raise ValueError("Shape {!r} is not present in {}".format(key, path))
    with _undo_chunk("Import Controller Shape"):
        return create_from_data(records[key], name=controller_name or key + "_CTRL",
                                size=size, color=color)


def library_path():
    from .core.library import LIBRARY_PATH
    return str(LIBRARY_PATH)


def library_shapes(path=None):
    """Return names stored in the persistent, scene-independent JSON library."""
    from .core.library import ordered_names
    return ordered_names(path)


def save_to_library(source, name, path=None, category="Panel"):
    """Add or replace one named shape in libraries/user_shapes.json."""
    from .core.library import save_shape
    from .core.shape_utils import serialize
    data = serialize(source)
    data["category"] = category
    data["label"] = name
    return save_shape(name, data, path)


def create_from_library(name, controller_name="controller", size=1.0, color=None,
                        path=None):
    """Create a controller from the shared JSON library."""
    from .core.creator import create_from_data
    from .core.library import load
    shapes = load(path)
    if name not in shapes:
        raise ValueError("Library shape does not exist: {}".format(name))
    with _undo_chunk("Create Library Controller"):
        return create_from_data(shapes[name], name=controller_name,
                                size=size, color=color)


def remove_from_library(name, path=None):
    from .core.library import remove_shape
    return remove_shape(name, path)


def move_library_shape(name, offset, path=None):
    from .core.library import move_shape
    return move_shape(name, offset, path)


def set_library_category(name, category, path=None):
    from .core.library import set_category
    return set_category(name, category, path)


def library_tab_order(category, path=None):
    from .core.library import tab_order
    return tab_order(category, path)


def set_library_tab_order(category, item_ids, path=None):
    from .core.library import set_tab_order
    return set_tab_order(category, item_ids, path)


def library_hidden_items(category, path=None):
    from .core.library import hidden_items
    return hidden_items(category, path)


def set_library_item_hidden(category, item_id, hidden=True, path=None):
    from .core.library import set_item_hidden
    return set_item_hidden(category, item_id, hidden, path)


def library_categories(path=None):
    from .core.library import categories
    return categories(path)


def add_library_category(label, path=None):
    from .core.library import add_category
    return add_category(label, path)


def rename_library_category(key, label, path=None):
    from .core.library import rename_category
    return rename_category(key, label, path)


def library_item_category(item_id, default=None, path=None):
    from .core.library import item_category
    return item_category(item_id, default, path)


def assign_library_item(item_id, category, path=None):
    from .core.library import assign_item
    return assign_item(item_id, category, path)


def remove_library_category(key, path=None):
    from .core.library import remove_category
    return remove_category(key, path)


def move_library_category(key, offset, path=None):
    from .core.library import move_category
    return move_category(key, offset, path)


__all__ = [
    "available_shapes", "create_controller", "replace_shape", "add_shape",
    "copy_shape", "paste_shape", "scale_shape", "rotate_shape", "move_shape",
    "set_color", "snap_to", "create_zero_group", "create_offset_group",
    "export_shape", "import_shape", "create_text_controller", "combine_controllers",
    "library_path", "library_shapes", "save_to_library", "create_from_library",
    "remove_from_library", "move_library_shape", "set_library_category",
    "library_tab_order", "set_library_tab_order",
    "library_hidden_items", "set_library_item_hidden",
    "library_categories", "add_library_category", "rename_library_category",
    "library_item_category", "assign_library_item",
    "remove_library_category", "move_library_category",
]
