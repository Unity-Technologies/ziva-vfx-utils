from vfx_test_case import VfxTestCase
from os import path
import utils.licenseRegister.licenseRegister as licReg

class TestLicenseRegister(VfxTestCase):
  
  def setUp(self):
    super(TestLicenseRegister, self).setUp()
    plugin_path = path.abspath(__file__)
    self.licReg = licReg.LicenseRegister(plugin_path)


  def test_register_node_based_license(self):
    self.licReg.set_node_based_license_info('ZivaVFX.lic')
    self.assertTrue(self.licReg.register())


  def test_register_floating_license(self):
    self.licReg.set_floating_license_info({})
    self.assertTrue(self.licReg.register())
