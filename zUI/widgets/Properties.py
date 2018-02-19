# from PySide import QtGui, QtCore
from zUI.Qt import QtGui, QtWidgets, QtCore # https://github.com/mottosso/Qt.py by Marcus Ottosson
from zUI.Qt import __binding__

import functools
import os

import maya.cmds as mc
import maya.mel as mm
from maya import OpenMaya as om

import logging

logger = logging.getLogger(__name__)

icons = {}
icons['zBone'] =            'icons\\zBone.xpm'
icons['close'] =            'icons\\Fileclose.xpm'
icons['zTissue'] =          'icons\\zTissue.xpm'
icons['zTet'] =             'icons\\zTet.xpm'
icons['zAttachment'] =      'icons\\zAttachment.xpm'
icons['zSolver']=           'icons\\out_zSolver.xpm'
icons['zSolverTransform']=  'icons\\out_zSolver.xpm'
icons['zMaterial']=         'icons\\zMaterial.xpm'
icons['zFiber']=            'icons\\zFiber.xpm'
icons['zEmbedder']=            'icons\\out_zSolver.xpm'
icons['zCache']=            'icons\\zFiber.xpm'


class MCallbackIdWrapper(object):
    '''Wrapper class to handle cleaning up of MCallbackIds from registered MMessage
    '''
    def __init__(self, callbackId):
        super(MCallbackIdWrapper, self).__init__()
        self.callbackId = callbackId
        #logger.info( 'creating callback: {}'.format(self.callbackId) )   

    def __del__(self):
        #logger.info( 'deleting callback: {}'.format(self.callbackId) )  
        om.MMessage.removeCallback(self.callbackId)

    def __repr__(self):
        return 'MCallbackIdWrapper(%r)'%self.callbackId


class Properties(QtWidgets.QTableWidget):
    def __init__(self, parent=None):
        super(Properties, self).__init__(parent)
        logger.info( 'instantiated: {}'.format(self) )    
        self.parent = parent

        self.nodeCallbacks = {}            # Node callbacks for handling attr value changes
        self.attrWidgets = {}              # Dict key=attrName, value=widget
        self._deferredUpdateRequest = {}   # Dict of widgets to update

        self.setRowCount(0)
        self.setColumnCount(2)
        self.setColumnWidth(0, 120)
        self.setColumnWidth(1, 80)
        self.setEditTriggers(QtWidgets.QAbstractItemView.CurrentChanged)

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenuEvent)

        self.itemPressed.connect(self.contextMenuEvent)


        v_header = self.verticalHeader()
        v_header.setVisible(False)
        v_header.setDefaultSectionSize(15)

        h_header = self.horizontalHeader()
        h_header.setStretchLastSection(False)
        h_header.setVisible(False)

        if __binding__ == "PySide":
            h_header.setResizeMode(0, QtWidgets.QHeaderView.Stretch)
            h_header.setResizeMode(1, QtWidgets.QHeaderView.Fixed)
        elif __binding__ == "PySide2":
            h_header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
            h_header.setSectionResizeMode(1, QtWidgets.QHeaderView.Fixed)


        #self.resizeRowsToContents()

        # Use functools.partial() to dynamically constructing a function
        # with additional parameters.  Perfect for menus too.
        #onSetAttrFunc =  functools.partial(self.onSetAttr)
        self.cellChanged.connect( self.onSetAttr )
        self._convert_icon_path()


    def _convert_icon_path(self):
        path = os.path.dirname(os.path.realpath(__file__))
        path = path.replace('\widgets','')
        for zNode in icons:
            icons[zNode] = os.path.join(path,icons[zNode])
        #print icons

    def set_properties(self,items):
        #print 'prop:set_properties-started'
        #self.ignore_updates(True)

        self.blockSignals(True)
        self.__block = True

        self.setUpdatesEnabled(False)
        self.nodeCallbacks.clear()
        self.attrWidgets.clear()
        self._deferredUpdateRequest.clear()
        # iColumns = self.columnCount()
        # iRows = self.rowCount()

        # for i in (0,iRows):
        #     for j in (0,iColumns):
        #         item = self.item(i,j)
        #         if item:
        #             item.disconnect()
        
        self.clearSpans()
        self.clear()
        # try:
        #     self.disconnect()
        # except:
        #     pass


        #find row count
        row_count=0
        for item in items:
            row_count = row_count+len(item.attrs)
            row_count+=1

        #print row_count
        self.setRowCount(row_count)

        row = 0
        for i in items:
            name = self.parent._get_name_from_item_data(i,fullPath=False)
            #print name
            fullname = self.parent._get_name_from_item_data(i,fullPath=True)
            #print fullname
            item = QtWidgets.QTableWidgetItem(name)
            item.setBackground(QtGui.QColor(60,60,60))
            item.setData(QtCore.Qt.UserRole, getDependNode(fullname))
            #print mc.objectType(fullName)
            #icon = QtWidgets.QIcon(icons[mc.objectType(fullName)])
            #item.setIcon(icon) 

            self.setItem(row,0,item)
            self.setSpan(row,0,1,2)
            row+=1
            if i.type():
                attribute_properties = self.parent.get_properties_wrapper(fullname)
                attr_order = attribute_properties[1]
                attrs = attribute_properties[0]
            else:
                attr_order = []
                attrs = []

            #print attrs
            for attr in attr_order:
                _type=attrs[attr]['type']

                if _type == 'weight':
                    p_item = QtWidgets.QTableWidgetItem(attrs[attr]['niceName'])
                    p_item.setTextAlignment(QtCore.Qt.AlignRight)
                    p_item.setBackground(QtGui.QColor(68,68,68))
                    p_item.setFlags( QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled )
                    
                    self.setItem(row,0,p_item)

                    p_item.setBackground(QtGui.QColor(100,100,100))
                    self.button = QtWidgets.QToolButton(self)
                    self.button.setIcon(QtGui.QIcon(icons['zCache']))
                    self.button.setStyleSheet('border: 0px; padding: 0px;')
                    self.button.setCursor(QtCore.Qt.PointingHandCursor)
                    self.setCellWidget(row,1,self.button)


                    onButPressFunc = functools.partial(self._weight_button_clicked,attr=attr,name=name,_type=_type)
                    self.button.clicked.connect(onButPressFunc)
                else:
                    p_item = QtWidgets.QTableWidgetItem(attr)
                    p_item.setTextAlignment(QtCore.Qt.AlignRight)
                    p_item.setBackground(QtGui.QColor(68,68,68))
                    p_item.setFlags( QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled )
                    #p_item.node_name = name
                    self.setItem(row,0,p_item)

                    v_item = QtWidgets.QTableWidgetItem()
                    v_item.node_name = name
                    v_item.attr_type = attrs[attr]['type']
                    if v_item.attr_type == 'enum':
                        v_item.setFlags( QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled )
                    v_item.attr_name = attr
                    v_item.attr_widget = i

                    value = attrs[attr]['value']
                    nodeAttr = ('%s.%s' % (v_item.node_name,attr))
                    # if v_item.attr_type == 'bool':
                    #     v_item.setFlags( QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled )

                    self._set_widget_value(v_item,v_item.attr_type,nodeAttr,value)
                    
                    self.attrWidgets['%s.%s' % (name,attr)] = v_item

                    self.setItem(row,1,v_item)
                row+=1
                
            nodeObj = getDependNode(name)
            if name not in self.nodeCallbacks:
                #print 'creating node callback: ',name,i
                cb = om.MNodeMessage.addNodeDirtyPlugCallback(nodeObj, self.onDirtyPlug, None)
                self.nodeCallbacks[name] = MCallbackIdWrapper(cb)
        self.blockSignals(False)
        self.__block = False

        self.setUpdatesEnabled(True)
        #self.ignore_updates(False)
        #print 'prop:set_properties-finished'


    def _weight_button_clicked(self,*args,**kwargs):
        name = kwargs['name']
        attr = kwargs['attr']
        _type = mc.objectType(name)

        _map = 'weights'
        meshes = mm.eval('zQuery -m '+name)
        mesh = meshes[0]

        if _type == 'zFiber':
            if attr == 'endPoints':
                _map = 'endPoints'
                
        if _type == 'zAttachment':
            if attr == 'weightList[1].weights':
                mesh = meshes[1]


        
        self.blockSignals(True)

        mc.select(mesh)
        mc.select(name,addFirst=True)
        melStr =  """ArtPaintAttrTool; 
            artSetToolAndSelectAttr( \"artAttrCtx\", \"%s.%s.%s\" );""" % (_type,name,_map)
        print 'attempting to paint ',_type,meshes[0]
        mm.eval( melStr )
        self.blockSignals(False)


    def _set_widget_value(self,widget,_type,nodeAttr,value):

        #print 'prop:_set_widget_value-started'
        self.setUpdatesEnabled(False)
        #self.blockSignals(True)
        #self.__block = True
        #self.disconnect()

        if _type == 'bool':
            if value == True:
                widget.setCheckState(QtCore.Qt.Checked)
                #logger.info( 'setting widget {} {}'.format(widget,value) )
            else:
                widget.setCheckState(QtCore.Qt.Unchecked)
                #logger.info( 'setting widget {} {}'.format(widget,value) )
        elif _type == 'enum':
            value = mc.getAttr(nodeAttr,asString=True)
            widget.setText(str(value))
            #logger.info( 'setting widget {} {}'.format(widget,value) )
            #print 'setting widget enum: ',value
        elif _type == 'weight':
            print 'passing weight'
            pass
        else:
            widget.setText(str(value))
            #logger.info( 'setting widget {} {}'.format(widget,value) )

        #self.blockSignals(False)
        #self.__block = False
        self.setUpdatesEnabled(True)

        #print nodeAttr
        #print 'prop:_set_widget_value-finished'
        #self.cellChanged.connect( self.onSetAttr )


    def contextMenuEvent(self,*args,**kwargs):
        item = args[0]
        if item.column() == 1 and item.attr_type == 'enum':
            attrName = item.attr_name
            nodeName = item.node_name
            enum_list = self._get_enum_list(nodeName,attrName)

            self.menu = QtWidgets.QMenu(self)
            for el in enum_list:
                onButPressFunc = functools.partial(
                    self.renameSlot,
                    item=item,
                    new=el)
         
                action = QtWidgets.QAction(el, self)
                action.triggered.connect(onButPressFunc)
                self.menu.addAction(action)
            # add other required actions
            self.menu.popup(QtGui.QCursor.pos())


           


    def renameSlot(self,*args,**kwargs):
        new = kwargs['new']
        item = kwargs['item']

        item.setText(new)
        #print "renaming slot called"


    def update_properties(self,items):
        self.blockSignals(True)
        #print 'prop:update_properties:',tmp
        self.set_properties(items)
        self.blockSignals(False)

    def onSetAttr(self, *args, **kwargs):
        #print 'prop:onSetAttr-started',args
        '''Handle setting the attribute when the UI widget edits the value for it.
        If it fails to set the value, then restore the original value to the UI widget
        '''

        if not self.__block:
            #-NAME CHANGE-----------------------------------------------------------
            # if args[1] is 0 it is first column and therefore a name change
            if args[1] == 0:
                item = self.item(args[0],args[1])
                lname = self._get_name_from_item_data(item,fullPath=True)

                if lname:
                    mc.rename(lname,item.text())

            # ATTRIBUTE VALUE CHANGE------------------------------------------------
            # if args[1] is 1 it is second column and therefore a value change
            if args[1] == 1:
                item = self.item(args[0],args[1])

                attrType = item.attr_type
                attrName = item.attr_name
                nodeName = item.node_name
                nodeAttr = ('%s.%s' % (nodeName,attrName))



                try:
                    if attrType == 'string':
                        mc.setAttr('%s.%s'%(nodeName, attrName), item.text(), type=attrType)
                        logger.info( 'setting string attr {}.{}'.format(nodeName,attrName) )  
                    elif attrType == 'bool':
                        checkState = item.checkState()
                        if checkState == 0:
                            mc.setAttr('%s.%s'%(nodeName, attrName), 0)
                        if checkState == 2:
                            mc.setAttr('%s.%s'%(nodeName, attrName), 1)
                        logger.info( 'setting bool attr {}.{}'.format(nodeName,attrName) )  
                    elif attrType == 'enum':
                        #print nodeName,attrName,'----------------------------------
                        
                        val = str(item.text()).strip()
                        enum_list = self._get_enum_list(nodeName,attrName)
                        newval = enum_list.index(val)
                        #print 'setting maya enum: ',newval
                        mc.setAttr('%s.%s'%(nodeName, attrName), newval)
                        logger.info( 'setting enum attr {}.{}'.format(nodeName,attrName) ) 
                    elif attrType == 'weight':
                        print 'assing weight'
                        pass
                    else:
                        mc.setAttr('%s.%s'%(nodeName, attrName), eval(item.text()))
                        logger.info( 'setting attr {}.{}'.format(nodeName,attrName) ) 
                except Exception, e:
                    logger.info( 'Cannot set weight.  reverting {}.{}'.format(nodeName,attrName) )  
                    curVal = mc.getAttr('%s.%s'%(nodeName, attrName))
                    self._set_widget_value(item,attrType,nodeAttr,curVal)


            #import sys, traceback
            #traceback.print_stack()
            #attrs = self.parent.get_properties_wrapper(nodeName)
            #print 'attrs before:'
            #item.attr_widget.attrs = attrs
            #print 'attrs after:'
        #self.blockSignals(False)

        #print 'prop:onSetAttr-finished'

    def _get_enum_list(self,node,attr):
        tmp = mc.attributeQuery(attr,node=node,listEnum=True)[0]
        return [item.strip() for item in tmp.split(':')]

    def onDirtyPlug(self, node, plug, *args, **kwargs):
        #print 'prop:onDirtyPlug'

        '''Add to the self._deferredUpdateRequest member variable that is then 
        deferred processed by self._processDeferredUpdateRequest(). 
        '''
        # get long name of the attr, to use as the dict key
        #attrName = plug.partialName(False, False, False, False, False, True)
        nodeAttrName = plug.partialName(True, False, False, False, False, True) 
        #print 'onDirtyPlug: ',node,plug,args,kwargs
        #print '   attrName: ',nodeAttrName
        # # get widget associated with the attr
        widget = self.attrWidgets.get(nodeAttrName, None)
        if widget:
            # get node.attr string
            #nodeAttrName = plug.partialName(True, False, False, False, False, True) 

            # Add to the dict of widgets to defer update
            self._deferredUpdateRequest[nodeAttrName] = widget

            # Trigger an evalDeferred action if not already done
            if len(self._deferredUpdateRequest) == 1:
                mc.evalDeferred(self._processDeferredUpdateRequest, low=True)


    def _processDeferredUpdateRequest(self):
        '''Retrieve the attr value and set the widget value
        '''
        #print 'prop:_processDeferredUpdateRequest'
        self.blockSignals(True)

        for nodeAttrName,widget in self._deferredUpdateRequest.items():
            v = mc.getAttr(nodeAttrName)
            t = mc.getAttr(nodeAttrName,type=True)


            self._set_widget_value(widget,t,nodeAttrName,v)

            # nodeName = nodeAttrName.split('.')[0]
            # attr = nodeAttrName.split('.')[1]
            # print 'deferred',nodeName,attr
            #print 'item:',widget.attrs
            #attrs = self.parent.get_properties_wrapper(nodeName)
            #widget.attrs = attrs

            #print "_processDeferredUpdateRequest ", widget, nodeAttrName, v
        self._deferredUpdateRequest.clear()
        self.blockSignals(False)

    def _clear_callbacks(self):
        self.nodeCallbacks.clear()

    def _get_name_from_item_data(self,item,fullPath=True):
        mobject = item.data(QtCore.Qt.UserRole)
        if mobject:
            if mobject.hasFn(om.MFn.kDagNode):
                dagpath = om.MDagPath()
                om.MFnDagNode(mobject).getPath(dagpath)
                if fullPath:
                    return dagpath.fullPathName()
                else:
                    return dagpath.partialPathName()
            else:
                return om.MFnDependencyNode(mobject).name()
        else:
            return None

def getDependNode(nodeName):
    """Get an MObject (depend node) for the associated node name

    :Parameters:
        nodeName
            String representing the node
    
    :Return: depend node (MObject)

    """
    dependNode = om.MObject()
    selList = om.MSelectionList()
    selList.add(nodeName)
    if selList.length() > 0: 
        selList.getDependNode(0, dependNode)
    return dependNode