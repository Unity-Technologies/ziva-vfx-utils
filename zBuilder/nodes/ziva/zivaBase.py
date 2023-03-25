import logging

from collections import defaultdict
from maya import cmds
from zBuilder.utils.commonUtils import get_first_element
from zBuilder.utils.mayaUtils import build_attr_list, build_attr_key_values, get_type
from zBuilder.utils.vfxUtils import get_association
from ..deformer import Deformer

logger = logging.getLogger(__name__)


class Ziva(Deformer):
    """Base node for Ziva type nodes.

    extended from base to deal with maps and meshes and storing the solver.
    """
    EXTEND_ATTR_LIST = list()

    try:
        cmds.loadPlugin('ziva', qt=True)
    except RuntimeError:
        pass

    def __init__(self, parent=None, builder=None):
        super(Ziva, self).__init__(parent=parent, builder=builder)
        self.solver = None
        self.connections = defaultdict(list)

    def populate(self, maya_node=None):
        """ This populates the node given a selection.

        Args:
            maya_node: Maya node to populate with.
        """
        # TODO:
        # this populate is actually duplicating functionality from it's superclass Deformer.populate()
        # It is currently in here because removing it and calling super populate()
        # was causing errors that made no sense.
        # The plan is to revert this like so and re-visit it with this ticket:
        # https://zivadynamics.atlassian.net/browse/VFXACT-689

        maya_node = get_first_element(maya_node)

        self.name = maya_node
        self.type = get_type(maya_node)
        attr_list = build_attr_list(maya_node)
        if self.EXTEND_ATTR_LIST:
            attr_list.extend(self.EXTEND_ATTR_LIST)
        attrs = build_attr_key_values(maya_node, attr_list)
        self.attrs = attrs

        mesh = get_association(maya_node)
        self.association = mesh

        if self.type == 'zSolver':
            self.solver = self
        else:
            solver = cmds.zQuery(self.long_name, t='zSolver')
            if solver:
                self.solver = self.builder.get_scene_items(name_filter=solver[0])[0]

    def post_populate(self):
        '''
        This is a callback function that can be customized by each Ziva ZVX node.
        It is called right after the the populate() function returns successfully.
        This overrides DGNode post_populate function.
        '''
        self.retrieve_connections()

    def do_post_build(self):
        '''
        This is a callback function that can be customized by each Ziva ZVX node.
        It is called right after the build() function.
        This overrides DGNode do_post_build function.
        '''
        self.build_connections()

    def retrieve_connections(self):
        """
        The ziva rig is connected to non-ziva nodes in the scene.  This will collect them and store them 
        in the object for later retrieval.  It stores them as a list like so

        ['obj1.translateX', 'fiber1.excitation']
        
        This function requires calling mayaUtils.build_attr_key_values() in advance.
        """
        for attr in self.attrs.keys():
            connections = cmds.listConnections(self.name + '.' + attr,
                                               destination=False,
                                               skipConversionNodes=True,
                                               plugs=True,
                                               connections=True)
            if connections:
                self.connections[connections[0]].append(connections[1])

    def build_connections(self):
        """
        Restoring previously saved connections.
        """
        if not hasattr(self, 'connections'):
            return

        for item in self.connections:
            if cmds.objExists(item) and cmds.objExists(self.connections[item][0]):
                if not cmds.isConnected(self.connections[item][0], item):
                    cmds.connectAttr(self.connections[item][0], item, f=True)
            else:
                logger.info("Missing object for connection {} connection not restored to {}".format(
                    self.connections[item], item))

    @staticmethod
    def check_meshes(meshes):
        '''Checks meshes for potential problems

        This checks meshes for known problems that would prevent a body from 
        being created and raises an error if found.  This does not check
        problems that would cause a warning.

        Args:
            meshes (list): list of meshes to check

        Raises:
            Exception: if any mesh fails a check
        '''
        cmds.select(meshes, r=True)

        # this is all the required checks for a body.  If any of these fail the
        # check it will not create body.
        cmds.select(meshes, r=True)
        bad_meshes = cmds.zMeshCheck(iso=True, vb=True, me=True, mv=True, st=True, la=True, oe=True)
        if bad_meshes:
            bad_meshes = [x.split('.')[0] for x in bad_meshes]
            bad_meshes = list(set(bad_meshes))

            if bad_meshes:
                error_message = ''':\n
                Meshes failed some required checks.
                Offending meshes: {}.
                Please Run Mesh Analysis in Ziva Tools menu on selected meshes.
                '''.format(str(bad_meshes))

                cmds.select(bad_meshes)
                raise Exception(error_message)
        else:
            return None

    def check_parameter_name(self):
        # This is to prevent a specific case that causes string_replace
        # to not function.  When you use string_replace to mirror and the ziva
        # elements in the scene do not have a side deliminator.

        # This checks name of node (self.name) against the name of the node
        # stored in the .parameters map .name.  If they are not the same it
        # updates the map name with correct name.

        # It also fixes the linkage between newly created scene items after
        # deepcopy builder operation.

        for item in self.parameters['map']:
            parameter_name = item.name.split('.')[0]
            if parameter_name != self.name:
                item.string_replace(parameter_name, self.name)
