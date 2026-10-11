"""Reproduce the native empty-catalog dereference; not a client repair."""
import hashlib
import json
from pathlib import Path
import struct
import unittest

from unicorn import Uc,UcError,UC_ARCH_X86,UC_MODE_32,UC_HOOK_MEM_INVALID
from unicorn.x86_const import UC_X86_REG_ECX,UC_X86_REG_ESP,UC_X86_REG_EIP


class EmptyMapCatalogTests(unittest.TestCase):
    def test_native_reconnect_processes_reuse_same_decompression_path(self):
        root=Path(__file__).resolve().parents[2]/'artifacts/runs'
        paths=[]
        for peer in (0,1):
            folder=root/f'native-mapfile-20260921-02-again{peer}'
            records=[json.loads(path.read_text()) for path in folder.glob('map-file-*.json')]
            game=[row for row in records if bytes.fromhex(row['source_hex']).lower().endswith(b'gamedata.csv')]
            self.assertEqual(len(game),1)
            self.assertNotEqual(game[0]['open_result'],0)
            self.assertEqual(game[0]['return_value'],1)
            self.assertEqual(len(game[0]['temporary']),1)
            paths.append(bytes.fromhex(game[0]['temporary'][0]['path_hex']))
        self.assertEqual(paths[0],paths[1])
        self.assertTrue(paths[0].lower().endswith(b'\\client\\tmp\\tmp.2'))
        failed=[]
        for peer in (0,1):
            path=root/f'native-mapfile-20260921-02-again{peer}'/'run.json'
            if path.exists():
                result=json.loads(path.read_text())
                if 'world_table_fault' in result:failed.append(result['world_table_fault'])
        self.assertTrue(failed)
        self.assertTrue(all((fault['pc'],fault['count'],fault['table'])==(0x459ed2,0,0) for fault in failed))

    def test_failed_reconnect_dispatched_other_sections_but_not_catalog(self):
        root=Path(__file__).resolve().parents[2]/'artifacts/runs'
        result=json.loads((root/'native-mapsection-20260921-01-again0/run.json').read_text())
        self.assertEqual(result['result'],'UNEXPECTED_STOP')
        sections=result['map_section_dispatch']
        self.assertGreater(len(sections),20)
        names=[bytes.fromhex(row['section_hex']) for row in sections]
        self.assertIn(b'NPCList',names)
        self.assertIn(b'ShopRate',names)
        self.assertNotIn(b'Map_City_Coordniate',names)
        fault=result['world_table_fault']
        self.assertEqual((fault['pc'],fault['count'],fault['table']),(0x459ed2,0,0))
        self.assertEqual({row['owner'] for row in sections},{fault['owner']})
        self.assertEqual([row['stage'] for row in result['map_catalog_trace']],['FIRST_BIND'])
        self.assertLess(sections[-1]['sequence'],result['map_catalog_trace'][0]['sequence'])

    def test_skill_reconnect_captured_empty_first_bind(self):
        root=Path(__file__).resolve().parents[2]/'artifacts/runs'
        result=json.loads((root/'native-skill-reconnect-20260921-02-again0/run.json').read_text())
        self.assertEqual(result['result'],'UNEXPECTED_STOP')
        fault=result['world_table_fault']
        self.assertEqual((fault['pc'],fault['table_cursor'],fault['count'],fault['table']),(0x459ed2,0,0,0))
        trace=result['map_catalog_trace']
        self.assertEqual([event['stage'] for event in trace],['FIRST_BIND'])
        self.assertEqual((trace[0]['owner'],trace[0]['count'],trace[0]['table']),(fault['owner'],0,0))

    def test_live_loader_publishes_catalog_before_binding(self):
        root=Path(__file__).resolve().parents[2]/'artifacts/runs'
        owner=json.loads((root/'native-maploader-trace-20260921-01/shared-result.json').read_text())
        self.assertEqual(owner['result'],'TWO_NATIVE_PLAYER_POOLS_OBSERVED')
        names=list(owner['peers'].values())+list(owner['live_reconnect']['peers'].values())
        self.assertEqual(len(set(names)),4)
        for name in names:
            with self.subTest(run=name):
                result=json.loads((root/name/'run.json').read_text())
                self.assertEqual(result['result'],'NATIVE_SHARED_PLAYER_VISIBILITY_OBSERVED')
                self.assertNotIn('world_table_fault',result)
                trace=result['map_catalog_trace']
                self.assertEqual([e['stage'] for e in trace],['LOADER_ENTRY','LOADER_RETURN','FIRST_BIND'])
                self.assertEqual([e['count'] for e in trace],[0,144,144])
                self.assertEqual(trace[0]['table'],0)
                self.assertNotEqual(trace[1]['table'],0)
                self.assertEqual(trace[1]['table'],trace[2]['table'])
                self.assertEqual(len({e['owner'] for e in trace}),1)
                self.assertLess(trace[0]['sequence'],trace[1]['sequence'])
                self.assertLess(trace[1]['sequence'],trace[2]['sequence'])

    def test_original_empty_catalog_reaches_observed_null_read(self):
        root=Path(__file__).resolve().parents[2]
        image=(root/'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin').read_bytes()
        self.assertEqual(hashlib.sha256(image).hexdigest(),
                         '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763')
        vm=Uc(UC_ARCH_X86,UC_MODE_32)
        vm.mem_map(0x459000,0x1000)
        vm.mem_write(0x459000,image[0x59000:0x5a000])
        owner=0x10000000;stack=0x20000000
        vm.mem_map(owner,0xd3000);vm.mem_map(stack,0x1000)
        vm.mem_write(stack+0x800,struct.pack('<II',0x459ee6,0))
        vm.reg_write(UC_X86_REG_ECX,owner)
        vm.reg_write(UC_X86_REG_ESP,stack+0x800)
        faults=[]
        def invalid(uc,access,address,size,value,data):
            faults.append((uc.reg_read(UC_X86_REG_EIP),address,size))
            return False
        vm.hook_add(UC_HOOK_MEM_INVALID,invalid)
        with self.assertRaises(UcError):vm.emu_start(0x459e70,0x459ee6,count=30)
        self.assertEqual(faults,[(0x459ed2,0x1a0,4)])
        self.assertEqual(bytes(vm.mem_read(owner+0xd2aba,6)),bytes(6))


if __name__=='__main__':unittest.main()
