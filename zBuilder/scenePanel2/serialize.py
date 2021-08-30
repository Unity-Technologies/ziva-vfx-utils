import json
import logging

from .treeItem import *
from ..uiUtils import is_zsolver_node

logger = logging.getLogger(__name__)

_version = 1

def serialize_tree_model(root_node):
    """
    Serializes tree items representing model of the ScenePanel2 TreeView 
    """
    tree_data = dict()
    tree_data["version"] = _version
    tree_nodes = dict()

    if _version == 1:
        # traverse nodes in DFS order and record each node
        list_to_traverse = root_node.children[:]
        while list_to_traverse:
            current_node = list_to_traverse.pop(0)
            path_to_node = current_node.get_tree_path()
            index = current_node.row()
            node_key = str(index) + str(path_to_node) # index is needed for key uniqueness

            if current_node._is_group_item():
                tree_nodes[node_key] ={
                                           "index": index,
                                           "name": current_node.data.name,
                                           "type": current_node.data.type}
            elif is_zsolver_node(current_node.data):
                tree_nodes[node_key] = {
                                            "index": index,
                                            "name": current_node.data.name,
                                            "type": current_node.data.type,
                                            "long_name": current_node.data.long_name}
            else:
                tree_nodes[node_key] = {
                                            "index": index,
                                            "pin_state": current_node.pin_state,
                                            "name": current_node.data.name,
                                            "type": current_node.data.type,
                                            "long_name": current_node.data.long_name}
            # add children
            if current_node.children:
                list_to_traverse.extend(current_node.children)

    tree_data["nodes"] = tree_nodes
    json_to_string(tree_data)
    return tree_data

def json_to_string(data):
    """Returns json data as a string.
    """
    return json.dumps(data)


def write_serialized_data_to_file(data, file_path):
    """Writes json data to a given file.
    """
    logger.debug("Serializing Scene Panel2 tree structure to {}.".format(file_path))

    try:
        with open(file_path, 'w') as output_file:
                json.dump(data,
                          output_file,
                          sort_keys=True,
                          indent=4,
                          separators=(',', ': '))
        logger.debug("Finished writing serialized data to {}.".format(file_path))
    except:
        logger.error("Failed to write serialized data to {}.".format(file_path))
