"""Bounded CAN data import tests; original-code execution is qualified separately."""
from contextlib import redirect_stderr, redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab import world_scenes as scenes
from tools.strike_lab.world_atlas import SOURCE, parse_catalog
from tools.strike_lab.omega_assets import decode_csvz


def record(path=b'indoor\\groceryl.hmd', tag=1):
    return bytes([tag]) + path + b'\0' * (63 - len(path))


def can(records, indices):
    return (b'CAN v1.0' + struct.pack('<I', len(records)) + b''.join(records)
            + struct.pack('<I', len(indices))
            + b''.join(struct.pack('<H', index) for index in indices))


def csvz(raw):
    return (b'\x05\x16' + struct.pack('<I', len(raw)) + b'\0'
            + b''.join(b'\xff' + raw[i:i + 8] for i in range(0, len(raw), 8)))


def catalog_row(scene=0, mdt=b'Island01\\Island01.mdt'):
    return b','.join([b'region', b'island', b'map', b'2', b'0', str(scene).encode(),
                      b'0', b'0', b'music.wav', b'fight.wav', mdt, b'1', b'1', b'1'])


class CanBoundsTests(unittest.TestCase):
    def test_raw_bytes_tags_padding_and_repeated_indices_are_retained(self):
        raw_record = bytes([255]) + b'room.hmd\0' + b'X' * 54
        raw = can([raw_record], [0, 0])
        result = scenes.parse_can(raw)
        self.assertEqual(result['scene_file_indices'], [0, 0])
        entry = result['files'][0]
        self.assertEqual(entry['raw_tag'], 255)
        self.assertEqual(entry['asset_path'], 'room.hmd')
        self.assertEqual(bytes.fromhex(entry['raw_record_hex']), raw_record)
        self.assertEqual(entry['source_record_sha256'], hashlib.sha256(raw_record).hexdigest())
        self.assertNotIn('kind', entry)

    def test_counts_accept_zero_and_the_inclusive_256_boundary(self):
        self.assertEqual(scenes.parse_can(can([], []))['files'], [])
        result = scenes.parse_can(can([record(b'a' * 62)] * 256, [255] * 256))
        self.assertEqual((result['file_count'], result['scene_count']), (256, 256))
        self.assertEqual(result['scene_file_indices'], [255] * 256)

    def test_bad_headers_counts_lengths_indices_and_unterminated_paths(self):
        good = can([record()], [0])
        invalid = [good[:i] for i in range(len(good))]
        invalid += [b'CAN v2.0' + good[8:], good + b'\0',
                    b'CAN v1.0' + struct.pack('<I', 257) + b'\0' * 4,
                    b'CAN v1.0' + struct.pack('<I', 0xffffffff) + b'\0' * 4,
                    can([record()], [])[:-4] + struct.pack('<I', 257),
                    can([record()], [])[:-4] + struct.pack('<I', 0xffffffff),
                    can([record()], [1]), can([record()], [65535]), can([], [0]),
                    can([b'\0' + b'x' * 63], []),
                    b'CAN v1.0' + b'\0' * scenes.MAX_CAN_SIZE]
        for index, raw in enumerate(invalid):
            with self.subTest(case=index), self.assertRaises(ValueError):
                scenes.parse_can(raw)

    def test_paths_reject_traversal_roots_streams_and_windows_aliases(self):
        for path in (b'', b'../bad', b'..\\bad', b'indoor\\..\\bad',
                     b'C:\\bad', b'C:bad', b'/bad', b'\\bad', b'\\\\host\\bad',
                     b'bad:stream', b'.. \\bad', b'indoor\\.. \\bad',
                     b'room.hmd.', b'room.hmd ', b'CON.hmd', b'NUL', b'COM1.x',
                     b'a\\\\b', b'a/./b', b'a/', b'bad?.hmd', b'bad*.hmd',
                     b'bad\nhmd', b'bad\xff.hmd'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                scenes.parse_can(can([record(path)], []))


class SceneImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.client = self.work / 'client'
        source = self.client / SOURCE
        source.parent.mkdir(parents=True)
        rows = [catalog_row(), catalog_row(15, b'Other\\wrong.mdt')]
        source.write_bytes(csvz(b'Map_City_Coordniate,2\n' + b'\n'.join(rows) + b'\n'))
        self.base = self.client / 'Data2/map/Island01'
        self.base.mkdir(parents=True)
        self.can_path = self.base / 'Island01.can'

    def test_base_catalog_path_asset_variants_and_raw_provenance(self):
        raw = can([record(b'indoor\\room.hmd', 2), record(b'missing.hmd')], [1, 0, 0])
        self.can_path.write_bytes(raw)
        room = self.base / 'indoor/room.hmd'
        room.parent.mkdir()
        room.write_bytes(b'plain asset')
        room.with_suffix('.hmdZ').write_bytes(csvz(b'compressed asset'))
        result = scenes.build_scenes(self.client)
        area = result['areas'][0]
        self.assertEqual(bytes.fromhex(area['source']['raw_hex']), raw)
        self.assertEqual(area['source']['sha256'], hashlib.sha256(raw).hexdigest())
        self.assertEqual(area['scene_file_indices'], [1, 0, 0])
        self.assertEqual([s['file_index'] for s in result['scenes']], [1, 0, 0])
        self.assertEqual(result['scenes'][0]['asset_variants'], [])
        variants = result['scenes'][1]['asset_variants']
        self.assertEqual([v['path'] for v in variants],
                         ['Data2/map/Island01/indoor/room.hmd',
                          'Data2/map/Island01/indoor/room.hmdZ'])
        self.assertEqual([v['decoded_sha256'] for v in variants],
                         [hashlib.sha256(b'plain asset').hexdigest(),
                          hashlib.sha256(b'compressed asset').hexdigest()])
        self.assertEqual(result['counts']['areas_total'], 1)
        self.assertEqual(result['counts']['files_with_assets'], 1)
        self.assertEqual(result['counts']['scenes_with_assets'], 2)
        self.assertFalse(any('kind' in s for s in result['scenes']))

    def test_missing_can_and_oversized_can(self):
        result = scenes.build_scenes(self.client)
        self.assertEqual(result['counts']['areas_with_can'], 0)
        self.assertEqual(result['scenes'], [])
        self.assertIsNone(result['areas'][0]['source'])
        self.can_path.write_bytes(b'X' * (scenes.MAX_CAN_SIZE + 1))
        with self.assertRaisesRegex(ValueError, 'length bound'):
            scenes.build_scenes(self.client)

    def test_catalog_traversal_is_rejected(self):
        (self.client / SOURCE).write_bytes(csvz(
            b'Map_City_Coordniate,1\n' + catalog_row(mdt=b'..\\escape.mdt') + b'\n'))
        with self.assertRaises(ValueError):
            scenes.build_scenes(self.client)

    def _symlink(self, link, target):
        try:
            link.symlink_to(target)
        except OSError as error:
            self.skipTest('OS does not permit test symlinks: ' + str(error))

    def test_can_source_symlink_escape(self):
        outside = self.work / 'outside.can'
        outside.write_bytes(can([], []))
        self._symlink(self.can_path, outside)
        with self.assertRaisesRegex(ValueError, 'escapes'):
            scenes.build_scenes(self.client)

    def test_scene_asset_symlink_cannot_escape_area_directory(self):
        outside = self.client / 'outside.hmd'
        outside.write_bytes(b'asset in a different subtree')
        self.can_path.write_bytes(can([record(b'room.hmd')], [0]))
        self._symlink(self.base / 'room.hmdZ', outside)
        with self.assertRaisesRegex(ValueError, 'escapes'):
            scenes.build_scenes(self.client)

    def test_cli_is_deterministic_and_rejects_output_inside_client(self):
        self.can_path.write_bytes(can([record(b'missing.hmd')], [0]))
        output = self.work / 'output/scenes.json'
        args = ['--client', str(self.client), '--output', str(output)]
        with redirect_stdout(io.StringIO()):
            scenes.main(args)
            first = output.read_bytes()
            scenes.main(args)
        self.assertEqual(first, output.read_bytes())
        self.assertNotIn(b'\r', first)
        self.assertEqual(json.loads(first), scenes.build_scenes(self.client))
        before = self.can_path.read_bytes()
        with patch.object(scenes, 'build_scenes') as build, redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as error:
                scenes.main(['--client', str(self.client), '--output', str(self.can_path)])
            self.assertEqual(error.exception.code, 2)
            build.assert_not_called()
        self.assertEqual(self.can_path.read_bytes(), before)

    def test_cli_rejects_output_directory_symlink_into_client(self):
        link = self.work / 'output'
        try:
            link.symlink_to(self.client, target_is_directory=True)
        except OSError as error:
            self.skipTest('OS does not permit test symlinks: ' + str(error))
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            scenes.main(['--client', str(self.client), '--output', str(link / 'scenes.json')])
        self.assertFalse((self.client / 'scenes.json').exists())


@unittest.skipUnless((ROOT.parent / 'God2' / SOURCE).is_file(), 'Current client assets unavailable')
class CurrentSceneDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = ROOT.parent / 'God2'
        cls.result = scenes.build_scenes(cls.client)

    def test_actual_area_two_scene_fifteen_uses_can_record_twelve(self):
        result = self.result
        self.assertEqual(result['source']['sha256'],
                         '70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731')
        row = next(s for s in result['scenes'] if (s['area'], s['scene']) == (2, 15))
        area = next(a for a in result['areas'] if a['area'] == 2)
        self.assertEqual(row['file_index'], 12)
        self.assertEqual(row['raw_tag'], 1)
        self.assertEqual(row['source_sha256'],
                         'f2b9ca9dc4dcebcd1c1c40de14ea63f1b2061993f644c49b9c7baca9ce2d2f97')
        self.assertEqual(bytes.fromhex(area['files'][12]['raw_path_hex']), b'indoor\\groceryl.hmd')
        self.assertEqual(row['asset_relative'], 'Data2/map/Island01/indoor/groceryl.hmd')
        self.assertEqual([v['path'] for v in row['asset_variants']],
                         ['Data2/map/Island01/indoor/groceryl.hmdZ'])
        catalog = parse_catalog(decode_csvz((self.client / SOURCE).read_bytes()))
        self.assertFalse(any((r['area'], r['scene']) == (2, 15) for r in catalog))

    def test_current_counts_preserve_rows_without_runtime_or_placement_claims(self):
        self.assertEqual(self.result['counts'], {
            'areas_total': 14, 'areas_with_can': 14, 'files_total': 303,
            'files_with_assets': 287, 'scenes_total': 613, 'scenes_imported': 613,
            'scenes_with_assets': 585, 'scenes_server_loaded': 0,
            'scenes_runtime_validated': 0, 'npc_placements_imported': 0,
            'monster_spawns_imported': 0, 'teleports_imported': 0})
        for row in self.result['scenes']:
            self.assertIsNone(row['spawn'])
            self.assertIsNone(row['collision'])
            self.assertNotIn('kind', row)
        for area in self.result['areas']:
            raw = bytes.fromhex(area['source']['raw_hex'])
            self.assertEqual(area['source']['sha256'], hashlib.sha256(raw).hexdigest())
            for row in (s for s in self.result['scenes'] if s['area'] == area['area']):
                self.assertEqual(struct.unpack_from('<H', raw, row['source_offset'])[0], row['file_index'])
        self.assertEqual(self.result, scenes.build_scenes(self.client))


if __name__ == '__main__':
    unittest.main()
