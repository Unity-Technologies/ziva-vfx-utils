import unittest
import os
from os import path
import tempfile
from vfx_test_case import VfxTestCase
from utils.licenseRegister.licenseRegister import LICENSE_FILE_NAME
from utils.licenseRegister.licenseRegister import register_node_based_license, register_floating_license


def delete_file(file_path):
    if path.exists(file_path) and path.isfile(file_path):
        os.remove(file_path)


class TestLicenseRegister(VfxTestCase):

    @classmethod
    def setUpClass(cls):
        # setup module path
        cls.temp_dir = tempfile.gettempdir()
        cls.module_path = path.join(cls.temp_dir, 'Ziva/VFX/Ziva-VFX-Maya-Module')
        try:
            os.makedirs(cls.module_path)
        except OSError:
            pass  # path exists, proceed

        # setup existing license file path
        cls.canonical_license_file_path = path.join(cls.module_path, LICENSE_FILE_NAME)

        # create empty node based license file
        cls.empty_license_file_path = path.join(cls.module_path, 'empty.lic')
        open(cls.empty_license_file_path, 'a').close()

        # create new node based license file
        cls.new_license_file_path = path.join(cls.module_path, 'new_node_based_license.lic')
        cls.new_node_based_license_content = '''
LICENSE zivadyn ziva-vfx-author 1.99 1-jan-2020 uncounted hostid=ANY
  _ck=abcde12345 sig="AABBCCDDEEFF112233445566AABBCCDDEEFF112233445566
  ABCDEF123456ABCDEF123456ABCDEF123456"
'''.strip()
        with open(cls.new_license_file_path, 'w') as input_file:
            input_file.write(cls.new_node_based_license_content)

    @classmethod
    def tearDownClass(cls):
        delete_file(cls.empty_license_file_path)
        delete_file(cls.new_license_file_path)
        
        if path.exists(cls.module_path) and path.isdir(cls.module_path):
            os.removedirs(cls.module_path)


    def tearDown(self):
        super(TestLicenseRegister, self).tearDown()
        # delete zivavfx.lic as its content changes in some test cases
        delete_file(self.canonical_license_file_path)


    def create_canonical_license_file(self):
        '''
        Helper function that creates a MODULE_PATH/zivavfx.lic file with valid content

        Returns:
            str: existing license file content
        '''
        existing_lic_content = '''
HOST localhost ANY 5054
HOST localhost ANY 5055
LICENSE zivadyn ziva-vfx-author 1.99 1-jan-2020 uncounted hostid=ANY
  _ck=12345abcde sig="AABBCCDDEEFF112233445566AABBCCDDEEFF112233445566
  ABCDEF123456ABCDEF123456ABCDEF123456"
LICENSE zivadyn ziva-vfx-batch 1.99 1-jan-2020 uncounted hostid=ANY
  _ck=abcde54321 sig="AABBCCDDEEFF112233445566AABBCCDDEEFF112233445566
  ABCDEF123456ABCDEF123456ABCDEF654321"
'''.strip()

        with open(self.canonical_license_file_path, 'w') as input_file:
            input_file.write(existing_lic_content)
        return existing_lic_content

    # --------------------------------------------------------------------------------

    def test_register_node_based_license(self):
        '''
        Test registering a node-based license, no existing license file
        '''
        # Act
        register_node_based_license(self.module_path, TestLicenseRegister.new_license_file_path)

        # Verify
        self.assertTrue(path.exists(self.canonical_license_file_path))
        self.assertTrue(path.isfile(self.canonical_license_file_path))
        with open(self.canonical_license_file_path, 'r') as lic_file:
            generated_content = lic_file.read()
            self.assertEqual(TestLicenseRegister.new_node_based_license_content, generated_content)


    def test_non_exist_input_node_based_file(self):
        # Act
        with self.assertRaises(RuntimeError):
            register_node_based_license(self.module_path, "non/exist/file/path")


    def test_register_empty_node_based_license(self):
        '''
        Test input node-based file is empty, no existing license file
        '''
        # Act
        register_node_based_license(self.module_path, TestLicenseRegister.empty_license_file_path)

        # Verify
        self.assertEqual(os.stat(self.canonical_license_file_path).st_size, 0)


    def test_merge_empty_node_based_license(self):
        '''
        Test input node-based file is empty, merge with existing license file
        '''
        # Setup
        existing_content = self.create_canonical_license_file()

        # Act
        register_node_based_license(self.module_path, TestLicenseRegister.empty_license_file_path)

        # Verify
        self.assertTrue(path.exists(self.canonical_license_file_path))
        self.assertTrue(path.isfile(self.canonical_license_file_path))
        with open(self.canonical_license_file_path, 'r') as lic_file:
            generated_content = lic_file.read()
            self.assertEqual(existing_content, generated_content.strip())


    def test_merge_node_based_lic_with_existing_file(self):
        '''
        Test registering a node-based license, merge with existing license file
        '''
        # Setup
        existing_content = self.create_canonical_license_file()
        expected_merged_content = '{}\n{}'.format(existing_content, 
            TestLicenseRegister.new_node_based_license_content)

        # Act
        register_node_based_license(self.module_path, TestLicenseRegister.new_license_file_path)

        # Verify
        self.assertTrue(path.exists(self.canonical_license_file_path))
        self.assertTrue(path.isfile(self.canonical_license_file_path))
        with open(self.canonical_license_file_path, 'r') as lic_file:
            generated_content = lic_file.read()
            self.assertEqual(expected_merged_content, generated_content)


    def test_register_floating_license(self):
        '''
        Test registering a floating license, no existing license file
        '''
        # Setup
        expected_floating_license_content = 'HOST localhost ANY 5053'

        # Act
        register_floating_license(self.module_path, 'localhost', 'ANY', 5053)
        
        # Verify
        self.assertTrue(path.exists(self.canonical_license_file_path))
        self.assertTrue(path.isfile(self.canonical_license_file_path))
        with open(self.canonical_license_file_path, 'r') as lic_file:
            generated_content = lic_file.read()
            self.assertEqual(expected_floating_license_content, generated_content)


    def test_merge_floating_lic_with_existing_file(self):
        '''
        Test registering a floating license, merge it with existing license file
        '''
        # Setup
        existing_content = self.create_canonical_license_file()
        expected_floating_license_content = 'HOST localhost ANY 5053'
        expected_merged_content = '{}\n{}'.format(expected_floating_license_content, existing_content)

        # Act
        register_floating_license(self.module_path, 'localhost', 'ANY', 5053)
        
        # Verify
        self.assertTrue(path.exists(self.canonical_license_file_path))
        self.assertTrue(path.isfile(self.canonical_license_file_path))
        with open(self.canonical_license_file_path, 'r') as lic_file:
            generated_content = lic_file.read()
            self.assertEqual(expected_merged_content, generated_content)
