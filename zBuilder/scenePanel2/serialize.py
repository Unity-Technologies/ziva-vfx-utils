import os
import json
import logging

from .treeItem import TreeItem, is_group_item
from .groupNode import GroupNode
from ..nodes.base import Base

logger = logging.getLogger(__name__)

_version = 1  # Serialization format version


def is_serialize_data_to_zsolver_node():
    """ Helper function to determine whether to save Scene Panel data to zSolver plug.
    Since the saving process requires de-select first, it may cause un-wanted result.
    Provide the ZIVA_ZBUILDER_DONT_SAVE_SCENE_PANEL_DATA env var to give users option
    to stop proceed the saving process.
    """
    return "ZIVA_ZBUILDER_DONT_SAVE_SCENE_PANEL_DATA" not in os.environ


class PendingTreeEntry(object):
    def __init__(self, *args):
        """ Overloaded construtor
        """
        if len(args) == 1:
            # Take TreeItem as input argument
            tree_item = args[0]
            assert isinstance(tree_item, TreeItem)
            self._tree_path = tree_item.get_tree_path()
            self._row_index = tree_item.row()
            self._node_type = tree_item.data.type
            self._node_data = {} if is_group_item(tree_item) else {
                "pin_state": tree_item.pin_state,
                "name": tree_item.data.long_name,  # Store Maya DGNode long_name
            }
        else:
            # Take json data as input arguments
            self._tree_path = args[0]
            self._row_index = args[1]
            self._node_type = args[2]
            self._node_data = args[3]

    @property
    def tree_path(self):
        return self._tree_path

    @property
    def dir_tree_path(self):
        """ Return tree path excludes last segement.
        E.g., "|a|b|c" --> "|a|b"
        """
        return self._tree_path.rsplit("|", 1)[0]

    @property
    def group_name(self):
        assert "group" == self._node_type
        return self._tree_path.split("|")[-1]

    @property
    def depth(self):
        return self._tree_path.count("|")

    @property
    def row_index(self):
        return self._row_index

    @property
    def node_type(self):
        return self._node_type

    @property
    def node_data(self):
        return self._node_data

    def to_json_object(self):
        return [self._tree_path, self._row_index, self._node_type, self._node_data]


def flatten_tree(root_node):
    """ Flatten a TreeItem tree which represents model of the ScenePanel2 TreeView,
    to a PendingTreeEntry list.
    It traverses nodes in DFS order and append each node to list.
    At the end, it sorts the list according to tree node depth(primary) and row index(secondary).

    Returns:
        PendingTreeEntry list
    """
    tree_entry_list = []
    list_to_traverse = []
    if root_node.is_root_node():  # skip root node
        list_to_traverse.extend(root_node.children)
    else:
        list_to_traverse.append(root_node)
    while list_to_traverse:
        current_node = list_to_traverse.pop(0)
        tree_entry_list.append(PendingTreeEntry(current_node))
        # Add child items, if any
        if current_node.children:
            list_to_traverse.extend(current_node.children)
    # Sort entry firstly by tree item depth, then by tree item index.
    # Refer to construct_tree() for details.
    tree_entry_list.sort(key=lambda entry: (entry.depth, entry.row_index))
    return tree_entry_list


def to_json_string(tree_entry_list):
    """ Convert dict of PendingTreeEntry list and version number to a json string
    """
    data = dict()
    data["version"] = _version  # Always serialize the latest format version
    data["nodes"] = [entry.to_json_object() for entry in tree_entry_list]
    return json.dumps(data)


def to_json_file(tree_entry_list, file_path):
    """ Convert dict of PendingTreeEntry list and version number to a json file.
    This is an internal helper function for debugging.
    """
    data = dict()
    data["version"] = _version  # Set the version you want to test
    data["nodes"] = [entry.to_json_object() for entry in tree_entry_list]
    with open(file_path, "w") as output_file:
        json.dump(data, output_file, sort_keys=True, indent=4, separators=(",", ": "))
    logger.debug("Finished writing serialized data to {}.".format(file_path))


def to_tree_entry_list(json_data, version=None):
    """ Convert json string to PendingTreeEntry list.

    Args:
        json_data(str, list): The input Json data.
            It is string type in normal case and is list type for internal use.
        version(int): Specified Json data version number, for internal use.

    Returns:
        PendingTreeEntry list
    """
    # Normal workflow, json string load from solverTM plug
    if isinstance(json_data, str):
        dict_data = json.loads(json_data)
        if dict_data["version"] == 1:
            # Create entry data according to version number
            tree_entries = [PendingTreeEntry(*entry) for entry in dict_data["nodes"]]
            return tree_entries

    # Internal workflow for unit test, manually constructed json string
    if isinstance(json_data, list):
        if version == 1:
            # Create entry data according to version number
            tree_entries = [PendingTreeEntry(*entry) for entry in json_data]
            return tree_entries

    raise RuntimeError("Unhandled Json data or invalid version number.")


def construct_tree(tree_entry_list):
    """ Construct a TreeItem tree according to PendingTreeEntry list
    """
    # set root node
    root_base_node = Base()
    root_base_node.name = "ROOT"
    root_node = TreeItem(None, root_base_node)

    # initialize values for tree traversal
    curr_entry_depth = 0
    curr_entry_index = 0
    prev_entry_index = 0
    curr_parent_item = None
    parent_to_visit = [(root_node, "ROOT")]

    # The tree entries are sorted firstly by depth then by row index,
    # we can run BFS on the tree with those keys based on depth.
    for entry in tree_entry_list:
        prev_entry_depth = curr_entry_depth
        curr_entry_depth = entry.depth
        prev_entry_index = curr_entry_index
        curr_entry_index = entry.row_index
        curr_entry_data = entry.node_data

        # We pick the next parent from "parent_to_visit" when
        # 1. Moving to the next depth
        # 2. Processing other entry from a different parent, i.e.,
        #    on the same depth but row index <= current entry
        if curr_entry_depth > prev_entry_depth or curr_entry_index <= prev_entry_index:
            # Finding the right parent from the list.
            # Note: Group node might not have any child.
            for parent_item in parent_to_visit:
                curr_parent_item, curr_parent_tree_path = parent_item
                # Next we need to find the right parent from the "parent_to_visit" list.
                # We do that by comparing current node key and parent node key.
                if entry.dir_tree_path == curr_parent_tree_path:
                    # Once found, remove the parent from "parent_to_visit"
                    # and add its children to the tree.
                    parent_to_visit.remove(parent_item)
                    break

        node_type = entry.node_type
        if node_type == "group":
            item = TreeItem(curr_parent_item, GroupNode(entry.group_name))
        else:
            zbuilder_node = Base()
            zbuilder_node.name = curr_entry_data["name"]
            zbuilder_node.type = node_type
            item = TreeItem(curr_parent_item, zbuilder_node)
            item.pin_state = curr_entry_data["pin_state"]

        # Save the container node to the "parent_to_visit" list for later processing
        container_node_type = ("group", "zSolverTransform")
        if node_type in container_node_type:
            parent_to_visit.append((item, entry.tree_path))

    return root_node
