import json
import logging

from .treeItem import *
from .groupNode import GroupNode
from zBuilder.nodes.base import Base

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
                                           "name": current_node.data.name,
                                           "type": current_node.data.type}
            else:
                tree_nodes[node_key] = {
                                            "pin_state": current_node.pin_state,
                                            # since long name cannot be set, we store "long_name" as name
                                            "name": current_node.data.long_name,
                                            "type": current_node.data.type}
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


def deserialize_tree_model(serialized_data):
    """
    De-serializes data to represent model of ScenePanel2 TreeView
    """
    tree_nodes = serialized_data["nodes"]

    # set root node
    root_base_node = Base()
    root_base_node.name = "ROOT"
    root_node = TreeItem(None, root_base_node)

    if serialized_data["version"] == 1:
        # sort keys by tree item level, and then by tree item index
        tree_keys = list(serialized_data["nodes"].keys()) # need to use explicit conversion for python 3
        tree_keys.sort(key=lambda x: (x.count("|"), int(x.split("|", 1)[0])))

        # initialize values for tree traversal
        current_level_count = 0
        current_index = 0
        previous_index = 0
        current_parent = None
        parent_key = "ROOT"
        parent_to_visit = [(root_node, parent_key)]

        for key in tree_keys:
            previous_level_count = current_level_count
            current_level_count = key.count("|")

            # Since the keys are sorted by depth level and then by index, we can run BFS
            # on the tree with those keys and store parents that we need to process next.
            # We pop the next parent to add child once we have traversed the previous level
            # or found children of a node on the same level by comparing index which are
            # sorted for each node. Then we compare key with parent key to make sure we found
            # the right parent.
            path_node_list = key.split("|")
            previous_index = current_index
            current_index = int(path_node_list[0])
            current_node = tree_nodes[key]
            # processing children of next level from the tree and finding right parent.
            # A group node might not have any child
            if current_level_count > previous_level_count or current_index <= previous_index:
                while(parent_to_visit):
                    parent_key_tuple = parent_to_visit.pop(0)
                    current_parent = parent_key_tuple[0]
                    parent_key = parent_key_tuple[1]
                    if key.split("|")[1:-1] == parent_key.split("|")[1:]:
                        break

            if current_node["type"] == "group":
               child_node = TreeItem(current_parent, GroupNode(path_node_list[-1]))
               # a GroupNode can be a parent
               parent_to_visit.append((child_node, key))
            else:
                # TODO: resolve conflict with loaded tree here
                child_base_data = Base()
                child_base_data.name = path_node_list[-1]
                child_base_data.type = current_node["type"]
                child_node = TreeItem(current_parent, child_base_data)
                child_node.pin_state = current_node["pin_state"]
                # a "zSolverTransform" node can be a parent node
                if current_node["type"] == "zSolverTransform":
                    parent_to_visit.append((child_node, key))
    return root_node


def string_to_json(data):
    """Returns json data from string.
    """
    return json.loads(data)
