import unittest

import maya.standalone

maya.standalone.initialize(name="python")

from maya import cmds

from controller_shape_library import api
from controller_shape_library.core import shape_data, shape_utils, text_shape


class ControllerShapeMayaTests(unittest.TestCase):
    def setUp(self):
        cmds.file(new=True, force=True)

    def test_create_compound_and_cv_edit(self):
        controller = api.create_controller("sphere", "char:L_arm_CTRL", size=2, color=6)
        self.assertEqual(controller, "char:L_arm_CTRL")
        self.assertEqual(len(cmds.listRelatives(controller, shapes=True)), 3)
        api.scale_shape(controller, .5)
        self.assertEqual(cmds.getAttr(controller + ".scaleX"), 1.0)

    def test_created_controller_keeps_asymmetric_preset_orientation(self):
        controller = api.create_controller("pin", "pin_CTRL")
        expected = shape_data.get_shape("pin")["curves"][0]["points"]
        actual = shape_utils.serialize(controller)["curves"][0]["points"]
        self.assertEqual(len(actual), len(expected))
        for actual_point, expected_point in zip(actual, expected):
            for actual_axis, expected_axis in zip(actual_point, expected_point):
                self.assertAlmostEqual(actual_axis, expected_axis)

    def test_direction_presets_use_the_free_form_text_font(self):
        for name in ("left", "right", "front", "back", "up", "down"):
            expected = text_shape.outline_data(name.upper())["curves"]
            self.assertEqual(shape_data.get_shape(name)["curves"], expected)

    def test_shape_copy_replace_and_grouping(self):
        source = api.create_controller("square", "source_CTRL")
        target = api.create_controller("circle", "target_CTRL")
        api.copy_shape(source)
        api.paste_shape(target)
        self.assertEqual(len(cmds.listRelatives(target, shapes=True)), 1)
        self.assertEqual(api.create_zero_group(target), "target_ZERO")

    def test_direction_uses_only_curves(self):
        controller = api.create_controller("left", "left_CTRL")
        history = cmds.listHistory(controller) or []
        self.assertFalse([node for node in history if cmds.nodeType(node) == "type"])
        self.assertGreater(len(cmds.listRelatives(controller, shapes=True)), 2)

    def test_snap_can_apply_translation_only(self):
        controller = api.create_controller("circle", "snap_CTRL")
        target = cmds.createNode("transform", name="snap_target")
        cmds.setAttr(target + ".translate", 1, 2, 3)
        cmds.setAttr(target + ".rotate", 10, 20, 30)
        api.snap_to(controller, target, translate=True, rotate=False)
        self.assertEqual(tuple(cmds.xform(controller, query=True, worldSpace=True,
                                         translation=True)), (1.0, 2.0, 3.0))
        self.assertEqual(tuple(cmds.xform(controller, query=True, worldSpace=True,
                                         rotation=True)), (0.0, 0.0, 0.0))

    def test_combine_preserves_each_shape_color(self):
        red = api.create_controller("circle", "red_CTRL", color=13)
        blue = api.create_controller("square", "blue_CTRL", color=(0.1, 0.2, 0.9))
        result = api.combine_controllers([red, blue], target=blue)
        shapes = cmds.listRelatives(result, shapes=True, fullPath=True)
        self.assertEqual(len(shapes), 2)
        states = {(cmds.getAttr(shape + ".overrideRGBColors"),
                   cmds.getAttr(shape + ".overrideColor")) for shape in shapes}
        self.assertIn((False, 13), states)
        rgb_shapes = [shape for shape in shapes
                      if cmds.getAttr(shape + ".overrideRGBColors")]
        self.assertEqual(len(rgb_shapes), 1)
        rgb = cmds.getAttr(rgb_shapes[0] + ".overrideColorRGB")[0]
        self.assertAlmostEqual(rgb[2], 0.9)

    def test_custom_zero_suffix(self):
        target = api.create_controller("circle", "hand_CTRL")
        self.assertEqual(api.create_zero_group(target, "ZRO"), "hand_ZRO")

    def test_all_added_presets_create_only_nurbs_curves(self):
        names = (
            "hemisphere", "pyramid", "capsule", "rotate_360", "rotate_cw",
            "rotate_ccw", "rotate_xyz", "pole_vector", "root", "ik", "fk",
            "settings", "world", "eye", "foot", "hand",
        )
        for name in names:
            controller = api.create_controller(name, name + "_CTRL")
            shapes = cmds.listRelatives(controller, shapes=True) or []
            self.assertTrue(shapes, name)
            self.assertTrue(all(cmds.nodeType(shape) == "nurbsCurve"
                                for shape in shapes), name)

    def test_new_text_controller_saves_without_a_second_correction(self):
        import json
        import tempfile
        from pathlib import Path

        controller = api.create_text_controller("HIGH", "HIGH_CTRL")
        self.assertTrue(cmds.getAttr(
            controller + ".controllerShapePreviewFlipX"))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "shapes.json"
            api.save_to_library(controller, "HIGH", path, "Direction")
            record = json.loads(path.read_text(encoding="utf-8"))["shapes"]["HIGH"]
            self.assertFalse(record["preview_flip_x"])
            self.assertTrue(record["preview_flip_z"])
            self.assertFalse(record["apply_orientation"])
            # New library records retain Maya-space CVs, so recreating must
            # preserve the selected controller's orientation exactly.
            recreated = api.create_from_library(
                "HIGH", "HIGH_COPY_CTRL", path=path)
            original_points = cmds.xform(
                cmds.listRelatives(controller, shapes=True, fullPath=True)[0]
                + ".cv[*]", query=True, objectSpace=True, translation=True)
            recreated_points = cmds.xform(
                cmds.listRelatives(recreated, shapes=True, fullPath=True)[0]
                + ".cv[*]", query=True, objectSpace=True, translation=True)
            self.assertEqual(original_points, recreated_points)


if __name__ == "__main__":
    unittest.main()
