"""Current quest notification and direct producer/consumer frontier.

Executes original DB subtype1/2 receiver and original sound routines through
return with the real constructor's absent-device state. Only timeGetTime is
adapted; no game function is replaced. No quest/reward authority is inferred.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

import capstone
import pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn import x86_const as x
from .omega_assets import decode_csvz

ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT.parent/'God2'
PE_PIN = '6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'
IMAGE_PIN = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
BASE, UI, SOUND, STACK, PACKET, STOP, API = 0x400000, 0x10000000, 0x20000000, 0x30000000, 0x40000000, 0x31000000, 0x32000000
SP = STACK+0x8000
SPANS = ((0x854f0,0x856d0), (0x4d9f0,0x4db90), (0x4db90,0x4dc43),
         (0x4e320,0x4e4e8), (0xc9670,0xc9770), (0x97dc0,0x97e00),
         (0xc84a0,0xc84d0), (0x96750,0x967b0), (0xc9260,0xc9390),
         (0xb9f8d,0xba060), (0x6b44e,0x6b46e))


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


class Oracle:
    def __init__(self, image):
        self.v = v = Uc(UC_ARCH_X86, UC_MODE_32)
        for at,size in ((0,4096), (BASE,(len(image)+4095)&~4095), (UI,0x240000),
                        (SOUND,0x16000), (STACK,0x10000), (PACKET,4096), (STOP,4096), (API,4096)):
            v.mem_map(at,size)
        v.mem_write(BASE,image)
        self.put(BASE+0x1707bc,API)
        self.put(UI+0xcff5c,SOUND)
        # Distinct nonzero owned state sentinels, not native actor/save values.
        v.mem_write(UI+0xc2104,bytes((17+i*3)&255 for i in range(60)))
        v.mem_write(UI+0x85610,bytes((29+i*7)&255 for i in range(50*24)))
        self.sound_calls=[]; self.writes=[]; self.steps=0; self.os_calls=0
        self.record=False
        v.hook_add(UC_HOOK_CODE,self.code)
        v.hook_add(UC_HOOK_MEM_WRITE,self.write)
        self.call(0x4d9f0,SOUND,[],0)
        require(bytes(v.mem_read(SOUND,4))==bytes(4), 'Original constructor device must be absent')
        require(bytes(v.mem_read(SOUND+0x7f19,1))==b'\x01', 'Original sound-enabled state')
        self.before_ui=sha(bytes(v.mem_read(UI,0x240000)))
        self.before_code=sha(bytes(v.mem_read(BASE,0x170000)))

    def put(self,at,*values):
        self.v.mem_write(at,struct.pack('<'+'I'*len(values),*(n&0xffffffff for n in values)))

    def word(self,at):
        return struct.unpack('<I',self.v.mem_read(at,4))[0]

    def code(self,v,at,size,_):
        self.steps+=1
        if at==API:
            self.os_calls+=1
            sp=v.reg_read(x.UC_X86_REG_ESP)
            v.reg_write(x.UC_X86_REG_EAX,123456)
            v.reg_write(x.UC_X86_REG_EIP,self.word(sp));v.reg_write(x.UC_X86_REG_ESP,sp+4)
            return
        require(BASE<=at<BASE+0x170000,'Unexpected native execution '+hex(at))
        if self.record and at in (0x44db90,0x44e320):
            sp=v.reg_read(x.UC_X86_REG_ESP)
            self.sound_calls.append({'entry_va':hex(at),'this':v.reg_read(x.UC_X86_REG_ECX),
                                     'args':[self.word(sp+4+i*4) for i in range(1 if at==0x44db90 else 7)]})

    def write(self,v,access,at,size,value,_):
        if self.record:
            self.writes.append({'va':at,'size':size,'pc':v.reg_read(x.UC_X86_REG_EIP)})

    def call(self,rva,obj,args,cleanup):
        self.put(SP,STOP,*args)
        self.v.reg_write(x.UC_X86_REG_ESP,SP)
        self.v.reg_write(x.UC_X86_REG_ECX,obj)
        self.v.reg_write(x.UC_X86_REG_EFLAGS,2)
        self.steps=0
        self.v.emu_start(BASE+rva,STOP,count=200000)
        require(self.v.reg_read(x.UC_X86_REG_EIP)==STOP,'Native budget / return')
        require(self.v.reg_read(x.UC_X86_REG_ESP)==SP+4+cleanup,'Native stack cleanup')
        return self.v.reg_read(x.UC_X86_REG_EAX)

    def consume(self,packet):
        require(len(packet)==13 and packet[0]==0xdb,'Exact DB logical record required')
        self.v.mem_write(PACKET,packet)
        self.record=True
        self.call(0x854f0,UI,[PACKET+1,0x12345678,0x9abcdef0],12)
        self.record=False
        subtype=packet[1]
        expected=603 if subtype==1 else struct.unpack_from('<H',packet,9)[0] if subtype==2 else None
        require(len(self.sound_calls)==(0 if expected is None else 2),'Sound call count')
        if expected is not None:
            first,second=self.sound_calls
            require(first['args'][0]&65535==expected and second['args'][1]&65535==expected,'Sound selector preservation')
            require(first['this']==SOUND and second['this']==SOUND,'Sound owner')
            require(second['args'][2:]==[0]*5,'Unexpected playback arguments')
        require(sha(bytes(self.v.mem_read(UI,0x240000)))==self.before_ui,'UI/journal/inventory changed')
        require(sha(bytes(self.v.mem_read(BASE,0x170000)))==self.before_code,'Native code changed')
        require(bytes(self.v.mem_read(PACKET,13))==packet,'Packet changed')
        require(all(at['va']<4 or STACK<=at['va']<STACK+0x10000 or SOUND<=at['va']<SOUND+0x16000 for at in self.writes),
                'Unexpected gameplay/global write')
        return {'logical_hex':packet.hex(),'subtype':subtype,'selected_sound_word':expected,
                'calls':self.sound_calls,'steps':self.steps,'time_api_calls':self.os_calls,
                'ui_journal_inventory_unchanged':True,'native_return':True,
                'playback_verified':False,'device_fixture':'original constructor leaves null device'}


def run():
    raw=(CLIENT/'God2.exe').read_bytes();require(sha(raw)==PE_PIN,'Current executable pin')
    image=pefile.PE(data=raw).get_memory_mapped_image()
    saved=(ROOT/'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin').read_bytes()
    require(sha(saved)==IMAGE_PIN,'Mapped image pin')
    spans=[]
    for a,b in SPANS:
        require(image[a:b]==saved[a:b],'Native code span mismatch '+hex(a))
        spans.append({'start_rva':hex(a),'end_rva':hex(b),'sha256':sha(image[a:b])})
    length=struct.unpack_from('<I',image,0x1324+4*0xdb)[0]-BASE
    length_oracle=Oracle(image)
    require(length_oracle.call(length,0,[],0)==13,'Original DB length routine')
    require(struct.unpack_from('<I',image,0x6b5d4+4*0xdb)[0]==0x46b44e,'World DB dispatch target')
    raw=(CLIENT/'Data2/Snd/commsnd.csvZ').read_bytes();plain=decode_csvz(raw)
    require(sha(raw)=='e5704115a5ec39cd97f9712dd5bfb1163e502671faaae65d7f45d9e541a11f0d','Sound source pin')
    require(sha(plain)=='b34f206476b0b307fdbc153b1322c680698fc3bf41f29102a4aa1c1a8cc6dc5f','Sound decoded pin')
    row=plain.splitlines()[605];require(row==b'603,MissionEnd.wav','Exact source sound603')
    wav=(CLIENT/'Data2/Snd/MissionEnd.wav').read_bytes()
    require(sha(wav)=='29192eb5cae137878d2848e4e603aaffb834d437cb47a6de16bcdc122cb1f711','MissionEnd WAV pin')
    require(wav[:4]==b'RIFF' and wav[8:12]==b'WAVE','Source audio header')
    cases=[]
    for subtype in (0,1,2,6,255):
        keys=(0,1,603,669,1023,1024,32767,32768,65535) if subtype==2 else (0,0x1234,65535)
        for key in keys:
            for poison in (0,0xa5,0xff):
                packet=bytearray([poison]*13);packet[:2]=bytes([0xdb,subtype])
                struct.pack_into('<H',packet,9,key)
                cases.append(Oracle(image).consume(bytes(packet)))
    rejects=[]
    for packet in (bytes(12),b'\xdb'+bytes(13),b'\xda'+bytes(12)):
        try:Oracle(image).consume(packet)
        except ValueError as error:rejects.append(str(error))
        else:raise ValueError('Invalid record fixture accepted')
    # Scoped direct displacement/call audit; this is not all indirect dataflow.
    offsets={}
    for target in (0xb2c58,0xb2c5c,0xc2104):
        hits=[];at=0;needle=struct.pack('<I',target)
        while True:
            at=image.find(needle,at,0x170000)
            if at<0:break
            hits.append(hex(BASE+at));at+=4
        offsets[hex(target)]=hits
    calls={}
    for target in (0x4c9670,0x497dc0,0x4c84a0):
        hits=[hex(BASE+n) for n in range(0x1000,0x170000)
              if image[n]==0xe8 and BASE+n+5+struct.unpack_from('<i',image,n+1)[0]==target]
        calls[hex(target)]=hits
    require(calls['0x4c9670']==['0x485665','0x4856a6'],'New journal setter caller requires audit')
    require(calls['0x497dc0']==['0x4c8447','0x4c84b8','0x4c8589'],'New dialogue producer caller requires audit')
    require(calls['0x4c84a0']==['0x496776'],'New pending-reply flush caller requires audit')
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
    disassembly={hex(BASE+a):['%08X %s %s'%(i.address,i.mnemonic,i.op_str)
                             for i in md.disasm(image[a:b],BASE+a)] for a,b in SPANS}
    require(len(cases)==63 and len(rejects)==3,'Case count')
    return {'status':'PASS','current_pe_sha256':PE_PIN,'mapped_sha256':IMAGE_PIN,
            'counts':{'native_notification_cases':len(cases),'fixture_rejections':len(rejects),
                      'new_quest_transition_rules':0,'qualified_reward_rules':0},
            'sound_source':{'file':'Data2/Snd/commsnd.csvZ','file_sha256':sha(raw),'decoded_sha256':sha(plain),
                            'physical_line':606,'raw_hex':row.hex(),'row_sha256':sha(row),
                            'wav':'Data2/Snd/MissionEnd.wav','wav_sha256':sha(wav),'wav_bytes':len(wav)},
            'native_cases':cases,'fixture_rejections':rejects,'direct_displacement_refs':offsets,
            'direct_call_refs':calls,'code_spans':spans,'disassembly':disassembly,
            'scope':'Complete DB1/2/default consumers and real absent-device sound routines; original timeGetTime adapted. Not sound playback, live acceptance, quest completion, consumption or rewards.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    require(args.output.resolve().is_relative_to((ROOT/'artifacts/research/quest-transition-frontier-20260927').resolve()),'Output scope')
    result=run();args.output.parent.mkdir(parents=True,exist_ok=True)
    pending=args.output.with_suffix('.pending');pending.write_text(json.dumps(result,indent=2),encoding='utf-8');pending.replace(args.output)
    print(json.dumps(result['counts']))
