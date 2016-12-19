maplist = {}

maplist['zTet'] = ['weightList[0].weights']
maplist['zMaterial'] = ['weightList[0].weights']
maplist['zFiber'] = ['weightList[0].weights','endPoints']
maplist['zAttachment'] = ['weightList[0].weights','weightList[1].weights']

niceMaplist = {}
niceMaplist['zTet'] = ['weights']
niceMaplist['zMaterial'] = ['weights']
niceMaplist['zFiber'] = ['weights','endPoints']
niceMaplist['zAttachment'] = ['source','target']

ZNODES = [
        #'zGeo',
        'zSolver',
        'zSolverTransform',
        #'zIsoMesh',
        #'zDelaunayTetMesh',
        'zTet',
        'zTissue',
        'zBone',
        #'zShell',
        'zSolver',
        'zCache',
        'zEmbedder',
        'zAttachment',
        'zMaterial',
        'zFiber',
        #'zCacheTransform'
        ]