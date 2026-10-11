"""Execute pinned native blade3 RTB side selection; no live process/UI writes.

RTB/ROM bytes are real trial files. Coordinates are fixture inputs, allocation
is observed at the native ACT boundary; this is not rendered-client acceptance.
"""
from pathlib import Path
import hashlib
import json
import struct
from unicorn import UC_PROT_READ, UC_PROT_WRITE
from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_EAX
from tools.strike_lab.current_battle_entry import NativeRun, BASE, SP, RETURN
from tools.strike_lab.current_monster_binary_producer import parse_rtb
from tools.skills.build_shunying_client import chunks, decode_csvz, PINS, ROUTES, CATALOG, decode_definitions

ROOT = Path(__file__).resolve().parents[2]
TRIAL = ROOT/'artifacts/playtests/private-shunying-manual-thousand-bulls-20260930-01/client'
RTB = 'Data2/Fight/Spg/spg9008.rtb'
ROM = 'Data2/Fight/Spg/spg9006.ROMZ'


def case(raw, layout, actions, side, slot, target_slot):
    n=NativeRun()
    owner, manager, bank, table, arena, targets = (0x3400000,0x3600000,0x3700000,0x3800000,0x3900000,0x3a00000)
    n.map(owner,0xa7000)
    n.map(manager,0x1000)
    n.map(bank,0x2000)
    n.vm.mem_protect(0x5b5000,0x1000,UC_PROT_READ|UC_PROT_WRITE)
    n.put32(owner+0xa654c,manager)
    n.put32(manager+0xc,bank)
    n.put32(bank+0x108c,len(actions))
    for i,action in enumerate(actions):
        n.put32(bank+0x1090+i*4,arena+i*4)
        n.put32(arena+i*4,action)
    n.put(owner+0xa1042,raw[8:12])
    n.put(owner+0xa104c,raw[12:14])
    n.put32(owner+0xa1048,table)
    n.put(table,raw[14:])
    for rec in layout['records']:
        n.put32(table+rec['index']*52+48,table+rec['frames_start']-14)
    target=(1-side)*128+target_slot
    n.put(targets,bytes([target]))
    n.put(SP,struct.pack('<9I',RETURN,0,0,0,side*128+slot,1,targets,0,0))
    n.registers(ecx=owner,esp=SP)
    created=[];pc=0x2f6a0
    for _ in range(100):
        n.run(pc,[(0x2f6a0,0x2fe80),(0x1ae20,0x1ae70)],{0x11e630,0x1afe0},budget=30000)
        if n.stop==RETURN:break
        sp=n.vm.reg_read(UC_X86_REG_ESP);ret=n.get32(sp)
        if n.stop==0x11e630:
            s,t=(n.get32(sp+4)&255,n.get32(sp+8)&255)
            assert s in (0,1) and t<14
            point=arena+0x1000+(s*14+t)*8
            n.put(point,struct.pack('<ii',500-t*10 if s==0 else 200+t*20,350-t*10 if s==0 else 200+t*30))
            value,argc=point,0 # cdecl; original caller removes both arguments
        else:
            args=[n.get32(sp+4+i*4) for i in range(8)]
            created.append(dict(action=args[3],mode=args[4]&255,x=args[1],y=args[2],depth=args[5]))
            # Do not render/allocate ACTs; observe the real call arguments.
            value,argc=0xffff,8
        n.registers(eax=value,esp=sp+4+argc*4)
        pc=ret-BASE
    assert n.stop==RETURN and n.vm.reg_read(UC_X86_REG_ESP)==SP+36
    assert n.vm.reg_read(UC_X86_REG_EAX)==1
    expected=[20510,20520,20530] if side==0 else [20110,20120,20130]
    assert [c['action'] for c in created]==expected,(side,created)
    active=[i for i in range(layout['objects']) if n.get32(owner+0x34+i*32)==2]
    assert active==([3,4,5] if side==0 else [0,1,2])
    return dict(caster_side=side,caster_slot=slot,target_side=1-side,target_slot=target_slot,
                active_tracks=active,native_created=created)


def main():
    raw=(TRIAL/RTB).read_bytes();rom=(TRIAL/ROM).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==PINS[RTB]
    assert hashlib.sha256(rom).hexdigest()==PINS[ROM]
    # Pin the installed custom-to-native route as well as the referenced files.
    routes=[row.split(b',') for row in decode_csvz((TRIAL/ROUTES).read_bytes()).splitlines()]
    native_route=next(row for row in routes if row[:2]==[b'r1',b'8'])
    custom_route=next(row for row in routes if row[:2]==[b'r1',b'126'])
    assert custom_route[2:6]==native_route[2:6]==[b'9008',b'data2\\fight\\spg\\spg9006.rom',b'data2\\fight\\spg\\spg9008.rtg',b'324']
    catalog=decode_definitions((TRIAL/CATALOG).read_bytes())
    assert catalog[0,126].raw[70:]==catalog[0,8].raw[70:]
    actions=[struct.unpack_from('<I',d)[0] for t,d,_ in chunks(decode_csvz(rom)) if t==b'ACT_DATA']
    layout=parse_rtb(raw)
    cases=[case(raw,layout,actions,side,slot,target) for side in (0,1) for slot in range(14) for target in (0,13)]
    report=dict(status='NATIVE_DIRECTION_SELECTION_PASSED',cases=cases,passed=len(cases),
                native_entry='0042F6A0',native_action_lookup='0041AE20',
                native_image_sha256=hashlib.sha256(NativeRun().image).hexdigest(),
                resource_sha256={RTB:PINS[RTB],ROM:PINS[ROM]},
                installed_custom126_route_matches_native8=True,
                live_rendered_acceptance=False,
                limitations='Formation coordinates are fixture inputs; ACT creation is intercepted, not rendered.')
    out=ROOT/'artifacts/custom-skills/shunying/direction-native.json'
    out.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=len(cases),friendly_actions=[20510,20520,20530],enemy_actions=[20110,20120,20130],report=str(out))))


if __name__=='__main__':main()
