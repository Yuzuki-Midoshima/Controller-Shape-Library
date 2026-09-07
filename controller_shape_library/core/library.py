"""Persistent, scene-independent custom shape library."""

from __future__ import annotations

import json
from pathlib import Path

from .shape_data import validate_shape


LIBRARY_PATH = Path(__file__).resolve().parents[2] / "libraries" / "user_shapes.json"
DEFAULT_CATEGORIES = [
    {"key": "Basic", "label": "基本"},
    {"key": "Solid", "label": "立体"},
    {"key": "Arrow", "label": "矢印"},
    {"key": "Direction", "label": "文字"},
    {"key": "Panel", "label": "パネル"},
]


def _payload(path=None):
    library_path = Path(path) if path else LIBRARY_PATH
    if not library_path.exists():
        return {"version": 2, "shapes": {}, "order": [], "tab_orders": {},
                "hidden": {}, "categories": list(DEFAULT_CATEGORIES),
                "assignments": {}}
    with library_path.open("r", encoding="utf-8") as stream:
        payload = json.load(stream)
    shapes = payload.get("shapes", {})
    if not isinstance(shapes, dict):
        raise ValueError("Library JSON must contain a shapes object")
    for name, data in shapes.items():
        validate_shape(name, data)
    order = [name for name in payload.get("order", []) if name in shapes]
    order.extend(name for name in shapes if name not in order)
    tab_orders = payload.get("tab_orders", {})
    if not isinstance(tab_orders, dict):
        tab_orders = {}
    hidden = payload.get("hidden", {})
    if not isinstance(hidden, dict):
        hidden = {}
    categories = payload.get("categories", DEFAULT_CATEGORIES)
    if not isinstance(categories, list):
        categories = list(DEFAULT_CATEGORIES)
    assignments = payload.get("assignments", {})
    if not isinstance(assignments, dict):
        assignments = {}
    return {"version": 2, "shapes": shapes, "order": order,
            "tab_orders": tab_orders, "hidden": hidden,
            "categories": categories, "assignments": assignments}


def _write(payload, path=None):
    library_path = Path(path) if path else LIBRARY_PATH
    library_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = library_path.with_suffix(".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
    temporary.replace(library_path)
    return str(library_path)


def load(path=None):
    return _payload(path)["shapes"]


def ordered_names(path=None):
    return list(_payload(path)["order"])


def save_shape(name, data, path=None):
    name = str(name).strip()
    if not name:
        raise ValueError("Library shape name must not be empty")
    validate_shape(name, data)
    library_path = Path(path) if path else LIBRARY_PATH
    payload = _payload(library_path)
    shapes = payload["shapes"]
    is_new = name not in shapes
    shapes[name] = data
    if is_new:
        payload["order"].append(name)
    return _write(payload, library_path)


def remove_shape(name, path=None):
    library_path = Path(path) if path else LIBRARY_PATH
    payload = _payload(library_path)
    shapes = payload["shapes"]
    if name not in shapes:
        raise ValueError("Library shape does not exist: {}".format(name))
    del shapes[name]
    payload["order"] = [item for item in payload["order"] if item != name]
    return _write(payload, library_path)


def move_shape(name, offset, path=None):
    payload = _payload(path)
    order = payload["order"]
    if name not in order:
        raise ValueError("Library shape does not exist: {}".format(name))
    category = payload["shapes"][name].get("category", "Panel")
    siblings = [item for item in order
                if payload["shapes"][item].get("category", "Panel") == category]
    sibling_index = siblings.index(name)
    new_sibling_index = max(0, min(
        len(siblings) - 1, sibling_index + int(offset)))
    if sibling_index != new_sibling_index:
        other = siblings[new_sibling_index]
        old_index, new_index = order.index(name), order.index(other)
        order[old_index], order[new_index] = order[new_index], order[old_index]
        _write(payload, path)
    return new_sibling_index


def set_category(name, category, path=None):
    payload = _payload(path)
    if name not in payload["shapes"]:
        raise ValueError("Library shape does not exist: {}".format(name))
    payload["shapes"][name]["category"] = str(category)
    return _write(payload, path)


def tab_order(category, path=None):
    return list(_payload(path)["tab_orders"].get(str(category), []))


def set_tab_order(category, item_ids, path=None):
    payload = _payload(path)
    payload["tab_orders"][str(category)] = list(item_ids)
    return _write(payload, path)


def hidden_items(category, path=None):
    return list(_payload(path)["hidden"].get(str(category), []))


def set_item_hidden(category, item_id, hidden=True, path=None):
    payload = _payload(path)
    values = payload["hidden"].setdefault(str(category), [])
    if hidden and item_id not in values:
        values.append(item_id)
    elif not hidden and item_id in values:
        values.remove(item_id)
    return _write(payload, path)


def categories(path=None):
    return [dict(item) for item in _payload(path)["categories"]]


def add_category(label, path=None):
    label = str(label).strip()
    if not label:
        raise ValueError("Category label must not be empty")
    payload = _payload(path)
    existing = {item["key"] for item in payload["categories"]}
    base = "UserTab"
    index = 1
    while "{}{}".format(base, index) in existing:
        index += 1
    key = "{}{}".format(base, index)
    payload["categories"].append({"key": key, "label": label})
    _write(payload, path)
    return key


def rename_category(key, label, path=None):
    label = str(label).strip()
    if not label:
        raise ValueError("Category label must not be empty")
    payload = _payload(path)
    for item in payload["categories"]:
        if item["key"] == key:
            item["label"] = label
            _write(payload, path)
            return label
    raise ValueError("Category does not exist: {}".format(key))


def remove_category(key, path=None):
    payload = _payload(path)
    if len(payload["categories"]) <= 1:
        raise ValueError("At least one category is required")
    keys = [item["key"] for item in payload["categories"]]
    if key not in keys:
        raise ValueError("Category does not exist: {}".format(key))
    fallback = next((value for value in keys if value != key), keys[0])
    payload["categories"] = [item for item in payload["categories"]
                               if item["key"] != key]
    for name, data in payload["shapes"].items():
        if data.get("category") == key:
            data["category"] = fallback
    for item_id, category in list(payload["assignments"].items()):
        if category == key:
            payload["assignments"][item_id] = fallback
    payload["tab_orders"].pop(key, None)
    payload["hidden"].pop(key, None)
    return _write(payload, path)


def move_category(key, offset, path=None):
    payload = _payload(path)
    records = payload["categories"]
    old = next((index for index, item in enumerate(records)
                if item["key"] == key), -1)
    if old < 0:
        raise ValueError("Category does not exist: {}".format(key))
    new = max(0, min(len(records) - 1, old + int(offset)))
    if old != new:
        records.insert(new, records.pop(old))
        _write(payload, path)
    return new


def item_category(item_id, default=None, path=None):
    return _payload(path)["assignments"].get(str(item_id), default)


def assign_item(item_id, category, path=None):
    payload = _payload(path)
    payload["assignments"][str(item_id)] = str(category)
    return _write(payload, path)
