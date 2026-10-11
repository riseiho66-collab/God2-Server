"""Pinned quest-one text and NPC definitions; no server transition inference."""
import hashlib
import json
import struct
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.strike_lab.recover_quests import build_catalog
from tools.strike_lab.omega_assets import decode_csvz


class TownGuideSourceTests(unittest.TestCase):
    def test_town_map_source_and_scene_preload_membership(self):
        from tools.strike_lab.import_native_catalog import pinned_records
        from tools.strike_lab.recover_companions import parse_sections
        client=ROOT.parent/'God2'
        maps=[row for row in pinned_records(client) if row[4].split(b',')[1]==b'CityI1']
        self.assertEqual(len(maps),1)
        self.assertEqual(maps[0][5:],(2,4,0))
        self.assertEqual(maps[0][4].split(b',')[2],'\u6953\u83ef\u93ae'.encode('cp950'))
        plain=decode_csvz((client/'Data2/Patch/Comm/gamedata.csvZ').read_bytes())
        groups={}
        for row in parse_sections(plain,('NPCList',))['NPCList']['records']:
            values=list(map(int,bytes.fromhex(row['raw_record_hex']).split(b',')))
            groups.setdefault(tuple(values[:2]),[]).extend(values[2:])
        self.assertEqual(len(groups[2,4]),46)
        self.assertEqual(groups[2,4].count(20),1)
        self.assertEqual(groups[2,15],[21,2143])

    def test_live_original_loader_preserves_scene_and_returns(self):
        run=ROOT/'artifacts/runs/native-town-resource-load-20260921-01'
        evidence=json.loads((run/'run.json').read_text(encoding='utf-8'))
        self.assertIsNone(evidence.get('error'))
        self.assertEqual(evidence['result'],'NATIVE_TOWN_RESOURCE_LOADED')
        before=evidence['npc_live_state'];returned=evidence['town_resource_return'];after=returned['state']
        self.assertEqual(returned['sp'],evidence['town_resource_probe']['entry_sp'])
        self.assertLess(before['sequence'],returned['sequence'])
        self.assertLess(returned['sequence'],evidence['town_resource_final_frame']['sequence'])
        prior={r['ordinal']:r for r in before['resources']}
        current={r['ordinal']:r for r in after['resources']}
        self.assertEqual(prior[19]['loaded_slot'],-1)
        self.assertGreaterEqual(current[19]['loaded_slot'],0)
        self.assertEqual(prior.keys(),current.keys())
        for ordinal,row in prior.items():
            if ordinal!=19:self.assertEqual(row,current[ordinal])
        self.assertEqual(before['templates'],after['templates'])
        self.assertEqual(before['pools'],after['pools'])
        self.assertEqual(prior[19]['path'],current[19]['path'])
        self.assertEqual(current[19]['path'].lower(),'data2\\rom\\npc\\npc2720.rom')

    def test_live_templates_and_unloaded_appearance_resource(self):
        run=ROOT/'artifacts/runs/native-town-guide-catalog-20260921-01'
        evidence=json.loads((run/'run.json').read_text(encoding='utf-8'))
        self.assertIsNone(evidence.get('error'))
        self.assertEqual(evidence['result'],'NATIVE_NPC_DIALOGUE_CANCEL_TRANSPORT_OBSERVED')
        state=evidence['npc_live_state']
        templates={row['selector']:row for row in state['templates']}
        for identity,name in ((1606,'\u6d82\u8ae6\u980c'),(1607,'\u5b8b\u710d\u5857')):
            row=templates[identity];raw=bytes.fromhex(row['record_hex'])
            self.assertEqual(len(raw),94)
            self.assertEqual(raw[:16].split(b'\0',1)[0],name.encode('cp950'))
            self.assertEqual(struct.unpack_from('<HH',raw,0x10),(0x4000,20))
            self.assertEqual((row['flags'],row['appearance_code']),(0x4000,20))
        resource=next(row for row in state['resources'] if row['ordinal']==19)
        self.assertEqual(resource['path'].lower(),'data2\\rom\\npc\\npc2720.rom')
        self.assertEqual((resource['loaded_slot'],resource['action_count'],resource['palette']),(-1,16,6))
        self.assertTrue(all(not pool['entries'] for pool in state['pools']))

    def test_current_quest_text_and_unique_appearance_definitions(self):
        client=ROOT.parent/'God2'
        catalog=build_catalog(client)
        self.assertEqual(catalog['tables']['missions']['source_sha256'],
            '659c8f38ffd9c34107969b449afd16488665a08970110910c9aed8448a0bb716')
        quest=catalog['quests'][0]
        self.assertEqual((quest['id'],quest['step_field']),(1,2))
        names=['\u6d82\u8ae6\u980c','\u5b8b\u710d\u5857']
        first,second=quest['objectives_text']
        for name in names:self.assertIn(name,first['text'])
        self.assertIn('(110/110)',first['text'])
        self.assertIn('(116/62)',first['text'])
        self.assertIn(names[0]+'(110/110)',second['text'])
        self.assertEqual(quest['rewards'],'UNKNOWN')
        self.assertEqual(quest['transitions'],'UNKNOWN')
        raw=(client/'Data2/Patch/Comm/gamedata.csvZ').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
            '70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731')
        # This original format is unquoted comma-separated data.
        rows=[line.split(b',') for line in decode_csvz(raw).splitlines()]
        start=next(i for i,row in enumerate(rows) if row[0]==b'NPCAppearData')
        self.assertEqual(int(rows[start][1]),4043)
        definitions=rows[start+1:start+1+4043]
        for name,identity in zip(names,(1606,1607)):
            matches=[row for row in definitions if len(row)>1 and row[1]==name.encode('cp950')]
            self.assertEqual(matches,[[str(identity).encode(),name.encode('cp950'),b'20',b'0',b'1',b'0',b'0',b'0',b'0']])


if __name__=='__main__':unittest.main()
