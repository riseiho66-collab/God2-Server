"""Pinned original create profession event/sender and UI stat binding evidence."""
import json
import struct
from .current_player_sex_contract_20260927 import PINS
from .current_dialogue_mode4_native_20260926 import Native,require,sha,ROOT,UI,PACKET,pefile,SHA
from .current_four_stat_ui_binding import parse_rom,descriptors,IMAGE_PATH,IMAGE_SHA
from .omega_assets import decode_csvz

def audit():
    client=ROOT.parent/'God2';raw=(client/'God2.exe').read_bytes();require(sha(raw)==SHA,'Current client changed');pe=pefile.PE(data=raw)
    path=client/'Data3/Flow/FlowGui.ROMZ';rom_raw=path.read_bytes();require(sha(rom_raw)==PINS['data3/flow/FlowGui.ROMZ'],'Flow art changed')
    rom=parse_rom(decode_csvz(rom_raw));names=['Flow_TipSword','Flow_TipWizard','Flow_TipRuse','Flow_TipDoctor']
    for index,name in enumerate(names):require(rom['actions'][56+index]['name']==name,'Profession action order changed')
    cases=[]
    for entry,refresh,sender,builder,opcode in ((0x4097a0,0x409680,0x40c0b0,0x414cf0,0x17),
                                              (0x40c680,0x40c580,0x40c160,0x414cc0,0x1b)):
        for category in range(4):
            for sex in range(2):
                n=Native(pe,[b'']);profile=bytearray(40);profile[0]=65;profile[29]=0;profile[31]=0;profile[33]=sex
                n.vm.mem_write(UI+0x15280,bytes(profile));n.setup(11+category,1);n.run(entry,[refresh])
                observed=bytes(n.vm.mem_read(UI+0x15280,40));expected=profile.copy();expected[29]=2*category+sex
                require(observed==bytes(expected),'Unexpected native class event mutation')
                n.setup(PACKET,PACKET+4);n.run(sender,[builder]);ptr=n.read(n.reg('ESP')+4,'I');wire=bytes(n.vm.mem_read(ptr,40))
                expected[29]+=1;expected[31]+=1;expected[38]=(expected[38]&0xf0)|sex
                require(wire==bytes(expected),'Native profession sender mismatch')
                cases.append({'opcode':opcode,'control':11+category,'sex':sex,'wire29':wire[29],
                              'catalog_class_id':[1,2,4,3][category],'original_action_name':names[category]})
    image=IMAGE_PATH.read_bytes();require(sha(image)==IMAGE_SHA,'Mapped image changed')
    controls=descriptors(image,0x196db8,32)
    labels=[{'control':control,'actor_offset':offset,'label':label,'descriptor':controls[control]}
            for control,offset,label in ((14,0x78,'體力'),(15,0x7c,'力量'),(16,0x80,'智力'),(17,0x84,'速度'),(22,0x90,'剩餘點數'))]
    return {'native_event_sender_cases':cases,'case_count':len(cases),'exe_sha256':SHA,'mapped_image_sha256':IMAGE_SHA,
            'flow_rom_sha256':sha(rom_raw),'stat_labels':labels,
            'label_basis':'Visual transcription of original Status_BGOpen and Flow_TipWizard/Ruse/Doctor assets; TipSword original name',
            'growth_formula_origin':'OWNER_CONFIRMED_20260927, not derived from client arithmetic','runtime_activated':False}

if __name__=='__main__':
    report=audit();p=ROOT/'artifacts/research/character-growth-native-20260927';p.mkdir(exist_ok=True)
    (p/'binding.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'native_event_sender_cases':report['case_count'],'source_pins':'PASS'}))
