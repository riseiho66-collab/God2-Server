"""DB4/5 packed journal value -> original Mission_data description consumer.

Offline x86 execution, no patched code or stubs. C9550 runs through its real
list-selection helper and stops at the text-renderer entry; click handling runs
the C92EA selection slice. Neither claims rendering or quest progression.
"""
import hashlib
from pathlib import Path
import struct
import subprocess
import sys
import unittest

import test_current_quest_sync as quest
from unicorn import UcError, UC_HOOK_MEM_READ, UC_PROT_READ
from unicorn.x86_const import (
    UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_ESI,
    UC_X86_REG_ESP,
)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab.recover_quests import build_catalog
from tools.strike_lab.omega_assets import decode_csvz
from tools.strike_lab.current_quest_rule_frontier_20260927 import MissionNative

BASE = quest.routes.BASE
UI, RESOURCE = quest.UI, quest.RESOURCE
ROWS = RESOURCE + 0x1000
ARENA, ARENA_SIZE = 0x3a00000, 0x100000
SOURCE_SHA = '659c8f38ffd9c34107969b449afd16488665a08970110910c9aed8448a0bb716'
DECODED_SHA = 'f57cb8d1a9426e2f797c9cdfea32beb07642415ae3e2bb30a8909373a1c0a5f0'


class CurrentQuestRecordTests(unittest.TestCase):
    run_to = quest.CurrentQuestSyncTests.run_to
    dispatch = quest.CurrentQuestSyncTests.dispatch

    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT / 'artifacts/capture_work/host-20260918-1430/output/'
                     'native-master-01-stable.bin').read_bytes()
        if hashlib.sha256(cls.image).hexdigest() != quest.routes.IMAGE_SHA:
            raise AssertionError('Pinned native image changed')
        catalog = build_catalog(ROOT.parent / 'God2')
        table = catalog['tables']['missions']
        if (table['source_sha256'], table['decoded_sha256']) != (SOURCE_SHA, DECODED_SHA):
            raise AssertionError('Pinned Mission_data changed')
        if catalog['validation']['structural_issues']:
            raise AssertionError('Malformed source catalog')
        cls.missions = catalog['quests']
        cls.counts = [q['step_field'] for q in cls.missions]
        plain = decode_csvz((ROOT.parent / 'God2' /
                             'Data2/Patch/Comm/Mission_data.csvZ').read_bytes())
        # Execute the actual source loader first. Raw source bytes differ from
        # the native token output for two long descriptions; preserve both.
        native = MissionNative(cls.image, plain.splitlines(keepends=True)[3:])
        cls.loaded = native.parse(418)
        cls.texts = [[bytes.fromhex(text) for text in row['description_hex']]
                     for row in cls.loaded]
        by_line = {r['source_line']: r for r in table['records']}
        cls.raw_texts = [[bytes.fromhex(by_line[o['source_line']]['raw_fields_hex'][3])
                          for o in q['objectives_text']] for q in cls.missions]
        if [r['description_count'] for r in cls.loaded] != cls.counts:
            raise AssertionError('Native loader/source description count mismatch')
        # 585F6 uses read order, not the parsed STEP number, as the array index.
        for index, mission in enumerate(cls.missions, 1):
            if mission['id'] != index or [o['step'] for o in mission['objectives_text']] != list(
                    range(1, mission['step_field'] + 1)):
                raise AssertionError('Current source no longer has contiguous ordered rows')
        directory = ROOT / 'artifacts/quest-record'
        directory.mkdir(parents=True, exist_ok=True)
        cls.executable = quest.build_fixture(directory)

    def cpp(self, counts, values):
        inputs = [len(counts), *counts, *values]
        result = subprocess.run([str(self.executable), '--descriptions'],
                                input=' '.join(map(str, inputs)), capture_output=True,
                                text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = [line.split() for line in result.stdout.splitlines()]
        self.assertEqual(len(rows), len(values))
        return [(None if a == '-' else (int(a), int(b)), bytes.fromhex(raw))
                for a, b, raw in rows]

    def vm(self):
        vm = quest.CurrentQuestSyncTests.vm(self, suppress_open=1)
        vm.mem_write(UI + 0xc2104, bytes(60))
        vm.mem_write(RESOURCE + 0xd2ac4, struct.pack('<I', ROWS))
        vm.mem_map(ARENA, ARENA_SIZE)
        cursor = ARENA
        self.pointers = []
        for mission, texts in enumerate(self.texts):
            array = cursor
            cursor += 4 * len(texts)
            pointers = []
            for text in texts:
                pointers.append(cursor)
                vm.mem_write(cursor, text + b'\0')
                cursor += len(text) + 1
            vm.mem_write(array, struct.pack('<' + 'I' * len(pointers), *pointers))
            vm.mem_write(ROWS + 40 * mission, struct.pack('<H', len(texts)))
            vm.mem_write(ROWS + 40 * mission + 36, struct.pack('<I', array))
            self.pointers.append(pointers)
        self.assertLess(cursor, ARENA + ARENA_SIZE)
        vm.mem_protect(ARENA, ARENA_SIZE, UC_PROT_READ)
        return vm

    def description(self, vm, slot=14, click=False):
        vm.reg_write(UC_X86_REG_ESP, quest.routes.SP)
        if click:
            vm.mem_write(UI + 0xc2144, struct.pack('<h', slot // 5))
            vm.reg_write(UC_X86_REG_ESI, UI)
            vm.reg_write(UC_X86_REG_EAX, slot % 5)
            entry = 0xc92ea
        else:
            vm.reg_write(UC_X86_REG_ECX, UI)
            vm.mem_write(quest.routes.SP, struct.pack('<II', quest.routes.RETURN, slot))
            entry = 0xc9550
        self.run_to(vm, entry, 0x10f580)
        # Original code has pushed the string, color and zero, then CALL's return.
        sp = vm.reg_read(UC_X86_REG_ESP)
        ret, pointer, color, zero = struct.unpack('<4I', vm.mem_read(sp, 16))
        self.assertEqual((color, zero), (0xff000000, 0))
        self.assertIn(ret - BASE, (0xc95e6, 0xc9602, 0xc9365, 0xc9382))
        return pointer

    def test_source_loader_and_both_consumer_instructions(self):
        expected = {
            0x584ae: '0fbfb42424100000',  # Signed catalog allocation count.
            0x584f1: '8bd84b',            # Mission ID minus one.
            0x58575: '66893c19',          # STEP count -> row word.
            0x58594: '89441a24',          # Description pointer array -> row +36.
            0x585f6: '8904b2',            # Store by sequential ESI, not STEP label.
            0xc958a: '81e1ffff0000c1e810740148',
            0xc95c6: '0fbf113bc2731e',
            0xc95d7: '8b1481',
            0xc9304: '25ffff0000c1e910740149',
            0xc933f: '0fbf103bca7325',
            0xc9356: '8b0c88',
        }
        for rva, hex_bytes in expected.items():
            raw = bytes.fromhex(hex_bytes)
            self.assertEqual(self.image[rva:rva + len(raw)], raw, hex(rva))
        self.assertEqual((len(self.counts), sum(self.counts), max(self.counts)), (418, 2014, 29))
        self.assertEqual(self.image[0x1b4640], 0)  # Native empty-description fallback.

    def test_long_descriptions_use_actual_loader_output_without_changing_source(self):
        differences = [(m+1, i, len(raw), len(text))
                       for m, (raws, texts) in enumerate(zip(self.raw_texts, self.texts))
                       for i, (raw, text) in enumerate(zip(raws, texts)) if raw != text]
        self.assertEqual(differences, [(60, 9, 416, 379), (168, 2, 380, 379)])
        vm = self.vm()
        for mission, index, _, _ in differences:
            expected = self.texts[mission-1][index]
            for subtype in (4, 5):
                raw = subprocess.check_output([str(self.executable), '--encode', '14',
                    str(subtype), str(((index+1)<<16)|mission)], text=True, timeout=5)
                self.dispatch(vm, bytes.fromhex(raw))
                pointer = self.description(vm)
                self.assertEqual(bytes(vm.mem_read(pointer, len(expected)+1)), expected+b'\0')

    def test_full_journal_snapshot_overwrites_stale_slots(self):
        vm=self.vm()
        values=[0 if slot%3==0 else ((self.counts[slot]<<16)|(slot+1)) for slot in range(15)]
        for snapshot in (values,[0]*15):
            inputs=[len(self.counts),*self.counts,*snapshot]
            result=subprocess.run([str(self.executable),'--journal'],
                input=' '.join(map(str,inputs)),capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stderr)
            raw=bytes.fromhex(result.stdout)
            self.assertEqual(len(raw),195)
            vm.mem_write(UI+0x232eb0,struct.pack('<I',1))
            for slot in range(15):
                record=raw[slot*13:(slot+1)*13]
                self.assertEqual(record,bytes.fromhex('db04000000')+struct.pack('<II',slot,snapshot[slot]))
                self.dispatch(vm,record)
            self.assertEqual(bytes(vm.mem_read(UI+0xc2104,60)),struct.pack('<15I',*snapshot))
        for slot in range(15):
            invalid=values.copy();invalid[slot]=419
            result=subprocess.run([str(self.executable),'--journal'],
                input=' '.join(map(str,[len(self.counts),*self.counts,*invalid])),
                capture_output=True,text=True,timeout=10)
            self.assertNotEqual(result.returncode,0)
            self.assertEqual(result.stdout,'')

    def test_every_source_description_and_bound_through_native_consumer(self):
        values, expected = [], []
        for mission, count in enumerate(self.counts, 1):
            for selector in range(count + 2):
                values.append((selector << 16) | mission)
                expected.append((mission, max(selector - 1, 0)) if selector <= count else None)
        values += [0, 0xffff0000, 419, 0xffffffff, 0x80000001]
        expected += [None] * 5
        vm = self.vm()
        observed_reads = []
        hook = vm.hook_add(UC_HOOK_MEM_READ, lambda uc, access, address, size, value, data:
                           observed_reads.append((address, size)), begin=ARENA,
                           end=ARENA + ARENA_SIZE - 1)
        try:
            for packed, want, (actual, record) in zip(values, expected, self.cpp(self.counts, values)):
                with self.subTest(packed=hex(packed)):
                    self.assertEqual(actual, want)
                    self.assertEqual(struct.unpack_from('<I', record, 9)[0], packed)
                    self.dispatch(vm, record)
                    observed_reads.clear()
                    pointer = self.description(vm)
                    if want is None:
                        self.assertEqual(pointer, BASE + 0x1b4640)
                        self.assertEqual(observed_reads, [])
                    else:
                        mission, index = want
                        self.assertEqual(pointer, self.pointers[mission - 1][index])
                        text = self.texts[mission - 1][index]
                        self.assertEqual(bytes(vm.mem_read(pointer, len(text) + 1)), text + b'\0')
                        self.assertEqual(len(observed_reads), 1)
                    # The display resolver has not rewritten the packed DB value.
                    self.assertEqual(bytes(vm.mem_read(UI + 0xc213c, 4)), struct.pack('<I', packed))
        finally:
            vm.hook_del(hook)

    def test_click_consumer_selects_only_valid_description_for_both_subtypes(self):
        # Actual first mission has two descriptions. 0 and 1 must stay distinct
        # packed values despite selecting identical text; selector 3 is blank.
        values = [1, 0x10001, 0x20001, 0x30001, 0x80000001, 0x801a2]
        candidates = self.cpp(self.counts, values)
        for subtype in (4, 5):
            vm = self.vm()
            for packed, (reference, _) in zip(values, candidates):
                raw = subprocess.check_output([str(self.executable), '--encode', '14',
                                               str(subtype), str(packed)], text=True, timeout=5)
                self.dispatch(vm, bytes.fromhex(raw))
                vm.mem_write(UI + 0x232eb8, struct.pack('<I', 0x76543210))
                pointer = self.description(vm, click=True)
                self.assertEqual(pointer, BASE + 0x1b4640 if reference is None else
                                 self.pointers[reference[0] - 1][reference[1]])
                selected = struct.unpack('<I', vm.mem_read(UI + 0x232eb8, 4))[0]
                self.assertEqual(selected, packed if reference else 0x76543210)

    def test_signed_count_hazard_is_rejected_without_discarding_raw_record(self):
        for count in (0, 0x8000, 0xffff):
            outputs = self.cpp([count], [1, 0x20001, 0xffff0001])
            self.assertTrue(all(reference is None for reference, _ in outputs))
            self.assertEqual([struct.unpack_from('<I', raw, 9)[0] for _, raw in outputs],
                             [1, 0x20001, 0xffff0001])
        vm = self.vm()
        vm.mem_write(ROWS, struct.pack('<H', 0xffff))
        # Negative word sign-extends to 0xffffffff; unsigned JAE fails to
        # reject index 1. The actual pointer load then crosses an unmapped page.
        vm.mem_write(ROWS + 36, struct.pack('<I', ARENA + ARENA_SIZE - 4))
        vm.mem_write(UI + 0xc213c, struct.pack('<I', 0x20001))
        with self.assertRaises(UcError):
            self.description(vm)
        self.assertEqual(vm.reg_read(quest.routes.UC_X86_REG_EIP), BASE + 0xc95d7)

    def test_bounded_catalog_domain_and_standalone_cpp_assertions(self):
        self.assertEqual(self.cpp([], [1])[0][0], None)
        self.assertEqual(self.cpp([1] * 32768, [1])[0][0], None)
        self.assertEqual(self.cpp([1] * 32767, [32767])[0][0], (32767, 0))
        values = [(32767 << 16) | 1, (32768 << 16) | 1]
        self.assertEqual([r for r, _ in self.cpp([32767], values)], [(1, 32766), None])
        subprocess.run([str(self.executable)], check=True, timeout=5)


if __name__ == '__main__':
    unittest.main()
