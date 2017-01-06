Tutorials
=========
zBuilder saves the current state of the ziva setup and allows you to re-build
scene amoung other things.  For example searching and replacing and using that
to mirror setups.  The basic idea is to build a ziva setup by hand and use these 
scripts to save it.

Saving and Loading Setup
------------------------

To build we need to instantiate a :class:`zBuilder.setup.Ziva.ZivaSetup` object and we do it like so::

    import zBuilder.setup.Ziva as zva
    z = zva.ZivaSetup()

once we have that we need to fill it with what is in maya scene like so::

    z.retrieve_from_scene()

This command works on selection.  It gets the setup from any ziva node selected including tissue or bone geo.  If nothing is selected it grabs a solver in the scene.  

Once we have that we can do a few things.  One thing is to save on disk::

    z.write('C:\\Temp\\test.ziva')

all at once::

    import zBuilder.setup.Ziva as zva
    z = zva.ZivaSetup()
    z.retrieve_from_scene()
    z.write('C:\\Temp\\test.ziva')

to load it from disk we retrieve it from file::

    import zBuilder.setup.Ziva as zva
    z = zva.ZivaSetup()
    z.retrieve_from_file('C:\\Temp\\test.ziva')






Building Setup
--------------
Assuming we have the 'z' object loaded with setup we want, to build we do a::

    z.apply()

note that this works on a clean scene with only the geo or an existing setup.
with an exisitng setup if it finds the same node it updates properties and maps.

Maps
----
this stores the mesh information so if you updated geo with different topology it 
will interpolate maps in world space.  By default, it checks if it needs to
and if it doesn't it ignores this step.  To force it or turn it off use this flag::

    z.apply(interp_maps='auto')

''True'' = always interp maps
''False'' = Never interp maps
''auto'' = checks if needed

Search and replace
------------------
to search and replace you can do a::

    z.string_replace('r_bicep_muscle22','r_bicep_muscle')

That will replace all instances of `r_bicep_muscle22` with `r_bicep_muscle`
you can feed it regular expressions so this::
    
    z.string_replace('^r_','l_')

will replace `r_` with `l_` IF it is at begining of line.

Mirroring Setup
---------------
Earlier I showed you about retrieve_from_scene.  For mirroring it is best to use::

    z.retrieve_from_scene_selection()

That method will use selection to fill the data.  Use case is to select your left muscles for example and mirror them.  So lets try it::

    # select left muscles in scene
    z = zva.ZivaSetup()
    z.retrieve_from_scene_selection()
    z.string_replace('^l_','r_')
    z.apply()

What that does is put the left muscles in object and does searches for `l_` at begining of name and replaces with `r_`.  Sometimes you need to do a couple seach and replaces
and you do that like so::

    z = zva.ZivaSetup()
    z.retrieve_from_scene_selection()
    z.string_replace('^l_','r_')
    z.string_replace('_l_','_r_')
    z.apply()

that will again replace `l_` with `r_` if at beinging of line AND replace `_l_`
with `_r_` andwhere it finds it.  

currently for mirroring to work the zNodes need to be named with some naming 
convention that can be search and replacable so it can identify opposite side.

