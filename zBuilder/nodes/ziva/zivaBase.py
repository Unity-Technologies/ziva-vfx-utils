import zBuilder.zMaya as mz
import maya.cmds as mc
import maya.mel as mm

from zBuilder.nodes.deformer import Deformer
import logging

logger = logging.getLogger(__name__)


class Ziva(Deformer):
    """Base node for Ziva type nodes.

    extended from base to deal with maps and meshes and storing the solver.
    """
    EXTEND_ATTR_LIST = list()

    try:
        mc.loadPlugin('ziva', qt=True)
    except RuntimeError:
        pass

    def __init__(self, parent=None, builder=None, deserialize=None):
        Deformer.__init__(self, builder=builder, deserialize=deserialize, parent=parent)
        self.solver = None

    def populate(self, maya_node=None):
        """ This populates the node given a selection.

        Args:
            maya_node: Maya node to populate with.
        """

        maya_node = mz.check_maya_node(maya_node)

        self.name = maya_node
        self.type = mc.objectType(maya_node)
        attr_list = mz.build_attr_list(maya_node)
        if self.EXTEND_ATTR_LIST:
            attr_list.extend(self.EXTEND_ATTR_LIST)
        attrs = mz.build_attr_key_values(maya_node, attr_list)
        self.attrs = attrs
        self.mobject = maya_node

        mesh = mz.get_association(maya_node)
        self.association = mesh

        solver = mm.eval('zQuery -t zSolver {}'.format(self.name))
        if solver:
            self.solver = solver[0]

    @staticmethod
    def check_meshes(meshes):
        '''Checks meshes for potential problems

        This checks meshes for known problems that would prevent a body from 
        being created and raises an error if found.  This does not check
        problems that would cause a warning.

        Args:
            meshes (list): list of meshes to check

        Raises:
            StandardError: if any mesh fails a check
        '''
        mc.select(meshes, r=True)

        # this is all the required checks for a body.  If any of these fail the
        # check it will not create body.
        mc.select(meshes, r=True)
        bad_meshes = mm.eval('zMeshCheck -iso -vb -me -mv -st -la -oe')
        if bad_meshes:
            bad_meshes = [x.split('.')[0] for x in bad_meshes]
            bad_meshes = list(set(bad_meshes))

            if bad_meshes:
                error_message = ''':\n
                Meshes failed some required checks.
                Offending meshes: {}.
                Please Run Mesh Analysis in Ziva Tools menu on selected meshes.
                '''.format(str(bad_meshes))

                mc.select(bad_meshes)
                raise StandardError(error_message)
        else:
            return None
