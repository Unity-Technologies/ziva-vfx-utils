import os
import json
import logging

from .treeItem import *
from .groupNode import GroupNode
from zBuilder.nodes.base import Base

logger = logging.getLogger(__name__)

_version = 1

def serialize_tree_model(root_node):
    """
    Serializes tree items representing model of the ScenePanel2 TreeView.
    """
    tree_data = dict()
    tree_data["version"] = _version
    tree_nodes = dict()

    if _version == 1:
        # traverse nodes in DFS order and record each node
        if root_node.is_root_node(): # skip root node
            list_to_traverse = root_node.children[:]
        else:
            list_to_traverse = [root_node]
        while list_to_traverse:
            current_node = list_to_traverse.pop(0)
            path_to_node = current_node.get_tree_path()
            index = current_node.row()
            node_key = str(index) + str(path_to_node) # index is needed for key uniqueness

            if current_node._is_group_item():
                tree_nodes[node_key] ={
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
        tree_keys = sorted(serialized_data["nodes"].keys(), key=lambda x: (x.count("|"), int(x.split("|", 1)[0])))

        # initialize values for tree traversal
        current_level_count = 0
        current_index = 0
        previous_index = 0
        current_parent = None
        parent_key = "ROOT"
        parent_to_visit = [(root_node, parent_key)]

        # Since the keys are sorted by depth level and then by index,
        # we can run BFS on the tree with those keys based on level.
        # For each key node we process,
        # we store its children (only if "group" or "zSolverTransform") as parents for later processing by storing in "parent_to_visit".
        # We pick the next parent from "parent_to_visit" in two cases -
        # 1) when moving to the next level or
        # 2) processing child node of a different parent (on the same level if an index is equal or smaller).
        # Next we need to find the right parent from the "parent_to_visit" list.
        # We do that by comparing current node key and parent node key.
        # Once found, we remove the parent from "parent_to_visit" and add its children to the tree.
        for key in tree_keys:
            previous_level_count = current_level_count
            current_level_count = key.count("|")
            path_node_list = key.split("|")
            previous_index = current_index
            current_index = int(path_node_list[0])
            current_node = tree_nodes[key]
            # find next parent when moving to next level or next node in the same level
            if current_level_count > previous_level_count or current_index <= previous_index:
                # Finding the right parent from the list, a group node might not have any child
                for parent in parent_to_visit:
                    parent_key_tuple = parent
                    current_parent = parent_key_tuple[0]
                    parent_key = parent_key_tuple[1]
                    # found parent
                    if key.split("|")[1:-1] == parent_key.split("|")[1:]:
                        parent_to_visit.remove(parent)
                        break

            if current_node["type"] == "group":
                child_node = TreeItem(current_parent, GroupNode(path_node_list[-1]))
            else:
                child_base_data = Base()
                child_base_data.name = current_node["name"]
                child_base_data.type = current_node["type"]
                child_node = TreeItem(current_parent, child_base_data)
                child_node.pin_state = current_node["pin_state"]
            # a "group" or a "zSolverTransform" node can be a parent node
            if current_node["type"] in {"group", "zSolverTransform"}:
                parent_to_visit.append((child_node, key))

    return root_node


def string_to_json(data):
    """Returns json data from string.
    """
    return json.loads(data)


def is_save_serialized_data_to_zsolver_plug():
    """Returns based on value of "ZIVA_ZBUILDER_DONT_SAVE_SCENE_PANEL_DATA" environment variable.
    """
    if "ZIVA_ZBUILDER_DONT_SAVE_SCENE_PANEL_DATA" in os.environ:
        return False
    else:
        return True
