"""Retained own-server native town path evidence, not whole-world acceptance."""
import json
import csv
import io
import hashlib
from pathlib import Path
import sqlite3
import struct
import subprocess
import sys
import unittest
from contextlib import closing

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.strike_lab.current_login_command import town_movement_path_page
from tools.strike_lab.town_probe_route import east_detour,agreement_window


class CurrentTownRuntimeTests(unittest.TestCase):
    def test_native_full_town_quest_chain_on_one_connection(self):
        self.check_full_town_quest_chain('native-town-full-quest-chain-20260921-01',
                                       'NATIVE_TOWN_QUEST_THREE_STAGES_AND_REWARD_COMMITTED')

    def test_native_full_chain_then_map_use_on_same_connection(self):
        name='native-town-chain-map-20260921-02'
        self.check_full_town_quest_chain(name,'NATIVE_TOWN_MAP_CANDIDATE_PANEL_STATE_OBSERVED')
        run=ROOT/'artifacts/runs'/name
        result=json.loads((run/'run.json').read_text())
        order=[result[key]['sequence'] for key in ('town_reward_chain_completed',
            'town_map_request_return','town_map_control_entry','town_map_control_return','town_map_final_frame')]
        self.assertTrue(all(a<b for a,b in zip(order,order[1:])))
        before=result['town_map_control_entry']['snapshot']
        after=result['town_map_control_return']['snapshot']
        self.assertEqual((before['flags'],after['flags']),(0x11,0x21))
        self.assertEqual(before['slot0_hex'],after['slot0_hex'])
        self.assertEqual(result['town_map_request_return']['queued_hex'],'25c1150000')
        matched=[]
        for path in (run/'crypto-private').glob('*.json'):
            meta=json.loads(path.read_text())
            if meta.get('opcode') not in (0x25,0x3f):continue
            plain=(path.parent/meta['plain_file']).read_bytes()
            wire=(path.parent/meta['wire_file']).read_bytes()
            self.assertEqual(hashlib.sha256(plain).hexdigest(),meta['plain_sha256'])
            self.assertEqual(hashlib.sha256(wire).hexdigest(),meta['wire_sha256'])
            self.assertEqual(sum(v+0x3c for v in plain[:-1])&255,plain[-1])
            matched.append((meta['direction'],plain[2:-1].hex(),meta['socket']))
        socket=result['quest_confirm_transport']['socket']
        self.assertCountEqual(matched,[('C2S','25c1150000',socket),('S2C','3f0100',socket)])
        snapshots=[]
        for folder in (run,ROOT/'artifacts/runs/native-town-full-quest-chain-20260921-01'):
            with closing(sqlite3.connect((folder/'town-diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True)) as db:
                self.assertEqual(db.execute('pragma integrity_check').fetchall(),[('ok',)])
                tables=[row[0] for row in db.execute("select name from sqlite_master where type='table'")]
                snapshot={table:db.execute('select * from "'+table+'"').fetchall() for table in tables}
                # Each independent run applies migrations at its own wall-clock time.
                snapshot['schema_migrations']=db.execute(
                    'select version,name,sql_text from schema_migrations order by version').fetchall()
                snapshots.append(snapshot)
        self.assertEqual(snapshots[0],snapshots[1])

    def test_full_chain_map_reward_survives_cold_restore(self):
        root=ROOT/'artifacts/runs'
        run=root/'native-town-chain-map-restore-20260921-01'
        source=root/'native-town-chain-map-20260921-02'
        result=json.loads((run/'run.json').read_text())
        old=json.loads((source/'run.json').read_text())
        self.assertIsNone(result.get('error'))
        self.assertEqual(result['result'],'NATIVE_TOWN_MAP_CANDIDATE_PANEL_STATE_OBSERVED')
        self.assertNotEqual(result['world_initializer']['pid'],old['world_initializer']['pid'])
        restored=result['journal_restore_returns']
        self.assertEqual(len(restored),15)
        self.assertEqual(restored[-1]['slots_hex'],'00'*60)
        slot=bytes.fromhex(result['town_reward_inventory']['record_hex'])
        self.assertEqual((slot[0],int.from_bytes(slot[4:6],'little')),(1,5569))
        self.assertEqual(result['town_map_request_return']['queued_hex'],'25c1150000')
        before=result['town_map_control_entry']['snapshot']
        after=result['town_map_control_return']['snapshot']
        self.assertEqual((before['flags'],after['flags']),(0x11,0x21))
        self.assertEqual(before['slot0_hex'],after['slot0_hex'])
        self.assertGreater(result['town_map_final_frame']['sequence'],result['town_map_control_return']['sequence'])
        log=(run/'diagnostic-server.log').read_text()
        self.assertNotIn('reward=CUSTOM-0022:item5569x1',log)
        self.assertNotIn('policy or response rejected',log)
        packets=[]
        for path in (run/'crypto-private').glob('*.json'):
            meta=json.loads(path.read_text())
            if meta.get('opcode') not in (0x25,0x3f):continue
            plain=(path.parent/meta['plain_file']).read_bytes()
            wire=(path.parent/meta['wire_file']).read_bytes()
            self.assertEqual(hashlib.sha256(plain).hexdigest(),meta['plain_sha256'])
            self.assertEqual(hashlib.sha256(wire).hexdigest(),meta['wire_sha256'])
            self.assertEqual(sum(v+0x3c for v in plain[:-1])&255,plain[-1])
            packets.append((meta['direction'],plain[2:-1].hex(),meta['socket']))
        socket=result['quest_confirm_transport']['socket']
        self.assertCountEqual(packets,[('C2S','25c1150000',socket),('S2C','3f0100',socket)])
        manifest=json.loads((run/'town-restore.json').read_text())
        original=source/'town-diagnostic-accounts.db'
        self.assertEqual(Path(manifest['source']).resolve(),original.resolve())
        self.assertEqual(hashlib.sha256(original.read_bytes()).hexdigest(),manifest['source_sha256'])
        snapshots=[]
        for folder in (source,run):
            with closing(sqlite3.connect((folder/'town-diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True)) as db:
                self.assertEqual(db.execute('pragma integrity_check').fetchall(),[('ok',)])
                tables=[row[0] for row in db.execute("select name from sqlite_master where type='table'")]
                snapshots.append({table:db.execute('select * from "'+table+'"').fetchall() for table in tables})
        self.assertEqual(snapshots[0],snapshots[1])

    def check_full_town_quest_chain(self,name,outcome):
        run=ROOT/'artifacts/runs'/name
        result=json.loads((run/(name+'-result.json')).read_text())
        self.assertIsNone(result.get('error'))
        self.assertEqual(result['result'],outcome)
        self.assertEqual(len(result['town_completed_conversations']),2)
        conversations=result['town_completed_conversations']+[result]
        sockets=[]
        last=0
        for stage,(evidence,target,pages,value) in enumerate(zip(conversations,(1606,1607,1606),(7,5,7),(0x10001,0x20001,0))):
            request=evidence['npc_request_transport'];confirm=evidence['quest_confirm_transport']
            self.assertEqual(request['logical_hex'],(b'\x37'+struct.pack('<I',target)).hex())
            self.assertEqual(evidence['quest_dialogue_header']['request_word'],0x1234+stage)
            self.assertEqual(bytes.fromhex(confirm['logical_hex'])[:6],b'\x85'+struct.pack('<HHB',0x1234+stage,2,0x9a))
            self.assertEqual([p['page_index'] for p in evidence['town_dialogue_page_returns']],list(range(1,pages)))
            self.assertEqual(evidence['npc_journal_entry']['a1'],value)
            self.assertEqual(evidence['npc_journal_return']['slots_hex'],(struct.pack('<I',value)+bytes(56)).hex())
            self.assertLess(last,request['sequence'])
            self.assertLess(confirm['sequence'],evidence['npc_journal_return']['sequence'])
            last=evidence['npc_conversation_final_frame']['sequence']
            sockets.extend((request['socket'],confirm['socket']))
        self.assertEqual(len(set(sockets)),1)
        slot=bytes.fromhex(result['town_reward_inventory']['record_hex'])
        self.assertEqual((slot[0],int.from_bytes(slot[4:6],'little')),(1,5569))
        log=(run/'diagnostic-server.log').read_text()
        self.assertEqual(log.count('DIAGNOSTIC_TOWN_PROGRESS_CONFIRMED'),3)
        self.assertEqual(log.count('reward=CUSTOM-0022:item5569x1'),1)
        self.assertNotIn('policy or response rejected',log)
        source=ROOT/'artifacts/runs/native-town-full-chain-fixture-20260921-01/town-diagnostic-accounts.db'
        with closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)) as baseline, closing(sqlite3.connect((run/'town-diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True)) as db:
            self.assertEqual(db.execute('SELECT stage,journal_description,revision FROM diagnostic_town_guide_progress').fetchall(),[(3,0,3)])
            self.assertEqual(db.execute('SELECT item_id,count,revision FROM diagnostic_inventory_slots').fetchall(),[(5569,1,2)])
            self.assertEqual(db.execute('SELECT item_id,count,slot_revision,progress_revision FROM diagnostic_town_guide_reward').fetchall(),[(5569,1,2,3)])
            allowed={'schema_migrations','native_data_sources','native_quest_descriptions','diagnostic_inventory_slots'}
            for (table,) in baseline.execute("SELECT name FROM sqlite_master WHERE type='table'"):
                if table not in allowed:
                    self.assertEqual(db.execute('SELECT * FROM "'+table+'"').fetchall(),baseline.execute('SELECT * FROM "'+table+'"').fetchall(),table)

    def test_native_map_panel_matches_current_island_map_asset(self):
        from tools.strike_lab.omega_assets import decode_csvz
        from tools.strike_lab.current_four_stat_ui_binding import parse_rom,select_action
        raw=(ROOT.parent/'God2/Data3/Flow/Island01Map.ROMZ').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),'b4806bf65a45b3b07a9f8cb3e2c30a8c86579948154531b0f02ebd6e830064d3')
        plain=decode_csvz(raw,limit=16*1024*1024)
        self.assertEqual(hashlib.sha256(plain).hexdigest(),'de22ae7038a1d03ad2ccd943e793ff46f7ba8312fb776033f8c4e680c52cc4b0')
        rom=parse_rom(plain,name_encoding='cp950')
        self.assertEqual((len(rom['actions']),len(rom['images']),len(rom['palettes'])),(8,8,8))
        action=rom['actions'][7]
        self.assertEqual(action['name'],'\u6953\u83ef\u93ae\u5927\u5730\u5716')
        self.assertEqual(action['meta'],(10070,0,400,300,1,1))
        selected,art=select_action(rom,7)
        self.assertEqual((selected['image_index'],selected['palette_index']),(7,4))
        self.assertEqual(art.size,(800,600))
        self.assertEqual(selected['pixels_sha256'],'00473a9a3a22c385af144d663e0f6ec1df2b21af9804ae836c8e5130df48ef07')
        self.assertEqual(selected['palette_sha256'],'4d3d847d383e515cb552b3f569e4b3ac60e08f8340e12ce067a2dfd921e60540')
        from PIL import Image
        with Image.open(io.BytesIO(rom['images'][7]['data'])) as independent:
            independent.load()
            self.assertEqual(independent.size,art.size)
            self.assertEqual(independent.tobytes(),art.tobytes())
        name='native-town-map-resource-20260921-01'
        run=ROOT/'artifacts/runs'/name
        result=json.loads((run/(name+'-result.json')).read_text())
        self.assertIsNone(result.get('error'))
        self.assertEqual(result['result'],'NATIVE_TOWN_MAP_CANDIDATE_PANEL_STATE_OBSERVED')
        snapshot=result['town_map_control_return']['snapshot']
        metadata=snapshot['scene_map_metadata']
        image=(ROOT/'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin').read_bytes()
        self.assertEqual(hashlib.sha256(image).hexdigest(),'149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763')
        rva=metadata['pointer']-0x400000
        self.assertEqual(rva,0x18b8d4)
        header=bytes.fromhex(metadata['header_hex'])
        self.assertEqual(header,image[rva:rva+0x28])
        self.assertEqual(header[:16].split(b'\0')[0],b'CityI1')
        self.assertEqual(struct.unpack_from('<3H',header,0x20),(47,5,7))
        node=bytes.fromhex(snapshot['node_header_hex'])
        self.assertEqual(struct.unpack_from('<H',node,2)[0],47)
        render=snapshot['render_object']
        self.assertEqual(struct.unpack_from('<H',node,4)[0],render['handle'])
        self.assertGreater(render['bank'],0)
        self.assertGreater(render['action'],0)
        self.assertEqual(bytes.fromhex(render['action_header_hex'])[:44],action['data'][:44])
        self.assertEqual(struct.unpack_from('<I',bytes.fromhex(render['bank_header_hex']),4)[0],8)
        self.assertEqual(result['town_map_control_entry']['snapshot']['flags'],0x11)
        self.assertEqual(snapshot['flags'],0x21)

    def test_native_map_candidate_round_trip_preserves_save(self):
        name='native-town-map-candidate-20260921-01'
        run=ROOT/'artifacts/runs'/name
        result=json.loads((run/(name+'-result.json')).read_text())
        self.assertIsNone(result.get('error'))
        self.assertEqual(result['result'],'NATIVE_TOWN_MAP_CANDIDATE_PANEL_STATE_OBSERVED')
        self.assertEqual(result['town_map_request_return']['queued_hex'],'25c1150000')
        before=result['town_map_control_entry']['snapshot']
        after=result['town_map_control_return']['snapshot']
        self.assertEqual((before['panel'],before['flags'],after['flags']),(1,0x11,0x21))
        self.assertEqual(before['node'],after['node'])
        self.assertEqual(before['slot0_hex'],after['slot0_hex'])
        old=bytes.fromhex(before['node_header_hex']);new=bytes.fromhex(after['node_header_hex'])
        self.assertEqual(old[1:],new[1:])
        self.assertEqual(struct.unpack_from('<H',old,2)[0],47)
        order=[result[k]['sequence'] for k in ('town_map_request_return','town_map_control_entry',
                                              'town_map_control_return','town_map_final_frame')]
        self.assertTrue(all(a<b for a,b in zip(order,order[1:])))
        sockets=[]
        for file,direction,expected in (('packet-0401.json','C2S','25c1150000'),
                                        ('packet-0411.json','S2C','3f0100')):
            path=run/'crypto-private'/file
            data=json.loads(path.read_text())
            plain=(path.parent/data['plain_file']).read_bytes()
            wire=(path.parent/data['wire_file']).read_bytes()
            self.assertEqual(data['direction'],direction)
            self.assertEqual(hashlib.sha256(plain).hexdigest(),data['plain_sha256'])
            self.assertEqual(hashlib.sha256(wire).hexdigest(),data['wire_sha256'])
            self.assertEqual(plain[2:-1].hex(),expected)
            sockets.append(data['socket'])
        self.assertEqual(sockets[0],sockets[1])
        snapshots=[]
        for directory in (ROOT/'artifacts/runs/native-town-quest-reward-20260921-01',run):
            with closing(sqlite3.connect((directory/'town-diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True)) as db:
                tables=[r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
                snapshots.append({t:db.execute('SELECT * FROM "'+t+'"').fetchall() for t in tables})
        self.assertEqual(snapshots[0],snapshots[1])

    def test_native_town_reward_and_reconnect_without_duplicate(self):
        names=('native-town-quest-reward-20260921-01',
               'native-town-quest-reward-reconnect-20260921-01')
        snapshots=[]
        for index,name in enumerate(names):
            run=ROOT/'artifacts/runs'/name
            result=json.loads((run/(name+'-result.json')).read_text())
            self.assertIsNone(result.get('error'))
            self.assertEqual(result['result'],('NATIVE_TOWN_QUEST_REWARD_OCCUPANCY_OBSERVED',
                                              'NATIVE_TOWN_COMPLETED_QUEST_RESTORED')[index])
            self.assertEqual(result['npc_journal_return']['slots_hex'],'00'*60)
            self.assertEqual(len(result['journal_restore_returns']),15)
            restored=bytes.fromhex(result['journal_restore_returns'][-1]['slots_hex'])
            self.assertEqual(restored,struct.pack('<I',0 if index else 0x20001)+bytes(56))
            slot=bytes.fromhex(result['town_reward_inventory']['record_hex'])
            self.assertEqual(len(slot),24)
            self.assertEqual((slot[0],int.from_bytes(slot[4:6],'little')),(1,5569))
            self.assertGreater(result['town_reward_inventory']['sequence'],result['npc_journal_return']['sequence'])
            with closing(sqlite3.connect((run/'town-diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True)) as db:
                self.assertEqual(db.execute('SELECT stage,journal_description,revision FROM diagnostic_town_guide_progress').fetchall(),[(3,0,3)])
                self.assertEqual(db.execute('SELECT slot,item_id,count,revision FROM diagnostic_inventory_slots').fetchall(),[(0,5569,1,2)])
                self.assertEqual(db.execute('SELECT progress_revision,slot,slot_revision,item_id,count,design_id FROM diagnostic_town_guide_reward').fetchall(),[(3,0,2,5569,1,'CUSTOM-0022')])
                tables=[r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
                snapshots.append({table:db.execute('SELECT * FROM "'+table+'"').fetchall() for table in tables})
        self.assertEqual(snapshots[0],snapshots[1], 'Reconnect changed saved tables or granted another reward')

    def test_native_loaded_map_item_matches_current_definition(self):
        from tools.strike_lab.omega_assets import decode_csvz
        from tools.strike_lab.recover_items import lines_of,section
        raw=(ROOT.parent/'God2/Data2/Patch/Comm/gamedata.csvZ').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
                         '70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731')
        definitions=section(lines_of(decode_csvz(raw)),b'SPI')
        matches=[(line,row) for line,row in definitions if row.split(b',')[0]==b'5569']
        self.assertEqual(len(matches),1)
        line,row=matches[0]
        self.assertEqual(line,8236)
        fields=row.split(b',')
        self.assertEqual(fields[2],b'Spi01069')
        self.assertEqual(fields[4].decode('cp950'),'\u91d1\u9c32\u5cf6\u5730\u5340\u5730\u5716')
        name='native-town-map-item-catalog-20260921-01'
        result=json.loads((ROOT/'artifacts/runs'/name/(name+'-result.json')).read_text())
        self.assertIsNone(result.get('error'))
        self.assertEqual(result['result'],'NATIVE_TOWN_NPC_CONVERSATION_CONFIRMED')
        item=result['town_reward_item']
        self.assertEqual(item['item_id'],5569)
        self.assertGreater(item['pointer'],0)
        self.assertEqual(item['resource'],result['quest_text_table']['resource'])
        record=bytes.fromhex(item['record_hex'])
        self.assertEqual(len(record),0x18c)
        self.assertEqual(record[8:46].split(b'\0')[0],fields[4])
        self.assertEqual(struct.unpack_from('<II',record),tuple(map(int,fields[5:7])))
        for index in range(6):
            offset=46+38*index
            self.assertEqual(record[offset:offset+38].split(b'\0')[0],fields[7+index])
        self.assertEqual(struct.unpack_from('<H',record,0x112)[0],int(fields[13]))
        self.assertEqual(struct.unpack_from('<H',record,0x114)[0],int(fields[3]))
        flags=[int(v) if v else 0 for v in fields[14:26]]
        self.assertEqual(record[0x11a],sum((v&1)<<i for i,v in enumerate(flags[:8])))
        self.assertEqual(record[0x11b]&15,sum((v&1)<<i for i,v in enumerate(flags[8:])))
        # Resource group/action can be rebound at load; don't label live slots
        # as source IDs or infer a reward count/effect implementation from them.

    def test_native_two_stage_quest_on_one_connection(self):
        name='native-town-quest-chain-20260921-01'
        run=ROOT/'artifacts/runs'/name
        result=json.loads((run/(name+'-result.json')).read_text())
        self.assertEqual(result['result'],'NATIVE_TOWN_QUEST_TWO_STAGES_COMMITTED')
        self.assertIsNone(result.get('error'))
        self.assertEqual(len(result['town_completed_conversations']),1)
        first=result['town_completed_conversations'][0]
        sockets=[]
        for evidence,target,word,value,pages in ((first,1606,0x1234,0x10001,7),
                                                (result,1607,0x1235,0x20001,5)):
            request=evidence['npc_request_transport'];confirm=evidence['quest_confirm_transport']
            self.assertEqual(request['logical_hex'],(b'\x37'+struct.pack('<I',target)).hex())
            self.assertEqual(bytes.fromhex(confirm['logical_hex'])[:6],b'\x85'+struct.pack('<HHB',word,2,0x9a))
            sockets.extend((request['socket'],confirm['socket']))
            self.assertEqual([p['page_index'] for p in evidence['town_dialogue_page_returns']],list(range(1,pages)))
            self.assertEqual(evidence['npc_journal_entry']['a1'],value)
            self.assertEqual(evidence['npc_journal_return']['slots_hex'],(struct.pack('<I',value)+bytes(56)).hex())
            self.assertLess(confirm['sequence'],evidence['npc_journal_entry']['sequence'])
            self.assertLess(evidence['npc_journal_return']['sequence'],evidence['npc_conversation_final_frame']['sequence'])
        self.assertEqual(len(set(sockets)),1)
        self.assertLess(first['npc_conversation_final_frame']['sequence'],result['npc_before_request']['sequence'])
        log=(run/'diagnostic-server.log').read_text()
        self.assertEqual(log.count('DIAGNOSTIC_TOWN_PROGRESS_CONFIRMED'),2)
        self.assertEqual(log.count('DIAGNOSTIC_TOWN_GUIDES_SENT'),1)
        self.assertNotIn('policy or response rejected',log)
        with closing(sqlite3.connect((run/'town-diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True)) as db:
            self.assertEqual(db.execute('SELECT character_id,stage,journal_description,revision FROM diagnostic_town_guide_progress').fetchall(),[(1,2,2,2)])
            self.assertEqual(db.execute('SELECT character_id,area,scene,x,y,revision FROM recovered_positions').fetchall(),[(1,2,4,110,70,53)])
            self.assertEqual(db.execute('SELECT count(*) FROM diagnostic_quest_journal').fetchone(),(0,))

    def test_native_quest_reconnect_restores_then_commits_second_stage(self):
        name='native-town-quest-reconnect-visit-20260921-01'
        run=ROOT/'artifacts/runs'/name
        result=json.loads((run/(name+'-result.json')).read_text())
        self.assertEqual(result['result'],'NATIVE_TOWN_QUEST_VISIT_COMMITTED')
        self.assertIsNone(result.get('error'))
        restores=result['journal_restore_returns']
        self.assertEqual([p['slot'] for p in restores],list(range(15)))
        self.assertEqual([p['value'] for p in restores],[0x10001]+[0]*14)
        self.assertEqual(restores[-1]['slots_hex'],(struct.pack('<I',0x10001)+bytes(56)).hex())
        self.assertLess(restores[-1]['sequence'],result['npc_before_request']['sequence'])
        self.assertEqual(result['npc_request_transport']['logical_hex'],'3747060000')
        self.assertEqual([p['page_index'] for p in result['town_dialogue_page_returns']],list(range(1,5)))
        entry=result['npc_journal_entry'];returned=result['npc_journal_return']
        self.assertEqual((entry['a0'],entry['a1']),(0,0x20001))
        self.assertEqual(returned['sp'],entry['sp']+12)
        self.assertEqual(returned['slots_hex'],(struct.pack('<I',0x20001)+bytes(56)).hex())
        self.assertLess(result['quest_confirm_transport']['sequence'],entry['sequence'])
        self.assertLess(returned['sequence'],result['npc_conversation_final_frame']['sequence'])
        log=(run/'diagnostic-server.log').read_text()
        for marker in ('DIAGNOSTIC_TOWN_JOURNAL_RESTORE','DIAGNOSTIC_TOWN_PROGRESS_CONFIRMED'):
            self.assertEqual(log.count(marker),1)
        self.assertIn('stage=2 no_rewards',log)
        self.assertNotIn('policy or response rejected',log)
        source=ROOT/'artifacts/runs/native-town-quest-accept-20260921-01/town-diagnostic-accounts.db'
        manifest=json.loads((run/'town-restore.json').read_text())
        self.assertEqual(manifest['source_sha256'],hashlib.sha256(source.read_bytes()).hexdigest())
        with closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)) as baseline, \
             closing(sqlite3.connect((run/'town-diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True)) as current:
            self.assertEqual(current.execute('SELECT character_id,stage,journal_description,revision FROM diagnostic_town_guide_progress').fetchall(),[(1,2,2,2)])
            tables=baseline.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
            self.assertEqual(tables,current.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall())
            for (table,) in tables:
                if table=='diagnostic_town_guide_progress':continue
                query='SELECT * FROM "'+table.replace('"','""')+'"'
                self.assertEqual(baseline.execute(query).fetchall(),current.execute(query).fetchall(),table)

    def test_native_town_quest_acceptance_persists_and_projects(self):
        name='native-town-quest-accept-20260921-01'
        run=ROOT/'artifacts/runs'/name
        result=json.loads((run/(name+'-result.json')).read_text())
        self.assertEqual(result['result'],'NATIVE_TOWN_QUEST_ACCEPTED')
        self.assertIsNone(result.get('error'))
        settings=json.loads((run/'diagnostic-server-config.json').read_text())
        self.assertTrue(settings['development']['diagnostic_town']['quest_progress'])
        self.assertEqual(result['npc_request_transport']['logical_hex'],'3746060000')
        self.assertEqual(bytes.fromhex(result['quest_confirm_transport']['logical_hex'])[:6],bytes.fromhex('85341202009a'))
        self.assertEqual(result['npc_request_transport']['socket'],result['quest_confirm_transport']['socket'])
        self.assertEqual([p['page_index'] for p in result['town_dialogue_page_returns']],list(range(1,7)))
        entry=result['npc_journal_entry'];returned=result['npc_journal_return']
        self.assertEqual((entry['a0'],entry['a1']),(0,0x10001))
        self.assertEqual(returned['sp'],entry['sp']+12)
        before=bytes.fromhex(entry['slots_hex']);after=bytes.fromhex(returned['slots_hex'])
        self.assertEqual(after[:4],struct.pack('<I',0x10001))
        self.assertEqual(after[4:],before[4:])
        self.assertLess(result['quest_confirm_transport']['sequence'],entry['sequence'])
        self.assertLess(entry['sequence'],returned['sequence'])
        self.assertLess(returned['sequence'],result['npc_conversation_final_frame']['sequence'])
        log=(run/'diagnostic-server.log').read_text()
        self.assertEqual(log.count('DIAGNOSTIC_TOWN_PROGRESS_CONFIRMED'),1)
        self.assertIn('stage=1 no_rewards',log)
        self.assertNotIn('policy or response rejected',log)
        source=ROOT/'artifacts/runs/native-town-cross-window-20260921-01/town-diagnostic-accounts.db'
        manifest=json.loads((run/'town-restore.json').read_text())
        self.assertEqual(manifest['source_sha256'],hashlib.sha256(source.read_bytes()).hexdigest())
        with closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)) as baseline, \
             closing(sqlite3.connect((run/'town-diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True)) as current:
            self.assertEqual(current.execute('SELECT character_id,stage,journal_description,revision,source_sha256,design_id FROM diagnostic_town_guide_progress').fetchall(),
                             [(1,1,1,1,'1ff497204b5cf77cbbccffdf1836d7aeee30e46980ac1e85d8d0a08a0a4bcda7','CUSTOM-0021')])
            tables=baseline.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
            self.assertEqual(set(current.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()),
                             set(tables)|{('diagnostic_town_guide_progress',)})
            for (table,) in tables:
                # Explicit schema migration and pinned display import, not gameplay mutation.
                if table in ('schema_migrations','native_data_sources','native_quest_descriptions'):continue
                query='SELECT * FROM "'+table.replace('"','""')+'"'
                self.assertEqual(baseline.execute(query).fetchall(),current.execute(query).fetchall(),table)
            self.assertEqual(current.execute('SELECT count(*) FROM native_quest_descriptions').fetchone(),(2014,))

    def test_town_guide_native_text_table_and_pagination(self):
        from tools.strike_lab.omega_assets import decode_csvz
        from tools.strike_lab.current_quest_live import advance_or_confirm_page
        image=(ROOT/'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin').read_bytes()
        self.assertEqual(hashlib.sha256(image).hexdigest(),
                         '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763')
        self.assertEqual(struct.unpack_from('<I',image,0xc86cc+3*4)[0],0x4c85fe)
        self.assertEqual(image[0xc8600],0xe8)
        self.assertEqual(0xc8605+struct.unpack_from('<i',image,0xc8601)[0],0xc8750)
        for address,ui in ((0,1),(1,0),(0x100000000,1),(1,0xffffffff)):
            with self.assertRaises(ValueError):advance_or_confirm_page(address,ui)
        raw=(ROOT.parent/'God2/Data2/Patch/Comm/NPCMission01.csvZ').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
                         '1ff497204b5cf77cbbccffdf1836d7aeee30e46980ac1e85d8d0a08a0a4bcda7')
        rows=list(csv.reader(io.StringIO(decode_csvz(raw).decode('latin1'))))
        self.assertEqual(rows[1],['NPCMissionMessage','1000'])
        texts={int(row[0]):','.join(row[1:]).encode('latin1') for row in rows[2:] if row and row[0].isdigit()}
        for target,revision,key in ((1606,'02',894),(1607,'01',899)):
            name=f'native-town-guide-source-text-{target}-20260921-{revision}'
            result=json.loads((ROOT/'artifacts/runs'/name/(name+'-result.json')).read_text())
            self.assertIsNone(result.get('error'))
            entries=result['town_quest_texts']['entries']
            self.assertEqual([e['key'] for e in entries],list(range(894,902)))
            for entry in entries:
                expected=texts[entry['key']]
                self.assertEqual(bytes.fromhex(entry['text_hex']),expected)
                self.assertEqual(entry['length'],len(expected))
                self.assertTrue(entry['terminated'])
            payload=bytes.fromhex(result['quest_dialogue_entry']['payload_hex'])
            self.assertEqual(struct.unpack_from('<H',payload,6)[0],key)
            probe=result['quest_confirm_probe']
            page=probe['page']
            code,trap=advance_or_confirm_page(page['address'],result['quest_dialogue_entry']['ui'])
            self.assertEqual(page['hex'],code.hex())
            self.assertEqual(page['return_trap'],page['address']+trap)
            self.assertEqual(probe['page_index'],0)
            self.assertGreater(probe['page_count'],1)
            self.assertEqual(result['quest_confirm_return']['sp'],probe['entry_sp'])
            pages=result['town_dialogue_page_returns']
            self.assertEqual([p['page_index'] for p in pages],list(range(1,probe['page_count'])))
            for page in pages:
                self.assertEqual(page['page_count'],probe['page_count'])
                self.assertEqual(page['queued_length'],0)
                self.assertEqual(page['sp'],probe['entry_sp'])
            self.assertLess(pages[-1]['sequence'],result['quest_confirm_return']['sequence'])

    def test_both_town_guides_native_conversation_round_trip(self):
        from tools.strike_lab.recovered_packet_pipeline import OpcodeDispatcher
        source=ROOT/'artifacts/runs/native-town-cross-window-20260921-01/town-diagnostic-accounts.db'
        for target,variant,revision in ((1606,'dialogue','01'),(1607,'dialogue','01'),
                                        (1606,'source-text','02'),(1607,'source-text','01')):
            with self.subTest(target=target,variant=variant):
                name=f'native-town-guide-{variant}-{target}-20260921-{revision}'
                run=ROOT/'artifacts/runs'/name
                result=json.loads((run/(name+'-result.json')).read_text())
                self.assertEqual(result['result'],'NATIVE_TOWN_NPC_CONVERSATION_CONFIRMED')
                self.assertIsNone(result.get('error'))
                npc=result['npc_request_transport'];confirm=result['quest_confirm_transport']
                self.assertEqual(npc['socket'],confirm['socket'])
                self.assertEqual(npc['logical_hex'],(b'\x37'+struct.pack('<I',target)).hex())
                self.assertEqual(bytes.fromhex(confirm['logical_hex'])[:6],bytes.fromhex('85341202009a'))
                self.assertEqual(len(bytes.fromhex(confirm['logical_hex'])),7)
                self.assertEqual(result['quest_confirm_probe']['queued_before'],0)
                self.assertEqual(result['npc_request_probe']['action'],'NPC_REQUEST_96750_SELECTION_BYPASSED')
                self.assertEqual(result['quest_confirm_probe']['action'],
                                 'DIALOGUE_ADVANCE_OR_CONFIRM_NATIVE' if variant=='source-text' else 'DIALOGUE_CONFIRM_C8500')
                for prefix,transport,identity in (('npc_request',npc,'NPC_INTERACTION_REQUEST'),
                                                  ('quest_confirm',confirm,'QUEST_DIALOGUE_ACTION')):
                    self.assertEqual(result[prefix+'_return']['sp'],result[prefix+'_probe']['entry_sp'])
                    self.assertEqual(result[prefix+'_return']['queued_hex'],transport['logical_hex'])
                    path=run/transport['packet_evidence']
                    metadata=json.loads(path.read_text())
                    plain=(path.parent/metadata['plain_file']).read_bytes()
                    wire=(path.parent/metadata['wire_file']).read_bytes()
                    self.assertEqual(hashlib.sha256(plain).hexdigest(),metadata['plain_sha256'])
                    self.assertEqual(hashlib.sha256(wire).hexdigest(),metadata['wire_sha256'])
                    self.assertEqual(OpcodeDispatcher.identify(plain,'C2S')['identification'],identity)
                    self.assertEqual(plain[2:-1].hex(),transport['logical_hex'])
                sequence=[result['npc_before_request']['sequence'],npc['sequence'],
                          result['quest_dialogue_entry']['sequence'],result['quest_dialogue_header']['sequence'],
                          result['quest_dialogue_return']['sequence'],result['quest_confirm_return']['sequence'],
                          confirm['sequence'],result['npc_conversation_final_frame']['sequence']]
                self.assertTrue(all(a<b for a,b in zip(sequence,sequence[1:])))
                log=(run/'diagnostic-server.log').read_text()
                for marker in ('DIAGNOSTIC_TOWN_GUIDES_SENT','DIAGNOSTIC_NPC_REQUEST_ACCEPTED','DIAGNOSTIC_QUEST_CONFIRM_ACCEPTED'):
                    self.assertEqual(log.count(marker),1)
                self.assertIn(f'target={target} owned_saved_position_checked',log)
                self.assertNotIn('policy or response rejected',log)
                self.assertNotIn('npc_journal_return',result)
                self.assertNotIn('town_resource_probe',result)
                manifest=json.loads((run/'town-restore.json').read_text())
                self.assertEqual(manifest['source_sha256'],hashlib.sha256(source.read_bytes()).hexdigest())
                with closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)) as before, \
                     closing(sqlite3.connect((run/'town-diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True)) as after:
                    tables=before.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
                    self.assertEqual(tables,after.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall())
                    for (table,) in tables:
                        query='SELECT * FROM "'+table.replace('"','""')+'"'
                        self.assertEqual(before.execute(query).fetchall(),after.execute(query).fetchall(),table)

    def test_native_town_guide_allocation_preserves_saved_data(self):
        name='native-town-guides-spawn-20260921-01'
        run=ROOT/'artifacts/runs'/name
        result=json.loads((run/(name+'-result.json')).read_text())
        self.assertEqual(result['result'],'NATIVE_TOWN_GUIDES_ALLOCATED')
        self.assertFalse(result.get('error'))
        settings=json.loads((run/'diagnostic-server-config.json').read_text())
        self.assertTrue(settings['development']['diagnostic_town']['spawn_guides'])
        self.assertFalse(settings['development']['local_account_registration'])
        state=result['town_guides_after_spawn']
        entries=[e for pool in state['pools'] for e in pool['entries']]
        self.assertEqual(sorted((e['identity'],e['x'],e['y']) for e in entries),
                         [(1606,110,69),(1607,112,70)])
        self.assertEqual(result['town_guides_final_frame']['event_type'],'LIVE_WORLD_FRAME_RETURN')
        self.assertNotIn('town_resource_probe',result)
        resource=next(r for r in state['resources'] if r['ordinal']==19)
        self.assertGreaterEqual(resource['loaded_slot'],0)
        self.assertEqual(resource['path'].lower(),r'data2\rom\npc\npc2720.rom')
        log=(run/'diagnostic-server.log').read_text()
        self.assertEqual(log.count('DIAGNOSTIC_TOWN_GUIDES_SENT'),1)
        self.assertNotIn('policy or response rejected',log)
        source=ROOT/'artifacts/runs/native-town-cross-window-20260921-01/town-diagnostic-accounts.db'
        manifest=json.loads((run/'town-restore.json').read_text())
        self.assertEqual(manifest['source_sha256'],hashlib.sha256(source.read_bytes()).hexdigest())
        with closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)) as before, \
             closing(sqlite3.connect((run/'town-diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True)) as after:
            tables=before.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
            self.assertEqual(tables,after.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall())
            for (table,) in tables:
                query='SELECT * FROM "'+table.replace('"','""')+'"'
                self.assertEqual(before.execute(query).fetchall(),after.execute(query).fetchall(),table)

    def test_town_naturally_preloads_guide_resources(self):
        name='native-town-natural-npc-preload-20260921-01'
        run=ROOT/'artifacts/runs'/name
        result=json.loads((run/(name+'-result.json')).read_text())
        self.assertEqual(result['result'],'NATIVE_TOWN_SAVED_POSITION_RESTORED')
        self.assertFalse(result.get('error'))
        self.assertNotIn('town_resource_probe',result)
        self.assertNotIn('town_resource_return',result)
        state=result['npc_live_state']
        resources=[r for r in state['resources'] if r['ordinal']==19]
        self.assertEqual(len(resources),1)
        resource=resources[0]
        self.assertEqual(resource['path'].lower(),r'data2\rom\npc\npc2720.rom')
        self.assertGreaterEqual(resource['loaded_slot'],0)
        self.assertEqual((resource['action_count'],resource['palette']),(16,6))
        for selector in (1606,1607):
            template=next(t for t in state['templates'] if t['selector']==selector)
            self.assertEqual((template['flags'],template['appearance_code']),(0x4000,20))
            self.assertEqual(len(bytes.fromhex(template['record_hex'])),94)
        self.assertEqual(len(state['pools']),2)
        self.assertTrue(all(not pool['entries'] for pool in state['pools']))

    def test_original_client_moves_after_cold_restore(self):
        name='native-town-resumed-movement-20260921-01'
        run=ROOT/'artifacts/runs'/name
        result=json.loads((run/(name+'-result.json')).read_text())
        self.assertEqual(result['result'],'NATIVE_MOVEMENT_PATH_COMPLETED')
        self.assertFalse(result.get('error'))
        self.assertEqual(result['restored_town_position_hex'],struct.pack('<II',110,70).hex())
        self.assertEqual(result['restored_town_ring_hex'],'010001')
        self.assertEqual(len(result['movement_steps']),3)
        for index,step in enumerate(result['movement_steps'],1):
            x=111 if index%2 else 110
            self.assertEqual(step['town_target'],[x,70])
            self.assertEqual(step['ack_hex'],bytes((0x5d,index)).hex())
            self.assertEqual(step['ring_after_ack'],bytes((1,index,index+1)).hex())
            self.assertEqual(step['precondition']['position_hex'],struct.pack('<II',110 if index%2 else 111,70).hex())
            self.assertEqual(step['return_eax'],1)
            code,_=town_movement_path_page(step['page']['address'],step['world'],x,70)
            self.assertEqual(step['page']['hex'],code.hex())
        self.assertEqual(result['movement_completion']['position_hex'],struct.pack('<II',111,70).hex())
        self.assertEqual(result['movement_completion']['motion_state'],0)
        source=ROOT/'artifacts/runs/native-town-cross-window-20260921-01/town-diagnostic-accounts.db'
        manifest=json.loads((run/'town-restore.json').read_text())
        self.assertEqual(manifest['source_sha256'],hashlib.sha256(source.read_bytes()).hexdigest())
        with closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)) as before, \
             closing(sqlite3.connect((run/'town-diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True)) as after:
            self.assertEqual(after.execute('SELECT character_id,area,scene,x,y,revision FROM recovered_positions').fetchall(),
                             [(1,2,4,111,70,56)])
            tables=before.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
            self.assertEqual(tables,after.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall())
            for (table,) in tables:
                if table=='recovered_positions':continue
                query='SELECT * FROM "'+table.replace('"','""')+'"'
                self.assertEqual(before.execute(query).fetchall(),after.execute(query).fetchall(),table)

    def test_original_client_cold_restore_preserves_database(self):
        name='native-town-cold-restore-20260921-01'
        run=ROOT/'artifacts/runs'/name
        result=json.loads((run/(name+'-result.json')).read_text())
        self.assertEqual(result['result'],'NATIVE_TOWN_SAVED_POSITION_RESTORED')
        self.assertFalse(result.get('error'))
        self.assertEqual(result['restored_town_position_hex'],struct.pack('<II',110,70).hex())
        self.assertEqual(result['restored_town_ring_hex'],'010001')
        self.assertTrue(result['town_window_builds'])
        self.assertTrue(all(b['known_cell_mismatches']==0 for b in result['town_window_builds']))
        settings=json.loads((run/'diagnostic-server-config.json').read_text())
        self.assertFalse(settings['development']['local_account_registration'])
        manifest=json.loads((run/'town-restore.json').read_text())
        source=ROOT/'artifacts/runs/native-town-cross-window-20260921-01/town-diagnostic-accounts.db'
        self.assertEqual(Path(manifest['source']).resolve(),source.resolve())
        self.assertEqual(manifest['source_sha256'],hashlib.sha256(source.read_bytes()).hexdigest())
        target=run/'town-diagnostic-accounts.db'
        with closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)) as before, \
             closing(sqlite3.connect(target.as_uri()+'?mode=ro',uri=True)) as after:
            tables=before.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
            self.assertEqual(tables,after.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall())
            for (table,) in tables:
                query='SELECT * FROM "'+table.replace('"','""')+'"'
                self.assertEqual(before.execute(query).fetchall(),after.execute(query).fetchall(),table)

    def test_agreement_route_matches_compiled_server_cells(self):
        atlas=json.loads((ROOT/'artifacts/world-atlas/town-2-4.json').read_text())
        window=agreement_window(atlas)
        actual=subprocess.check_output([str(ROOT/'build/tests/Release/recovered-town-navigation.exe'),
                                        '--consistent-cells'],text=True,timeout=10).strip()
        self.assertEqual(window['cells_hex'],actual)
        route=east_detour(window,(63,64),110)
        self.assertEqual((len(route),route[-1]),(54,(110,70)))

    def test_native_grocery_approach_and_isolated_save(self):
        run=ROOT/'artifacts/runs/native-town-grocery-approach-20260921-01'
        report=json.loads((run/'run.json').read_text())
        self.assertEqual(report['result'],'NATIVE_TOWN_GROCERY_APPROACH_COMPLETED')
        self.assertIsNone(report.get('error'))
        atlas=json.loads((ROOT/'artifacts/world-atlas/town-2-4.json').read_text())
        path=east_detour(agreement_window(atlas),(111,70),86,71)[1:]
        self.assertEqual(report['door_probe']['path'],[list(p) for p in path])
        self.assertEqual(report['door_probe']['index'],26)
        self.assertEqual(len(report['movement_steps']),26)
        self.assertEqual(len(report['door_probe']['arrivals']),26)
        for index,(step,arrival,point) in enumerate(zip(report['movement_steps'],report['door_probe']['arrivals'],path),1):
            self.assertEqual(step['return_eax'],1)
            self.assertEqual(step['ack_hex'],bytes([0x5d,index]).hex())
            snap=arrival['snapshot']
            self.assertEqual((snap['area'],snap['scene'],snap['kind'],snap['x'],snap['y']), (2,4,0,*point))
            self.assertEqual(snap['ring_hex'],bytes([1,index,index+1]).hex())
        self.assertEqual(report['door_probe_final']['snapshot'],report['door_probe']['arrivals'][-1]['snapshot'])
        source=ROOT/'artifacts/runs/native-indoor-town-walk-20260921-01/town-diagnostic-accounts.db'
        with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as a, \
             sqlite3.connect((run/'town-diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as b:
            self.assertEqual(a.execute('SELECT * FROM recovered_positions').fetchall(),[(1,2,4,111,70,57)])
            self.assertEqual(b.execute('SELECT * FROM recovered_positions').fetchall(),[(1,2,4,86,71,83)])
            schema="SELECT name,sql FROM sqlite_master WHERE type='table' ORDER BY name"
            self.assertEqual(a.execute(schema).fetchall(),b.execute(schema).fetchall())
            for name,_ in a.execute(schema):
                if name=='recovered_positions':continue
                query='SELECT * FROM "'+name.replace('"','""')+'"'
                self.assertEqual(sorted(a.execute(query).fetchall(),key=repr),sorted(b.execute(query).fetchall(),key=repr),name)
        self.assertNotIn('policy or response rejected',(run/'cpp-server.log').read_text())

    def test_native_special_entry_is_accepted_movement_not_scene_transfer(self):
        run=ROOT/'artifacts/runs/native-town-special-entry-20260921-02'
        report=json.loads((run/'run.json').read_text())
        self.assertEqual(report['result'],'NATIVE_TOWN_SPECIAL_ENTRY_MOVEMENT_ACCEPTED')
        self.assertIsNone(report.get('error'))
        step=report['movement_step']
        self.assertEqual((step['return_eax'],step['ack_hex'],step['ring_after_ack']),(1,'5d1b','011b1c'))
        final=report['special_entry_final']
        snap=final['snapshot']
        self.assertEqual(tuple(snap[k] for k in ('area','scene','kind','x','y','ring_hex')),(2,4,0,86,70,'011b1c'))
        self.assertGreater(final['sequence'],report['special_entry_arrival']['sequence'])
        packets=[]
        folder=run/'crypto-private'
        for file in folder.glob('*.json'):
            meta=json.loads(file.read_text())
            if meta['sequence']<=report['door_probe_final']['sequence']:continue
            plain=(folder/meta['plain_file']).read_bytes()
            wire=(folder/meta['wire_file']).read_bytes()
            self.assertEqual(hashlib.sha256(plain).hexdigest(),meta['plain_sha256'])
            self.assertEqual(hashlib.sha256(wire).hexdigest(),meta['wire_sha256'])
            self.assertTrue(meta['checksum_valid'])
            self.assertFalse(meta['brute_force_used'])
            packets.append((meta['sequence'],meta['direction'],plain.hex()))
        packets.sort()
        self.assertEqual([(d,p) for _,d,p in packets if p!='0500300025'],
                         [('C2S','0a002e560046001bc2cd'),('S2C','05005d1b6d')])
        self.assertTrue(all(d=='C2S' for _,d,p in packets if p=='0500300025'))
        source=ROOT/'artifacts/runs/native-indoor-town-walk-20260921-01/town-diagnostic-accounts.db'
        with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as a, \
             sqlite3.connect((run/'town-diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as b:
            self.assertEqual(b.execute('SELECT * FROM recovered_positions').fetchall(),[(1,2,4,86,70,84)])
            for (name,) in a.execute("SELECT name FROM sqlite_master WHERE type='table'"):
                if name=='recovered_positions':continue
                query='SELECT * FROM "'+name.replace('"','""')+'"'
                self.assertEqual(sorted(a.execute(query).fetchall(),key=repr),sorted(b.execute(query).fetchall(),key=repr),name)
        self.assertNotIn('policy or response rejected',(run/'cpp-server.log').read_text())

    def test_grocery_approach_keeps_special_entry_cell_separate(self):
        atlas=json.loads((ROOT/'artifacts/world-atlas/town-2-4.json').read_text())
        window=agreement_window(atlas)
        route=east_detour(window,(111,70),86,71)
        self.assertEqual((len(route),route[0],route[-1]),(27,(111,70),(86,71)))
        for x,y in route:
            self.assertEqual(window['cells_hex'][(y*189+x)*2:(y*189+x)*2+2],'01')
        for a,b in zip(route,route[1:]):self.assertEqual(abs(a[0]-b[0])+abs(a[1]-b[1]),1)
        self.assertEqual(window['cells_hex'][(70*189+86)*2:(70*189+86)*2+2],'02')
        with self.assertRaises(ValueError):east_detour(window,(111,70),86,70)
        with self.assertRaises(ValueError):east_detour(window,(111,70),86,189)

    def test_detour_itinerary_uses_only_known_cardinal_cells(self):
        atlas=json.loads((ROOT/'artifacts/world-atlas/town-2-4.json').read_text())
        window=atlas['windows'][30]
        route=east_detour(window,(63,64))
        self.assertEqual((len(route),route[-1]),(44,(100,70)))
        for x,y in route:
            offset=((y-window['origin_y'])*63+x-window['origin_x'])*2
            self.assertEqual(window['cells_hex'][offset:offset+2],'01')
        for a,b in zip(route,route[1:]):self.assertEqual(abs(a[0]-b[0])+abs(a[1]-b[1]),1)
        for target in (-1,105):
            with self.assertRaises(ValueError):east_detour(window,(63,64),target)
        with self.assertRaises(ValueError):east_detour(window,(90,64))

    def test_path_thunk_arguments_and_bounds(self):
        for x,y in ((0,0),(63,64),(128,188),(188,128)):
            code,trap=town_movement_path_page(0x2000000,0x3000000,x,y)
            self.assertEqual(code[:10],b'\x68'+struct.pack('<I',y)+b'\x68'+struct.pack('<I',x))
            self.assertEqual(code[10:15],b'\xb9'+struct.pack('<I',0x3000000))
            self.assertEqual(code[15:22],b'\xb8'+struct.pack('<I',0x5024c0)+b'\xff\xd0')
            self.assertEqual(code[trap:],b'\xcc\x0f\x0b')
        for value in (-1,189,2**32,1.5,True):
            with self.assertRaises(ValueError):town_movement_path_page(0x2000000,0x3000000,value,64)
            with self.assertRaises(ValueError):town_movement_path_page(0x2000000,0x3000000,63,value)

    def test_retained_native_path_and_durable_position(self):
        self.check_run('native-town-movement-20260921-01',3,False)

    def test_retained_east_path_crosses_coordinate_block_boundary(self):
        self.check_run('native-town-east-path-20260921-01',26,True)

    def test_native_detour_rebuild_and_ring_wrap(self):
        name='native-town-detour-20260921-02'
        self.check_run(name,43,True)
        result=json.loads((ROOT/'artifacts/runs'/name/(name+'-result.json')).read_text())
        self.assertEqual([b['center'] for b in result['town_window_builds']],[[3,3],[4,3]])
        self.assertTrue(all(b['known_cell_mismatches']==0 for b in result['town_window_builds']))

    def test_native_path_beyond_initial_window(self):
        name='native-town-cross-window-20260921-01'
        self.check_run(name,53,True)
        run=ROOT/'artifacts/runs'/name
        settings=json.loads((run/'diagnostic-server-config.json').read_text())
        self.assertTrue(settings['development']['diagnostic_town']['source_consensus'])
        result=json.loads((run/(name+'-result.json')).read_text())
        self.assertEqual(result['town_route'][-1],[110,70])
        self.assertGreater(result['town_route'][-1][0],104)
        self.assertTrue(all(b['known_cell_mismatches']==0 for b in result['town_window_builds']))

    def test_observed_native_window_build_matches_static_source(self):
        name='native-town-streaming-20260921-01'
        self.check_run(name,26,True)
        result=json.loads((ROOT/'artifacts/runs'/name/(name+'-result.json')).read_text())
        builds=result['town_window_builds']
        self.assertEqual(len(builds),1)
        self.assertEqual(builds[0]['center'],[3,3])
        self.assertEqual(builds[0]['origin'],[63,63])
        self.assertEqual(builds[0]['known_cell_mismatches'],0)
        self.assertGreater(builds[0]['return_sequence'],builds[0]['entry_sequence'])

    def test_camera_moves_while_window_origin_stays_fixed(self):
        name='native-town-camera-state-20260921-01'
        self.check_run(name,26,True)
        result=json.loads((ROOT/'artifacts/runs'/name/(name+'-result.json')).read_text())
        cameras=[]
        managers=set()
        for step in result['movement_steps']:
            state=step['precondition']['town_navigation']
            managers.add(state['manager'])
            self.assertEqual((state['kind'],state['mode'],state['origin']),(0,5,[63,63]))
            cameras.append(struct.unpack('<ii',bytes.fromhex(state['camera_hex'])))
        self.assertEqual(len(managers),1)
        self.assertEqual(cameras[0],(-320,140))
        for before,after in zip(cameras,cameras[1:]):
            self.assertEqual((after[0]-before[0],after[1]-before[1]),(40,-20))
        self.assertEqual(len(result['town_window_builds']),1)

    def check_run(self,name,count,east):
        run=ROOT/'artifacts/runs'/name
        result=json.loads((run/(name+'-result.json')).read_text())
        self.assertEqual(result['result'],'NATIVE_MOVEMENT_PATH_COMPLETED')
        self.assertFalse(result.get('error'))
        self.assertEqual(len(result['movement_steps']),count)
        route=result.get('town_route')
        for index,step in enumerate(result['movement_steps'],1):
            self.assertEqual(step['return_eax'],1)
            self.assertEqual(step['ack_hex'],bytes((0x5d,index%40)).hex())
            self.assertEqual(step['ring_after_ack'],bytes((1,index%40,(index+1)%40)).hex())
            page=step['page']
            x=63+index if east else (64 if index%2 else 63)
            target=route[index] if route else [x,64]
            expected,_=town_movement_path_page(page['address'],step['world'],*target)
            self.assertEqual(page['hex'],expected.hex())
            before=63+index-1 if east else (63 if index%2 else 64)
            previous=route[index-1] if route else [before,64]
            self.assertEqual(step['precondition']['position_hex'],struct.pack('<II',*previous).hex())
            if east:self.assertEqual(step['town_target'],target)
        completion=result['movement_completion']
        final_x=63+count if east else (64 if count%2 else 63)
        final=route[-1] if route else [final_x,64]
        self.assertEqual(completion['position_hex'],struct.pack('<II',*final).hex())
        self.assertEqual(completion['motion_state'],0)
        database=run/'town-diagnostic-accounts.db'
        with closing(sqlite3.connect(database.as_uri()+'?mode=ro',uri=True)) as db:
            self.assertEqual(db.execute('SELECT character_id,area,scene,x,y,revision FROM recovered_positions').fetchall(),
                             [(1,2,4,*final,count)])


if __name__=='__main__':unittest.main()
