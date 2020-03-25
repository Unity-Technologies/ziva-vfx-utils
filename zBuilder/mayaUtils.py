def get_short_name(node_name):
    # type: (str) -> str
    '''
    Return short name of Maya node, if it's already short name, return it as is.
    '''
    return node_name.split('|')[-1]