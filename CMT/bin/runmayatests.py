#!/usr/bin/env python
"""
Command-line unit test runner for mayapy.

This can be used to run tests from a commandline environment like on a build server.

Usage:
python runmayatests.py -m 2016
"""
import argparse
import errno
import os
import platform
import shutil
import stat
import subprocess
import tempfile
import uuid
import sys

CMT_ROOT_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))


def get_maya_location(maya_version):
    """Get the location where Maya is installed.

    @param maya_version The maya version number.
    @return The path to where Maya is installed.
    """
    if 'MAYA_LOCATION' in os.environ.keys():
        return os.environ['MAYA_LOCATION']
    elif platform.system() == 'Windows':
        return 'C:/Program Files/Autodesk/Maya{0}'.format(maya_version)
    elif platform.system() == 'Darwin':
        return '/Applications/Autodesk/maya{0}/Maya.app/Contents'.format(maya_version)
    else:
        location = '/usr/autodesk/maya{0}'.format(maya_version)
        if float(maya_version) < 2016:
            # Starting Maya 2016, the default install directory name changed.
            location += '-x64'
        return location


def mayapy(maya_version):
    """Get the mayapy executable path.

    @param maya_version The maya version number.
    @return: The mayapy executable path.
    """
    python_exe = '{0}/bin/mayapy'.format(get_maya_location(maya_version))
    if platform.system() == 'Windows':
        python_exe += '.exe'
    return python_exe


def create_clean_maya_app_dir(directory=None):
    """Creates a copy of the clean Maya preferences so we can create predictable results.

    @return: The path to the clean MAYA_APP_DIR folder.
    """
    app_dir = os.path.join(CMT_ROOT_DIR, 'scripts', 'clean_maya_app_dir')
    temp_dir = tempfile.gettempdir()
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    dst = directory if directory else os.path.join(temp_dir, 'maya_app_dir{0}'.format(str(uuid.uuid4())))
    if os.path.exists(dst):
        shutil.rmtree(dst, ignore_errors=False, onerror=remove_read_only)
    shutil.copytree(app_dir, dst)
    return dst


def remove_read_only(func, path, exc):
    """Called by shutil.rmtree when it encounters a readonly file.

    :param func:
    :param path:
    :param exc:
    """
    excvalue = exc[1]
    if func in (os.rmdir, os.remove) and excvalue.errno == errno.EACCES:
        os.chmod(path, stat.S_IRWXU| stat.S_IRWXG| stat.S_IRWXO) # 0777
        func(path)
    else:
        raise RuntimeError('Could not remove {0}'.format(path))


def main():
    parser = argparse.ArgumentParser(description='Runs unit tests for a Maya module')
    parser.add_argument('-m', '--maya',
                        help='Maya version',
                        default='2018')
    parser.add_argument('-mad', '--maya-app-dir',
                        help='Just create a clean MAYA_APP_DIR and exit')
    parser.add_argument('-p', '--path',
                        help='Path to a folder with tests')
    pargs = parser.parse_args()
    mayaunittest = os.path.join(CMT_ROOT_DIR, 'scripts', 'cmt', 'test', 'mayaunittest.py')
    cmd = []
    cmd.append(mayapy(pargs.maya))
    cmd.append(mayaunittest)
    
    # passing through "--path" argument so that it can be used in mayaunittest.py module
    if pargs.path:
        cmd.append('--path')
        cmd.append(pargs.path)

    if not os.path.exists(cmd[0]):
        raise RuntimeError('Maya {0} is not installed on this system. Location examined {1}'.format(pargs.maya, cmd[0]))

    # adding python path
    python_path = 'PYTHONPATH'
    if python_path not in os.environ:
        os.environ["PYTHONPATH"] = {}
        os.environ["PYTHONPATH"] = os.path.abspath(r'..\..\..')
    else:
        os.environ["PYTHONPATH"] = os.path.abspath(r'..\..\..') + os.pathsep + os.environ["PYTHONPATH"]

    app_directory = pargs.maya_app_dir
    maya_app_dir = create_clean_maya_app_dir(app_directory)
    if app_directory:
        return

    # Create clean prefs
    os.environ['MAYA_APP_DIR'] = maya_app_dir
    # Clear out any MAYA_SCRIPT_PATH value so we know we're in a clean env.
    os.environ['MAYA_SCRIPT_PATH'] = ''
    # Run the tests in this module.
    os.environ['MAYA_MODULE_PATH'] = CMT_ROOT_DIR
    exitCode = 0
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as error:
        exitCode = error.returncode
    finally:
        shutil.rmtree(maya_app_dir)
    
    sys.exit(exitCode)

if __name__ == '__main__':
    main()
