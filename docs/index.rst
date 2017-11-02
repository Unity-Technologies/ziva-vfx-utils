.. include:: introduction.rst

.. toctree::
    :maxdepth: 1
    :caption: Contents

    introduction
    installation
    packages
    release
    contributing
    glossary


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
.. currentmodule:: zBuilder.nodes.base

.. autoclass:: Base

   .. automethod:: __init__
   .. automethod:: serialize


   .. rubric:: Methods

   .. autosummary::

      ~Base.__init__
      ~Base.serialize
      ~Base.build
      ~Base.write

   .. rubric:: Attributes

   .. autosummary::

      ~Base.name
      ~Base.type

.. automodule:: SomeModuleName