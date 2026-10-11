"""Original common actor tail with native tables/resources; scene is not joined."""
from pathlib import Path
import json
import struct
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab.current_world_actor import (
    NativeWorldActor, ACTOR, WORLD, CAT, PETDRV, UI, MANAGER, MESSAGES, OWNER_POISON,
    NPC_GROUPS_OFFSET, NPC_AREA_STRIDE, NPC_GROUP_STRIDE)
from tools.strike_lab.current_indoor_resources import SCRATCH
from tools.strike_lab.current_appearance_resources import AppearanceResources
import test_current_world_entry as entry


def u32(raw, offset):
    return struct.unpack_from('<I', raw, offset)[0]


class CurrentWorldActorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        open_file = Path.open
        retired = (Path('C:/God2Evidence/classic-20260820').resolve(),
                   (ROOT/'artifacts/legacy-evidence').resolve())

        def current_only(path, *args, **kwargs):
            resolved = path.resolve()
            if (any(resolved == root or root in resolved.parents for root in retired)
                    or resolved.name.lower().startswith(('xjz-server-cpp-clean-',
                                                         'god2-classic-server-formal-handoff-'))):
                raise AssertionError('Retired evidence is forbidden in current actor tests')
            return open_file(path, *args, **kwargs)

        guard = patch.object(Path, 'open', current_only)
        guard.start()
        cls.addClassCleanup(guard.stop)
        cls.appearance = AppearanceResources()
        cls.native = NativeWorldActor(cls.appearance)
        cls.body = bytes.fromhex(json.loads(
            (ROOT/'tests/fixtures/recovered-world-entry.json').read_text())['body_hex'])
        entry.CurrentWorldEntryTests.setUpClass()
        cls.transport = entry.CurrentWorldEntryTests()

    def test_retired_evidence_open_is_rejected_before_io(self):
        for path in (Path('C:/God2Evidence/classic-20260820/forbidden.sql'),
                     ROOT/'artifacts/legacy-evidence/xjz-20260820/forbidden.json',
                     ROOT/'God2-Classic-Server-Formal-Handoff-20260820-020345.zip'):
            with self.assertRaisesRegex(AssertionError, 'Retired evidence'):
                path.read_bytes()

    def test_all_cat_fields_and_native_localization(self):
        n = self.native
        self.assertEqual(n.u32(CAT+0x121e8), 9)
        self.assertEqual(n.cat_before_localization[:44], bytes(44))
        for row in n.cat_rows:
            ordinal = int(row[1])
            original = n.cat_before_localization[ordinal*44:(ordinal+1)*44]
            for column, offset in ((3, 0), (4, 8), (5, 16)):
                self.assertEqual(original[offset:offset+8].split(b'\0')[0],
                                 row[column].encode('latin1'))
            self.assertEqual(struct.unpack_from('<5I', original, 24),
                             tuple(int(row[col]) for col in range(6, 11)))
            localized = bytes(n.vm.mem_read(CAT+0x121ec+ordinal*44, 44))
            label_index = (ordinal-1)//2
            message_id = struct.unpack('<H', n.vm.mem_read(0x58ab40+2*label_index, 2))[0]
            pointer = n.u32(n.program_pointers+4*(message_id-1))
            self.assertEqual(n.u32(0x5b5668+4*label_index), pointer)
            label = n.string(pointer)
            self.assertEqual(localized[8:8+len(label)+1], label+b'\0')
            self.assertEqual(localized[:8], original[:8])
            self.assertEqual(localized[16:], original[16:])

    def test_all_program_messages_loaded_by_original_row_parser(self):
        n = self.native
        self.assertEqual(struct.unpack('<H', n.vm.mem_read(MESSAGES+0xb2c6c, 2))[0], 1080)
        seen = set()
        for row in n.program_rows:
            fields = [bytes.fromhex(field) for field in row['fields_hex']]
            identity = int(fields[0])
            self.assertNotIn(identity, seen)
            seen.add(identity)
            pointer = n.u32(n.program_pointers+4*(identity-1))
            self.assertNotEqual(pointer, 0)
            self.assertEqual(n.string(pointer), fields[1] if len(fields) > 1 else b'')
        self.assertEqual(seen, set(range(1, 1081)))

    def test_petdrv_binding_and_all_source_offsets(self):
        n = self.native
        self.assertEqual(n.u32(PETDRV+4), MANAGER+0x682e0+0x121f8)
        self.assertEqual(n.u32(PETDRV+8), n.accessory_records)
        self.assertEqual(n.u32(PETDRV+12), 119)
        for index, row in enumerate(self.appearance.driver_rows):
            self.assertEqual(n.call(0x64280, index, this=PETDRV) & 0xffff, int(row[4]) & 0xffff)
        self.assertEqual(int(self.appearance.driver_rows[27][4]), 30)

    def test_all_npc_resource_groups_loaded_and_queried_by_original_code(self):
        n = self.native
        self.assertEqual(len(n.npc_group_rows), 451)
        self.assertEqual(len(n.npc_group_codes), 251)
        self.assertEqual(sum(map(len, n.npc_group_codes.values())), 1509)
        for area in range(17):
            base = MESSAGES+NPC_GROUPS_OFFSET+area*NPC_AREA_STRIDE
            scenes = [scene for a, scene in n.npc_group_codes if a == area]
            self.assertEqual(n.vm.mem_read(base, 1)[0], len(scenes))
            for ordinal, scene in enumerate(scenes):
                pointer = n.call(0x5aa70, area, scene, this=MESSAGES)
                self.assertEqual(pointer, base+1+ordinal*NPC_GROUP_STRIDE)
                record = bytes(n.vm.mem_read(pointer, NPC_GROUP_STRIDE))
                codes = n.npc_group_codes[area, scene]
                pairs = bytes(part for code in codes
                              for part in ((code//1000) & 255, (code % 1000) & 255))
                self.assertEqual(record[:2], bytes((scene, len(codes))))
                self.assertEqual(record[2:2+len(pairs)], pairs)
                self.assertEqual(record[2+len(pairs):], bytes(140-len(pairs)))
            for scene in (130, 255, 256, 65535):
                self.assertEqual(n.call(0x5aa70, area, scene, this=MESSAGES), 0)
        for area in (17, 18, 255):
            self.assertEqual(n.call(0x5aa70, area, 15, this=MESSAGES), 0)

    def test_initial_scene_has_real_npc_resource_group_not_empty_table(self):
        n = self.native
        self.assertEqual(n.npc_group_codes[2, 15], [21, 2143])
        pointer = n.call(0x5aa70, 2, 15, this=MESSAGES)
        self.assertNotEqual(pointer, 0)
        self.assertEqual(bytes(n.vm.mem_read(pointer, 6)), bytes((15, 2, 0, 21, 2, 143)))

    def test_town_guide_scene_native_group_contains_appearance20(self):
        n=self.native
        codes=n.npc_group_codes[2,4]
        self.assertEqual(len(codes),46)
        self.assertEqual(codes.count(20),1)
        pointer=n.call(0x5aa70,2,4,this=MESSAGES)
        self.assertNotEqual(pointer,0)
        record=bytes(n.vm.mem_read(pointer,NPC_GROUP_STRIDE))
        self.assertEqual(record[:2],bytes((4,46)))
        index=codes.index(20)
        self.assertEqual(record[2+2*index:4+2*index],bytes((0,20)))

    def test_complete_original_enemy_loader_and_all_visible_group_records(self):
        n = self.native
        self.assertEqual(len(n.enemy_loaded_groups), 97)
        self.assertEqual(sum(len(rows) for _, _, _, rows in n.enemy_loaded_groups), 7815)
        self.assertEqual(len(n.enemy_groups), 96)
        self.assertEqual(sum(map(len, n.enemy_groups.values())), 7791)
        self.assertEqual(len(n.enemy_calloc_calls), 17)
        self.assertEqual(n.enemy_calloc_calls[0][:2], (26, 7815))
        self.assertEqual(n.enemy_stream_position, len(n.enemy_stream))
        self.assertEqual(n.u32(MESSAGES+4), 0)
        records_base = n.u32(MESSAGES+0xd2e24)
        self.assertEqual(records_base, n.enemy_calloc_calls[0][2])
        special_count = 0
        for area in range(17):
            groups = [(scene, rows) for (a, scene), rows in n.enemy_groups.items() if a == area]
            self.assertEqual(n.u32(MESSAGES+0xd2d9c+area*8), len(groups))
            table = n.u32(MESSAGES+0xd2da0+area*8)
            for index, (scene, rows) in enumerate(groups):
                pointer = records_base+26*n.enemy_group_offsets[area, scene]
                group = n.call(0x5a000, area, scene, this=MESSAGES)
                self.assertEqual(group, table+index*12)
                self.assertEqual(struct.unpack('<3I', n.vm.mem_read(group, 12)),
                                 (scene, len(rows), pointer))
                for row_index, row in enumerate(rows):
                    record = bytes(n.vm.mem_read(pointer+26*row_index, 26))
                    self.assertEqual(record[0], ((int(row[2]) << 4) & 255)
                                     | (int(row[3]) & 1) | ((int(row[5]) & 7) << 1))
                    self.assertEqual(record[1], int(row[4]) & 255)
                    self.assertEqual(record[2:18].split(b'\0')[0], row[1].encode('latin1'))
                    components = bytearray(8)
                    if 5001 <= int(row[4]) <= 5003 and int(row[3]) & 1:
                        special_count += 1
                        category = int(row[4])-5001
                        for column, offset in ((6, 4), (7, 2), (8, 0), (9, 6)):
                            component = row[column]
                            components[offset] = category | (int(component[2]) << 4)
                            components[offset+1] = (int(component[0]) << 5) | (int(component[3:]) & 31)
                    self.assertEqual(record[18:26], components)
                for ordinal in range(1, len(rows) + 1):
                    self.assertEqual(n.call(0x5a0a0, area, scene, ordinal, this=MESSAGES),
                                     pointer+26*(ordinal-1))
                for ordinal in (0, len(rows)+1):
                    self.assertEqual(n.call(0x5a0a0, area, scene, ordinal, this=MESSAGES), 0)
        self.assertEqual(special_count, 3109)
        visible = [r for r in n.enemy_identity_records if r['lookup_visible']]
        self.assertEqual(len(visible), 7791)
        for row in visible:
            pointer = records_base + 26 * row['source_record_index']
            self.assertEqual(n.string(pointer + 2), bytes.fromhex(row['name_bytes_hex']))
        self.assertEqual(n.call(0x5a000, 2, 15, this=MESSAGES), 0)
        for area in (17, 18, 255):
            self.assertEqual(n.call(0x5a000, area, 0, this=MESSAGES), 0)

    def test_enemy_source_bounds_fail_before_native_allocations(self):
        source = self.native.game_data
        variants = [
            source.replace(b'EnyNameTotal,7815', b'EnyNameTotal,-1', 1),
            source.replace(b'EnyNameIsland_Area,1,2', b'EnyNameIsland_Area,17,2', 1),
            source.replace(b'EnyNameAreaId_Idx,0,21', b'EnyNameAreaId_Idx,0,7816', 1),
            source.replace(b'EnyNameAreaId_Idx,0,21', b'EnyNameAreaId_Idx,65536,21', 1),
            source.replace(b'EnyNameTotal,7815', b'EnyNameTotal,7815\0', 1),
            source[:source.index(b'SpecialEnyInfo,')],
        ]
        for damaged in variants:
            with self.subTest(length=len(damaged)):
                self.assertNotEqual(damaged, source)
                # No VM or allocator is supplied: failure must precede execution.
                probe = NativeWorldActor.__new__(NativeWorldActor)
                probe.game_data = damaged
                with self.assertRaises(ValueError):
                    probe._load_enemy_groups()

    def test_scene_group_queries_are_joined_to_original_actor_progress_setup(self):
        n = self.native
        for area, scene in ((2, 15), (2, 0), (7, 13), (9, 0), (16, 9)):
            body = bytearray(self.body)
            struct.pack_into('<H', body, 24, area | (scene << 6))
            visits = len(n.visits)
            n.initialize(bytes(body))
            count = len(n.npc_group_codes.get((area, scene), []))
            count += len(n.enemy_groups.get((area, scene), []))
            self.assertEqual(struct.unpack('<H', n.vm.mem_read(WORLD+0xa7f2f64, 2))[0],
                             count*8//7)
            self.assertEqual(n.visits[visits:visits+4],
                             [0x681cf, 0x5aa70, 0x5a000, 0x607d0])

    def assert_actor(self, actor, body, name, *, mount_slot=4):
        n = self.native
        word0, word1 = struct.unpack_from('<2I', body)
        position = u32(body, 28)
        self.assertEqual(struct.unpack_from('<4I', actor),
                         (word0 & 0x3fff, 1, (position >> 2) & 0x7fff, position >> 17))
        self.assertEqual(actor[0x10], position & 3)
        self.assertEqual(u32(actor, 0x14), (u32(body, 24) & 65535) >> 6)
        self.assertEqual(struct.unpack_from('<H', actor, 0x18)[0], body[24] & 63)
        self.assertEqual(u32(actor, 0x24), ((word1 & 7)-1) & 7)
        self.assertEqual(u32(actor, 0x28), body[13] >> 5)
        self.assertEqual(u32(actor, 0x2c), 26)
        self.assertEqual(u32(actor, 0x30), mount_slot)
        self.assertEqual(u32(actor, 0x40), 30)
        self.assertEqual(u32(actor, 0x50), 0xffffffff)
        self.assertEqual(actor[0xb7:0xb7+len(name)+1], name+b'\0')
        self.assertEqual(u32(actor, 0x124), 999)
        self.assertEqual(u32(actor, 0xa8), 0)
        self.assertEqual(actor[0xac:0xae], bytes(2))
        selector = (word1 >> 11) & 31
        normalized = selector-1 if 1 <= selector <= 8 else 0
        self.assertEqual(struct.unpack_from('<H', actor, 0x90)[0], normalized)
        self.assertEqual(actor[0x4590], selector)
        label = n.string(CAT+0x121ec+44*selector+8)
        self.assertEqual(actor[0xae:0xae+len(label)+1], label+b'\0')
        self.assertEqual(u32(actor, 0x4504), OWNER_POISON+0xa924d7c)
        self.assertEqual(actor[0x15e:0x165], b'\x01\xff'+bytes(5))
        self.assertEqual(actor[0x168:0x4028], bytes(0x3ec0))
        self.assertEqual(u32(actor, 0x4544), 0xffffffff)
        self.assertEqual(actor[0x4548:0x4584], bytes(60))
        self.assertEqual(actor[0x4584:0x4590], body[12:24])
        self.assertEqual(actor[0x4694], (word0 >> 14) & 3)
        self.assertEqual(actor[0x4695], body[34])
        self.assertEqual(actor[0x4698], body[35])
        self.assertEqual(bytes(n.vm.mem_read(ACTOR+0x4699, 0x6000-0x4699)),
                         b'\xa5'*(0x6000-0x4699))
        self.assertEqual(n.u32(SCRATCH+0x4000), word0 >> 31)
        self.assertEqual(n.u32(SCRATCH+0x4004), 0xa5a5a5a5)
        self.assertEqual(n.u32(WORLD+0xa7f2f3c), word0 >> 31)
        self.assertFalse(n.handles)
        self.assertEqual(n.u32(0), 0xffffffff)

    def test_native_actor_reset_uses_real_resources_and_clears_ui_arrays(self):
        n = self.native
        for offset, size in ((0x85604, 4), (0x8560c, 1200), (0x866a8, 40)):
            n.vm.mem_write(UI+offset-4, b'\xa5'*(size+8))
        visits = len(n.visits)
        self.assert_actor(n.initialize(self.body), self.body, b'BoundHero')
        self.assertEqual(n.visits[visits:],
                         [0x681cf, 0x5aa70, 0x5a000, 0x607d0,
                          0x68315, 0x61270, 0x64280, 0x68120, 0x97fe0])
        self.assertEqual(struct.unpack('<H', n.vm.mem_read(WORLD+0xa7f2f64, 2))[0], 2)
        for offset, size in ((0x85604, 4), (0x8560c, 1200), (0x866a8, 40)):
            self.assertEqual(bytes(n.vm.mem_read(UI+offset, size)), bytes(size))
            self.assertEqual(n.u32(UI+offset-4), 0xa5a5a5a5)
            self.assertEqual(n.u32(UI+offset+size), 0xa5a5a5a5)
        self.assertEqual(n.next_slot, 5)
        self.assertEqual(len(n.opens), 5)

    def test_cpp_wire_original_decoder_to_native_actor_repeated_profiles(self):
        n, transport = self.native, self.transport
        for first in range(7):
            for second in range(7):
                identity = (1, 217, 16383)[(first+second) % 3]
                x, y = ((17, 13), (18, 12), (0, 0), (32767, 32767))[(first+second) % 4]
                wire = bytes.fromhex(subprocess.check_output(
                    [str(transport.binary), '--dump', str(identity), str(first),
                     str(second), str(x), str(y)], text=True, timeout=5).strip())
                plain = transport.decode(transport.vm(), wire)
                self.assertEqual(plain[:3], b'\x28\0\x2a')
                name = ('Hero'+str(identity)).encode()
                self.assert_actor(n.initialize(plain[3:-1], name=name), plain[3:-1], name)
        self.assertEqual(n.next_slot, 5)
        self.assertEqual(len(n.opens), 5)

    def test_bounded_inputs_fail_before_native_execution(self):
        n = self.native
        malformed = [self.body[:length] for length in range(36)] + [self.body+b'\0']
        for offset, value in ((6, 0), (2, 1), (12, 2), (13, 0xe0), (15, 0xe0),
                              (24, 0), (24, 17), (32, 1)):
            changed = bytearray(self.body)
            changed[offset] = value
            malformed.append(bytes(changed))
        before = (list(n.visits), list(n.opens), n.next_slot)
        for body in malformed:
            with self.assertRaises(ValueError):
                n.initialize(body)
        for name in (b'', b'a'*21, b'a\0b', b'\xff'):
            with self.assertRaises(ValueError):
                n.initialize(self.body, name=name)
        for flags in (-1, 1 << 32):
            with self.assertRaises(ValueError):
                n.initialize(self.body, prior_flags=flags)
        self.assertEqual((n.visits, n.opens, n.next_slot), before)


if __name__ == '__main__':
    unittest.main()
