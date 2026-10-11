"""Native evasion outcome binding and RNG counterfactuals, not a hit model."""
import hashlib
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab import current_hit_formula as h


class CurrentHitFormulaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for target in ('subprocess.Popen', 'socket.socket', 'sqlite3.connect'):
            guard = patch(target, side_effect=AssertionError('Offline native proof only'))
            guard.start()
            cls.addClassCleanup(guard.stop)
        cls.image = h.read_pinned(h.IMAGE, h.IMAGE_SHA256)

    def test_pin_size_and_original_dispatch_binding(self):
        with self.assertRaisesRegex(AssertionError, 'Pinned image'):
            h.NativeHit(bytes([self.image[0] ^ 1]) + self.image[1:])
        n = h.NativeHit(self.image)
        n.execute(0x1252)
        self.assertEqual((n.get('EAX'), n.get('ESP')), (15, h.SP + 4))
        size_entry = struct.unpack_from('<I', self.image, 0x1324 + 4 * 0x83)[0]
        self.assertEqual(size_entry, h.BASE + 0x1252)
        index = self.image[0x11465c + 0x83 - 0x1c]
        self.assertEqual(struct.unpack_from('<I', self.image, 0x114634 + 4 * index)[0],
                         h.BASE + 0x11436b)
        self.assertEqual(self.image[0x19ce48:0x19ce4d], bytes.fromhex('b06ac1d700'))
        self.assertEqual(self.image[0x147d87:0x147d96].hex(), '69c9fd43030081c1c39e2600894814')

    def test_continuous_incoming_outcome_vs_signed_amount(self):
        n = h.NativeHit(self.image)
        for outcome in (0, 6, 7, 8, 9, 11, 12):
            for amount in (-32768, -1, 0, 1, 32767):
                with self.subTest(outcome=outcome, amount=amount):
                    r = n.incoming(h.fixture(outcome, amount))
                    expected = {6: b'', 7: bytes.fromhex('a8bebf6d'),
                                8: bytes.fromhex('b06ac1d7')}.get(outcome, b'HP %+d')
                    self.assertEqual(bytes.fromhex(r['format_hex']), expected)
                    self.assertEqual(r['numeric_argument'], amount if b'%' in expected else None)
                    self.assertIn(dict(rva=0x12c612, address=h.RECORD + 11, size=1), r['reads'])
                    self.assertIn(dict(rva=0x12c615, address=h.RECORD + 9, size=2), r['reads'])
                    forwarded = next(c['arguments'] for c in r['calls'] if c['rva'] == 0x12b060)
                    self.assertEqual([a & 255 for a in forwarded[:4]], [0, 0, 1, 0])
                    self.assertEqual(forwarded[4] & 65535, amount & 65535)
                    self.assertEqual((forwarded[6] & 255, forwarded[7] & 255), (outcome, 34))
                    expected_writes = [
                        (0x116af4, h.BATTLE + 0xa9e9c6c, 4, 0),
                        (0x12c54d, h.CONTEXT + 0x309, 1, 1),
                        (0x12a953, h.ACTOR + 0x1e7, 1, 1),
                        (0x12a95f, h.ACTOR + 0x1e9, 1, 1),
                        (0x12a995, h.ACTOR + 0x1ea, 1, 17),
                        (0x12a9a1, h.ACTOR + 0x235, 1, 128),
                        (0x12a9a7, h.ACTOR + 0x233, 1, 0),
                        (0x12a9b4, h.ACTOR + 0x277, 1, 0),
                        (0x12a9c3, h.TARGET + 0x277, 1, 1),
                        (0x12b3cd, h.ACTOR + 0x286, 2, amount & 65535),
                        (0x12b3d4, h.ACTOR + 0x288, 2, 0),
                    ]
                    self.assertEqual([(w['rva'], w['address'], w['size'], w['value'])
                                      for w in r['writes']], expected_writes)
                    self.assertNotIn(0x147d7f, n.trace)
                    self.assertEqual(bytes(n.vm.mem_read(h.BASE, len(self.image))), self.image)

    def test_transmitted_status_flags_and_other_entity_bytes_do_not_choose_evasion(self):
        n = h.NativeHit(self.image)
        for flags in (0, 1, 0x40, 0xffffffff):
            for poison in (0, 0xa5):
                for outcome in (7, 8):
                    r = n.incoming(h.fixture(outcome, -32768), flags=flags, poison=poison)
                    self.assertEqual(r['format_rva'], 0x19ce48 if outcome == 8 else 0x19ce00)
                    for entity in (h.ACTOR, h.TARGET):
                        self.assertEqual(n.read(entity + 0xdb8, '<I')[0], flags)
                        self.assertFalse(any(entity + 0xdb8 <= read['address'] < entity + 0xdbc
                                             for read in r['reads']))
                    self.assertNotIn(0x147d7f, n.trace)

    def test_actual_rng_calls_stop_at_tls_without_substitution(self):
        n = h.NativeHit(self.image)
        result = n.rng_call_boundary()
        self.assertEqual(result['return_chain_rvas'], [0x147d84, 0x12a8a2])
        self.assertEqual(result['stop_rva'], 0x14e001)
        self.assertEqual(n.trace, [0x12a89d, 0x147d7f])
        self.assertEqual(n.writes, [])

    def test_original_rng_dword_wrap_and_fifteen_bit_output(self):
        n = h.NativeHit(self.image)
        for initial in (0, 1, 2, 42, 0x12345678, 0x7fffffff, 0x80000000, 0xffffffff):
            seed = initial
            for _ in range(4):
                result = n.rng_core(seed)
                expected_state = (seed * 0x343fd + 0x269ec3) & 0xffffffff
                self.assertEqual(result, dict(seed=seed, next_seed=expected_state,
                                              value=(expected_state >> 16) & 0x7fff))
                self.assertEqual(n.trace, [0x147d84, 0x147d87, 0x147d8d, 0x147d93,
                                           0x147d96, 0x147d98, 0x147d9b, 0x147da0])
                seed = result['next_seed']

    def test_remainder_boundaries_change_numeric_argument_not_outcome(self):
        n = h.NativeHit(self.image)
        for value in (0, 1, 98, 99, 100, 101, 199, 200, 32766, 32767):
            r = n.local_numeric_tail(value)
            self.assertEqual(r['format_text'], 'HP %+d')
            self.assertEqual(r['numeric_argument'], value % 100)
            call, = r['calls']
            self.assertEqual(call['arguments'], [0, 0, 1, 0, value % 100, 0, 0, 34])
            self.assertIn(0x12a8a8, n.trace)  # Original IDIV, not Python replacement.
            self.assertNotIn(0x12b41b, n.trace)  # Evasion-format push never selected.

    def test_action_mapping_and_state_modifiers_are_not_chance_modifiers(self):
        n = h.NativeHit(self.image)
        for outcome, mapped in ((0, 15), (7, 3), (8, 5), (11, 130)):
            for target_state in (0, 3):
                for secondary in (0, 34):
                    r = n.action_binding(outcome, target_state=target_state, secondary=secondary)
                    expected = 3 if target_state == 3 and mapped not in (5, 130) else mapped
                    if secondary == 0 and mapped != 130:
                        expected = 9
                    self.assertEqual(r['mapped_action'], mapped)
                    self.assertEqual(r['actor_raw_action'], mapped)
                    self.assertEqual(r['actor_action'], expected)
                    self.assertEqual(r['mapped_secondary'], 9 if secondary == 0 else 119)
                    self.assertTrue(all(w['address'] in (h.ACTOR + 0x1e8, h.ACTOR + 0x1eb,
                                       h.ACTOR + 0x232, h.TARGET + 0x232) and w['size'] == 1
                                        for w in r['writes']))
                    self.assertNotIn(0x147d7f, n.trace)

    def test_invalid_fixture_inputs_reject_before_execution(self):
        n = h.NativeHit(self.image)
        n.prepare()
        before = {p: bytes(n.vm.mem_read(p, 4096)) for p in n.pages}
        for record in (h.fixture()[:-1], h.fixture() + b'\0', bytes(15),
                       b'\x83\x02' + h.fixture()[2:]):
            with self.assertRaises(ValueError):
                n.incoming(record)
        for seed in (-1, 2**32, True):
            with self.assertRaises(ValueError):
                n.rng_core(seed)
        for value in (-1, 32768, True):
            with self.assertRaises(ValueError):
                n.local_numeric_tail(value)
        for page, expected in before.items():
            self.assertEqual(bytes(n.vm.mem_read(page, 4096)), expected)

    def test_report_replays_native_observations_and_exact_slices(self):
        report = h.build_report(self.image)
        self.assertEqual(report['counts'], dict(incoming_cases=35, rng_seed_cases=7,
                                                action_binding_cases=16))
        for row in report['slices']:
            raw = self.image[row['start_rva']:row['end_rva_exclusive']]
            self.assertEqual(row['raw_hex'], raw.hex())
            self.assertEqual(row['sha256'], hashlib.sha256(raw).hexdigest())
        for row in report['rng']:
            self.assertEqual(row['numeric_tail']['numeric_argument'], row['value'] % 100)
            self.assertEqual(row['numeric_tail']['calls'][0]['arguments'][6], 0)


if __name__ == '__main__':
    unittest.main()
