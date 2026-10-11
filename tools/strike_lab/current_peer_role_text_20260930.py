"""Current-PE-qualified full native6F secondary-text consumer and replacement.

Uses the existing resource-backed original world/display oracle and its explicit
OS/CRT adapters. No game setter is mocked; no process, socket or production DB
is opened. Native replacement discards queued interpolation, which is reported
and tested rather than being represented as a text-only update.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'artifacts/tooling/crypto-oracle-python')]
import pefile
from unicorn import UC_HOOK_CODE,UC_PROT_ALL
from unicorn.x86_const import UC_X86_REG_ESI,UC_X86_REG_EBX,UC_X86_REG_EBP,UC_X86_REG_ESP
from tools.strike_lab.current_world_display import NativeWorldDisplay,DISPLAY_POOL,SCENE_BRIDGE
from tools.strike_lab.current_world_viewport import ROLE_POOL
from tools.strike_lab.current_world_actor import WORLD,PETDRV
from tools.strike_lab.current_battle_character_binding import NativeBattleCharacterBinding
from tools.strike_lab.current_indoor_resources import SCRATCH,SP

BASE=0x400000
CLIENT_SHA='9be38ef858bc9c63b6f296cae4a8e601ddcfaf614700e725c4bec44065b53336'
MAPPED_SHA='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
def require(value,message):
    if not value:raise ValueError(message)
def sha(raw):return hashlib.sha256(raw).hexdigest()


def verify():
    raw=(ROOT/'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin').read_bytes()
    current=(ROOT.parent/'God2/God2.exe').read_bytes()
    require(sha(raw)==MAPPED_SHA and sha(current)==CLIENT_SHA,'Native source pin changed')
    pe=pefile.PE(data=current);image=pe.get_memory_mapped_image()
    require(struct.unpack_from('<I',raw,0x6b5d4+4*0x6f)[0]==0x4695c8,'Native6F dispatch changed')
    leaf=struct.unpack_from('<I',raw,0x1324+4*0x6f)[0]-BASE
    require(raw[leaf:leaf+6]==bytes.fromhex('b851000000c3'),'Native6F length is not81')
    for start,end in ((leaf,leaf+6),(0x6b5d4+4*0x6f,0x6b5d8+4*0x6f),(0x1324+4*0x6f,0x1328+4*0x6f)):
        require(raw[start:end]==image[start:end],'Current PE dispatch/length mismatch')
    bodies=[];folder=ROOT/'artifacts/runs/native-remote-pool-baseline-20260921-01/crypto-private'
    for path in folder.glob('*.json'):
        meta=json.loads(path.read_text());plain=(folder/meta['plain_file']).read_bytes()
        if meta['direction']=='S2C' and plain[2]==0x2a:
            require(sha(plain)==meta['plain_sha256'] and meta['checksum_valid'],'Captured2A changed')
            bodies.append(plain[3:39])
    require(len(bodies)==1,'Exactly one qualified2A required')
    body=bytearray(bodies[0]);struct.pack_into('<H',body,24,2|(15<<6));struct.pack_into('<I',body,28,2|(17<<2)|(13<<17))
    native=NativeWorldDisplay();native.bind_title_resources();native.enter_scene(bytes(body))
    from tools.strike_lab.current_world_startup_assets import pinned_assets,ASSETS
    from tools.strike_lab.current_world_resource_banks import CWD
    resource=next(a for a in ASSETS if a.record==3);packed,plain=pinned_assets()[3]
    relative=resource.asset.lower();name=relative.rsplit('/',1)[-1]
    native.files[relative]=packed;native.decoded[name]=plain;native.asset_names[relative]=native.asset_names[relative[:-1]]=name
    native.vm.mem_write(SCRATCH,CWD+resource.literal_path.encode('ascii')+b'\0')
    status=native.call(0x60a90,SCRATCH,this=native.manager);require(status>=0,'Native status resource missing')
    native.vm.reg_write(UC_X86_REG_EBP,WORLD);native._slice(0x64f58,0x64f5e)
    binding=NativeBattleCharacterBinding(native.vm,root=native.actor_address,ui=WORLD+0xa7f2f6c,sp=SCRATCH+0x6000,packet=SCRATCH+0x6200)
    binding.bind_packet_source()
    native.call(0xfabb0,SCENE_BRIDGE,native.renderer_address,DISPLAY_POOL,native.title_slot,0,this=ROLE_POOL)
    native.vm.reg_write(UC_X86_REG_ESI,WORLD);native.vm.reg_write(UC_X86_REG_EBX,PETDRV);native._slice(0x64552,0x64558)
    block=bytes([1,0,1,0,1,0,0x81,0]);language=native.call(0x131c10);require(language in (0,1),'Native language flag')
    remote=bytearray(80);struct.pack_into('<I',remote,0,7|(language<<25));struct.pack_into('<I',remote,12,(18<<2)|(12<<17)|2)
    remote[20:28]=block;remote[28:44]=b'PrimaryHero\0'+bytes(4);remote[60:76]=b'FixedThird\0'+bytes(5)
    # The current owner-approved client includes frozen streamer/font wrappers.
    # Execute its actual .text and appended executable sections in this offline
    # VM; preserve captured imports/initialized original data used by adapters.
    current_sections=[]
    for section in pe.sections:
        name=section.Name.rstrip(b'\0').decode('ascii')
        if name=='.text' or name in ('.imefix','.stream','.fontcfg'):
            start=BASE+section.VirtualAddress;size=(max(section.Misc_VirtualSize,section.SizeOfRawData)+4095)&~4095
            native._map_rw(start,size);native.vm.mem_protect(start,size,UC_PROT_ALL)
            native.vm.mem_write(start,image[section.VirtualAddress:section.VirtualAddress+max(section.Misc_VirtualSize,section.SizeOfRawData)])
            current_sections.append([name,start,start+size])
    trace={};calls=set();cases=[];current_differences=set()
    def qualify(vm,address,size,_):
        if any(start<=address<end for _,start,end in current_sections):
            key=(address,size)
            if key not in trace:
                offset=address-BASE
                require(bytes(vm.mem_read(address,size))==image[offset:offset+size],f'Executed instruction differs in current PE at{address:x}')
                trace[key]=image[offset:offset+size]
                if raw[offset:offset+size]!=image[offset:offset+size]:current_differences.add(address)
                if image[offset]==0xe8 and size==5:calls.add(address+5+struct.unpack_from('<i',image,offset+1)[0])
    hook=native.vm.hook_add(UC_HOOK_CODE,qualify)
    def dispatch(opcode,payload,start):
        native.vm.mem_write(SCRATCH+0x5200,bytes([opcode])+bytes(payload));native.vm.reg_write(UC_X86_REG_ESP,SP)
        native.vm.reg_write(UC_X86_REG_EBP,WORLD);native.vm.reg_write(UC_X86_REG_EBX,SCRATCH+0x5200);native._slice(start,0x6b517)
        require(native.vm.reg_read(UC_X86_REG_ESP)==SP,'Native dispatch stack imbalance')
    def capture(actor):
        handle=struct.unpack('<h',native.vm.mem_read(actor+0x48,2))[0];require(0<=handle<4096,'Renderer handle missing')
        return {'identity':native.u32(actor),'fields':[native.string(actor+off,16).hex() for off in (4,0x14,0x24)],
            'renderer':[native.string(DISPLAY_POOL+handle*0xa7e0+off,17).hex() for off in (0x70,0x81,0x92)],
            'xy':list(struct.unpack('<II',native.vm.mem_read(actor+0x64,8))),
            'queue':bytes(native.vm.mem_read(actor+0xa9,2)).hex(),
            'appearance':{'components':[[bytes(native.vm.mem_read(actor+0x228+6*i,2)).hex(),native.vm.mem_read(actor+0x22c+6*i,1)[0]] for i in range(4)],
                'packed':bytes(native.vm.mem_read(actor+0x250,8)).hex(),'scalars':bytes(native.vm.mem_read(actor+0x262,4)).hex()}}
    def texts(actor,secondary):
        result=capture(actor);expected=(b'PrimaryHero',secondary,b'FixedThird')
        require(result['fields']==[x.hex() for x in expected],'Actor field mismatch')
        require(result['renderer']==[(b' '*max(0,(14-len(x))//2)+x).hex() for x in expected],'Renderer field mismatch')
        return result
    try:
        dispatch(0x6f,remote,0x695c8);actor=ROLE_POOL+0x18;initial=texts(actor,b'')
        other=bytearray(remote);struct.pack_into('<I',other,0,8|(language<<25));dispatch(0x6f,other,0x695c8)
        neighbor=actor+0x268;neighbor_before=bytes(native.vm.mem_read(neighbor,0x268));neighbor_display=capture(neighbor)
        for text in (b'RoleNativeProof',b'AB',b'',bytes.fromhex('a4a4a4e5') if language==0 else bytes.fromhex('d6d0cec4')):
            changed=bytearray(remote);changed[44:60]=text+bytes(16-len(text))
            require([i for i,(a,b) in enumerate(zip(changed,remote)) if a!=b]==[i for i in range(44,60) if changed[i]!=remote[i]],'Non-secondary wire change')
            dispatch(0x6f,changed,0x695c8);actual=texts(actor,text)
            require(actual['appearance']==initial['appearance'] and actual['xy']==initial['xy'],'Text replacement changed appearance or saved position')
            require(bytes(native.vm.mem_read(neighbor,0x268))==neighbor_before and capture(neighbor)==neighbor_display,'Unrelated peer changed')
            cases.append({'kind':'existing-replacement','secondary_hex':text.hex(),'native':actual})
        dispatch(0x5e,struct.pack('<III',7,0,19|(12<<11)),0x69a60)
        require(bytes(native.vm.mem_read(actor+0xa9,2))==b'\0\1','Native movement not queued')
        latest=bytearray(remote);latest[44:60]=b'LatestRole'+bytes(6);struct.pack_into('<I',latest,12,(19<<2)|(12<<17)|2)
        dispatch(0x6f,latest,0x695c8);actual=texts(actor,b'LatestRole')
        require(actual['queue']=='0000' and actual['xy']==[19,12],'Replacement must clear queue and install latest saved position')
        require(actual['appearance']==initial['appearance'],'Replacement changed component appearance')
        cases.append({'kind':'queued-movement-replacement','queue_cleared':True,'native':actual})
        dispatch(0x5e,struct.pack('<III',7,0,20|(12<<11)),0x69a60)
        require(bytes(native.vm.mem_read(actor+0xa9,2))==b'\0\1','Movement after replacement not accepted')
        require(struct.unpack('<II',native.vm.mem_read(actor+0xac,8))==(20,12),'Movement after replacement lost target')
        cases.append({'kind':'next-native5E','target':[20,12]})
        dispatch(0x73,struct.pack('<I',7),0x69a28);require(native.u32(actor)==0xffffffff,'Native remove failed')
        dispatch(0x6f,latest,0x695c8);cases.append({'kind':'fresh-insertion','native':texts(actor,b'LatestRole')})
        require(bytes(native.vm.mem_read(neighbor,0x268))==neighbor_before and capture(neighbor)==neighbor_display,'Late insertion changed neighbor')
        require(0x4fb460 in calls and 0x4fc560 in calls and 0x4fc1c0 in calls and 0x509e70 in calls,'Full original consumer path not executed')
    finally:native.vm.hook_del(hook)
    spans=[]
    for (address,size),value in sorted(trace.items()):
        if spans and spans[-1]['end']==address:spans[-1]['end']=address+size
        else:spans.append({'start':address,'end':address+size})
    for span in spans:span['sha256']=sha(image[span['start']-BASE:span['end']-BASE])
    return {'accepted':True,'client_sha256':CLIENT_SHA,'mapped_sha256':MAPPED_SHA,'language':language,
        'logical_size':81,'secondary_logical_offset_decimal':45,'secondary_actor_offset_hex':'14','renderer_offset_hex':'81',
        'executed_current_pe_instruction_count':len(trace),'executed_spans':spans,'cases':cases,
        'current_sections_executed':current_sections,'current_vs_captured_instruction_differences':sorted(current_differences),
        'replacement_side_effect':'Removes existing display, reconstructs actor and clears pending movement queue; requires latest committed position.',
        'cross_language_qualified':False,'actual_client_acceptance':False,
        'limits':['Native display buffers only, no host graphics device.','Existing resource oracle OS/CRT adapters remain explicit.','No dedicated text-only opcode inferred.']}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    result=verify();args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:result[key] for key in ('accepted','client_sha256','language','executed_current_pe_instruction_count','replacement_side_effect')}))
    return 0
if __name__=='__main__':raise SystemExit(main())
