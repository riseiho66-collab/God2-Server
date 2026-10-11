"""Pinned original21 sender and role-panel one-point branch, offline only."""
import json,struct
from .current_dialogue_mode4_native_20260926 import Native,require,sha,ROOT,UI,RESOURCE,QUEUE,RETURN,pefile,SHA

def audit():
    raw=(ROOT.parent/'God2/God2.exe').read_bytes();require(sha(raw)==SHA,'Client pin changed');pe=pefile.PE(data=raw)
    rows=[]
    for control,selector,index in ((20,2,0),(21,3,1),(22,1,2),(23,4,3)):
        n=Native(pe,[b'']);role=RESOURCE+0x10000;n.write(UI+0x86888,'I',role)
        n.write(role+0x90,'H',4);n.vm.mem_write(role+0x78,struct.pack('<4I',10,20,30,40))
        n.write(UI+0x232dda,'h',0)
        # The imported OS clock and unrelated modal-UI reset are fixture boundaries.
        n.vm.mem_write(0x5ff000,b'\xb8\x88\x13\x00\x00\xc3');n.write(0x5707bc,'I',0x5ff000)
        n.setup(control,0x20);require(n.run(0x4e8910,[0x4b1a80])==0x4b1a80,'Click branch missing')
        sp=n.reg('ESP');ret=n.read(sp,'I');n.setreg('ESP',sp+8)
        n.run(ret,[0x5077c0]);expected=[10,20,30,40];expected[index]+=1
        require(list(struct.unpack('<4I',n.vm.mem_read(role+0x78,16)))==expected,'Wrong original stat mutation')
        require(n.read(role+0x90,'H')==3,'Wrong original budget mutation')
        require(n.calls==[{'opcode':0x21,'payload':bytes([selector]).hex()}],'Unexpected allocation queue call')
        # Execute the entire primitive sender independently, including queue append.
        p=Native(pe,[b'']);p.setup(selector);p.run(0x496300,[RETURN])
        length=p.read(QUEUE+0x36c4,'I');wire=bytes(p.vm.mem_read(QUEUE+0x36c8,length))
        require(wire==bytes((0x21,selector)),'Wrong exact native logical record')
        rows.append({'control':control,'selector':selector,'stat_index':index,'logical_hex':wire.hex(),
            'points_before':4,'points_after':3,'stats_after':expected})
    return {'exe_sha256':SHA,'cases':rows,'native_sender':'496300 -> 4132E0',
        'native_event':'4E8910 -> 4E8AEC..4E8CA4',
        'mocked_boundaries':['GetTickCount constant5000','4B1A80 modal-UI reset; one argument'],
        'authority':'NATIVE_VERIFIED one-point local mutation and outbound structure; no derived attack/HP formulas'}

if __name__=='__main__':
    result=audit();path=ROOT/'artifacts/research/character-growth-native-20260927/allocation-binding.json'
    path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'native_allocation_cases':len(result['cases'])}))
