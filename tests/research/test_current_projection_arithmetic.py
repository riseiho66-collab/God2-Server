import unittest

from tools.strike_lab.current_projection_arithmetic import (
    ProjectionProof, END, ALTERNATE, MASK, signed, SP, BATTLE,
)


class ProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proof = ProjectionProof()

    def test_native_matrix(self):
        for mode in (0, 1, MASK):
            for descriptor in (0x01, 0x11, 0x21, 0x31, 0xf1):
                for current, supplied in ((100, 20), (60, 20), (0, 0),
                                          (100, MASK), (100, 0x40000000),
                                          (0x7fffffff, 1), (0x80000000, 0)):
                    with self.subTest(mode=mode, descriptor=descriptor,
                                      current=current, supplied=supplied):
                        result = self.proof.run(current, supplied, descriptor, mode)
                        delta = (supplied * (descriptor >> 4)) & MASK if mode else supplied
                        zero = signed(current) <= signed(delta)
                        expected = 0 if zero else (current - delta) & MASK
                        self.assertEqual(result['projected'], expected)
                        self.assertEqual(result['zero_branch'], int(zero))
                        self.assertEqual(result['stop_rva'], END)
                        self.assertTrue(result['source_unchanged'])
                        self.assertEqual([r[2] for r in result['reads']], [1, 4])
                        self.assertEqual({w[1] for w in result['writes']},
                                         {SP + 0x74, SP + 0x9c})

    def test_native_indexed_inputs(self):
        for row, column, slot in ((0, 0, 0), (1, 1, 2), (3, 1, 13)):
            result = self.proof.run(100, 20, 0x31, 1, row=row, column=column, slot=slot)
            self.assertEqual(result['projected'], 40)
            self.assertEqual(result['reads'][1][1],
                             BATTLE + 0xa9ea508 + row * 32 + column * 8)
            self.assertEqual(result['writes'][-1][1], SP + 0x9c + slot * 4)

    def test_other_descriptor_arm_stops_before_execution(self):
        for descriptor in (3, 4, 0xf3, 0xf4):
            result = self.proof.run(100, 20, descriptor, 1)
            self.assertEqual(result['stop_rva'], ALTERNATE)
            self.assertEqual(result['projected'], 100)
            self.assertEqual([r[2] for r in result['reads']], [1])
            self.assertEqual({w[1] for w in result['writes']}, {SP + 0x74})

    def test_invalid_live_ins(self):
        for args in ((-1, 20, 0x31, 1), (100, 1 << 32, 0x31, 1),
                     (100, 20, 256, 1), (100, 20, 0x31, True)):
            with self.assertRaises(ValueError):
                self.proof.run(*args)


if __name__ == '__main__':
    unittest.main()
