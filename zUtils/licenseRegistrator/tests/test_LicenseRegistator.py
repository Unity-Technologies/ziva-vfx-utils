import unittest
from os import path
from zUtils.licenseRegistrator import licenseRegistrator

class TestLicenseRegistrator(unittest.TestCase):
  
  def setUp(self):
    super(TestLicenseRegistrator, self).setUp()
    plugin_path = path.abspath(__file__)
    self.licReg = licenseRegistrator.LicenseRegistrator(plugin_path)

  def test_node_based_license_registration(self):
    self.licReg.set_node_based_license_info('ZivaVFX.lic')
    self.assertTrue(self.licReg.register())


  def test_floating_license_registration(self):
    self.licReg.set_floating_license_info({})
    self.assertTrue(self.licReg.register())


if __name__ == '__main__':
  unittest.main()