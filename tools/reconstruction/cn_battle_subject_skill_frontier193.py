"""193 actual subject-row prerequisite and bounded initializer frontier.

Never runs native/C++/codec/DB/build/tests or edits shared source/accounting.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import io
import json
import capstone
import pefile

ROOT=Path(__file__).resolve().parents[2]
ROUND=ROOT/'artifacts/integration/packet-connections-20261006/cn-native-battle-skill-selection-source-01'
OUT=ROUND/'agents/cn-battle-subject-skill-frontier'
EXE=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe')
RECOVERY=EXE.parent.parent/'God2_opt_source_recovery_20260926_055734/decompiled'
PIN='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
BEFORE='6d48485ee39748151f27a3521e19de11feef6e4bc27ecbffed1276edef00ab73'
OWN='tools/reconstruction/cn_battle_subject_skill_frontier193.py'
STABLE=[OWN,
 'src/cn/world/SharedSubjectSkillPublication.h','src/cn/world/SharedSubjectSkillPublication.cpp',
 'src/cn/protocol/CnWorldSubjectSkillUpdate.h',
 'src/cn/world/CnPrebornSkillReferences.h','src/cn/world/CnPrebornSkillReferences.cpp',
 'src/cn/world/CnPrebornSubjectState.h','src/cn/world/CnPrebornSubjectState.cpp',
 'tools/reconstruction/cn_preborn_skill_reference_source_delivery.py',
 'tools/reconstruction/cn_world_subject_skill_format_source_delivery.py',
 'tools/reconstruction/cn_preborn_selected_subject_source_delivery.py',
 'tools/reconstruction/cn_native_skill_catalog_source_delivery.py']
GUIDELINES=['AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md']
ADDRESSES=['0048fcc0','004d5e60','004d5cc0','004af370','004d2d30','0048caa0',
 '00492e70','00543560','004d39c0','0054a320','00533300','00534640','004ac850']
SPANS=[
 (0x4d5e60,479,'retained_complete_consumer','Original WORLD34 subject update; old preborn skill-reference whole native evidence, no repeated recovery count.'),
 (0x4d5cc0,411,'retained_complete_consumer','Original WORLD35 subject update; flags3 is a local observation, not learned/cast authority.'),
 (0x48d3e2,110,'retained_bounded_owner','Actual constructor branch returns H or null, P+8885F0 saved; P+1478084 actual R passed to role initializer. Old selected-subject whole CFG.'),
 (0x493540,27,'retained_bounded_bank','Successful original role initialization R+4504=actual H+9D223C; old skill catalog explicitly proved same bank.'),
 (0x4af485,22,'retained_bounded_mode0_caller','Actual mode0 R+90 passed to4D2D30; old selected-subject whole source.'),
 (0x4d2d40,26,'retained_bounded_component_attachment','Actual argument copied to U+430A8; old selected-subject source.')]

def sha(raw):return hashlib.sha256(raw).hexdigest()
def put(rel,raw):
    p=OUT/rel;p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():
        if p.read_bytes()!=raw:raise RuntimeError('Preserve actual epoch: '+rel)
        return
    with p.open('xb') as f:f.write(raw)
def dump(rel,obj):put(rel,(json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())
def original(path,copy):
    raw=path.read_bytes();put(copy,raw)
    return {'path':str(path.resolve()),'copy':copy,'bytes':len(raw),'sha256':sha(raw)}

def facts(final=False):
    f={'round':193,'BATCHFINAL_received':final,'owned_cpp_new':0,'owned_cpp_modified':0,
      'new_bounded_native_spans':0,'new_bounded_native_bytes':0,'new_native_relations':[],
      'retained_bounded_native_spans':6,'retained_bounded_native_bytes':1075,
      'retained_relations':[
       {'key':'subject_update_actual_component_row','scope':'WORLD U+0x430A8=I; I+0xD4 BYTE count, row I+0xD8+ordinal*0x3EC; row WORD+0 compared with zeroextended raw wire subject BYTE. WORD identity, ordinal and common64 root remain distinct.','rawsites':['004d5e60','004d5cc0']},
       {'key':'subject_row_owned_pointer_membership','scope':'Actual row BYTE+0x1F0 count, BYTE flags at+0x1F1, DWORD pointers at+0x258. WORLD34 appends exact bank pointer and flag0, WORLD35 finds that exact pointer and sets flag3. No permission or server learning/MP/save settlement is inferred.','rawsites':['004d5e60','004d5cc0']},
       {'key':'same_original_bank_already_recovered','scope':'Old catalog already proves H+0x149DF8+0x888444=H+0x9D223C=R+0x4504=I+0x4474. Conditional same actual P/H/R/U and successful source epoch; allocation failure and role null input never promote synthetic bank or current.','rawsites':['0048d404','0048d40c','0048d41b','00493540','00493546','00493555']},
       {'key':'same_original_mode0_component_already_recovered','scope':'In captured mode0 domain actual R+0x90 is passed and saved to U+0x430A8; this does not qualify every UI variant or map actor selector to common root.','rawsites':['004af485','004af493','004af496','004d2d40','004d2d54']}],
      'source_qualification_actions':[
       'Reuse actual existing CnPrebornSubjectState full source/selected row and CnPrebornSkillReferences; do not create equivalent isolated reader.',
       'Nativepeer separately proves battle initializer subject argument and group+0x2D4 actual row pointer only. Subject-row-to-list materialization and learned entitlement are not thereby recovered. This agent does not recount peer553x/listwriter spans or assume a join from equal kind/id.',
       'A qualified supplier must retain same original world/battle/subject component, row ordinal and WORD identifier, whole row/full pointer order/flags, exact current epoch and actual complete bank/source provenance. C35 source selection, selected signed index, common learned entitlement and native grant history stay separately qualified.',
       'Existing SharedSubjectSkillPublication only publishes actual committed WORLD34/35 native identities after actual common rules/save/replay qualification. It is not an incoming battle authority or a proof that flags0/3 authorize skills.'],
      'native_original_input_count':16,'new_opcodes':0,'new_phase_bindings':0,'new_complete_routes':0,
      'receiver_contexts':14,'qualified_receiver_contexts':12,
      'unresolved_helpers':[{'va':x,'phase':None,'slot':None,'producer':None} for x in ['0047DE70','004812B0']],
      'whole_game_route_denominator':None,'whole_game_percentage':None,
      'gaps':[
       'Actual common learned skills/actor ownership/grant86 complete history/MP cost/range/formation/item custody/semantic continuation/settlement/native replies/Main suppliers remain OPEN.',
       'Only original mode0 attachment and original WORLD34/35 consumer scope retained here. No global absence/unreachability or every battle subject mapping asserted.',
       'Row WORD identifier may exceed the WORLD34/35 BYTE identity domain; no truncation or alias maps it to that wire byte or common64 identity.',
       'Local flags0/3, pointer equality and definition provenance are source facts, never original server permission. Record publication cannot stand in for the unconfigured authoritative issuer.',
       'Initial misaligned locating dumps48D3CC and4AF476 were not used as instruction evidence. Correct bounded blocks begin at48D3E2 and4AF485.',
       'Stopped155 formatter/capacity/render/glyph chain and52F330/52F170 are excluded; no callee followup or native execution.'],
      'build_test_runtime_native_codec_api_db_deploy':False}
    if (OUT/'native-extension-spans.json').exists():
        f.update(new_bounded_native_spans=1,new_bounded_native_bytes=382,native_original_input_count=17)
        f['new_native_relations']=[
          {'key':'actual_initializer_materialization_call_frontier','scope':'Exact553C7B..553DF9 calls552870 then553220 before primary normalization, and5540B0/5545C0 after. Materialization is not inline here; no row+1F0/+258→group provenance claimed. All UI/render callees remain stopped at original callsite.','rawsites':['00553cbd','00553cc4','00553d39','00553d40']},
          {'key':'primary_whole_group_normalization','scope':'Within exact new block16 groups stride0x2D0,100 WORDs fromgroup+0x14 AND0x7FFF clears bit15 only; clears100 bytes atgroup+0x26C andBYTE group+0x2D0. Does not clear bit14 or prove a definition/learned grant; exact current caller layout must qualify source.','rawsites':['00553ccc','00553cd3','00553cf0','00553cf6','00553d00','00553d03','00553d06','00553d0b','00553d0e','00553d12','00553d17','00553d1d','00553d28','00553d2b']}]
        f['gaps'].append('New initializer382B supplies exact552870/553220/5540B0/5545C0 call frontier and normalization, not the missing subject-row-to-primary-list materializer. No inferred pointer join or UI rights.')
        f['source_ready_epochs_preserved']=['findings-source-ready.json','findings-source-ready2.json','source-ready/tool.py','refinement/tool-before-extension.py']
    return f

def recover():
    if (OUT/'seal.json').exists():raise RuntimeError('Immutable artifact')
    before_raw=(ROUND/'before-manifest.json').read_bytes()
    if sha(before_raw)!=BEFORE or len(json.loads(before_raw))!=1382:raise RuntimeError('Freshbefore1382 differs')
    before={x['path']:x for x in json.loads(before_raw)};old=[]
    for n,rel in enumerate(STABLE[1:]+GUIDELINES):
        row=before[rel];raw=(ROUND/row['snapshot']).read_bytes()
        if sha(raw)!=row['sha256'] or len(raw)!=row['bytes']:raise RuntimeError('Full actual before differs')
        copy=f'before/b{n:02d}'+Path(rel).suffix;put(copy,raw)
        old.append({'path':str((ROOT/rel).resolve()),'copy':copy,'bytes':len(raw),'sha256':sha(raw),'epoch':'freshbefore1382'})
    dump('before-source-origins.json',old)
    dump('before-owned-absence.json',[{'path':str((ROOT/OWN).resolve()),'absent_in_freshbefore':OWN not in before}])
    raw=EXE.read_bytes()
    if len(raw)!=47541760 or sha(raw)!=PIN:raise RuntimeError('Pinned actual PE differs')
    meta=(RECOVERY/'functions.tsv').read_bytes();calls=(RECOVERY/'calls.tsv').read_bytes()
    rows={q['address']:q for q in csv.DictReader(io.StringIO(meta.decode('utf-8-sig')),delimiter='\t')}
    inputs=[original(EXE,'originals/cn.exe'),original(RECOVERY/'functions.tsv','originals/functions.tsv'),original(RECOVERY/'calls.tsv','originals/calls.tsv')]
    primary=[]
    for n,address in enumerate(ADDRESSES):
        p=RECOVERY/rows[address]['file'];r=original(p,f'originals/p{n:02d}.c');inputs.append(r)
        for line,text in enumerate((OUT/r['copy']).read_text(encoding='utf-8-sig').splitlines(),1):
            if any(k in text.lower() for k in ['430a8','4504','4474','8885f0','9d223c','0x3ec','0x1f1','puvar10 + 300','puvar7 + 300','case 0x34','case 0x35']):
                primary.append({'path':str(p.resolve()),'line':line,'text':text,'original_sha256':r['sha256'],'retained_only':True})
    dump('native-original-inputs.json',inputs);dump('primary-source-sites.json',primary)
    dump('bounded-call-rows.json',[q for q in csv.DictReader(io.StringIO(calls.decode('utf-8-sig')),delimiter='\t') if q['target'] in ['004d5e60','004d5cc0','004d2d30','004af370','00492e70']])
    p=pefile.PE(data=raw,fast_load=True);base=p.OPTIONAL_HEADER.ImageBase
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);spans=[];sites=[]
    for n,(va,size,classification,scope) in enumerate(SPANS):
        off=p.get_offset_from_rva(va-base);b=raw[off:off+size];copy=f'raw/s{n:02d}.bin';put(copy,b)
        decoded=[{'va':f'{i.address:08x}','bytes':i.bytes.hex(),'mnemonic':i.mnemonic,'operands':i.op_str,'span':n,'classification':classification} for i in md.disasm(b,va)]
        if sum(len(bytes.fromhex(i['bytes'])) for i in decoded)!=size:raise RuntimeError('Bounded whole instruction bytes incomplete')
        dump(f'derived/s{n:02d}.json',decoded);sites.extend(decoded)
        spans.append({'va_start':f'{va:08x}','va_end':f'{va+size:08x}','bytes':size,'file_offset':off,'copy':copy,'sha256':sha(b),'classification':classification,'scope':scope})
    dump('native-spans.json',spans);dump('instruction-sites.json',sites)
    dump('initial-source-origins.json',[original(ROOT/OWN,'initial/tool.py')])
    dump('source-ready-source-origins.json',[original(ROOT/OWN,'source-ready/tool.py')])
    dump('findings-source-ready.json',facts())
    print(json.dumps({'state':'source-ready','native_inputs':len(inputs),'retained_spans':6,'retained_bytes':1075,'new_spans':0,'new_relations':0,'new_routes':0}))

def extend():
    if (OUT/'seal.json').exists():raise RuntimeError('Immutable artifact')
    raw=EXE.read_bytes()
    if sha(raw)!=PIN:raise RuntimeError('Pinned actual PE differs')
    original_inputs=json.loads((OUT/'native-original-inputs.json').read_bytes())
    meta=(RECOVERY/'functions.tsv').read_bytes()
    rows={q['address']:q for q in csv.DictReader(io.StringIO(meta.decode('utf-8-sig')),delimiter='\t')}
    source=original(RECOVERY/rows['00553bc0']['file'],'originals-extension/00553bc0.c')
    dump('native-additional-original-inputs.json',[source])
    dump('native-original-inputs-v2.json',original_inputs+[source])
    p=pefile.PE(data=raw,fast_load=True);va=0x553c7b;size=0x553df9-va
    off=p.get_offset_from_rva(va-p.OPTIONAL_HEADER.ImageBase);body=raw[off:off+size]
    put('raw-extension/00553c7b.bin',body)
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
    decoded=[{'va':f'{i.address:08x}','bytes':i.bytes.hex(),'mnemonic':i.mnemonic,'operands':i.op_str,'classification':'new_bounded_initializer_frontier_not_full_materializer'} for i in md.disasm(body,va)]
    if sum(len(bytes.fromhex(i['bytes'])) for i in decoded)!=size:raise RuntimeError('Exact bounded instructions incomplete')
    dump('derived-extension/00553c7b.json',decoded)
    dump('native-extension-spans.json',[{'va_start':f'{va:08x}','va_end':'00553df9','bytes':size,'file_offset':off,
       'copy':'raw-extension/00553c7b.bin','sha256':sha(body),'classification':'new_bounded_initializer_frontier_not_full_materializer',
       'scope':'Root newly assigned exclusive interval between nativepeer initializer spans; all caller UI/render/font/deferred callsites retained without entering callees.'}])
    dump('source-ready2-source-origins.json',[original(ROOT/OWN,'source-ready2/tool.py')])
    dump('findings-source-ready2.json',facts())
    print(json.dumps({'state':'source-ready2','native_inputs':17,'new_spans':1,'new_bytes':382,'new_relations':2,'retained_spans':6,'retained_bytes':1075,'new_routes':0}))

def final(context):
    if (OUT/'seal.json').exists():raise RuntimeError('Immutable artifact')
    inputs=json.loads((OUT/('native-original-inputs-v2.json' if (OUT/'native-original-inputs-v2.json').exists() else 'native-original-inputs.json')).read_bytes())
    for r in inputs:
        raw=Path(r['path']).read_bytes()
        if sha(raw)!=r['sha256'] or len(raw)!=r['bytes'] or (OUT/r['copy']).read_bytes()!=raw:raise RuntimeError('Actual full original differs')
    current=[original(ROOT/rel,f'current/c{n:02d}'+Path(rel).suffix) for n,rel in enumerate(STABLE)]
    contexts=[original(ROOT/rel,f'context-final/k{n:02d}'+Path(rel).suffix) for n,rel in enumerate(GUIDELINES+context)]
    dump('current-source-origins.json',current);dump('final-context-source-origins.json',contexts)
    dump('original-inputs.json',inputs+current+contexts)
    dump('findings.json',facts(True));dump('gaps.json',facts()['gaps'])
    dump('actual-read-epochs.json',{'before_sha256':BEFORE,'before_stable_full':11,'before_guidelines_full':3,'owned_before_absent':1,
     'initial_own_tool_full':1,'source_ready_own_tool_full':1,'native_original_full':len(inputs),'current_stable_full':len(current),'final_context_full':len(contexts),
     'source_ready2_tool_full':1,'reporting_refinement_previous_tool_full':2,'initial_actual_context_full':6,
     'original_native_inputs_epoch1':16,'additional_actual_native_original_full':1,
     'old_tools_read_not_rerun':True,'early_peer_epoch_not_reconstructed':True,'aggregate_decompiled_locating_text_not_used_as_original_native_source':True})
    members=[]
    for p in sorted(OUT.rglob('*')):
        if p.is_file():
            raw=p.read_bytes();members.append({'path':p.relative_to(OUT).as_posix(),'bytes':len(raw),'sha256':sha(raw)})
    dump('LIST.json',members);raw=(OUT/'LIST.json').read_bytes();members.append({'path':'LIST.json','bytes':len(raw),'sha256':sha(raw)})
    dump('seal.json',{'round':193,'scope':'Actual source/static retained CN subject prerequisites plus new bounded initializer frontier; materialization and authoritative suppliers OPEN','members':members,
     'member_count':len(members),'member_bytes':sum(q['bytes'] for q in members),'current_source_count':len(current),'context_source_count':len(contexts),'native_original_input_count':len(inputs)})
    print(json.dumps({'state':'sealed','seal_sha256':sha((OUT/'seal.json').read_bytes()),'members':len(members),'total_files_with_seal':len(members)+1,
     'member_bytes':sum(q['bytes'] for q in members),'current':len(current),'context':len(contexts),'original_inputs':len(inputs)+len(current)+len(contexts),'native_inputs':len(inputs),'tool_sha256':sha((ROOT/OWN).read_bytes())}))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('stage',choices=['recover','extend','final']);a.add_argument('--context',nargs='*',default=[])
    args=a.parse_args()
    if args.stage=='recover':recover()
    elif args.stage=='extend':extend()
    else:final(args.context)
