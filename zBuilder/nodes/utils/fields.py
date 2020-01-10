from zBuilder.nodes.dg_node import DGNode
from maya import cmds


class Field(DGNode):
    """ The base node for the node functionality of all nodes
    """
    type = None
    TYPES = [
        'airField', 'dragField', 'gravityField', 'newtonField', 'radialField', 'turbulenceField',
        'uniformField', 'vortexField'
    ]
    """ The type of node. """

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
            results = factory[self.type](n=name)

        else:
            new_name = cmds.rename(name, self.name)

        self.set_maya_attrs(attr_filter=attr_filter)

    def populate(self, maya_node=None):
        super(Field, self).populate(maya_node=maya_node)
