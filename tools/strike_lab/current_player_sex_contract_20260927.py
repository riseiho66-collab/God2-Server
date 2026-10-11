"""Current create UI sex labels -> native fields; no client/DB/UI mutation.

Executes bounded original instruction slices, stopping before drawing or queueing.
The weapon-description predicate is a source-backed server policy candidate,
not a recovered original-server equip refusal implementation.
"""
import argparse
import json
import struct
from pathlib import Path
from .current_dialogue_mode4_native_20260926 import Native, require, sha, ROOT, UI, PACKET, RETURN, pefile, SHA
from .current_weapon_selector_authority_20260926 import chunks
from .omega_assets import decode_csvz

PINS={
 'Data2/Patch/FlowComm.csvZ':'27a0660b158d0cfcfe6afd5a01fcae91f98732d0f73efdde953b9d98fbe717e1',
 'data3/flow/FlowGui.ROMZ':'2ad797d15aa6daa6562652fb69d39c9e3dbbdc108965c230c199735c8e682503',
 'Data2/Patch/Comm/gamedata.csvZ':'70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731',
}


def profile_sex(profile):
    # Only a persisted raw first40 bytes from the qualified17/1B producer.
    if len(profile)!=40 or not 1<=profile[29]<=8 or profile[33] not in (0,1):return None
    if ((profile[29]-1)&1)!=profile[33] or (profile[38]&15)!=profile[33]:return None
    return profile[33]


def audit():
    client=ROOT.parent/'God2';raw=(client/'God2.exe').read_bytes()
    require(sha(raw)==SHA,'Current client mismatch');pe=pefile.PE(data=raw)
    sources={}
    for name,pin in PINS.items():
        data=(client/name).read_bytes();require(sha(data)==pin,'Source mismatch '+name)
        sources[name]=decode_csvz(data,limit=32*1024*1024)
    flow=sources['Data2/Patch/FlowComm.csvZ'].splitlines()
    require(flow[4].startswith(b'0,FlowGui.ROM,'),'Flow group0 binding changed')
    actions=[b for tag,b in chunks(sources['data3/flow/FlowGui.ROMZ']) if tag==b'ACT_DATA']
    labels=[]
    for i,name in ((95,'Flow_CarBoyH'),(96,'Flow_CarBoyL'),(97,'Flow_CarGirlH'),(98,'Flow_CarGirlL')):
        actual=actions[i][24:48].split(b'\0')[0].decode('ascii')
        require(actual==name,'Native action name changed')
        labels.append(dict(action_index=i,action_id=struct.unpack_from('<I',actions[i])[0],name=actual))
    for table in (0x183088,0x183608):
        require(struct.unpack('<2h',pe.get_data(table+4*8,4))==(95,96),'Boy control binding changed')
        require(struct.unpack('<2h',pe.get_data(table+5*8,4))==(97,98),'Girl control binding changed')
    cases=[]
    for entry,refresh,sender,builder,opcode in ((0x4097a0,0x409680,0x40c0b0,0x414cf0,0x17),
                                               (0x40c680,0x40c580,0x40c160,0x414cc0,0x1b)):
        for initial in range(8):
            for sex,control in ((0,15),(1,16)):
                n=Native(pe,[b'']);profile=bytearray(range(40));profile[29]=initial;profile[31]=3
                n.vm.mem_write(UI+0x15280,bytes(profile));n.setup(control,1)
                n.run(entry,[refresh]);observed=bytes(n.vm.mem_read(UI+0x15280,40))
                expected=profile.copy();expected[29]=(initial//2)*2+sex;expected[33]=sex
                require(observed==bytes(expected),'Native sex event changed unexpected profile field')
                n.setup(PACKET,PACKET+4);n.run(sender,[builder]);sp=n.reg('ESP');ptr=n.read(sp+4,'I')
                wire=bytes(n.vm.mem_read(ptr,40));expected[29]+=1;expected[31]+=1
                expected[38]=(expected[38]&0xf0)|sex
                require(wire==bytes(expected),'Native create field projection mismatch')
                require(profile_sex(wire)==sex,'Candidate persisted-profile predicate differs')
                # Existing2A portrait binding: body20..23 stack block -> actor458C.
                portrait=bytes((wire[36]&0xe7,0,wire[38],wire[39]))
                n.setup();sp=n.reg('ESP');n.setreg('EBP',UI)
                n.vm.mem_write(sp+0x34,bytes(8)+portrait);n.write(sp+0x48,'I',0)
                n.run(0x468315,[0x468376])
                require(bytes(n.vm.mem_read(UI+0x458c,4))==portrait,'2A portrait copy mismatch')
                n.write(UI+0x232e50,'h',0);n.setup(UI+0x458c);n.run(0x4abe80,[0x5068c0])
                sp=n.reg('ESP');bank=n.read(sp+8,'I')
                require(bank==21+sex,'HUD portrait sex bank mismatch')
                cases.append(dict(opcode=hex(opcode),initial_category=initial,control=control,sex=sex,
                    persisted_profile_hex=wire.hex(),portrait_hex=portrait.hex(),hud_bank=bank,
                    stops=[hex(refresh),hex(builder),'0x468376','0x5068c0']))
    for case in cases:
        p=bytearray.fromhex(case['persisted_profile_hex'])
        for offset,value in ((29,0),(29,9),(33,2),(33,1-case['sex']),
                             (38,(p[38]&0xf0)|(1-case['sex']))):
            bad=p.copy();bad[offset]=value;require(profile_sex(bad) is None,'Inconsistent profile accepted')
    rows=sources['Data2/Patch/Comm/gamedata.csvZ'].splitlines();restricted=[]
    for family,count in (('WPN',630),('TWP',629)):
        start=next(i for i,r in enumerate(rows) if r==f'{family},{count}'.encode())
        for index,row in enumerate(rows[start+1:start+1+count],start+1):
            fields=row.split(b',');notes=[v.decode('cp950') for v in fields[7:13]]
            sexes=[sex for sex,text in ((0,'限男性角色裝備'),(1,'限女性角色裝備')) if any(text in n for n in notes)]
            require(len(sexes)<=1,'Conflicting native restriction text')
            if sexes:restricted.append(dict(family=family,key=int(fields[0]),source_line=index+1,
                name=fields[4].decode('cp950'),required_sex=sexes[0],notes=notes,raw_hex=row.hex()))
    require(len(restricted)==69,'69-row description scope changed')
    return dict(schema='current-player-sex-contract-20260927',status='PASS',exe_sha256=SHA,
        sources=[dict(path=p,raw_sha256=h,decoded_sha256=sha(sources[p])) for p,h in PINS.items()],
        flow_group0_line=dict(line=5,raw=flow[4].decode('cp950')),action_labels=labels,
        vectors=cases,restricted_weapons=restricted,
        scope='32 native event+prequeue create+portrait-copy+HUD-first-call slices; male0/female1 from exact ROM action names and UI binding. Does not run full renderer, send packets, infer model binary or prove original server weapon refusal.')


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=audit();a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('PASS32 native sex/create/portrait slices; 69 source restrictions; '+str(a.output))


if __name__=='__main__':main()
