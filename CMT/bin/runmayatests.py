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


def mayapy(maya_version, launch_py2):
    """Get the mayapy executable path.

    @param maya_version The maya version number.
    @return: The mayapy executable path.
    """
    if launch_py2:
        assert int(maya_version) == 2022, "'-py2' flag is not needed for Maya {}." \
        "It uses Python 2 environment by default.".format(maya_version)

    exec_name = 'mayapy2' if launch_py2 else 'mayapy'
    python_exe = '{0}/bin/{1}'.format(get_maya_location(maya_version), exec_name)
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
    dst = directory if directory else os.path.join(temp_dir, 'maya_app_dir{0}'.format(
        str(uuid.uuid4())))
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
        os.chmod(path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)  # 0777
        func(path)
    else:
        raise RuntimeError('Could not remove {0}'.format(path))


def test_output_looks_okay(output, maya_version):
    """
    Pass this the output (stderr) from runing the CMT tests.
    If the output looks okay, this returns true, else false.
    The definition of "looks okay" is some string processing
    based on matching what a successful test run looks like.

    This is to help us ignore random Maya crashes when exiting.
    """
    # ----------
    # First check
    # Search the stderr log for:
    # 1. failed test cases(with FAIL suffix),
    # 2. runtime error test cases(with ERROR suffix)
    # If none is found, we consider this run is good.
    # 'ok', 'skip' and 'expected failure' are valid results.

    # Note this check has a potential problem:
    # The stderror log doesn't contain last test case result,
    # it only has '...' but no status.
    # If the last test case failed in Maya 2022 Linux platform,
    # it passes first check and skips the second check(see skip logic below).
    # Let's hope this never happens.
    failed_testcase_patterns = ("... FAIL", "... ERROR")
    if any(x in output for x in failed_testcase_patterns):
        return False

    # Maya 2022 runs on Linux does not return message with OK.
    # We consider it is good as it has passed first check.
    if platform.system() == 'Linux' and int(maya_version) == 2022:
        return True

    # ----------
    # Second check
    # After the tests are run, this big bar is printed.
    # Search for it so we can look at the summary that comes after.
    sep = "----------------------------------------------------------------------"
    parts = output.split(sep)
    if len(parts) != 2:
        return False  # output doesn't match <tests><sep><summary>
    summary = parts[1]

    # A successful run puts "OK" on a line by itself.
    # In a truly successful run, it's at the end,
    # but sometimes maya prints some irrelevant error messages after it.
    # Another successful run pattern is, "OK (skipped=XXX)".
    # That's also fine as certain test cases may be skipped.
    import re
    okay_pattern = "^OK"
    return re.search(okay_pattern, summary, flags=re.MULTILINE)


def main():
    parser = argparse.ArgumentParser(description='Runs unit tests for a Maya module')
    parser.add_argument('-m', '--maya', help='Maya version', default='2023')
    parser.add_argument('-mad', '--maya-app-dir', help='Just create a clean MAYA_APP_DIR and exit')
    parser.add_argument('-p', '--path', help='Path to a folder with tests')
    parser.add_argument('-msp',
                        '--maya-script-path',
                        help='Path append to MAYA_SCRIPT_PATH environment variable')
    parser.add_argument('-mmp',
                        '--maya-module-path',
                        help='Path append to MAYA_MODULE_PATH environment variable')
    parser.add_argument('--plugin', help='Path to a maya plugin')
    parser.add_argument(
        '--py2',
        action='store_true',
        help='Launch mayapy in Python 2 environment. Works only starts from Maya 2022.')
    pargs = parser.parse_args()
    mayaunittest = os.path.join(CMT_ROOT_DIR, 'scripts', 'cmt', 'test', 'mayaunittest.py')
    cmd = []
    cmd.append(mayapy(pargs.maya, pargs.py2))
    # cmd.extend(['-m','pdb']) # Add '-m pdb' to start mayapy in the Python debugger
    cmd.append(mayaunittest)

    # passing through "--path" argument so that it can be used in mayaunittest.py module
    if pargs.path:
        cmd.append('--path')
        cmd.append(pargs.path)

    if pargs.plugin:
        cmd.append('--plugin')
        cmd.append(pargs.plugin)

    if not os.path.exists(cmd[0]):
        raise RuntimeError('Maya {0} is not installed on this system. Location examined {1}'.format(
            pargs.maya, cmd[0]))

    app_directory = pargs.maya_app_dir
    maya_app_dir = create_clean_maya_app_dir(app_directory)
    if app_directory:
        return
    # Create clean prefs
    os.environ['MAYA_APP_DIR'] = maya_app_dir

    # Clear out any MAYA_SCRIPT_PATH value except explicit specified
    os.environ['MAYA_SCRIPT_PATH'] = ''
    mayaScriptPath = pargs.maya_script_path
    if mayaScriptPath:
        os.environ['MAYA_SCRIPT_PATH'] = mayaScriptPath

    # Run the tests in this module, and other explicit specified ones
    os.environ['MAYA_MODULE_PATH'] = CMT_ROOT_DIR
    mayaModulePath = pargs.maya_module_path
    if mayaModulePath:
        os.environ['MAYA_MODULE_PATH'] += (os.pathsep + mayaModulePath)

    module_dir = os.path.dirname(os.path.abspath(__file__))
    python_path = os.path.abspath(os.path.join(module_dir, r'../..'))

    if "PYTHONPATH" not in os.environ:
        os.environ["PYTHONPATH"] = python_path
    else:
        os.environ["PYTHONPATH"] = python_path + os.pathsep + os.environ["PYTHONPATH"]

    exitCode = 0
    try:
        # TODO: use subprocess.check_output(cmd) when we have Python 2.7 available.
        # This code is lifted from the cpython implementaion of check_output
        # https://github.com/python/cpython/blob/2.7/Lib/subprocess.py#L194

        process = subprocess.Popen(cmd,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   universal_newlines=True)
        _, stderr = process.communicate()
        exitCode = process.poll()

        # mayapy is a monster. As hard as we try, we cannot stop it from exiting
        # with errors or segfaults or other silly things, even when all of the tests pass.
        # So, we do not depend on the error code. Instead, we look for the final "OK"
        # from python's unit tests runner. If that OK was printed, then the tests are good.

        output_looks_ok = test_output_looks_okay(stderr, pargs.maya)
        if (exitCode != 0) and output_looks_ok:
            # Make this case phenomenal
            for i in range(5):
                print('#' * 80)
            print("WARNING mayapy exited with {0}, but the tests look okay\n".format(exitCode))
            sys.exit(0)

        # This rarely happens. If it does, test_output_looks_okay() needs overhaul
        if (exitCode == 0) and not output_looks_ok:
            # Make this unusual case phenomenal
            for i in range(5):
                print('@' * 80)
            print(
                "WARNING mayapy runs well but stderr does not look okay.\n Error message: {0}\n\n".
                format(stderr))
            sys.exit(1)

        # print stderr as diagnose info
        print(stderr)

    except subprocess.CalledProcessError:
        pass
        # TODO: use this when we switch to subprocess.check_output
        # output = error.output
        # exitCode = error.returncode
    finally:
        shutil.rmtree(maya_app_dir, ignore_errors=True)

    sys.exit(exitCode)


if __name__ == '__main__':
    main()
