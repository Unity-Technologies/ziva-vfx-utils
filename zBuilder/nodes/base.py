import re
import maya.cmds as mc

class BaseNode(object):
    def __init__(self):
        self._name = None
        self._attrs = {}
        self._maps = {}
        self._association = []
        self._type = None
        self._class = (self.__class__.__module__,self.__class__.__name__)
        #print self._class

    def __str__(self):
        if self.get_name():
            return '<%s.%s "%s">' % (self.__class__.__module__,self.__class__.__name__, self.get_name())
        return '<%s.%s>' % (self.__class__.__module__,self.__class__.__name__)

    def __repr__(self):
        return self.__str__()

    def print_(self):
        print '----------------------------------------------------'
        #print 'index: \t',i
        print 'python node: \t',self
        print 'name: \t',self.get_name(longName=True)
        print 'type: \t',self.get_type()
        
        attrList =  self.get_attr_list()
        if attrList:
            print 'attrs: ',
            for attr in attrList:   
                print '\t\t',attr,self.get_attr_key_value(attr,'type'),self.get_attr_key_value(attr,'value')
        
        maps = self.get_maps()
        if maps:
            print 'maps: ',
            for key in maps:
                print '\t\t',key,maps[key]['mesh'],maps[key]['value']
        associations = self.get_association(longName=True)
        if associations:
            print 'association: ',associations

    def string_replace(self,search,replace):
        # name replace----------------------------------------------------------
        name = self.get_name(longName=True)
        newName = replace_longname(search,replace,name)
        self.set_name(newName)



        # association replace---------------------------------------------------
        assNames = self.get_association(longName=True)
        newNames = []
        if assNames:
            for name in assNames:
                newName = replace_longname(search,replace,name)
                newNames.append(newName)
            self.set_association(newNames)

        #maps-------------------------------------------------------------------

        maps = self.get_maps()
        for key in maps:
            if maps[key].get('mesh',None):
                maps[key]['mesh'] = replace_longname(search,replace,maps[key]['mesh'])


    def get_attr_value(self,attr):
        return self._attrs[attr]['value']

    def set_attr_value(self,attr,value):
        self._attrs[attr]['value'] = value

    def get_attr_list(self):
        return self._attrs.keys()

    def get_attr_key(self,key):
        return self._attrs.get(key)

    def get_attr_key_value(self,attr,key):
        return self._attrs[attr][key]

    def set_attr_key_value(self,attr,key,value):
        self._attrs[attr][key] = value

    def get_name(self,longName=False):
        if self._name:
            if longName:
                return self._name
            else:
                return self._name.split('|')[-1]
        else:
            return None
        

    def set_name(self,name):

        self._name = name   

    def get_type(self):
        return self._type

    def set_type(self,type_):
        self._type = type_

    def get_maps(self):
        return self._maps

    def set_maps(self,maps):
        self._maps = maps



    # def get_attrs(self):
    #     return self._attrs

    def set_attrs(self,attrs):
        # TODO explicit set and gets
        self._attrs = attrs

    def get_association(self,longName=False):
        if not longName:
            tmp = []
            for item in self._association:
                tmp.append(item.split('|')[-1])
            return tmp
        else:
            return self._association

    def set_association(self,association):
        if isinstance(association, str):
            self._association =[association]
        else:
            self._association =association

    
def replace_longname(search,replace,longName):
    items = longName.split('|')
    newName = ''
    for i in items:
        if i:
            i = re.sub(search, replace,i)
            newName+='|'+i

    return newName


def build_attr_list(selection,attr_filter=None):

    exclude = ['controlPoints','uvSet','colorSet','weightList','pnts',
        'vertexColor','target']

    tmps = mc.listAttr(selection,k=True)
    cb = mc.listAttr(selection,cb=True)
    if cb:
        tmps.extend(mc.listAttr(selection,cb=True))
    attrs = []
    for attr in tmps:
        if not attr.split('.')[0] in exclude:
            attrs.append(attr)

    if attr_filter:
        #attrs = list(set(attrs).intersection(attr_filter))
        attrs = attr_filter
        
    return attrs


def build_attr_key_values(selection,attrList):
    tmp = {}
    for attr in attrList:
        tmp[attr] = {}
        tmp[attr]['type'] = mc.getAttr(selection+'.'+attr,type=True)
        tmp[attr]['value'] = mc.getAttr(selection+'.'+attr)
        tmp[attr]['locked'] = mc.getAttr(selection+'.'+attr,l=True)

    return tmp

def set_attrs(nodes,attr_filter=None):
    for node in nodes:
        name = node.get_name()
        type_ = node.get_type()
        nodeAttrs = node.get_attr_list()
        if attr_filter:
            if attr_filter.get(type_,None):
                nodeAttrs = list(set(nodeAttrs).intersection(attr_filter[type_]))


        for attr in nodeAttrs:
            if node.get_attr_key('type') == 'doubleArray':
                if mc.objExists(name+'.'+attr):
                    if not mc.getAttr(name+'.'+attr,l=True):
                        mc.setAttr(name+'.'+attr,node.get_attr_value(attr),
                            type='doubleArray')
                else:
                    print name+'.'+attr + ' not found, skipping'
            else:
                if mc.objExists(name+'.'+attr):
                    if not mc.getAttr(name+'.'+attr,l=True):
                        try:
                            mc.setAttr(name+'.'+attr,node.get_attr_value(attr))
                        except:
                            #print 'tried...',attr
                            pass
                else:
                    print name+'.'+attr + ' not found, skipping'