from pathlib import Path
import hashlib,json,struct
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
OUT=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012/tw-native-petegg-operation-selection-source-336')
BASE=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012')
INPUT=BASE/'tw-native-entry-body-alias-and-remote-opaque-315/native-entry'
SERVER=Path('C:/Users/risei/Desktop/God2/God2-Server')
sha=lambda b:hashlib.sha256(b).hexdigest()
image=(INPUT/'native-image.bin').read_bytes();original=(INPUT/'originalPE.bin').read_bytes()
assert sha(image)=='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
assert sha(original)=='5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde'
pe=pefile.PE(data=original);md=Cs(CS_ARCH_X86,CS_MODE_32);target=OUT/'native-final';target.mkdir(exist_ok=False);cuts=[];flow={}
def cut(name,va,end,code,scope,complete=False):
 raw=image[va-0x400000:end-0x400000];off=pe.get_offset_from_rva(va-0x400000);assert raw==original[off:off+len(raw)]
 rows=list(md.disasm(raw,va)) if code else []
 if code:assert sum(r.size for r in rows)==len(raw)
 (target/(name+'.bin')).write_bytes(raw)
 if code:(target/(name+'.tsv')).write_text('va\tbytes\tmnemonic\toperands\n'+''.join(f'{r.address:08X}\t{r.bytes.hex()}\t{r.mnemonic}\t{r.op_str}\n' for r in rows),encoding='utf8',newline='\n')
 cuts.append(dict(name=name,va=f'{va:08X}',end_exclusive=f'{end:08X}',bytes=len(raw),code=code,instruction_sites=len(rows),sha256=sha(raw),original_pe_offset=off,original_pe_equal=True,scope=scope))
 if complete:
  sites={r.address for r in rows};jumps=[];calls=[]
  for r in rows:
   if r.mnemonic.startswith('j'):
    dest=int(r.op_str,16);assert dest in sites;jumps.append(dict(va=f'{r.address:08X}',target=f'{dest:08X}',kind=r.mnemonic))
   if r.mnemonic=='call':calls.append(dict(va=f'{r.address:08X}',target=r.op_str,scope='Selectedcontroller/status relations documented; other childrenopaque'))
  flow[name]=dict(rets=[dict(va=f'{r.address:08X}',pop=r.op_str) for r in rows if r.mnemonic=='ret'],jumps=jumps,calls=calls)
 return rows
for name,va,end,pad in [('controller-default-complete',0x4d78d0,0x4d78f8,0x4d7900),('controller-bit29-complete',0x4d7900,0x4d7936,0x4d7940),('controller-status-complete',0x4d7980,0x4d7da3,0x4d7db0),('operation-ui-parameters-complete',0x4d5e40,0x4d628a,0x4d6290),('controller-reset-complete',0x4d7de0,0x4d7de7,0x4d7df0)]:
 cut(name,va,end,True,'Complete directselected controller, not globalnovelty/authority; UI childrenopaque',True)
 cut(name+'-padding-after',end,pad,False,'Raw boundarypadding, adjacentmethods excluded')
cut('known-open-selected-type0e-branch',0x4d55ee,0x4d562f,True,'Needed CALL/branch operands within historicalfullOpen, no wholemethod recredit')
cut('known-open-selected-type0f-branch',0x4d565a,0x4d56a9,True,'Needed CALL/branch operands within historicalfullOpen, no wholemethod recredit')
cut('known-primary-action-selected-parent',0x4826f5,0x482714,True,'Prior329 actualsameU formalcall to4D6940, branchprefix only historicalwholeparent')
(target/'cuts.json').write_text(json.dumps(cuts,indent=2)+'\n',encoding='utf8',newline='\n')
(target/'control-flow.json').write_text(json.dumps(flow,indent=2)+'\n',encoding='utf8',newline='\n')
refs=[dict(path=str(INPUT/n),bytes=len(b),sha256=sha(b),copied=False) for n,b in [('native-image.bin',image),('originalPE.bin',original)]]
prior_specs=[('tw-native-e5-egg-input-source-328',['seal.json','native/cuts.json','native/known-egg-open-complete.bin','native/known-egg-open-selector-table.bin','native-refresh/known-egg-refresh-complete.bin']),('tw-native-petegg-selection-source-329',['seal.json','native/action-complete.bin','native/action-table.bin','native/action-targets.tsv','native/action-state-leaf.bin','native/action-eligibility-leaf.bin','native/b1-producer-complete.bin','native/primary-action-dispatch-complete.bin','native/primary-action-main-prefix.bin']),('tw-native-petegg-e7-list-input-source-331',['seal.json','native/e7-receiver-complete.bin','native/e7-state-word-leaf-complete.bin']),('tw-native-petegg-event-control-source-332',['seal.json']),('tw-native-petegg-list-nonzero-source-333',['seal.json','native/status30-32-ui-helper-complete.bin','native-extra/selected-ui-forwarder-complete.bin','native-extra/selected-return-leaf-complete.bin'])]
comparisons=[]
for folder,names in prior_specs:
 for name in names:
  p=BASE/folder/name;raw=p.read_bytes();refs.append(dict(path=str(p),bytes=len(raw),sha256=sha(raw),copied=False,scope='Selected immutableprior source reference, not wholearchive closureaudit'))
  ranges={'native/known-egg-open-complete.bin':0x4d53f0,'native-refresh/known-egg-refresh-complete.bin':0x4d5970,'native/action-complete.bin':0x4d6940,'native/action-table.bin':0x4d6b74,'native/action-state-leaf.bin':0x4d7df0,'native/action-eligibility-leaf.bin':0x4d68c0,'native/b1-producer-complete.bin':0x4d6ba0,'native/primary-action-dispatch-complete.bin':0x4820a0,'native/e7-receiver-complete.bin':0x4d6340,'native/e7-state-word-leaf-complete.bin':0x4d7db0,'native/status30-32-ui-helper-complete.bin':0x4d94d0,'native-extra/selected-ui-forwarder-complete.bin':0x4d98b0,'native-extra/selected-return-leaf-complete.bin':0x4d97f0}
  if name in ranges:
   va=ranges[name];off=pe.get_offset_from_rva(va-0x400000);assert raw==image[va-0x400000:va-0x400000+len(raw)]==original[off:off+len(raw)]
   comparisons.append(dict(path=str(p),va=f'{va:08X}',bytes=len(raw),sha256=sha(raw),mapped_equal=True,original_pe_equal=True,original_pe_offset=off))
(OUT/'input-references.json').write_text(json.dumps(refs,indent=2)+'\n',encoding='utf8',newline='\n')
(OUT/'selected-prior-byte-comparisons.json').write_text(json.dumps(comparisons,indent=2)+'\n',encoding='utf8',newline='\n')
sources=[]
for rel in ['AGENTS.md','docs/GOAL_ACCEPTANCE.md','docs/research/tw-native-e6-petegg-input-source-20261012.md','docs/research/tw-native-petegg-selection-and-b1-source-20261012.md','docs/research/tw-native-petegg-e7-list-source-20261012.md','src/protocol/RecoveredPetEggControl.h']:
 p=SERVER/rel;raw=p.read_bytes();dest=OUT/'source'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);sources.append(dict(path=str(p),bytes=len(raw),sha256=sha(raw),retained=dest.relative_to(OUT).as_posix()))
(OUT/'source-references.json').write_text(json.dumps(sources,indent=2)+'\n',encoding='utf8',newline='\n')
metrics=dict(final_cuts=len(cuts),code_bytes=sum(r['bytes'] for r in cuts if r['code']),data_bytes=sum(r['bytes'] for r in cuts if not r['code']),instruction_sites=sum(r['instruction_sites'] for r in cuts),complete_direct_controller_ranges=len(flow),complete_controller_rets=sum(len(v['rets']) for v in flow.values()),prior_byte_comparisons=len(comparisons),new_primary_selectors=0,new_opcodes=0,new_codecs=0,new_authority_rules=0,new_complete_routes=0,runtime_gameplay_count=0,denominator=None,completion_percent=None)
(OUT/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n',encoding='utf8',newline='\n');print(json.dumps(metrics))
