import os
import shutil
import tempfile

from tests.utils import get_tmp_file_location
from vfx_test_case import VfxTestCase
from utility.licenseRegister.licenseRegister import LICENSE_FILE_NAME, register_node_locked_license, register_floating_license
from os import path


def create_random_name_file(prefix, dir, file_content):
    '''
    Create file with give content and return file name.
    To prevent race condition, file name is randomized through given prefix and directory.
    '''
    file_path = get_tmp_file_location('.lic', prefix, dir)
    with open(file_path, 'w') as input_file:
        input_file.write(file_content)
    return file_path


def create_fixed_name_file(file_path, file_content):
    '''
    Create file with give content and return file name.
    '''
    with open(file_path, 'w') as input_file:
        input_file.write(file_content)
    return file_path


class TestLicenseRegister(VfxTestCase):

    # Constants
    floating_lic_content = '''
HOST localhost ANY 5054
HOST localhost ANY 5055
'''.strip()

    exist_node_locked_license_content = '''
LICENSE zivadyn ziva-vfx-author 1.99 1-jan-2020 uncounted hostid=ANY
  _ck=abcde123456 sig="AABBCCDDEEFF112233445566AABBCCDDEEFF112233445566
  ABCDEF123456ABCDEF123456ABCDEF123456"
'''.strip()

    new_node_locked_license_content1 = '''
LICENSE zivadyn ziva-vfx-author 1.99 1-feb-2020 uncounted hostid=ANY
  _ck=abcde123456 sig="AABBCCDDEEFF112233445566AABBCCDDEEFF112233445566
  ABCDEF123456ABCDEF123456ABCDEF123456"
'''.strip()

    new_node_locked_license_content2 = '''
LICENSE zivadyn ziva-vfx-author 1.99 1-mar-2020 uncounted hostid=ANY
  _ck=abcde123456 sig="AABBCCDDEEFF112233445566AABBCCDDEEFF112233445566
  ABCDEF123456ABCDEF123456ABCDEF123456"
'''.strip()

    @classmethod
    def setUpClass(cls):
        # setup module path
        cls.temp_dir = tempfile.gettempdir()
        cls.module_path = path.join(cls.temp_dir, 'Ziva/VFX/Ziva-VFX-Maya-Module')
        try:
            os.makedirs(cls.module_path)
        except OSError:
            pass  # path exists, skip

    def test_non_exist_input_node_locked_file(self):
        # Act
        with self.assertRaises(RuntimeError):
            register_node_locked_license(TestLicenseRegister.module_path, "non/exist/file/path")

        with self.assertRaises(RuntimeError):
            register_node_locked_license(TestLicenseRegister.module_path,
                                         TestLicenseRegister.module_path)

    def test_register_node_locked_license(self):
        '''
        Test registering node-locked license
        '''
        # Setup
        exist_node_locked_license_file = create_random_name_file(
            'exist_node_locked', TestLicenseRegister.module_path,
            TestLicenseRegister.exist_node_locked_license_content)
        new_license_file_in_temp_path = create_random_name_file(
            'new_node_locked_license', TestLicenseRegister.temp_dir,
            TestLicenseRegister.new_node_locked_license_content1)
        new_license_file_in_module_path = path.join(TestLicenseRegister.module_path,
                                                    path.basename(new_license_file_in_temp_path))

        # Act
        register_node_locked_license(TestLicenseRegister.module_path, new_license_file_in_temp_path)

        # Verify
        # Existing file unaffected
        self.assertTrue(path.exists(exist_node_locked_license_file))
        self.assertTrue(path.isfile(exist_node_locked_license_file))
        with open(exist_node_locked_license_file, 'r') as lic_file:
            generated_content = lic_file.read()
            self.assertEqual(TestLicenseRegister.exist_node_locked_license_content,
                             generated_content)

        # New file is copied to module path
        self.assertTrue(path.exists(new_license_file_in_module_path))
        self.assertTrue(path.isfile(new_license_file_in_module_path))
        with open(new_license_file_in_module_path, 'r') as lic_file:
            generated_content = lic_file.read()
            self.assertEqual(TestLicenseRegister.new_node_locked_license_content1,
                             generated_content)

    def test_overriding_existing_node_based_license(self):
        '''
        Test overriding existing node locked license file.
        This should not happen as each node locked license file name is unique.
        '''
        # Setup
        # Create same name file in both source and destination path
        license_file_in_src_path = create_random_name_file(
            'new_node_locked_license', TestLicenseRegister.temp_dir,
            TestLicenseRegister.new_node_locked_license_content1)
        license_file_in_dst_path = path.join(TestLicenseRegister.module_path,
                                             path.basename(license_file_in_src_path))
        create_fixed_name_file(license_file_in_dst_path,
                               TestLicenseRegister.new_node_locked_license_content2)

        # Act
        register_node_locked_license(TestLicenseRegister.module_path, license_file_in_src_path)

        # Verify
        # New file overrides same name file
        self.assertTrue(path.exists(license_file_in_dst_path))
        self.assertTrue(path.isfile(license_file_in_dst_path))
        with open(license_file_in_dst_path, 'r') as lic_file:
            generated_content = lic_file.read()
            self.assertEqual(TestLicenseRegister.new_node_locked_license_content1,
                             generated_content)

    def test_register_floating_license(self):
        '''
        Test registering a floating license, no existing license file
        '''
        # Setup
        expected_floating_license_content = 'HOST localhost ANY 5053'
        # The register_floating_license() function writes to
        # a fixed name license file. To randomize the path,
        # it needs a random folder name.
        temp_module_path = tempfile.mkdtemp(prefix='module')
        floating_license_file_path = path.join(temp_module_path, LICENSE_FILE_NAME)

        # Act
        register_floating_license(temp_module_path, 'localhost', 'ANY', 5053)

        # Verify
        self.assertTrue(path.exists(floating_license_file_path))
        self.assertTrue(path.isfile(floating_license_file_path))
        with open(floating_license_file_path, 'r') as lic_file:
            generated_content = lic_file.read()
            self.assertEqual(expected_floating_license_content, generated_content)

    def test_merge_floating_lic_with_existing_file(self):
        '''
        Test registering a floating license, merge it with existing license file
        '''
        # Setup
        # The register_floating_license() function writes to
        # a fixed name license file. To randomize the path,
        # it needs a random folder name.
        temp_module_path = tempfile.mkdtemp(prefix='module')
        floating_license_file_path = path.join(temp_module_path, LICENSE_FILE_NAME)
        create_fixed_name_file(floating_license_file_path, TestLicenseRegister.floating_lic_content)

        newly_added_floating_license_content = 'HOST localhost ANY 5053'
        expected_merged_content = '{}\n{}'.format(newly_added_floating_license_content,
                                                  TestLicenseRegister.floating_lic_content)

        # Act
        register_floating_license(temp_module_path, 'localhost', 'ANY', 5053)

        # Verify
        self.assertTrue(path.exists(floating_license_file_path))
        self.assertTrue(path.isfile(floating_license_file_path))
        with open(floating_license_file_path, 'r') as lic_file:
            generated_content = lic_file.read()
            self.assertEqual(expected_merged_content, generated_content)
