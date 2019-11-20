Release Notes
=============

1.0.10
======

Functionality
-------------
- **Scene Panel:** Right click menu updated.  Added copy/paste/invert and paint to maps. Added copy/paste for attributes.  
- **Scene Panel:** Appearence changes to Scene Panel
- **Ziva VFX Utils:** Added a merge solvers function.
- **Ziva VFX Utils:** Added license Register module with UI to help
- **zBuilder:** Added a Solver Disabler context manager to help facilitate turning off solver during a build.  
- **zBuilder:** Removed deprecated check_mesh flag from .build()
- **zBuilder:** Added apply_weights() to Map class.
- **zBuilder:** Added ability to invert maps in Map class.
- **zBuilder:** Rename "Cache" to "Simulation RAM Cache" in menu.
- **zBuilder:** Added ability to compare zBuilder objects. if builder1 == builder2:
- **zBuilder:** Changed newton iterations in demo arm from 2 to 10.
- **zBuilder:** Unit tests can run in linux.
- **zBuilder:** Move unit tests outside of zBuilder module.
- **zBuilder:** Speed increase to retrieve when dealing with meshes.

Bug Fixes
---------
- **zBuilder:** When retrieving multiple times in a scene strange things could end up in builder.
- **zBuilder:** zBuilder build() would fail when something was connected to .enable
- **zBuilder:** zBuilder being too chatty when building by printing out every node type.  Now only the ones it operated on.
- **zBuilder:** Prefix or Suffix could mess up string_replace in zBuilder and menu.
- **zBuilder:** Speed slow down when building.
- **zBuilder:** When using retrieve_scene_selection() when selecting only one out of multiple restShapes
- **zBuilder:** When you tried to copy in menu with you have a non-restShaped tissue selected

1.0.9
-----
* Fix for Copy/Paste transfer menu items.
* Now able to deepcopy a builder object
* Rename util.py to utils.py
* Adding support for zRestShape (retrieving, building, serialize, deserialize, Scene Panel)
* Improvements to serialization and deserialization
* Support for multiple curves for zLineOfAction
* Storing mObjectHandle instead of mObject for robustness
* Adding zRivet and repective curves to Scene Panel
* Fix for zCloth objects not mirroring
* Storing intermediate shape of mesh
* Fix for zTissue attributes not updating in some edge cases
* Genreal bug fixes and cleanup

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
* zLineOfAction functionality added to retrieve_from_scene_selecton
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
* depractated set_attrs and set_weights in favor of using a MayaMixin class
* storing mObjects internally during node creation to get around maya renaming 
* zMaya.rename_ziva_nodes() handles zBones and zCloth

0.10.0
------
* save out component data and node data seperatly
* changed map.py to maps.py
* fixed bug in cloth creation
* changed node_filter to name_filter.  Better representation on what it is.

0.9.5
-----
* changed order of cloth application when applying

0.9.4
-----
* retrieving from scene in ZivaSetup now works by passing nodes or not.  Default behavior is unchanged.
* restoring user selection when using zMapa.py methods.
* added support for cloth
