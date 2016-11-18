import zBuilder.nodes.base as base
import zBuilder.nodeCollection as nc
import zBuilder.zMaya as mz


class AttributesSetup(nc.NodeCollection):
    def __init__(self):
        super(AttributesSetup,self).__init__()

    def retrieve_from_scene(self,selection):
    
        for sel in selection:
            nodeAttrList = mz.build_attr_list(sel)
            nodeAttrs = mz.build_attr_key_values(sel,nodeAttrList)


            node = base.BaseNode()
            node.set_name(sel)
            node.set_type(mz.get_type(sel))
            node.set_attrs(nodeAttrs)
            self.add_node(node)


    def apply(self):
        nodes = self.get_nodes()
        mz.set_attrs(nodes)

  

