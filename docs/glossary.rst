Glossary
********

    Throughout the Ziva VFX Utils you can find the use of this terminology.  Kept here
    for clarity and consistency.

.. glossary::
    :sorted:

    zBuilder
        A python package used to serialize and deserialize Maya scenes.

    parameter
        Represents a specific part of the maya scene with the ability to retrieve it and to re-build it.

    bundle
        A collection of parameters.

    Builder
        The main entry point into using zBuilder.  The builder manages the parameters and bundle.

    Builders
        Inherited from Builder.  These are a specialized builder that helps define what
        part of the maya scene to inspect, modify and build.

    node
        Use of the term node is referring to a maya dg node.

    body
        Maya dg node that is a solid object in simulation (tissue, bone or cloth).

    zNode
        A maya dg node specific to ziva.  zTet, zTissue, zAttachment, etc.

    build()
        The act of using a builder to interactively assemble a maya scene from the parameters.

    retrieve()
        Capturing the maya maya scene through the builder and storing them as parameters in the bundle.
