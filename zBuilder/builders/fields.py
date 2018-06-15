from zBuilder.builder import Builder
import maya.cmds as mc
import zBuilder.zMaya as mz

class Fields(Builder):
    """Storing maya fields.
    """

    def __init__(self):
        Builder.__init__(self)

        self.acquire = ['airField','dragField','gravityField','newtonField',
        'radialField','turbulenceField','uniformField','vortexField']

    @Builder.time_this
    def retrieve_from_scene(self, *args, **kwargs):
        selection = mz.parse_maya_node_for_selection(args)
        
        tmp = list()
        tmp.extend([x for x in selection if mc.objectType(x) in self.acquire])

        for item in tmp:
            parameter = self.node_factory(item)
            self.bundle.extend_scene_items(parameter)
        self.stats()

    @Builder.time_this
    def build(self):
        parameters = self.get_scene_items()
        for parameter in parameters:
            parameter.build()
