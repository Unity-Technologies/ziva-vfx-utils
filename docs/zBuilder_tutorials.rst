Tutorials
~~~~~~~~~

I'll bring you through some example usage of this in terms of Ziva and I will be
doing it on the demo arm that ships with the plugin so if you want to follow along
it should be easy.

First thing is to run the demo arm.  You can find that in the 'Ziva Tools' menu.
Examples/Run Demo/Anatomical Arm.  Now that we have that in our scene Lets start
playing with zBuilder.

Retrieving
^^^^^^^^^^

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

Items captured in this case are:

* All the Ziva nodes. (zTissue, zTet, zAttachment, etc..)
* Order of the nodes so we can re-create material layers reliably.
* Attributes and values of the nodes. (Including weight maps)
* Sub-tissue information.
* User defined tet mesh reference.  (Not the actual mesh)
* Any embedded mesh reference. (Not the actual mesh)
* Curve reference to drive zLineOfAction. (Not actual curve)
* Relevant zSolver for each node.
* Mesh information used for world space lookup to interpolate maps if needed.

Building
^^^^^^^^

Building takes the information from retrieving and applying it back into the scene.
The expectation is that you have a scene with geometry in it and it builds with that geo.  zBuilder will
not re-create the geometry.  The geometry can have a Ziva setup on it already or not, just as long as the geo is already in scene.

Building to restore scene to previous state
*******************************************

To restore the scene first we need to make a change to the arm so we can confirm
it restored it.  So paint a muscle attachment to all white for example, just
something that is easy to identify in viewport.  Once that is done, if you
have been following along, you can build it.

.. code-block:: python

    z.build()

Now after that you should see in viewport the state of the arm setup jump back to
when you retrieved it, as well as this output in script editor.

.. code-block:: python

    # zBuilder.builders.ziva : Building.... #
    # zBuilder.builder : Finished: ---Elapsed Time = 0:00:01.139000 #

.. note::

    When you .build() in maya on an existing scene it does a few things.  It checks
    if parameter in builder exists in scene.  If it doesn't exist it tries to build
    it in scene.  If it does exist, it updates the scene to what is in builder.

Building to build a Ziva setup from scratch
*******************************************
The first example showed how to build with a Ziva setup in the scene.  That will
update the scene setup to match what is in the builder object.

Second example we will build from scratch, meaning there is no Ziva in scene at all.
The command is exactly the same, only difference is the lack of and Ziva nodes.

First thing we do on arm in scene is clean out Ziva setup then we build.

.. code-block:: python

    import zBuilder.zMaya as mz
    mz.clean_scene()

That is a utility function to cleanup all of the Ziva footprint in the scene.  If you look in scene
the solver should be gone.  Now that we have a scene with just models in it if
we build that same builder it will build all the Ziva maya nodes for us.

.. code-block:: python

    z.build()

With that, you can manage bringing in any geometry and building a Ziva scene on it as long as you
captured the state previously.  Simply replace the mz.clean_scene() with an importing of the desired
geometry.

Building with differing topologies
**********************************

In production a common case unfortunately is the geometry vert count will change and you will have
to deal with it.  Lets show how we can accommodate geometry changing.

First thing, lets clean scene to represent new geometry coming in.

.. code-block:: python

    import zBuilder.zMaya as mz
    mz.clean_scene()

Now change the bicep for example.  A quick way is to apply a mesh smooth.  Once the
bicep is a different topology simply build the same way as before again.

.. code-block:: python

    z.build()

Now your script editor output will be slightly different.  It should be as below:

.. code-block:: python

    # zBuilder.builders.ziva : Building.... #
    # zBuilder.parameters.maps : interpolating map:  r_bicep_muscle_zTet.weightList[0].weights #
    # zBuilder.parameters.maps : interpolating map:  r_bicep_muscle_zMaterial.weightList[0].weights #
    # zBuilder.parameters.maps : interpolating map:  r_bicep_muscle_r_brachialis_muscle.weightList[0].weights #
    # zBuilder.parameters.maps : interpolating map:  r_bicep_muscle_r_brachialis_muscle.weightList[1].weights #
    # zBuilder.parameters.maps : interpolating map:  r_bicep_muscle_r_humerus_bone.weightList[0].weights #
    # zBuilder.parameters.maps : interpolating map:  r_bicep_muscle_r_humerus_bone.weightList[1].weights #
    # zBuilder.parameters.maps : interpolating map:  r_bicep_muscle_r_radius_bone.weightList[0].weights #
    # zBuilder.parameters.maps : interpolating map:  r_bicep_muscle_r_radius_bone.weightList[1].weights #
    # zBuilder.parameters.maps : interpolating map:  r_bicep_muscle_r_scapula_bone.weightList[0].weights #
    # zBuilder.parameters.maps : interpolating map:  r_bicep_muscle_r_scapula_bone.weightList[1].weights #
    # zBuilder.parameters.maps : interpolating map:  r_bicep_muscle_zFiber.weightList[0].weights #
    # zBuilder.parameters.maps : interpolating map:  r_bicep_muscle_zFiber.endPoints #
    # zBuilder.builder : Finished: ---Elapsed Time = 0:00:03.585000 #

You will notice above that it listed out all the maps that got interpolated.

.. note::

    When the maps get interpolated it is based on world space of the stored geometry.
    So, if the muscle changes enough where it is in a different world space location,
    or maybe part of it is the interpolation won't work too well.

Writing to disk
^^^^^^^^^^^^^^^

Now that we have the arm setup in builder object in memory we can write it out to disk.  All we need to do is

.. code-block:: python

        # replace path with a working temp directory on your system
        z.write('C:\\Temp\\test.ziva')

This writes out a json file of all the information to retrieve later.


Reading from disk
^^^^^^^^^^^^^^^^^

To test the writing worked properly lets setup the scene with just the geometry again.
Build Anatomical Arm demo again then clean scene.

Once we have the arm geometry in the scene lets grab it from the disk then build it.

.. code-block:: python

    import zBuilder.builders.ziva as zva
    z = zva.Ziva()
    z.retrieve_from_file('C:\\Temp\\test.ziva')

You should have seen something like this in your script editor.

.. code-block:: python

    z.retrieve_from_file('C:\\Temp\\test.ziva')
    # zBuilder.builder : reading parameters. 134 nodes #
    # zBuilder.builder : reading info #
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
    # zBuilder.builder : Read File: C:\Temp\test.ziva in 0:00:00.052000 #

This is a simple output to give you a hint of what has been retrieved.  Now we can build.

.. code-block:: python

    z.build()

If you have been following along the output should look like this again as there would
be no map interpolation.

.. code-block:: python

    # zBuilder.builders.ziva : Building.... #
    # zBuilder.builder : Finished: ---Elapsed Time = 0:00:03.578000 #


String Replacing
^^^^^^^^^^^^^^^^

You can do basic string replace operations on the information stored in the builder.  This is very useful
if you have name changes on the geometry you are dealing with or even as a basic mirror.

When you do a string replace you give it a search and replace term.  It looks for all the references of the
search term and does a replace.  In the context of Ziva it will search and replace
node names, map names (zAttachment1.weights for example), curve names for zLineOfAction, any mesh name (embedded, user tet).

This works with regular expressions as well.  With that you can say search for only a 'r_' at beginning
of name.

Lets build the Anatomical Arm demo from the Ziva menu. Then we can retrieve the setup into builder.

.. code-block:: python

    import zBuilder.builders.ziva as zva
    z = zva.Ziva()
    z.retrieve_from_scene()

To represent a model name change lets clean the scene and change the name of a muscle.

.. code-block:: python

    import zBuilder.zMaya as mz
    mz.clean_scene()

    mc.rename('r_bicep_muscle', 'r_biceps_muscle')

Now the information in the builder is out of sync.  We can update it by doing the following
