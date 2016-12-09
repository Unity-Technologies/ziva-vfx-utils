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

    z.retrieve_from_scene('zSolver1')

Once we have that we can do a few things.  One thing is to save on disk::

    z.write('C:\\Temp\\test.ziva')

all at once::

    import zBuilder.setup.Ziva as zva
    z = zva.ZivaSetup()
    z.retrieve_from_scene('zSolver1')
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
mirroring is just using search and replace.  It for now, assumes that the geo 
is topologically mirrored.  Sometimes you need to do a couple seach and replaces
and you do that like so::

    z.string_replace('^r_','l_')
    z.string_replace('_r_','_l_')

that will again replace `r_` with `l_` if at beinging of line AND replace `_r_`
with `_l_` andwhere it finds it.  

currently for mirroring to work the zNodes need to be named with some naming 
convention that can be search and replacable so it can identify opposite side.

