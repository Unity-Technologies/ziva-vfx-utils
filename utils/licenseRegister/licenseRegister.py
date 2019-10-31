from os import path

# This is the file name LicenseRegister reads, merges and writes.
# It does not override or conflict with existing license info in other .lic files,
# RLM enusres loading all .lic files and parse them in its search paths.
LICENSE_FILE_NAME = 'zivavfx.lic'

# License type
NODE_BASED_LICENSE = 0
FLOATING_LICENSE = 1

def register_node_based_license(module_path, new_license_path):
    try:
        content = _read_license_content(new_license_path)
    except:
        raise RuntimeError("Fail to read input license file: {}".format(new_license_path))

    merged_content = _merge_new_content_with_existing_license(module_path, content, NODE_BASED_LICENSE)
    _write_license_content(module_path, merged_content)


def register_floating_license(module_path, server, host_id, host_port):
    content = 'HOST {} {} {}'.format(server, host_id, host_port)
    merged_content = _merge_new_content_with_existing_license(module_path, content, FLOATING_LICENSE)
    _write_license_content(module_path, merged_content)


def _merge_new_content_with_existing_license(module_path, new_content, license_type):
    '''
    If MODULE_PATH/zivavfx.lic exists, return merged content, return input content otherwise.

    The license file format is:
    HOST XXXXXXXXX  - floating license, can be multiple HOST lines
    LICENSE XXXXXX  - node-based license, can be multiple LICENSE lines

    A valid license file can mix both license type.
    RLM server will try all of them till find proper one.
    However, it requires HOST line appears before LICENSE line, or the HOST line is not considered.
    
    The merge policy is:
    If new content is node-based license, append it to the existing content;
    If new content is floating license, prepend it to the existing content.
    '''
    license_path = path.join(module_path, LICENSE_FILE_NAME)
    if path.exists(license_path) and path.isfile(license_path):
        with open(license_path, 'r') as lic_file:
            existing_content = lic_file.read()
            merged_content = existing_content
            if NODE_BASED_LICENSE == license_type:
                merged_content = '{}\n{}'.format(existing_content, new_content)
            elif FLOATING_LICENSE == license_type:
                merged_content = '{}\n{}'.format(new_content, existing_content)
            else:
                raise RuntimeError("Unknow license type: {}".format(license_type))
            return merged_content
    return new_content


def _read_license_content(license_path):
    with open(license_path, 'r') as lic_file:
        content = lic_file.read()
        return content


def _write_license_content(module_path, content):
    output_path = path.join(module_path, LICENSE_FILE_NAME)
    with open(output_path, 'w') as lic_file:
        lic_file.write(content)
