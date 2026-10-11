import unittest

from tools.strike_lab.current_projection_sink import run_sink, CONTEXT, NET


class SinkTests(unittest.TestCase):
    def test_continuous_native_tail_to_encoder(self):
        for text in (b'!\x05\x16actor 3', b'!\x05\x16actor 4', b'!\x05\x16',
                     b'!\x05\x16' + b'x' * 117):
            result = run_sink(text)
            self.assertEqual(result['stop_rva'], 0x132e0)
            self.assertEqual(result['return_rva'], 0x96f29)
            self.assertEqual(result['encoder_this'], NET)
            self.assertEqual(result['opcode'], 0x2f)
            self.assertEqual(result['channel'], 1)
            self.assertEqual(bytes.fromhex(result['text_hex']), text[1:] + b'\x00')
            self.assertEqual(result['body_size'], len(text) + 6)
            self.assertEqual(result['declared_length'], result['body_size'] + 1)
            self.assertEqual(result['calls_reached'], [0x96990, 0x148810, 0x131c10, 0x147f90])
            for _, address, size, _ in result['outside_stack_writes']:
                self.assertTrue(CONTEXT + 0x5bfa8 <= address and
                                address + size <= CONTEXT + 0x5bfa8 + 264)

    def test_unassigned_header_byte_is_not_a_verified_constant(self):
        zero, poison = run_sink(padding=0), run_sink(padding=0xa5)
        a, b = bytes.fromhex(zero['body_hex']), bytes.fromhex(poison['body_hex'])
        self.assertEqual([i for i, (x, y) in enumerate(zip(a, b)) if x != y], [3])
        self.assertEqual(zero['text_hex'], poison['text_hex'])

    def test_invalid_fixture_rejected(self):
        for text in (b'', b'ordinary text', b'!\x05\x16\x00', b'!\x05\x16' + b'x' * 118):
            with self.assertRaises(ValueError):
                run_sink(text)


if __name__ == '__main__':
    unittest.main()
