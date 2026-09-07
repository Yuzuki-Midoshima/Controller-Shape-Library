"""Explicit transform snapping without selection side effects."""

from maya import cmds


def snap_to(node, target, translate=True, rotate=True, scale=False):
    if not cmds.objExists(node) or not cmds.objExists(target):
        raise ValueError("Both node and target must exist")
    if cmds.referenceQuery(node, isNodeReferenced=True):
        raise RuntimeError("Referenced nodes cannot be transformed: {}".format(node))
    attrs = []
    if translate:
        attrs.extend(("tx", "ty", "tz"))
    if rotate:
        attrs.extend(("rx", "ry", "rz"))
    if scale:
        attrs.extend(("sx", "sy", "sz"))
    locked = [attr for attr in attrs if cmds.getAttr(node + "." + attr, lock=True)]
    if locked:
        raise RuntimeError("Locked attributes prevent snap: {}".format(", ".join(locked)))
    if translate or rotate:
        options = {"maintainOffset": False}
        if not translate:
            options["skipTranslate"] = ("x", "y", "z")
        if not rotate:
            options["skipRotate"] = ("x", "y", "z")
        constraint = cmds.parentConstraint(target, node, **options)[0]
        cmds.delete(constraint)
    if scale:
        constraint = cmds.scaleConstraint(target, node, maintainOffset=False)[0]
        cmds.delete(constraint)
    return node
