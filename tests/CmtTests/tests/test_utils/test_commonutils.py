from vfx_test_case import VfxTestCase
from zBuilder.utils.commonUtils import parse_version_info


class CommonUtilsTestCase(VfxTestCase):

    def test_version_parse_function(self):
        # Valid cases
        # major.minor.patch-tag
        major, minor, patch, tag = parse_version_info("1.2.30-alpha")
        self.assertEqual(major, 1)
        self.assertEqual(minor, 2)
        self.assertEqual(patch, 30)
        self.assertEqual(tag, "alpha")

        # major.minor.patch
        major, minor, patch, tag = parse_version_info("1.20.3")
        self.assertEqual(major, 1)
        self.assertEqual(minor, 20)
        self.assertEqual(patch, 3)
        self.assertEqual(tag, "")

        # major.minor-tag
        major, minor, patch, tag = parse_version_info("1.33-beta")
        self.assertEqual(major, 1)
        self.assertEqual(minor, 33)
        self.assertEqual(patch, 0)
        self.assertEqual(tag, "beta")

        # major.minor
        major, minor, patch, tag = parse_version_info("10.2")
        self.assertEqual(major, 10)
        self.assertEqual(minor, 2)
        self.assertEqual(patch, 0)
        self.assertEqual(tag, "")

        # Invalid cases
        # major-tag
        with self.assertRaises(AssertionError):
            parse_version_info("1-gammar")

        # major only
        with self.assertRaises(AssertionError):
            parse_version_info("1")

        # non-integer version number
        with self.assertRaises(AssertionError):
            parse_version_info("1.0c")

        # missing major version
        with self.assertRaises(AssertionError):
            parse_version_info(".1.2")

        # negative version number
        with self.assertRaises(AssertionError):
            parse_version_info("1.-2")
