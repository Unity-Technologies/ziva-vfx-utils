Release Notes
=============
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
