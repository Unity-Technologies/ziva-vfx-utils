# Runs zBuilder tests
# with specified maya version as a first argument ( default is 2018 )
# Usage: python run_zbuilder_test.py -m 2018

import os
import sys
import subprocess
import argparse
import json

MAYA_SCRIPT_PATH = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../..'))

cmd = ["python", "{}/CMT/bin/runmayatests.py".format(MAYA_SCRIPT_PATH)]

parser = argparse.ArgumentParser(description='Runs unit tests for a Maya module')
parser.add_argument('-m', '--maya',
                    help='Maya version',
                    default='2018')

pargs = parser.parse_args()

cmd.extend(["--maya", pargs.maya])
cmd.extend(["--path", "./tests"])
cmd.extend(["--maya-script-path", "{}/scripts".format(MAYA_SCRIPT_PATH)])

if sys.platform.startswith('linux'):
    maya_plugin_version = 'lin_' + pargs.maya
elif sys.platform.startswith('win32'):
    maya_plugin_version = 'win_' + pargs.maya
else:
    raise StandardError('OS {} is not supported.'.format(sys.platform))

with open('settings.json') as json_file:
    data = json.load(json_file)
    if maya_plugin_version in data['plugin_path']:
        cmd.extend(["--plugin", '{}'.format(data['plugin_path'][maya_plugin_version])])
    else:
        raise StandardError('Plugin {} is not listed. Please change settings.json.'.format(maya_plugin_version))

subprocess.call(cmd)
