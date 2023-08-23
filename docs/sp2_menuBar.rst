.. include:: <isonum.txt>

.. # define a hard line break for HTML
..  raw:: html

   <br />

Menubar
------------

File Menu
^^^^^^^^^^^^

.. _sec-zLoadSaveRig:

Load/Save Ziva Rig
"""""""""""""""""""

Loads a Ziva rig from a disk file, and applies it to the specified solver.
Refer to :func:`load_rig() <zBuilder.commands.load_rig>` docstring for Python script usage.

Saves the Ziva rig present only in the selected solver to a disk file.
Refer to :func:`save_rig() <zBuilder.commands.save_rig>` docstring for Python script usage.


Cut/Copy/Paste Selection
""""""""""""""""""""""""

Here are the commands to cut/copy/paste selected Ziva objects.
To apply such commands, targets can be individual simulation bodies or entire solvers,
and the rigs can be transferred within a creature, or from one creature onto another.
For example, if part of a creature is already rigged,
and an additional rig is needed that has the same number of mesh vertices and triangle connectivity
(but not the same vertex positions),
then one can select those already rigged objects,
cut/copy and paste their Ziva rigs onto previously un-rigged additional geometry.

.. note::
    For copying an entire Ziva rig of a creature onto
    a "clean" un-rigged creature (either into the same solver or into a separate solver),
    you can also use the zRigTransfer script (:ref:`sec-zRigTransfer`).

Refer to :func:`rig_cut() <zBuilder.commands.rig_cut>`, 
:func:`rig_copy() <zBuilder.commands.rig_copy>` and 
:func:`rig_paste() <zBuilder.commands.rig_paste>` docstring for Python script usage.

**Python commands**:

.. code-block:: python

  from zBuilder import commands as vfx_cmds
  # Either cut or copy the Ziva VFX rig
  vfx_cmds.rig_cut()
  vfx_cmds.rig_copy()
  # Paste the Ziva VFX rig
  vfx_cmds.rig_paste()


Mirror
""""""

Refer to :ref:`Mirror <mirror>` tutorial section.

Update Ziva Rig
""""""""""""""""

This command updates the Ziva rig in the selected solver to use the current geometry.
This is useful if you made modifications to creature's geometry *after* you converted it into Ziva simulation bodies.
In this way, the Ziva rig is identical to a Ziva rig that you would obtain
if the current geometry was originally used to make the Ziva simulation bodies directly.
This feature is also useful if you warped a creature using one of our warping tools
and you want to update the Ziva rig to use the newly warped geometry.
Refer to :func:`rig_update() <zBuilder.commands.rig_update>` docstring for Python script usage.

.. _sec-zRigTransfer:

Transfer Ziva Rig...
"""""""""""""""""""""

Suppose there is a fully set up source Ziva creature with both geometry and Ziva rig,
and a target creature geometry without a Ziva rig.
If the target geometry has same triangle connectivity but different vertex positions than the source geometry
(e.g. a target creature geometry obtained by warping the source creature geometry using ZAT),
this feature can transfer the Ziva rig from the source geometry onto the target geometry.

The transferred rig is made available in whatever solver chosen by the user.
A common choice is to make it available in its own separate solver,
so that the target creature is completely independent of the source creature.
After transferring the rig, the new Ziva rig on the target creature can be saved to disk using :ref:`sec-zLoadSaveRig` menu item.
Optionally, the source creature and its solver can also be removed from the scene, 
using the **Ziva** |rarr| **Remove** |rarr| **Selected Solver(s)** command,
leaving a scene that has just the target creature in it.

In order to warp the Ziva rig, you will need to provide the source and target solvers (in the dialog box).
Refer to :func:`rig_transfer() <zBuilder.commands.rig_transfer>` docstring for Python script usage.


Transfer Skin Cluster...
"""""""""""""""""""""""""

Suppose there is a fully set up Ziva creature with some Maya skin clusters
that are used to drive the bone meshes based on the joint hierarchy motion.

To perform skin cluster transfer, the source and target meshes and joints
must be in the scene with the same name (a configurable prefix is required).
The target meshes have two requirements:

1. No warper deformers (such as zBoneWarp) can be applied.
2. The meshes must be in an equivalent state (and are so if Maya's Delete History function has been applied).

The bone meshes and the joint hierarchy are transferred onto a new (target) creature
by copying the skin cluster weights from source meshes to the target meshes,
and by connecting the target meshes to the target joint hierarchy.

To execute the skin cluster transfer:

1. Select the source meshes and the **Transfer Skin Cluster...** menu item.
2. In the popup dialog, click the **Transfer** button.

Refer to :func:`skincluster_transfer() <zBuilder.commands.skincluster_transfer>` docstring for Python script usage.


Edit Menu
^^^^^^^^^^^^

It is the same as :ref:`sec-toolbar-edit-section` in the toolbar, refer to it for detailed introduction.


Create Menu
^^^^^^^^^^^^

It is the same as :ref:`sec-toolbar-create-section` in the toolbar, refer to it for detailed introduction.


Add Menu
^^^^^^^^^

It is the same as :ref:`sec-toolbar-add-section` in the toolbar, refer to it for detailed introduction.


Tools Menu
^^^^^^^^^^^^

**Merge Solvers**

Merges selected solvers into one.
Useful if you have objects that you want to simulate under the same solver so they can interact.
Refer to :func:`merge_solvers() <zBuilder.commands.merge_solvers>` docstring for Python script usage.


**Toggle Enabled Bodies**

Toggle the active state of selected bodies (tissues, cloth or bones).

Meshing
"""""""""""""""""

**zPolyCombine**

Combine the selected meshes together into a single mesh using the `zPolyCombine <https://docs.zivadynamics.com/vfx/mel_commands/zPolyCombine.html>`_ node.
The zPolyCombine node and new mesh maintain a live connection to the input meshes,
which are not destroyed.

This is equivalent to executing **zPolyCombine;**.

See the `zPolyCombine <https://docs.zivadynamics.com/vfx/nodes/zPolyCombine.html>`__ node
and `zPolyCombine <https://docs.zivadynamics.com/vfx/mel_commands/zPolyCombine.html>`_ command.

**Extract Rest Shape**

Given three meshes as input: a neutral shape of a tissue, the shape of the Tissue after simulation and a sculpted/corrected mesh, it creates a rest shape for a tissue.

This is the same as executing **zRestShape -pg;**

See the `zRestShape <https://docs.zivadynamics.com/vfx/mel_commands/zRestShape.html>`_ command.

Mesh Inspection
"""""""""""""""""

**Run Mesh Analysis**

Qualitatively test the selected mesh(es).
The command tests for poor quality triangles, non-manifold geometry and non-closed manifolds (meshes with boundary).

This is the same as executing **zMeshCheck -select;**

**Find Intersections**

From a source/target pair of selected meshes, select any source faces that intersect the target mesh.

This is the same as executing **select -r `zFindIntersections -xs`;**

**Find Self Intersections**

From a selected mesh, select any faces that self-intersect.

This is the same as executing **select -r `zFindIntersections -xo`;**

Proximity Tools
"""""""""""""""""

**Select Vertices**

Given a source/target pair of selected meshes,
select vertices on the source mesh that are near the target mesh.

**Paint Attachments By Proximity**

Given a selected attachment, paint the attachment weight map on the source that falls-off smoothly
between the prescribed min and max distance from the target.

Naming
"""""""

.. _naming:

**Rename Ziva Nodes**

This traverses through the scene and renames Ziva nodes based on geometry they are connected to.
Refer to :func:`rename_ziva_nodes() <zBuilder.commands.rename_ziva_nodes>` docstring for Python script usage.

.. note::

    This only renames nodes that have not been manually named previously.
    This allows nodes to be renamed by hand without the threat of the name changing again.

Help Menu
^^^^^^^^^^^^

**Ziva Command Help**

Prints the ziva command help to the script editor.

This is the same as executing **ziva -h;**

**Run Demo**

The plugin has a few demo scene built in.
The menu options under this item will create a new maya scene with the demo.

* Anatomical Arm
* Goaling, Self-Collisions, and Spatially Varying Materials
* Self-Collisions, Ziva Cache, and Delaunay Tet Mesher
* Attachments
* Collisions
* One Of Each Attachments
* One Of Each Collision Types
* Spatially Varying Materials
* Cloth Demo
* Cloth Rest Scale and Pressure
* Isomesher Demo

**Register License**

Launch the GUI tool to help users setup their license for using Ziva VFX.

**About**

Return some information about the plugin, including the current version number.

This is the same as executing **ziva -z;**

**Online Resources**

Launch a web browser to open the resources page on Ziva's website.