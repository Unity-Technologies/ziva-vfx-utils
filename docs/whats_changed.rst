Whats changed in 1.0.0
----------------------

zBuilder 1.0.0 is backwards compatible with previous versions but some of command names
have changed.  For the most part it will be unnoticeable but a few things have changed
in how zBuilder is accessed.  For instance:

.. code-block:: python

    # pre 1.0.0 instantiating object
    import zBuilder.setup.Ziva as zva
    z = zva.ZivaSetup()

    # 1.0.0
    import zBuilder.builders.ziva as zva
    z = zva.Ziva()


Building has changed as well.  Previously that was called 'apply'

.. code-block:: python

    # pre 1.0.0 instantiating object
    import zBuilder.setup.Ziva as zva
    z = zva.ZivaSetup()
    z.apply()

    # 1.0.0
    import zBuilder.builders.ziva as zva
    z = zva.Ziva()
    z.build()


At the higher level just remember "setups" are now "builders" and "apply" is now "build".