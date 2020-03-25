import zBuilder.zMaya as mz
from maya import cmds
from maya import mel

from zBuilder.nodes.deformer import Deformer
import logging

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

    def populate(self, maya_node=None):
        """ This populates the node given a selection.

        Args:
            maya_node: Maya node to populate with.
        """

        maya_node = mz.check_maya_node(maya_node)

        self.name = maya_node
        self.type = cmds.objectType(maya_node)
        attr_list = mz.build_attr_list(maya_node)
        if self.EXTEND_ATTR_LIST:
            attr_list.extend(self.EXTEND_ATTR_LIST)
        attrs = mz.build_attr_key_values(maya_node, attr_list)
        self.attrs = attrs

        mesh = mz.get_association(maya_node)
        self.association = mesh

        if self.type == 'zSolver':
            self.solver = self
        else:
            solver = mel.eval('zQuery -t zSolver {}'.format(self.long_name))
            if solver:
                self.solver = self.builder.get_scene_items(name_filter=solver[0])[0]

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
        bad_meshes = mel.eval('zMeshCheck -iso -vb -me -mv -st -la -oe')
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
