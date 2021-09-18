import os
import json
import logging

from .treeItem import TreeItem, is_group_item
from .groupNode import GroupNode
from ..nodes.base import Base

logger = logging.getLogger(__name__)

_version = 1  # Serialization format version


def serialize_tree_model(root_node):
    """ Serializes tree items representing model of the ScenePanel2 TreeView.
    Traverse nodes in DFS order and record each node.

    Returns:
        List of tree nodes (tree item path, row index, item type, node data) tuple
    """
    tree_nodes = []
    list_to_traverse = []
    if root_node.is_root_node():  # skip root node
        list_to_traverse.extend(root_node.children)
    else:
        list_to_traverse.append(root_node)
    while list_to_traverse:
        current_node = list_to_traverse.pop(0)
        # Append entry
        entry = [
            current_node.get_tree_path(),
            current_node.row(),
            current_node.data.type,
            {} if is_group_item(current_node) else {
                "pin_state": current_node.pin_state,
                "name": current_node.data.long_name,  # Store Maya DGNode long_name
            }
        ]
        tree_nodes.append(entry)
        # Add child items, if any
        if current_node.children:
            list_to_traverse.extend(current_node.children)
    # Sort tree_nodes firstly by tree item level, then by tree item index
    # Refer to deserialize_tree_model() for details.
    tree_nodes.sort(key=lambda x: (x[0].count("|"), x[1]))
    return tree_nodes


def to_json_string(tree_nodes):
    """ Returns json data as a string.
    """
    data = dict()
    data["version"] = _version  # Always serialize the latest format version
    data["nodes"] = tree_nodes
    return json.dumps(data)


def to_json_file(tree_nodes, file_path):
    """ Writes json data to a given file.
    This is an internal helper function for debugging.
    """
    data = dict()
    data["version"] = _version  # Set the version you want to test
    data["nodes"] = tree_nodes
    with open(file_path, "w") as output_file:
        json.dump(data, output_file, sort_keys=True, indent=4, separators=(",", ": "))
    logger.debug("Finished writing serialized data to {}.".format(file_path))


def deserialize_tree_model(tree_nodes, version):
    """ De-serializes data to represent model of ScenePanel2 TreeView
    """
    # set root node
    root_base_node = Base()
    root_base_node.name = "ROOT"
    root_node = TreeItem(None, root_base_node)

    if version == 1:
        # initialize values for tree traversal
        current_level_count = 0
        current_index = 0
        previous_index = 0
        current_parent_node = None
        parent_to_visit = [(root_node, "ROOT")]

        # Since the tree nodes are sorted firstly by depth level then by index,
        # we can run BFS on the tree with those keys based on level.
        # For each node we process, we store its children (only if "group" or "zSolverTransform")
        # as parents for later processing by storing in "parent_to_visit".
        # We pick the next parent from "parent_to_visit" in two cases:
        # 1) when moving to the next level or
        # 2) processing child node of a different parent (on the same level if an index is equal or smaller).
        # Next we need to find the right parent from the "parent_to_visit" list.
        # We do that by comparing current node key and parent node key.
        # Once found, we remove the parent from "parent_to_visit" and add its children to the tree.
        for entry in tree_nodes:
            # Assign triplet value to each variable
            tree_item_path, row_index, node_type, node_data = entry
            previous_level_count = current_level_count
            current_level_count = tree_item_path.count("|")
            path_node_list = tree_item_path.split("|")
            previous_index = current_index
            current_index = row_index
            current_node = node_data
            # find next parent when moving to next level or next node in the same level
            if current_level_count > previous_level_count or current_index <= previous_index:
                # Finding the right parent from the list, a group node might not have any child
                for parent_entry in parent_to_visit:
                    current_parent_node, current_parent_item_path = parent_entry
                    # found parent
                    if tree_item_path.split("|")[1:-1] == current_parent_item_path.split("|")[1:]:
                        parent_to_visit.remove(parent_entry)
                        break

            if node_type == "group":
                child_node = TreeItem(current_parent_node, GroupNode(path_node_list[-1]))
            else:
                child_base_data = Base()
                child_base_data.name = current_node["name"]
                child_base_data.type = node_type
                child_node = TreeItem(current_parent_node, child_base_data)
                child_node.pin_state = current_node["pin_state"]

            container_node_type = ("group", "zSolverTransform")
            if node_type in container_node_type:
                parent_to_visit.append((child_node, tree_item_path))

    return root_node


def string_to_json(data):
    """ Returns json data from string.
    """
    return json.loads(data)


def is_serialize_data_to_zsolver_node():
    """ Helper function to determine whether to save Scene Panel data to zSolver plug.
    Since the saving process requires de-select first, it may cause un-wanted result.
    Provide the ZIVA_ZBUILDER_DONT_SAVE_SCENE_PANEL_DATA env var to give users option
    to stop proceed the saving process.
    """
    return not ("ZIVA_ZBUILDER_DONT_SAVE_SCENE_PANEL_DATA" in os.environ)
