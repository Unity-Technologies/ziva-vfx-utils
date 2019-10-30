import unittest
from os import path, mkdir
import tempfile
from vfx_test_case import VfxTestCase
from utils.licenseRegister.licenseRegister import LICENSE_FILE_NAME
from utils.licenseRegister.licenseRegister import register_node_based_license, register_floating_license


class TestLicenseRegister(VfxTestCase):
  
    def setUp(self):
        super(TestLicenseRegister, self).setUp()

        # setup module path
        self.temp_dir = tempfile.gettempdir()
        self.module_path = path.join(self.temp_dir, 'Ziva/VFX/Ziva-VFX-Maya-Module')
        try:
            mkdir(self.module_path)
        except OSError:
            pass  # path exists, proceed
        

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
        new_node_based_license_file_path = path.join(self.temp_dir, 'new_node_based_license.lic')
        with open(new_node_based_license_file_path, 'w') as input_file:
            input_file.write(new_node_based_license_content)
            
        # Act
        register_node_based_license(self.module_path, new_node_based_license_file_path)

        # Verify
        file_path = path.join(self.module_path, LICENSE_FILE_NAME)
        self.assertTrue(path.exists(file_path))
        self.assertTrue(path.isfile(file_path))
        with open(file_path, 'r') as lic_file:
            generated_content = lic_file.read()
            self.assertEqual(new_node_based_license_content, generated_content)


    def test_non_exist_input_node_based_file(self):
        # Act
        with self.assertRaises(RuntimeError):
            register_node_based_license(self.module_path, "non/exist/file/path")


    def test_register_floating_license(self):
        '''
        Test registering a floating license, no existing license file
        '''
        # Setup
        expected_floating_license_content = 'HOST localhost ANY 5053'

        # Act
        register_floating_license(self.module_path, 'localhost', 'ANY', 5053)
        
        # Verify
        file_path = path.join(self.module_path, LICENSE_FILE_NAME)
        self.assertTrue(path.exists(file_path))
        self.assertTrue(path.isfile(file_path))
        with open(file_path, 'r') as lic_file:
            generated_content = lic_file.read()
            self.assertEqual(expected_floating_license_content, generated_content)

