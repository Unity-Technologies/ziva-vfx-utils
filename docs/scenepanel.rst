.. include:: <isonum.txt>
.. _sec-ScenePanel:

##############
Scene Panel
##############

.. note:: Scene Panel will be superseded by :ref:`sec-ScenePanel2`.

Scene Panel is an object-viewing tool to inspect the Ziva setup,
which bases on zBuilder retrieve operation results.

Launches a new object-viewing panel that can be used to inspect the current Ziva setup.

.. image:: images/scene_panel1.png
    :alt: Screenshot of the Ziva panel

The Ziva Scene Panel allows you to quickly browse a subset of the Ziva objects in your scene. 
The selected Ziva objects and their immediate connections are shown in a tree, allowing you to focus on specific parts of your scene. 
To display the full scene in the panel select the solver and launch the scene panel or hit refresh.

By selecting muscle or bone geometry and launching it will check all attachments to see what else is connected and add those to the tree view.  
By selecting an attachment it checks the source and destination and adds those.  It does this so you have control over what is viewed 
to minimize amount of items you have to sort through.

Selecting an item in the panel selects the corresponding item in the Maya scene.

.. note:: If you update the Maya scene, the panel is not automatically updated.  
          You can update it by closing the Scene Panel and re-opening it via **Ziva** |rarr| **Launch Scene Panel**.
          Another approach is to press the refresh button on the Scene Panel toolbar.

The Scene Panel can also be launched from python by the following:
::

  from zBuilder.ui import zUI
  zUI.run()

.. _sec-ScenePanelMenu:

Right Click Menu
----------------

Attributes Sub-Menu
^^^^^^^^^^^^^^^^^^^

.. image:: images/scene_panel2.png
    :alt: The Attributes section.

If a node has attributes to manipulate an Attributes sub-menu will appear on the right click menu.

Copy
""""
This will copy all attributes values and allow you to paste onto node of same type.  i.e. zAttachment |rarr| zAttachment.  

Paste
"""""
This pastes the attribute values onto the selected node.

.. note::  The paste button is disabled if there is nothing in the clipboard OR if what is in the clipboard is not same type with current selection.


Maps Sub-Menu
^^^^^^^^^^^^^

.. image:: images/scene_panel3.png
    :alt: The Maps section.

If a node has any weight maps associated with it, a sub-menu for each map appears on the right click Menu.
In the case of the image above it is showing a sub-menu for 'Weight' and 'EndPoints' which are maps 
for a zFiber.

Paint
"""""
This sets up the viewport with the painting context so you can paint the map.  This is the same as
in viewport right clicking and choosing Paint |rarr| zFiber.

Invert
""""""
This inverts the map.  Values of 1 become 0 and 0 becomes 1.  A good example of a use case is if you are
trying to layer material maps.  You can paint one, copy it then do a paste then invert and
You now have 2 maps covering whole mesh.

Copy
""""
This copies the map into the map clipboard to be pasted.

Paste
"""""
This pastes the map onto the selected map.  This is handy if you want to copy a map from one node type to another.
A good example is if you have a fiber weight map and you want the same map to be applied to the material for example.

.. note:: If you are trying to copy a map from one mesh to another with different topology
          a dialog will pop up asking if you are sure you want to do this.  More than likely
          unpredictable results will happen.

Select Source and Target
^^^^^^^^^^^^^^^^^^^^^^^^
On a zAttachment node this item appears.  It selects both the source and target mesh for
convenience.

Paint by Proximity Sub-Menu
^^^^^^^^^^^^^^^^^^^^^^^^^^^
For a zAttachment this paints the attachment weight map on the source that falls-off smoothly between the prescribed min and max distance from the target.

