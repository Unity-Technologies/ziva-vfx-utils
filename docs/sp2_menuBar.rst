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

**Python commands**:

.. code-block:: python

    # Load a Ziva rig from a file. Geometry must already be in the scene.
    # If solverName is not provided, the rig is applied to the solver stored in the zBuilder file.
    # If solverName is provided, replace the name of the solver stored in the zBuilder file with a given solverName,
    # and apply the rig to that solver.
    import zBuilder.commands as vfx_cmds
    vfx_cmds.load_rig(file_name, solver_name=None)

Saves the Ziva rig present only in the selected solver to a disk file.

**Python commands**:

.. code-block:: python

  # Save a Ziva rig to a file.
  # If there is only one solver in the scene, it is saved.
  # If there is multiple solvers, save the first solver in the union
  # of selected solvers and the default solver.
  import zBuilder.commands as vfx_cmds
  vfx_cmds.save_rig(file_name, solver_name=None)


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

**Python commands**:

.. code-block:: python

  # Cut the Ziva rig available on currently selected objects into the Ziva clipboard.
  # Selection cannot be empty; otherwise an error is reported.
  # Selection can contain zero or one solver node; otherwise an error is reported
  # (it does not matter if the solver node is a solver transform node, or solver shape node).
  # The selected objects must all come from exactly one solver; otherwise an error is reported.
  import zBuilder.commands as vfx_cmds
  vfx_cmds.rig_cut()

  # Copy the Ziva rig available on currently selected objects, into the Ziva clipboard.
  # Same usage notes as with rig_cut.
  import zBuilder.commands as vfx_cmds
  vfx_cmds.rig_copy()

  # Paste the Ziva rig from the Ziva clipboard onto scene geometry.
  # If nothing is selected, or the Ziva clipboard contains an explicit solver node,
  # the Ziva rig is applied to scene geometry that is named inside the Ziva clipboard.
  # If something is selected, then:
  #   source selection 1 is pasted onto target selection 1;
  #   source selection 2 is pasted onto target selection 2; and so on.
  # The pasted Ziva rig is added to the solver that was used for the last cut/copy operation.
  # If such a solver does not exist any more in the Maya scene (because, say, it has been cut),
  # it is created.
  import zBuilder.commands as vfx_cmds
  vfx_cmds.rig_paste()


Mirror
""""""

:ref:`Mirror <mirror>`

Update Ziva Rig
""""""""""""""""

This command updates the Ziva rig in the selected solver to use the current geometry.
This is useful if you made modifications to creature's geometry *after* you converted it into Ziva simulation bodies.
In this way, the Ziva rig is identical to a Ziva rig that you would obtain
if the current geometry was originally used to make the Ziva simulation bodies directly.
This feature is also useful if you warped a creature using one of our warping tools
and you want to update the Ziva rig to use the newly warped geometry.

**Python commands**:

.. code-block:: python

  # Updates the Ziva rig in the solver(s).
  # This command can be used if you made geometry modifications and you'd like to re-use a previously
  # built Ziva rig on the modified geometry.
  # If no "solvers" are provided, they are inferred from selection.
  import zBuilder.commands as vfx_cmds
  vfx_cmds.rig_update(solvers=None)


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

**Python commands**:

.. code-block:: python

  # Transfers the Ziva rig from 'sourceSolver' to another solver (targetSolver).
  # This command does not transfer the geometry.
  # It assumes that a copy of the geometry from sourceSolver is already available in the scene,
  # prefixed by "prefix" (without the quotes).
  # For example, if sourceSolver is 'zSolver1', and prefix is 'warped_',
  # and 'zSolver1' has a tissue geometry (a mesh) called "tissue1",
  # then this command assumes that there is a mesh called "warped_tissue1" in the scene.
  # The command generates a Ziva rig on the 'warped_*' geometry in the targetSolver.
  # If targetSolver is "", the command sets the targetSolver to sourceSolver + prefix.
  # If targetSolver does not exist yet, the command generates it.
  # Note that the targetSolver may be the same as the sourceSolver, 
  # in which case the rig on the 'warped_*' geometry is added into the sourceSolver.
  import zBuilder.commands as vfx_cmds
  vfx_cmds.rig_transfer(sourceSolver, prefix, targetSolver="")

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

**Python command**:

.. code-block:: python

  # Transfer the skin clusters for some selected meshes onto their warped counterparts 
  # and to connect the warped joint hierarchy.
  # This requires both geometries (selected and warped) have the same topology.
  # Also, the names of the warped meshes must be prefixed with "prefix".
  # Note: Warp the source meshes and the corresponding joint hierarchy before running the command.
  import zBuilder.commands as vfx_cmds
  vfx_cmds.skincluster_transfer(prefix="")


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

This is the same as executing::

    import zBuilder.commands as vfx_cmds
    from maya import cmds
    vfx_cmds.merge_solvers(cmds.ls(sl=True))

Given a selection list of zSolverTransform nodes, merge them all into the first solver.

The zSolverTransform, zSolver, and zEmbedder nodes for all but the first solver in the list will be deleted.
If that is not possible, such as when the solvers are referenced nodes,
those solvers will remain in the scene but be empty.
They will have no bones, tissues, cloth, attachments, etc.

The first solver keeps all of its attribute values and connections.
Any differences between this solver and the others is ignored.

All other nodes (besides the zSolverTransform, zSolver, and zEmbedder) are re-wired to connect to the first solver.
All existing attributes, connections, or any other properties remain unchanged.

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