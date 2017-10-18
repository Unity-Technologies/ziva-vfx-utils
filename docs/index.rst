Welcome to Ziva's VFX Utilities!
================================

These are the docs for Ziva's VFX python utilities.  You can find the Bit Bucket repo for these tools
`here <https://bitbucket.org/zivadynamics/ziva-vfx-utils>`_.

`Ziva Dynamics <http://zivadynamics.com>`_

.. toctree::
    :maxdepth: 1
    :caption: Contents

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
.. currentmodule:: zBuilder.parameters.base

.. autoclass:: BaseParameter

   .. automethod:: __init__
   .. automethod:: serialize


   .. rubric:: Methods

   .. autosummary::

      ~BaseParameter.__init__
      ~BaseParameter.serialize
      ~BaseParameter.build
      ~BaseParameter.write

   .. rubric:: Attributes

   .. autosummary::

      ~BaseParameter.name
      ~BaseParameter.type
