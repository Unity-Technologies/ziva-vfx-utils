Glossary
========

.. glossary::
    :sorted:

    Scene Panel 2
        The original Scene Panel has been updated to provide a better user experience
        by providing a split view window, and integrating the Ziva VFX Menu and shelf features.

    Scene Panel
        A Maya UI to help you navigate scenes containing Ziva rigs.

    parameter
        A specific piece of data in the Maya scene, for example a mesh or an attribute of a node. These are the secondary type of :term:`scene item` managed by a :term:`builder`, and are always associated in some way with the :term:`nodes<node>` in the scene.

    builder
        The main entry point into using zBuilder. A builder object manages a list of :term:`scene items<scene item>`.
        There are different types of specialized builders, each one defining what types of :term:`nodes<node>` and
        :term:`parameters<parameter>` they allow you to inspect, modify and build in the Maya scene.

    node
        A Maya dependency graph (DG) node. These are the fundamental building blocks that define the state of a Maya scene. Therefore they are the primary :term:`scene items<scene item>` that a :term:`builder` retrieves from and rebuilds into a scene.

    body
        (simulation body) Bone, tissue or cloth objects.

    build()
        The act of assembling a Maya scene from the :term:`scene items<scene item>` stored in a :term:`builder` object.

    retrieve()
        Capturing the Maya scene with a :term:`builder` and storing it as a set of :term:`scene items<scene item>` in the :term:`builder` object.

    map
        A type of :term:`parameter` consisting of per-vertex data on a mesh, typically created in Maya through the weight painting tool. Commonly used by deformers, as well as many Ziva nodes.

    scene item
        :term:`Nodes<node>` and associated :term:`parameters<parameter>` that together define the current state of a scene in Maya. These are the items that a :term:`builder` retrieves from the scene, allowing you to inspect them, modify them, and re-apply them to a scene at a later time.

    zNode
        A Maya DG node specific to Ziva. Examples include zTet, zTissue, zAttachment, etc.

    rig
        The set of all components that go into creating an animatable character in Maya. A typical Ziva rig includes geometry defining the shape of the anatomy, and a suite of dependency graph nodes that define the physical characteristics of all the simulation :term:`bodies<body>`. Often used interchangeably with :term:`setup`.

    setup
        Used as a synonym for :term:`rig` in the context of creating characters in Maya with Ziva VFX.