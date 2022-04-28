from maya import cmds


class SolverDisabler:

    def __init__(self, solver_name):
        """SolverDisabler is a context manager object that disables a solver for the duration of
        the context and then restores its initial state. This is useful for improving the
        performance of a code block that's making many changes to a solver. This manager object
        is preferable to doing it 'by hand' because it handles exceptions and DG connections that
        the naive solution (getAttr/setAttr) would fail to handle."""

        self.enable_plug = solver_name + '.enable'
        self.connection_source = None
        self.enable_value = True

    def __enter__(self):
        self.enable_value = cmds.getAttr(self.enable_plug)
        self.connection_source = cmds.listConnections(self.enable_plug, plugs=True)
        if self.connection_source:
            cmds.disconnectAttr(self.connection_source[0], self.enable_plug)

        cmds.setAttr(self.enable_plug, False)

    def __exit__(self, type, value, traceback):
        cmds.setAttr(self.enable_plug, self.enable_value)

        if self.connection_source:
            cmds.connectAttr(self.connection_source[0], self.enable_plug)
