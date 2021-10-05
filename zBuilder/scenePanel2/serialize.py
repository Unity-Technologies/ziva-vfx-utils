import os
import json
import logging

from .treeItem import TreeItem, is_group_item, build_scene_panel_tree
from .groupNode import GroupNode
from ..uiUtils import zGeo_UI_node_types
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
    """ Data structure for merging zBuilder node and tree view data.
    """
    def __init__(self, *args):
        """ Overloaded construtor for different data types.
        """
        # member variable for merge_tree_data() and construct_tree().
        # Not for serialization.
        self._zBuilder_node = None

        if len(args) == 1:
            assert isinstance(args[0], TreeItem)
            # Create entry through TreeItem
            tree_item = args[0]
            self._tree_path = tree_item.get_tree_path()
            self._node_type = tree_item.data.type
            self._node_data = {} if is_group_item(tree_item) else {
                "pin_state": tree_item.pin_state,
                "name": tree_item.data.long_name,  # Store Maya DGNode long_name
            }
            return

        # Create entry with Json data and version number
        version = args[-1]
        assert isinstance(
            version, int) and version > 0, "Version must be an integer. Got: {}".format(version)
        self._tree_path = args[0]
        self._node_type = args[1]
        self._node_data = args[2]

    @property
    def tree_path(self):
        assert self._tree_path
        return self._tree_path

    @property
    def dir_tree_path(self):
        """ Return tree path excludes last segement.
        E.g., "|a|b|c" --> "|a|b"
        """
        assert self._tree_path
        return self._tree_path.rsplit("|", 1)[0]

    @property
    def group_name(self):
        assert "group" == self._node_type
        return self._tree_path.split("|")[-1]

    @property
    def depth(self):
        assert self._tree_path
        return self._tree_path.count("|")

    @property
    def node_type(self):
        return self._node_type

    @property
    def node_data(self):
        return self._node_data

    @property
    def long_name(self):
        assert "group" != self._node_type, "Only zBuilder node has long name."
        return self._node_data["name"]

    @property
    def zBuilder_node(self):
        assert "group" != self._node_type, "Only zBuilder node type can be called."
        return self._zBuilder_node

    @zBuilder_node.setter
    def zBuilder_node(self, node):
        assert "group" != self._node_type, "Only zBuilder node type entry can be set."
        self._zBuilder_node = node

    def to_json_object(self):
        assert self._tree_path
        assert self._node_type
        return [self._tree_path, self._node_type, self._node_data]


def flatten_tree(root_node):
    """ Flatten a TreeItem tree which represents model of the ScenePanel2 TreeView,
    to a PendingTreeEntry list.
    The return entry list is organized in DFS form.
    The construct_tree() can retore the return value to tree structure.

    Returns:
        PendingTreeEntry list
    """
    node_stack = []
    if root_node.is_root_node():
        # root node is not needed, append its children copy in reverse order
        node_stack.extend(list(reversed(root_node.children)))
    else:
        node_stack.append(root_node)

    tree_entry_list = []
    while node_stack:
        current_node = node_stack.pop()
        tree_entry_list.append(PendingTreeEntry(current_node))
        # Append child node copy in reverse order, if any
        if current_node.children:
            node_stack.extend(list(reversed(current_node.children)))

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
        json_data_version = dict_data["version"]
        # Create entry data according to version number
        # TODO: Since Python 3.5, Additional Unpacking Generalizations is valid, see
        # https://stackoverflow.com/questions/12720450/unpacking-arguments-only-named-arguments-may-follow-expression
        # Once switch to Python 3 only, change this grammar
        tree_entries = [
            PendingTreeEntry(*(entry + [json_data_version])) for entry in dict_data["nodes"]
        ]
        return tree_entries

    # Internal workflow for unit test, manually constructed json string
    # The version number is manually specified to test version handling.
    if isinstance(json_data, list):
        assert version, "Version number is not set."
        assert isinstance(version, int), "Version is not an integer."
        tree_entries = [PendingTreeEntry(*(entry + [version])) for entry in json_data]
        return tree_entries

    raise RuntimeError(
        "Unhandled Json data and/or invalid version number: input data = {}, version = {}".format(
            json_data, version))


def construct_tree(tree_entry_list, mock_zBuilder_node):
    """ Construct a TreeItem tree according to PendingTreeEntry list

    Args:
        tree_entry_list: PendingTreeEntry list whose elements are must arranged in DFS order.
            Otherwise will cause unexpected result.
            The DFS form data are generated by flatten_tree() function.
        mock_zBuilder_node(bool): Create a mock zBuilder node for unit test, if True.

    Returns:
        TreeItem tree.
    """
    def create_tree_item(parent, entry):
        """ Helper function to create TreeItem instance.
        """
        if entry.node_type == "group":
            item = TreeItem(parent, GroupNode(entry.group_name))
        else:
            if mock_zBuilder_node:
                zbuilder_node = Base()
                zbuilder_node.name = entry.long_name
                zbuilder_node.type = entry.node_type
                item = TreeItem(parent, zbuilder_node)
            else:
                item = TreeItem(parent, entry.zBuilder_node)
            item.pin_state = entry.node_data["pin_state"]
        return item

    def get_parent_item(item, level):
        """ Helper function to get parent of given TreeItem object.
        """
        assert level > 0
        assert item.parent
        cur_item = item
        while level > 0 and cur_item.parent:
            cur_item = cur_item.parent
            level -= 1
        return cur_item

    assert tree_entry_list
    root_item = None  # the return value
    last_entry = None  # last processed tree entry
    last_item = None  # TreeItem created based on last_entry
    for entry in tree_entry_list:
        if last_entry is None:
            # root node
            assert last_item is None
            root_item = create_tree_item(None, entry)
            last_item = root_item
            last_entry = entry
            continue

        depth_diff = entry.depth - last_entry.depth
        if depth_diff > 0:
            assert depth_diff == 1, "Current entry {} depth large than last entry {} depth by 1.".format(
                entry.tree_path, last_entry.tree_path)
            last_item = create_tree_item(last_item, entry)
        elif depth_diff == 0:
            last_item = create_tree_item(get_parent_item(last_item, 1), entry)
        else:  # depth_diff < 0
            last_item = create_tree_item(get_parent_item(last_item, -depth_diff + 1), entry)
        last_entry = entry

    return root_item


def merge_tree_data(zBuilder_node_list, tree_view_entry_list):
    """ Merge data between zBuilder parse result and tree_entry_list.

    Args:
        zBuilder_node_list: zBuilder node retrieved from current scene.
            They need to belong to the same solver.
        tree_entry_list: PendingTreeEntry list from tree view,
            or deserialized from solverTM plug.

    Return:
        Merged TreeItem tree.
    """
    assert zBuilder_node_list
    if not tree_view_entry_list:
        # zGeo Tree View has no data, create the tree from zBuilder node list
        solverTM = list(filter(lambda node: node.type == "zSolverTransform", zBuilder_node_list))[0]
        return build_scene_panel_tree(solverTM,
                                      zGeo_UI_node_types + ["zSolver", "zSolverTransform"])[0]

    # TODO: Merge zBuilder node list and tree view entry list

    # Map zBuilder nodes to tree enties
    node_dict = {node.long_name: node for node in zBuilder_node_list}
    for entry in tree_view_entry_list:
        if entry.node_type != "group":
            entry.zBuilder_node = node_dict[entry.long_name]
    return construct_tree(tree_view_entry_list, False)
