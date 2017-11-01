from zBuilder.nodes.dg_node import DGNode
import maya.cmds as mc


class TransformNode(DGNode):
    type = 'transform'
    EXTEND_ATTR_LIST = ['rotatePivotX', 'rotatePivotY', 'rotatePivotZ']

    def __init__(self, *args, **kwargs):
        self.parent = None
        self.world_position = list()
        self.world_rotation = list()
        self.joint_orient = list()

        DGNode.__init__(self, *args, **kwargs)

    def populate(self, transformName):
        transformData_dict = get_transformData_data(transformName)

        self.name = transformName
        self.type = transformData_dict['type']
        self.world_rotation = transformData_dict['worldRotation']
        self.world_position = transformData_dict['worldPosition']
        self.parent = transformData_dict['parent']

        if transformData_dict['type'] == 'joint':
            self.joint_orient = transformData_dict['jointOrient']

    def build(self):
        build_transform(self.name,
                        self.type,
                        self.parent,
                        self.joint_orient)


def build_transform(transformName, transformType, parentName, jointOrient):
    print 'name = %s \ntype = %s\n' % (transformName, transformType)

    newTransformName = None

    if transformType == 'locator':
        newTransformName = mc.createNode(transformType)
        newTransformName = mc.listRelatives(newTransformName, parent=True)[0]

    elif transformType == 'nurbsCurve':
        newTransformName = mc.createNode('transform')

    else:
        newTransformName = mc.createNode(transformType)

    mc.rename(newTransformName, transformName)


def get_transformData_data(transformName):
    transformData_dict = dict()

    # get type
    objectType = mc.objectType(
        transformName)  # need to find out if it's a locator.
    if objectType == 'transform':
        shapeNodes = mc.listRelatives(transformName, shapes=True)
        if shapeNodes != None:
            # print 'setting type to:', transformName, mc.objectType( shapeNodes[0] )
            transformData_dict['type'] = mc.objectType(shapeNodes[0])
        else:
            if mc.objectType(transformName, isType='transform'):
                transformData_dict['type'] = 'transform'
    else:
        transformData_dict['type'] = objectType

    # get parent
    returnedParent = mc.listRelatives(transformName, parent=True)
    transformData_dict['parent'] = returnedParent
    if type(transformData_dict['parent']) is list:
        transformData_dict['parent'] = returnedParent[0]


        # get world position
    transformData_dict['worldPosition'] = mc.xform(transformName, q=True,
                                                   t=True, ws=True)

    # get world rotation
    transformData_dict['worldRotation'] = mc.xform(transformName, q=True,
                                                   ro=True, ws=True)

    # get joint orient
    if transformData_dict['type'] == 'joint':
        # print 'setting joint orient to',list( mc.getAttr( transformName+'.jointOrient' )[0] )
        transformData_dict['jointOrient'] = list(
            mc.getAttr(transformName + '.jointOrient')[0])

    return transformData_dict
