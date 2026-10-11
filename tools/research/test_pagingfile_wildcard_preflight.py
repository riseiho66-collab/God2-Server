import unittest

from tools.research.pagingfile_wildcard_preflight import client_math, resolve_paths


class PagefilePreflightTests(unittest.TestCase):
    def test_three_paths(self):
        for value, expected in [(699, 'MESSAGE_905_BRANCH'), (700, 'NO_WARNING_PATH'),
                                (701, 'EARLIER_MESSAGE_916_BRANCH')]:
            self.assertEqual(client_math(0, 2, 512, value)['predicted_branch'], expected)

    def test_real_observation(self):
        result = client_math(0, 8, 512, 122687082)
        self.assertEqual(result['T'], 490748328)
        self.assertEqual(result['predicted_branch'], 'EARLIER_MESSAGE_916_BRANCH')

    def test_uint32_and_signed_p(self):
        self.assertEqual(client_math(700, 8, 512, 0)['predicted_branch'], 'NO_WARNING_PATH')
        self.assertEqual(client_math(0, 0x80000000, 2, 9)['Q'], 0)
        self.assertEqual(client_math(0, 2, 512, 0x100000001)['Q'], 1)
        self.assertEqual(client_math(0xffffffff, 2, 512, 702)['predicted_branch'], 'EARLIER_MESSAGE_916_BRANCH')

    def test_active_path_not_system_drive_guess(self):
        self.assertEqual(resolve_paths([r'\??\D:\pagefile.sys']),
                         ([r'D:\pagefile.sys'], ['D:\\']))

    def test_ambiguous_resolution_fails(self):
        for paths in [[], [r'?:\pagefile.sys'], [r'C:\pagefile.sys', r'D:\pagefile.sys'], ['pagefile.sys']]:
            with self.subTest(paths=paths), self.assertRaises(ValueError):
                resolve_paths(paths)


if __name__ == '__main__':
    unittest.main()
