from os import path

# This is the file name LicenseRegister reads, merges and writes.
# It does not override or conflict with existing license info in other .lic files,
# RLM enusres loading all .lic files and parse them in its search paths.
LICENSE_FILE_NAME = 'zivavfx.lic'

def register_node_based_license(module_path, new_license_path):
    try:
        content = _read_license_content(new_license_path)
    except:
        raise RuntimeError("Fail to read input license file: {}".format(new_license_path))
    _write_license_content(module_path, content)


def register_floating_license(module_path, server, host_id, host_port):
    content = 'HOST {} {} {}'.format(server, host_id, host_port)
    _write_license_content(module_path, content)


def _read_license_content(license_path):
    with open(license_path, 'r') as lic_file:
        content = lic_file.read()
        return content


def _write_license_content(module_path, content):
    output_path = path.join(module_path, LICENSE_FILE_NAME)
    with open(output_path, 'w') as lic_file:
        lic_file.write(content)
