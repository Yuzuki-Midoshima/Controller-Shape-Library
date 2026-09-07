import json
import tempfile
import unittest
from pathlib import Path

from controller_shape_library import api
from controller_shape_library.core import library, naming, shape_data


class ControllerShapeDataTests(unittest.TestCase):
    def test_all_required_shapes_exist_and_validate(self):
        required = {
            "circle", "circle_low", "triangle", "square", "cross", "fat_cross",
            "pentagon", "hexagon", "diamond", "cube", "sphere", "cone", "aim",
            "single_arrow", "double_arrow", "four_arrow", "rotation_90", "rotation_180",
            "left", "right", "front", "back", "up", "down",
        }
        self.assertTrue(required.issubset(set(api.available_shapes())))
        for name in required:
            self.assertTrue(shape_data.validate_shape(name, shape_data.get_shape(name)))

    def test_direction_shapes_are_compound_curve_strokes(self):
        for name in ("left", "right", "front", "back", "up", "down"):
            self.assertGreater(len(shape_data.get_shape(name)["curves"]), 2)

    def test_get_shape_is_an_independent_copy(self):
        data = shape_data.get_shape("square")
        data["curves"][0]["points"][0] = (99, 99, 99)
        self.assertNotEqual(shape_data.get_shape("square")["curves"][0]["points"][0],
                            (99, 99, 99))

    def test_json_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "shape.json"
            shape_data.save_json(path, {"square": shape_data.get_shape("square")})
            self.assertEqual(list(shape_data.load_json(path)), ["square"])
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["version"], 1)

    def test_namespace_name_is_preserved(self):
        self.assertEqual(naming.sanitized("char:L arm CTRL"), "char:L_arm_CTRL")
        self.assertEqual(naming.derived("char:L_arm_CTRL", "ZERO"), "char:L_arm_ZERO")
        self.assertEqual(naming.derived("controller_CTRL", "-ZERO"), "controller-ZERO")
        self.assertEqual(
            naming.derived("controller_CTRL", "ZERO-", "prefix"),
            "ZERO-controller")
        self.assertEqual(
            naming.derived("controller_CTRL", "ZERO", "prefix"),
            "ZERO_controller")

    def test_library_order_is_persistent_and_old_files_are_compatible(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "user_shapes.json"
            path.write_text(json.dumps({
                "version": 1,
                "shapes": {
                    "one": shape_data.get_shape("circle"),
                    "two": shape_data.get_shape("square"),
                },
            }), encoding="utf-8")
            self.assertEqual(library.ordered_names(path), ["one", "two"])
            library.move_shape("two", -1, path)
            self.assertEqual(library.ordered_names(path), ["two", "one"])
            library.set_category("one", "Basic", path)
            self.assertEqual(library.load(path)["one"]["category"], "Basic")
            order = ["builtin:circle", "custom:one", "builtin:square"]
            library.set_tab_order("Basic", order, path)
            self.assertEqual(library.tab_order("Basic", path), order)
            library.set_item_hidden("Basic", "builtin:circle", True, path)
            self.assertEqual(
                library.hidden_items("Basic", path), ["builtin:circle"])
            library.set_item_hidden("Basic", "builtin:circle", False, path)
            self.assertEqual(library.hidden_items("Basic", path), [])
            key = library.add_category("顔", path)
            self.assertEqual(library.categories(path)[-1]["label"], "顔")
            library.rename_category(key, "フェイス", path)
            self.assertEqual(library.categories(path)[-1]["label"], "フェイス")
            library.assign_item("builtin:circle", key, path)
            self.assertEqual(library.item_category("builtin:circle", None, path), key)
            library.move_category(key, -1, path)
            self.assertEqual(library.categories(path)[-2]["key"], key)
            library.remove_category(key, path)
            self.assertNotIn(key, [item["key"] for item in library.categories(path)])


if __name__ == "__main__":
    unittest.main()
