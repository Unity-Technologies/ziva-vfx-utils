from zBuilder.nodes.base import BaseNode
import maya.cmds as mc


class ConstraintNode(BaseNode):
    """ The base node for the node functionality of all nodes
    """
    type = None
    TYPES = ['pointConstraint', 'orientConstraint']
    """ The type of node. """

    SEARCH_EXCLUDE = ['_class', '_attrs']
    """ List of attributes to exclude with a string_replace"""
    EXTEND_ATTR_LIST = list()
    """ List of maya attributes to add to attribute list when capturing."""

    def __init__(self, *args, **kwargs):
        BaseNode.__init__(self, *args, **kwargs)
        self.__constrained = None
        self.__targets = list()
        self.__upObject = None
        self.__ikHandle = None

        self.targets = list()
        self.constrained = list()

    def apply(self, *args, **kwargs):
        """ Builds the node in maya.  mean to be overwritten.
        """
        raise NotImplementedError

    def set_targets(self, targets_list):
        self.__targets = targets_list

    def get_targets(self):
        return self.__targets

    def set_constrained(self, constrained_object):
        self.__constrained = constrained_object

    def get_constrained(self):
        return self.__constrained

    def set_upObject(self, upObject):
        self.__upObject = upObject

    def get_upObject(self):
        return self.__upObject

    def build(self):
        build_constraint(self.name,
                         self.type,
                         self.get_targets(),
                         self.get_constrained(),
                         self.get_upObject())

    # def string_replace( self, search, replace) :
    #     super(ConstraintNode, self).string_replace( search, replace )
    #
    #     # do replace name of parent
    #     if self.get_upObject() != None:
    #         newUpObjectName = base.replace_longname( search, replace, self.get_upObject() )
    #         self.set_upObject( newUpObjectName )
    #
    #     newConstrainedName = base.replace_longname( search, replace, self.get_constrained() )
    #     self.set_constrained( newConstrainedName )
    #
    #     newTargets_list = list()
    #     for oldTargetName in self.get_targets():
    #         newTargetName = base.replace_longname( search, replace, oldTargetName )
    #         newTargets_list.append( newTargetName )
    #
    #     self.set_targets( newTargets_list )
    #

    def populate(self, constraint_name):
        super(ConstraintNode, self).populate(constraint_name)

        constraintData_dict = get_constraint_data(constraint_name)
        print constraintData_dict
        self.name = constraint_name
        self.type = constraintData_dict['type']
        self.set_targets(constraintData_dict['targets'])
        self.set_constrained(constraintData_dict['constrained'])

        if constraintData_dict['type'] == 'aimConstraint':
            self.set_upObject(constraintData_dict['upObject'])

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


def get_constraint_data(constraintName):
    constraintData_dict = dict()

    # Get generic stuff
    constraintData_dict['type'] = mc.objectType(constraintName)
    targetObjects_list = list()
    i = 0
    while not mc.listConnections('%s.target[%i].targetParentMatrix' % (
    constraintName, i)) == None:
        targetObjects_list.append(mc.listConnections(
            '%s.target[%i].targetParentMatrix' % (constraintName, i))[0])
        i += 1
    constraintData_dict['targets'] = targetObjects_list

    if constraintData_dict['type'] == 'aimConstraint':
        # up object
        worldUpObj = mc.listConnections(constraintName + '.worldUpMatrix')
        if not worldUpObj == None:
            constraintData_dict['upObject'] = worldUpObj[0]
        else:
            constraintData_dict['upObject'] = None

        # constrained object
        constraintData_dict['constrained'] = \
        mc.listConnections(constraintName + '.constraintRotateOrder')[0]

    if constraintData_dict['type'] == 'parentConstraint':

        # if there's no connections to rotations we check translations. 
        # TO DO this should probably support skipping axes
        print 'working on populating data for %s' % constraintName
        constrainedObject = mc.listConnections(
            constraintName + '.constraintRotate.constraintRotateX')
        if constrainedObject != None:
            constraintData_dict['constrained'] = constrainedObject[0]
        else:
            constraintData_dict['constrained'] = mc.listConnections(
                constraintName + '.constraintTranslate.constraintTranslateX')[0]

    if constraintData_dict['type'] == 'poleVectorConstraint':
        print 'working on populating data for %s' % constraintName
        constraintData_dict['constrained'] = \
        mc.listConnections(constraintName + '.constraintParentInverseMatrix')[0]

    return constraintData_dict


def build_constraint(constraintName, constraintType, targetObjects,
                     constrainedObject, upObject):
    if constraintType == 'aimConstraint':
        py_cmd = 'mc.aimConstraint( %s, \'%s\', worldUpObject=\'%s\', name=\'%s\', mo=True )' % (
        targetObjects, constrainedObject, upObject, constraintName)
        exec (py_cmd)

    if constraintType == 'parentConstraint':
        py_cmd = 'mc.parentConstraint( %s, \'%s\', name=\'%s\' )' % (
        targetObjects, constrainedObject, constraintName)
        exec (py_cmd)

    if constraintType == 'poleVectorConstraint':
        py_cmd = 'mc.poleVectorConstraint( %s, \'%s\', name=\'%s\' )' % (
        targetObjects, constrainedObject, constraintName)
        exec (py_cmd)
