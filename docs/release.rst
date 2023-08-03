Release Notes
=============
.. |br| raw:: html

   <br>

.. == STYLE ==
.. For consistency, prefer to use an imperative style, like:
.. - Add a new widget for pies.
.. - Fix broken rendering.
.. - Allow foo.
.. For bug fixes, just say what the bug was. e.g.
.. - Broken rendering on tissue blah blah.
.. - Fibers will not generate on tissues with multiple components.

2.2.0
------

Functionality
+++++++++++++
- **zBuilder:** Robust Mirror Operation:
    - **zBuilder.nodes.parameters.mesh** Added ability to mirror mesh on X, Y or Z.
    - **zBuilder.commands** Added **mirror** command.
- **zBuilder:** The Maya deformer builder (which supports Blendshape, DeltaMush, Wrap and SkinCluster) is revived.
- **zBuilder:** **Bundle** class is deleted to simplify class hierarchy.
- **zBuilder:** Remove unused **attr_filter**, **name_filter** from **build()** method.

Bug Fixes
+++++++++
- **zBuilder:** VFXACT-1749 Fix for locked/connected attribute when setAttr() called for **zMaretial.weightList[0].weight**.
- **zBuilder:** VFXACT-1579	Fix the broken set/get paintablemap() function since Maya 2022
- **zBuilder:** VFXACT-1651 add zBuilder support for zRestShape alias attributes.
- **zBuilder:** VFXACT-1525 Fix for zRivetToBoneLocator naming issue.
- **zBuilder:** VFXACT-1528 **rename_ziva_nodes()** Name zLineOfAction off of zFiber.
- **zBuilder:** VFXACT-1499 **rename_ziva_nodes()** Number suffix for all zAttachments.


2.1.0
------

Functionality
+++++++++++++
- **zBuilder:** **zBuilder.builders.write** zips a JSON file into the ".zbuilder" file.
  |br|
  The ".zBuilder" file size is decreased for large scenes.
- **zBuilder:** **zBuilder.builders.read** can read both a zipped file and an unzipped JSON file.
- **zBuilder:** Refactoring code structure:
    - Renamed **zBuilder.builders.IO** to **zBuilder.builders.serialize**.
    - Renamed **Builder.retrieve_from_file** to **read** and moved to **zBuilder.builders.serialize**.
      |br|
      There is still **Builder.retrieve_from_file** for backward compatibility, but this method will be deprecated.
    - Moved **Builder.write** to **zBuilder.builders.serialize**.
      |br|
      There is still **Builder.write** for backward compatibility, but this method will be deprecated.
    - Move **rename_ziva_nodes()** from **zBuilder.zMaya** to **zBuilder.utils**.
    - Rename **zBuilder.utils** to **zBuilder.commands**.
    - Rename **zBuilder.zMaya** to **zBuilder.utils.vfxUtils**.
    - Move zBuilder utility files to **zBuilder.utils** folder.
    - Cleanup unused builder and node types.
    - Reorganize unit test files by modules.
- **Scene Panel:** The scene refresh speed is improved by deferring mesh/map data retrieval until they are actually needed.
  |br|
  The refresh time for a test character scene was reduced from 7.5s to 1.5s.
- **Scene Panel:** Extract scene panel folders out of zBuilder folder and make these standalone modules.
- **Utility Commands:** Clear zCache command supports multiple selection clearance.
- **Demo:** Update "One of Each Attachment", "One of Each Collision", "Attachments" demo:
    - Remove deprecated `isHard` attribute.
    - Add damping attributes with zero and non-zero values for effect comparison.
    - Add non-zero attachment damping for "One of Each Collision" demo.

Bug Fixes
+++++++++
- **zBuilder:** VFXACT-1288 Fix the regression of building mesh with different topologies.
- **zBuilder:** VFXACT-1328 Add `map_type` and `interp_method` attribute to `base.SEARCH_EXCLUDE`.
- **zBuilder:** VFXACT-1347 Add `info` attribute to `base.SEARCH_EXCLUDE`.


2.0.0
------

Functionality
+++++++++++++
- **Scene Panel:** Newly added :ref:`sec-ScenePanel2`.
- **Scene Panel:** Show source/target attachments with different icons.
- Removed "Select" option from Ziva menu.

Bug Fixes
+++++++++
- **zBuilder:** VFXACT-955 Load zBuilder file throws exception at the first run
- **zBuilder:** VFXACT-975 zBuilder update command reports error when applying to tissue object
- **zBuilder:** VFXACT-1067 Rename zRivetToBoneLocator node when run rename_ziva_nodes() command.
- **zBuilder:** VFXACT-1107 Mirror operation creates extra attachment copy


1.1.1
------

Bug Fixes
+++++++++
- **zBuilder:** Load zBuilder setup reports error if no other zBuilder operation runs before.

1.1.0
------
- Add support for Maya 2022.
- Add support for Python 3.
- Phase out support for Maya 2018 and older

Functionality
+++++++++++++
- Automatically output logging information to a zBuilder log file.
- Set *ZIVA_ZBUILDER_DEBUG=1* environment variable before launching Maya to get extra debug info.
- Add utility function *remove_zRivetToBone_nodes()* -- correctly remove a zRivetToBone object from the scene.

Bug Fixes
+++++++++
- **zBuilder:** zRivet locator names now stored and re-applied
- **zBuilder:** zRivet locator group node now stored and re-parented if group node exists
- **zBuilder:** Scene Panel refresh and Copy-Paste did not work in some cases with sub-tissues.
- **zBuilder:** Trying to paint a map from scene panel would fail due to an AttributeError.
- **zBuilder:** Can now open zBuilder files created in Ziva VFX 1.7 or older.
- **zBuilder:** Workaround breakage of MFnGeometryFilter.deformerSet() in Maya 2022. This API breakage is related to the new "component tag" feature of Geometry Filters in Maya 2022. Performance may be reduced when serializing large scenes in Maya 2022.

1.0.11
------

Functionality
+++++++++++++
- **Scene Panel:** Now able to rename nodes by double-clicking on them.
- **Scene Panel:** Add right-click menu for zSolver.
- **Scene Panel:** Update icons.
- **Shelf:** Add Ziva Shelf.
- **zBuilder:** Add Merge Solvers to the Ziva menu.
- **zBuilder:** Add support for referencing.
- **zBuilder:** Now storing a link to map and mesh in scene item.
- **zBuilder:** Remove use of mObject inside zBuilder.
- **zBuilder:** Add unit tests for mirroring and referencing coverage.
- **zBuilder:** Performance improvements to zBuilder.

Benchmark Runtimes (in seconds, lower is better):

+---------------------+------------------------+--------------------+-------------------+-------------------+
|                     | Action                 | 1.0.9              | 1.0.10            | 1.0.11            |
+=====================+========================+====================+===================+===================+
|   **Demo Arm**      | build()                | 2.80               | 1.70              | 0.93              |
+                     +------------------------+--------------------+-------------------+-------------------+
|                     | retrieve()             | 0.42               | 0.37              | 0.32              |
+                     +------------------------+--------------------+-------------------+-------------------+
|                     | retrieve_from_file()   | 0.07               | 0.06              | 0.06              |
+                     +------------------------+--------------------+-------------------+-------------------+
|                     | write()                | 0.35               | 0.36              | 0.30              |
+---------------------+------------------------+--------------------+-------------------+-------------------+
|   **Jellyphant**    | build()                | 9.27               | 7.05              | 3.33              |
+                     +------------------------+--------------------+-------------------+-------------------+
|                     | retrieve()             | 1.11               | 0.96              | 0.53              |
+                     +------------------------+--------------------+-------------------+-------------------+
|                     | retrieve_from_file()   | 0.22               | 0.18              | 0.23              |
+                     +------------------------+--------------------+-------------------+-------------------+
|                     | write()                | 1.17               | 1.16              | 0.90              |
+---------------------+------------------------+--------------------+-------------------+-------------------+
| **bob-leg-muscles** | build()                | 184.72             | 53.67             | 32.48             |
+                     +------------------------+--------------------+-------------------+-------------------+
|                     | retrieve()             | 9.5                | 6.92              | 4.80              |
+                     +------------------------+--------------------+-------------------+-------------------+
|                     | retrieve_from_file()   | 2.14               | 1.06              | 1.82              |
+                     +------------------------+--------------------+-------------------+-------------------+
|                     | write()                | 7.95               | 7.66              | 7.30              |
+---------------------+------------------------+--------------------+-------------------+-------------------+

Bug Fixes
+++++++++
- **Scene Panel:** Opening Node Editor clears Scene Panel content while detached from the dock.
- **Scene Panel:** Some maps in Scene Panel right-click menu did not work.
- **zBuilder:** When detecting a zRestShape node on tissue it is now name agnostic.
- **zBuilder:** Copy and Paste from menu did not work on objects with multiple rest shapes.
- **zBuilder:** zMaya.rename_ziva_nodes() didn't work on zRestShapes.

1.0.10
------

Functionality
+++++++++++++
- **Scene Panel:** Updated the right-click menu: added copy/paste/invert and paint to maps; added copy/paste for attributes.
- **Scene Panel:** Changed appearance of the Scene Panel.
- **Ziva VFX Utils:** Added ``utils.merge_solvers()`` function.
- **Ziva VFX Utils:** Added License Register module with UI.
- **zBuilder:** Added ``SolverDisabler`` context manager to help facilitate turning off solver during a build.
- **zBuilder:** Removed deprecated ``check_mesh`` flag from ``build()``.
- **zBuilder:** Added ``apply_weights()`` to Map class.
- **zBuilder:** Added ability to invert maps in Map class.
- **zBuilder:** Rename "Cache" to "Simulation RAM Cache" in the menu.
- **zBuilder:** Added ability to compare zBuilder objects.
- **zBuilder:** Changed Newton iterations in demo arm from 2 to 10.
- **zBuilder:** Unit tests can run in Linux.
- **zBuilder:** Move unit tests outside of zBuilder module.
- **zBuilder:** Speed increase to retrieve when dealing with meshes.

Benchmark Runtimes (in seconds, lower is better):

+---------------------+------------------------+--------------------+-------------------+
|                     | Action                 | 1.0.9              | 1.0.10            |
+=====================+========================+====================+===================+
|   **Demo Arm**      | build()                | 2.80               | 1.70              |
+                     +------------------------+--------------------+-------------------+
|                     | retrieve()             | 0.42               | 0.37              |
+                     +------------------------+--------------------+-------------------+
|                     | retrieve_from_file()   | 0.07               | 0.06              |
+                     +------------------------+--------------------+-------------------+
|                     | write()                | 0.35               | 0.36              |
+---------------------+------------------------+--------------------+-------------------+
|   **Jellyphant**    | build()                | 9.27               | 7.05              |
+                     +------------------------+--------------------+-------------------+
|                     | retrieve()             | 1.11               | 0.96              |
+                     +------------------------+--------------------+-------------------+
|                     | retrieve_from_file()   | 0.22               | 0.18              |
+                     +------------------------+--------------------+-------------------+
|                     | write()                | 1.17               | 1.16              |
+---------------------+------------------------+--------------------+-------------------+
| **bob-leg-muscles** | build()                | 184.72             | 53.67             |
+                     +------------------------+--------------------+-------------------+
|                     | retrieve()             | 9.5                | 6.92              |
+                     +------------------------+--------------------+-------------------+
|                     | retrieve_from_file()   | 2.14               | 1.06              |
+                     +------------------------+--------------------+-------------------+
|                     | write()                | 7.95               | 7.66              |
+---------------------+------------------------+--------------------+-------------------+

- **zBuilder:** Added a bunch of unit tests.

Bug Fixes
+++++++++
- **zBuilder:** When retrieving multiple times in a scene strange things could end up in builder.
- **zBuilder:** zBuilder ``build()`` would fail when something was connected to ``enable`` attribute.
- **zBuilder:** zBuilder being too chatty when building by printing out every node type. Now only the ones it operated on.
- **zBuilder:** Prefix or suffix could mess up string_replace in zBuilder and menu.
- **zBuilder:** Speed slow down when building while using ``retrieve_from_scene_selection()``.
- **zBuilder:** Error when you tried to a copy/paste in the menu when you have a non-restShaped tissue selected.

1.0.9
-----
* Fix for Copy/Paste transfer menu items.
* Now able to deepcopy a builder object
* Rename util.py to utils.py
* Adding support for zRestShape (retrieving, building, serialize, deserialize, Scene Panel)
* Improvements to serialization and deserialization
* Support for multiple curves for zLineOfAction
* Storing mObjectHandle instead of mObject for robustness
* Adding zRivet and respective curves to Scene Panel
* Fix for zCloth objects not mirroring
* Storing intermediate shape of mesh
* Fix for zTissue attributes not updating in some edge cases
* General bug fixes and cleanup

1.0.8
-----
* clamping values when interpolating maps
* fix mirroring rivet issue
* bug fixes

1.0.7
-----
* Adding unit tests (CMT tools)
* Adding support for zRivetToBone
* Added ability to use groups in regular expressions
* multi select items in maya scene through Scene Panel
* various bug fixes

1.0.5
-----
* Support for Maya fields
* Support for zFieldAdaptor node
* UI overhaul (Launch from Ziva menu)
* various bug fixes

1.0.4
-----
* QT tree view for builder data
* bug fixes

1.0.3
-----
* zUI support on maya 2017 and 2018
* bug fixes

1.0.0
-----
* major refactor
* file backwards compatibility
* support for multiple solvers
* easier to extend

0.11.3
------
* zBuilder support for sub-tissues
* mirroring of geo before application (experimental)
* zLineOfAction functionality added to retrieve_from_scene_selection
* general bug fixes



0.11.2
------
* Restructure of class hierarchy
* packages can extend themselves
* bug fixes

0.11.1
------
* Material, Fiber and Attachment creation now more robust.  No longer name cascading problems.
* lineOfAction node added 


0.11.0
------
* removed abstract methods from NodeCollection
* deprecated set_attrs and set_weights in favor of using a MayaMixin class
* storing mObjects internally during node creation to get around maya renaming 
* zMaya.rename_ziva_nodes() handles zBones and zCloth

0.10.0
------
* save out component data and node data separately
* changed map.py to maps.py
* fixed bug in cloth creation
* changed node_filter to name_filter.  Better representation on what it is.

0.9.5
-----
* changed order of cloth application when applying

0.9.4
-----
* retrieving from scene in ZivaSetup now works by passing nodes or not.  Default behavior is unchanged.
* restoring user selection when using zMaya.py methods.
* added support for cloth
