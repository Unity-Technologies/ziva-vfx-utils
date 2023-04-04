from maya import cmds
from zBuilder.utils.mayaUtils import FIELD_TYPES
from ..dg_node import DGNode


class Field(DGNode):

    type = None

    # The TYPES is required by find_class() function,
    # to correctly build Field node instances.
    TYPES = FIELD_TYPES

    def do_build(self, *args, **kwargs):
        """ Builds the Maya field nodes in the scene.
        """

        if not cmds.objExists(self.name):
            # clearing the selection before we create anything as the
            # selection is used to assign it to something.
            cmds.select(cl=True)
            factory = {
                'airField': cmds.air,
                'dragField': cmds.drag,
                'gravityField': cmds.gravity,
                'newtonField': cmds.newton,
                'radialField': cmds.radial,
                'turbulenceField': cmds.turbulence,
                'uniformField': cmds.uniform,
                'vortexField': cmds.vortex
            }
            factory[self.type](n=self.name)

        self.set_maya_attrs()

    def populate(self, maya_node=None):
        super(Field, self).populate(maya_node=maya_node)
