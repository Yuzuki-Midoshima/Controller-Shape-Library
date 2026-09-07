import unittest

import maya.standalone

maya.standalone.initialize(name="python")

from maya import cmds

from controller_shape_library import api


class ControllerShapeMayaTests(unittest.TestCase):
    def setUp(self):
        cmds.file(new=True, force=True)

    def test_create_compound_and_cv_edit(self):
        controller = api.create_controller("sphere", "char:L_arm_CTRL", size=2, color=6)
        self.assertEqual(controller, "char:L_arm_CTRL")
        self.assertEqual(len(cmds.listRelatives(controller, shapes=True)), 3)
        api.scale_shape(controller, .5)
        self.assertEqual(cmds.getAttr(controller + ".scaleX"), 1.0)

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


if __name__ == "__main__":
    unittest.main()
