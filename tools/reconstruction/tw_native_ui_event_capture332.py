from pathlib import Path
import hashlib,json
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
OUT=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012/tw-native-petegg-event-control-source-332')
INPUT=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012/tw-native-entry-body-alias-and-remote-opaque-315/native-entry')
BASE=INPUT.parent.parent
SERVER=Path('C:/Users/risei/Desktop/God2/God2-Server')
sha=lambda b:hashlib.sha256(b).hexdigest()
image=(INPUT/'native-image.bin').read_bytes();original=(INPUT/'originalPE.bin').read_bytes()
if sha(image)!='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763' or sha(original)!='5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde':raise RuntimeError('Image pins changed')
pe=pefile.PE(data=original);md=Cs(CS_ARCH_X86,CS_MODE_32);target=OUT/'native-final';target.mkdir(exist_ok=False);cuts=[]
def cut(name,va,end,scope,code=True):
 raw=image[va-0x400000:end-0x400000];off=pe.get_offset_from_rva(va-0x400000)
 if raw!=original[off:off+len(raw)]:raise RuntimeError('PE range differs')
 rows=list(md.disasm(raw,va)) if code else []
 if code and sum(i.size for i in rows)!=len(raw):raise RuntimeError('Incomplete static decode')
 (target/(name+'.bin')).write_bytes(raw)
 if code:(target/(name+'.tsv')).write_text('va\tbytes\tmnemonic\toperands\n'+''.join(f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}\n' for i in rows),encoding='utf8')
 item=dict(name=name,va=f'{va:08X}',end_exclusive=f'{end:08X}',bytes=len(raw),sha256=sha(raw),original_pe_offset=off,original_pe_equal=True,code=code,instruction_sites=len(rows),scope=scope);cuts.append(item)
 return rows
rows=cut('actual-event-output-complete',0x504620,0x504c84,'Complete actual native method and both RET8, direct UI field/output writes; all children opaque. Not a queue, authoritative result, lease or owned source.')
addresses={i.address for i in rows};jumps=[];calls=[]
for i in rows:
 if i.mnemonic.startswith('j'):
  addr=int(i.op_str,16)
  if addr not in addresses:raise RuntimeError('Jump leaves complete method')
  jumps.append(dict(va=f'{i.address:08X}',target=f'{addr:08X}',kind=i.mnemonic))
 if i.mnemonic=='call':calls.append(dict(va=f'{i.address:08X}',target=i.op_str,scope='Opaque child; no transitive execution or semantic claim'))
rets=[dict(va=f'{i.address:08X}',bytes=i.bytes.hex(),pop_bytes=int(i.op_str)) for i in rows if i.mnemonic=='ret']
if [r['va'] for r in rets]!=['00504958','00504C81']:raise RuntimeError('RET inventory drift')
(target/'control-flow.json').write_text(json.dumps(dict(rets=rets,direct_jumps=jumps,opaque_direct_calls=calls),indent=2)+'\n')
cut('actual-parent-output-alias-and-prefix',0x48224a,0x4822e2,'Selected original329 parent fragment; actual ECX/stack aliases, intervening child order and signed DI gate; historical no new parent coverage')
cut('actual-parent-deferred16-branch',0x482733,0x482752,'Selected original329 parent fragment; DI match U232E9C, low width locals passed actual4DA730; historical')
cut('actual-parent-deferred23-branch',0x482790,0x4827af,'Selected original329 parent fragment; DI match U232EA2, low width locals passed actual4DC880; historical')
cut('event-entry-boundary-before',0x504614,0x504620,'Raw boundary evidence only; not code qualification',False)
cut('event-entry-boundary-after',0x504c84,0x504c90,'Raw padding boundary after last RET; adjacent method excluded',False)
parent=BASE/'tw-native-petegg-selection-source-329/native/primary-action-dispatch-complete.bin'
parentraw=parent.read_bytes()
if parentraw!=image[0x4820a0-0x400000:0x48314f-0x400000]:raise RuntimeError('Immutable full parent changed')
refs=[dict(path=str(INPUT/n),bytes=len(b),sha256=sha(b),copied=False) for n,b in [('native-image.bin',image),('originalPE.bin',original)]]
priorrefs=[parent,BASE/'tw-native-petegg-selection-source-329/native/primary-action-dispatch-complete.tsv',BASE/'tw-native-petegg-selection-source-329/native/cuts.json',BASE/'tw-native-petegg-selection-source-329/seal.json',BASE/'tw-native-petegg-alternative-actions-source-330/native/alternative16-action-complete.tsv',BASE/'tw-native-petegg-alternative-actions-source-330/native/alternative23-action-complete.tsv',BASE/'tw-native-petegg-alternative-actions-source-330/seal.json']
refs += [dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p.read_bytes()),copied=False,scope='Selected immutable references, not a whole historical closure verification') for p in priorrefs]
(target/'input-references.json').write_text(json.dumps(refs,indent=2)+'\n')
(target/'cuts.json').write_text(json.dumps(cuts,indent=2)+'\n')
sources=[]
for n in ['AGENTS.md','docs/GOAL_ACCEPTANCE.md','docs/research/tw-native-petegg-deferred-b1-source-20261012.md','docs/research/tw-native-petegg-e7-list-source-20261012.md']:
 p=SERVER/n;raw=p.read_bytes();dest=OUT/'source'/n;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);sources.append(dict(path=str(p),bytes=len(raw),sha256=sha(raw),retained=str(dest.relative_to(OUT))))
(OUT/'source-references.json').write_text(json.dumps(sources,indent=2)+'\n')
metrics=dict(final_cuts=len(cuts),code_bytes=sum(c['bytes'] for c in cuts if c['code']),data_bytes=sum(c['bytes'] for c in cuts if not c['code']),instruction_sites=sum(c['instruction_sites'] for c in cuts),full_event_method_bytes=0x504c84-0x504620,full_event_ret_count=len(rets),native_descendants_opened=0,all_final_cuts_pe_equal=True,parent_new_credit=0,global_new_coverage_claim=False,new_opcode=0,new_complete_routes=0,denominator=None,percent=None)
(OUT/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n');print(json.dumps(metrics))
