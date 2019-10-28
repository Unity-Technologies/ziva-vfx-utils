class LicenseRegistrator(object):

  # License type
  NODE_BASED_LICENSE = 0
  FLOATING_LICENSE = 1

  def __init__(self, plugin_path):
    super(LicenseRegistrator, self).__init__()
    self.plugin_path = plugin_path
    self.license_type = None
    self.license_path = None # for Node-based license
    self.license_server_info = {} # for Floating license


  def set_node_based_license_info(self, license_path):
    self.license_type = LicenseRegistrator.NODE_BASED_LICENSE
    self.license_path = license_path


  def set_floating_license_info(self, license_server_info):
    self.license_type = LicenseRegistrator.FLOATING_LICENSE
    self.license_server_info = license_server_info


  def register(self):
    if LicenseRegistrator.NODE_BASED_LICENSE == self.license_type:
      self._register_node_based_license()
    elif LicenseRegistrator.FLOATING_LICENSE == self.license_type:
      self._register_floating_license()
    else:
      raise ValueError("Unknonwn license type: {}".format(self.license_type))
    
    return True


  def _register_node_based_license(self):
    pass


  def _register_floating_license(self):
    pass