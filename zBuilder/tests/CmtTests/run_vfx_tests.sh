#!/bin/bash

# Get folder containing this file.
# https://stackoverflow.com/questions/59895/getting-the-source-directory-of-a-bash-script-from-within
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

export ZIVA_CMT_PLUGINS_TO_LOAD="C:/ziva/dev/Maya/plugins/zMaya/x64/Develop2016/ziva_devel.mll"
export ZIVA_CMT_TEST_SUIT_PARENT_DIR="C:/ziva/ziva-vfx-utils/zBuilder/tests/CmtTests"
export ZIVA_CMT_OUTPUT_TEXT_FILE="${ZIVA_CMT_TEST_SUIT_PARENT_DIR}/script_editor_out.txt"
export PYTHONPATH="${PYTHONPATH};C:/ziva/dev/Maya/CMT/scripts;C:/ziva/dev/Maya/plugins/zMaya/CmtTests"

rm ${ZIVA_CMT_OUTPUT_TEXT_FILE}
"C:/Program Files/Autodesk/Maya2016/bin/maya.exe" -noAutoloadPlugins -command 'python("import run_in_maya")'
result=$?
cat ${ZIVA_CMT_OUTPUT_TEXT_FILE}
rm ${ZIVA_CMT_OUTPUT_TEXT_FILE}
echo "Result = ${result}"


# Wipe existing MAYA_MODULE_PATH and put just these tests on it
#export MAYA_MODULE_PATH=$DIR

# Put CMT on the path.
#export PYTHONPATH="${PYTHONPATH};C:\ziva\dev\Maya\CMT\scripts"

#export MAYA_PLUGINS_NEEDED_FOR_TEST="C:/ziva/dev/Maya/plugins/zMaya/x64/Develop2016/ziva_devel.mll"

#python ../../../CMT/bin/runmayatests.py -m 2016
