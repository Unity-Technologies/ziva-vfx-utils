API Reference
~~~~~~~~~~~~~

.. currentmodule:: zBuilder.builders.ziva

.. autoclass:: Builder

    .. automethod:: write(file_path, type_filter=list(), invert_match=False)

    .. automethod:: retrieve_from_file(file_path)

    .. automethod:: string_replace(search, replace)

    .. automethod:: stats()

    .. automethod:: print_(type_filter=[], name_filter=[])

.. currentmodule:: zBuilder.builders.ziva

.. autoclass:: Ziva

    .. automethod:: retrieve_from_scene

    .. automethod:: build(name_filter=None, attr_filter=None, interp_maps='auto', mirror=False, permissive=True, check_meshes=True)


