"""Zero and offset group creation."""

from maya import cmds

from . import naming


def create_group(node, name_part, position="suffix"):
    if not cmds.objExists(node):
        raise ValueError("Node does not exist: {}".format(node))
    if cmds.referenceQuery(node, isNodeReferenced=True):
        raise RuntimeError("Cannot reparent a referenced node: {}".format(node))
    name_part = str(name_part).strip()
    if not name_part:
        raise ValueError("Group name part must not be empty")
    parent = (cmds.listRelatives(node, parent=True, fullPath=True) or [None])[0]
    matrix = cmds.xform(node, query=True, worldSpace=True, matrix=True)
    group = cmds.createNode(
        "transform", name=naming.derived(node, name_part, position), parent=parent)
    cmds.xform(group, worldSpace=True, matrix=matrix)
    cmds.parent(node, group, absolute=True)
    return group
