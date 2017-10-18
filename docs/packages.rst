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


Example Usage
~~~~~~~~~~~~~

I'll bring you through some example usage of this in terms of Ziva and I will be
doing it on the demo arm that ships with the plugin so if you want to follow along
it should be easy.

First thing is to run the demo arm.  You can find that in the 'Ziva Tools' menu.
Examples/Run Demo/Anatomical Arm.  Now that we have that in our scene Lets start
playing with zBuilder.

.. code-block:: python

    import zBuilder.builders.ziva as zva
    z = zva.Ziva()

You can call help to get some information.

.. code-block:: python

    help(z)

To capture the arm scene into something zBuilder can use run a retrieve method.
In this case we want to retrieve from the scene.

.. code-block:: python

    z.retrieve_from_scene()

You should have seen something like this in your script editor.

.. code-block:: python

    # zBuilder.bundle : zTissue 7 #
    # zBuilder.bundle : map 68 #
    # zBuilder.bundle : zAttachment 21 #
    # zBuilder.bundle : zMaterial 7 #
    # zBuilder.bundle : zEmbedder 1 #
    # zBuilder.bundle : zBone 4 #
    # zBuilder.bundle : zTet 7 #
    # zBuilder.bundle : mesh 11 #
    # zBuilder.bundle : zSolver 1 #
    # zBuilder.bundle : zSolverTransform 1 #
    # zBuilder.bundle : zFiber 6 #
    # zBuilder.builder : Finished: ---Elapsed Time = 0:00:00.087000 #

When you retrieve items, it prints out the stats about what it captured.  In this
case you can see there are 7 zTissues and 4 zBones for example.

Those items in builder we call a :term:`parameter`.  They get placed in a :term:`bundle`.

This essentially saves the state of the scene.  From here we can save it out to a text file,
we can continue working on arm and use it to restore the state or we can manipulate the
information in the builder and re-apply it.  That is useful for mirroring and such
which we will get into later.

To restore the scene first we need to make a change to the arm so we can confirm
it restored it.  So paint a muscle attachment to all white for example, just
something that is easy to identify in viewport.  Once that is done, if you
have been following along, you can build it.

.. code-block:: python

    z.build()

Now after that you should see in viewport the state of the arm setup jump back to
when you retrieved it.

.. note::

    When you .build() in maya on an existing scene it does a few things.  It checks
    if parameter in builder exists in scene.  If it doesn't exist it tries to build
    it in scene.  If it does exist, it updates the scene to what is in builder.

extending
~~~~~~~~~



zUI
---