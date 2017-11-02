Glossary
********

    Throughout the Ziva VFX Utils you can find the use of this terminology.  Kept here
    for clarity and consistency.

.. glossary::
    :sorted:

    zUi
        A maya UI to help you navigate the scene.  Currently Beta.

    parameter
        A specific piece of data in the Maya scene, for example a mesh or an attribute of a node. These are the secondary type of scene item managed by a builder, and are always associated in some way with the nodes in the scene.

    bundle
        A collection of parameters.

    Builder
        The main entry point into using zBuilder. A builder object  manages a bundle of scene items.
        There are different types of specialized builders, each one defining what types of nodes and
        parameters they allow you to inspect, modify and build in the Maya scene.

    Builders
        Inherited from Builder.  These are a specialized builder that helps define what
        part of the maya scene to inspect, modify and build.

    node
        A Maya dependency graph (DG) node. These are the fundamental building blocks that define the state of a Maya scene. Therefore they are the primary scene items that a Builder retrieves from and rebuilds into a scene.

    body
        (simulation body) Bone, tissue or cloth objects.

    build()
        The act of using a builder to assemble a Maya scene from the scene items stored in that builder.

    retrieve()
        Capturing the Maya scene with a builder and storing it as a set of scene items in the builder object.

    map
        A type of parameter consisting of per-vertex data on a mesh, typically created in Maya through the weight painting tool. Commonly used by deformers, as well as many Ziva nodes.

    Scene Item

        Nodes and associated parameters that together define the current state of a scene in Maya. These are the items that a builder retrieves from the scene, allowing you to inspect them, modify them, and re-apply them to a scene at a later time.

    zNode

        A Maya DG node specific to ziva. Examples include zTet, zTissue, zAttachment, etc.
