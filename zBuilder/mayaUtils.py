from maya import cmds
from maya import OpenMaya as om

'''
The module contains helper functions depends on Maya Python API.
'''

def get_short_name(node_name):
    # type: (str) -> str
    '''
    Return short name of Maya node, if it's already short name, return it as is.
    '''
    return node_name.split('|')[-1]


def safe_rename(old_name, new_name):
    """
    Same as cmds.rename but does not throw an exception if renaming failed
    Useful if need to rename all the nodes that are not referenced
    """
    if old_name != new_name:
        try:
            return cmds.rename(old_name, new_name)
        except RuntimeError:
            pass

    return old_name

def get_mdagpath_from_mesh(mesh_name):
    """ Maya stuff, getting the dagpath from a mesh name

    Args:
        mesh_name: The mesh to get dagpath from.
    """
    mesh_m_dag_path = om.MDagPath()
    sel_list = om.MSelectionList()
    sel_list.add(mesh_name)
    sel_list.getDagPath(0, mesh_m_dag_path)

    return mesh_m_dag_path

def get_name_from_m_object(m_object, long_name=True):
    """ Gets maya scene name from given mObject.
    Args:
        m_object: The m_object to get name from.
        long_name: Returns long name. Default = ``True``

    Returns:
        str: Maya object name.

    """
    if m_object.hasFn(om.MFn.kDagNode):
        dagpath = om.MDagPath()
        om.MFnDagNode(m_object).getPath(dagpath)
        if long_name:
            name = dagpath.fullPathName()
        else:
            name = dagpath.partialPathName()
    else:
        name = om.MFnDependencyNode(m_object).name()
    return name

