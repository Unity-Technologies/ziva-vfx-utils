import unittest
import os
from vfx_test_case import VfxTestCase
from os import path
import re
import tempfile
import utils.licenseRegister.licenseRegister as licReg

class TestLicenseRegister(VfxTestCase):
  
    def setUp(self):
        super(TestLicenseRegister, self).setUp()

        # setup module path
        self.temp_dir = tempfile.gettempdir()
        self.module_path = self.temp_dir + '/Ziva/VFX/Ziva-VFX-Maya-Module'
        try:
            os.mkdir(self.module_path)
        except OSError:
            pass  # path exists, proceed
        
        self.licReg = licReg.LicenseRegister(self.module_path)

    def test_register_without_set_license_type(self):
        with self.assertRaises(RuntimeError):
            self.licReg.register()


    def test_register_node_based_license(self):
        '''
        Test registering a node-based license, no existing license file
        '''
        # Setup
        new_node_based_license_content = '''
LICENSE zivadyn ziva-vfx-author 1.99 1-jan-2020 uncounted hostid=ANY
  _ck=abcde12345 sig="AABBCCDDEEFF112233445566AABBCCDDEEFF112233445566
  ABCDEF123456ABCDEF123456ABCDEF123456"
'''.strip()
        new_node_based_license_file_path = \
            '{}/new_node_based_license.lic'.format(self.temp_dir)
        with open(new_node_based_license_file_path, 'w') as input_file:
            input_file.write(new_node_based_license_content)
            
        # Act
        self.licReg.set_node_based_license_info(new_node_based_license_file_path)
        self.licReg.register()

        # Verify
        file_path = '{}/zivavfx.lic'.format(self.module_path)
        self.assertTrue(os.path.exists(file_path))
        self.assertTrue(os.path.isfile(file_path))
        with open(file_path, 'r') as lic_file:
            generated_content = lic_file.read()
            self.assertEqual(new_node_based_license_content, generated_content)

    def test_non_exist_input_node_based_file(self):
        # Act
        self.licReg.set_node_based_license_info("non/exist/file/path")
        with self.assertRaises(RuntimeError):
            self.licReg.register()


    def test_register_floating_license(self):
        '''
        Test registering a floating license, no existing license file
        '''
        # Setup
        new_floating_license_server_info = {
          'SERVER' : 'localhost',
          'HOSTID' : 'ANY',
          'HOSTPORT': 5053
        }
        expected_floating_license_content = 'HOST localhost ANY 5053'

        # Act
        self.licReg.set_floating_license_info(new_floating_license_server_info)
        self.licReg.register()
        
        # Verify
        file_path = '{}/zivavfx.lic'.format(self.module_path)
        self.assertTrue(os.path.exists(file_path))
        self.assertTrue(os.path.isfile(file_path))
        with open(file_path, 'r') as lic_file:
            generated_content = lic_file.read()
            self.assertEqual(expected_floating_license_content, generated_content)


    def test_invalid_license_server_info(self):
        self.licReg.set_floating_license_info({})
        with self.assertRaises(RuntimeError):
            self.licReg.register()


