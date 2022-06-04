from functools import partial
from PySide2 import QtWidgets
from zBuilder.nodes.base import Base
from ..uiUtils import ProximityWidget

attrs_clipboard = {}  # clipboard for copied attributes
maps_clipboard = None  # clipboard for the maps. This is either a zBuilder Map object or None.


def append_attr_actions(parent, menu, node):
    """ Append attribute actions to the menu.
    Args:
        menu (QMenu): menu to add option to
        node (zBuilder object): zBuilder.nodes object
    """

    def copy_attrs(node):
        # update the model in case maya updated
        node.get_maya_attrs()
        global attrs_clipboard
        attrs_clipboard = {}
        attrs_clipboard[node.type] = node.attrs.copy()

    def paste_attrs(node):
        # type: (zBuilder.whatever.Base) -> None
        """
        Paste the attributes from the clipboard onto given node.
        @pre The node's type has an entry in the clipboard.
        """
        assert isinstance(
            node, Base), "Precondition violated: argument needs to be a zBuilder node of some type"
        assert node.type in attrs_clipboard, "Precondition violated: node type is not in the clipboard"
        orig_node_attrs = attrs_clipboard[node.type]
        assert isinstance(orig_node_attrs,
                          dict), "Invariant violated: value in attrs clipboard must be a dict"
        # Here, we expect the keys to be the same on node.attrs and orig_node_attrs.
        # We probably don't need to check, but we could:
        assert set(node.attrs) == set(
            orig_node_attrs
        ), "Invariant violated: copied attribute list do not match paste-target's attribute list"

        node.attrs = orig_node_attrs.copy()
        # Note: given the above invariant, this should be the same as node.attrs.update(orig_node_attrs)
        node.set_maya_attrs()

    copy_attrs_action = QtWidgets.QAction(parent)
    copy_attrs_action.setText("Copy")
    copy_attrs_action.triggered.connect(partial(copy_attrs, node))

    paste_attrs_action = QtWidgets.QAction(parent)
    paste_attrs_action.setText("Paste")
    paste_attrs_action.triggered.connect(partial(paste_attrs, node))
    # only enable "paste" IF it is same type as what is in buffer
    paste_attrs_action.setEnabled(node.type in attrs_clipboard)

    attrs_menu = menu.addMenu("Attributes")
    attrs_menu.addAction(copy_attrs_action)
    attrs_menu.addAction(paste_attrs_action)


def append_map_actions(parent, menu, menu_name, node, map_index):
    """ Append map actions to the menu.
    Args:
        menu (QMenu): menu to add option to
        node (zBuilder object): zBuilder.nodes object
        map_index (int): map index. 0 for source map 1 for target/endPoints map
    """
    map_menu = menu.addMenu(menu_name)

    paint_action = QtWidgets.QAction(parent)
    paint_action.setText("Paint")
    paint_action.triggered.connect(node.parameters["map"][map_index].open_paint_tool)
    map_menu.addAction(paint_action)

    def invert_weights(node, map_index):
        node.parameters["map"][map_index].retrieve_values()
        map_ = node.parameters["map"][map_index]
        map_.invert()
        map_.apply_weights()

    invert_action = QtWidgets.QAction(parent)
    invert_action.setText("Invert")
    invert_action.triggered.connect(partial(invert_weights, node, map_index))
    map_menu.addAction(invert_action)
    map_menu.addSeparator()

    def copy_weights(node, map_index):
        global maps_clipboard
        node.parameters["map"][map_index].retrieve_values()
        maps_clipboard = node.parameters["map"][map_index]

    copy_action = QtWidgets.QAction(parent)
    copy_action.setText("Copy")
    copy_action.triggered.connect(partial(copy_weights, node, map_index))
    map_menu.addAction(copy_action)

    def paste_weights(node, new_map_index):
        """
        Pasting the maps.  Terms used here
            orig/new.
            The map/node the items were copied from are prefixed with orig.
            The map/node the items are going to be pasted onto are prefixed with new

        """
        if maps_clipboard:
            orig_map = maps_clipboard
        else:
            return

        # It will be simple for a user to paste the wrong map in wrong location
        # here we are comparing the length of the maps and if they are different we can bring up
        # a dialog to warn user unexpected results may happen,
        node.parameters["map"][map_index].retrieve_values()
        new_map = node.parameters["map"][new_map_index]
        orig_map_length = len(orig_map.values)
        new_map_length = len(new_map.values)

        dialog_return = None
        if orig_map_length != new_map_length:
            msg_box = QtWidgets.QMessageBox()
            msg_box.setText(
                "The map you are copying from ({}) and pasting to ({}) have a different length.  Unexpected results may happen."
                .format(orig_map_length, new_map_length))
            msg_box.setInformativeText("Are you sure you want to continue?")
            msg_box.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            msg_box.setDefaultButton(QtWidgets.QMessageBox.No)
            dialog_return = msg_box.exec_()

        if dialog_return == QtWidgets.QMessageBox.Yes or orig_map_length == new_map_length:
            new_map.copy_values_from(orig_map)
            new_map.apply_weights()

    paste_action = QtWidgets.QAction(parent)
    paste_action.setText("Paste")
    paste_action.triggered.connect(partial(paste_weights, node, map_index))
    paste_action.setEnabled(bool(maps_clipboard))
    map_menu.addAction(paste_action)


def create_attr_context_menu(parent, node):
    menu = QtWidgets.QMenu(parent)
    append_attr_actions(parent, menu, node)
    return menu


def create_attr_map_context_menu(parent, node):
    menu = QtWidgets.QMenu(parent)
    append_attr_actions(parent, menu, node)
    menu.addSection("Maps")
    append_map_actions(parent, menu, "Weight", node, 0)
    return menu


def create_fiber_context_menu(parent, node):
    menu = QtWidgets.QMenu(parent)
    append_attr_actions(parent, menu, node)
    menu.addSection("Maps")
    append_map_actions(parent, menu, "Weight", node, 0)
    append_map_actions(parent, menu, "EndPoints", node, 1)
    return menu


def create_attachment_context_menu(parent, node):
    menu = QtWidgets.QMenu(parent)
    # Attribute section
    append_attr_actions(parent, menu, node)

    # Select source and target section
    sel_src_tgt_action = QtWidgets.QAction(parent)
    sel_src_tgt_action.setText("Select Source and Target")
    sel_src_tgt_action.triggered.connect(parent.select_source_and_target)
    menu.addAction(sel_src_tgt_action)

    # Source and target map section
    truncate = lambda x: (x[:12] + "..") if len(x) > 14 else x
    menu.addSection("Maps")
    source_menu_text = "Source ({})".format(truncate(node.association[0]))
    append_map_actions(parent, menu, source_menu_text, node, 0)
    target_menu_text = "Target ({})".format(truncate(node.association[1]))
    append_map_actions(parent, menu, target_menu_text, node, 1)

    # Paint by proximity section
    menu.addSection("")
    proximity_menu = menu.addMenu("Paint By Proximity")
    paint_by_prox_action = QtWidgets.QWidgetAction(proximity_menu)
    paint_by_prox_action.setDefaultWidget(ProximityWidget())
    proximity_menu.addAction(paint_by_prox_action)
    return menu
