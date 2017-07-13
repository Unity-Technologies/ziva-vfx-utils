import maya.cmds as mc




def copy_paste(*args,**kwargs):
    '''
    A utility wrapper for copying and pasting a tissue
    '''
    sel = mc.ls(sl=True)
    #print sel

    selection = None
    if args:
        selection = mc.ls(args[0],l=True)
    else:
        selection = mc.ls(sl=True,l=True)

    import zBuilder.setup.Ziva as zva
    z = zva.ZivaSetup()
    z.retrieve_from_scene_selection(selection[0])
    z.string_replace(selection[0].split('|')[-1], selection[1].split('|')[-1])
    z.stats()
    z.apply(kwargs)

    mc.select(sel)



