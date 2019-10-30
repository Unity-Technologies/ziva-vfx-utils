import os.path as path

class LicenseRegister(object):

    # License type
    NODE_BASED_LICENSE = 0
    FLOATING_LICENSE = 1

    # This is the file name LicenseRegister reads, merges and writes.
    # It does not override or conflict with existing license info in other .lic files,
    # RLM enusres loading all .lic files and parse them in its search paths.
    LICENSE_FILE_NAME = 'zivavfx.lic'

    def __init__(self, module_path):
        super(LicenseRegister, self).__init__()
        self.module_path = module_path
        self.license_type = None
        self.license_path = None # for Node-based license
        self.license_server_info = {} # for Floating license
        self.lic_file_content = {} # parse result of existing license file


    def set_node_based_license_info(self, license_path):
        self.license_type = LicenseRegister.NODE_BASED_LICENSE
        self.license_path = license_path


    def set_floating_license_info(self, license_server_info):
        self.license_type = LicenseRegister.FLOATING_LICENSE
        self.license_server_info = license_server_info


    def register(self):
        if LicenseRegister.NODE_BASED_LICENSE == self.license_type:
          self._register_node_based_license()
        elif LicenseRegister.FLOATING_LICENSE == self.license_type:
          self._register_floating_license()
        else:
          raise RuntimeError("Unknonwn license type to register: {}".format(self.license_type))


    def _register_node_based_license(self):
        assert(LicenseRegister.NODE_BASED_LICENSE == self.license_type)

        try:
            content = self._read_license_content()
        except:
          raise RuntimeError("Fail to read input license file: {}".format(self.license_path))
        
        self._write_license_content(content)


    def _register_floating_license(self):
        assert(LicenseRegister.FLOATING_LICENSE == self.license_type)

        try:
            content = 'HOST {} {} {}'.format(
                self.license_server_info['SERVER'],
                self.license_server_info['HOSTID'],
                self.license_server_info['HOSTPORT']
            )
        except:
            raise RuntimeError("Invalid floating license server info: {}".
                format(self.license_server_info))

        self._write_license_content(content)


    def _read_license_content(self):
        with open(self.license_path, 'r') as lic_file:
            content = lic_file.read()
            return content


    def _write_license_content(self, content):
        output_path = '{}/{}'.format(self.module_path, LicenseRegister.LICENSE_FILE_NAME)
        with open(output_path, 'w') as lic_file:
            lic_file.write(content)
