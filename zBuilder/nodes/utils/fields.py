from zBuilder.nodes.dg_node import DGNode
import maya.cmds as mc


class Field(DGNode):
    """ The base node for the node functionality of all nodes
    """
    type = None
    TYPES = [
        'airField', 'dragField', 'gravityField', 'newtonField', 'radialField', 'turbulenceField',
        'uniformField', 'vortexField'
    ]
    """ The type of node. """

    def __init__(self, *args, **kwargs):
        DGNode.__init__(self, *args, **kwargs)

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
        if not mc.objExists(name):
            # clearing the selection before we create anything as the
            # selection is used to assign it to something.
            mc.select(cl=True)
            factory = {
                'airField': mc.air,
                'dragField': mc.drag,
                'gravityField': mc.gravity,
                'newtonField': mc.newton,
                'radialField': mc.radial,
                'turbulenceField': mc.turbulence,
                'uniformField': mc.uniform,
                'vortexField': mc.vortex
            }
            results = factory[self.type](n=name)
            self.mobject = name

        else:
            new_name = mc.rename(name, self.name)
            self.mobject = new_name

        self.set_maya_attrs(attr_filter=attr_filter)

    def populate(self, maya_node=None):
        super(Field, self).populate(maya_node=maya_node)
