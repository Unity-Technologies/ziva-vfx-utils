import os
import zBuilder.builders.ziva as zva
from maya import cmds
from maya import mel

from vfx_test_case import VfxTestCase, attr_values_from_scene


class ZivaFieldGenericTestCase(VfxTestCase):
    @classmethod
    def setUpClass(cls):
        cls.field_names = ["airField1", "dragField1", "gravityField1", "newtonField1", "radialField1", "turbulenceField1", "uniformField1", "vortexField1"]
        cls.field_attrs = ["magnitude", "attenuation", "useMaxDistance"]

    def setUp(self):
        super(ZivaFieldGenericTestCase, self).setUp()
        # Setup simple scene with 2 spheres and 2 joints
        obj = cmds.polySphere(ch=False, n="field_mesh")
        cmds.select(obj)
        cmds.ziva(t=True)
        mel.eval('source zivaMenuFunctions;')
        mel.eval('ziva_attachField("air");')
        mel.eval('ziva_attachField("drag");')
        mel.eval('ziva_attachField("gravity");')
        mel.eval('ziva_attachField("newton");')
        mel.eval('ziva_attachField("radial");')
        mel.eval('ziva_attachField("turbulence");')
        mel.eval('ziva_attachField("uniform");')
        mel.eval('ziva_attachField("vortex");')
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

    def tearDown(self):
        if os.path.exists(self.temp_file_path):
            os.remove(self.temp_file_path)
        super(ZivaFieldGenericTestCase, self).tearDown()

    def check_retrieve_field_looks_good(self, builder):
        """Args:
            builder (builders.fields.Fields()): builder object
        """
        field_types = ["airField", "dragField", "gravityField", "newtonField", "radialField", "turbulenceField", "uniformField", "vortexField"]
        self.check_retrieve_looks_good(builder, {}, self.field_names, field_types)

    def test_retrieve(self):
        self.check_retrieve_field_looks_good(self.builder)

    def test_build_restores_attr_values(self):
        plug_names = {
            '{}.{}'.format(geo, attr)
            for geo in self.field_names for attr in self.field_attrs
        }
        attrs_before = attr_values_from_scene(plug_names)

        # remove all field nodes from the scene and build them
        cmds.select(cmds.ls(type="field"))
        mel.eval("doDelete;")
        self.builder.build()

        attrs_after = attr_values_from_scene(plug_names)
        self.assertEqual(attrs_before, attrs_after)

    def test_builder_has_same_field_nodes_after_writing_to_disk(self):
        ## ACT
        self.builder.write(self.temp_file_path)

        ## VERIFY
        self.assertTrue(os.path.exists(self.temp_file_path))

        ## ACT
        builder = zva.Ziva()
        builder.retrieve_from_file(self.temp_file_path)

        ## VERIFY
        self.check_retrieve_field_looks_good(builder)

    def test_build(self):
        ## SETUP
        cmds.select(cmds.ls(type="field"))
        mel.eval("doDelete;")

        ## ACT
        self.builder.build()
        builder = zva.Ziva()
        builder.retrieve_from_scene()

        ## VERIFY
        self.check_retrieve_field_looks_good(builder)

    def test_build_from_file(self):
        ## SETUP
        self.builder.write(self.temp_file_path)
        self.assertTrue(os.path.exists(self.temp_file_path))
        cmds.select(cmds.ls(type="field"))
        mel.eval("doDelete;")

        ## ACT
        builder = zva.Ziva()
        builder.retrieve_from_file(self.temp_file_path)
        builder.build()

        builder = zva.Ziva()
        cmds.select("zSolver1")
        builder.retrieve_from_scene()
        self.check_retrieve_field_looks_good(builder)

    def test_string_replace(self):
        ## VERIFY
        # check if an item exists before string_replace
        field = self.builder.get_scene_items(name_filter="airField1")
        self.assertGreaterEqual(len(field), 1)

        ## ACT
        self.builder.string_replace("airField1", "airField2")

        ## VERIFY
        field = self.builder.get_scene_items(name_filter="airField1")
        self.assertEqual(field, [])
        field = self.builder.get_scene_items(name_filter="airField2")
        self.assertEqual(len(field), 1)

    def test_build_changes_attribute_value(self):
        ## SETUP
        cmds.setAttr('airField1.useMaxDistance', 1)

        ## ACT
        self.builder.build()

        ## VERIFY
        # if built properly value should be 0
        self.assertEqual(cmds.getAttr('airField1.useMaxDistance'), 0)
