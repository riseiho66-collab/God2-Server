"""World cache/path/ROM native chain; no original process or rendered world."""
from pathlib import Path
import hashlib
import json
import struct
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab.current_appearance_resources import AppearanceResources, RECORDS
from tools.strike_lab.current_world_role_resources import (
    NativeWorldRoleResources, COUNTER, CWD, DIRECTORY, ACTOR, COMPONENT_MANAGER)
from tools.strike_lab.current_role_doll_resources import BANK as ROM_BANK, STRIDE
from tools.strike_lab.current_indoor_resources import SP
import test_current_world_entry as entry


class CurrentWorldRoleResourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.appearance = AppearanceResources()

    def native(self):
        return NativeWorldRoleResources(self.appearance)

    def test_uncached_wrapper_real_load_cache_commit_and_cached_reuse(self):
        n = self.native()
        cases = [((0, 2, 0, 0, 0), 'r1h000', 'r01w800.romz', 4201),
                 ((0, 1, 0, 2, 0), 'r1f002', 'r01f002.romz', 4001),
                 ((1, 1, 0, 2, 0), 'r2f002', 'r02f002.romz', 0),
                 ((1, 2, 0, 0, 0), 'r2h000', 'r01w800.romz', 4201)]
        for slot, (key, label, filename, native_id) in enumerate(cases):
            self.assertEqual(n.cache(label), 0xffff)
            self.assertEqual(n.load_key(*key), slot)
            self.assertEqual(n.next_slot, slot+1)
            self.assertEqual(n.cache(label), slot)
            self.assertEqual(n.opens[-1], DIRECTORY+filename)
            self.assertEqual(n.u32(ROM_BANK+slot*STRIDE), native_id)
            self.assertEqual(n.cache_writes[-1], ((n.record_by_key[label]-RECORDS)//44, slot))
        # Identical filenames under two real keys have independent cache slots.
        self.assertNotEqual(n.cache('r1h000'), n.cache('r2h000'))
        before = (len(n.opens), len(n.cache_writes), len(n.parser_inputs), n.next_slot)
        for _ in range(2):
            for slot, (key, label, _, _) in enumerate(cases):
                self.assertEqual(n.load_key(*key), slot)
                self.assertEqual(n.cache(label), slot)
        self.assertEqual((len(n.opens), len(n.cache_writes), len(n.parser_inputs), n.next_slot), before)
        for rva in (0x526f0, 0x52680, 0x12f550):
            self.assertEqual(n.wrapper_visits.count(rva), 4)
        self.assertEqual(n.wrapper_visits.count(0x526c0), 12)
        self.assertEqual(n.native_visits.count(0x29820), 4)
        self.assertEqual(n.cwd_calls, 1)
        prefix = CWD.decode().replace('\\', '/').lower()+'/'
        self.assertEqual(n.full_paths, [prefix+DIRECTORY+c[2] for c in cases])
        expected = bytearray(n.record_baseline)
        for ordinal, value in n.cache_writes:
            struct.pack_into('<H', expected, ordinal*44+30, value)
        self.assertEqual(bytes(n.vm.mem_read(RECORDS, len(expected))), expected)
        self.assertEqual(bytes(n.vm.mem_read(COUNTER+2, 14)), b'\xa5'*14)
        self.assertFalse(n.handles)
        self.assertEqual(n.u32(0), 0xffffffff)

    def test_failed_rom_does_not_publish_cache_or_consume_slot_and_can_retry(self):
        n = self.native()
        path = DIRECTORY+'r01f002.romz'
        raw = n.files.pop(path)
        before = bytes(n.vm.mem_read(ROM_BANK, STRIDE))
        self.assertEqual(n.load_key(0, 1, 0, 2, 0), 0xffff)
        self.assertEqual(n.cache('r1f002'), 0xffff)
        self.assertEqual(n.next_slot, 0)
        self.assertFalse(n.cache_writes)
        self.assertFalse(n.parser_inputs)
        self.assertEqual(bytes(n.vm.mem_read(ROM_BANK, STRIDE)), before)
        self.assertFalse(n.handles)
        n.files[path] = raw
        self.assertEqual(n.load_key(0, 1, 0, 2, 0), 0)
        self.assertEqual(n.cache('r1f002'), 0)
        self.assertEqual(n.next_slot, 1)
        self.assertEqual(n.u32(0), 0xffffffff)

    def test_last_real_slot_then_full_bank_rejects_miss_but_preserves_hit(self):
        n = self.native()
        n.vm.mem_write(COUNTER, struct.pack('<H', 511))
        self.assertEqual(n.load_key(0, 1, 0, 2, 0), 511)
        self.assertEqual(n.cache('r1f002'), 511)
        self.assertEqual(n.next_slot, 512)
        self.assertEqual(n.u32(ROM_BANK+511*STRIDE), 4001)
        before = (list(n.opens), list(n.cache_writes), list(n.parser_inputs))
        self.assertEqual(n.load_key(1, 1, 0, 2, 0), 0xffff)
        self.assertEqual(n.cache('r2f002'), 0xffff)
        self.assertEqual(n.load_key(0, 1, 0, 2, 0), 511)
        self.assertEqual(n.next_slot, 512)
        self.assertEqual((n.opens, n.cache_writes, n.parser_inputs), before)

    def test_unqualified_format_bounds_are_rejected_before_native_execution(self):
        n = self.native()
        for key in ((), (0, 4, 0, 0, 0), (0, 2, 0, 0, 3), (-1, 2, 0, 0, 0),
                    (256, 2, 0, 0, 0)):
            with self.assertRaises(ValueError):
                n.load_key(*key)
        self.assertEqual(n.next_slot, 0)
        self.assertFalse(n.wrapper_visits)
        self.assertFalse(n.opens)

    def test_consumer_rejects_unqualified_selectors_and_blocks_before_loading(self):
        n = self.native()
        normal = bytearray(36)
        normal[18] = 0x80
        malformed = [bytes(normal[:length]) for length in range(36)] + [bytes(normal)+b'\0']
        for offset, value in ((6, 1), (6, 27), (2, 1), (32, 1), (12, 2),
                              (13, 0xe0), (15, 1), (16, 1), (18, 0), (19, 1)):
            changed = bytearray(normal)
            changed[offset] = value
            malformed.append(bytes(changed))
        for body in malformed:
            with self.assertRaises(ValueError):
                n.consume_world_appearance(body)
        for block in (b'', bytes(7), bytes(9), bytes.fromhex('0000000000000000')):
            with self.assertRaises(ValueError):
                n.load_components(block)
        self.assertFalse(n.component_manager_ready)
        self.assertFalse(n.actor_ready)
        self.assertFalse(n.wrapper_visits)
        self.assertFalse(n.opens)

    def test_full_component_loader_and_all_native_accessory_rows(self):
        n = self.native()
        self.assertEqual(n.load_components(bytes.fromhex('0000000000008000')),
                         (0, 1, 2, 3, 0xffff, 0xffff))
        self.assertEqual(n.load_components(bytes.fromhex('0100010001008100')),
                         (4, 5, 6, 7, 0xffff, 0xffff))
        self.assertEqual(n.next_slot, 8)
        self.assertEqual(len(n.opens), 8)
        self.assertEqual(len(set(n.opens)), 6)
        self.assertEqual(struct.unpack('<H', n.vm.mem_read(
            COMPONENT_MANAGER+0x682e0+0x24f70, 2))[0], 120)
        factor = struct.unpack('<f', n.vm.mem_read(0x570cbc, 4))[0]
        for ordinal, row in enumerate(n.accessory_rows):
            record = bytes(n.vm.mem_read(n.accessory_records+136*ordinal, 136))
            self.assertEqual(struct.unpack_from('<H', record)[0], int(row[1] or 0))
            self.assertEqual(record[2:4], b'\xff\xff')
            self.assertEqual(record[4:8], struct.pack('<f', int(row[3])*factor))
            self.assertEqual(record[8:].split(b'\0')[0], row[4].encode('ascii'))
        self.assertEqual(n.accessory_rows[0][4], '')
        self.assertFalse(n.handles)

    def test_native_world_consumer_real_resources_for_all_98_preview_blocks(self):
        n = self.native()
        for binary in (0, 1):
            for first in range(7):
                for second in range(7):
                    block = bytes([binary, first << 5, binary, second << 5,
                                   binary, 0, 0x80 | binary, 0])
                    body = bytearray(36)
                    body[12:20] = block
                    handles, variants = n.consume_world_appearance(bytes(body))
                    self.assertEqual(handles, tuple(range(4*binary, 4*binary+4)))
                    self.assertEqual(variants, (first, second, 0, 0))
                    self.assertEqual(bytes(n.vm.mem_read(ACTOR+0x4584, 12)), body[12:24])
                    self.assertEqual(n.u32(ACTOR+0x28), first)
        self.assertEqual(n.next_slot, 8)
        self.assertEqual(len(n.opens), 8)
        handles, variants = n.consume_world_appearance(bytes(body), override=True)
        self.assertEqual(handles, (4, 5, 6, 7))
        self.assertEqual(variants, (7, 7, 7, 7))
        self.assertEqual(len(n.opens), 8)
        self.assertEqual(n.next_slot, 8)
        self.assertFalse(n.handles)
        self.assertEqual(n.u32(0), 0xffffffff)

    def test_retained_production_candidate_uses_actual_mounted_resources(self):
        fixture = json.loads((ROOT / 'tests/fixtures/recovered-world-entry.json').read_text())
        body = bytes.fromhex(fixture['body_hex'])
        self.assertEqual(hashlib.sha256(body).hexdigest(),
                         '79e98fef8d5e97c16eb60b52ba806cf965509f46e230b6010ff9671bea8e8aa7')
        n = self.native()
        handles, variants = n.consume_world_appearance(body)
        self.assertEqual(handles, (0, 1, 2, 3))
        self.assertEqual(variants, (4, 3, 3, 0))
        self.assertEqual(struct.unpack('<6H', n.vm.mem_read(SP+0x1c, 12)),
                         (0, 1, 2, 3, 4, 0xffff))
        self.assertEqual(n.opens, [DIRECTORY+'r02b600.romz', DIRECTORY+'r02f102.romz',
                                  DIRECTORY+'r01w800.romz', DIRECTORY+'r02w800.romz',
                                  'data2/rom/drv/drv5477.romz'])
        self.assertEqual(n.attempts, n.opens)
        self.assertEqual(n.next_slot, 5)
        self.assertEqual([n.cache(key) for key in ('r2b600', 'r2f102', 'r2h900', 'r2w800')],
                         [0, 1, 2, 3])
        mount_record = COMPONENT_MANAGER+0x682e0+0x121f8+27*32
        self.assertEqual(struct.unpack('<H', n.vm.mem_read(mount_record+16, 2))[0], 4)
        entry.CurrentWorldEntryTests.setUpClass()
        transport = entry.CurrentWorldEntryTests()
        for first in range(7):
            for second in range(7):
                identity = (1, 217, 16383)[(first+second) % 3]
                wire = bytes.fromhex(subprocess.check_output(
                    [str(transport.binary), '--dump', str(identity), str(first), str(second)],
                    text=True, timeout=5).strip())
                plain = transport.decode(transport.vm(), wire)
                self.assertEqual(plain[:3], b'\x28\0\x2a')
                changed = bytearray(body)
                original = struct.unpack_from('<I', changed)[0]
                struct.pack_into('<I', changed, 0, (original & ~0x3fff) | identity)
                changed[13] = (changed[13] & 31) | (first << 5)
                changed[15] = (changed[15] & 31) | (second << 5)
                self.assertEqual(plain[3:-1], changed)
                self.assertEqual(n.consume_world_appearance(plain[3:-1]),
                                 ((0, 1, 2, 3), (first, second, 3, 0)))
        self.assertEqual(len(n.opens), 5)
        self.assertEqual(n.next_slot, 5)
        self.assertFalse(n.handles)
        self.assertEqual(n.u32(0), 0xffffffff)


if __name__ == '__main__':
    unittest.main()
