# Runs zBuilder tests
# with specified maya version as a first argument ( default is 2018 )
# Usage: python run_zbuilder_test.py --maya 2018

import os
import sys
import subprocess
import argparse
import json

MAYA_SCRIPT_PATH = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../..'))

current_directory_path = os.path.dirname(os.path.realpath(__file__))

cmd = ["python", "{0}/CMT/bin/runmayatests.py".format(MAYA_SCRIPT_PATH)]

parser = argparse.ArgumentParser(description='Runs unit tests for a Maya module')
parser.add_argument('--maya',
                    help='Maya version',
                    default='2018')

pargs = parser.parse_args()

cmd.extend(["--maya", pargs.maya])
cmd.extend(["--path", "{0}/tests".format(current_directory_path)])
cmd.extend(["--maya-script-path", "{0}/scripts".format(MAYA_SCRIPT_PATH)])

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
        raise Exception('Plugin {0} is not listed. Please change settings.json.'.format(maya_plugin_version))

subprocess.call(cmd)
