import json
import hashlib
import tempfile
import unittest
from pathlib import Path

from controller_shape_library import api
from controller_shape_library.core import library, naming, shape_data


class ControllerShapeDataTests(unittest.TestCase):
    def test_existing_shape_geometry_is_unchanged(self):
        fixture = Path(__file__).with_name("existing_shape_fingerprints.json")
        expected = json.loads(fixture.read_text(encoding="utf-8"))
        self.assertTrue(expected)
        for name, digest in expected.items():
            # Direction words intentionally follow the active Maya/Qt Arial
            # outline generator and are no longer static hand-drawn geometry.
            if name in {"left", "right", "front", "back", "up", "down"}:
                continue
            self.assertIn(name, shape_data.SHAPES)
            data = shape_data.SHAPES[name]
            stable = {"category": data.get("category"), "curves": data["curves"]}
            raw = json.dumps(stable, sort_keys=True, separators=(",", ":"))
            actual = hashlib.sha256(raw.encode("utf-8")).hexdigest()
            self.assertEqual(actual, digest, name)

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

    def test_new_shape_set_exists_and_validates(self):
        added = {
            "hemisphere", "pyramid", "capsule", "rotate_360", "rotate_cw",
            "rotate_ccw", "rotate_xyz", "pole_vector", "root", "ik", "fk",
            "settings", "world", "eye", "foot", "hand",
        }
        self.assertTrue(added.issubset(shape_data.SHAPES))
        for name in added:
            self.assertTrue(shape_data.validate_shape(
                name, shape_data.get_shape(name)))

    def test_direction_shapes_are_compound_curve_strokes(self):
        for name in ("left", "right", "front", "back", "up", "down"):
            self.assertGreater(len(shape_data.get_shape(name)["curves"]), 1)

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

    def test_saving_selected_shape_under_new_name_renames_the_entry(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "user_shapes.json"
            library.save_shape("one", shape_data.get_shape("circle"), path)
            library.save_shape("two", shape_data.get_shape("square"), path)
            library.set_tab_order(
                "Basic", ["custom:one", "custom:two"], path)
            library.set_item_hidden("Basic", "custom:one", True, path)
            library.assign_item("custom:one", "Basic", path)

            replacement = shape_data.get_shape("triangle")
            library.save_shape(
                "renamed", replacement, path, replace_name="one")

            self.assertEqual(library.ordered_names(path), ["renamed", "two"])
            self.assertNotIn("one", library.load(path))
            expected = json.loads(json.dumps(replacement))
            self.assertEqual(library.load(path)["renamed"], expected)
            self.assertEqual(
                library.tab_order("Basic", path),
                ["custom:renamed", "custom:two"])
            self.assertEqual(
                library.hidden_items("Basic", path), ["custom:renamed"])
            self.assertEqual(
                library.item_category("custom:renamed", None, path), "Basic")

    def test_new_library_save_refuses_an_existing_name(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "user_shapes.json"
            original = shape_data.get_shape("circle")
            library.save_shape("one", original, path)

            with self.assertRaises(ValueError):
                library.save_shape(
                    "one", shape_data.get_shape("square"), path,
                    allow_overwrite=False)

            expected = json.loads(json.dumps(original))
            self.assertEqual(library.load(path)["one"], expected)


if __name__ == "__main__":
    unittest.main()
