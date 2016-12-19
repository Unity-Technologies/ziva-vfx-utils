import maya.cmds as mc
import maya.mel as mm
from maya import OpenMaya as om


def getDependNode(nodeName):
    """Get an MObject (depend node) for the associated node name

    :Parameters:
        nodeName
            String representing the node
    
    :Return: depend node (MObject)

    """
    #print nodeName
    dependNode = om.MObject()
    selList = om.MSelectionList()
    selList.add(nodeName)
    if selList.length() > 0: 
        selList.getDependNode(0, dependNode)
    return dependNode
