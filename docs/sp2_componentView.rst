.. include:: <isonum.txt>

.. _sec-ComponentView:

Component View
---------------

General Introduction
^^^^^^^^^^^^^^^^^^^^^^^^

The Component View displays detailed Ziva VFX component object infomation,
according to the selected and/or pinned objects in the :ref:`sec-SceneView`.
Each component instance is displayed as a tree structure in each Component Section View,
with its parent object in the Scene View as root.
Same component types, or related types are group together in the same tree structure.
For example, if the tissue object has muscle fiber as well as line of action,
both of them will be displayed in the same Component Section View.
Users can browse the component objects and edit the maps that affiliated to them through popup menu.
Numbered headings below refer to the numbered interface elements in the figure.

.. image:: images/component_view_interface.png

1. **Component Type Name**
2. **Component Type Icon**
3. **Fold Button**

The name and icon of component type are shown at the top of each view.
If there are multiple component, the name and icon will be shown altogether.
The leftmost button beside component name is the fold button.
When clicked, it folds/expand current component view.

Context Menu
^^^^^^^^^^^^

You can edit those components that contain paintable maps through the context menu.

Attributes Sub-Menu
""""""""""""""""""""

.. image:: ./images/scene_panel2.png
    :alt: The Attributes section.

If a node has attributes to manipulate an Attributes sub-menu will appear on the right click menu.

**Copy**

This will copy all attributes values and allow you to paste onto node of same type, i.e., zAttachment |rarr| zAttachment.

**Paste**

This pastes the attribute values onto the selected node.

.. note::  The paste button is disabled if there is nothing in the clipboard OR if what is in the clipboard is not same type with current selection.


Maps Sub-Menu
""""""""""""""

.. image:: images/scene_panel3.png
    :alt: The Maps section.

If a node has any weight maps associated with it, a sub-menu for each map appears on the right click Menu.
In the case of the image above it is showing a sub-menu for 'Weight' 
and 'EndPoints' which are maps for a zFiber.

**Paint**

This sets up the viewport with the painting context so you can paint the map.  This is the same as
in viewport right clicking and choosing Paint |rarr| zFiber.

**Invert**

This inverts the map.  Values of 1 become 0 and 0 becomes 1.  A good example of a use case is if you are
trying to layer material maps.  You can paint one, copy it then do a paste then invert and
You now have 2 maps covering whole mesh.

**Copy**

This copies the map into the map clipboard to be pasted.

**Paste**

This pastes the map onto the selected map.
This is handy if you want to copy a map from one node type to another.
A good example is if you have a fiber weight map
and you want the same map to be applied to the material.

.. note:: If you are trying to copy a map from one mesh to another with different topology
    a dialog will pop up asking if you are sure you want to do this.
    More than likely unpredictable results will happen.

zAttachment Sub-Menu
"""""""""""""""""""""

.. image:: images/attachment_context_menu.png

**Select Source and Target**

On a zAttachment node this item appears.
It selects both the source and target mesh for convenience.

**Paint by Proximity Sub-Menu**

For a zAttachment this paints the attachment weight map on the source that falls-off smoothly between the prescribed min and max distance from the target.

