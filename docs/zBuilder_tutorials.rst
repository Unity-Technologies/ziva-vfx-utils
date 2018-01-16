Tutorials
---------

Tutorial -- Basics
~~~~~~~~~~~~~~~~~~

Let's explore some example usage of zBuilder by trying it out on the anatomical
arm demo that ships with the ZivaVFX Maya plugin. First, set the Python path 
to zBuilder as explained in the :doc:`installation` section.

First, run the anatomical arm demo, which can be found in the 'Ziva Tools' menu:
Ziva Tool > Examples > Run Demo > Anatomical Arm.
Now that you have the arm :term:`setup` in your scene, let's start playing with zBuilder.

Retrieving the Ziva rig from the Maya scene
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Retrieving a whole Ziva rig
***************************

In order to interact with a Ziva scene with zBuilder, we first need to create a 
Ziva :term:`builder` object:

.. code-block:: python

    import zBuilder.builders.ziva as zva
    z = zva.Ziva()

You can use the help command to get some information about the Ziva builder.

.. code-block:: python

    help(z)

We can use our builder to capture the Ziva arm rig by running a method to retrieve the current state of the Ziva Maya scene:

.. code-block:: python

    z.retrieve_from_scene()

When you run this command, you should see output that looks something like this in your script editor:

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

These are the stats about which :term:`scene items<scene item>` were retrieved
by the builder.
In this case you can see there are 7 zTissues, 4 zBones, etc.
Scene items typically fall into two categories:

* :term:`Nodes<node>`, which are the Maya dependency graph nodes in the scene.
* :term:`Parameters<node>`, which are the relevant pieces of data associated with nodes, like meshes and :term:`maps<map>`.

To give you a sense of the complexity that zBuilder is handling for you here, the scene items captured in this case are:

* All the Ziva nodes. (zTissue, zTet, zAttachment, etc..)
* Order of the nodes so we can re-create material layers reliably.
* Attributes and values of the nodes. (Including weight maps)
* Sub-tissue information.
* User defined tet mesh reference.  (Not the actual mesh)
* Any embedded mesh reference. (Not the actual mesh)
* Curve reference to drive zLineOfAction. (Not actual curve)
* Relevant zSolver for each node.
* Mesh information used for world space lookup to interpolate maps if needed.

Fortunately, zBuilder handles all this data for you, allowing you to treat all the complexity of a Ziva :term:`rig` as a single logical object.
You can then save it out to a text file, and/or restore the rig to the captured state at a later time.
You can also manipulate the information in the builder before re-applying it.
This is useful for mirroring, for example, which we'll describe later.

Retrieving parts of a Ziva rig
******************************

Above, we retrieved Ziva builder data from the entire Maya scene.
However, if you only want to capture a part of the scene, you can select the items
you are interested in and call retrieve_from_scene_selection().
This comes in handy if you want to mirror the setup, for example.

.. code-block:: python

    import maya.cmds as mc
    mc.select('r_bicep_muscle')
    import zBuilder.builders.ziva as zva
    z = zva.Ziva()
    z.retrieve_from_scene_selection()

By default retrieve_from_scene_selection() grabs all items that are connected to the selected items. In this example, therefore, it grabs the fibers and attachments connected to the muscle in addition to the muscle itself.
Your script editor output should have looked something like this:

.. code-block:: python

    # zBuilder.bundle : zTissue 1 #
    # zBuilder.bundle : map 12 #
    # zBuilder.bundle : zAttachment 4 #
    # zBuilder.bundle : zMaterial 1 #
    # zBuilder.bundle : zEmbedder 1 #
    # zBuilder.bundle : zBone 3 #
    # zBuilder.bundle : zTet 1 #
    # zBuilder.bundle : mesh 5 #
    # zBuilder.bundle : zSolver 1 #
    # zBuilder.bundle : zSolverTransform 1 #
    # zBuilder.bundle : zFiber 1 #
    # zBuilder.builder : Finished: ---Elapsed Time = 0:00:00.166000 #

Notice now we are only retrieving 1 tissue.


Building
^^^^^^^^

Building takes the data stored in a builder object, and applies it to the Maya scene, equipping it with the Ziva rig stored in the builder object.

.. note::

    zBuilder does not currently re-create geometry.
    The expectation is that any geometry required by the rig will already exist in the scene, and the builder will then apply the rig onto it.
    It's fine if the geometry is already being used in a Ziva rig, just as long as the geometry is already in scene.

With the exception of geometry, building restores the state of all the nodes and parameters in the builder. Each scene item is first checked to see if it exists in the Maya scene. If it doesn't exist, it is created. If it does exist, its data values are set to what is stored in the builder.

Restoring a Ziva rig to a previous state
****************************************

This simple example demonstrates how to revert the Ziva rig to a previous state.
First, load the Anatomical Arm Demo. Then, let's capture the whole scene, so that we can later restore it.

.. code-block:: python

    import zBuilder.builders.ziva as zva
    z = zva.Ziva()
    z.retrieve_from_scene()

Now, the builder object "z" contains the Ziva rig.
Let's make a change to the arm. 
For example, paint a muscle attachment to all white,
something that is easy to identify in viewport.
Now let's apply our builder to it, to revert the rig to the previous state.

.. code-block:: python

    z.build()

In the viewport, you should see that the state of the arm rig jumped back to the way it 
was when you retrieved it, as well as this output in the script editor:

.. code-block:: python

    # zBuilder.builders.ziva : Building.... #
    # zBuilder.builder : Finished: ---Elapsed Time = 0:00:01.139000 #


Building a Ziva rig from scratch
********************************

It is also possible to build a Ziva rig into a Maya scene that doesn't contain any Ziva nodes or data.
The command is exactly the same as before, but we'll start from a "clean" scene containing only geometry.

First, clean out the entire Ziva rig with the following command:

.. code-block:: python

    import zBuilder.zMaya as mz
    mz.clean_scene()

clean_scene() is a utility function to remove all of the Ziva footprint in the scene.
If you look in the scene the Ziva solver nodes should now be gone.

Now that we have a scene with just geometry in it, let's see what happens when
we apply that same builder.

.. code-block:: python

    z.build()

The full Ziva rig should now be restored and acting on the scene's geometry.
zBuilder built all of the Ziva maya nodes for us.

Building with differing topologies
**********************************

In production a common occurrence (unfortunately) is the geometry that goes into your rig will change and you will be the one who has to deal with it.

Let's show how zBuilder can accommodate changes to geometry.

First thing, let's clean the scene to represent brand new geometry coming in.

.. code-block:: python

    import zBuilder.zMaya as mz
    mz.clean_scene()

Now change the bicep for example.  A quick way is to apply a mesh smooth.  Once the
bicep has a different topology simply build the same way as before again.

.. code-block:: python

    z.build()

This time your script editor output will be slightly different.  It should be as below:

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

You will notice above that it listed out a bunch of maps that got interpolated.
This shows that zBuilder noticed the change in topology between the mesh in the
original rig and the new rig.
Furthermore, the call to build() modified all the maps painted onto the old
mesh and re-applied them to the new mesh by interpolation.

.. note::

    When the maps get interpolated it is currently done in world space of the stored geometry.
    So, if a muscle's new geometry is in a significantly different position in world space, the interpolation may not work very well.
    However, it should be fine in cases where the position and shape of the muscle only make relatively small changes.

With this feature, you can manage bringing in any new geometry and building a
previously-captured Ziva scene on it.
Typically you will import the desired geometry into a scene from an external
source instead of editing it directly in Maya (also ensure that it's given the same name as the original mesh it's replacing in the rig).


Reading/Writing Files
^^^^^^^^^^^^^^^^^^^^^

Writing to disk
***************

Once we have the arm Ziva rig saved into a builder object in memory, we can write it out to disk.  All we need to do is:

.. code-block:: python

        # replace path with a working temp directory on your system
        z.write('C:\\Temp\\test.ziva')

This writes out a json file of all the information so it can be retrieved later.


Reading from disk
*****************

To test that writing worked properly let's setup the scene with just the geometry again.
Run the Anatomical Arm demo again, then run mz.clean_scene().

Once we have a scene with just the arm geometry, let's retrieve the Ziva rig from the file on disk.

.. code-block:: python

    import zBuilder.builders.ziva as zva
    z = zva.Ziva()
    # Use the same path here that you used above.
    z.retrieve_from_file('C:\\Temp\\test.zBuilder')

You should see something like this in your script editor:

.. code-block:: python

    z.retrieve_from_file('C:\\Temp\\test.zBuilder')
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
    # zBuilder.builder : Read File: C:\Temp\test.zBuilder in 0:00:00.052000 #

Like before, this is a simple printout to give you a hint of what has been loaded from the file.  Now we can build:

.. code-block:: python

    z.build()

If you have been following along the output should look like this again as there would have been no map interpolation.

.. code-block:: python

    # zBuilder.builders.zBuilder : Building.... #
    # zBuilder.builder : Finished: ---Elapsed Time = 0:00:03.578000 #

The Anatomical Arm rig should now be completely restored back to its original state.


String Replacing
^^^^^^^^^^^^^^^^

You can do basic string replace operations on the information stored in a builder.
This is very useful if you have name changes of the geometry you are dealing with, or even to create a basic mirroring of the rig.

When you do a string replace you provide a search term and a replace term.
In the context of the Ziva builder it will search and replace:

* node names
* map names (zAttachment1.weights for example)
* curve names for zLineOfAction
* any mesh name (embedded, user tet)

This works with regular expressions as well.
For example you can search for occurrences of "r_" at the beginning of a name.

Changing geometry name
**********************

As before, let's build the Anatomical Arm demo from the Ziva menu and retrieve the Ziva rig into a builder object.

.. code-block:: python

    import zBuilder.builders.ziva as zva
    z = zva.Ziva()
    z.retrieve_from_scene()

To represent a model name change let's clean the scene and change the name of one of the muscles.

.. code-block:: python

    import zBuilder.zMaya as mz
    mz.clean_scene()

    mc.rename('r_bicep_muscle', 'r_biceps_muscle')

Now the information in the builder is out of sync with the geometry in the scene.
We can update it by doing the following:

.. code-block:: python

    z.string_replace('r_bicep_muscle','r_biceps_muscle')

Now when we build you see that the newly-named muscle is correctly integrated into the rig, and all the maps painted on that mesh have had their names corrected as well.

.. code-block:: python

    z.build()

Mirroring a setup
*****************

We can also use string replace to mirror half of a Ziva rig into a full symmetric Ziva rig.

In order for this to work the geometry needs to be already-mirrored,
with r_* and l_* prefixes used to distinguish between each pair of mirrored meshes.
Assuming you have already created a rig on the right-side of the character,
you will then tell the builder to replace r_muscle with l_muscle
(note that all zBuilder will be doing here is changing names, so it expects all of
the l_muscle meshes to already be in the scene).

Let's run a little test scene that sets up 2 spheres and a cube with 1 attachment.

.. code-block:: python

    import zBuilder.tests.utils as utl

    utl.build_mirror_sample_geo()
    utl.ziva_mirror_sample_geo()

You should see a cube and 2 spheres in your scene.
The right-side sphere "r_muscle" is a tissue and the cube is a bone, and they are connected by a single attachment.
We want to mirror this so the "l_muscle" gets a tissue
and attachment as well.
To do this we can just create and initialize a builder, perform a string replace, and then rebuild.

.. code-block:: python

    import zBuilder.builders.ziva as zva

    z = zva.Ziva()
    z.retrieve_from_scene()
    z.string_replace('^r_','l_')

Notice the *^* in the search field.
This is a regular expression to tell it to search just for an "r_" at the beginning of a name.

Now when you build you should have a mirrored setup:

.. code-block:: python

    z.build()



Tutorial -- Advanced
~~~~~~~~~~~~~~~~~~~~

Here we'll cover some of the more involved concepts.

Changing values before building
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

It's possible to inspect and modify the contents of the builder before you actually build.
For example, maybe you are in a specific shot and want to build a Ziva rig with a
value different than what was saved on disk.
A common use case is to change the start frame of the Ziva solver based on the shot environment. Let's try doing that.

Build the Anatomical Arm demo again and retrieve the scene.

.. code-block:: python

    import zBuilder.builders.ziva as zva

    z = zva.Ziva()
    z.retrieve_from_scene()

Now we need to find the scene item we want to modify, in this case the solver.  You can do that with the following code:

.. code-block:: python

    scene_items = z.get_scene_items(name_filter='zSolver1')
    print scene_items[0]

Here we're using the name filter to search for the specific item we're interested in.  You should see something like this in the script editor.

.. code-block:: python

    = zSolver1 <zBuilder.nodes.ziva.zSolverTransform SolverTransformNode> ==================================
        _builder_type - zBuilder.nodes
        solver - zSolver1Shape
        _DGNode__mobject - <maya.OpenMaya.MObject; proxy of <Swig Object of type 'MObject *' at 0x000001E90F8E9690> >
        _name - |zSolver1
        _association - []
        attrs - {u'enable': {'locked': False, 'type': u'bool', 'value': True, 'alias': None}, u'translateX': {'locked': False, 'type': u'doubleLinear', 'value': 0.0, 'alias': None}, u'translateY': {'locked': False, 'type': u'doubleLinear', 'value': 0.0, 'alias': None}, u'translateZ': {'locked': False, 'type': u'doubleLinear', 'value': 0.0, 'alias': None}, u'scaleX': {'locked': False, 'type': u'double', 'value': 100.0, 'alias': None}, u'scaleY': {'locked': False, 'type': u'double', 'value': 100.0, 'alias': None}, u'visibility': {'locked': False, 'type': u'bool', 'value': True, 'alias': None}, u'rotateX': {'locked': False, 'type': u'doubleAngle', 'value': 0.0, 'alias': None}, u'rotateY': {'locked': False, 'type': u'doubleAngle', 'value': 0.0, 'alias': None}, u'rotateZ': {'locked': False, 'type': u'doubleAngle', 'value': 0.0, 'alias': None}, u'scaleZ': {'locked': False, 'type': u'double', 'value': 100.0, 'alias': None}, u'startFrame': {'locked': False, 'type': u'double', 'value': 1.0, 'alias': None}}
        _class - ('zBuilder.nodes.ziva.zSolverTransform', 'SolverTransformNode')
        type - zSolverTransform
        builder - <zBuilder.builders.ziva.Ziva object at 0x000001E90FDB97B8>

That's all the information that the builder has stored for the solver scene item.
To query and change the attributes you go through the ``attrs`` dictionary like so:

.. code-block:: python

    print 'Before:', scene_item[0].attrs['startFrame']['value']
    # set the value of startFrame to 10
    scene_item[0].attrs['startFrame']['value'] = 10
    print 'After:', scene_item[0].attrs['startFrame']['value']

In the above example we're printing the value of start frame before and after we change it.

Now if you apply the builder, the startFrame of the zSolver1 node will be given the new value you set.
As before, the new value is applied whether or not the zSolver1 node already existed in the scene before the call to build().

.. code-block:: python

    z.build()

