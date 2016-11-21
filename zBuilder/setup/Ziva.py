import zBuilder.zMaya as mz

import zBuilder.nodes.base as base
import zBuilder.nodes.zEmbedder as embedderNode
import zBuilder.nodes.zTet as tetNode
import zBuilder.data.mesh as msh

import zBuilder.nodeCollection as nc

import maya.cmds as mc
import maya.mel as mm

import time

maplist = {}
maplist['zTet'] = ['weightList[0].weights']
maplist['zMaterial'] = ['weightList[0].weights']
maplist['zFiber'] = ['weightList[0].weights','endPoints']
maplist['zAttachment'] = ['weightList[0].weights','weightList[1].weights']

zNodes = [
        'zSolver',
        'zSolverTransform',
        'zTet',
        'zTissue',
        'zBone',
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
    def retrieve_from_scene(self,solver):
        sel = mc.ls(sl=True,l=True)
        print solver
        type_ = mz.get_type(solver)
        
        if type_ == 'zSolverTransform':
            print '\ngetting ziva......'
            mc.select(solver,r=True)
            solShape = mm.eval('zQuery -t "zSolver" -l')[0]
            self.__add_ziva_node(solver)
            self.__add_ziva_node(solShape)

            type_s = ['zBone','zTissue','zTet','zMaterial','zFiber','zAttachment']

            for t in type_s:
                zNodes = mm.eval('zQuery -t "'+t+'" -l')
                if zNodes:
                    for zNode in zNodes:
                        self.__add_ziva_node(zNode)



            self.__retrieve_embedded_from_selection(mm.eval('zQuery -t "zTissue" -m'))

            self.stats()

        else:
            print 'select a solver'

        mc.select(sel,r=True)
        

    @nc.time_this
    def retrieve_from_scene_selection(self,selection,connections=False):
        print '\ngetting ziva......'

        if connections:
            self.__retrieve_solver_from_selection(selection)
            self.__retrieve_bones_from_selection(selection)
            self.__retrieve_tissues_from_selection(selection)
            self.__retrieve_attachments_from_selection(selection)
            self.__retrieve_materials_from_selection(selection)
            self.__retrieve_fibers_from_selection(selection)
            self.__retrieve_embedded_from_selection(selection)
        else:
            self.__retrieve_node_selection(selection)

        self.stats()


    def __add_ziva_node(self,zNode):
        type_ = mz.get_type(zNode)

        attrList = base.build_attr_list(zNode)
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

        ml = maplist.get(type_,None)
        if ml:
            associations = mz.get_association(zNode)
            maps = msh.get_weights(zNode,associations,ml)
            node.set_maps(maps)
            for ass in associations:
                self.add_data('mesh',ass)

        self.add_node(node)



    def __retrieve_node_selection(self,selection):
        longnames = mc.ls(selection,l=True)
        for s in longnames:
            if mc.objectType(s) == 'transform' or mc.objectType(s) == 'mesh':
                nodes = []
                nodes.append(mm.eval('zQuery -t zTet'))
                nodes.append(mm.eval('zQuery -t zTissue'))
                nodes.append(mm.eval('zQuery -t zBone'))
                for n in nodes:
                    if n:
                        self.__add_ziva_node(n[0])
            if mz.get_type(s) in zNodes:
                self.__add_ziva_node(s)

    def __retrieve_solver_from_selection(self,selection,connections=False):

        solver = mz.get_zSolver(selection[0])
        if solver:
            solver = solver[0]
            self.__add_ziva_node(solver)

            solverTransform = mz.get_zSolverTransform(selection[0])[0]
            self.__add_ziva_node(solverTransform)
            mc.select(selection,r=True)
        else:
            print 'no solver found'




    def __retrieve_bones_from_selection(self,selection,connections=False):
        longnames = mc.ls(selection,l=True)
        for bone in mz.get_zBones(longnames):
            self.__add_ziva_node(bone)
            
        mc.select(selection)     

    def __retrieve_tissues_from_selection(self,selection,connections=False):
        longnames = mc.ls(selection,l=True)

        for tissue in mz.get_zTissues(longnames):
            self.__add_ziva_node(tissue)

        for tet in mz.get_zTets(longnames):
            self.__add_ziva_node(tet)


        mc.select(longnames)


    def __retrieve_attachments_from_selection(self,selection,connections=False):

        longnames = mc.ls(selection,l=True)
        attachments = mz.get_zAttachments(longnames)

        for attachment in attachments:
            self.__add_ziva_node(attachment)



    def __retrieve_materials_from_selection(self,selection,connections=False):
        if connections:
            longnames = mc.ls(selection,l=True)
            materials = mz.get_zMaterials(longnames)

            for material in materials:
                self.__add_ziva_node(material)


    def __retrieve_fibers_from_selection(self,selection,connections=False):
        if connections:
            longnames = mc.ls(selection,l=True)
            fibers = mz.get_zFibers(longnames)

            for fiber in fibers:
                self.__add_ziva_node(fiber)


    def __retrieve_embedded_from_selection(self,selection,connections=False):
        #if connections:
        longnames = mc.ls(selection,l=True)
        embedder = embedderNode.get_zEmbedder(longnames)
        #print 'OMG',embedder,selection
        if embedder:
            if longnames:
                associations = embedderNode.get_embedded_meshes(longnames)
                type_ = mz.get_type(embedder)

                # get attributes/values
                attrList = base.build_attr_list(embedder)
                attrs = base.build_attr_key_values(embedder,attrList)

                node = embedderNode.EmbedderNode()
                node.set_name(embedder)
                node.set_type(type_)
                node.set_attrs(attrs)
                node.set_embedded_meshes(associations[0])
                node.set_collision_meshes(associations[1])

                self.add_node(node)

    @nc.time_this
    def apply(self,filter_=None,interp_maps='auto'):
        '''
        '''
        sel = mc.ls(sl=True)
        self.__apply_solver()

        #turn off solver to speed up build
        zSolverTransform = self.get_nodes(type_='zSolverTransform')[0]
        sn = zSolverTransform.get_name()
        solver_value = zSolverTransform.get_attr_value('enable')
        mc.setAttr(sn+'.enable',0)

        self.__apply_bones(filter_=filter_)

        self.__apply_tissues(interp_maps=interp_maps,filter_=filter_)
        self.__apply_attachments(interp_maps=interp_maps,filter_=filter_)
        self.__apply_materials(interp_maps=interp_maps,filter_=filter_)
        self.__apply_fibers(interp_maps=interp_maps,filter_=filter_)
        self.__apply_embedded()

        # set solver back to whatever it was in data
        mc.setAttr(sn+'.enable',solver_value)
        mc.select(sel,r=True)


    def __apply_solver(self):
        zSolver = self.get_nodes(type_='zSolver')
        if zSolver:
            zSolver = zSolver[0]
            zSolverTransform = self.get_nodes(type_='zSolverTransform')[0]

            solverName = zSolver.get_name()
            solverTransformName = zSolverTransform.get_name()

            if not mc.objExists(solverName):
                print 'building solver: ',solverName
                sol = mm.eval('ziva -s')

            base.set_attrs([zSolver,zSolverTransform])

    def __apply_bones(self,filter_=None):
        sol = mc.ls(type='zSolverTransform')[0]
        sval = mc.getAttr(sol+'.enable')
        mc.setAttr(sol+'.enable',False)
        #TODO: check if bone got created properly, if not gracefully error
        # check if existing solver, if there is not lets create one at default 
        # values
        solver = mc.ls(type='zSolver')
        if not solver:
            mm.eval('ziva -s')
            

        zBones = self.get_nodes(type_='zBone',filter_=filter_)
        bone_meshes = []
        bone_names = []

        for zBone in zBones:
            association = zBone.get_association()
            if not mc.objExists(zBone.get_name()):
                bone_meshes.append(association[0])
                bone_names.append(zBone.get_name())

        #-----------------------------------------------------------------------
        # check meshes for existing zTissue
        for mesh in bone_meshes:
            mc.select(mesh)
            if mm.eval('zQuery -t "zBone"'):
                bone_meshes.remove(mesh)
            if mm.eval('zQuery -t "zTissue"'):
                #logging.error('cannot create tissue, %s is a zBone' % mesh)
                raise StandardError, 'cannot create bone, %s is already a zTissue' % mesh
        
        # check mesh quality----------------------------------------------------
        mc.select(bone_meshes)
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

            # rename zTissues and zTets-----------------------------------------
            for new,i in zip(results[1::2],bone_names):
                mc.rename(new,i)

        base.set_attrs(zBones)
        mc.setAttr(sol+'.enable',sval)

    def __apply_tissues(self,interp_maps=False,filter_=None):
        sol = mc.ls(type='zSolverTransform')[0]
        sval = mc.getAttr(sol+'.enable')
        mc.setAttr(sol+'.enable',False)
        #TODO: check if tissue got created properly, if not gracefully error
        # check if existing solver, if there is not lets create one at default 
        # values
        solver = mc.ls(type='zSolver')
        if not solver:
            mm.eval('ziva -s')

        # get zTets and zTissues in data----------------------------------------
        zTets = self.get_nodes(type_='zTet',filter_=filter_)
        zTissues = self.get_nodes(type_='zTissue',filter_=filter_)

        # build a list of tissues to build all  at once (faster this way)-------
        tissue_meshes = []
        tissue_names = []
        tet_names = []

        for zTissue,zTet in zip(zTissues,zTets):
            tmp = zTissue.get_association()
            if not mc.objExists(zTissue.get_name()):
                tissue_meshes.append(tmp[0])
                tissue_names.append(zTissue.get_name())
                tet_names.append(zTet.get_name())

        #-----------------------------------------------------------------------
        # check meshes for existing zTissue
        for mesh in tissue_meshes:
            if mc.objExists(mesh):
                mc.select(mesh)
                if mm.eval('zQuery -t "zTissue"'):
                    tissue_meshes.remove(mesh)
                if mm.eval('zQuery -t "zBone"'):
                    #logging.error('cannot create tissue, %s is a zBone' % mesh)
                    raise StandardError, 'cannot create tissue, %s is already a zBone' % mesh
            else:
                tissue_meshes.remove(mesh)
                print mesh, 'does not exist in scene, skipping'
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

        # set tet maps if so desired--------------------------------------------\
        msh.set_weights(zTets,self.get_meshes(),interp_maps=interp_maps)


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
        base.set_attrs(zTets)
        base.set_attrs(zTissues)

        mc.setAttr(sol+'.enable',sval)


    def __apply_attachments(self,interp_maps=False,filter_=None):

        sol = mc.ls(type='zSolverTransform')[0]
        sval = mc.getAttr(sol+'.enable')
        mc.setAttr(sol+'.enable',False)


        attachments = self.get_nodes(type_='zAttachment',filter_=filter_)
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
                        print 'creating attachment...',name
                    except:
                        continue
                    mc.rename(new_att,name)
                else:
                    print 'skipping...',name

                

        msh.set_weights(attachments,self.get_meshes(),interp_maps=interp_maps)

        base.set_attrs(attachments)

        mc.setAttr(sol+'.enable',sval)

    def __apply_materials(self,interp_maps=False,filter_=None):
        sol = mc.ls(type='zSolverTransform')[0]
        sval = mc.getAttr(sol+'.enable')
        mc.setAttr(sol+'.enable',False)

        #TODO one more loop for order sanity check
        materials = self.get_nodes(type_='zMaterial',filter_=filter_)

        tmp = {}
        for material in materials:
            mesh = material.get_association()[0]
            if mc.objExists(mesh):
                if not mesh in tmp:
                    tmp[mesh] = []
                tmp[mesh].append(material)
            else:
                print mesh, 'does not exists in scene, skipping material'
        for mesh in tmp:
            current_material = mz.get_zMaterials([mesh])
            if len(current_material) > 0:
                for i in range(0,len(tmp[mesh])):
                    name = tmp[mesh][i].get_name()

                    if not mc.objExists(name):
                        if i == 0:
                            print 'rename: ',current_material,name
                            mc.rename(current_material,name)
                        else:
                            mc.select(mesh)
                            tmpmat = mm.eval('ziva -m')
                            mc.rename(tmpmat[0],name)

        msh.set_weights(materials,self.get_meshes(),interp_maps=interp_maps)

        base.set_attrs(materials)

        mc.setAttr(sol+'.enable',sval)


    def __apply_fibers(self,interp_maps=False,filter_=None):
        sol = mc.ls(type='zSolverTransform')[0]
        sval = mc.getAttr(sol+'.enable')
        mc.setAttr(sol+'.enable',False)
        #TODO build them all at once
        fibers = self.get_nodes(type_='zFiber',filter_=filter_)

        for fiber in fibers:
            name = fiber.get_name()
            association = fiber.get_association()
            if mc.objExists(association[0]):
                if not mc.objExists(name):
                    mc.select(association)
                    tmp = mm.eval('ziva -f')
                    mc.rename(tmp[0],name)
            else:
                print association[0], ' mesh does not exists in scene, skippings fiber'

        msh.set_weights(fibers,self.get_meshes(),interp_maps=interp_maps)

        base.set_attrs(fibers)
        mc.setAttr(sol+'.enable',sval)

    def __apply_embedded(self,interp_maps=False,filter_=None):
        # TODO get maps working and filter_.  Will need to filter slightly
        # differently then other nodes as there is 1 embedder and we care
        # about associations in this case
        
        embeddedNode = self.get_nodes(type_='zEmbedder')[0]
        if embeddedNode:
            
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

    def mirror(search,replace):
        self.string_replace(search,replace)



