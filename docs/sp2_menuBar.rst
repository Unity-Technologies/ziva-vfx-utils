.. include:: <isonum.txt>

.. # define a hard line break for HTML
..  raw:: html

   <br />

Menubar
------------

File Menu
^^^^^^^^^^^^

.. _sec-zLoadSaveRig:

Load.../Save...
""""""""""""""""

Loads a Ziva rig from a disk file, and applies
it to the specified solver.

**Python commands**::

  # Load a Ziva rig from a file. Geometry must already be in the scene.
  # If solverName is not provided, the rig is applied to the solver stored in the zBuilder file.
  # If solverName is provided, replace the name of the solver stored in the zBuilder file with a given solverName,
  # and apply the rig to that solver.
  import zBuilder.utils as utils
  utils.load_rig(file_name, solver_name=None)

Saves the Ziva rig present only in the selected solver to a disk file.

**Python commands**::

  # Save a Ziva rig to a file.
  # If there is only one solver in the scene, it is saved.
  # If there is multiple solvers, save the first solver in the union
  # of selected solvers and the default solver.
  import zBuilder.utils as utils
  utils.save_rig(file_name, solver_name=None)


.. _sec-zRigCutCopyPaste:

Cut/Copy/Paste
"""""""""""""""

These commands make it possible to cut, copy, and paste Ziva rigs.
Targets can be individual simulation bodies or entire solvers,
and the rigs can be transferred within a creature, or from one creature onto another.
For example, suppose that part of the creature is already rigged,
and an additional rig is needed that has the same number of mesh vertices and triangle connectivity
(but not the same vertex positions).
Then you can select those already rigged objects, copy them,
and paste their Ziva rigs onto this previously un-rigged additional geometry.
Note that for copying an entire Ziva rig of a creature onto a "clean" un-rigged creature,
either into the same solver or into a separate solver,
you can also use the zRigTransfer script (:ref:`sec-zRigTransfer`).

**Python commands**::

  # Cut the Ziva rig available on currently selected objects into the Ziva clipboard.
  # Selection cannot be empty; otherwise an error is reported.
  # Selection can contain zero or one solver node; otherwise an error is reported
  # (it does not matter if the solver node is a solver transform node, or solver shape node).
  # The selected objects must all come from exactly one solver; otherwise an error is reported.
  import zBuilder.utils as utils
  utils.rig_cut()

  # Copy the Ziva rig available on currently selected objects, into the Ziva clipboard.
  # Same usage notes as with rig_cut.
  import zBuilder.utils as utils
  utils.rig_copy()

  # Paste the Ziva rig from the Ziva clipboard onto scene geometry.
  # If nothing is selected, or the Ziva clipboard contains an explicit solver node,
  # the Ziva rig is applied to scene geometry that is named inside the Ziva clipboard.
  # If something is selected, then:
  #   source selection 1 is pasted onto target selection 1;
  #   source selection 2 is pasted onto target selection 2; and so on.
  # The pasted Ziva rig is added to the solver that was used for the last cut/copy operation.
  # If such a solver does not exist any more in the Maya scene (because, say, it has been cut),
  # it is created.
  import zBuilder.utils as utils
  utils.rig_paste()


.. _sec-zRigCopyPasteWithNameSubstitution:

Copy/Paste with Name Substitution
""""""""""""""""""""""""""""""""""

Suppose you have already modeled the geometry of a creature,
and a Ziva rig on one half (say, the left side) of a creature.
The name of left side meshes starts with ``l_`` and right side meshes starts wtih ``r_``.
This tool makes it possible to copy the rig onto the other side of the creature.
This is achieved through regular expression replacements.
The method requires a regular expression and a string with which to replace any regular expression matches.
For example, if regular expression is ``^l_`` and string to substitute with is ``r_``,
then all instances of geometry that begin with ``r_`` 
will be rigged in the same way as the corresponding geometry that begins with ``l_``.
The new Ziva rig elements are added to the same solver as the source.
For example, ``r_biceps`` will be rigged in the same way as ``l_biceps``.
In order for all the elements of the Ziva rig to be transferred properly
(such as painted attachments, or other painted properties),
the geometries of ``r_biceps`` and ``l_biceps`` must be mirror images of one another.

.. note::
    This regular expression tool is more general than just for mirroring;
    arbitrary Python regular expressions are supported.
    Examples of useful pairs are:

    - ``(^|_)l($|_)`` and ``r``
    - ``^l_`` and ``r_``
    - ``_l_`` and ``_r_``
    - ``_l$`` and ``_r``

    You can learn more about regular expressions at the `Regex101 website <https://regex101.com/>`_.

**Python command**::

  # Copy/Pastes Ziva rig for the selected solver, using regular expressions.
  # If multiple solvers are selected, only the first solver is processed.
  import zBuilder.utils as utils
  utils.copy_paste_with_substitution(regular_expression, string_to_substitute_matches_with)


.. _sec-zRigUpdate:

Update
"""""""

This command updates the Ziva rig in the selected solver to use the current geometry.
This is useful if you made modifications to creature's geometry *after* you converted it into Ziva simulation bodies.
In this way, the Ziva rig is identical to a Ziva rig that you would obtain
if the current geometry was originally used to make the Ziva simulation bodies directly.
This feature is also useful if you warped a creature using one of our warping tools
and you want to update the Ziva rig to use the newly warped geometry.

**Python command**::

  # Updates the Ziva rig in the solver(s).
  # This command can be used if you made geometry modifications and you'd like to re-use a previously
  # built Ziva rig on the modified geometry.
  # If no "solvers" are provided, they are inferred from selection.
  import zBuilder.utils as utils
  utils.rig_update(solvers=None)


.. _sec-zRigTransfer:

Transfer...
""""""""""""

Suppose you have a fully set up source Ziva creature with both the geometry and Ziva rig,
and a target creature for which you have the geometry,
but no Ziva rig.
Suppose the target geometry has the same triangle connectivity 
but different vertex positions than the source geometry.
This is the case, for example,
when the target creature geometry was obtained by warping the source creature geometry using ZAT.

In this case, this feature makes it possible to transfer the Ziva rig from the source geometry onto the target geometry.
The transferred rig is made available in whatever solver chosen by the user.
A common choice is to make it available in its own separate solver,
so that the target creature is completely independent of the source creature.
After transferring the rig, the new Ziva rig on the target creature can be saved to disk using :ref:`sec-zLoadSaveRig`.
Optionally, the source creature and its solver can also be removed from the scene, 
using the **Ziva** |rarr| **Remove** |rarr| **Selected Solver(s)** command,
leaving a scene that has just the target creature in it.

In order to warp the Ziva rig, you will need to provide the source and target solvers (in the dialog box).

**Python command**::

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
  import zBuilder.utils as utils
  utils.rig_transfer(sourceSolver, prefix, targetSolver="")



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

    from zBuilder import utils
    from maya import cmds
    utils.merge_solvers(cmds.ls(sl=True))

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