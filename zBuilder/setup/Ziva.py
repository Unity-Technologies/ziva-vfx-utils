import zBuilder.zMaya as mz

import zBuilder.nodes.base as base
import zBuilder.nodes.zEmbedder as embedderNode
import zBuilder.nodes.zTet as tetNode

import zBuilder.data.mesh as msh
import zBuilder.data.maps as mps

import zBuilder.nodeCollection as nc

import maya.cmds as mc
import maya.mel as mm

import time
import datetime 
import logging



logger = logging.getLogger(__name__)


MAPLIST = {}
MAPLIST['zTet'] = ['weightList[0].weights']
MAPLIST['zMaterial'] = ['weightList[0].weights']
MAPLIST['zFiber'] = ['weightList[0].weights','endPoints']
MAPLIST['zAttachment'] = ['weightList[0].weights','weightList[1].weights']

ZNODES = [
        'zSolver',
        'zSolverTransform',
        'zTet',
        'zTissue',
        'zBone',
        'zCloth',
        'zSolver',
        'zEmbedder',
        'zAttachment',
        'zMaterial',
        'zFiber',
        ]




class ZivaSetup(nc.NodeCollection):
    '''
    To capture a ziva setup
    '''
    def __init__(self):
        nc.NodeCollection.__init__(self)
        for plugin in mc.pluginInfo( query=True, listPluginsPath=True ):
            cmds = mc.pluginInfo(plugin,q=True,c=True)
            if cmds:
                if 'ziva' in cmds:
                    plug=plugin.split('/')[-1]
                    continue
        #self.info['plugin_name'] = plug
        #self.info['plugin_version'] = mc.pluginInfo(plug,q=True,v=True)     

    @nc.time_this
    def retrieve_from_scene(self,*args,**kwargs):
        '''
        Retreives data from scene given any node in ziva connection.

        Args:
            attr_filter (dict):  Attribute filter on what attributes to get. 
                dictionary is key value where key is node type and value is 
                list of attributes to use.

                af = {'zSolver':['substeps']}
            get_mesh (bool): get mesh info. Defaults to True
            get_maps (bool): get map info. Defaults to True
        '''
        # args
        selection = None
        if args:
            if isinstance(args[0], (list, tuple)):
                selection = args[0]
            else:
                selection = [args[0]]

        # kwargs
        attr_filter = kwargs.get('attr_filter',None)
        get_mesh = kwargs.get('get_mesh',True)
        get_maps = kwargs.get('get_maps',True)

        try:
            if selection:
                solShape = mm.eval('zQuery -t "zSolver" -l {"'+selection[0]+'"}')
            else:
                solShape = mm.eval('zQuery -t "zSolver" -l ')

        except RuntimeError, e:
            logger.exception('No Ziva nodes found in scene. Has a solver been created for the scene yet?')
            raise StandardError, 'No Ziva nodes found in scene. Has a solver been created for the scene yet?'

        # get selection to re-apply it
        sel = mc.ls(sl=True,l=True)
        if solShape:
            solShape = solShape[0]

            logger.info('          getting ziva for {}'.format(solShape)) 

            mc.select(solShape,r=True)
            solver = mm.eval('zQuery -t "zSolverTransform" -l')[0]
            if attr_filter:
                self.__add_ziva_node(solver,get_mesh=get_mesh,get_maps=get_maps,
                    attr_filter=attr_filter.get('zSolverTransform',None))
                self.__add_ziva_node(solShape,get_mesh=get_mesh,get_maps=get_maps,
                    attr_filter=attr_filter.get('zSolver',None))
            else:
                self.__add_ziva_node(solver,get_mesh=get_mesh,get_maps=get_maps)
                self.__add_ziva_node(solShape,get_mesh=get_mesh,get_maps=get_maps)

            type_s = ['zBone','zTissue','zTet','zMaterial','zFiber','zAttachment','zCloth']

            for t in type_s:
                ZNODES = mm.eval('zQuery -t "'+t+'" -l')
                if ZNODES:
                    for zNode in ZNODES:
                        if attr_filter:
                            if t in attr_filter:
                                self.__add_ziva_node(zNode,get_mesh=get_mesh,
                                        attr_filter=attr_filter.get(t,None),get_maps=get_maps)
                        else:
                            self.__add_ziva_node(zNode,get_mesh=get_mesh,
                                    attr_filter=None,get_maps=get_maps)



            self.__retrieve_embedded_from_selection(mm.eval('zQuery -t "zTissue" -m'))
            self.stats()
        else:
            print 'no solver found in scene'
        mc.select(sel,r=True)
        

    @nc.time_this
    def retrieve_from_scene_selection(self,*args,**kwargs):

        '''
        Gets data based on selection

        Args:
            attr_filter (dict):  Attribute filter on what attributes to get. 
                dictionary is key value where key is node type and value is 
                list of attributes to use.

                af = {'zSolver':['substeps']}
            connections (bool): Gets the ziva nodes connected to selection as well. Defaults to True
            solver (bool): Gets solver data.  Defaults to True
            bones (bool): Gets bone data.  Defaults to True
            tissue (bool): Gets tissue data.  Defaults to True
            attachments (bool): Gets attachments data.  Defaults to True
            materials (bool): Gets materials data.  Defaults to True
            fibers (bool): Gets fibers data.  Defaults to True
            cloth (bool): Gets cloth data.  Defaults to True
            embedder (bool): Gets embedder data.  Defaults to True
            get_mesh (bool): get mesh info. Defaults to True
            get_maps (bool): get map info. Defaults to True

        '''

        # get current selection to re-apply
        sel = mc.ls(sl=True)

        # args
        selection = None
        if args:
            selection = mc.ls(args[0],l=True)
        else:
            selection = mc.ls(sl=True,l=True)

        # kwargs
        connections = kwargs.get('connections',True)
        attr_filter = kwargs.get('attr_filter',None)
        solver = kwargs.get('solver',True)
        bones = kwargs.get('bones',True)
        tissues = kwargs.get('tissues',True)
        attachments = kwargs.get('attachments',True)
        materials = kwargs.get('materials',True)
        fibers = kwargs.get('fibers',True)
        cloth = kwargs.get('cloth',True)
        embedder = kwargs.get('embedder',True)
        get_mesh = kwargs.get('get_mesh',True)
        get_maps = kwargs.get('get_maps',True)


        print '\ngetting ziva......'

        if not attr_filter:
            attr_filter = {}
            
        if connections:
            if solver:
                logger.info('getting solver') 
                sol = mz.get_zSolver(selection[0])
                if sol:
                    self.__add_ziva_node(sol[0],attr_filter=attr_filter.get('zSolver',None))
                    solverTransform = mz.get_zSolverTransform(selection[0])[0]
                    self.__add_ziva_node(solverTransform,attr_filter=attr_filter.get('zSolverTransform',None))
                    #mc.select(selection,r=True)

            if bones:
                logger.info('getting bones') 
                for bone in mz.get_zBones(selection):
                    self.__add_ziva_node(bone,attr_filter=attr_filter.get('zBone',None),
                        get_mesh=get_mesh,get_maps=get_maps)

            if tissues:
                logger.info('getting tissues') 
                for tissue in mz.get_zTissues(selection):
                    self.__add_ziva_node(tissue,attr_filter=attr_filter.get('zTissue',None),
                        get_mesh=get_mesh,get_maps=get_maps)

                for tet in mz.get_zTets(selection):
                    self.__add_ziva_node(tet,attr_filter=attr_filter.get('zTet',None),
                        get_mesh=get_mesh,get_maps=get_maps)

            if attachments:
                logger.info('getting attachments') 
                for attachment in mz.get_zAttachments(selection):
                    self.__add_ziva_node(attachment,attr_filter=attr_filter.get('zAttachment',None),
                        get_mesh=get_mesh,get_maps=get_maps)

            if materials:
                logger.info('getting materials') 
                for material in mz.get_zMaterials(selection):
                    self.__add_ziva_node(material,attr_filter=attr_filter.get('zMaterial',None),
                        get_mesh=get_mesh,get_maps=get_maps)

            if fibers:
                logger.info('getting fibers') 
                for fiber in mz.get_zFibers(selection):
                    self.__add_ziva_node(fiber,attr_filter=attr_filter.get('zFiber',None),
                        get_mesh=get_mesh,get_maps=get_maps)

            if cloth:
                logger.info('getting cloth') 
                for cloth in mz.get_zCloth(selection):
                    self.__add_ziva_node(cloth,attr_filter=attr_filter.get('zCloth',None),
                        get_mesh=get_mesh,get_maps=get_maps)

            if embedder:
                logger.info('getting embedder') 
                self.__retrieve_embedded_from_selection(selection,attr_filter=attr_filter)
        else:
            self.__retrieve_node_selection(selection,attr_filter=attr_filter,
                get_mesh=get_mesh,get_maps=get_maps)

        mc.select(sel,r=True)
        self.stats()


    def __add_ziva_node(self,zNode,attr_filter=None,get_mesh=True,get_maps=True):
        type_ = mz.get_type(zNode)

        attrList = base.build_attr_list(zNode,attr_filter=attr_filter)
        attrs = base.build_attr_key_values(zNode,attrList)

        if type_ == 'zTet':
            node = tetNode.TetNode()
            node.set_user_tet_mesh(mz.get_zTet_user_mesh(zNode))
        else:
            node = base.BaseNode()

        node.set_name(zNode)
        node.set_type(type_)
        node.set_attrs(attrs)
        node.set_association(mz.get_association(zNode))

        if get_maps:
            ml = MAPLIST.get(type_,None)
            if ml:
                associations = mz.get_association(zNode)

                # If it is a zFiber, the same mesh is used for both maps
                if type_ == 'zFiber':
                    associations.append(associations[0])

                maps = []
                for mp,ms in zip(ml,associations):
                    mapName = '{}.{}'.format(zNode,mp)
                    mapData = mps.get_map_data(zNode,mp,ms)
                    self.add_data('map',mapName,data=mapData)

                    maps.append(mapName)

                node.set_maps(maps)
                if get_mesh:
                    for ass in associations:
                        if not self.get_data_by_key_name('mesh',ass):
                            self.add_data('mesh',ass,data=msh.get_mesh_data(ass))

        self.add_node(node)



    def __retrieve_node_selection(self,selection,attr_filter=None,get_mesh=True,get_maps=True):
        longnames = mc.ls(selection,l=True)
        for s in longnames:
            if mc.objectType(s) == 'transform' or mc.objectType(s) == 'mesh':
                nodes = []
                nodes.append(mm.eval('zQuery -t zTet'))
                nodes.append(mm.eval('zQuery -t zTissue'))
                nodes.append(mm.eval('zQuery -t zBone'))
                for n in nodes:
                    if n:
                        self.__add_ziva_node(n[0],
                            attr_filter=attr_filter.get(mz.get_type(n),None),
                            get_mesh=get_mesh,get_maps=get_maps)
            if mz.get_type(s) in ZNODES:
                self.__add_ziva_node(s,
                    attr_filter=attr_filter.get(mz.get_type(s),None),
                    get_mesh=get_mesh,get_maps=get_maps)



    def __retrieve_embedded_from_selection(self,selection,connections=False,attr_filter=None):
        if not attr_filter:
            attr_filter = {}
        #if connections:
        longnames = mc.ls(selection,l=True)
        embedder = embedderNode.get_zEmbedder(longnames)
        #print 'OMG',embedder,selection
        if embedder:
            if longnames:
                associations = embedderNode.get_embedded_meshes(longnames)
                type_ = mz.get_type(embedder)

                # get attributes/values
                attrList = base.build_attr_list(embedder,attr_filter=attr_filter.get('zEmbedder',None))
                attrs = base.build_attr_key_values(embedder,attrList)

                node = embedderNode.EmbedderNode()
                node.set_name(embedder)
                node.set_type(type_)
                node.set_attrs(attrs)
                node.set_embedded_meshes(associations[0])
                node.set_collision_meshes(associations[1])

                self.add_node(node)

    @nc.time_this
    def apply(self,node_filter=None,attr_filter=None,interp_maps='auto',
            solver=True,bones=True,tissues=True,attachments=True,materials=True,
            fibers=True,embedder=True,permisive=True,cloth=True):

        '''

        Args:
            attr_filter (dict):  Attribute filter on what attributes to get. 
                dictionary is key value where key is node type and value is 
                list of attributes to use.

                tmp = {'zSolver':['substeps']}
            node_filter (str): filter by node name.  Defaults to **None**
        '''

        sel = mc.ls(sl=True)
        if solver:
            self.__apply_solver(attr_filter=attr_filter)

        #turn off solver to speed up build
        try:
            zSolverTransform = self.get_nodes(type_filter='zSolverTransform')[0]
            sn = zSolverTransform.get_name()
            solver_value = zSolverTransform.get_attr_value('enable')
            mc.setAttr(sn+'.enable',0)
        except:
            pass

        if bones:
            self.__apply_bones(node_filter=node_filter)
        if tissues:
            self.__apply_tissues(interp_maps=interp_maps,node_filter=node_filter,
                attr_filter=attr_filter)
        if cloth:
            self.__apply_cloth(interp_maps=interp_maps,node_filter=node_filter,
                attr_filter=attr_filter)
        if attachments:
            self.__apply_attachments(interp_maps=interp_maps,node_filter=node_filter,
                attr_filter=attr_filter)
        if materials:
            self.__apply_materials(interp_maps=interp_maps,node_filter=node_filter,
                attr_filter=attr_filter)
        if fibers:
            self.__apply_fibers(interp_maps=interp_maps,node_filter=node_filter,
                attr_filter=attr_filter)

        if embedder:
            self.__apply_embedded()

        try:
            # set solver back to whatever it was in data
            mc.setAttr(sn+'.enable',solver_value)
            mc.select(sel,r=True)
        except:
            pass


    def __apply_solver(self,attr_filter=None):
        logger.info('applying solver')  
        zSolver = self.get_nodes(type_filter='zSolver')

        if len(zSolver) > 0:
            zSolver = zSolver[0]
            zSolverTransform = self.get_nodes(type_filter='zSolverTransform')[0]

            solverName = zSolver.get_name()
            solverTransformName = zSolverTransform.get_name()

            if not mc.objExists(solverName):
                print 'building solver: ',solverName
                sol = mm.eval('ziva -s')

            base.set_attrs([zSolver,zSolverTransform],attr_filter=attr_filter)

    def __apply_bones(self,node_filter=None,attr_filter=None):
        #TODO: check if bone got created properly, if not gracefully error
        # check if existing solver, if there is not lets create one at default 
        # values
        logger.info('applying bones') 
        solver = mc.ls(type='zSolver')
        if not solver:
            mm.eval('ziva -s')
            


        zBones = self.get_nodes(type_filter='zBone',node_filter=node_filter)

        bone_meshes = []
        bone_names = []

        for zBone in zBones:
            association = zBone.get_association()
            if not mc.objExists(zBone.get_name()):
                bone_meshes.append(association[0])
                bone_names.append(zBone.get_name())

        #-----------------------------------------------------------------------
        # check meshes for existing zTissue
        bone_meshes_tmp = []
        bone_names_tmp = []
        for mname,bname in zip(bone_meshes,bone_names):

            if mc.objExists(mname):
                index = bone_meshes.index(mname)
                bone_meshes_tmp.append(bone_meshes[index])
                bone_names_tmp.append(bone_names[index])
                mc.select(mname)
                if mm.eval('zQuery -t "zBone"'):
                    # rename bone as it is in DATA
                    mc.rename(mm.eval('zQuery -t "zBone"')[0],bname)
                    bone_meshes.remove(mname)
                if mm.eval('zQuery -t "zTissue"'):
                    #logging.error('cannot create tissue, %s is a zBone' % mesh)
                    raise StandardError, 'cannot create bone, %s is already a zTissue' % mname
            else:
                logger.warning( mname +' does not exist in scene, skipping bone creation')

        bone_meshes = bone_meshes_tmp
        bone_names = bone_names_tmp


        # check mesh quality----------------------------------------------------
        mc.select(bone_meshes,add=True)
        mesh_quality = mm.eval('ziva -mq')

        #TODO command return something useful
        sel = mc.ls(sl=True)
        if sel:
            if 'vtx[' in sel[0]:
                raise StandardError, mesh_quality

        #build tissues all at once----------------------------------------------

        if bone_meshes:
            mc.select(bone_meshes,r=True)
            results = mm.eval('ziva -b')

            # ok, going to rename to a temp name then to name in data
            # rename zBones-----------------------------------------------------
            for new,i in zip(results[1::2],bone_names):
                #logger.debug( 'rename: {} {}_'.format(new,new))
                mc.rename(new,new+'_')


            # rename zBones-----------------------------------------------------
            for new,i in zip(results[1::2],bone_names):
                logger.debug( 'rename: {}_ {}'.format(new,i))
                mc.rename(new+'_',i)

        base.set_attrs(zBones,attr_filter=attr_filter)

    def __apply_tissues(self,interp_maps=False,node_filter=None,attr_filter=None):
        #TODO: check if tissue got created properly, if not gracefully error
        # check if existing solver, if there is not lets create one at default 
        # values
        logger.info('applying tissues') 
        solver = mc.ls(type='zSolver')
        if not solver:
            mm.eval('ziva -s')

        # get zTets and zTissues in data----------------------------------------

        zTets = self.get_nodes(type_filter='zTet',node_filter=node_filter)
        zTissues = self.get_nodes(type_filter='zTissue',node_filter=node_filter)


        # build a list of tissues to build all  at once (faster this way)-------
        tissue_meshes = []
        tissue_names = []
        tet_names = []
        for zTissue in zTissues:
            tmp = zTissue.get_association()
            #sync up tissues with mesh in data:
            if mc.objExists(tmp[0]):
                mc.select(tmp,r=True)
                tisMe = mm.eval('zQuery -t zTissue')
                if tisMe:
                    mc.rename(tisMe[0],zTissue.get_name())
            if not mc.objExists(zTissue.get_name()):
                tissue_meshes.append(tmp[0])
                tissue_names.append(zTissue.get_name())

        for zTet in zTets:
            tmp = zTet.get_association()[0]
            #sync up tissues with mesh in data:
            if mc.objExists(tmp):
                mc.select(tmp,r=True)
                tisMe = mm.eval('zQuery -t zTet')
                if tisMe:
                    mc.rename(tisMe[0],zTet.get_name())
            if not mc.objExists(zTet.get_name()):
                tet_names.append(zTet.get_name())



        #-----------------------------------------------------------------------
        # check meshes for existing zTissue
        for mname,tname in zip(tissue_meshes,tissue_names):
            if mc.objExists(mname):
                mc.select(mname)
                print 'name: ',mname
                if mm.eval('zQuery -t "zTissue"'):
                    # rename tissue as it is in DATA
                    mc.rename(mm.eval('zQuery -t "zTissue"')[0],tname)
                    tissue_meshes.remove(mname)
                if mm.eval('zQuery -t "zBone"'):
                    #logging.error('cannot create tissue, %s is a zBone' % mesh)
                    raise StandardError, 'cannot create tissue, %s is already a zBone' % mname
            else:
                index = tissue_meshes.index(mname)
                del tissue_meshes[index]
                del tissue_names[index]
                del tet_names[index]
                mc.warning( mname +' does not exist in scene, skipping tissue creation')

        # check mesh quality----------------------------------------------------
        mc.select(tissue_meshes)
        mesh_quality = mm.eval('ziva -mq')

        #TODO command return something useful
        sel = mc.ls(sl=True)
        if sel:
            if 'vtx[' in sel[0]:
                raise StandardError, mesh_quality


        #build tissues all at once----------------------------------------------
        if tissue_meshes:
            mc.select(tissue_meshes,r=True)
            results = mm.eval('ziva -t')

            # rename zTissues and zTets-----------------------------------------
            for new,i in zip(results[1::4],tissue_names):
                mc.rename(new,i)

            for new,i in zip(results[2::4],tet_names):
                mc.rename(new,i)


        # set tet maps if so desired--------------------------------------------
        mps.set_weights(zTets,self,interp_maps=interp_maps)


        ## apply user tet meshes if needed
        for zTet in zTets:
            if zTet.get_user_tet_mesh():
                try: 
                    mc.connectAttr( str(zTet.get_user_tet_mesh())+'.worldMesh', zTet.get_name()+'.iTet',f=True )
                except:
                    print 'could not connect %s to %s' % ( str(zTet.get_user_tet_mesh())+'.worldMesh', zTet.get_name()+'.iTet' )
                # mc.select(zTet.get_association())
                # mc.select(zTet.get_user_tet_mesh(),add=True)
                # mm.eval('ziva -cut')

        # set zTissue and zTet attributes---------------------------------------
        base.set_attrs(zTets,attr_filter=attr_filter)
        base.set_attrs(zTissues,attr_filter=attr_filter)




    def __apply_attachments(self,interp_maps=False,node_filter=None,attr_filter=None):
        logger.info('applying attachments') 
        attachments = self.get_nodes(type_filter='zAttachment',node_filter=node_filter)

        for att in attachments:
            name = att.get_name()
            # check if attachment exists, if it does just update it

            if mc.objExists(name):
                new_att = name
                #print 'found existing attachment, updating....',new_att
            else:
                associations = att.get_association()
                ass0 = associations[0]
                ass1 = associations[1]

                # TODO a way to check and turn it off
                # for s in associations:
                #     mc.select(s,r=True)
                #     if mm.eval('zQuery -t "zBone"') == None and mm.eval('zQuery -t "zTissue"') == None:
                #         raise StandardError, 'cannot create attachment, %s is neither tissue or bone' % s

                if mc.objExists(ass0) and mc.objExists(ass1):
                    mc.select(ass0,r=True)
                    mc.select(ass1,add=True)

                    try:
                        tmp = mm.eval('ziva -a')
                        new_att = mc.ls(tmp,type='zAttachment')[0]
                        #print 'creating attachment...',name
                    except:
                        continue
                    mc.rename(new_att,name)
                else:
                    print mc.warning('skipping attachment creation...'+name)

                

        mps.set_weights(attachments,self,interp_maps=interp_maps)

        base.set_attrs(attachments,attr_filter=attr_filter)

  

    def __apply_materials(self,interp_maps=False,node_filter=None,attr_filter=None):
        logger.info('applying materials') 
        materials = self.get_nodes(type_filter='zMaterial',node_filter=node_filter)


        tmp = {}
        for material in materials:
            mesh = material.get_association()[0]
            if mc.objExists(mesh):
                if not mesh in tmp:
                    tmp[mesh] = []
                tmp[mesh].append(material)
            else:
                mc.warning(mesh + ' does not exists in scene, skipping material')
        for mesh in tmp:
            current_material = mz.get_zMaterials([mesh])
            if len(current_material) > 0:
                for i in range(0,len(tmp[mesh])):
                    name = tmp[mesh][i].get_name()

                    if not mc.objExists(name):
                        if i == 0:
                            logger.debug('rename-- {} {}'.format(current_material[0],name))
                            mc.rename(current_material[0],name)
                            
                        else:
                            mc.select(mesh)
                            tmpmat = mm.eval('ziva -m')
                            mc.rename(tmpmat[0],name)

        mps.set_weights(materials,self,interp_maps=interp_maps)

        base.set_attrs(materials,attr_filter=attr_filter)


    def __apply_fibers(self,interp_maps=False,node_filter=None,attr_filter=None):
        #TODO build them all at once
        logger.info('applying fibers') 
        fibers = self.get_nodes(type_filter='zFiber',node_filter=node_filter)


        for fiber in fibers:
            name = fiber.get_name()
            #print 'ww',fiber.get_maps()
            association = fiber.get_association()
            if mc.objExists(association[0]):
                if not mc.objExists(name):
                    mc.select(association)
                    tmp = mm.eval('ziva -f')
                    mc.rename(tmp[0],name)
            else:
                mc.warning( association[0] +' mesh does not exists in scene, skippings fiber')

        mps.set_weights(fibers,self,interp_maps=interp_maps)

        base.set_attrs(fibers,attr_filter=attr_filter)

    def __apply_cloth(self,interp_maps=False,node_filter=None,attr_filter=None):
        #TODO build them all at once
        logger.info('applying cloth') 
        cloth = self.get_nodes(type_filter='zCloth',node_filter=node_filter)


        for item in cloth:
            name = item.get_name()
            #print 'ww',fiber.get_maps()
            association = item.get_association()
            if mc.objExists(association[0]):
                if not mc.objExists(name):
                    mc.select(association)
                    tmp = mm.eval('ziva -c')
                    mc.rename(tmp[0],name)
            else:
                mc.warning( association[0] +' mesh does not exists in scene, skippings cloth')


        base.set_attrs(cloth,attr_filter=attr_filter)

    def __apply_embedded(self,interp_maps=False,node_filter=None,attr_filter=None):
        # TODO get maps working and node_filter.  Will need to filter slightly
        # differently then other nodes as there is 1 embedder and we care
        # about associations in this case

        logger.info('applying embedder') 
        
        embeddedNode = self.get_nodes(type_filter='zEmbedder')
        if embeddedNode:
            embeddedNode = embeddedNode[0]
            name = embeddedNode.get_name()
            collision_meshes = embeddedNode.get_collision_meshes()
            embedded_meshes = embeddedNode.get_embedded_meshes()

            if collision_meshes:
                for mesh in collision_meshes:
                    for item in collision_meshes[mesh]:
                        try:
                            mc.select(mesh,item,r=True)
                            mm.eval('ziva -tcm')
                        except:
                            pass

            if embedded_meshes:
                for mesh in embedded_meshes:
                    for item in embedded_meshes[mesh]:
                        try:
                            mc.select(mesh,item,r=True)
                            mm.eval('ziva -e')
                        except:
                            pass

    # def mirror(search,replace):

    #     self.string_replace(search,replace)


