from pathlib import Path
import json,hashlib,subprocess
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
O=Path(__file__).resolve().parent;A=O.parent;S=Path('C:/Users/risei/Desktop/God2/God2-Server');h=lambda b:hashlib.sha256(b).hexdigest()
def put(n,b):
 p=O/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b)
def out(n,v):put(n,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
# Native-call source leads and complete intraprocedural facts, no general caller
# or cbspec2-text interpretation inferred from a metadata function label.
root=S/'artifacts/integration/packet-connections-20261006/cn-native-skill-book-bindings-source-01'
# Reference read existing qualified lookup docs; never execute native/decoder.
pepath=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe');b=pepath.read_bytes();assert h(b)=='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8';pe=pefile.PE(data=b,fast_load=True);md=Cs(CS_ARCH_X86,CS_MODE_32)
metadata=json.loads((O/'candidate/selected-entry-metadata.json').read_bytes());facts=[]
for m in metadata:
 lo=int(m['start'],16);raw=b[m['physical_PE_offset']:m['physical_PE_offset']+m['metadata_size']];assert h(raw)==m['sha256'];ins=list(md.disasm(raw,lo));starts={i.address for i in ins};branches=[]
 for i in ins:
  if i.mnemonic.startswith('j'):
   dest=int(i.op_str,16);assert dest in starts;branches.append(dict(va=f'{i.address:08X}',target=f'{dest:08X}'))
 rets=[dict(va=f'{i.address:08X}',cleanup=i.op_str) for i in ins if i.mnemonic=='ret'];assert rets
 # Each old declared inbound CALL site must encode a call to this actual entry.
 inbound=[]
 for line in m['inbound_static_metadata']:
  cols=line.split('\t');site=int(cols[1],16);off=pe.get_offset_from_rva(site-0x400000);code=b[off:off+5];decoded=list(md.disasm(code,site));assert len(decoded)==1 and decoded[0].mnemonic=='call' and int(decoded[0].op_str,16)==lo
  put(f'call-sites/cn-{site:08X}.bin',code);inbound.append(dict(parent_metadata=cols[0],site=f'{site:08X}',bytes=5,sha256=h(code),PE_offset=off,complete_parent_not_recaptured=True))
 facts.append(dict(**m,branches=branches,returns=rets,entry_CALL_bytes_verified=inbound,physical_local_body_complete=True,new_method_credit=0,scope='direct local instructions only; source/success/fault/memory/caller-wide behavior conditional'))
out('native-text-consumer-local-proof.json',dict(entries=facts,critical='Both MP/name readers take WORD42 from incoming110record but stringpointer is lookup(kind,id)->returned396item+8, not raw110record+2/20. Itemlookup fallback/currentbank remains source condition.',cbspec_direct_text_widths_qualified=False,shorttext_nativeconsumer_qualified=False,CRT_UI_children_expanded=False))
# Verify existing sealed all-record raw evidence rather than rerun its extraction.
rawroot=A/'round358-skills-raw-three-source-audit';seal=(rawroot/'seal.json').read_bytes();assert h(seal)=='e46c925c8503768b71b51cd6efbfe2c950aecdd4b0f4c627c0d309f80b3cf003';z=json.loads(seal)
for m in z['members']:
 p=rawroot/m['path'];assert p.resolve().is_relative_to(rawroot.resolve());bb=p.read_bytes();assert len(bb)==m['bytes'] and h(bb)==m['sha256']
assert len(z['members'])==35 and sum(m['bytes'] for m in z['members'])==2756012
out('raw-source-individual-reference.json',dict(root=rawroot.as_posix(),seal_sha256=h(seal),members=35,member_bytes=2756012,individual_members=z['members'],helper_rerun=False))
# Candidate full150 source is distinct from current installed453 original/addon.
cp=S/'artifacts/custom-skills/thousand-bulls/client-candidate/Data2/Fight/Spg/cbspec2.bin';c=cp.read_bytes();assert len(c)==112660 and c[:4]==b'1.03';count=int.from_bytes(c[4:8],'little');assert count==150
source453=(rawroot/'raw/tw_installed/cbspec2.bin').read_bytes()
for kind,n in enumerate([126,129,87,111]):
 for ident in range(1,n+1):
  off=8+kind*0x6e04+(ident-1)*110;assert c[off:off+110]==source453[off:off+110]
off150=8+149*110;record=c[off150:off150+110];base=source453[8+72*110:8+73*110];expected=bytearray(base);expected[0]=150
for offset,text in [(2,'牛轉仙界踏'),(32,'牛轉仙界踏 全體物理')]:expected[offset:offset+30]=text.encode('cp950').ljust(30,b'\0')
assert record==bytes(expected)
put('retained-custom150-record.bin',record)
out('custom150-candidate-fullrecord-reference.json',dict(actual_path=cp.as_posix(),bytes=len(c),sha256=h(c),counts=[int.from_bytes(c[4+k*0x6e04:8+k*0x6e04],'little') for k in range(4)],declared_rows=477,profile='candidate-only ownerCUSTOM0059; not installed TW453 or CNnative857',record_offset=off150,record_sha256=h(record),base_kind=0,base_id=73,all_installed453_records_unchanged=True,reserved127to149_not_native_skills=True,CN_added_profile_required=True,CN_extension_implemented=False))
files=['src/db/NativeSkillCatalog.h','src/db/NativeSkillCatalog.cpp','src/cn/assets/CnNativeSkillCatalog.h','src/cn/assets/CnNativeSkillCatalog.cpp','src/cn/assets/CnSharedSkillCatalog.h','src/cn/assets/CnSharedSkillCatalog.cpp','src/cn/net/SharedCredentialServer.h','src/cn/net/SharedCredentialServer.cpp','src/handlers/RecoveredBattleService.h','src/handlers/RecoveredBattleService.cpp','src/game/ShunyingSanshazhan.h','src/game/ThousandBulls.h','tools/skills/build_shunying_client.py','tools/skills/build_thousand_bulls_client.py','docs/research/cn-native-skill-book-bindings-source-20261008.md','docs/research/current-skill-book-binding-20260920.md','src/core/Application.cpp']
refs=[]
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=S).decode().strip()
for f in files:
 bb=(S/f).read_bytes();rel='source/'+f;put(rel,bb);refs.append(dict(actual_path=(S/f).as_posix(),retained=rel,bytes=len(bb),sha256=h(bb),source_state='actual current read-only; incidental gitHEAD recorded, not a new baseline authorisation'))
out('source-references.json',refs)
out('read-only-source-context.json',dict(observed_HEAD=head,tracked_mutations=0,root_baseline359_authorization_pending=True,source_current_hashes=sum(r['bytes'] for r in refs)))
print(json.dumps(dict(native_local_code=253,inbound_CALL_bytes=20,cbspec_native_text_widths_closed=False,custom150_source_hash=h(c),custom150_record_sha=h(record),source_refs=len(refs),source_bytes=sum(r['bytes'] for r in refs))))
