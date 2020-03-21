from zBuilder.nodes.dg_node import DGNode
from maya import cmds


class Constraint(DGNode):
    """ The base node for the node functionality of all nodes
    """
    type = None
    TYPES = ['pointConstraint', 'orientConstraint', 'parentConstraint']
    """ The type of node. """

    SEARCH_EXCLUDE = ['_class', '_attrs']
    """ List of attributes to exclude with a string_replace"""
    EXTEND_ATTR_LIST = list()
    """ List of maya attributes to add to attribute list when capturing."""

    def build(self, *args, **kwargs):
        """ Builds the zCloth in maya scene.

        Args:
            attr_filter (dict):  Attribute filter on what attributes to get.
                dictionary is key value where key is node type and value is
                list of attributes to use.

                tmp = {'zSolver':['substeps']}
            permissive (bool): Pass on errors. Defaults to ``True``
        """
        attr_filter = kwargs.get('attr_filter', list())
        permissive = kwargs.get('permissive', True)

        name = self.get_scene_name()
        if not cmds.objExists(name):

            cmds.select(self.association)
            constraint = None
            if self.type == 'parentConstraint':
                results = cmds.parentConstraint(mo=True)
                constraint = cmds.ls(results, type='parentConstraint')[0]
            if self.type == 'pointConstraint':
                results = cmds.pointConstraint(mo=True)
                constraint = cmds.ls(results, type='pointConstraint')[0]
            if self.type == 'orientConstraint':
                results = cmds.orientConstraint(mo=True)
                constraint = cmds.ls(results, type='orientConstraint')[0]

            cmds.rename(constraint, name)
        else:
            new_name = cmds.rename(self.name, self.name)

        self.set_maya_attrs(attr_filter=attr_filter)

    @property
    def targets(self):
        short = [x.split('|')[-1] for x in self.association]
        return short[:-1]

    @property
    def constrained(self):
        short = [x.split('|')[-1] for x in self.association]
        return short[-1]

    def populate(self, maya_node=None):
        super(Constraint, self).populate(maya_node=maya_node)

        name = self.get_scene_name()
        targets = get_targets(name)
        constrained = get_constrained(name)

        association = targets
        association.extend(constrained)
        self.association = association

        # if constraintData_dict['type'] == 'aimConstraint':
        #     self.set_upObject(constraintData_dict['upObject'])

        # # TO DO: This is hardcoded to expect that the constraint has only one target
        # if self.get_type() == 'parentConstraint':
        #     attrList.append('target[0].targetOffsetTranslateX')
        #     attrList.append('target[0].targetOffsetTranslateY')
        #     attrList.append('target[0].targetOffsetTranslateZ')
        #     attrList.append('target[0].targetOffsetRotateX')
        #     attrList.append('target[0].targetOffsetRotateY')
        #     attrList.append('target[0].targetOffsetRotateZ')
        #
        # attrs = base.build_attr_key_values(constraint_name, attrList)
        # self.set_attrs(attrs)


def get_targets(constraint_name):
    i = 0
    targets = list()
    while not cmds.listConnections('{}.target[{}].targetParentMatrix'.format(constraint_name,
                                                                           i)) == None:
        targets.extend(
            cmds.listConnections('{}.target[{}].targetParentMatrix'.format(constraint_name, i)))
        i += 1
    return targets


def get_constrained(constraint_name):
    con = [
        'constraintTranslateX', 'constraintTranslateY', 'constraintTranslateZ', 'constraintRotateX',
        'constraintRotateY', 'constraintRotateZ'
    ]

    constrained = [
        cmds.listConnections('{}.{}'.format(constraint_name, c))[0] for c in con
        if cmds.objExists('{}.{}'.format(constraint_name, c))
    ]
    constrained = list(set(constrained))
    return constrained


#
# def get_constraint_data(constraintName):
#     constraintData_dict = dict()
#
#     # Get generic stuff
#     constraintData_dict['type'] = cmds.objectType(constraintName)
#     targetObjects_list = list()
#     i = 0
#     while not cmds.listConnections('%s.target[%i].targetParentMatrix' % (
#     constraintName, i)) == None:
#         targetObjects_list.append(cmds.listConnections(
#             '%s.target[%i].targetParentMatrix' % (constraintName, i))[0])
#         i += 1
#     constraintData_dict['targets'] = targetObjects_list
#
#     if constraintData_dict['type'] == 'aimConstraint':
#         # up object
#         worldUpObj = cmds.listConnections(constraintName + '.worldUpMatrix')
#         if not worldUpObj == None:
#             constraintData_dict['upObject'] = worldUpObj[0]
#         else:
#             constraintData_dict['upObject'] = None
#
#         # constrained object
#         constraintData_dict['constrained'] = \
#         cmds.listConnections(constraintName + '.constraintRotateOrder')[0]
#
#     if constraintData_dict['type'] == 'parentConstraint':
#
#         # if there's no connections to rotations we check translations.
#         # TO DO this should probably support skipping axes
#         print 'working on populating data for %s' % constraintName
#         constrainedObject = cmds.listConnections(
#             constraintName + '.constraintRotate.constraintRotateX')
#         if constrainedObject != None:
#             constraintData_dict['constrained'] = constrainedObject[0]
#         else:
#             constraintData_dict['constrained'] = cmds.listConnections(
#                 constraintName + '.constraintTranslate.constraintTranslateX')[0]
#
#     if constraintData_dict['type'] == 'poleVectorConstraint':
#         print 'working on populating data for %s' % constraintName
#         constraintData_dict['constrained'] = \
#         cmds.listConnections(constraintName + '.constraintParentInverseMatrix')[0]
#
#     return constraintData_dict
#
#
# def build_constraint(constraintName, constraintType, targetObjects,
#                      constrainedObject, upObject):
#     if constraintType == 'aimConstraint':
#         py_cmd = 'cmds.aimConstraint( %s, \'%s\', worldUpObject=\'%s\', name=\'%s\', mo=True )' % (
#         targetObjects, constrainedObject, upObject, constraintName)
#         exec (py_cmd)
#
#     if constraintType == 'parentConstraint':
#         py_cmd = 'cmds.parentConstraint( %s, \'%s\', name=\'%s\' )' % (
#         targetObjects, constrainedObject, constraintName)
#         exec (py_cmd)
#
#     if constraintType == 'poleVectorConstraint':
#         py_cmd = 'cmds.poleVectorConstraint( %s, \'%s\', name=\'%s\' )' % (
#         targetObjects, constrainedObject, constraintName)
#         exec (py_cmd)
