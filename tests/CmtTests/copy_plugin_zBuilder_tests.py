# Copy plugin for zBuilder tests
# with specified maya version as a first argument ( default is 2023 )
# Usage: python  tests/CmtTests/copy_plugin_zBuilder_tests.py --maya 2023

import os
import sys
import subprocess
import argparse
import json

current_directory_path = os.path.dirname(os.path.realpath(__file__))

parser = argparse.ArgumentParser(description='Runs unit tests for a Maya module')
parser.add_argument('--maya', help='Maya version', default='2023')

pargs = parser.parse_args()

cmd = ['aws s3 cp']

with open('{0}/settings.json'.format(current_directory_path)) as json_file:
    data = json.load(json_file)

if sys.platform.startswith('linux'):
    maya_plugin_version = 'lin_' + pargs.maya
    maya_plugin_s3_path = 's3://ziva-ci/{0}'.format(data['plugin_path'][maya_plugin_version][13:])
elif sys.platform.startswith('win32'):
    maya_plugin_version = 'win_' + pargs.maya
    maya_plugin_s3_path = 's3://ziva-ci/{0}'.format(data['plugin_path'][maya_plugin_version][3:])
else:
    raise Exception('OS {0} is not supported.'.format(sys.platform))

if maya_plugin_version in data['plugin_path']:
    cmd.extend([maya_plugin_s3_path])
    cmd.extend(['{0}'.format(data['plugin_path'][maya_plugin_version])])
else:
    raise Exception(
        'Plugin {0} is not listed. Please change settings.json.'.format(maya_plugin_version))

exit_code = subprocess.check_call(' '.join(cmd) + ' --quiet', shell=True)

sys.exit(exit_code)
