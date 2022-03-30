# Runs zBuilder tests
# with specified maya version as a first argument ( default is 2019 )
# Usage: python run_zbuilder_test.py --maya 2019

import os
import sys
import subprocess
import argparse
import json

REPO_ROOT_PATH = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                               '../..'))

current_directory_path = os.path.dirname(os.path.realpath(__file__))

cmd = ["python", "{0}/CMT/bin/runmayatests.py".format(REPO_ROOT_PATH)]

parser = argparse.ArgumentParser(description='Runs unit tests for a Maya module')
parser.add_argument('--maya', help='Maya version', default='2019')
parser.add_argument('--py2',
                    action='store_true',
                    help='Launch mayapy in Python 2 environment. Works only starts from Maya 2022.')

pargs = parser.parse_args()

cmd.extend(["--maya", pargs.maya])
cmd.extend(["--path", "{0}/tests".format(current_directory_path)])
cmd.extend(["--maya-script-path", "{0}/scripts".format(REPO_ROOT_PATH)])
# Launch Maya in Python 2 environment, only affect since Maya 2022
if pargs.py2:
    assert int(pargs.maya) >= 2022, "-py2 argument only works since Maya 2022"
    cmd.extend([
        "--py2",
    ])

# Prepend CMT framework script path
cmt_script_path = "{0}/CMT/scripts".format(REPO_ROOT_PATH)
if "PYTHONPATH" not in os.environ:
    os.environ["PYTHONPATH"] = cmt_script_path
else:
    os.environ["PYTHONPATH"] = cmt_script_path + os.pathsep + os.environ["PYTHONPATH"]

if sys.platform.startswith('linux'):
    maya_plugin_version = 'lin_' + pargs.maya
elif sys.platform.startswith('win32'):
    maya_plugin_version = 'win_' + pargs.maya
else:
    raise Exception('OS {0} is not supported.'.format(sys.platform))

with open('{0}/settings.json'.format(current_directory_path)) as json_file:
    data = json.load(json_file)
    if maya_plugin_version in data['plugin_path']:
        cmd.extend(["--plugin", '{0}'.format(data['plugin_path'][maya_plugin_version])])
    else:
        raise Exception(
            'Plugin {0} is not listed. Please change settings.json.'.format(maya_plugin_version))

exit_code = subprocess.check_call(cmd)

sys.exit(exit_code)
