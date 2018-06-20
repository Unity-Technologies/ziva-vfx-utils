import zBuilder.builders.ziva as zva

class ZivaUi():

    # Show window with docking ability
    def run(self):
        z = zva.Ziva()

        z.retrieve_from_scene(get_parameters=False)
        z.view()



