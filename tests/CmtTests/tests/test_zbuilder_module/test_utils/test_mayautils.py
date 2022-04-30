from vfx_test_case import VfxTestCase
from zBuilder.utils.mayaUtils import replace_long_name


class MayaUtilsTestCase(VfxTestCase):

    def test_replace_long_name_usecase1(self):
        # searching and replacing r_ at begining of string
        # check long name use case
        strings = [
            'r_bicep', 'r_bicep__r_tricep', '|muscle_geo|r_bicep', 'rr_bicep', '|r_bicep',
            'r_bicep_r'
        ]

        outputs = [
            'l_bicep', 'l_bicep__r_tricep', '|muscle_geo|l_bicep', 'rr_bicep', '|l_bicep',
            'l_bicep_r'
        ]

        results = list()

        for case in strings:
            results.append(replace_long_name('^r_', 'l_', case))

        self.assertEqual(results, outputs)

    def test_replace_long_name_usecase2(self):
        strings = [
            'r_bicep', 'r_bicep__r_tricep', '|muscle_geo|r_bicep', 'rr_bicep', '|r_bicep',
            'r_bicep_r'
        ]

        outputs = [
            'r_bicep', 'r_bicep__l_tricep', '|muscle_geo|r_bicep', 'rr_bicep', '|r_bicep',
            'r_bicep_r'
        ]

        results = list()

        for case in strings:
            results.append(replace_long_name('_r_', '_l_', case))

        self.assertEqual(results, outputs)

    def test_replace_long_name_prefix(self):
        # yapf: disable
        expected = {
            'r_bicep'           : 'prefix_r_bicep',
            'r_bicep__r_tricep' : 'prefix_r_bicep__r_tricep',
            '|r_bicep'          : '|prefix_r_bicep',
            '|foo|r_bicep'      : '|prefix_foo|prefix_r_bicep',
            '|foo|bar|r_bicep'  : '|prefix_foo|prefix_bar|prefix_r_bicep',
            None                :  None,
            ''                  : '',
            ' '                 : ' ',
        }
        # yapf: enable
        observed = {k: replace_long_name('^', 'prefix_', k) for k in expected.keys()}

        self.assertDictEqual(expected, observed)

    def test_replace_long_name_postfix(self):
        # yapf: disable
        expected = {
            'r_bicep'           : 'r_bicep_postfix',
            'r_bicep__r_tricep' : 'r_bicep__r_tricep_postfix',
            '|r_bicep'          : '|r_bicep_postfix',
            '|foo|r_bicep'      : '|foo_postfix|r_bicep_postfix',
            '|foo|bar|r_bicep'  : '|foo_postfix|bar_postfix|r_bicep_postfix',
            None                :  None,
            ''                  : '',
            ' '                 : ' ',
        }
        # yapf: enable
        observed = {k: replace_long_name('$', '_postfix', k) for k in expected.keys()}

        self.assertDictEqual(expected, observed)

    def test_replace_long_name_groups(self):
        # yapf: disable
        expected = {
            '|muscles_geo|bicep_r|muscle_r' : '|muscles_geo|bicep_l|muscle_l',
            'rr_bicep'                      : 'rr_bicep',
            'r_bicep'                       : 'l_bicep',
            'r_bicep__r_tricep'             : 'l_bicep__l_tricep',
            '|r_bicep'                      : '|l_bicep',
            '|foo|r_bicep'                  : '|foo|l_bicep',
            '|foo|bar|r_bicep'              : '|foo|bar|l_bicep',
            None                            :  None,
            ''                              : '',
            ' '                             : ' ',
        }
        # yapf: enable
        observed = {k: replace_long_name('(^|_)r($|_)', 'l', k) for k in expected.keys()}

        self.assertDictEqual(expected, observed)
