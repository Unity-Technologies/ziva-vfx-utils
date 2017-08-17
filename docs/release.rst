Release Notes
=============
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