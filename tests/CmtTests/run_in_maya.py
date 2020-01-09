import os
from maya import cmds
import cmt.test
import cmt.test.mayaunittest

outTextFile = os.environ["ZIVA_CMT_OUTPUT_TEXT_FILE"]

zMayaTestDir = os.environ["ZIVA_CMT_TEST_SUIT_PARENT_DIR"]
os.environ["MAYA_MODULE_PATH"] += os.pathsep + zMayaTestDir

cmds.scriptEditorInfo(wh=1, historyFilename=outTextFile)

plugins = os.environ["ZIVA_CMT_PLUGINS_TO_LOAD"].split(os.pathsep)
for plugin_name in plugins:
    cmds.loadPlugin(plugin_name)

run_tests_result = cmt.test.mayaunittest.run_tests()
cmds.scriptEditorInfo(wh=0, historyFilename="")

myExitCode = len(run_tests_result.errors)

# Maya won't exit right away, due to "Cannot quit when application is busy.".
# So, defer the quit until later.
cmds.evalDeferred("cmds.quit(force=True, exitCode=" + str(myExitCode) + ")")
