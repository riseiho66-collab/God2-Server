"""Current scene-transfer prefix; not death policy or full scene acceptance."""
import struct
import unittest
import hashlib
import json
import sqlite3
from pathlib import Path

from tools.strike_lab.current_battle_entry import (
    NativeRun, WORLD, SP, PACKET_PAGE, native_length, pinned_image,
)
from unicorn.x86_const import UC_X86_REG_ESP


class SceneTransferTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = pinned_image()

    def test_native_dispatch_and_logical_length(self):
        self.assertEqual(native_length(0x61), 9)
        self.assertEqual(struct.unpack_from('<I', self.image, 0x6b5d4 + 4*0x61)[0], 0x469345)
        n = NativeRun(self.image)
        n.put(PACKET_PAGE, b'\x61' + bytes(8))
        n.registers(ebx=PACKET_PAGE, ebp=WORLD)
        n.run(0x68b4e, ((0x68b4e,0x68b68),(0x69345,0x69352)), {0x814f0})
        self.assertEqual(n.stop, 0x814f0)  # UI prelude remains outside this proof.

    def test_original_prefix_same_scene_flag_and_selector_boundaries(self):
        # Start after the UI prelude, not with a fabricated callee return.
        cases = 0
        for area, scene in ((0,0),(2,4),(2,15),(63,1023)):
            for previous_area, previous_scene in ((area,scene),(area ^ 1,scene),(area,scene ^ 1)):
                for flags in (0,1,2,3,0x10000,0x10001,0x10002,0xffffffff):
                    with self.subTest(area=area, scene=scene, previous=(previous_area,previous_scene), flags=flags):
                        n = NativeRun(self.image)
                        n.map(0,4096)  # Explicit SEH chain head for the original prologue.
                        body = struct.pack('<HHI', area | (scene << 6), 0xa55a, flags)
                        n.put(PACKET_PAGE, b'\x61' + body)
                        n.put32(WORLD+0x15396850, previous_scene)
                        n.put(WORLD+0x15396854, struct.pack('<H',previous_area))
                        n.put(WORLD+0x1539684c, b'\xa5')
                        n.put32(WORLD+0xaa36480, 0x6200000)
                        n.registers(ebx=PACKET_PAGE, ebp=WORLD)
                        n.run(0x69352, ((0x69352,0x6935d),(0x6bcc0,0x6bd62)), {0x5aa70})
                        same = (previous_area,previous_scene)==(area,scene)
                        reuse = same and bool(flags & 0x10000)
                        expected = flags & ~0x10000 if reuse else flags
                        self.assertEqual(bytes(n.vm.mem_read(PACKET_PAGE+1,8)),
                                         struct.pack('<HHI',area | (scene << 6),0xa55a,expected))
                        self.assertEqual(n.get32(WORLD+0x15396850),scene)
                        self.assertEqual(struct.unpack('<H',n.vm.mem_read(WORLD+0x15396854,2))[0],area)
                        self.assertEqual(bytes(n.vm.mem_read(WORLD+0x1539684c,1)),bytes([flags & 3]))
                        # At the first metadata call, the prologue ESP is 12 bytes above current ESP.
                        sp = n.vm.reg_read(UC_X86_REG_ESP)
                        self.assertEqual(n.get32(sp+12+0x18),int(not reuse))
                        self.assertEqual(n.get32(sp+4) & 0xff,area)
                        self.assertEqual(n.get32(sp+8) & 0xffff,scene)
                        self.assertIn(0x6bcc0,n.visits)
                        cases += 1
        self.assertEqual(cases,96)

    def test_actual_indoor_return_prefix_and_cross_scene_flag_hazard(self):
        for previous_scene,target_scene,kind,x,y in ((4,15,2,17,13),(15,4,0,110,70),
                                                      (4,0,1,477,209)):
            for accidental_reuse_flag in (False,True):
                with self.subTest(previous=previous_scene,target=target_scene,reuse=accidental_reuse_flag):
                    packed=kind | (x<<2) | (y<<17) | (0x10000 if accidental_reuse_flag else 0)
                    body=struct.pack('<HHI',2 | (target_scene<<6),0,packed)
                    n=NativeRun(self.image)
                    n.map(0,4096)
                    n.put(PACKET_PAGE,b'\x61'+body)
                    n.put32(WORLD+0x15396850,previous_scene)
                    n.put(WORLD+0x15396854,struct.pack('<H',2))
                    n.put32(WORLD+0xaa36480,0x6200000)
                    n.registers(ebx=PACKET_PAGE,ebp=WORLD)
                    n.run(0x69352,((0x69352,0x6935d),(0x6bcc0,0x6bd62)),{0x5aa70})
                    normalized=bytes(n.vm.mem_read(PACKET_PAGE+1,8))
                    self.assertEqual(normalized,body)  # Cross-map prefix never clears bit16.
                    self.assertEqual(n.get32(WORLD+0x15396850),target_scene)
                    self.assertEqual(n.get32(n.vm.reg_read(UC_X86_REG_ESP)+12+0x18),1)
                    # A separate resource-complete coordinate island; not continuous execution.
                    coordinates=NativeRun(self.image)
                    coordinates.put(PACKET_PAGE,normalized)
                    coordinates.put32(WORLD+0x224,0xdeadbeef)
                    coordinates.put32(WORLD+0x228,0xcafebabe)
                    coordinates.put32(WORLD+0xa7e05dc,0x6000000)
                    coordinates.put32(0x6000000+0xbc,0)
                    coordinates.registers(esi=WORLD,edi=PACKET_PAGE)
                    coordinates.run(0x6c33a,((0x6c33a,0x6c3ce),),{0x6c224})
                    self.assertEqual(coordinates.get32(WORLD+0x224),x+(0x4000 if accidental_reuse_flag else 0))
                    self.assertEqual(coordinates.get32(WORLD+0x228),y)
                    if target_scene==4 and not accidental_reuse_flag:
                        self.assertEqual((b'\x61'+body).hex(),'6102010000b8018c00')

    def test_coordinate_island_uses_mutable_packet_not_saved_position(self):
        # Independent post-resource precondition. No metadata/renderer call is faked.
        for kind in range(4):
            for x,y in ((0,0),(110,70),(0x3fff,0),(0x4000,1),(0x7fff,0x7fff)):
                for clear_same_scene_flag in (False,True):
                    packed = kind | (x << 2) | (y << 17)
                    normalized = packed & ~0x10000 if clear_same_scene_flag else packed
                    n = NativeRun(self.image)
                    n.put(PACKET_PAGE,struct.pack('<HHI',2 | (4 << 6),0xa55a,normalized))
                    n.put32(WORLD+0x224,0xdeadbeef)
                    n.put32(WORLD+0x228,0xcafebabe)
                    n.put32(WORLD+0xa7e05dc,0x6000000)
                    n.put32(0x6000000+0xbc,0)  # Explicit missing auxiliary object branch.
                    n.registers(esi=WORLD,edi=PACKET_PAGE)
                    n.run(0x6c33a,((0x6c33a,0x6c3ce),),{0x6c224})
                    self.assertEqual(n.get32(WORLD+0x224),(normalized >> 2) & 0x7fff)
                    self.assertEqual(n.get32(WORLD+0x228),normalized >> 17)
                    self.assertEqual(n.get32(SP+0x40),1)
                    if kind==2:
                        self.assertEqual(n.get32(SP+0x14),(normalized >> 2) & 0x7fff)
                        self.assertEqual(n.get32(SP+0x10),(normalized >> 17)+1)

    def test_transfer_resets_ring_and_seeds_destination_slot_zero(self):
        for previous in range(40):
            n=NativeRun(self.image)
            n.put(WORLD+0x234,b'\xa5'*324)
            n.put(WORLD+0x234,bytes([17,previous,(previous+1)%40]))
            n.put32(WORLD+0x224,111);n.put32(WORLD+0x228,70)
            n.registers(esi=WORLD)
            n.run(0x6c414,((0x6c414,0x6c443),(0x103640,0x103651),
                          (0x103680,0x1036a5),(0x1036b0,0x1036fb)),{0x6c443})
            self.assertEqual(bytes(n.vm.mem_read(WORLD+0x234,3)),bytes([1,0,1]))
            self.assertEqual(bytes(n.vm.mem_read(WORLD+0x238,8)),struct.pack('<II',111,70))
            self.assertEqual(n.vm.reg_read(UC_X86_REG_ESP),SP)


class SceneTransferCapturedRuntimeTests(unittest.TestCase):
    def test_cross_scene_receiver_loads_native_indoor_grid_without_save_mutation(self):
        root=Path(__file__).resolve().parents[2]
        run=root/'artifacts/runs/native-town-indoor-transfer-20260921-04'
        report=json.loads((run/'run.json').read_text())
        self.assertEqual(report['result'],'NATIVE_TOWN_TO_INDOOR_RECEIVER_RETURNED')
        self.assertIsNone(report.get('error'))
        entry,end,frame=(report[k] for k in ('town_scene_entry','town_scene_return','town_indoor_loaded_scene'))
        self.assertEqual((entry['pc'],end['pc'],end['eax']),(0x46bcc0,0x46935d,1))
        self.assertEqual(end['sp'],entry['sp']+12)
        self.assertEqual(entry['body_hex'],'c203000046001a00')
        self.assertEqual(end['body_hex'],entry['body_hex'])
        self.assertEqual(len({(e['pid'],e['tid']) for e in (entry,end,frame)}),1)
        self.assertLess(entry['sequence'],end['sequence'])
        self.assertLess(end['sequence'],frame['sequence'])
        state=frame['snapshot']
        self.assertEqual((state['area'],state['scene'],state['kind'],state['x'],state['y']),(2,15,2,17,13))
        self.assertEqual(state['ring_hex'],'010001')
        self.assertEqual(state['slot0_hex'],entry['snapshot']['slot0_hex'])
        grid=json.loads((root/'artifacts/world-atlas/indoor-2-15.json').read_text())['grid']
        self.assertEqual((state['grid_width'],state['grid_height']),(31,31))
        self.assertEqual(state['grid_hex'],grid['cells_hex'])
        # Retained town UI metadata is not the active indoor collision object.
        self.assertEqual(state['loaded_scene_id'],258)
        self.assertTrue(bytes.fromhex(state['metadata_hex']).startswith(b'CityI1\0'))
        self.assertNotEqual(state['indoor'],state['scene_object'])
        packets=[]
        for name,expected,direction in (
                ('packet-0411','0c0061c203000046001a0026','S2C'),
                ('packet-0417','08001c01000000c9','C2S')):
            folder=run/'crypto-private'
            metadata=json.loads((folder/(name+'.json')).read_text())
            plain=(folder/metadata['plain_file']).read_bytes()
            self.assertEqual(plain.hex(),expected)
            self.assertEqual(metadata['direction'],direction)
            self.assertTrue(metadata['checksum_valid'])
            self.assertEqual(hashlib.sha256(plain).hexdigest(),metadata['plain_sha256'])
            self.assertEqual(hashlib.sha256((folder/metadata['wire_file']).read_bytes()).hexdigest(),metadata['wire_sha256'])
            packets.append(metadata)
        self.assertEqual(packets[0]['socket'],packets[1]['socket'])
        self.assertLess(packets[0]['sequence'],entry['sequence'])
        self.assertLess(end['sequence'],packets[1]['sequence'])
        self.assertLess(packets[1]['sequence'],frame['sequence'])
        source=root/'artifacts/runs/native-town-quest-reward-20260921-01/town-diagnostic-accounts.db'
        with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as a, \
             sqlite3.connect((run/'town-diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as b:
            schema="SELECT name,sql FROM sqlite_master WHERE type='table' ORDER BY name"
            self.assertEqual(a.execute(schema).fetchall(),b.execute(schema).fetchall())
            for name,_ in a.execute(schema):
                query='SELECT * FROM "'+name.replace('"','""')+'"'
                self.assertEqual(sorted(a.execute(query).fetchall(),key=repr),
                                 sorted(b.execute(query).fetchall(),key=repr),name)
        log=(run/'cpp-server.log').read_text()
        self.assertEqual(log.count('DIAGNOSTIC_TOWN_SCENE_CONTEXT_ACCEPTED'),1)
        self.assertNotIn('policy or response rejected',log)

    def test_fresh_connection_restores_post_transfer_walk(self):
        root=Path(__file__).resolve().parents[2]/'artifacts/runs'
        source=root/'native-town-relocation-move-20260921-02'
        run=root/'native-town-relocation-move-relogin-20260921-01'
        before=json.loads((source/'run.json').read_text())
        report=json.loads((run/'run.json').read_text())
        self.assertEqual(report['result'],'NATIVE_TOWN_COMPLETED_QUEST_RESTORED')
        self.assertIsNone(report.get('error'))
        state=report['town_completed_world_snapshot']['snapshot']
        self.assertEqual((state['area'],state['scene'],state['kind'],state['x'],state['y']),(2,4,0,112,70))
        self.assertEqual(state['ring_hex'],'010001')
        self.assertNotEqual(report['login_entry']['pid'],before['login_entry']['pid'])
        self.assertNotIn('town_scene_entry',report)
        self.assertNotIn('movement_steps',report)
        with sqlite3.connect((source/'town-diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as a, \
             sqlite3.connect((run/'town-diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as b:
            schema="SELECT name,sql FROM sqlite_master WHERE type='table' ORDER BY name"
            self.assertEqual(a.execute(schema).fetchall(),b.execute(schema).fetchall())
            for name,_ in a.execute(schema):
                query='SELECT * FROM "'+name.replace('"','""')+'"'
                self.assertEqual(sorted(a.execute(query).fetchall(),key=repr),
                                 sorted(b.execute(query).fetchall(),key=repr),name)

    def test_relocation_then_native_walk_persists_only_position(self):
        root=Path(__file__).resolve().parents[2]
        run=root/'artifacts/runs/native-town-relocation-move-20260921-02'
        report=json.loads((run/'run.json').read_text())
        self.assertEqual(report['result'],'NATIVE_TOWN_RELOCATION_AND_MOVEMENT_COMPLETED')
        self.assertIsNone(report.get('error'))
        entry,end=(report[k]['snapshot'] for k in ('town_scene_entry','town_scene_return'))
        self.assertEqual((entry['x'],entry['y'],end['x'],end['y']),(110,70,111,70))
        self.assertEqual(end['ring_hex'],'010001')
        self.assertEqual(entry['slot0_hex'],end['slot0_hex'])
        self.assertEqual(len(report['movement_steps']),1)
        self.assertEqual(report['movement_steps'][0]['ack_hex'],'5d01')
        self.assertEqual(report['movement_steps'][0]['ring_after_ack'],'010102')
        final=report['town_scene_movement_complete']
        self.assertEqual(final['position_hex'],struct.pack('<II',112,70).hex())
        self.assertEqual(final['ring_hex'],'010102')
        self.assertLess(report['town_scene_return']['sequence'],report['town_scene_movement_ack']['sequence'])
        self.assertLess(report['town_scene_movement_ack']['sequence'],final['sequence'])
        source=root/'artifacts/runs/native-town-quest-reward-20260921-01/town-diagnostic-accounts.db'
        with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as a, \
             sqlite3.connect((run/'town-diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as b:
            self.assertEqual(b.execute('SELECT * FROM recovered_positions').fetchall(),[(1,2,4,112,70,55)])
            self.assertEqual(a.execute('SELECT * FROM recovered_positions').fetchall(),[(1,2,4,110,70,53)])
            for (name,) in a.execute("SELECT name FROM sqlite_master WHERE type='table'"):
                if name=='recovered_positions':continue
                query='SELECT * FROM "'+name.replace('"','""')+'"'
                self.assertEqual(sorted(a.execute(query).fetchall(),key=repr),
                                 sorted(b.execute(query).fetchall(),key=repr),name)
        log=(run/'cpp-server.log').read_text()
        self.assertEqual(log.count('DIAGNOSTIC_TOWN_RELOCATION_COMMITTED'),1)
        self.assertEqual(log.count('DIAGNOSTIC_TOWN_SCENE_CONTEXT_ACCEPTED'),1)
        self.assertNotIn('policy or response rejected',log)

    def test_complete_receiver_notice_and_unchanged_save(self):
        root=Path(__file__).resolve().parents[2]
        run=root/'artifacts/runs/native-town-scene-transfer-20260921-03'
        report=json.loads((run/'run.json').read_text())
        self.assertEqual(report['result'],'NATIVE_TOWN_SAME_SCENE_TRANSFER_RETURNED')
        self.assertIsNone(report.get('error'))
        entry,end,frame=(report[k] for k in ('town_scene_entry','town_scene_return','town_scene_final_frame'))
        self.assertEqual((entry['pc'],end['pc'],end['eax']),(0x46bcc0,0x46935d,1))
        self.assertEqual(end['sp'],entry['sp']+12)
        self.assertEqual(entry['snapshot'],end['snapshot'])
        self.assertEqual((entry['snapshot']['x'],entry['snapshot']['y']),(110,70))
        self.assertEqual(entry['body_hex'],'02010000b8018d00')
        self.assertEqual(end['body_hex'],'02010000b8018c00')
        self.assertEqual(len({(e['pid'],e['tid']) for e in (entry,end,frame)}),1)
        self.assertLess(entry['sequence'],end['sequence'])
        self.assertLess(end['sequence'],frame['sequence'])
        packets=[]
        for filename,expected,direction in (
                ('packet-0413','0c006102010000b8018d004a','S2C'),
                ('packet-0421','08001c01000000c9','C2S')):
            folder=run/'crypto-private'
            metadata=json.loads((folder/(filename+'.json')).read_text())
            plain=(folder/metadata['plain_file']).read_bytes()
            wire=(folder/metadata['wire_file']).read_bytes()
            self.assertEqual(plain.hex(),expected)
            self.assertEqual(metadata['direction'],direction)
            self.assertTrue(metadata['checksum_valid'])
            self.assertFalse(metadata['brute_force_used'])
            self.assertEqual(hashlib.sha256(plain).hexdigest(),metadata['plain_sha256'])
            self.assertEqual(hashlib.sha256(wire).hexdigest(),metadata['wire_sha256'])
            packets.append(metadata)
        self.assertEqual(packets[0]['socket'],packets[1]['socket'])
        self.assertLess(packets[0]['sequence'],entry['sequence'])
        self.assertLess(end['sequence'],packets[1]['sequence'])
        self.assertLess(packets[1]['sequence'],frame['sequence'])
        log=(run/'cpp-server.log').read_text()
        self.assertEqual(log.count('DIAGNOSTIC_TOWN_SCENE_CANDIDATE'),1)
        self.assertEqual(log.count('DIAGNOSTIC_TOWN_SCENE_CONTEXT_ACCEPTED'),1)
        self.assertNotIn('policy or response rejected',log)
        source=root/'artifacts/runs/native-town-quest-reward-20260921-01/town-diagnostic-accounts.db'
        with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as a, \
             sqlite3.connect((run/'town-diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as b:
            schema="SELECT name,sql FROM sqlite_master WHERE type='table' ORDER BY name"
            self.assertEqual(a.execute(schema).fetchall(),b.execute(schema).fetchall())
            for name,_ in a.execute(schema):
                query='SELECT * FROM "'+name.replace('"','""')+'"'
                self.assertEqual(sorted(a.execute(query).fetchall(),key=repr),
                                 sorted(b.execute(query).fetchall(),key=repr),name)

    def test_durable_indoor_receiver_with_explicit_locale_compatibility(self):
        root=Path(__file__).resolve().parents[2]
        run=root/'artifacts/runs/native-town-indoor-durable-20260921-02'
        report=json.loads((run/'run.json').read_text())
        self.assertEqual(report['result'],'NATIVE_TOWN_TO_INDOOR_DURABLE_RECEIVER_RETURNED')
        self.assertIsNone(report.get('error'))
        locale=report['resource_locale_override']
        self.assertEqual((locale['before_hex'],locale['after_hex']),('04000200','04000100'))
        self.assertIn('GetSystemDefaultLangID',locale['language_import'])
        entry,end,frame=(report[k] for k in ('town_scene_entry','town_scene_return','town_scene_final_frame'))
        self.assertEqual((end['eax'],end['sp']-entry['sp']),(1,12))
        self.assertEqual(entry['body_hex'],end['body_hex'])
        snap=report['town_indoor_loaded_scene']['snapshot']
        self.assertEqual(tuple(snap[k] for k in ('area','scene','kind','x','y')),(2,15,2,17,13))
        grid=json.loads((root/'artifacts/world-atlas/indoor-2-15.json').read_text())['grid']
        self.assertEqual((snap['grid_width'],snap['grid_height']),(grid['side'],grid['side']))
        self.assertEqual(snap['grid_hex'],grid['cells_hex'])
        packets=[]
        for stem,direction,expected in (('packet-0411','S2C','0c0061c203000046001a0026'),
                                        ('packet-0417','C2S','08001c01000000c9')):
            folder=run/'crypto-private'
            meta=json.loads((folder/(stem+'.json')).read_text())
            plain=(folder/meta['plain_file']).read_bytes()
            wire=(folder/meta['wire_file']).read_bytes()
            self.assertEqual((plain.hex(),meta['direction']),(expected,direction))
            self.assertTrue(meta['checksum_valid'])
            self.assertFalse(meta['brute_force_used'])
            self.assertEqual(hashlib.sha256(plain).hexdigest(),meta['plain_sha256'])
            self.assertEqual(hashlib.sha256(wire).hexdigest(),meta['wire_sha256'])
            packets.append(meta)
        self.assertEqual(packets[0]['socket'],packets[1]['socket'])
        self.assertLess(packets[0]['sequence'],entry['sequence'])
        self.assertLess(entry['sequence'],end['sequence'])
        self.assertLess(end['sequence'],packets[1]['sequence'])
        self.assertLess(packets[1]['sequence'],frame['sequence'])
        source=root/'artifacts/runs/native-town-quest-reward-20260921-01/town-diagnostic-accounts.db'
        with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as a, \
             sqlite3.connect((run/'town-diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as b:
            self.assertEqual(b.execute('SELECT * FROM recovered_positions').fetchall(),[(1,2,15,17,13,54)])
            self.assertEqual(a.execute('SELECT * FROM recovered_positions').fetchall(),[(1,2,4,110,70,53)])
            for (name,) in a.execute("SELECT name FROM sqlite_master WHERE type='table'"):
                if name=='recovered_positions':continue
                query='SELECT * FROM "'+name.replace('"','""')+'"'
                self.assertEqual(sorted(a.execute(query).fetchall(),key=repr),sorted(b.execute(query).fetchall(),key=repr),name)
        log=(run/'cpp-server.log').read_text()
        self.assertEqual(log.count('DIAGNOSTIC_INDOOR_TRANSFER_COMMITTED'),1)
        self.assertEqual(log.count('DIAGNOSTIC_TOWN_SCENE_CONTEXT_ACCEPTED'),1)
        self.assertNotIn('policy or response rejected',log)

    def test_durable_indoor_followup_movement(self):
        root=Path(__file__).resolve().parents[2]
        run=root/'artifacts/runs/native-town-indoor-walk-20260921-01'
        report=json.loads((run/'run.json').read_text())
        self.assertEqual(report['result'],'NATIVE_TOWN_TO_INDOOR_AND_MOVEMENT_COMPLETED')
        self.assertIsNone(report.get('error'))
        final=report['town_indoor_movement_complete']
        snap=final['snapshot']
        self.assertEqual(tuple(snap[k] for k in ('area','scene','kind','x','y','ring_hex')),(2,15,2,18,12,'010102'))
        self.assertEqual(final['saved_position'],[1,2,15,18,12,55])
        self.assertEqual(report['town_indoor_saved_position'],[1,2,15,17,13,54])
        self.assertEqual(len(report['movement_steps']),1)
        step=report['movement_steps'][0]
        self.assertEqual((step['return_eax'],step['ack_hex'],step['ring_after_ack']),(1,'5d01','010102'))
        self.assertIn('b8c0245000ffd0',step['page']['hex'])
        self.assertLess(report['town_scene_return']['sequence'],report['town_scene_movement_ack']['sequence'])
        self.assertLess(report['town_scene_movement_ack']['sequence'],final['sequence'])
        folder=run/'crypto-private'
        meta=json.loads((folder/'packet-0426.json').read_text())
        plain=(folder/meta['plain_file']).read_bytes()
        wire=(folder/meta['wire_file']).read_bytes()
        self.assertEqual((plain.hex(),meta['direction']),('05005d0153','S2C'))
        self.assertTrue(meta['checksum_valid'])
        self.assertFalse(meta['brute_force_used'])
        self.assertEqual(hashlib.sha256(plain).hexdigest(),meta['plain_sha256'])
        self.assertEqual(hashlib.sha256(wire).hexdigest(),meta['wire_sha256'])
        source=root/'artifacts/runs/native-town-quest-reward-20260921-01/town-diagnostic-accounts.db'
        with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as a, \
             sqlite3.connect((run/'town-diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as b:
            self.assertEqual(b.execute('SELECT * FROM recovered_positions').fetchall(),[(1,2,15,18,12,55)])
            for (name,) in a.execute("SELECT name FROM sqlite_master WHERE type='table'"):
                if name=='recovered_positions':continue
                query='SELECT * FROM "'+name.replace('"','""')+'"'
                self.assertEqual(sorted(a.execute(query).fetchall(),key=repr),sorted(b.execute(query).fetchall(),key=repr),name)
        log=(run/'cpp-server.log').read_text()
        self.assertEqual(log.count('DIAGNOSTIC_INDOOR_TRANSFER_COMMITTED'),1)
        self.assertEqual(log.count('DIAGNOSTIC_TOWN_SCENE_CONTEXT_ACCEPTED'),1)
        self.assertNotIn('policy or response rejected',log)

    def test_cross_map_fresh_client_reconnect(self):
        root=Path(__file__).resolve().parents[2]
        source=root/'artifacts/runs/native-town-indoor-walk-20260921-01'
        run=root/'artifacts/runs/native-town-indoor-relogin-20260921-03'
        prior=json.loads((source/'run.json').read_text())
        report=json.loads((run/'run.json').read_text())
        self.assertEqual(report['result'],'NATIVE_CROSS_MAP_RECONNECT_RESTORED')
        self.assertIsNone(report.get('error'))
        final=report['indoor_reconnect_final']
        self.assertNotEqual(final['pid'],prior['town_indoor_movement_complete']['pid'])
        for absent in ('town_scene_entry','town_map_probe','movement_step'):
            self.assertNotIn(absent,report)
        snap=final['snapshot']
        self.assertEqual(tuple(snap[k] for k in ('area','scene','kind','x','y','ring_hex')),(2,15,2,18,12,'010001'))
        self.assertEqual(snap['scene_object'],0)
        self.assertIsNone(snap['metadata_hex'])
        grid=json.loads((root/'artifacts/world-atlas/indoor-2-15.json').read_text())['grid']
        self.assertEqual((snap['grid_width'],snap['grid_height']),(grid['side'],grid['side']))
        self.assertEqual(snap['grid_hex'],grid['cells_hex'])
        self.assertEqual(snap['slot0_hex'],'01000000c115000000000000000000000000000000000000')
        restored=report['journal_restore_returns']
        self.assertEqual([v['slot'] for v in restored],list(range(15)))
        self.assertEqual(restored[-1]['slots_hex'],'00'*60)
        self.assertLess(restored[-1]['sequence'],final['sequence'])
        self.assertFalse(any(pool['entries'] for pool in final['npcs']['pools']))
        with sqlite3.connect((source/'town-diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as a, \
             sqlite3.connect((run/'town-diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as b:
            schema="SELECT name,sql FROM sqlite_master WHERE type='table' ORDER BY name"
            self.assertEqual(a.execute(schema).fetchall(),b.execute(schema).fetchall())
            for name,_ in a.execute(schema):
                query='SELECT * FROM "'+name.replace('"','""')+'"'
                self.assertEqual(sorted(a.execute(query).fetchall(),key=repr),sorted(b.execute(query).fetchall(),key=repr),name)
        log=(run/'cpp-server.log').read_text()
        self.assertEqual(log.count('DIAGNOSTIC_INDOOR_SAVE_RESTORED'),1)
        self.assertNotIn('DIAGNOSTIC_INDOOR_TRANSFER_COMMITTED',log)
        self.assertNotIn('DIAGNOSTIC_TOWN_GUIDES_SENT',log)
        self.assertNotIn('policy or response rejected',log)

    def test_indoor_to_town_receiver_without_save_mutation(self):
        root=Path(__file__).resolve().parents[2]
        run=root/'artifacts/runs/native-indoor-town-return-20260921-01'
        report=json.loads((run/'run.json').read_text())
        self.assertEqual(report['result'],'NATIVE_INDOOR_TO_TOWN_RECEIVER_RETURNED')
        self.assertIsNone(report.get('error'))
        entry,end,final=(report[k] for k in ('town_scene_entry','town_scene_return','town_return_final'))
        self.assertEqual((end['eax'],end['sp']-entry['sp']),(1,12))
        self.assertEqual(entry['body_hex'],'02010000b8018c00')
        self.assertEqual(end['body_hex'],entry['body_hex'])
        self.assertEqual(entry['snapshot']['scene'],15)
        snap=final['snapshot']
        self.assertEqual(tuple(snap[k] for k in ('area','scene','kind','x','y','ring_hex')),(2,4,0,110,70,'010001'))
        self.assertEqual(snap['slot0_hex'],entry['snapshot']['slot0_hex'])
        self.assertEqual(snap['loaded_scene_id'],258)
        self.assertTrue(bytes.fromhex(snap['metadata_hex']).startswith(b'CityI1\0'))
        packets=[]
        for stem,direction,expected in (('packet-0484','S2C','0c006102010000b8018c0049'),
                                        ('packet-0492','C2S','08001c01000000c9')):
            folder=run/'crypto-private'
            meta=json.loads((folder/(stem+'.json')).read_text())
            plain=(folder/meta['plain_file']).read_bytes()
            wire=(folder/meta['wire_file']).read_bytes()
            self.assertEqual((plain.hex(),meta['direction']),(expected,direction))
            self.assertTrue(meta['checksum_valid'])
            self.assertFalse(meta['brute_force_used'])
            self.assertEqual(hashlib.sha256(plain).hexdigest(),meta['plain_sha256'])
            self.assertEqual(hashlib.sha256(wire).hexdigest(),meta['wire_sha256'])
            packets.append(meta)
        self.assertEqual(packets[0]['socket'],packets[1]['socket'])
        self.assertLess(packets[0]['sequence'],entry['sequence'])
        self.assertLess(entry['sequence'],end['sequence'])
        self.assertLess(end['sequence'],packets[1]['sequence'])
        self.assertLess(packets[1]['sequence'],final['sequence'])
        source=root/'artifacts/runs/native-town-indoor-walk-20260921-01/town-diagnostic-accounts.db'
        with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as a, \
             sqlite3.connect((run/'town-diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as b:
            schema="SELECT name,sql FROM sqlite_master WHERE type='table' ORDER BY name"
            self.assertEqual(a.execute(schema).fetchall(),b.execute(schema).fetchall())
            for name,_ in a.execute(schema):
                query='SELECT * FROM "'+name.replace('"','""')+'"'
                self.assertEqual(sorted(a.execute(query).fetchall(),key=repr),sorted(b.execute(query).fetchall(),key=repr),name)
        log=(run/'cpp-server.log').read_text()
        self.assertEqual(log.count('DIAGNOSTIC_RETURN_TOWN_CANDIDATE'),1)
        self.assertEqual(log.count('DIAGNOSTIC_TOWN_SCENE_CONTEXT_ACCEPTED'),1)
        self.assertNotIn('policy or response rejected',log)

    def test_durable_return_restores_town_npcs_without_reward_replay(self):
        root=Path(__file__).resolve().parents[2]
        run=root/'artifacts/runs/native-indoor-town-durable-20260921-01'
        report=json.loads((run/'run.json').read_text())
        self.assertEqual(report['result'],'NATIVE_DURABLE_RETURN_WITH_TOWN_NPCS')
        self.assertIsNone(report.get('error'))
        final=report['town_return_durable']
        snap=final['snapshot']
        self.assertEqual(tuple(snap[k] for k in ('area','scene','kind','x','y','ring_hex')),(2,4,0,110,70,'010001'))
        self.assertEqual(final['saved_position'],[1,2,4,110,70,56])
        self.assertEqual(snap['slot0_hex'],report['indoor_reconnect_final']['snapshot']['slot0_hex'])
        npcs=[e for pool in final['npcs']['pools'] for e in pool['entries']]
        self.assertEqual(sorted((e['identity'],e['x'],e['y']) for e in npcs),[(1606,110,69),(1607,112,70)])
        entry,end=report['town_scene_entry'],report['town_scene_return']
        self.assertEqual((end['eax'],end['sp']-entry['sp']),(1,12))
        self.assertEqual(entry['body_hex'],'02010000b8018c00')
        self.assertLess(end['sequence'],final['sequence'])
        source=root/'artifacts/runs/native-town-indoor-walk-20260921-01/town-diagnostic-accounts.db'
        with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as a, \
             sqlite3.connect((run/'town-diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as b:
            self.assertEqual(a.execute('SELECT * FROM recovered_positions').fetchall(),[(1,2,15,18,12,55)])
            self.assertEqual(b.execute('SELECT * FROM recovered_positions').fetchall(),[(1,2,4,110,70,56)])
            for (name,) in a.execute("SELECT name FROM sqlite_master WHERE type='table'"):
                if name=='recovered_positions':continue
                query='SELECT * FROM "'+name.replace('"','""')+'"'
                self.assertEqual(sorted(a.execute(query).fetchall(),key=repr),sorted(b.execute(query).fetchall(),key=repr),name)
        log=(run/'cpp-server.log').read_text()
        self.assertEqual(log.count('DIAGNOSTIC_RETURN_TOWN_COMMITTED'),1)
        self.assertEqual(log.count('DIAGNOSTIC_TOWN_SCENE_CONTEXT_ACCEPTED'),1)
        self.assertEqual(log.count('DIAGNOSTIC_TOWN_GUIDES_SENT'),1)
        self.assertLess(log.index('DIAGNOSTIC_TOWN_SCENE_CONTEXT_ACCEPTED'),log.index('DIAGNOSTIC_TOWN_GUIDES_SENT'))
        self.assertNotIn('policy or response rejected',log)

    def test_return_walk_and_fresh_reconnect_preserve_all_other_state(self):
        root=Path(__file__).resolve().parents[2]/'artifacts/runs'
        source=root/'native-town-indoor-walk-20260921-01'
        walk=root/'native-indoor-town-walk-20260921-01'
        reconnect=root/'native-indoor-town-walk-relogin-20260921-01'
        report=json.loads((walk/'run.json').read_text())
        fresh=json.loads((reconnect/'run.json').read_text())
        self.assertEqual(report['result'],'NATIVE_DURABLE_RETURN_AND_MOVEMENT_COMPLETED')
        self.assertEqual(fresh['result'],'NATIVE_TOWN_COMPLETED_QUEST_RESTORED')
        self.assertIsNone(report.get('error'));self.assertIsNone(fresh.get('error'))
        final=report['town_return_walk']
        snap=final['snapshot']
        self.assertEqual(tuple(snap[k] for k in ('area','scene','kind','x','y','ring_hex')),(2,4,0,111,70,'010102'))
        self.assertEqual(final['saved_position'],[1,2,4,111,70,57])
        step,=report['movement_steps']
        self.assertEqual((step['return_eax'],step['ack_hex'],step['ring_after_ack']),(1,'5d01','010102'))
        self.assertIn('b8c0245000ffd0',step['page']['hex'])
        self.assertLess(report['town_return_durable']['sequence'],report['town_scene_movement_ack']['sequence'])
        self.assertLess(report['town_scene_movement_ack']['sequence'],final['sequence'])
        restored=fresh['town_completed_world_snapshot']['snapshot']
        self.assertEqual(tuple(restored[k] for k in ('area','scene','kind','x','y','ring_hex')),(2,4,0,111,70,'010001'))
        self.assertNotEqual(final['pid'],fresh['npc_conversation_final_frame']['pid'])
        for absent in ('town_scene_entry','movement_step','town_map_probe'):self.assertNotIn(absent,fresh)
        with sqlite3.connect((source/'town-diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as a, \
             sqlite3.connect((walk/'town-diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as b, \
             sqlite3.connect((reconnect/'town-diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as c:
            self.assertEqual(b.execute('SELECT * FROM recovered_positions').fetchall(),[(1,2,4,111,70,57)])
            schema="SELECT name,sql FROM sqlite_master WHERE type='table' ORDER BY name"
            self.assertEqual(b.execute(schema).fetchall(),c.execute(schema).fetchall())
            for name,_ in a.execute(schema):
                query='SELECT * FROM "'+name.replace('"','""')+'"'
                rows=sorted(b.execute(query).fetchall(),key=repr)
                self.assertEqual(rows,sorted(c.execute(query).fetchall(),key=repr),name)
                if name!='recovered_positions':self.assertEqual(rows,sorted(a.execute(query).fetchall(),key=repr),name)
        for run in (walk,reconnect):
            self.assertNotIn('policy or response rejected',(run/'cpp-server.log').read_text())

    def test_indoor_connection_cells_emit_movement_not_proven_transfer(self):
        root=Path(__file__).resolve().parents[2]/'artifacts/runs'
        run=root/'native-indoor-door-walk-20260921-01'
        source=root/'native-town-indoor-walk-20260921-01'
        report=json.loads((run/'run.json').read_text())
        self.assertEqual(report['result'],'NATIVE_INDOOR_CONNECTION_CELLS_VISITED')
        self.assertIsNone(report.get('error'))
        path=[[17,13],[16,14],[15,15],[14,16],[14,17],[15,18],[16,19],[16,20]]
        probe=report['door_probe']
        self.assertEqual(probe['path'],path)
        self.assertEqual(probe['index'],8)
        self.assertEqual(len(report['movement_steps']),8)
        self.assertEqual(len(probe['arrivals']),8)
        packets=[]
        folder=run/'crypto-private'
        start=report['indoor_reconnect_final']['sequence']
        for file in folder.glob('*.json'):
            meta=json.loads(file.read_text())
            if meta['sequence']<=start:continue
            plain=(folder/meta['plain_file']).read_bytes()
            wire=(folder/meta['wire_file']).read_bytes()
            self.assertTrue(meta['checksum_valid'])
            self.assertFalse(meta['brute_force_used'])
            self.assertEqual(hashlib.sha256(plain).hexdigest(),meta['plain_sha256'])
            self.assertEqual(hashlib.sha256(wire).hexdigest(),meta['wire_sha256'])
            self.assertEqual(int.from_bytes(plain[:2],'little'),len(plain))
            packets.append((meta,plain))
        packets.sort(key=lambda item:item[0]['sequence'])
        self.assertEqual(len(packets),16)
        self.assertEqual(len({meta['socket'] for meta,_ in packets}),1)
        for index,(point,step,arrival) in enumerate(zip(path,report['movement_steps'],probe['arrivals']),1):
            request,ack=packets[(index-1)*2:index*2]
            self.assertEqual((request[0]['direction'],request[0]['opcode']),('C2S',0x2e))
            self.assertEqual(request[1][2:-1],b'\x2e'+struct.pack('<HHBB',*point,index,0xc2))
            self.assertEqual((ack[0]['direction'],ack[0]['opcode']),('S2C',0x5d))
            self.assertEqual(ack[1][2:-1],bytes([0x5d,index]))
            ring=bytes([1,index,index+1]).hex()
            self.assertEqual((step['return_eax'],step['ack_hex'],step['ring_after_ack']),
                             (1,bytes([0x5d,index]).hex(),ring))
            self.assertIn('b8c0245000ffd0',step['page']['hex'])
            snap=arrival['snapshot']
            self.assertEqual([snap['x'],snap['y']],point)
            self.assertEqual((snap['area'],snap['scene'],snap['kind'],snap['ring_hex']),(2,15,2,ring))
            self.assertLess(request[0]['sequence'],ack[0]['sequence'])
            self.assertLess(ack[0]['sequence'],arrival['sequence'])
        final=report['door_probe_final']
        self.assertGreater(final['frame_counter'],probe['arrivals'][-1]['frame_counter'])
        self.assertEqual(final['snapshot'],probe['arrivals'][-1]['snapshot'])
        for absent in ('town_scene_entry','town_map_probe'):self.assertNotIn(absent,report)
        with sqlite3.connect((source/'town-diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as a, \
             sqlite3.connect((run/'town-diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as b:
            self.assertEqual(a.execute('SELECT * FROM recovered_positions').fetchall(),[(1,2,15,18,12,55)])
            self.assertEqual(b.execute('SELECT * FROM recovered_positions').fetchall(),[(1,2,15,16,20,63)])
            schema="SELECT name,sql FROM sqlite_master WHERE type='table' ORDER BY name"
            self.assertEqual(a.execute(schema).fetchall(),b.execute(schema).fetchall())
            for name,_ in a.execute(schema):
                if name=='recovered_positions':continue
                query='SELECT * FROM "'+name.replace('"','""')+'"'
                self.assertEqual(sorted(a.execute(query).fetchall(),key=repr),sorted(b.execute(query).fetchall(),key=repr),name)
        self.assertNotIn('policy or response rejected',(run/'cpp-server.log').read_text())

    def test_initial_rejected_followup_not_promoted(self):
        root=Path(__file__).resolve().parents[2]/'artifacts/runs'
        for suffix in ('01','02'):
            run=root/('native-town-scene-transfer-20260921-'+suffix)
            self.assertIn('closing: Recovered world policy or response rejected',
                          (run/'cpp-server.log').read_text())
        report=json.loads((root/'native-town-scene-transfer-20260921-02/run.json').read_text())
        self.assertEqual(report['result'],'TOOL_ERROR')
        self.assertIn('server rejected followup',report['error'])


if __name__ == '__main__':
    unittest.main()
