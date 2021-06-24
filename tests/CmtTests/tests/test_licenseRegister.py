import unittest
import os
from os import path
import tempfile
from vfx_test_case import VfxTestCase
from utility.licenseRegister.licenseRegister import LICENSE_FILE_NAME
from utility.licenseRegister.licenseRegister import register_node_locked_license, register_floating_license


def create_file(file_path, file_content):
    with open(file_path, 'w') as input_file:
        input_file.write(file_content)


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

        # setup floating license file path
        cls.floating_license_file_path = path.join(cls.module_path, LICENSE_FILE_NAME)
        cls.floating_lic_content = '''
HOST localhost ANY 5054
HOST localhost ANY 5055
'''.strip()

        # create existing node locked license file
        cls.exist_node_locked_license_file_path = path.join(cls.module_path,
                                                            'exist_node_locked.lic')
        cls.exist_node_locked_license_content = '''
LICENSE zivadyn ziva-vfx-author 1.99 1-jan-2020 uncounted hostid=ANY
  _ck=abcde12345 sig="AABBCCDDEEFF112233445566AABBCCDDEEFF112233445566
  ABCDEF123456ABCDEF123456ABCDEF123456"
'''.strip()
        create_file(cls.exist_node_locked_license_file_path, cls.exist_node_locked_license_content)

        # create new node locked license file
        cls.new_license_file_name = 'new_node_locked_license.lic'
        cls.new_license_file_path = path.join(cls.temp_dir, cls.new_license_file_name)
        cls.new_license_file_in_module_path = path.join(cls.module_path, cls.new_license_file_name)
        cls.new_node_locked_license_content1 = '''
LICENSE zivadyn ziva-vfx-author 1.99 1-feb-2020 uncounted hostid=ANY
  _ck=abcde12345 sig="AABBCCDDEEFF112233445566AABBCCDDEEFF112233445566
  ABCDEF123456ABCDEF123456ABCDEF123456"
'''.strip()

        # setup another node locked license content, for overriding test
        cls.new_node_locked_license_content2 = '''
LICENSE zivadyn ziva-vfx-author 1.99 1-mar-2020 uncounted hostid=ANY
  _ck=abcde12345 sig="AABBCCDDEEFF112233445566AABBCCDDEEFF112233445566
  ABCDEF123456ABCDEF123456ABCDEF123456"
'''.strip()

    @classmethod
    def tearDownClass(cls):
        delete_file(cls.new_license_file_in_module_path)
        delete_file(cls.new_license_file_path)
        delete_file(cls.exist_node_locked_license_file_path)
        delete_file(cls.new_license_file_path)

        if path.exists(cls.module_path) and path.isdir(cls.module_path):
            os.removedirs(cls.module_path)

    def tearDown(self):
        # delete these files as their content changes between test cases
        delete_file(self.floating_license_file_path)
        delete_file(self.new_license_file_in_module_path)
        super(TestLicenseRegister, self).tearDown()

    # --------------------------------------------------------------------------------

    def test_non_exist_input_node_locked_file(self):
        # Act
        with self.assertRaises(RuntimeError):
            register_node_locked_license(self.module_path, "non/exist/file/path")

        with self.assertRaises(RuntimeError):
            register_node_locked_license(self.module_path, self.module_path)

    def test_register_node_locked_license(self):
        '''
        Test registering node-locked license
        '''
        # Setup
        create_file(self.new_license_file_path, self.new_node_locked_license_content1)

        # Act
        register_node_locked_license(self.module_path, self.new_license_file_path)

        # Verify
        # Existing file unaffected
        self.assertTrue(path.exists(self.exist_node_locked_license_file_path))
        self.assertTrue(path.isfile(self.exist_node_locked_license_file_path))
        with open(self.exist_node_locked_license_file_path, 'r') as lic_file:
            generated_content = lic_file.read()
            self.assertEqual(self.exist_node_locked_license_content, generated_content)

        # New file is copied to module path
        self.assertTrue(path.exists(self.new_license_file_in_module_path))
        self.assertTrue(path.isfile(self.new_license_file_in_module_path))
        with open(self.new_license_file_in_module_path, 'r') as lic_file:
            generated_content = lic_file.read()
            self.assertEqual(self.new_node_locked_license_content1, generated_content)

    def test_overriding_existing_node_based_license(self):
        '''
        Test overriding existing node locked license file.
        This should not happen as each node locked license file name is unique.
        '''
        # Setup
        # Create new license file in source and destination path
        create_file(self.new_license_file_in_module_path, self.new_node_locked_license_content1)
        create_file(self.new_license_file_path, self.new_node_locked_license_content2)

        # Act
        register_node_locked_license(self.module_path, self.new_license_file_path)

        # Verify
        # Existing file unaffected
        self.assertTrue(path.exists(self.exist_node_locked_license_file_path))
        self.assertTrue(path.isfile(self.exist_node_locked_license_file_path))
        with open(self.exist_node_locked_license_file_path, 'r') as lic_file:
            generated_content = lic_file.read()
            self.assertEqual(self.exist_node_locked_license_content, generated_content)

        # New file overrides same name file
        self.assertTrue(path.exists(self.new_license_file_in_module_path))
        self.assertTrue(path.isfile(self.new_license_file_in_module_path))
        with open(self.new_license_file_in_module_path, 'r') as lic_file:
            generated_content = lic_file.read()
            self.assertEqual(self.new_node_locked_license_content2, generated_content)

    def test_register_floating_license(self):
        '''
        Test registering a floating license, no existing license file
        '''
        # Setup
        expected_floating_license_content = 'HOST localhost ANY 5053'

        # Act
        register_floating_license(self.module_path, 'localhost', 'ANY', 5053)

        # Verify
        self.assertTrue(path.exists(self.floating_license_file_path))
        self.assertTrue(path.isfile(self.floating_license_file_path))
        with open(self.floating_license_file_path, 'r') as lic_file:
            generated_content = lic_file.read()
            self.assertEqual(expected_floating_license_content, generated_content)

    def test_merge_floating_lic_with_existing_file(self):
        '''
        Test registering a floating license, merge it with existing license file
        '''
        # Setup
        create_file(self.floating_license_file_path, self.floating_lic_content)
        expected_floating_license_content = 'HOST localhost ANY 5053'
        expected_merged_content = '{}\n{}'.format(expected_floating_license_content,
                                                  self.floating_lic_content)

        # Act
        register_floating_license(self.module_path, 'localhost', 'ANY', 5053)

        # Verify
        self.assertTrue(path.exists(self.floating_license_file_path))
        self.assertTrue(path.isfile(self.floating_license_file_path))
        with open(self.floating_license_file_path, 'r') as lic_file:
            generated_content = lic_file.read()
            self.assertEqual(expected_merged_content, generated_content)
