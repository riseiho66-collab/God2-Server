"""Bounded current original x86 source396 vs instance20 header evidence.
No UI, network, server or modifications of existing tooling/source.
"""
import argparse,json,struct,hashlib
from pathlib import Path
import pefile
import unicorn as uc
from .current_protocol_coverage import qualified_image
from .current_armor_20261002 import CAPTURE,ArmorMetadata
from .current_armor_projection_20261002 import ArmorProbe,BASE,PIN,LIVE,PACKET,SP
from . import current_item_metadata as metadata
from . import recover_companion_growth as growth
ROOT=Path(__file__).resolve().parents[2]
def require(ok,message):
    if not ok:raise RuntimeError(message)
def sha(value):return hashlib.sha256(value).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output-dir',type=Path,default=ROOT/'artifacts/research/current-armor-source-instance-20261002');args=ap.parse_args()
    raw=LIVE.read_bytes();require(sha(raw)==PIN,'Current client changed');pe=pefile.PE(data=raw);mapped=pe.get_memory_mapped_image();original=qualified_image()
    old=metadata.CLIENT;metadata.CLIENT=CAPTURE
    try:n=ArmorMetadata()
    finally:metadata.CLIENT=old
    visited=set()
    def match(v,a,size,_):
        if n.active_code and a!=n.stop_address:
            require(bytes(v.mem_read(a,size))==mapped[a-BASE:a-BASE+size],f'Current parser/lookup mismatch{a:x}');visited.add(a)
    n.vm.hook_add(uc.UC_HOOK_CODE,match)
    definitions=[];lookup=[];differentials=[]
    flags=(0,0x00400000,0x00800000,0x01000000,0x40000000,0x80000000)
    for section,expected_family in (('EQU',2),('TEQ',26)):
        row=n.sections[section]['records'][0];tokens=growth.fields(row);key=int(tokens[0]);baseline=n.item_row(section,0)['record']
        require(struct.unpack_from('<II',baseline)==(int(tokens[5]),int(tokens[6])),'Definition firstDWORD is not source5/6')
        definitions.append({'source_family':section,'item_key':key,'loader_selector':expected_family,'definition_first8':baseline[:8].hex(),'source_columns5_6':[int(tokens[5]),int(tokens[6])]})
        for column,value in ((5,b'123456'),(6,b'654321')):
            changed=list(tokens);changed[column]=value
            n.sections[section]['records'][0]=growth.record(b','.join(changed)+b'\n',row['source_line'],row['decoded_offset'])
            try:result=n.item_row(section,0)['record']
            finally:n.sections[section]['records'][0]=row
            expected=bytearray(baseline);struct.pack_into('<I',expected,0 if column==5 else 4,int(value))
            require(result==expected,'Price/cost differential changes unexpected definition field')
            differentials.append({'source_family':section,'source_column':column,'value':int(value),'only_definition_offset':0 if column==5 else 4})
        n.item_row(section,0,retain=True)
        for family in (2,26):
            for highflags in flags:
                header=key|(family<<16)|highflags
                ptr=n.call(0x59a60,header);require(ptr==n.RECORD+16,'59A60 unexpectedly validates family/highflags')
                lookup.append({'source_family':section,'item_key':key,'firstDWORD':hex(header),'instance_family':family,'highflags':hex(highflags),'lookup_return':hex(ptr),'exact_admission':family==expected_family})
        n.vm.mem_write(n.TABLE+0xb2d40+key*4,bytes(4));n.retained_key=None
    branch=[]
    targets={f:struct.unpack_from('<I',original,0xbc188+original[0xbc1d0+f-1]*4)[0] for f in (2,26)}
    for family in (2,26):
        for flags_value in (0,0x80000000):
            p=ArmorProbe(pe,original);header=1001|(family<<16)|flags_value;p.write(PACKET,'I',header);p.setup();p.write(SP+0x11ac,'I',PACKET);p.setreg('EDX',0)
            p.run(0x4b6414,set(targets.values()));require(p.reg('EIP')==0x4b8bee,'Native family branch differs')
            branch.append({'header':hex(header),'native_stop':'0x4b8bee','family':family,'bit31':bool(flags_value)})
    result={'status':'PASS','current_client_sha256':sha(raw),'mapped_image_sha256':sha(original),'definitions':definitions,'definition_differentials':differentials,'lookup_cases':lookup,'family_branch_cases':branch,'current_instruction_addresses':[hex(a) for a in sorted(visited)],
      'findings':{'definition':'Native59420 source column5→definition+0DWORD; source6→+4DWORD. Neither is item key/family header.',
       'lookup':'Native59A60 tests lowWORD<7F58, masksFFFF and reads global item index. Entire firstDWORD variants select identical source pointer, including crossed2/26 and bit31.',
       'family':'Native4B6426 extracts bits16..21; both2/26 branch4B8BEE. Native lookup/tooltip therefore does not establish strict source-family admission.',
       'admission':'Server source-instance consistency should compare owned key and expected family from qualified EQU2/TEQ26 namespace, rather than allow either armor family. This is explicit consistency policy, not native equip denial.',
       'flags':'Bits22..31 survive header and do not affect demonstrated lookup/family branch. No claim that every combination is authoritatively grantable, transferable or bindable. Do not compare or copy definition lowDWORD into an instance.',
       'scope':'Bounded machine source parser, native lookup and family branch only; no new appearance/stats formulas and no real UI acceptance'}}
    args.output_dir.mkdir(parents=True,exist_ok=True);(args.output_dir/'native.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('PASS',len(differentials),'definition differentials',len(lookup),'native lookup cases',len(branch),'native family cases')
if __name__=='__main__':main()
