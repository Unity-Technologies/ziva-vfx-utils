from os import path
from shutil import copy2

# This is the file name LicenseRegister reads, merges and writes.
# It does not override or conflict with existing license info in other .lic files,
# RLM enusres loading all .lic files and parse them in its search paths.
LICENSE_FILE_NAME = 'zivavfx.lic'


def register_node_locked_license(module_path, new_license_path):
    '''
    Copy new node-locked license to module path
    '''
    if not path.exists(new_license_path):
        raise RuntimeError("Input license file path: {} does not exist.".format(new_license_path))
    if not path.isfile(new_license_path):
        raise RuntimeError("Input license file path: {} is not a file.".format(new_license_path))

    file_name = path.basename(new_license_path)
    dst_path = path.join(module_path, file_name)
    try:
        copy2(new_license_path, dst_path)
    except Exception as e:
        raise RuntimeError("Failed to copy input license file: {}, {}".format(
            new_license_path, str(e)))


def register_floating_license(module_path, server, host_id, host_port):
    '''
    Add new license server info to MODULE_PATH/zivavfx.lic
    '''
    new_content = 'HOST {} {} {}'.format(server, host_id, host_port)
    '''
    If MODULE_PATH/zivavfx.lic exists, prepend new HOST line to the existing file,
    create the file and add new content to it otherwise.
    A valid license file may contain multiple HOST lines. 
    RLM server will try all of them till find proper one.
    '''
    merged_content = new_content
    license_path = path.join(module_path, LICENSE_FILE_NAME)
    if path.exists(license_path) and path.isfile(license_path):
        try:
            with open(license_path, 'r') as lic_file:
                existing_content = lic_file.read()
                merged_content = '{}\n{}'.format(new_content, existing_content)
        except:
            raise RuntimeError("Failed to read {} file content.".format(license_path))

    try:
        with open(license_path, 'w') as lic_file:
            lic_file.write(merged_content)
    except:
        raise RuntimeError("Failed to write new license server info to {}.".format(license_path))
