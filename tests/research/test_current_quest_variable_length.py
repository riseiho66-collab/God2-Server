"""Original receive-length slice only; no UI, quest rules or live acceptance."""
import hashlib
import csv
import io
import json
from pathlib import Path
import struct
import subprocess
import sqlite3
import sys
import unittest

from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ESI, UC_X86_REG_EDI, UC_X86_REG_EIP

ROOT = Path(__file__).resolve().parents[2]
IMAGE = ROOT/'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
SHA = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
BASE, NET = 0x400000, 0x10000000


class QuestVariableLengthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = IMAGE.read_bytes()
        if hashlib.sha256(cls.raw).hexdigest() != SHA:
            raise ValueError('Current client image changed')

    def test_7a_selects_variable_length_sentinel(self):
        pointer = struct.unpack_from('<I',self.raw,0x1324+4*0x7a)[0]
        self.assertEqual(pointer,BASE+0x1318)
        self.assertEqual(self.raw[pointer-BASE:pointer-BASE+6],bytes.fromhex('b8feffffffc3'))
        # Receive loop selects this path only after the -2 sentinel.
        self.assertEqual(self.raw[0x134e3:0x134e6],bytes.fromhex('83fffe'))

    def test_world_interaction_candidate_original_producer_not_npc_identity(self):
        sys.path.insert(0,str(ROOT))
        from tools.strike_lab.current_world_interaction_request import report,execute
        evidence=report()
        self.assertEqual(evidence['image_sha256'],SHA)
        self.assertEqual(len(evidence['cases']),12)
        for case in evidence['cases']:
            if case['target']<0x80000000:
                self.assertEqual(len(case['calls']),1)
                self.assertEqual(case['calls'][0]['opcode'],0x6e)
                self.assertEqual(case['calls'][0]['payload_length'],8)
            else:self.assertEqual(case['calls'],[])
        for selector in (0,255,256,65535,0xffffffff):
            result=execute(self.raw,selector,42,0x5a)
            self.assertEqual(result['queued_hex'],
                (b'\x6e'+bytes([selector&255])+b'\x5a'*3+struct.pack('<I',42)).hex())

    def test_native_npc_range_and_identity_to_37_producer(self):
        sys.path.insert(0,str(ROOT))
        from tools.strike_lab.current_npc_interaction import range_path,WORLD
        for dx,dy in ((0,0),(3,3),(-3,-3),(3,-3),(-3,3),(4,0),(-4,0),(0,4),(0,-4)):
            result=range_path(self.raw,x=10+dx,y=10+dy)
            self.assertEqual(result['reached_producer'],abs(dx)<=3 and abs(dy)<=3)
            if result['reached_producer']:
                self.assertEqual(result['target'],42)
                self.assertEqual(result['ui'],WORLD+0xa7f2f6c)
        for values in ({'slot':255},{'slot':256},{'identity':65535},{'hit':0x36}):
            result=range_path(self.raw,**values)
            self.assertEqual(result['reached_producer'],values=={'slot':255})

    def test_native_npc_37_clock_and_pending_dialogue(self):
        sys.path.insert(0,str(ROOT))
        from tools.strike_lab.current_npc_interaction import producer_after_clock
        for now,previous,allowed in ((0,0,False),(1000,0,False),(1001,0,True),
                                      (500,0xfffffe00,True)):
            result=producer_after_clock(self.raw,now=now,previous=previous)
            self.assertTrue(result['returned'])
            self.assertEqual(result['esp'],0x40008000+8)
            self.assertEqual(result['queued_hex'],'372a000000' if allowed else '')
            self.assertEqual(result['last_tick'],now if allowed else previous)
        for target in (0,65535,0x12345678,0x7fffffff):
            result=producer_after_clock(self.raw,target=target)
            self.assertEqual(result['queued_hex'],(b'\x37'+struct.pack('<I',target)).hex())
            self.assertEqual(result['selected'],target&65535)
            executable=ROOT/'build/tests/Release/recovered-world-records.exe'
            self.assertEqual(subprocess.check_output([str(executable),'--logical',result['queued_hex']],
                text=True,timeout=10).strip(),result['queued_hex'])
        result=producer_after_clock(self.raw,pending=True)
        self.assertEqual([call['opcode'] for call in result['calls']],[0x85,0x37])
        self.assertEqual(result['queued_hex'][:12],'85341202009a')
        self.assertTrue(result['queued_hex'].endswith('372a000000'))
        self.assertEqual(result['pending'],0)
        self.assertEqual(subprocess.check_output([str(executable),'--logical',result['queued_hex']],
            text=True,timeout=10).strip(),result['queued_hex'])
        from tools.strike_lab import current_quest_action as q
        for target in (0,0x7fffffff,0x80000000,0xffffffff):
            native=q.NativeAction(self.raw)
            native.write(q.SP,'<II',q.RETURN,target)
            native.setreg('ESP',q.SP);native.setreg('ECX',q.UI)
            end=native.run(0x96750,q.RETURN,q.BASE+0x9675d)
            self.assertEqual(end,q.RETURN if target>=0x80000000 else q.BASE+0x9675d)
            self.assertEqual(native.read(q.QUEUE+q.QUEUE_COUNT,'<I')[0],0)

    def test_native_spawn_identity_survives_to_interaction_request(self):
        sys.path.insert(0,str(ROOT))
        from tools.strike_lab.current_npc_interaction import range_path,producer_after_clock
        executable=ROOT/'build/tests/Release/recovered-world-records.exe'
        for primary in (0,42,3793,3954,65534,65535):
            for secondary in (0,0xabcd):
                record=bytearray(21);record[0]=0x72
                struct.pack_into('<HH',record,1,primary,secondary)
                struct.pack_into('<I',record,17,(13<<17)|(7<<2)|3)
                original=bytes(record)
                result=range_path(self.raw,slot=255,role_x=10,role_y=10,logical_spawn=record)
                self.assertEqual(result['spawn_fields'],dict(identity=primary,coordinates=[7,13]))
                self.assertEqual(result['reached_producer'],primary!=65535)
                self.assertEqual(bytes(record),original)
                if result['reached_producer']:
                    self.assertEqual(result['target'],primary)
                    outgoing=producer_after_clock(self.raw,target=result['target'])['queued_hex']
                    self.assertEqual(outgoing,(b'\x37'+struct.pack('<I',primary)).hex())
                    self.assertEqual(subprocess.check_output([str(executable),'--logical',outgoing],
                        text=True,timeout=10).strip(),outgoing)
        struct.pack_into('<I',record,17,(14<<17)|(7<<2))
        struct.pack_into('<H',record,1,42)
        self.assertFalse(range_path(self.raw,role_x=10,role_y=10,logical_spawn=record)['reached_producer'])

    def test_confirm_thunk_preserves_interrupted_registers(self):
        sys.path.insert(0,str(ROOT))
        from tools.strike_lab.current_quest_live import confirm_page
        from unicorn import x86_const as r
        page,ui,stack=0x20000000,0x10000000,0x30000800
        code,trap=confirm_page(page,ui)
        vm=Uc(UC_ARCH_X86,UC_MODE_32)
        vm.mem_map(page,4096);vm.mem_write(page,code)
        vm.mem_map(0x4c8000,4096)
        # Stub only tests lab thunk preservation, not the original game's action.
        vm.mem_write(0x4c8500,bytes.fromhex('b801000000ba02000000f9c3'))
        vm.mem_map(0x30000000,4096)
        names=('EAX','EBX','ECX','EDX','ESI','EDI','EBP','ESP','EFLAGS')
        registers=[getattr(r,'UC_X86_REG_'+name) for name in names]
        values=[17,18,19,20,21,22,23,stack,0x202]
        for register,value in zip(registers,values):vm.reg_write(register,value)
        calls=[]
        def observe(machine,address,size,data):
            if address==0x4c8500:calls.append(machine.reg_read(r.UC_X86_REG_ECX))
        vm.hook_add(UC_HOOK_CODE,observe)
        vm.emu_start(page,page+trap,count=30)
        self.assertEqual(calls,[ui])
        self.assertEqual([vm.reg_read(register) for register in registers],values)
        self.assertEqual(code[trap:],b'\xcc\x0f\x0b')
        for address,pointer in ((0,ui),(page,0),(0x100000000,ui),(page,0xffffffff)):
            with self.assertRaises(ValueError):confirm_page(address,pointer)

    def test_live_loaded_text_matches_current_source(self):
        sys.path.insert(0,str(ROOT))
        from tools.strike_lab.omega_assets import decode_csvz
        source=ROOT.parent/'God2/Data2/Patch/Comm/NPCMission01.csvZ'
        raw=source.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
            '1ff497204b5cf77cbbccffdf1836d7aeee30e46980ac1e85d8d0a08a0a4bcda7')
        rows=list(csv.reader(io.StringIO(decode_csvz(raw).decode('latin1'))))
        self.assertEqual(rows[1],['NPCMissionMessage','1000'])
        texts={int(row[0]):','.join(row[1:]).encode('latin1') for row in rows[2:] if row and row[0].isdigit()}
        run=ROOT/'artifacts/runs/native-quest-text-table-20260921-01/run.json'
        evidence=json.loads(run.read_text(encoding='utf-8'))
        self.assertIsNone(evidence.get('error'))
        table=evidence['quest_text_table']
        self.assertEqual(table['count'],14600)
        self.assertTrue(table['resource'] and table['table'])
        self.assertEqual([e['key'] for e in table['entries']],[1,2,3,4])
        for entry in table['entries']:
            expected=texts[entry['key']]
            self.assertEqual(bytes.fromhex(entry['text_hex']),expected[:256])
            self.assertEqual(entry['terminated_within_256'],len(expected)<256)
        self.assertTrue(table['entries'][2]['terminated_within_256'])

    def test_own_server_mode1_reaches_real_consumer_and_returns(self):
        run=ROOT/'artifacts/runs/native-quest-dialogue-20260921-01'
        evidence=json.loads((run/'run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'],'NATIVE_QUEST_DIALOGUE_CONSUMER_RETURNED')
        self.assertIsNone(evidence.get('error'))
        entry=evidence['quest_dialogue_entry'];header=evidence['quest_dialogue_header']
        returned=evidence['quest_dialogue_return']
        executable=ROOT/'build/tests/Release/recovered-quest-sync.exe'
        expected=bytes.fromhex(subprocess.check_output([str(executable),'--dialogue-mode1',
            '4660','2','154','3','14600'],text=True,timeout=10))
        self.assertEqual(bytes.fromhex(entry['payload_hex']),expected[1:])
        self.assertGreaterEqual(entry['widget_signed'],0)
        self.assertEqual((header['request_word'],header['reply_word']),(4660,2))
        self.assertLess(entry['sequence'],header['sequence'])
        self.assertLess(header['sequence'],returned['sequence'])
        self.assertEqual(returned['sp'],entry['sp']+8)
        self.assertEqual(evidence['quest_text_table']['count'],14600)
        log=(run/'cpp-server.log').read_text(encoding='utf-8')
        self.assertEqual(log.count('DIAGNOSTIC_QUEST_DIALOGUE_SENT'),1)
        self.assertNotIn('policy or response rejected',log)
        source=ROOT/'artifacts/runs/native-revival-postbattle-move-20260921-01/diagnostic-accounts.db'
        with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as before, \
             sqlite3.connect((run/'diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as after:
            for query in ('SELECT * FROM character_resources','SELECT * FROM recovered_positions',
                          'SELECT * FROM battle_checkpoints','SELECT * FROM battle_settlements'):
                self.assertEqual(before.execute(query).fetchall(),after.execute(query).fetchall())

    def test_compiled_mode1_candidate_through_original_consumer_and_action(self):
        sys.path.insert(0,str(ROOT))
        from tools.strike_lab import current_quest_action as q
        executable=ROOT/'build/tests/Release/recovered-quest-sync.exe'
        for request,reply,context in ((0,0,0),(65535,32767,255),(0x1234,0x8000,0x9a),
                                       (42,0xfffe,1),(7,0xffff,2)):
            with self.subTest(request=request,reply=reply):
                output=subprocess.check_output([str(executable),'--dialogue-mode1',str(request),
                    str(reply),str(context),'1','1'],text=True,timeout=10)
                packet=bytes.fromhex(output)
                self.assertEqual(len(packet),27)
                self.assertEqual(struct.unpack_from('<H',packet,1)[0],len(packet))
                self.assertEqual(packet,q.fixture(request_word=request,reply_word=reply,context_byte=context))
                native=q.NativeAction(self.raw)
                incoming=native.ingest(packet)
                self.assertEqual(incoming['stop_rva'],0xc8234)
                self.assertEqual(incoming['request_word'],request)
                self.assertEqual(incoming['context_byte'],context)
                normalized=reply if reply==0xffff else reply&0x7fff
                self.assertEqual(incoming['normalized_reply_word'],normalized)
                result=native.action(page=0,page_count=1,mode=1,threshold=0,choice=-1,
                    stack_byte=0xa5,queued_count=0,lock_pointer=0)
                self.assertEqual(result['stop_rva'],0xc8350)
                if reply==0xffff:
                    self.assertEqual(result['queue_count_after'],0)
                else:
                    self.assertEqual(result['appended_hex'],
                        (b'\x85'+struct.pack('<HHBB',request,normalized,context,0xa5)).hex())

    def test_live_native_confirm_enqueues_dialogue_request(self):
        run=ROOT/'artifacts/runs/native-quest-confirm-20260921-01'
        evidence=json.loads((run/'run.json').read_text(encoding='utf-8'))
        self.assertIsNone(evidence.get('error'))
        self.assertEqual(evidence['result'],'NATIVE_QUEST_CONFIRM_RETURNED')
        probe=evidence['quest_confirm_probe'];result=evidence['quest_confirm_return']
        self.assertEqual((probe['page_index'],probe['page_count']),(0,1))
        self.assertEqual(probe['queued_before'],0)
        self.assertEqual(probe['queued_hex_before'],'')
        self.assertEqual(result['sp'],probe['entry_sp'])
        self.assertEqual(result['queued_length'],7)
        queued=bytes.fromhex(result['queued_hex'])
        self.assertEqual(len(queued),7)
        self.assertEqual(queued[:6],bytes.fromhex('85341202009a'))
        # Final byte is untouched native stack residue, not a semantic field.
        self.assertGreater(result['sequence'],evidence['quest_dialogue_return']['sequence'])
        source=ROOT/'artifacts/runs/native-revival-postbattle-move-20260921-01/diagnostic-accounts.db'
        with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as before, \
             sqlite3.connect((run/'diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as after:
            for table in ('character_resources','recovered_positions','battle_checkpoints','battle_settlements'):
                self.assertEqual(before.execute('SELECT * FROM '+table).fetchall(),
                                 after.execute('SELECT * FROM '+table).fetchall())

    def test_live_confirm_transport_reaches_policy_rejection(self):
        sys.path.insert(0,str(ROOT))
        from tools.strike_lab.recovered_packet_pipeline import FrameParser,OpcodeDispatcher
        run=ROOT/'artifacts/runs/native-quest-transport-20260921-01'
        evidence=json.loads((run/'run.json').read_text(encoding='utf-8'))
        self.assertIsNone(evidence.get('error'))
        self.assertEqual(evidence['result'],'NATIVE_QUEST_CONFIRM_TRANSPORT_OBSERVED')
        transport=evidence['quest_confirm_transport']
        metadata_path=run/transport['packet_evidence']
        metadata=json.loads(metadata_path.read_text(encoding='utf-8'))
        plain=(metadata_path.parent/metadata['plain_file']).read_bytes()
        wire=(metadata_path.parent/metadata['wire_file']).read_bytes()
        self.assertEqual(hashlib.sha256(plain).hexdigest(),metadata['plain_sha256'])
        self.assertEqual(hashlib.sha256(wire).hexdigest(),metadata['wire_sha256'])
        self.assertEqual(len(wire),10)
        self.assertTrue(FrameParser.parse(plain)['frame_pass'])
        self.assertEqual(plain[2:-1].hex(),evidence['quest_confirm_return']['queued_hex'])
        self.assertLess(evidence['quest_confirm_return']['sequence'],transport['sequence'])
        self.assertLess(transport['sequence'],evidence['quest_post_transport_frame']['sequence'])
        identified=OpcodeDispatcher.identify(plain,'C2S')
        self.assertEqual(identified['identification'],'QUEST_DIALOGUE_ACTION')
        fields=identified['quest_action']
        self.assertEqual((fields['request_word'],fields['reply_word'],fields['context_byte']),
                         (0x1234,2,0x9a))
        self.assertFalse(fields['conversation_authorized'])
        self.assertIsNone(identified['state_consistent'])
        self.assertNotIn('quest_action',OpcodeDispatcher.identify(plain,'S2C'))
        for logical in (plain[2:-2],plain[2:-1]+b'\0'):
            body=struct.pack('<H',len(logical)+3)+logical
            malformed=body+bytes([sum(v+0x3c for v in body)&255])
            self.assertNotIn('quest_action',OpcodeDispatcher.identify(malformed,'C2S'))
        log=(run/'cpp-server.log').read_text(encoding='utf-8')
        self.assertEqual(log.count('closing: Recovered world policy or response rejected'),1)
        self.assertLess(log.index('DIAGNOSTIC_QUEST_DIALOGUE_SENT'),
                        log.index('closing: Recovered world policy or response rejected'))

    def test_bound_dialogue_confirm_accepted_without_gameplay_mutation(self):
        sys.path.insert(0,str(ROOT))
        from tools.strike_lab.recovered_packet_pipeline import OpcodeDispatcher
        run=ROOT/'artifacts/runs/native-quest-bound-confirm-20260921-01'
        evidence=json.loads((run/'run.json').read_text(encoding='utf-8'))
        self.assertIsNone(evidence.get('error'))
        self.assertEqual(evidence['result'],'NATIVE_QUEST_CONFIRM_TRANSPORT_OBSERVED')
        transport=evidence['quest_confirm_transport']
        meta_path=run/transport['packet_evidence']
        meta=json.loads(meta_path.read_text(encoding='utf-8'))
        plain=(meta_path.parent/meta['plain_file']).read_bytes()
        self.assertEqual(hashlib.sha256(plain).hexdigest(),meta['plain_sha256'])
        self.assertEqual(plain[2:-1].hex(),evidence['quest_confirm_return']['queued_hex'])
        self.assertEqual(OpcodeDispatcher.identify(plain,'C2S')['identification'],'QUEST_DIALOGUE_ACTION')
        self.assertEqual(meta['pipeline']['identification'],'QUEST_DIALOGUE_ACTION')
        log=(run/'cpp-server.log').read_text(encoding='utf-8')
        self.assertEqual(log.count('DIAGNOSTIC_QUEST_CONFIRM_ACCEPTED'),1)
        self.assertNotIn('policy or response rejected',log)
        self.assertLess(log.index('WORLD_INITIALIZER_TAIL_ACCEPTED'),log.index('DIAGNOSTIC_QUEST_DIALOGUE_SENT'))
        self.assertLess(log.index('DIAGNOSTIC_QUEST_DIALOGUE_SENT'),log.index('DIAGNOSTIC_QUEST_CONFIRM_ACCEPTED'))
        self.assertLess(transport['sequence'],evidence['quest_post_transport_frame']['sequence'])
        source=ROOT/'artifacts/runs/native-revival-postbattle-move-20260921-01/diagnostic-accounts.db'
        with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as before, \
             sqlite3.connect((run/'diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as after:
            for table in ('character_resources','recovered_positions','battle_checkpoints','battle_settlements'):
                self.assertEqual(before.execute('SELECT * FROM '+table).fetchall(),
                                 after.execute('SELECT * FROM '+table).fetchall())

    def test_live_scene_npc_resources_and_empty_pools(self):
        run=ROOT/'artifacts/runs/native-npc-resource-state-20260921-02'
        evidence=json.loads((run/'run.json').read_text(encoding='utf-8'))
        self.assertIsNone(evidence.get('error'))
        self.assertEqual(evidence['result'],'NATIVE_SAVED_POSITION_RESTORED')
        state=evidence['npc_live_state']
        self.assertEqual((state['bank'],state['count']),(0,319))
        self.assertEqual(state['table'],state['manager']+0x3d5d4)
        expected={20:('npc2721.ROM',8,16,6),81:('npc2782.ROM',-1,16,6),
                  87:('npc2788.ROM',-1,16,6),237:('npc2643.ROM',9,8,6),
                  318:('npc2401.ROM',7,8,1)}
        self.assertEqual(len(state['resources']),len(expected))
        for row in state['resources']:
            name,slot,actions,palette=expected[row['ordinal']]
            self.assertEqual(row['path'],'data2\\rom\\npc\\'+name)
            self.assertEqual((row['loaded_slot'],row['action_count'],row['palette']),(slot,actions,palette))
        self.assertEqual([pool['offset'] for pool in state['pools']],[0x1539aed8,0x153b8758])
        for pool in state['pools']:
            self.assertEqual(pool['capacity'],256)
            self.assertEqual(pool['entries'],[])
        source=ROOT/'artifacts/runs/native-revival-postbattle-move-20260921-01/diagnostic-accounts.db'
        with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as before, \
             sqlite3.connect((run/'diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as after:
            for table in ('character_resources','recovered_positions','battle_checkpoints','battle_settlements'):
                self.assertEqual(before.execute('SELECT * FROM '+table).fetchall(),
                                 after.execute('SELECT * FROM '+table).fetchall())

    def test_live_npc_templates_match_current_source_and_loaded_resources(self):
        sys.path.insert(0,str(ROOT))
        from tools.strike_lab.omega_assets import decode_csvz
        source=ROOT.parent/'God2/Data2/Patch/Comm/gamedata.csvZ'
        raw=source.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
            '70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731')
        rows=list(csv.reader(io.StringIO(decode_csvz(raw).decode('latin1'))))
        start=next(i for i,row in enumerate(rows) if row and row[0]=='NPCAppearData')
        count=int(rows[start][1]);self.assertEqual(count,4043)
        definitions={int(row[0]):row for row in rows[start+1:start+1+count]}
        run=ROOT/'artifacts/runs/native-npc-template-state-20260921-02'
        evidence=json.loads((run/'run.json').read_text(encoding='utf-8'))
        self.assertIsNone(evidence.get('error'))
        self.assertEqual(evidence['result'],'NATIVE_SAVED_POSITION_RESTORED')
        state=evidence['npc_live_state'];self.assertEqual(state['appearance_maximum'],6224)
        resources={r['ordinal']:r for r in state['resources']}
        self.assertEqual([t['selector'] for t in state['templates']],[531,3557])
        for template,ordinal,code in zip(state['templates'],(20,237),(21,2143)):
            row=definitions[template['selector']]
            record=bytes.fromhex(template['record_hex'])
            self.assertEqual(len(record),94)
            self.assertEqual(record[:16].split(b'\0',1)[0],row[1].encode('latin1'))
            self.assertEqual(template['flags'],struct.unpack_from('<H',record,0x10)[0])
            self.assertEqual(template['flags'],0x4000)
            self.assertEqual(template['appearance_code'],struct.unpack_from('<H',record,0x12)[0])
            self.assertEqual(template['appearance_code'],int(row[2]))
            self.assertEqual(template['appearance_code'],code)
            self.assertGreaterEqual(resources[ordinal]['loaded_slot'],0)
        self.assertTrue(all(not p['entries'] for p in state['pools']))

    def test_own_server_spawn_populates_original_npc_pool(self):
        run=ROOT/'artifacts/runs/native-quest-npc-spawn-20260921-01'
        evidence=json.loads((run/'run.json').read_text(encoding='utf-8'))
        self.assertIsNone(evidence.get('error'))
        self.assertEqual(evidence['result'],'NATIVE_QUEST_DIALOGUE_CONSUMER_RETURNED')
        before=evidence['npc_live_state'];after=evidence['npc_after_spawn']
        self.assertTrue(all(not pool['entries'] for pool in before['pools']))
        self.assertEqual(after['pools'][0]['entries'],[dict(slot=0,identity=531,x=17,y=12)])
        self.assertEqual(after['pools'][1]['entries'],[])
        self.assertEqual(before['resources'],after['resources'])
        self.assertEqual(before['templates'],after['templates'])
        self.assertLess(before['sequence'],after['sequence'])
        log=(run/'cpp-server.log').read_text(encoding='utf-8')
        self.assertEqual(log.count('DIAGNOSTIC_QUEST_NPC_SENT'),1)
        self.assertNotIn('policy or response rejected',log)
        source=ROOT/'artifacts/runs/native-revival-postbattle-move-20260921-01/diagnostic-accounts.db'
        with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as prior, \
             sqlite3.connect((run/'diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as current:
            for table in ('character_resources','recovered_positions','battle_checkpoints','battle_settlements'):
                self.assertEqual(prior.execute('SELECT * FROM '+table).fetchall(),
                                 current.execute('SELECT * FROM '+table).fetchall())

    def test_live_spawned_npc_request_reaches_server_policy(self):
        sys.path.insert(0,str(ROOT))
        from tools.strike_lab.recovered_packet_pipeline import OpcodeDispatcher
        run=ROOT/'artifacts/runs/native-npc-request-20260921-01'
        evidence=json.loads((run/'run.json').read_text(encoding='utf-8'))
        self.assertIsNone(evidence.get('error'))
        self.assertEqual(evidence['result'],'NATIVE_NPC_REQUEST_TRANSPORT_OBSERVED')
        self.assertEqual(evidence['npc_after_spawn']['pools'][0]['entries'],
                         [dict(slot=0,identity=531,x=17,y=12)])
        probe=evidence['quest_confirm_probe'];returned=evidence['quest_confirm_return']
        self.assertEqual(probe['action'],'NPC_REQUEST_96750_SELECTION_BYPASSED')
        self.assertEqual(probe['queued_before'],0)
        self.assertEqual(returned['sp'],probe['entry_sp'])
        self.assertEqual(returned['queued_hex'],'3713020000')
        transport=evidence['quest_confirm_transport']
        self.assertEqual(transport['logical_hex'],returned['queued_hex'])
        meta_path=run/transport['packet_evidence']
        meta=json.loads(meta_path.read_text(encoding='utf-8'))
        plain=(meta_path.parent/meta['plain_file']).read_bytes()
        wire=(meta_path.parent/meta['wire_file']).read_bytes()
        self.assertEqual(hashlib.sha256(plain).hexdigest(),meta['plain_sha256'])
        self.assertEqual(hashlib.sha256(wire).hexdigest(),meta['wire_sha256'])
        self.assertEqual(len(wire),8)
        identified=OpcodeDispatcher.identify(plain,'C2S')
        self.assertEqual(identified['npc_interaction']['raw_target'],531)
        self.assertFalse(identified['npc_interaction']['target_authorized'])
        self.assertIsNone(identified['state_consistent'])
        self.assertNotIn('npc_interaction',OpcodeDispatcher.identify(plain,'S2C'))
        executable=ROOT/'build/tests/Release/recovered-world-records.exe'
        # CLI --frame expects zero-seed encoded wire, not already decrypted bytes.
        self.assertEqual(subprocess.check_output([str(executable),'--logical',plain[2:-1].hex()],
            text=True,timeout=10).strip(),'3713020000')
        log=(run/'cpp-server.log').read_text(encoding='utf-8')
        self.assertEqual(log.count('closing: Recovered world policy or response rejected'),1)
        self.assertNotIn('DIAGNOSTIC_QUEST_CONFIRM_ACCEPTED',log)

    def test_live_npc_request_triggers_dialogue_after_authorization(self):
        run=ROOT/'artifacts/runs/native-npc-dialogue-response-20260921-01'
        evidence=json.loads((run/'run.json').read_text(encoding='utf-8'))
        self.assertIsNone(evidence.get('error'))
        self.assertEqual(evidence['result'],'NATIVE_NPC_DIALOGUE_RESPONSE_RETURNED')
        before=evidence['npc_before_request'];transport=evidence['quest_confirm_transport']
        entry=evidence['quest_dialogue_entry'];returned=evidence['quest_dialogue_return']
        self.assertEqual(before['pools'][0]['entries'],[dict(slot=0,identity=531,x=17,y=12)])
        self.assertEqual(transport['logical_hex'],'3713020000')
        self.assertLess(before['sequence'],transport['sequence'])
        self.assertLess(transport['sequence'],entry['sequence'])
        self.assertLess(entry['sequence'],returned['sequence'])
        self.assertEqual(returned['sp'],entry['sp']+8)
        self.assertEqual(evidence['quest_dialogue_header']['request_word'],0x1234)
        self.assertEqual(evidence['quest_dialogue_header']['reply_word'],2)
        log=(run/'cpp-server.log').read_text(encoding='utf-8')
        self.assertEqual(log.count('DIAGNOSTIC_NPC_REQUEST_ACCEPTED'),1)
        self.assertNotIn('DIAGNOSTIC_QUEST_DIALOGUE_SENT',log)
        self.assertNotIn('policy or response rejected',log)
        self.assertLess(log.index('DIAGNOSTIC_QUEST_NPC_SENT'),log.index('DIAGNOSTIC_NPC_REQUEST_ACCEPTED'))
        source=ROOT/'artifacts/runs/native-revival-postbattle-move-20260921-01/diagnostic-accounts.db'
        with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as prior, \
             sqlite3.connect((run/'diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as current:
            for table in ('character_resources','recovered_positions','battle_checkpoints','battle_settlements'):
                self.assertEqual(prior.execute('SELECT * FROM '+table).fetchall(),
                                 current.execute('SELECT * FROM '+table).fetchall())

    def test_single_connection_npc_dialogue_confirmation_round_trip(self):
        sys.path.insert(0,str(ROOT))
        from tools.strike_lab.recovered_packet_pipeline import OpcodeDispatcher
        run=ROOT/'artifacts/runs/native-npc-conversation-complete-20260921-01'
        evidence=json.loads((run/'run.json').read_text(encoding='utf-8'))
        self.assertIsNone(evidence.get('error'))
        self.assertEqual(evidence['result'],'NATIVE_NPC_CONVERSATION_CONFIRM_TRANSPORT_OBSERVED')
        npc=evidence['npc_request_transport'];confirm=evidence['quest_confirm_transport']
        self.assertEqual(npc['socket'],confirm['socket'])
        self.assertEqual(npc['logical_hex'],'3713020000')
        self.assertEqual(bytes.fromhex(confirm['logical_hex'])[:6],bytes.fromhex('85341202009a'))
        self.assertEqual(len(bytes.fromhex(confirm['logical_hex'])),7)
        self.assertEqual(evidence['npc_request_probe']['action'],'NPC_REQUEST_96750_SELECTION_BYPASSED')
        self.assertEqual(evidence['quest_confirm_probe']['action'],'DIALOGUE_CONFIRM_C8500')
        self.assertEqual(evidence['quest_confirm_probe']['queued_before'],0)
        for prefix,transport,identity in (('npc_request',npc,'NPC_INTERACTION_REQUEST'),
                                          ('quest_confirm',confirm,'QUEST_DIALOGUE_ACTION')):
            self.assertEqual(evidence[prefix+'_return']['sp'],evidence[prefix+'_probe']['entry_sp'])
            self.assertEqual(evidence[prefix+'_return']['queued_hex'],transport['logical_hex'])
            meta_path=run/transport['packet_evidence']
            meta=json.loads(meta_path.read_text(encoding='utf-8'))
            plain=(meta_path.parent/meta['plain_file']).read_bytes()
            wire=(meta_path.parent/meta['wire_file']).read_bytes()
            self.assertEqual(hashlib.sha256(plain).hexdigest(),meta['plain_sha256'])
            self.assertEqual(hashlib.sha256(wire).hexdigest(),meta['wire_sha256'])
            self.assertEqual(OpcodeDispatcher.identify(plain,'C2S')['identification'],identity)
            self.assertEqual(plain[2:-1].hex(),transport['logical_hex'])
        sequences=[evidence['npc_before_request']['sequence'],npc['sequence'],
                   evidence['quest_dialogue_entry']['sequence'],evidence['quest_dialogue_header']['sequence'],
                   evidence['quest_dialogue_return']['sequence'],evidence['quest_confirm_return']['sequence'],
                   confirm['sequence'],evidence['npc_conversation_final_frame']['sequence']]
        self.assertTrue(all(a<b for a,b in zip(sequences,sequences[1:])))
        log=(run/'cpp-server.log').read_text(encoding='utf-8')
        markers=('DIAGNOSTIC_QUEST_NPC_SENT','DIAGNOSTIC_NPC_REQUEST_ACCEPTED','DIAGNOSTIC_QUEST_CONFIRM_ACCEPTED')
        for marker in markers:self.assertEqual(log.count(marker),1)
        self.assertEqual(sorted(log.index(marker) for marker in markers),[log.index(marker) for marker in markers])
        self.assertNotIn('policy or response rejected',log)
        self.assertNotIn('DIAGNOSTIC_QUEST_DIALOGUE_SENT',log)
        source=ROOT/'artifacts/runs/native-revival-postbattle-move-20260921-01/diagnostic-accounts.db'
        with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as prior, \
             sqlite3.connect((run/'diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as current:
            for table in ('character_resources','recovered_positions','battle_checkpoints','battle_settlements'):
                self.assertEqual(prior.execute('SELECT * FROM '+table).fetchall(),
                                 current.execute('SELECT * FROM '+table).fetchall())

    def test_live_confirmation_projects_one_diagnostic_journal_slot(self):
        run=ROOT/'artifacts/runs/native-npc-journal-projection-20260921-01'
        evidence=json.loads((run/'run.json').read_text(encoding='utf-8'))
        self.assertIsNone(evidence.get('error'))
        self.assertEqual(evidence['result'],'NATIVE_NPC_CONVERSATION_CONFIRM_TRANSPORT_OBSERVED')
        entry=evidence['npc_journal_entry'];returned=evidence['npc_journal_return']
        self.assertEqual(entry['pc'],0x4c9670)
        self.assertEqual((entry['a0'],entry['a1']),(0,1))
        self.assertEqual(bytes.fromhex(entry['slots_hex']),bytes(60))
        self.assertEqual(bytes.fromhex(returned['slots_hex']),struct.pack('<15I',1,*([0]*14)))
        self.assertEqual(returned['pc'],entry['ret'])
        self.assertEqual(returned['sp'],entry['sp']+12)
        npc=evidence['npc_request_transport'];confirm=evidence['quest_confirm_transport']
        self.assertEqual(npc['socket'],confirm['socket'])
        self.assertEqual(npc['logical_hex'],'3713020000')
        self.assertEqual(bytes.fromhex(confirm['logical_hex'])[:6],bytes.fromhex('85341202009a'))
        sequence=[npc['sequence'],evidence['quest_dialogue_return']['sequence'],
                  confirm['sequence'],entry['sequence'],returned['sequence'],
                  evidence['npc_conversation_final_frame']['sequence']]
        self.assertTrue(all(a<b for a,b in zip(sequence,sequence[1:])))
        log=(run/'cpp-server.log').read_text(encoding='utf-8')
        for marker in ('DIAGNOSTIC_QUEST_NPC_SENT','DIAGNOSTIC_NPC_REQUEST_ACCEPTED',
                       'DIAGNOSTIC_QUEST_CONFIRM_ACCEPTED'):
            self.assertEqual(log.count(marker),1)
        self.assertNotIn('policy or response rejected',log)
        source=ROOT/'artifacts/runs/native-revival-postbattle-move-20260921-01/diagnostic-accounts.db'
        with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as prior, \
             sqlite3.connect((run/'diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as current:
            for table in ('character_resources','recovered_positions','battle_checkpoints','battle_settlements'):
                self.assertEqual(prior.execute('SELECT * FROM '+table).fetchall(),
                                 current.execute('SELECT * FROM '+table).fetchall())

    def test_live_journal_confirmation_is_durable(self):
        run=ROOT/'artifacts/runs/native-npc-journal-persist-20260921-02'
        evidence=json.loads((run/'run.json').read_text(encoding='utf-8'))
        self.assertIsNone(evidence.get('error'))
        self.assertEqual(evidence['result'],'NATIVE_NPC_CONVERSATION_CONFIRM_TRANSPORT_OBSERVED')
        entry=evidence['npc_journal_entry'];returned=evidence['npc_journal_return']
        expected=struct.pack('<15I',1,*([0]*14))
        self.assertEqual(bytes.fromhex(entry['slots_hex']),bytes(60))
        self.assertEqual(bytes.fromhex(returned['slots_hex']),expected)
        self.assertEqual(returned['sp'],entry['sp']+12)
        self.assertLess(evidence['quest_confirm_transport']['sequence'],entry['sequence'])
        self.assertLess(returned['sequence'],evidence['npc_conversation_final_frame']['sequence'])
        with sqlite3.connect((run/'diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as db:
            self.assertEqual(db.execute('SELECT character_id,slots,revision,source_sha256,design_id FROM diagnostic_quest_journal').fetchall(),
                [(1,expected,1,'659c8f38ffd9c34107969b449afd16488665a08970110910c9aed8448a0bb716','CUSTOM-0018')])
            self.assertEqual(db.execute('SELECT count(*) FROM native_quest_descriptions').fetchone(),(2014,))
        log=(run/'cpp-server.log').read_text(encoding='utf-8')
        self.assertEqual(log.count('DIAGNOSTIC_QUEST_CONFIRM_ACCEPTED'),1)
        self.assertNotIn('policy or response rejected',log)

    def test_fresh_connection_restores_saved_journal_without_confirmation(self):
        run=ROOT/'artifacts/runs/native-journal-relogin-20260921-01'
        source=ROOT/'artifacts/runs/native-npc-journal-persist-20260921-02'
        evidence=json.loads((run/'run.json').read_text(encoding='utf-8'))
        self.assertIsNone(evidence.get('error'))
        self.assertEqual(evidence['result'],'NATIVE_SAVED_JOURNAL_RESTORED')
        returns=evidence['journal_restore_returns']
        self.assertEqual([r['slot'] for r in returns],list(range(15)))
        self.assertEqual([r['value'] for r in returns],[1]+[0]*14)
        self.assertEqual(bytes.fromhex(returns[-1]['slots_hex']),struct.pack('<15I',1,*([0]*14)))
        self.assertTrue(all(a['sequence']<b['sequence'] for a,b in zip(returns,returns[1:])))
        self.assertLess(returns[-1]['sequence'],evidence['journal_restore_final_frame']['sequence'])
        self.assertNotIn('quest_confirm_probe',evidence)
        self.assertNotIn('quest_confirm_transport',evidence)
        log=(run/'cpp-server.log').read_text(encoding='utf-8')
        self.assertEqual(log.count('DIAGNOSTIC_JOURNAL_RESTORE'),1)
        self.assertNotIn('DIAGNOSTIC_QUEST_CONFIRM_ACCEPTED',log)
        self.assertNotIn('policy or response rejected',log)
        with sqlite3.connect((source/'diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as prior, \
             sqlite3.connect((run/'diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as current:
            for table in ('diagnostic_quest_journal','character_resources','recovered_positions','battle_checkpoints','battle_settlements'):
                self.assertEqual(prior.execute('SELECT * FROM '+table).fetchall(),current.execute('SELECT * FROM '+table).fetchall())

    def test_live_cancel_does_not_create_journal(self):
        run=ROOT/'artifacts/runs/native-npc-cancel-20260921-01'
        evidence=json.loads((run/'run.json').read_text(encoding='utf-8'))
        self.assertIsNone(evidence.get('error'))
        self.assertEqual(evidence['result'],'NATIVE_NPC_DIALOGUE_CANCEL_TRANSPORT_OBSERVED')
        probe=evidence['quest_confirm_probe'];returned=evidence['quest_confirm_return']
        transport=evidence['quest_confirm_transport']
        self.assertEqual(probe['action'],'DIALOGUE_CLOSE_C8350')
        self.assertEqual(returned['sp'],probe['entry_sp'])
        self.assertEqual(returned['queued_hex'],transport['logical_hex'])
        logical=bytes.fromhex(transport['logical_hex'])
        self.assertEqual((len(logical),logical[0]),(5,0x86))
        self.assertEqual(int.from_bytes(logical[3:5],'little'),evidence['quest_dialogue_entry']['ui']>>16)
        self.assertLess(evidence['npc_request_transport']['sequence'],transport['sequence'])
        self.assertLess(transport['sequence'],evidence['quest_cancel_final_frame']['sequence'])
        meta_path=run/transport['packet_evidence']
        meta=json.loads(meta_path.read_text(encoding='utf-8'))
        plain=(meta_path.parent/meta['plain_file']).read_bytes()
        wire=(meta_path.parent/meta['wire_file']).read_bytes()
        self.assertEqual(hashlib.sha256(plain).hexdigest(),meta['plain_sha256'])
        self.assertEqual(hashlib.sha256(wire).hexdigest(),meta['wire_sha256'])
        self.assertEqual(plain[2:-1],logical)
        log=(run/'cpp-server.log').read_text(encoding='utf-8')
        self.assertEqual(log.count('DIAGNOSTIC_QUEST_CANCEL_ACCEPTED'),1)
        self.assertNotIn('DIAGNOSTIC_QUEST_CONFIRM_ACCEPTED',log)
        self.assertNotIn('policy or response rejected',log)
        with sqlite3.connect((run/'diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM diagnostic_quest_journal').fetchone(),(0,))

    def test_same_connection_cancel_reopen_then_confirm(self):
        run=ROOT/'artifacts/runs/native-npc-reopen-20260921-01'
        evidence=json.loads((run/'run.json').read_text(encoding='utf-8'))
        self.assertIsNone(evidence.get('error'))
        self.assertEqual(evidence['result'],'NATIVE_NPC_CONVERSATION_CONFIRM_TRANSPORT_OBSERVED')
        first=evidence['cancelled_conversation']
        self.assertEqual(first['quest_dialogue_header']['request_word'],0x1234)
        self.assertEqual(evidence['quest_dialogue_header']['request_word'],0x1235)
        transports=[first['npc_request_transport'],first['quest_confirm_transport'],
                    evidence['npc_request_transport'],evidence['quest_confirm_transport']]
        self.assertEqual(len({t['socket'] for t in transports}),1)
        self.assertEqual([bytes.fromhex(t['logical_hex'])[0] for t in transports],[0x37,0x86,0x37,0x85])
        self.assertEqual(bytes.fromhex(transports[-1]['logical_hex'])[:6],bytes.fromhex('85351202009a'))
        self.assertTrue(all(a['sequence']<b['sequence'] for a,b in zip(transports,transports[1:])))
        for t in transports:
            path=run/t['packet_evidence'];meta=json.loads(path.read_text(encoding='utf-8'))
            plain=(path.parent/meta['plain_file']).read_bytes()
            wire=(path.parent/meta['wire_file']).read_bytes()
            self.assertEqual(hashlib.sha256(plain).hexdigest(),meta['plain_sha256'])
            self.assertEqual(hashlib.sha256(wire).hexdigest(),meta['wire_sha256'])
            self.assertEqual(plain[2:-1].hex(),t['logical_hex'])
        expected=struct.pack('<15I',1,*([0]*14))
        self.assertEqual(bytes.fromhex(evidence['npc_journal_return']['slots_hex']),expected)
        self.assertLess(evidence['npc_journal_return']['sequence'],evidence['npc_conversation_final_frame']['sequence'])
        with sqlite3.connect((run/'diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as db:
            self.assertEqual(db.execute('SELECT slots,revision,design_id FROM diagnostic_quest_journal').fetchall(),[(expected,1,'CUSTOM-0018')])
        log=(run/'cpp-server.log').read_text(encoding='utf-8')
        self.assertEqual(log.count('DIAGNOSTIC_NPC_REQUEST_ACCEPTED'),2)
        self.assertEqual(log.count('DIAGNOSTIC_QUEST_CANCEL_ACCEPTED'),1)
        self.assertEqual(log.count('DIAGNOSTIC_QUEST_CONFIRM_ACCEPTED'),1)
        self.assertNotIn('policy or response rejected',log)

    def test_compiled_mode1_rejects_invalid_fields_without_bytes(self):
        executable=ROOT/'build/tests/Release/recovered-quest-sync.exe'
        for values in ((65536,0,0,1,1),(0,65536,0,1,1),(0,0,256,1,1),
                       (0,0,0,0,1),(0,0,0,2,1),(0,0,0,1,32768),(0,0,0,1,0),
                       (-1,0,0,1,1)):
            result=subprocess.run([str(executable),'--dialogue-mode1',*map(str,values)],
                                  text=True,capture_output=True,timeout=10)
            self.assertNotEqual(result.returncode,0)
            self.assertEqual(result.stdout,'')

    def test_original_unsigned_length_and_exclusive_capacity(self):
        vm=Uc(UC_ARCH_X86,UC_MODE_32)
        vm.mem_map(BASE,(len(self.raw)+4095)&~4095)
        vm.mem_write(BASE,self.raw)
        vm.mem_protect(BASE,(len(self.raw)+4095)&~4095,5)
        vm.mem_map(NET,0x4000)
        stops={BASE+0x13534:'assertion',BASE+0x13558:'assemble',BASE+0x1359a:'capacity_reject'}
        reached=[]
        def stop(machine,address,size,data):
            if address in stops:
                reached.append(stops[address]);machine.emu_stop()
        vm.hook_add(UC_HOOK_CODE,stop)
        for length in (0,1,2,3,11,12,26,27,28,255,256,2559,2560,2561,32767,32768,65535):
            with self.subTest(length=length):
                reached.clear()
                vm.mem_write(NET+0x2cc4,b'\x7a'+struct.pack('<H',length))
                vm.mem_write(NET+0x2cc0,struct.pack('<I',3))
                vm.reg_write(UC_X86_REG_ESI,NET)
                vm.reg_write(UC_X86_REG_EDI,0xfffffffe)
                vm.emu_start(BASE+0x1351f,BASE+0x135c9,count=30)
                expected='assemble' if length<2560 else 'capacity_reject' if length==2560 else 'assertion'
                self.assertEqual(reached,[expected])
                self.assertEqual(vm.reg_read(UC_X86_REG_EDI),length)
                self.assertIn(vm.reg_read(UC_X86_REG_EIP),stops)


if __name__=='__main__':
    unittest.main()
