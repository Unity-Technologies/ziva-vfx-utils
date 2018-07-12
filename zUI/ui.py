import zBuilder.builders.ziva as zva

class ZivaUi():

    # Show window with docking ability
    def run(self):
        z = zva.Ziva()
        # Not getting the parameters in this case (maps and meshes) as that
        # slows down the retrieving of information.
        z.retrieve_connections()
        z.view()



