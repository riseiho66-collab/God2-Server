"""Native world-relative actor placement; no copied actor or forced UI branch."""
import json
from pathlib import Path
import struct
import unittest

from tools.strike_lab.current_embedded_world import (
    NativeEmbeddedWorld, EMBEDDED_ACTOR, ACTOR_EXTENT, RING, WORLD, BASE,
    ROLE_POOL, NPC_POOLS)
from tools.strike_lab.current_world_actor import ACTOR, MESSAGES
from tools.strike_lab.current_indoor_resources import SP, SCRATCH
from unicorn.x86_const import (UC_X86_REG_EIP, UC_X86_REG_ESP, UC_X86_REG_EAX,
                              UC_X86_REG_EBP, UC_X86_REG_ECX)

ROOT = Path(__file__).resolve().parents[2]


class EmbeddedWorldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.n = n = NativeEmbeddedWorld()
        # Input stimulus only: this does not prove original starting-state values.
        cls.body = bytes.fromhex(json.loads((ROOT/'tests/fixtures/recovered-world-entry.json')
                                            .read_text())['body_hex'])
        cls.adjacent_before = (bytes(n.vm.mem_read(EMBEDDED_ACTOR-16, 16)),
                               bytes(n.vm.mem_read(NPC_POOLS[0], 16)))
        cls.indoor = n.enter_scene(cls.body)
        cls.adjacent_after = (bytes(n.vm.mem_read(EMBEDDED_ACTOR-16, 16)),
                              bytes(n.vm.mem_read(NPC_POOLS[0], 16)))
        cls.before = struct.unpack('<ii', n.vm.mem_read(WORLD+0x21c, 8))
        cls.camera = n.finish_scene()

    def test_actor_is_initialized_in_place_without_touching_neighbors(self):
        n = self.n
        self.assertEqual(n.actor_address, EMBEDDED_ACTOR)
        self.assertEqual(n.actor_storage_size, ACTOR_EXTENT)
        self.assertEqual(self.adjacent_before, self.adjacent_after)
        self.assertFalse(any(a <= ACTOR <= b for a, b, _ in n.vm.mem_regions()))
        self.assertEqual(n.u32(EMBEDDED_ACTOR), int.from_bytes(self.body[:4], 'little') & 0x3fff)
        self.assertEqual(bytes(n.vm.mem_read(EMBEDDED_ACTOR+0x10, 1)), b'\x02')
        self.assertEqual(n.u32(EMBEDDED_ACTOR+0x14), 15)
        self.assertEqual(struct.unpack('<H', n.vm.mem_read(EMBEDDED_ACTOR+0x18, 2))[0], 2)
        self.assertEqual(n.string(EMBEDDED_ACTOR+0xb7), b'BoundHero')
        for pool in NPC_POOLS:
            self.assertTrue(all(n.u32(pool+0x70+0x1d8*i) == 0xffffffff for i in range(256)))
        self.assertTrue(all(n.u32(ROLE_POOL+0x18+0x268*i) == 0xffffffff for i in range(128)))

    def test_actual_branch_and_camera_ring_message_tail(self):
        n = self.n
        self.assertEqual(self.before, (1240, 540))
        self.assertEqual(self.camera, (840, 240))
        self.assertEqual(struct.unpack('<ii', n.vm.mem_read(self.indoor+0x6c, 8)), self.camera)
        self.assertIn(0x100831, n.tail_visits)
        self.assertNotIn(0x10083a, n.tail_visits)
        for rva in (0x1008b1, 0x103640, 0x103680, 0x1036b0, 0x100912, 0x15ab0):
            self.assertEqual(n.tail_visits.count(rva), 1)
        self.assertEqual(bytes(n.vm.mem_read(RING, 3)), b'\x01\x00\x01')
        self.assertEqual(bytes(n.vm.mem_read(RING+4, 8)), bytes(n.vm.mem_read(WORLD+0x224, 8)))
        message_id = n.u32(BASE+0x19b948) & 65535
        count = struct.unpack('<h', n.vm.mem_read(MESSAGES+0xb2c6c, 2))[0]
        self.assertTrue(1 <= message_id <= count)
        self.assertEqual(n.u32(BASE+0x1b8acc),
                         n.u32(n.u32(MESSAGES+0xb2c68)+4*(message_id-1)))
        self.assertEqual(n.music_resolver_calls, [(2, 2, 15, 0)])
        self.assertEqual(n.music_results, [0])
        self.assertEqual(n.vm.reg_read(UC_X86_REG_EIP), BASE+0x100930)
        self.assertEqual(n.u32(0), 0xffffffff)
        self.assertFalse(n.handles)

    def test_one_shot_and_scene_prerequisite(self):
        with self.assertRaises(ValueError):
            self.n.finish_scene()
        unloaded = NativeEmbeddedWorld.__new__(NativeEmbeddedWorld)
        unloaded.scene_loaded = False
        unloaded.viewport_started = False
        with self.assertRaises(ValueError):
            unloaded.finish_scene()
        self.assertFalse(unloaded.viewport_started)

    def test_original_scene_caller_passes_embedded_actor(self):
        n = self.n
        previous = bytes(n.vm.mem_read(WORLD+0x230, 1))
        try:
            with n.music_preserve_caller():
                n.vm.reg_write(UC_X86_REG_EBP, WORLD)
                n.vm.reg_write(UC_X86_REG_EAX, 1)
                n.vm.reg_write(UC_X86_REG_ESP, SP)
                n._slice(0x65424, 0x65435)
                sp = n.vm.reg_read(UC_X86_REG_ESP)
                self.assertEqual(sp, SP-8)
                self.assertEqual(n.vm.reg_read(UC_X86_REG_ECX), WORLD)
                self.assertEqual(struct.unpack('<II', n.vm.mem_read(sp, 8)),
                                 (EMBEDDED_ACTOR, 1))
        finally:
            n.vm.mem_write(WORLD+0x230, previous)

    def test_message_slot_is_original_writable_data_not_code(self):
        import pefile
        image = bytes(self.n.vm.mem_read(BASE, 4096))
        pe = pefile.PE(data=image, fast_load=True)
        section = next(s for s in pe.sections if s.VirtualAddress <= 0x1b8acc
                       < s.VirtualAddress+max(s.Misc_VirtualSize, s.SizeOfRawData))
        self.assertEqual(section.Name.rstrip(b'\0'), b'.data')
        self.assertTrue(section.Characteristics & 0x80000000)
        self.assertFalse(section.Characteristics & 0x20000000)
        self.assertEqual(next(p for a, b, p in self.n.vm.mem_regions()
                              if a <= BASE+0x1b8acc <= b), 3)

    def test_ring_retains_initial_point_then_wraps_without_overwrite(self):
        n = self.n
        saved = bytes(n.vm.mem_read(RING, 4+40*8))
        visits = list(n.tail_visits)
        points = [(0x12348000, 0x7fff), (0x8000ffff, 0xffff8001)]
        points += [(i, i+1) for i in range(37)]
        try:
            with n.music_preserve_caller():
                n.call(0x103700, RING, SCRATCH, this=WORLD)
                self.assertEqual(bytes(n.vm.mem_read(SCRATCH, 8)),
                                 bytes(n.vm.mem_read(WORLD+0x224, 8)))
                self.assertEqual(bytes(n.vm.mem_read(RING, 3)), b'\x00\x01\x01')
                for point in points:
                    n.vm.mem_write(SCRATCH, struct.pack('<II', *point))
                    self.assertEqual(n.call(0x1036b0, RING, SCRATCH, this=WORLD), 1)
                self.assertEqual(bytes(n.vm.mem_read(RING, 3)), b'\x27\x01\x00')
                full = bytes(n.vm.mem_read(RING, 4+40*8))
                self.assertEqual(n.call(0x1036b0, RING, SCRATCH, this=WORLD), 0)
                self.assertEqual(bytes(n.vm.mem_read(RING, 4+40*8)), full)
                for point in points:
                    n.call(0x103700, RING, SCRATCH, this=WORLD)
                    expected = tuple(struct.unpack('<h', struct.pack('<H', v & 65535))[0]
                                     for v in point)
                    self.assertEqual(struct.unpack('<ii', n.vm.mem_read(SCRATCH, 8)), expected)
                self.assertEqual(bytes(n.vm.mem_read(RING, 3)), bytes(3))
                n.vm.mem_write(SCRATCH, b'\xa5'*8)
                n.call(0x103700, RING, SCRATCH, this=WORLD)
                self.assertEqual(bytes(n.vm.mem_read(SCRATCH, 8)), b'\xa5'*8)
        finally:
            n.vm.mem_write(RING, saved)
            n.tail_visits[:] = visits


if __name__ == '__main__':
    unittest.main()
