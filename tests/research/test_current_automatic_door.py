"""Own-server captured CUSTOM-0025 entry, not official route/physical UI proof."""
import hashlib
import json
from pathlib import Path
import sqlite3
import unittest

ROOT=Path(__file__).resolve().parents[2]


class AutomaticDoorTests(unittest.TestCase):
    def test_live_remote_pool_baseline_and_unchanged_save(self):
        run=ROOT/'artifacts/runs/native-remote-pool-baseline-20260921-01'
        report=json.loads((run/'run.json').read_text())
        self.assertEqual(report['result'],'NATIVE_DOOR_ROUNDTRIP_RECONNECT_RESTORED')
        self.assertIsNone(report.get('error'))
        pool=report['door_reconnect_final']['remote_actors']
        self.assertEqual((pool['capacity'],pool['stride']),(128,0x268))
        self.assertEqual((pool['clear_mode'],pool['display_mode'],pool['extra_mode']),(1,1,1))
        self.assertEqual(pool['entries'],[])
        self.assertEqual(pool['records_sha256'],'0b0ff8a35500703b6280e49875c477203a8309c85c92f8e4bfa8d17ca8cbce3e')
        source=ROOT/'artifacts/runs/native-town-auto-roundtrip-20260921-03/town-diagnostic-accounts.db'
        with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as a, \
             sqlite3.connect((run/'town-diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as b:
            schema="SELECT name,sql FROM sqlite_master WHERE type='table' ORDER BY name"
            self.assertEqual(a.execute(schema).fetchall(),b.execute(schema).fetchall())
            for name,_ in a.execute(schema):
                query='SELECT * FROM "'+name.replace('"','""')+'"'
                self.assertEqual(sorted(a.execute(query).fetchall(),key=repr),sorted(b.execute(query).fetchall(),key=repr),name)

    def test_fresh_client_restores_roundtrip_save_without_mutation(self):
        run=ROOT/'artifacts/runs/native-town-door-reconnect-20260921-01'
        source=ROOT/'artifacts/runs/native-town-auto-roundtrip-20260921-03'
        report=json.loads((run/'run.json').read_text())
        self.assertEqual(report['result'],'NATIVE_DOOR_ROUNDTRIP_RECONNECT_RESTORED')
        self.assertIsNone(report.get('error'))
        snap=report['door_reconnect_final']['snapshot']
        self.assertEqual(tuple(snap[k] for k in ('area','scene','kind','x','y','ring_hex')),(2,4,0,86,71,'010001'))
        self.assertEqual(snap['slot0_hex'],'01000000c115000000000000000000000000000000000000')
        identities=sorted((e['identity'],e['x'],e['y']) for p in report['door_reconnect_final']['npcs']['pools'] for e in p['entries'])
        self.assertEqual(identities,[(1606,110,69),(1607,112,70)])
        self.assertEqual(len(report['journal_restore_returns']),15)
        self.assertEqual(report['journal_restore_returns'][-1]['slots_hex'],'00'*60)
        self.assertNotIn('movement_step',report)
        self.assertNotIn('automatic_door_hops',report)
        with sqlite3.connect((source/'town-diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as a, \
             sqlite3.connect((run/'town-diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as b:
            schema="SELECT name,sql FROM sqlite_master WHERE type='table' ORDER BY name"
            self.assertEqual(a.execute(schema).fetchall(),b.execute(schema).fetchall())
            self.assertEqual(b.execute('SELECT * FROM recovered_positions').fetchall(),[(1,2,4,86,71,91)])
            for name,_ in a.execute(schema):
                query='SELECT * FROM "'+name.replace('"','""')+'"'
                self.assertEqual(sorted(a.execute(query).fetchall(),key=repr),sorted(b.execute(query).fetchall(),key=repr),name)
        log=(run/'cpp-server.log').read_text()
        self.assertNotIn('DIAGNOSTIC_DOOR_COMMITTED',log)
        self.assertNotIn('policy or response rejected',log)

    def test_two_roundtrips_preserve_state_and_scene_npcs(self):
        run=ROOT/'artifacts/runs/native-town-auto-roundtrip-20260921-03'
        report=json.loads((run/'run.json').read_text())
        self.assertEqual(report['result'],'NATIVE_AUTOMATIC_GROCERY_ROUNDTRIPS_ACCEPTED')
        self.assertIsNone(report.get('error'))
        hops=report['automatic_door_hops']
        self.assertEqual(len(hops),4)
        folder=run/'crypto-private'
        messages=[]
        for path in folder.glob('*.json'):
            meta=json.loads(path.read_text())
            if meta['sequence']<=report['door_probe_final']['sequence']:continue
            plain=(folder/meta['plain_file']).read_bytes()
            wire=(folder/meta['wire_file']).read_bytes()
            self.assertTrue(meta['checksum_valid'])
            self.assertFalse(meta['brute_force_used'])
            self.assertEqual(hashlib.sha256(plain).hexdigest(),meta['plain_sha256'])
            self.assertEqual(hashlib.sha256(wire).hexdigest(),meta['wire_sha256'])
            if plain[2] in (0x2e,0x5d,0x61,0x1c):
                messages.append((meta['sequence'],meta['socket'],meta['direction'],plain[2:-1].hex()))
        messages.sort()
        self.assertEqual(len({m[1] for m in messages}),1)
        expected=[]
        for index in range(4):
            indoor=index%2==0
            request='2e560046001bc2' if index==0 else ('2e5600460001c2' if indoor else '2e1000140001c2')
            expected.extend([('C2S',request),('S2C','5d1b' if index==0 else '5d01'),
                ('S2C','61c203000042002600' if indoor else '610201000058018e00'),('C2S','1c01000000')])
        self.assertEqual([(m[2],m[3]) for m in messages],expected)
        for index,hop in enumerate(hops):
            self.assertLess(messages[index*4+3][0],hop['sequence'])
            if index<3:self.assertLess(hop['sequence'],messages[(index+1)*4][0])
            indoor=index%2==0
            snap=hop['snapshot']
            self.assertEqual(tuple(snap[k] for k in ('area','scene','kind','x','y','ring_hex')),
                (2,15,2,16,19,'010001') if indoor else (2,4,0,86,71,'010001'))
            self.assertEqual(snap['slot0_hex'],report['door_probe_final']['snapshot']['slot0_hex'])
            identities=sorted((e['identity'],e['x'],e['y']) for p in hop['npcs']['pools'] for e in p['entries'])
            self.assertEqual(identities,[] if indoor else [(1606,110,69),(1607,112,70)])
            self.assertEqual(hop['movement']['ack_hex'],'5d1b' if index==0 else '5d01')
            if indoor:
                grid=json.loads((ROOT/'artifacts/world-atlas/indoor-2-15.json').read_text())['grid']
                self.assertEqual(snap['grid_hex'],grid['cells_hex'])
            else:
                self.assertEqual(snap['loaded_scene_id'],258)
                self.assertTrue(bytes.fromhex(snap['metadata_hex']).startswith(b'CityI1\0'))
        source=ROOT/'artifacts/runs/native-indoor-town-walk-20260921-01/town-diagnostic-accounts.db'
        with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as a, \
             sqlite3.connect((run/'town-diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as b:
            self.assertEqual(b.execute('SELECT * FROM recovered_positions').fetchall(),[(1,2,4,86,71,91)])
            schema="SELECT name,sql FROM sqlite_master WHERE type='table' ORDER BY name"
            self.assertEqual(a.execute(schema).fetchall(),b.execute(schema).fetchall())
            for name,_ in a.execute(schema):
                if name=='recovered_positions':continue
                query='SELECT * FROM "'+name.replace('"','""')+'"'
                self.assertEqual(sorted(a.execute(query).fetchall(),key=repr),sorted(b.execute(query).fetchall(),key=repr),name)
        log=(run/'cpp-server.log').read_text()
        self.assertEqual(log.count('DIAGNOSTIC_DOOR_COMMITTED'),4)
        self.assertEqual(log.count('DIAGNOSTIC_TOWN_SCENE_CONTEXT_ACCEPTED'),4)
        self.assertEqual(log.count('DIAGNOSTIC_INDOOR_SAVE_RESTORED'),2)
        self.assertEqual(log.count('DIAGNOSTIC_TOWN_GUIDES_SENT'),3)
        self.assertNotIn('policy or response rejected',log)

    def test_original_client_accepts_movement_triggered_indoor_entry(self):
        run=ROOT/'artifacts/runs/native-town-auto-door-20260921-01'
        report=json.loads((run/'run.json').read_text())
        self.assertEqual(report['result'],'NATIVE_AUTOMATIC_GROCERY_ENTRY_ACCEPTED')
        self.assertIsNone(report.get('error'))
        final=report['automatic_door_final']
        snap=final['snapshot']
        self.assertEqual(tuple(snap[k] for k in ('area','scene','kind','x','y','ring_hex')),(2,15,2,16,19,'010001'))
        grid=json.loads((ROOT/'artifacts/world-atlas/indoor-2-15.json').read_text())['grid']
        self.assertEqual(snap['grid_hex'],grid['cells_hex'])
        self.assertEqual((snap['grid_width'],snap['grid_height']),(31,31))
        self.assertEqual(snap['slot0_hex'],report['door_probe_final']['snapshot']['slot0_hex'])
        packets=[]
        folder=run/'crypto-private'
        for path in folder.glob('*.json'):
            meta=json.loads(path.read_text())
            if meta['sequence']<=report['door_probe_final']['sequence']:continue
            plain=(folder/meta['plain_file']).read_bytes()
            wire=(folder/meta['wire_file']).read_bytes()
            self.assertTrue(meta['checksum_valid'])
            self.assertFalse(meta['brute_force_used'])
            self.assertEqual(hashlib.sha256(plain).hexdigest(),meta['plain_sha256'])
            self.assertEqual(hashlib.sha256(wire).hexdigest(),meta['wire_sha256'])
            packets.append((meta,plain[2:-1].hex()))
        def only(direction,logical):
            items=[m for m,p in packets if m['direction']==direction and p==logical]
            self.assertEqual(len(items),1)
            return items[0]
        request=only('C2S','2e560046001bc2')
        ack=only('S2C','5d1b')
        transfer=only('S2C','61c203000042002600')
        context=only('C2S','1c01000000')
        ordered=[request,ack,transfer,context]
        self.assertEqual(len({p['socket'] for p in ordered}),1)
        sequences=[p['sequence'] for p in ordered]
        self.assertEqual(sequences,sorted(sequences))
        self.assertLess(context['sequence'],final['sequence'])
        source=ROOT/'artifacts/runs/native-indoor-town-walk-20260921-01/town-diagnostic-accounts.db'
        with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as a, \
             sqlite3.connect((run/'town-diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as b:
            self.assertEqual(a.execute('SELECT * FROM recovered_positions').fetchall(),[(1,2,4,111,70,57)])
            self.assertEqual(b.execute('SELECT * FROM recovered_positions').fetchall(),[(1,2,15,16,19,85)])
            schema="SELECT name,sql FROM sqlite_master WHERE type='table' ORDER BY name"
            self.assertEqual(a.execute(schema).fetchall(),b.execute(schema).fetchall())
            for name,_ in a.execute(schema):
                if name=='recovered_positions':continue
                query='SELECT * FROM "'+name.replace('"','""')+'"'
                self.assertEqual(sorted(a.execute(query).fetchall(),key=repr),sorted(b.execute(query).fetchall(),key=repr),name)
        log=(run/'cpp-server.log').read_text()
        self.assertEqual(log.count('DIAGNOSTIC_DOOR_COMMITTED'),1)
        self.assertEqual(log.count('DIAGNOSTIC_TOWN_SCENE_CONTEXT_ACCEPTED'),1)
        self.assertNotIn('policy or response rejected',log)


if __name__=='__main__':
    unittest.main()
