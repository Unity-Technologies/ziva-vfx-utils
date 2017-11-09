zBuilder
========

At a high level, zBuilder is a python framework to help serialize and deserialize content from Maya scenes.
The basic idea is that you first interactively build a scene in Maya, and then
with zBuilder you can save that state and save it out and re-build it.

If we want to save a Ziva rig, for example, zBuilder can write out a json file representing the Ziva nodes in the scene.
That file would contain the nodes and attribute values and some basic information about their relationships.
zBuilder then gives you the ability to load that file into a scene with new geometry and re-build the rig there.
If the new geometry's topology (ie: triangles, number of vertices) is different from the original rig, zBuilder allows you to interpolate data (eg: maps) to work on the new geometry.

.. toctree::
	:maxdepth: 2

	zBuilder_tutorials
	zBuilder_api_reference
	zBuilder_extensions
	whats_changed