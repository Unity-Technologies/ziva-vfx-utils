Welcome to Ziva's VFX Utilities!
================================


.. toctree::
    :maxdepth: 1
    :caption: Contents:

    installation
    release
    contributing

.. currentmodule:: zBuilder

.. autosummary::

    sphinx.environment.BuildEnvironment
    sphinx.util.relative_uri
    zBuilder.builder.Builder

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

WHAT
====

.. currentmodule:: zBuilder.builder

.. autoclass:: Builder


   .. automethod:: __init__
   .. automethod:: parameter_factory


   .. rubric:: Methods

   .. autosummary::

      ~Builder.__init__
      ~Builder.parameter_factory
      ~Builder.retrieve_from_scene
      ~Builder.retrieve_from_file

   .. rubric:: Attributes

   .. autosummary::

      ~Builder.info
      ~Builder.bundle

