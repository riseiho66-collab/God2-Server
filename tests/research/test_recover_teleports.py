"""CLI evidence import and pinned native S2C61 scalar slices.

No sockets, client launch, shared build, renderer or resource-manager stubs.
Native tests enter named blocks directly; they do not prove a full transition.
"""
import hashlib
from contextlib import closing
import json
from pathlib import Path
import shutil
import sqlite3
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab import recover_teleports as teleports
import test_current_route_advertisement as routes
from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_EDI,
                               UC_X86_REG_ESI, UC_X86_REG_ESP)

ATLAS = ROOT / 'artifacts/world-atlas/current-scenes.json'
WORLD = 0x4000000


class RecoverTeleportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = teleports.build_teleports(teleports.CLASSIC, teleports.XJZ, ATLAS)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='god2-teleport-test-')
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.classic = self.work / 'classic'
        self.xjz = self.work / 'xjz'
        self.xjz.mkdir()
        for source in self.result['sources']:
            root, target = ((teleports.CLASSIC, self.classic) if source['corpus'] == 'classic'
                            else (teleports.XJZ, self.xjz))
            destination = target / source['file']
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / source['file'], destination)
        self.scenes = self.work / 'scenes.json'
        shutil.copyfile(ATLAS, self.scenes)
        # A tiny different-corpus database is enough for CLI failure tests.
        with closing(sqlite3.connect(self.xjz / 'xjz_evidence.sqlite')) as c:
            c.execute('CREATE TABLE teleport_flow_sample(sample_id INTEGER)')
            c.execute('CREATE TABLE transport_binding(binding_id INTEGER)')
            c.execute('CREATE TABLE transport_service_template('
                      'binding_kind TEXT, packet_evidence_boundary INTEGER)')
            c.commit()
        self.output = self.work / 'out/teleports.json'

    def cli(self, *extra, expected=0):
        result = subprocess.run([sys.executable, '-m', 'tools.strike_lab.recover_teleports',
            '--classic', str(self.classic), '--xjz', str(self.xjz),
            '--scenes', str(self.scenes), '--output', str(self.output), *extra],
            cwd=ROOT, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        if expected:
            self.assertNotIn('Traceback', result.stderr)
        return result

    def test_cli_repeat_is_byte_identical_and_keeps_derived_edges_out_of_runtime(self):
        self.cli()
        before = self.output.read_bytes()
        self.cli()
        self.assertEqual(before, self.output.read_bytes())
        self.assertNotIn(b'\r', before)
        data = json.loads(before)
        self.assertEqual(data['counts'], self.result['counts'])
        self.assertEqual(data['runtime_edges'], [])
        self.assertTrue(all(not r['runtime_eligible'] for r in data['edges']))
        self.assertEqual([r['id'] for r in data['edges'] if r['trigger']['evidence_status'] == 'Derived'], [3, 4])

    def test_cli_missing_source_and_database_do_not_replace_output(self):
        self.cli()
        before = self.output.read_bytes()
        (self.classic / teleports.ROUTES).unlink()
        self.cli(expected=2)
        self.assertEqual(before, self.output.read_bytes())
        self.cli('--classic', str(teleports.CLASSIC), '--xjz', str(self.work / 'missing'), expected=2)
        self.assertEqual(before, self.output.read_bytes())

    def test_cli_malformed_and_duplicate_json(self):
        for raw in ('{', '{"areas":[],"areas":[],"scenes":[]}',
                    '{"areas":NaN,"scenes":[]}'):
            with self.subTest(raw=raw):
                self.scenes.write_text(raw)
                self.cli(expected=2)
                self.assertFalse(self.output.exists())

    def test_cli_duplicate_scene_and_corrupt_can(self):
        for operation in ('duplicate', 'hash', 'selector'):
            document = json.loads(ATLAS.read_bytes())
            if operation == 'duplicate':
                document['scenes'].append(document['scenes'][0])
            elif operation == 'hash':
                document['areas'][0]['source']['sha256'] = '0' * 64
            else:
                document['scenes'][0]['file_index'] += 1
            with self.subTest(operation=operation):
                self.scenes.write_text(json.dumps(document))
                self.cli(expected=2)

    def test_cli_missing_scene_is_unresolved_not_remapped(self):
        document = json.loads(self.scenes.read_bytes())
        document['scenes'] = [r for r in document['scenes'] if (r['area'], r['scene']) != (15, 7)]
        self.scenes.write_text(json.dumps(document))
        self.cli()
        data = json.loads(self.output.read_bytes())
        edge = next(r for r in data['edges'] if r['id'] == 170015007)
        self.assertIsNone(edge['destination']['current_selector_match'])
        self.assertFalse(edge['runtime_eligible'])
        self.assertEqual(data['counts']['current_selector_pairs_present'], 4)

    def test_cli_duplicate_routes_candidates_and_gate_rejected(self):
        for relative, kind in ((teleports.ROUTES, 'route'), (teleports.CANDIDATES, 'candidate'),
                               (teleports.GATE, 'gate')):
            path = self.classic / relative
            raw = path.read_bytes()
            if kind == 'candidate':
                doc = json.loads(raw)
                doc['records'].append(doc['records'][0])
                doc['recordCount'] += 1
                changed = json.dumps(doc)
            elif kind == 'route':
                excerpt = self.result['edges'][0]['catalog_excerpt']
                changed = raw.decode().replace(excerpt, excerpt + ',\n' + excerpt)
            else:
                changed = raw.decode().replace('WHERE `portal_id` = 2', 'WHERE `portal_id` = 1')
            path.write_text(changed)
            with self.subTest(kind=kind):
                self.cli(expected=2)
            path.write_bytes(raw)

    def test_cli_hash_changed_migration_rejected_and_inputs_protected(self):
        relative = self.result['edges'][0]['provenance']['migration']
        path = self.classic / relative
        path.write_bytes(path.read_bytes() + b'\n')
        self.cli(expected=2)
        for output in (self.scenes, self.classic / 'new.json', self.xjz / 'new.json'):
            self.cli('--output', str(output), expected=2)

    def test_actual_source_counts_positions_and_atlas_match_are_separate(self):
        data = self.result
        self.assertEqual(data['counts'], {'retained_coordinate_edges': 5,
            'legacy_trigger_verified': 3, 'legacy_trigger_derived': 2,
            'current_selector_pairs_present': 5, 'unresolved_candidates': 68,
            'runtime_eligible_edges': 0})
        expected = {1: (4, 3, 252, 397, 4, 19, 28, 34),
                    2: (4, 19, 16, 20, 4, 3, 196, 139),
                    3: (2, 0, 284, 452, 2, 43, 52, 184),
                    4: (2, 43, 51, 185, 2, 0, 283, 453),
                    170015007: (15, 0, 249, 246, 15, 7, 48, 81)}
        for edge in data['edges']:
            values = tuple(edge[end][k] for end in ('source', 'destination') for k in ('area', 'scene', 'x', 'y'))
            self.assertEqual(values, expected[edge['id']])
            self.assertIsNone(edge['current_coordinate_transform'])
        self.assertTrue(data['edges'][2]['destination']['current_selector_match']['asset_relative'].endswith('/maze05/maze05.mdt'))
        self.assertEqual(data['xjz_audit']['teleport_flow_sample_count'], 0)
        self.assertEqual(data['xjz_audit']['transport_binding_count'], 255)
        self.assertEqual(sum(g['count'] for g in data['xjz_audit']['service_templates']), 255)
        self.assertEqual({g['packet_evidence_boundary'] for g in data['xjz_audit']['service_templates']}, {0})
        self.assertEqual(sum(r['retained_record']['kind'] == 'clientResourceRoomLinkCandidate'
                             for r in data['unresolved_candidates']), 65)
        self.assertEqual(data, json.loads((ROOT / 'artifacts/world-atlas/teleports.json').read_bytes()))


class CurrentPortalScalarTests(unittest.TestCase):
    vm = routes.CurrentRouteAdvertisementTests.vm
    run_to = routes.CurrentRouteAdvertisementTests.run_to

    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT / 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin').read_bytes()
        if hashlib.sha256(cls.image).hexdigest() != teleports.IMAGE_SHA:
            raise AssertionError('Pinned current image changed')
        cls.data = teleports.build_teleports(teleports.CLASSIC, teleports.XJZ, ATLAS)

    def prepared(self, body):
        vm = self.vm()
        for page in {WORLD, (WORLD + 0x15396850) & ~4095, (WORLD + 0xa7e05dc) & ~4095}:
            vm.mem_map(page, 4096)
        # Packet ends at an unmapped page boundary, including both opaque bytes.
        page = 0x3800000
        vm.mem_map(page, 4096)
        pointer = page + 4096 - len(body)
        vm.mem_write(pointer, body)
        vm.mem_write(routes.SP + 0x40, struct.pack('<I', pointer))
        vm.mem_write(WORLD + 0x15396850, struct.pack('<IH', 0xffffffff, 0xffff))
        vm.reg_write(UC_X86_REG_ESP, routes.SP)
        vm.reg_write(UC_X86_REG_ECX, WORLD)
        return vm, pointer

    def test_original_dispatch_and_size_identify_s2c61_consumer(self):
        self.assertEqual(struct.unpack_from('<I', self.image, 0x6b5d4 + 4 * 0x61)[0], 0x469345)
        size_fn = struct.unpack_from('<I', self.image, 0x1324 + 4 * 0x61)[0] - routes.BASE
        vm = self.vm()
        vm.mem_write(routes.SP, struct.pack('<I', routes.STACK + 0x3ff0))
        vm.reg_write(UC_X86_REG_ESP, routes.SP)
        self.run_to(vm, size_fn, routes.STACK + 0x3ff0 - routes.BASE)
        self.assertEqual(vm.reg_read(UC_X86_REG_EAX), 9)
        self.assertEqual(self.image[0x69358:0x6935d], bytes.fromhex('e863290000'))

    def test_retained_frames_native_selector_mode_and_position_slices(self):
        for edge in self.data['edges']:
            with self.subTest(edge=edge['id']):
                frame = bytes.fromhex(edge['retained_transition']['decoded_frame_hex'])
                body = frame[3:-1]
                self.assertEqual(len(body), 8)
                self.assertEqual(sum(v + 60 for v in frame[:-1]) & 255, frame[-1])
                vm, pointer = self.prepared(body)
                self.run_to(vm, 0x6bcdc, 0x6bd4a)
                dst = edge['destination']
                self.assertEqual(struct.unpack('<IH', vm.mem_read(WORLD + 0x15396850, 6)), (dst['scene'], dst['area']))
                self.assertEqual(bytes(vm.mem_read(WORLD + 0x1539684c, 1)), bytes([dst['position_mode']]))
                self.assertEqual(bytes(vm.mem_read(pointer, 8)), body)
                self.run_to(vm, 0x6bf6c, 0x6bf9e)
                self.assertEqual(struct.unpack('<III', vm.mem_read(WORLD + 0x224, 12)),
                                 (dst['x'], dst['y'], dst['position_mode']))

    def test_native_same_map_flag_clears_bit16_before_later_position_consumption(self):
        # The current handler has a special same-map path. Scalar compatibility
        # is not enough to claim unconditional, complete transition equivalence.
        body = struct.pack('<HHI', 7 << 6 | 15, 0x0f0f, (81 << 17) | (16384 << 2))
        vm, pointer = self.prepared(body)
        vm.mem_write(WORLD + 0x15396850, struct.pack('<IH', 7, 15))
        self.run_to(vm, 0x6bcdc, 0x6bd4a)
        self.assertEqual(struct.unpack('<I', vm.mem_read(pointer + 4, 4))[0], 81 << 17)
        self.assertEqual(struct.unpack('<I', vm.mem_read(routes.SP + 0x18, 4))[0], 0)

    def test_native_scalar_boundaries_all_modes_without_coordinate_transform(self):
        for x, y, mode in ((0, 0, 0), (32767, 32767, 1), (1, 32767, 2), (32767, 1, 3)):
            vm, pointer = self.prepared(struct.pack('<HHI', 2, 0xabcd, (y << 17) | (x << 2) | mode))
            vm.reg_write(UC_X86_REG_ESI, WORLD)
            vm.reg_write(UC_X86_REG_EDI, pointer)
            self.run_to(vm, 0x6bf6c, 0x6bf9e)
            self.assertEqual(struct.unpack('<III', vm.mem_read(WORLD + 0x224, 12)), (x, y, mode))


if __name__ == '__main__':
    unittest.main()
