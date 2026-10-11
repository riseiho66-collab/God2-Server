"""Offline pinned-x86 skill150 input/result/queue oracle; never opens a client.

Native graphics, text allocator and actor lookup are explicit sinks. Synthetic
actor occupancy is fixture input. This is not F1/mouse or live visual acceptance.
"""
from pathlib import Path
import hashlib
import json
import struct
import sys
import re
import unicorn as uc
from unicorn import x86_const as x
from tools.skills.native_clone.clone_evidence import IMAGE
from tools.skills.build_thousand_bulls_client import ROOT, OUTPUT, CATALOG, decode_definitions

OUT=ROOT/'artifacts/custom-skills/thousand-bulls'
BASE=0x400000
BATTLE=0x10000000
WAR=BATTLE+0x144938
ACTORS=0x20000000
STACK=0x21000000
SP=STACK+0xf000
RETURN=0x22000000
BUFFER=RETURN+0x1000
GATE=RETURN+0x3000
PACKET=BATTLE+0xa9e9cb0
QUEUE=BATTLE+0xa9ea4b0
PIN='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'


class Native:
    def __init__(self):
        image=IMAGE.read_bytes()
        assert hashlib.sha256(image).hexdigest()==PIN
        self.vm=uc.Uc(uc.UC_ARCH_X86,uc.UC_MODE_32)
        for address,size in ((BASE,(len(image)+4095)&~4095),(BATTLE,0xb000000),
                             (ACTORS,0x40000),(STACK,0x10000),(RETURN,0x10000)):
            self.vm.mem_map(address,size)
        self.vm.mem_write(BASE,image)
        self.events=[]
        self.stops=set()
        self.visits=[]
        self.vm.hook_add(uc.UC_HOOK_CODE,self.code)
        definition=decode_definitions((OUTPUT/CATALOG).read_bytes())[0,150].raw
        self.definition=WAR+0xa7e03da+150*110
        self.vm.mem_write(self.definition,definition)
        self.put(GATE+0x100,0,'<h') # Already-loaded native route resource slot fixture.
        self.put(GATE+0x106,-1,'<h')
        self.put(WAR+0xc,GATE+0x1000)
        self.put(BATTLE+0x83458,GATE+0x200)
        for i in range(28):
            a=self.actor(i)
            self.put(a+0x1a,i,'<H')
            self.put(a+0x1d8,i,'<H')
            self.put(a+0x234,(i//14)*128+i%14,'<B')
            self.put(a+0x1e7,255,'<B')
            self.put(a+0xdf8,self.definition)
            self.put(WAR+0x38+i*24,a)
            self.put(GATE+0x1000+0x10+i*0x290,2,'<B')
        self.put(BATTLE+0xa9df6b8,1)
        self.put(BATTLE+0xa9ea4c4,1)
        self.put(BATTLE+0x51,255,'<B') # No local player-info sidebar fixture.
        self.put(WAR+0x2f4,0x3fff)
        self.put(WAR+0x2f8,0x3fff)

    @staticmethod
    def actor(i):return ACTORS+i*0x2000
    def put(self,a,v,fmt='<I'):self.vm.mem_write(a,struct.pack(fmt,v))
    def get(self,a,fmt='<I'):return struct.unpack(fmt,self.vm.mem_read(a,struct.calcsize(fmt)))[0]
    def args(self,n):return struct.unpack('<'+'I'*n,self.vm.mem_read(self.vm.reg_read(x.UC_X86_REG_ESP)+4,n*4))
    def done(self,pop=0,result=0):
        s=self.vm.reg_read(x.UC_X86_REG_ESP)
        self.vm.reg_write(x.UC_X86_REG_EIP,self.get(s))
        self.vm.reg_write(x.UC_X86_REG_ESP,s+4+pop)
        self.vm.reg_write(x.UC_X86_REG_EAX,result)

    def code(self,vm,address,size,unused):
        if address in self.stops:vm.emu_stop();return
        if address in (0x516ae0,0x517230,0x52b060,0x52a8d0,0x52c520,
                       0x52d840,0x528a70,0x518a90,0x52ac20,0x524820):self.visits.append(hex(address))
        owner=vm.reg_read(x.UC_X86_REG_ECX)
        if address==0x51e6e0:
            side,slot,kind=self.args(3)
            assert side&255<2 and slot&255<14
            self.done(12,self.actor((side&255)*14+(slot&255)))
        elif address==0x5224a0:self.done(4)
        elif address==0x45f490:
            assert tuple(v&255 for v in self.args(2))==(0,150)
            self.done(8,GATE+0x100)
        elif address==0x547af7:
            dest,fmt,val=self.args(3)
            val=struct.unpack('<i',struct.pack('<I',val))[0]
            pattern=bytes(vm.mem_read(fmt,32)).split(b'\0')[0]
            rendered=pattern.replace(b'%+d',f'{val:+d}'.encode()).replace(b'%d',str(val).encode())
            vm.mem_write(dest,rendered+b'\0');self.done(0,len(rendered))
        elif address==0x41b330:self.events.append({'release':self.args(1)[0]});self.done(4)
        elif address==0x51dc00:
            self.events.append({'allocate':owner});self.put(owner+0xa,37,'<h')
            renderer=RETURN+0x5000;graphic=renderer+0x10+37*0x290
            self.put(owner+4,renderer)
            self.vm.mem_write(graphic,bytes(0x290));self.put(graphic,2,'<B')
            self.put(graphic+0xe,0xffff,'<H')
            self.vm.mem_write(graphic+0x256,b'\xff'*34)
            self.put(graphic+0x38,RETURN+0xf000)
            self.put(RETURN+0xf010,10)
            self.done(24,37)
        elif address==0x51de40:
            dest,txt=self.args(2)
            self.events.append({'text':bytes(vm.mem_read(txt,32)).split(b'\0')[0].decode('ascii'),'owner':dest});self.done()
        elif address in (0x51dd70,0x51dcc0):
            self.events.append({'visibility':hex(address),'owner':owner})
        elif address==0x508f50:
            self.events.append({'bar':list(self.args(3))});self.done(12)
        elif address==0x508fc0:self.done(12)
        elif address==0x509240:self.done(4,1)
        elif address==0x509200:self.done(8)
        elif address==0x529870:
            self.events.append({'pose':list(self.args(3))});self.done(12)
        elif address==0x52a200:self.done(12)
        elif address==0x52a710:self.done(8)
        elif address in (0x520300,0x45f450):
            self.events.append({'release_render_resources':hex(address)});self.done()
        elif address in (0x402c70,0x402b10):raise AssertionError('Native diagnostic at '+hex(address))

    def call(self,address,args=(),owner=WAR):
        self.vm.mem_write(SP,struct.pack('<'+'I'*(len(args)+1),RETURN,*[v&0xffffffff for v in args]))
        self.vm.reg_write(x.UC_X86_REG_ESP,SP)
        self.vm.reg_write(x.UC_X86_REG_ECX,owner)
        self.vm.reg_write(x.UC_X86_REG_EFLAGS,2)
        self.stops=set()
        try:self.vm.emu_start(address,RETURN,count=300000,timeout=3000000)
        except Exception as e:raise RuntimeError(f'native failure EIP={self.vm.reg_read(x.UC_X86_REG_EIP):08x}') from e
        assert self.vm.reg_read(x.UC_X86_REG_EIP)==RETURN
        assert self.vm.reg_read(x.UC_X86_REG_ESP)==SP+4+4*len(args)
        return self.vm.reg_read(x.UC_X86_REG_EAX)

    def dispatch(self,logical=None,pending=0):
        if logical is not None:
            self.vm.mem_write(BUFFER,logical)
            self.vm.mem_write(QUEUE,struct.pack('<5I',0,BUFFER,0,len(logical),4096))
        self.put(GATE,0xffffffff)
        self.put(GATE+4,pending)
        self.put(SP+0x28,GATE);self.put(SP+0x2c,GATE+4)
        self.put(BATTLE+0xa9ea4c4,1)
        self.vm.reg_write(x.UC_X86_REG_ESP,SP)
        self.vm.reg_write(x.UC_X86_REG_ESI,BATTLE)
        self.stops={0x52ac20}
        try:self.vm.emu_start(0x5142f0,RETURN,count=300000,timeout=3000000)
        except Exception as e:raise RuntimeError(f'dispatch EIP={self.vm.reg_read(x.UC_X86_REG_EIP):08x}') from e
        assert self.vm.reg_read(x.UC_X86_REG_EIP)==0x52ac20
        return {'cursor':self.get(QUEUE+8),'pending':self.get(GATE+4),
                'queue_continue':self.get(BATTLE+0xa9ea4c4)}


def command_checks():
    from tools.skills.verify_shunying_command import (CurrentSkillCommandTests,
        NativeSetupCommandTest,CurrentSkillTargetSetupTests,original_setup,targeting)
    CurrentSkillCommandTests.setUpClass()
    t=NativeSetupCommandTest()
    t.native_definition=decode_definitions((OUTPUT/CATALOG).read_bytes())[0,150].raw
    setup=CurrentSkillTargetSetupTests();setup.image=t.image
    vm=setup.target_machine()
    t.native_setup=original_setup(setup,vm,5)
    assert t.native_setup==(1,1)
    rows=[]
    try:
        fields=targeting.Fields.from_record(t.native_definition)
        for side in (0,1):
            for count in (1,2,14):
                enemy_side=1-side
                targets=tuple(enemy_side*14+i for i in range(count))
                raw,_,_,_=t.builder(targets,action=3,skill=True,skill_id=150,
                    actor=0,modes=(1,0) if side==0 else (0,1),poison=0)
                assert len(raw)==17 and raw[2]==3 and raw[13]==150
                masks=struct.unpack_from('<HH',raw,5)
                assert masks[enemy_side]==0x3fff and masks[side]==0
                # The target helper's actor is local slot0..13, not packed side.
                state=targeting.TargetState((1,(1<<count)-1),(0,0),(None,)*28)
                result=setup.compare_masks(vm,fields,0,state)
                rows.append({'side':side,'remaining':count,'command_hex':raw.hex(),
                    'native_target_masks':result.masks,'wire_masks':masks})
    finally:CurrentSkillCommandTests.doClassCleanups()
    return rows


def decode_frame(wire):
    assert wire[0]+256*wire[1]==len(wire)
    body=(ROOT/'src/protocol/RecoveredZeroSeedKey.h').read_text().split('recovered_zero_seed_key{',1)[1].split('}',1)[0]
    key=list(map(int,re.findall(r'\d+',body)));assert len(key)==256
    previous=0;checksum=(wire[0]+wire[1]+120)&255;logical=[]
    for i,byte in enumerate(wire[2:]):
        previous=((byte+3-previous)&255)^key[i&255]
        if i==len(wire)-3:assert previous==checksum
        else:logical.append(previous);checksum=(checksum+previous+60)&255
    return bytes(logical)


def result_checks(application=None):
    fixtures=OUT/'blackbox-server-wire.json'
    fixture=json.loads(fixtures.read_text(encoding='utf-8'))
    assert fixture['status']=='PASS'
    if application:
        app=json.loads(application.read_text(encoding='utf-8'))
        assert app['accepted'] and app['source_db_unchanged']
        logical_frames=[bytes.fromhex(c['received_decoded_logical']) for c in app['cast_frames']]
        assert len(logical_frames)==2
        first_action=next(i for i in range(len(logical_frames[0])) if logical_frames[0][i:i+2]==b'\x83\x03')
        fixture['cases'].append({'side':0,'source_slot':logical_frames[0][first_action+2],
            'scenario':'full_Application_two_rounds','targets':14,'sparse_target_bit':-1,
            'target_slot_start':14,'initial_target_hp':10000,'initial_source_mp':9999,
            'logical_frames':logical_frames,'wire_frames':logical_frames})
    rows=[]
    for case in fixture['cases']:
        # Negative-command cases intentionally have no skill reply.
        if not case.get('wire_frames'):continue
        n=Native();side=case['side'];source_slot=case.get('source_slot',side*14);source=n.actor(source_slot)
        bits=[case['sparse_target_bit']] if case['sparse_target_bit']>=0 else list(range(case['targets']))
        target_slots=[case['target_slot_start']+i for i in bits]
        n.put(source+0xde8,100);n.put(source+0xdf0,100)
        n.put(source+0xdec,case['initial_source_mp']);n.put(source+0xdf4,case['initial_source_mp'])
        for slot in target_slots:
            n.put(n.actor(slot)+0xde8,case['initial_target_hp'])
            n.put(n.actor(slot)+0xdf0,case['initial_target_hp'])
        rounds=[]
        for wire in case['wire_frames']:
            logical=wire if case.get('logical_frames') else decode_frame(wire)
            offset=0;records=[]
            while offset<len(logical):
                opcode=logical[offset]
                length={0x83:15,0x86:17,0x88:121}[opcode]
                records.append(logical[offset:offset+length]);offset+=length
            actions=[r for r in records if r[0]==0x83]
            assert len(actions)==len(target_slots)
            assert records[-1][0]==0x88
            assert all(r[1]==1 and r[2]==source_slot for r in records if r[0]==0x86)
            before=[n.get(n.actor(slot)+0xde8) for slot in target_slots]
            # Original ingestion normally begins a fresh native batch here.
            n.put(BATTLE+0xa9df6b8,1)
            held=n.dispatch(logical)
            assert held['pending']==1 and held['queue_continue']==0
            assert held['cursor']==len(logical)-121
            assert [n.get(n.actor(slot)+0xde8) for slot in target_slots]==before
            count=n.get(source+0x239,'<B');assert count==len(target_slots)
            totals=[n.get(source+0x28a+i*2,'<h') for i in range(count)]
            assert totals==[struct.unpack_from('<h',r,9)[0] for r in actions]
            final_states=[n.get(source+0x224+i,'<B') for i in range(count)]
            pending_before=[n.get(n.actor(slot)+0x277,'<B') for slot in target_slots]
            assert pending_before==[1]*count
            phase_rows=[]
            # Independent schedule oracle invokes ORIGINAL x86 ABI helpers.
            # Scheduling/death bookkeeping is fixture code, not compiled custom C++.
            for phase,(tick,lo,hi) in enumerate(zip((70,110,150,190),(0,20,45,75),(20,45,75,100))):
                losses=[]
                for i,slot in enumerate(target_slots):
                    target=n.actor(slot);loss=-totals[i]*hi//100-(-totals[i])*lo//100
                    losses.append(loss)
                    n.put(source+0x239,i,'<B')
                    n.call(0x52b060,(side,source_slot%14,slot//14,slot%14,-loss,0,0,28))
                    n.put(source+0x239,count,'<B');n.put(source+0x28a+i*2,totals[i],'<h')
                    n.call(0x528a70,(target,-loss));n.call(0x52d9f0,(target,))
                    n.call(0x51dcc0,owner=source+0x310+i*16)
                    graphic=RETURN+0x5000+0x10+37*0x290
                    assert n.get(graphic,'<B')==2 # Actual51DCC0 ->41B740 visibility writer.
                    if phase==3 and final_states[i]==9:
                        assert n.get(target+0x277,'<B')==1
                        n.put(target+0x277,0,'<B')
                    assert n.get(target+0xde8)==max(0,before[i]-((-totals[i])*hi//100))
                phase_rows.append({'tick':tick,'losses':losses,
                    'hp':[n.get(n.actor(slot)+0xde8) for slot in target_slots]})
                assert n.get(QUEUE+8)==held['cursor'] # Bulk still unread.
            after=[n.get(n.actor(slot)+0xde8) for slot in target_slots]
            assert after==[max(0,hp+total) for hp,total in zip(before,totals)]
            shown=[e for e in n.events if e.get('visibility')=='0x51dcc0']
            assert len(shown)>=4*count
            n.put(source+0x233,7,'<B')
            assert n.call(0x524820,(source,))==1
            assert n.get(source+0x239,'<B')==0 and n.get(source+0x259,'<B')==1
            for i,slot in enumerate(target_slots):
                if final_states[i]==9:
                    assert n.get(n.actor(slot)+0x1ea,'<B')==9
                    assert n.get(WAR+0x2f4+(slot//14)*4)&(1<<(slot%14))==0
            released=n.dispatch()
            assert n.get(QUEUE+0xc)==0 # Native queue compaction clears consumed length.
            assert n.get(BATTLE+0xa9df6b8)==0
            assert [n.get(n.actor(slot)+0xde8) for slot in target_slots]==after
            rounds.append({'logical_sha256':hashlib.sha256(logical).hexdigest(),
                'opcodes':[hex(r[0]) for r in records],'target_slots':target_slots,
                'hp_before':before,'hp_after_native_receive':before,'accepted_totals':totals,
                'native_final_states':final_states,'pending_hits_after_receive':pending_before,
                'bulk_held':held,'phases':phase_rows,'hp_after':after,
                'native_phase7_completed':True,'bulk_consumed_and_batch_reset':True})
        rows.append({'side':side,'scenario':case['scenario'],'targets':case['targets'],'rounds':rounds})
    return rows,hashlib.sha256(fixtures.read_bytes()).hexdigest()


def stale_86_regression():
    case=json.loads((OUT/'blackbox-server-wire.json').read_text())['cases'][0]
    logical=decode_frame(case['wire_frames'][0])
    stale=bytearray(17);stale[:3]=bytes((0x86,0,14))
    struct.pack_into('<II',stale,5,2000,1703)
    n=Native();n.put(n.actor(14)+0xde8,2000);n.put(n.actor(14)+0xdf0,2000)
    n.dispatch(logical[:-121]+bytes(stale)+logical[-121:])
    # Reproduce the removed bug using ORIGINAL86; the negative control matters.
    assert n.get(n.actor(14)+0xde8)==1703
    return {'old_per_target_86_reproduces_early_hp':True,'before':2000,'before_first_hit':1703}


def main():
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--application',type=Path)
    arguments=parser.parse_args()
    commands=command_checks()
    results,fixture_sha=result_checks(arguments.application)
    report={'status':'PASS','native_image_sha256':PIN,'server_fixture_sha256':fixture_sha,
        'native_command_cases':commands,'native_receive_cases':results,
        'stale_86_negative_control':stale_86_regression(),
        'application_evidence':{'path':str(arguments.application),
            'sha256':hashlib.sha256(arguments.application.read_bytes()).hexdigest()} if arguments.application else None,
        'native_entries':['518E50 command producer','51EAD0/51EE90 target helpers',
            '5142F0 dispatcher/51D3D0 queue','516AE0/52C520/52A8D0/52B060 result ingestion',
            '5173A0 MP scalar','528A70 HP','52D9F0 HP bar','51DCC0 floating text visibility',
            '524820/526430 phase7 cleanup','518A90/52D360 final88'],
        'limitations':['Synthetic actor and selected-skill fixtures; no F1 key or mouse interaction',
            'Route lookup, actor lookup, text formatting/allocation and draw sinks substituted',
            'Native activation scan stops at52AC20; custom scheduler independently modeled, not run by this oracle',
            'Phase7 and final88 execute original instructions; render-resource release calls are sinks',
            'Does not establish live visual, audio, real-time performance, or full Application acceptance']}
    out=OUT/'client-flow-native.json';out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'PASS','command_cases':len(commands),'receive_cases':len(results),'output':str(out)}))


if __name__=='__main__':main()
