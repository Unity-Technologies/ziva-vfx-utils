packages
========

zBuilder
--------

zBuilder is a python package framework to help serialize and deserialize content
from Maya scenes.  The idea being that you interactively build something in Maya and
with zBuilder you can save that state and save it out and re-build it.

If we save a Ziva rig for example, zBuilder would write out a json file representing the
Ziva nodes for example.  With that would be the attributes and values and some
basic relationship information.  With that you could bring in your geometry and
build a new rig.  If the geometry is of differing topology you could interpolate the
maps to work on new geo.

.. include:: zBuilder_tutorials.rst
.. include:: zBuilder_api_reference.rst

extending
~~~~~~~~~

To come....

zUI
---