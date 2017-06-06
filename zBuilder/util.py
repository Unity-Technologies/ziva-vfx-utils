import maya.cmds as mc





def copy_paste(*args,**kwargs):
    # get current selection to re-apply
    sel = mc.ls(sl=True)

    # args
    selection = None
    if args:
        selection = mc.ls(args[0],l=True)
    else:
        selection = mc.ls(sl=True,l=True)


    import zBuilder.setup.Ziva as zva
    z = zva.ZivaSetup()
    z.retrieve_from_scene_selection(selection[0])
    z.string_replace(selection[0].replace('|',''), selection[1].replace('|',''))
    z.stats()
    z.apply()

    mc.select(sel)
