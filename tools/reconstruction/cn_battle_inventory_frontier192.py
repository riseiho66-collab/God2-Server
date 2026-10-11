"""192 bounded CN inventory projection; file/PE/Capstone only, never runtime/tests."""
from pathlib import Path
import argparse
import csv
import hashlib
import io
import json
import struct
import capstone
import pefile

ROOT=Path(__file__).resolve().parents[2]
ROUND=ROOT/'artifacts/integration/packet-connections-20261006/cn-native-battle-command-data-source-01'
OUT=ROUND/'agents/cn-battle-inventory-frontier'
EXE=ROOT.parent.parent/'God2-xjz/XJZ-CN/God2_opt.exe'
RECOVERY=EXE.parent.parent/'God2_opt_source_recovery_20260926_055734/decompiled'
PIN='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
BEFORE='9daea736af7dd6bfb890e0e197d31072d64d5cba75f21aa6ee2bd7aa22df1ae2'
OWN=['src/cn/protocol/CnBattleInventorySlot.h','tools/reconstruction/cn_battle_inventory_frontier192.py']
STABLE=OWN+['src/game/Inventory.h','tools/reconstruction/cn_battle_command_frontier190.py','tools/reconstruction/cn_wrapper_route_frontier.py']
GUIDELINES=['AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md']
ADDRESSES=['004c9ae0','0054a9a0','00544daf','004c72e0','004c73e0','0048fcc0','0054ffc0']
SPANS=[
    (0x4c9ae0,47,'new_complete','Actual WORD-domain getter through both terminal ret4 branches'),
    (0x4c73e0,74,'new_complete','Actual backing page clear of0x708 bytes, through terminalret; not battle authority'),
    (0x4c72e0,252,'retained_complete','Original S41 updater already retained by cn_wrapper_route_frontier; no new opcode/phase'),
    (0x54a9a0,253,'retained_complete','Whole item selector already recovered190; preserve unusual30..37 edge and do not infer custody'),
    (0x54ffc0,1268,'retained_complete','Original full command producer recovered190; item operand packing remains unchanged'),
    (0x4913ff,20,'retained_bounded','Actual WORLD41 packet+1/owner+89B26C transfer to4C72E0 already known old wrapper trace')]

def sha(raw):return hashlib.sha256(raw).hexdigest()
def put(rel,raw):
    p=OUT/rel;p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():
        if p.read_bytes()!=raw:raise RuntimeError('Retain actual epoch, never replace '+rel)
        return
    with p.open('xb') as f:f.write(raw)
def dump(rel,obj):put(rel,(json.dumps(obj,indent=2)+'\n').encode())
def original(path,copy):
    raw=path.read_bytes();put(copy,raw)
    return {'path':str(path.resolve()),'copy':copy,'bytes':len(raw),'sha256':sha(raw)}

def findings(final=False):
    return {'round':192,'BATCHFINAL_received':final,'owned_cpp_new':1,'new_header':OWN[0],
        'native_original_input_count':10,'new_bounded_native_spans':2,'new_bounded_native_bytes':121,
        'retained_bounded_native_spans':4,'retained_bounded_native_bytes':1793,
        'new_native_relations':[
            {'key':'getter_actual_slot_record_domain','scope':'4C9AE0 WORD input unsigned<=0x25; CWDE then slot*9*4 gives stride36; owner+41AF8 WORD nonzero gates owner+41AF4 pointer. This38-slot getter is not total inventory capacity or common custody.',
             'rawsites':['004c9ae3','004c9ae7','004c9aeb','004c9aed','004c9aee','004c9af1','004c9af4','004c9afd','004c9aff']},
            {'key':'actual_inventory_owner_into_item_consumer','scope':'Retained54A9A0 passes actual battleowner+20 ECX to getter after signedBYTE CBW then WORD projection; negative signed slots fail getter domain. The receiver is a client record source, never a shared root/grant supplier.',
             'rawsites':['0054a9a4','0054a9aa','0054a9ad','0054a9b1','0054a9b4','0054aa12','0054aa16']},
            {'key':'backing_page_clear_domain_distinct_from_getter','scope':'4C73E0 clears owner+41AF4 bytes0x708=50*36, actual page extent independent of getter38. No stack cap or use/consume rule recovered; memory clear is not gameplay settlement.',
             'rawsites':['004c73e3','004c73ea','004c73fa','004c73fb']}],
        'retained_relations':[
            'S41→4913FF passes original packet+1 and owner+89B26C to4C72E0, then original dispatcher join. Already known cn_wrapper_route_frontier.',
            '4C72E0 payload WORD+0→record WORD+4, BYTE+2 slot<=49, BYTE+3→record BYTE+0; signed nonpositive count clears quantity/item. UI refresh callees deliberately not followed.',
            '54A9A0 scan29 downward to requested signedslot checks signed quantity>0 and equal WORD+4. Slots30..37 bypass scan but EBX remains29 while initial pointer/item remains requested record; preserve mismatch, never silently grant slot29 ownership.',
            '54FFC0 kind05/0C original operand highBYTE saved signedslot, middleBYTE0, lowWORD item; this is not lowWORD slot or fullDWORD<=37. No generickind/slot permission imposed.'],
        'readonly_source_action':'Complete36B actual supplied inventory-record copy with raw BYTE signed/unsigned quantity and LEWORD item; separate getter WORD domain. Actual qualified common source must provide fullScope, originalToken, source generation, complete record dictionary, custody and operation rules. Header never loads memory or produces wire/ACK.',
        'new_opcodes':0,'new_phase_bindings':0,'new_complete_routes':0,
        'receiver_contexts':14,'qualified_receiver_contexts':12,
        'unresolved_helpers':[{'va':x,'phase':None,'slot':None,'producer':None} for x in ['0047DE70','004812B0']],
        'whole_game_route_denominator':None,'whole_game_percentage':None,
        'gaps':['Actual common custody/equip/use/consume/expiry/generation and native reply/settlement suppliers remain OPEN.',
                'Other33 unnamed bytes of36B record remain opaque; backing memory is not a wire record. Client scan is not permission.',
                'Original unusual30..37 scan edge preserved; requested slot, selected slot and operand matching are not silently normalized.',
                'No99-stack implementation or activation inferred from signedBYTE memory quantity; numeric extensions remain separately scoped.',
                'Global call completeness/unknown receiver phases/Main activation/current-client acceptance remain OPEN.'],
        'build_test_runtime_native_codec_api_db_deploy':False}

def recover():
    if (OUT/'seal.json').exists():raise RuntimeError('Immutable sealed artifact')
    fresh=(ROUND/'before-manifest.json').read_bytes()
    if sha(fresh)!=BEFORE or len(json.loads(fresh))!=1373:raise RuntimeError('Actual freshbefore1373 changed')
    raw=EXE.read_bytes()
    if len(raw)!=47541760 or sha(raw)!=PIN:raise RuntimeError('Pinned actual CN PE changed')
    meta=(RECOVERY/'functions.tsv').read_bytes();calls=(RECOVERY/'calls.tsv').read_bytes()
    rows={r['address']:r for r in csv.DictReader(io.StringIO(meta.decode('utf-8-sig')),delimiter='\t')}
    originals=[original(EXE,'originals/cn.exe'),original(RECOVERY/'functions.tsv','originals/functions.tsv'),original(RECOVERY/'calls.tsv','originals/calls.tsv')]
    sites=[]
    for n,address in enumerate(ADDRESSES):
        p=RECOVERY/rows[address]['file'];row=original(p,f'originals/p{n:02d}.c');originals.append(row)
        for line,text in enumerate((OUT/row['copy']).read_text(encoding='utf-8-sig').splitlines(),1):
            if any(k in text.lower() for k in ['41af4','41af8','0x708','004c9ae0','004c72e0','a9713','case 0x41']):
                sites.append({'path':str(p.resolve()),'line':line,'text':text,'original_sha256':row['sha256'],'context_only':address=='00544daf'})
    dump('native-original-inputs.json',originals);dump('primary-source-sites.json',sites)
    dump('bounded-original-call-rows.json',[r for r in csv.DictReader(io.StringIO(calls.decode('utf-8-sig')),delimiter='\t') if r['target'] in ['004c9ae0','004c72e0','004c73e0']])
    pe=pefile.PE(data=raw,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase
    cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);spans=[];instructions=[]
    for n,(va,size,classification,purpose) in enumerate(SPANS):
        off=pe.get_offset_from_rva(va-base);body=raw[off:off+size];copy=f'raw/s{n:02d}.bin';put(copy,body)
        decoded=[{'va':f'{i.address:08x}','bytes':i.bytes.hex(),'mnemonic':i.mnemonic,'operands':i.op_str,'span':n,'classification':classification} for i in cs.disasm(body,va)]
        if sum(len(bytes.fromhex(i['bytes'])) for i in decoded)!=size:raise ValueError('Bounded instruction domain incomplete')
        dump(f'derived/s{n:02d}.json',decoded);instructions.extend(decoded)
        spans.append({'va_start':f'{va:08x}','va_end':f'{va+size:08x}','file_offset':off,'copy':copy,'bytes':size,'sha256':sha(body),'classification':classification,'scope':purpose})
    dump('native-spans.json',spans);dump('instruction-sites.json',instructions)
    va=0x4929d8+0x41*4;off=pe.get_offset_from_rva(va-base);body=raw[off:off+4];target=struct.unpack('<I',body)[0]
    if target!=0x4913ff:raise RuntimeError('Exact actual dispatch cell changed')
    put('raw/retained-world41-cell.bin',body)
    dump('data-sites.json',[{'va':f'{va:08x}','copy':'raw/retained-world41-cell.bin','bytes':4,'sha256':sha(body),'target':f'{target:08x}','classification':'retained_existing_relation','new_phase_binding':False}])
    dump('initial-source-origins.json',[original(ROOT/p,f'initial/i{n:02d}'+Path(p).suffix) for n,p in enumerate(OWN)])
    dump('source-ready-source-origins.json',[original(ROOT/p,f'source-ready/r{n:02d}'+Path(p).suffix) for n,p in enumerate(OWN)])
    dump('findings-source-ready.json',findings())
    print(json.dumps({'state':'source-ready','actual_native_inputs':len(originals),'new_spans':2,'new_bytes':121,'retained_spans':4,'retained_bytes':1793,'new_relations':3,'new_complete_routes':0}))

def final(extra):
    if (OUT/'seal.json').exists():raise RuntimeError('Immutable sealed artifact')
    native=json.loads((OUT/'native-original-inputs.json').read_bytes())
    for row in native:
        raw=Path(row['path']).read_bytes()
        if len(raw)!=row['bytes'] or sha(raw)!=row['sha256'] or (OUT/row['copy']).read_bytes()!=raw:raise RuntimeError('Actual full native original changed')
    current=[original(ROOT/p,f'current/c{n:02d}'+Path(p).suffix) for n,p in enumerate(STABLE)]
    context=[original(ROOT/p,f'context-final/k{n:02d}'+Path(p).suffix) for n,p in enumerate(GUIDELINES+extra)]
    dump('current-source-origins.json',current);dump('final-context-source-origins.json',context)
    dump('original-inputs.json',native+current+context)
    dump('findings.json',findings(True));dump('gaps.json',findings(True)['gaps'])
    dump('actual-read-epochs.json',{'freshbefore1373_sha256':BEFORE,'before_own_absence':2,'before_full_source':6,'before_base_sources':5,'before_locating_legacy_source':1,
        'initial_own_full_source':2,'source_ready_own_full_source':2,'current_stable':len(current),'final_context':len(context),
        'native_original_input_count':len(native),'unobserved_peer_transient_epochs_not_reconstructed':True,
        'incomplete_alignment_locating_dump_not_used_as_instruction_evidence':'initial4913E8 candidate began inside previous instruction; authoritative retained fullblock is4913FF..491413 only',
        'old_wrapper_relation_retained_not_rerun':True})
    members=[]
    for p in sorted(OUT.rglob('*')):
        if p.is_file():
            raw=p.read_bytes();members.append({'path':p.relative_to(OUT).as_posix(),'bytes':len(raw),'sha256':sha(raw)})
    dump('LIST.json',members);raw=(OUT/'LIST.json').read_bytes();members.append({'path':'LIST.json','bytes':len(raw),'sha256':sha(raw)})
    dump('seal.json',{'round':192,'scope':'Exact immutable source/static native inventory frontier','members':members,
        'member_count':len(members),'member_bytes':sum(r['bytes'] for r in members),'current_source_count':len(current),
        'context_source_count':len(context),'native_original_input_count':len(native)})
    print(json.dumps({'state':'sealed','seal_sha256':sha((OUT/'seal.json').read_bytes()),'members':len(members),'total_files_with_seal':len(members)+1,
        'member_bytes':sum(r['bytes'] for r in members),'current':len(current),'context':len(context),'original_inputs':len(native)+len(current)+len(context),
        'native_inputs':len(native),'tool_sha256':sha((ROOT/OWN[1]).read_bytes())}))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['recover','final']);parser.add_argument('--context',nargs='*',default=[])
    args=parser.parse_args();recover() if args.stage=='recover' else final(args.context)
