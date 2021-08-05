from PySide2 import QtWidgets

class ScenePanel2MenuBar(QtWidgets.QMenuBar):
    def __init__(self, parent=None):
        super(ScenePanel2MenuBar, self).__init__(parent)

        self.setup_menu_items()

    def setup_menu_items(self):
        self.file_menu = self.addMenu("File")
        self.cache_menu = self.addMenu("Cache")
        self.tool_menu = self.addMenu("Tool")
        self.help_menu = self.addMenu("Help")

        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
      
   

