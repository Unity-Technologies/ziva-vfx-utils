zBuilder
========

At a high level, zBuilder is a python framework to help serialize and deserialize content from Maya scenes.
The basic idea is that you first interactively build a scene in Maya, 
and then with zBuilder you can save that state and re-build it.

In order to save a Ziva rig, for example, zBuilder can write out a zipped JSON file representing the Ziva nodes in the scene.
That file would contain the nodes, attribute values, and some basic information about their relationships.
zBuilder then has the ability to load that file into a scene with new geometry, and re-build the rig there.
If the new geometry's topology (i.e. triangles or number of vertices) is different from the original rig,
zBuilder allows you to interpolate data (e.g. maps) to work on the new geometry.

.. toctree::
    :maxdepth: 2

    zBuilder_tutorials

