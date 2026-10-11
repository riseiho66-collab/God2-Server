"""Bounded native bank/table and cold-preload checks, not live/E2E acceptance."""
from collections import Counter
import hashlib
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab.current_world_resource_banks import (
    NativeWorldResourceBanks, BANK, BASE, BANK_STRIDE, CSV_SOURCES,
    MANAGER, RENDERER, SECOND_BANK)
from tools.strike_lab.current_indoor_resources import SCRATCH
from tools.strike_lab.current_role_doll_resources import STRIDE
from unicorn import UC_PROT_READ, UC_PROT_WRITE


def rows(native, name):
    lines = native.csv_sources[name].splitlines()
    start = int(lines[0].split(b',')[2])-1
    return [line.split(b',') for line in lines[start:] if line]


class WorldBankLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.n = NativeWorldResourceBanks()

    def test_original_constructors_and_bindings(self):
        n = self.n
        self.assertEqual(n.active_bank, -1)
        for index, pointer in enumerate((BANK, SECOND_BANK)):
            self.assertEqual(n.bank_state(index), {
                'pointer': pointer, 'next_slot': 0, 'saved_slot': 0,
                'area': 0, 'scene': 0, 'segment': 0, 'used': 0})
        self.assertEqual(n.bank_visits.count(0x60810), 1)
        self.assertEqual(n.bank_visits.count(0x608d0), 2)
        self.assertEqual(n.bank_visits.count(0x637b0), 2)
        self.assertEqual(n.handles, {})

    def test_zero_scene_is_initial_miss_then_hit(self):
        n = self.n
        self.assertEqual(n.select_scene(0, 0), 0)
        self.assertEqual(n.active_bank, 0)
        self.assertEqual(n.select_scene(0, 0), 1)
        self.assertEqual(n.active_bank, 0)
        self.assertEqual(n.bank_visits.count(0x28880), 1)

    def test_rotation_hit_and_eviction_bind_actual_renderer(self):
        n = self.n
        for area, scene, hit, bank in ((2, 15, 0, 0), (2, 0, 0, 1),
                                       (2, 15, 1, 0), (3, 1, 0, 1),
                                       (2, 0, 0, 0)):
            self.assertEqual(n.select_scene(area, scene), hit)
            self.assertEqual(n.active_bank, bank)
            state = n.bank_state(bank)
            self.assertEqual((state['area'], state['scene']), (area, scene))
            self.assertEqual(n.u32(RENDERER), state['pointer'])
            self.assertEqual(n.u32(RENDERER+12), state['pointer'])
        self.assertEqual(n.bank_visits.count(0x28880), 4)
        self.assertEqual(n.bank_visits.count(0x1fdf0), 5)

    def test_checkpoint_restores_each_native_allocator_and_slot(self):
        n = self.n
        initial_checkpoints = n.bank_visits.count(0x288e0)
        for bank, pointer in enumerate((BANK, SECOND_BANK)):
            self.assertNotEqual(n.call(0x28740, 128+bank, this=pointer+0x2a2800), 0)
            # Explicit preloaded-slot input, not a claim of executed ROM loads.
            n.vm.mem_write(MANAGER+0x121fc+bank*BANK_STRIDE,
                           struct.pack('<H', 7+bank))
        n.checkpoint()
        baseline = [n.bank_state(i) for i in (0, 1)]
        for bank, pointer in enumerate((BANK, SECOND_BANK)):
            n.call(0x28740, 321, this=pointer+0x2a2800)
            n.vm.mem_write(MANAGER+0x121fc+bank*BANK_STRIDE, struct.pack('<H', 19))
            self.assertEqual(n.bank_state(bank)['used'], baseline[bank]['used']+321)
            self.assertEqual(n.select_scene(2, 15+bank), 0)
            self.assertEqual(n.active_bank, bank)
            after = n.bank_state(bank)
            self.assertEqual(after['used'], baseline[bank]['used'])
            self.assertEqual(after['next_slot'], 7+bank)
            self.assertEqual(after['saved_slot'], 7+bank)
        self.assertEqual(n.bank_visits.count(0x288e0)-initial_checkpoints, 2)

    def test_selector_bounds_fail_before_native_execution(self):
        n = self.n
        before = list(n.bank_visits)
        for value in (-1, 65536, True, 1.5, '2', None):
            with self.assertRaises(ValueError):
                n.select_scene(value, 0)
            with self.assertRaises(ValueError):
                n.select_scene(0, value)
            with self.assertRaises(ValueError):
                n.bank_state(value)
        self.assertEqual(n.bank_visits, before)


class WorldBankTableTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.n = NativeWorldResourceBanks()
        cls.before_visits = Counter(cls.n.bank_visits)
        cls.result = cls.n.reload_character_tables()
        cls.reload_visits = Counter(cls.n.bank_visits)-cls.before_visits

    def test_full_original_loaders_and_read_only_files(self):
        n = self.n
        self.assertEqual(self.result, 1)
        for rva in (0x63bf0, 0x51f20, 0x15a47e, 0x63260, 0x63f40, 0x552c0):
            self.assertEqual(self.reload_visits[rva], 2)
        self.assertEqual(self.reload_visits[0x15a6a6], 1836)
        character_catalogs = ('data2/patch/drvdoll.csv', 'data2/patch/herodoll.csv',
                              'data2/patch/drv.csv', 'data/patch/goddoll.csv')
        for path in character_catalogs:
            self.assertEqual(n.csv_attempts.count((path+'z', b'rb')), 2)
            self.assertEqual(n.csv_attempts.count((path, b'rt')), 2)
        self.assertEqual({path.rstrip('z') for path, _ in n.csv_attempts},
                         set(character_catalogs))
        self.assertTrue(set(character_catalogs) < set(CSV_SOURCES))
        self.assertEqual(n.handles, {})
        self.assertNotIn(0x61ad0, n.bank_visits)

    def test_accessory_rows_match_exact_source(self):
        n = self.n
        source = rows(n, 'data2/patch/drvdoll.csv')
        self.assertEqual(len(source), 120)
        scale = struct.unpack('<f', n.vm.mem_read(0x570cbc, 4))[0]
        for bank in (0, 1):
            hero = MANAGER+0x682e0+bank*BANK_STRIDE
            self.assertEqual(struct.unpack('<H', n.vm.mem_read(hero+0x24f70, 2))[0], 120)
            records = n.u32(hero+0x24f74)
            for index, row in enumerate(source):
                ptr = records+136*index
                self.assertEqual(bytes(n.vm.mem_read(ptr, 4)),
                                 struct.pack('<2H', int(row[1] or b'0'), 65535))
                self.assertEqual(bytes(n.vm.mem_read(ptr+4, 4)),
                                 struct.pack('<f', int(row[3] or b'0')*scale))
                self.assertEqual(n.string(ptr+8), row[4])

    def test_all_hero_records_and_original_hash_lookup(self):
        n = self.n
        source = rows(n, 'data2/patch/herodoll.csv')
        self.assertEqual(len(source), 918)
        for bank in (0, 1):
            table = MANAGER+0x682e0+bank*BANK_STRIDE+0x12d78
            self.assertEqual(n.u32(table+0x121f0), 918)
            records, index = n.u32(table+0x121ec), n.u32(table+0x121f4)
            for ordinal, row in enumerate(source):
                ptr = records+ordinal*44
                self.assertEqual(n.string(ptr), row[3].lower())
                self.assertEqual(bytes(n.vm.mem_read(ptr+30, 2)), b'\xff\xff')
                key = (row[0]+row[1]).lower()
                self.assertEqual(n.string(ptr+32), key)
                self.assertEqual(n.vm.mem_read(ptr+42, 1)[0], int(row[5]))
                n.vm.mem_write(SCRATCH, key+b'\0')
                self.assertEqual(n.call(0x15a662, SCRATCH, SCRATCH+512, this=index), 1)
                self.assertEqual(n.u32(SCRATCH+512), ptr)

    def test_drv_rows_match_source_not_header_text(self):
        n = self.n
        source = rows(n, 'data2/patch/drv.csv')
        self.assertEqual(len(source), 92)
        for bank in (0, 1):
            hero = MANAGER+0x682e0+bank*BANK_STRIDE
            self.assertEqual(struct.unpack('<H', n.vm.mem_read(hero+0x121f6, 2))[0], 92)
            for ordinal, row in enumerate(source):
                ptr = hero+0x121f8+ordinal*32
                self.assertEqual(n.string(ptr), row[1])
                self.assertEqual(bytes(n.vm.mem_read(ptr+16, 2)), b'\xff\xff')
                for column, offset in ((2, 18), (3, 30), (4, 22), (5, 24), (6, 26), (7, 28)):
                    self.assertEqual(struct.unpack('<H', n.vm.mem_read(ptr+offset, 2))[0],
                                     int(row[column]))

    def test_goddoll_source_names_and_empty_cells(self):
        n = self.n
        source = rows(n, 'data/patch/goddoll.csv')
        expected = {}
        for row in source:
            gender = int(row[0][1:])
            component = {b'h': 0, b'b': 1, b'w': 2, b's': 3}[row[1][:1]]
            ordinal = int(row[1][1:])
            for side in ((0, 1) if gender == 0 else (gender-1,)):
                expected[side, component, ordinal] = row[3]
        self.assertGreater(len(expected), 0)
        for bank in (0, 1):
            table = MANAGER+0x682e0+bank*BANK_STRIDE+0x24f78
            for side in range(2):
                for component in range(4):
                    for ordinal in range(60):
                        ptr = table+0x121ec+((side*4+component)*60+ordinal)*262
                        self.assertEqual(bytes(n.vm.mem_read(ptr, 2)), b'\xff\xff')
                        self.assertEqual(n.string(ptr+2), expected.get((side, component, ordinal), b''))


class WorldBankColdPreloadTests(unittest.TestCase):
    WORLD = 0x08000000
    NPC_POINTER = SCRATCH+0x8000
    # Exact sources and decoded hashes from initial-npc-preload-assets-20260919.md.
    SOURCES = (
        ('data2/rom/npc/npc2401.romz', 10852, 23139,
         '4e728a03487842cd09334603dff50e7f52eef3e7c89401597866048db0123e02',
         'd35c29b93dde80c499feafd4fb46e2a609544eed1f6cc5db4891cfff05c4b512'),
        ('data2/rom/npc/npc2721.romz', 231827, 330378,
         '0c854a40de383269f6dde53cfc87a94d6d27b0cf590357cb6221ca4837110eda',
         '4977df017039bc671199962032d041fc6f3e97d655b3ea7ec546d43801688cae'),
        ('data2/rom/npc/npc2643.romz', 40978, 56146,
         'ef4625d222b9dc3e0cf182fedfc72ffc4d70e69f4c716c8796d4ecbc973fdc08',
         '92cb6316d08ce79b496bd7deb0f2aacc78fc8afc918e6872f95fbfc28bba7f1d'),
    )

    @classmethod
    def snapshot(cls):
        n = cls.n
        return {
            'bank_visits': Counter(n.bank_visits),
            'native_visits': Counter(n.native_visits),
            'opens': tuple(n.opens), 'parser_inputs': tuple(n.parser_inputs),
            'csv_attempts': tuple(n.csv_attempts), 'csv_reads': tuple(n.csv_reads),
            'tick_calls': tuple(n.tick_calls), 'handles': dict(n.handles),
            'active_bank': n.active_bank,
            'banks': tuple(n.bank_state(i) for i in (0, 1)),
            'slots': tuple(bytes(n.vm.mem_read(bank, 512*STRIDE))
                           for bank in (BANK, SECOND_BANK)),
            'catalogs': tuple(bytes(n.vm.mem_read(
                MANAGER+bank*BANK_STRIDE+offset+0x244e0, 4+350*76))
                for bank in (0, 1) for offset in (0x128c8, 0x3d5d4)),
            'progress': bytes(n.vm.mem_read(cls.WORLD+0xa7f2f64, 12)),
            'last_tick': n.u32(cls.WORLD+0x15aad388),
        }

    @classmethod
    def setUpClass(cls):
        cls.n = n = NativeWorldResourceBanks()
        for offset in (0xa7f2f64, 0x15aad388):
            n.vm.mem_map((cls.WORLD+offset) & ~4095, 4096,
                         UC_PROT_READ | UC_PROT_WRITE)
        n.call(0x607d0, 2, this=cls.WORLD)
        # Fixed clock fixture deliberately excludes the timed progress renderer.
        n.tick_count = 0
        n.vm.mem_write(cls.NPC_POINTER, bytes.fromhex('0f020015028f'))
        cls.before = cls.snapshot()
        cls.cold_result = n.call(0x61ad0, 2, 15, cls.NPC_POINTER, 0,
                                 cls.WORLD, this=MANAGER)
        cls.cold = cls.snapshot()
        cls.hit_result = n.call(0x61ad0, 2, 15, cls.NPC_POINTER, 0,
                                cls.WORLD, this=MANAGER)
        cls.hit = cls.snapshot()

    def test_cold_native_calls_and_two_fixed_clock_progress_increments(self):
        before, cold = self.before, self.cold
        self.assertEqual(self.cold_result, 1)
        self.assertEqual(before['active_bank'], -1)
        self.assertEqual(cold['active_bank'], 0)
        visits = cold['bank_visits']-before['bank_visits']
        for rva, count in ((0x61ad0, 1), (0x619d0, 1), (0x60b80, 1),
                           (0x60b10, 1), (0x616a0, 1), (0x60c60, 1),
                           (0x5e850, 4), (0x5f0e0, 3), (0x5eec0, 3),
                           (0x606d0, 2), (0x288e0, 2), (0x60731, 0)):
            with self.subTest(rva=hex(rva)):
                self.assertEqual(visits[rva], count)
        native = cold['native_visits']-before['native_visits']
        for rva in (0x29820, 0x1ec0, 0x2a1d0):
            self.assertEqual(native[rva], 3)
        self.assertEqual(cold['tick_calls'][len(before['tick_calls']):], (0, 0))
        self.assertEqual(self.n.tick_count, 0)
        self.assertEqual(struct.unpack('<H2xII', before['progress']), (2, 0, 0))
        self.assertEqual(struct.unpack('<H2xII', cold['progress']), (2, 2, 0))
        self.assertEqual((before['last_tick'], cold['last_tick']), (0, 0))

    def test_exact_sources_native_decoded_inputs_and_populated_slots(self):
        n = self.n
        names = tuple(source[0] for source in self.SOURCES)
        self.assertEqual(self.cold['opens'][len(self.before['opens']):], (
            'data2/patch/herodoll.csv', 'data2/patch/herodoll.csv',
            'data2/patch/drv.csv', 'data2/patch/drv.csv',
            'data/patch/goddoll.csv', 'data/patch/goddoll.csv',
            'data2/patch/eny.csv', 'data2/patch/eny.csv',
            'data2/patch/npc.csv', 'data2/patch/npc.csv', *names))
        self.assertEqual(self.cold['parser_inputs'][len(self.before['parser_inputs']):],
                         tuple((source[0], slot, source[2])
                               for slot, source in enumerate(self.SOURCES)))
        expected_slots = ((2401, 8, 4, 8), (2421, 8, 85, 16), (2643, 7, 12, 8))
        for slot, (path, raw_size, plain_size, raw_sha, plain_sha) in enumerate(self.SOURCES):
            with self.subTest(path=path):
                self.assertEqual(len(n.files[path]), raw_size)
                self.assertEqual(len(n.decoded[path]), plain_size)
                self.assertEqual(hashlib.sha256(n.files[path]).hexdigest(), raw_sha)
                self.assertEqual(hashlib.sha256(n.decoded[path]).hexdigest(), plain_sha)
                self.assertEqual(struct.unpack_from('<I', self.before['slots'][0],
                                                   slot*STRIDE)[0], 0xffffffff)
                self.assertEqual(tuple(n.u32(BANK+slot*STRIDE+offset)
                                       for offset in (0, 4, 0x88, 0x108c)),
                                 expected_slots[slot])
        self.assertEqual(self.cold['slots'][0][3*STRIDE:],
                         self.before['slots'][0][3*STRIDE:])
        self.assertEqual(self.cold['slots'][1], self.before['slots'][1])
        self.assertEqual(self.cold['banks'][0]['next_slot'], 3)
        self.assertEqual(self.cold['banks'][0]['saved_slot'], 0)
        self.assertEqual((self.cold['banks'][0]['area'], self.cold['banks'][0]['scene']),
                         (2, 15))
        self.assertGreater(self.cold['banks'][0]['used'], self.before['banks'][0]['used'])
        self.assertEqual(self.cold['banks'][1], self.before['banks'][1])
        self.assertEqual(self.cold['handles'], {})

    def test_all_eny_npc_paths_native_category_lookups_and_cache_slots_in_both_banks(self):
        n = self.n
        loaded = {318: 0, 20: 1, 237: 2}
        for name, offset, count in (('eny', 0x128c8, 215), ('npc', 0x3d5d4, 319)):
            path = 'data2/patch/'+name+'.csv'
            source = rows(n, path)
            self.assertEqual(len(source), count)
            attempts = Counter(self.cold['csv_attempts'])-Counter(self.before['csv_attempts'])
            self.assertEqual(attempts[path+'z', b'rb'], 2)
            self.assertEqual(attempts[path, b'rt'], 2)
            for bank in (0, 1):
                table = MANAGER+bank*BANK_STRIDE+offset
                self.assertEqual(n.u32(table+0x244e0), count)
                self.assertEqual(n.u32(table+0x2accc), 1 if name == 'eny' else 10)
                ordinals = Counter()
                for record, row in enumerate(source):
                    with self.subTest(catalog=name, bank=bank, record=record):
                        self.assertTrue(row[2])
                        self.assertEqual(row[0], str(record).encode() if name == 'eny' else b'')
                        category = int(row[6])
                        # Let the original category lookup resolve the record pointer.
                        pointer = n.call(0x5f130, category, ordinals[category], this=table)
                        ordinals[category] += 1
                        self.assertEqual(pointer, table+0x244e4+76*record)
                        self.assertEqual(n.string(pointer), row[1])
                        slot = loaded.get(record, 0xffff) if name == 'npc' and bank == 0 else 0xffff
                        self.assertEqual(struct.unpack('<H', n.vm.mem_read(pointer+64, 2))[0], slot)
                for category in range(n.u32(table+0x2accc)):
                    self.assertEqual(n.call(0x5f130, category, ordinals[category], this=table), 0)

    def test_documented_default_and_scene_category_records(self):
        n = self.n
        for bank in (0, 1):
            table = MANAGER+bank*BANK_STRIDE+0x3d5d4
            for slot, (category, ordinal, record) in enumerate(((9, 0, 318),
                                                               (0, 20, 20), (2, 142, 237))):
                pointer = n.call(0x5f130, category, ordinal, this=table)
                self.assertEqual(pointer, table+0x244e4+76*record)
                expected_path = self.SOURCES[slot][0][:-1].replace('/', '\\')[:-4]+'.ROM'
                self.assertEqual(n.string(pointer), expected_path.encode())
                self.assertEqual(struct.unpack('<H', n.vm.mem_read(pointer+64, 2))[0],
                                 slot if bank == 0 else 0xffff)

    def test_same_scene_hit_has_no_additional_loads_decodes_or_progress(self):
        self.assertEqual(self.hit_result, 1)
        self.assertEqual(self.hit['bank_visits']-self.cold['bank_visits'], Counter({
            0x61ad0: 1, 0x619d0: 1, 0x1fdf0: 1, 0x2d9e0: 1, 0x289b0: 1}))
        for key in self.cold:
            if key != 'bank_visits':
                with self.subTest(state=key):
                    self.assertEqual(self.hit[key], self.cold[key])
        self.assertEqual(self.hit['handles'], {})
        self.assertEqual(self.hit['bank_visits'][0x60731], 0)


if __name__ == '__main__':
    unittest.main()
