.. include:: <isonum.txt>
.. _sec-ScenePanel2:

Scene Panel 2
**************

Scene Panel 2 is a tool to view and organize the Ziva VFX nodes and edit their attributes.
It allows you to quickly browse and edit a subset of the Ziva VFX nodes in your scene.
It bases on zBuilder's retrieve operation results and intends to supersede the :ref:`sec-ScenePanel`.

To launch it, click the **Scene Panel** |sp_shelf_button| shelf button,
or choose the **Ziva** |rarr| **Launch Scene Panel** menu.

.. |sp_shelf_button| image:: images/scene_panel.png

The Scene Panel 2 can also be launched from following python script:

.. code-block:: python

  from zBuilder.scenePanel2 import main
  main.run()

If you prefer to use previous Scene Panel,
define the **ZIVA_ZBUILDER_USE_SCENE_PANEL1** environment variable and restart Maya,
then you can launch it through preceding methods.

**Interface overview**

This section is a brief summary of the main interface.
Numbered headings below refer to the numbered interface elements in the figure.

.. image:: images/scene_panel_2_interface.png

1. **Menubar**

   The Menubar contains the most functionality to work in your Ziva VFX scene.

2. **Toolbar**

   The toolbar contains the frequently used features organized by sections.
   Some toolbar button has submenu to access related features easier.

3. **Scene View**

   The Scene View shows the Ziva VFX scene objects: Solver, Bone, Tissue and Cloth.
   You can manage them by creating Group node and reorder them through drag&drop.

4. **Component View**

   The Component View shows each component according to your current selected scene object(s).
   Uses can apply attribute, maps copy paste operations through popup menu.

.. toctree::
    sp2_menuBar.rst
    sp2_toolBar.rst
    sp2_sceneView.rst
    sp2_componentView.rst