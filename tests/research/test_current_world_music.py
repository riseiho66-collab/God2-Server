"""Current original music reader/resolver and real absent-device branch only."""
import hashlib
import json
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab.current_world_music import (
    NativeWorldMusic, NativeWorldMusicMixin, music_source, PLAIN_SHA,
    SLOTS, PATHS, COUNT, CURRENT, PLAYING, OVERRIDE, SOUND_OWNER,
    WORLD, ACTOR, MESSAGES, BASE, SP, STACK)
from tools.strike_lab.current_world_viewport import (
    NativeWorldViewport, NPC_POOLS, ROLE_POOL, OPTIONAL_POOL)
from tools.strike_lab.current_world_resource_banks import CWD
from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ECX,
                              UC_X86_REG_EDX, UC_X86_REG_ESI, UC_X86_REG_EDI,
                              UC_X86_REG_EBP, UC_X86_REG_ESP, UC_X86_REG_EIP,
                              UC_X86_REG_EFLAGS)

REGISTERS = (UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ECX, UC_X86_REG_EDX,
             UC_X86_REG_ESI, UC_X86_REG_EDI, UC_X86_REG_EBP, UC_X86_REG_ESP,
             UC_X86_REG_EIP, UC_X86_REG_EFLAGS)


def caller(native):
    return (tuple(native.vm.reg_read(reg) for reg in REGISTERS),
            bytes(native.vm.mem_read(STACK, 0x80000)))


class CurrentWorldMusicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = n = NativeWorldMusic(absent_device_fixture=True)
        cls.loader_visits = tuple(n.music_visits)
        cls.cold_memory = bytes(n.vm.mem_read(SLOTS, PLAYING+4-SLOTS))
        cls.sound_memory = bytes(n.vm.mem_read(n.music_sound, 0x15360))

    def setUp(self):
        n = self.native
        n.vm.mem_write(SLOTS, self.cold_memory)
        n.vm.mem_write(n.music_sound, self.sound_memory)
        n.vm.mem_write(CURRENT, b'\xff\xff')
        n.vm.mem_write(OVERRIDE, bytes(4))
        n.music_visits.clear()
        n.music_selections.clear()
        n.music_resolver_calls.clear()
        n.music_playback_calls.clear()
        n.music_results.clear()

    def test_complete_native_reader_and_exact_current_sources(self):
        n = self.native
        self.assertFalse(n.music_catalog_reused)
        self.assertEqual(n.music_native_decoded_sha, PLAIN_SHA)
        self.assertEqual(n.music_source_span, (2462531, 2483449))
        self.assertEqual(n.music_callocs, [(144, 0x1a4)])
        for rva, count in ((0x565ec, 1), (0x59a80, 1), (0x51a90, 144),
                           (0x51be0, 144), (0xf7380, 1), (0x4d9f0, 1)):
            self.assertEqual(self.loader_visits.count(rva), count)
        n._verify_music_catalog()
        self.assertFalse(n.handles)
        self.assertEqual(n.u32(0), 0xffffffff)
        self.assertEqual(n.u32(SOUND_OWNER), n.music_sound)
        self.assertEqual(n.music_state()['paths'], tuple(
            b'\\data2\\music\\Fight\\att0'+str(i).encode()+b'.wav' for i in range(1, 5)))
        self.assertEqual(n.music_state()['slots'], (-1,)*30)

    def test_initial_exact_selection_and_native_playback_failure(self):
        n = self.native
        before = caller(n)
        slot = n.resolve_music(2, 2, 15)
        self.assertEqual(caller(n), before)
        self.assertEqual(slot, 4)
        self.assertEqual(n.music_resolver_calls, [(2, 2, 15, 0)])
        self.assertEqual(n.music_selections, [(0xf77aa, b'data2\\Music\\city\\city_I1.wav')])
        self.assertEqual(n.music_visits[:4], [0xf76e0, 0x59d80, 0x59e00, 0xf7400])
        opens = list(n.opens)
        state = n.play_music_without_device(slot)
        self.assertEqual(caller(n), before)
        self.assertEqual((state['current'], state['playing'], state['device']), (-1, 0, 0))
        self.assertEqual(state['slots'][slot], 0)
        self.assertEqual(n.music_results, [0])
        self.assertIn(0x4dd90, n.music_visits)
        self.assertIn(0x4e660, n.music_visits)
        self.assertNotIn(0x4ec90, n.music_visits)
        self.assertNotIn(0x4e080, n.music_visits)
        self.assertEqual(n.string(BASE+0x1b92c0), CWD+b'\\data2\\Music\\city\\city_I1.wav')
        self.assertEqual(n.opens, opens)
        self.assertEqual(n.u32(0), 0xffffffff)
        # A failed attempt caches the available sound slot, not playback success.
        attempts = n.music_visits.count(0x4dd90)
        n.play_music_without_device(slot)
        self.assertEqual(n.music_visits.count(0x4dd90), attempts)
        self.assertEqual(n.music_results, [0, 0])

    def test_source_selected_variants_use_native_direct_lookup(self):
        n = self.native
        selectors = ((1, 0), (1, 12), (2, 0), (2, 2), (2, 4), (2, 43), (16, 9))
        for area, scene in selectors:
            row = next(row for row in n.music_rows if (row['area'], row['scene']) == (area, scene))
            for combat, column, ret in ((False, 8, 0xf7788), (True, 9, 0xf7710)):
                with self.subTest(area=area, scene=scene, combat=combat):
                    slot = n.resolve_music(area, row['kind'], scene, combat=combat)
                    expected = bytes.fromhex(row['raw_fields_hex'][column])
                    self.assertEqual(n.music_selections[-1], (ret, expected))
                    self.assertEqual(n.music_state()['paths'][slot], expected)
        count = struct.unpack('<h', n.vm.mem_read(COUNT, 2))[0]
        first = n.resolve_music(2, 0, 4)
        self.assertEqual(n.resolve_music(2, 3, 4), first)
        self.assertEqual(struct.unpack('<h', n.vm.mem_read(COUNT, 2))[0], count)

    def test_native_fallback_order_including_combat_kind(self):
        n = self.native
        cases = [
            (2, 2, 15, False, 0xf77aa, b'data2\\Music\\city\\city_I1.wav'),
            (2, 3, 15, False, 0xf77aa, b'data2\\Music\\city\\city_I1.wav'),
            (2, 3, 15, True, 0xf7735, b'data\\Music\\Fight\\att_e.wav'),
            (2, 2, 15, True, 0xf7758, b'data\\Music\\Fight\\att_e.wav'),
            # Explicit missing-scene probes cover the original global fallback.
            (12, 2, 65535, False, 0xf77cd, b'data2\\Music\\city\\City_s01.wav'),
            (12, 2, 65535, True, 0xf7758, b'data\\Music\\Fight\\att_e.wav'),
        ]
        for area, kind, scene, combat, ret, expected in cases:
            with self.subTest(area=area, kind=kind, scene=scene, combat=combat):
                slot = n.resolve_music(area, kind, scene, combat=combat)
                self.assertEqual(n.music_selections[-1], (ret, expected))
                self.assertEqual(n.music_state()['paths'][slot], expected)

    def test_event_override_table_and_invalid_slot_gates(self):
        n = self.native
        slot = n.resolve_music(2, 2, 15)
        for event, expected in ((1, b'\\data2\\music\\XMas.wav'),
                                (2, b'\\data2\\music\\NewYear.wav')):
            with self.subTest(event=event):
                before = caller(n)
                state = n.play_music_without_device(slot, event=event)
                self.assertEqual(n.music_selections[-1], (0xf7551, expected))
                self.assertEqual((state['current'], state['playing']), (-1, 0))
                self.assertEqual(caller(n), before)
                self.assertEqual(n.u32(OVERRIDE), 0)
        n.play_music_without_device(-1)
        self.assertEqual(n.music_selections[-1], (0xf7551, b''))
        count = len(n.music_results)
        for invalid in (-2, 30, 32767):
            n.play_music_without_device(invalid)
        self.assertEqual(len(n.music_results), count)
        self.assertEqual(n.music_results, [0, 0, 0])

    def test_current_audio_files_and_literal_missing_paths(self):
        root = ROOT.parent/'God2'
        for relative, expected_size, sha in (
            ('Data2/Music/City/City_I1.wav', 1813818,
             '64860c40c510bdaabadf2d92ab44c425e732b4d4214fcd210d1bcbaa965c93d1'),
            ('Data2/Music/Field/field_i01.wav', 3426648,
             '4e79f25102fdf523f9cd7cb4e75ed12d87d22ed81872f55edb47581535d498b0'),
            ('Data2/Music/maze/MAZE_I01.WAV', 3274430,
             '77ba30ed95727ce93f6e7c3fb47fea0a7cebf3b7e7bf86a11add3a9c6dfff42e')):
            raw = (root/relative).read_bytes()
            self.assertEqual(len(raw), expected_size)
            self.assertEqual(hashlib.sha256(raw).hexdigest(), sha)
            self.assertEqual((raw[:4], raw[8:12]), (b'RIFF', b'WAVE'))
        for relative in ('Data/Music/Fight/att_e.wav', 'Data/Music/Fight/att_s.wav',
                         'Data2/Music/NewYear.wav'):
            self.assertFalse((root/relative).exists())

    def test_reject_changed_source_and_bad_inputs_without_native_work(self):
        n = self.native
        before = (caller(n), n.heap, tuple(n.music_visits), n.music_state())
        original = Path.read_bytes
        def changed(path):
            raw = original(path)
            return raw[:-1]+bytes([raw[-1] ^ 1]) if path.name.lower() == 'gamedata.csvz' else raw
        with patch.object(Path, 'read_bytes', changed):
            with self.assertRaisesRegex(ValueError, 'Pinned music catalog changed'):
                music_source()
        for args in ((True, 2, 15), (2, 4, 15), (2, 2, -1), (65536, 2, 15)):
            with self.assertRaises(ValueError):
                n.resolve_music(*args)
        with self.assertRaises(ValueError):
            n.resolve_music(2, 2, 15, combat=1)
        with self.assertRaises(ValueError):
            n.play_music_without_device(4, event=3)
        with self.assertRaises(ValueError):
            n.install_music(absent_device_fixture=False)
        with self.assertRaisesRegex(ValueError, 'already installed'):
            n.install_music(absent_device_fixture=True)
        self.assertEqual((caller(n), n.heap, tuple(n.music_visits), n.music_state()), before)

    def test_nonnull_device_fails_closed_and_restores_caller(self):
        n = self.native
        slot = n.resolve_music(2, 2, 15)
        before = caller(n)
        n.vm.mem_write(n.music_sound, struct.pack('<I', 0x30000000))
        try:
            with self.assertRaisesRegex(AssertionError, 'Live-device path'):
                n.play_music_without_device(slot)
            self.assertEqual(caller(n), before)
        finally:
            n.vm.mem_write(n.music_sound, bytes(4))


class MusicViewport(NativeWorldMusicMixin, NativeWorldViewport):
    pass


class CurrentWorldMusicCompositionTests(unittest.TestCase):
    def test_existing_viewport_catalog_and_exact_actor_caller(self):
        n = MusicViewport()
        records = n.catalog_records
        parser = bytes(n.vm.mem_read(MESSAGES+4, 6))
        before = caller(n)
        n.install_music(absent_device_fixture=True)
        self.assertEqual(caller(n), before)
        self.assertTrue(n.music_catalog_reused)
        self.assertEqual(n.music_records, records)
        self.assertEqual(n.music_callocs, [])
        self.assertEqual(bytes(n.vm.mem_read(MESSAGES+4, 6)), parser)
        # Existing current body is an input fixture only; no retired provenance
        # file is opened and no protocol/actor/resource function is stubbed.
        fixture = json.loads((ROOT/'tests/fixtures/recovered-world-entry.json').read_text())
        body = bytes.fromhex(fixture['body_hex'])
        indoor = n.enter_scene(body)
        self.assertEqual(tuple(n.vm.mem_read(ACTOR+0x10, 1)), (2,))
        self.assertEqual(n.u32(ACTOR+0x14), 15)
        self.assertEqual(struct.unpack('<H', n.vm.mem_read(ACTOR+0x18, 2))[0], 2)
        before = caller(n)
        n.music_visits.clear()
        self.assertEqual(struct.unpack('<ii', n.vm.mem_read(WORLD+0x21c, 8)), (1240, 540))
        with n.music_preserve_caller():
            n.vm.reg_write(UC_X86_REG_ESI, WORLD)
            n.vm.reg_write(UC_X86_REG_EDI, ACTOR)
            n.vm.reg_write(UC_X86_REG_ESP, SP)
            n._slice(0x10078f, 0x100831)
            self.assertEqual(n.vm.reg_read(UC_X86_REG_ESP), SP)
            self.assertEqual(n.vm.reg_read(UC_X86_REG_EIP), BASE+0x100831)
        state = n.music_state()
        self.assertEqual(caller(n), before)
        self.assertEqual(n.music_resolver_calls, [(2, 2, 15, 0)])
        self.assertEqual(n.music_playback_calls, [4])
        self.assertEqual(n.music_results, [0])
        self.assertEqual(state['paths'][4], b'data2\\Music\\city\\city_I1.wav')
        self.assertEqual((state['current'], state['playing'], state['device']), (-1, 0, 0))
        self.assertEqual(n.catalog_records, records)
        self.assertFalse(n.handles)
        self.assertEqual(n.u32(0), 0xffffffff)
        self.assertEqual(struct.unpack('<ii', n.vm.mem_read(WORLD+0x21c, 8)), (840, 240))
        self.assertEqual(struct.unpack('<ii', n.vm.mem_read(indoor+0x6c, 8)), (840, 240))
        for pool in NPC_POOLS:
            self.assertEqual(struct.unpack('<ii', n.vm.mem_read(pool+0x68, 8)), (840, 240))
        self.assertEqual(struct.unpack('<ii', n.vm.mem_read(ROLE_POOL+0x10, 8)), (840, 240))
        self.assertEqual(n.u32(OPTIONAL_POOL+0x3491a8), 0)
        self.assertEqual(n.viewport_visits.count(0x46520), 1)
        self.assertEqual(n.viewport_visits.count(0x103c70), 1)
        self.assertNotIn(0x1ac30, n.viewport_visits)
        # The standalone interval also leaves its caller and camera untouched.
        before = caller(n)
        camera_visits = list(n.viewport_visits)
        self.assertEqual(n.continue_music(), state)
        self.assertEqual(caller(n), before)
        self.assertEqual(n.viewport_visits, camera_visits)


if __name__ == '__main__':
    unittest.main()
