"""Retain native choice producer primitives and exact UI operand references.

File bytes/metadata/entry CFG only; no native, emulator, SQL or test execution.
"""
import bisect
import csv
import hashlib
import json
import struct
import capstone
from capstone.x86 import X86_OP_MEM
import pefile
from .cn_wrapper_route_frontier import ROOT,CN,RECOVERY,PIN
from .cn_pe_import_directory import FileView
from .cn_delete_caller_seh_frontier import decode_cfg

NAME='cn-creation-choice-producer-frontier-01'
ROUND='20261007-cn-creation-choice-producer-frontier'
SOURCES=('src/cn/protocol/CnCharacterLocationChoice.h',
    'src/cn/auth/SharedCreationLocationIdentity.cpp','src/cn/auth/SharedCharacterCreateOperation.cpp',
    'tools/reconstruction/cn_creation_choice_producer_frontier.py',
    'tools/reconstruction/dual_client_route_catalog.py',
    'docs/research/cn-creation-choice-producer-frontier-20261007.md')
FUNCTIONS=('0043d280','0043d580','0043d610','0043d8f0','00445040','00445b40',
    '00448950','0047e900','0047db70','00481440','00446bd0')
TARGETS=(0x43d280,0x43d580,0x43d610,0x43d8f0,0x448950)


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():
        raise RuntimeError('Require fresh before sources; preserve old artifacts')
    unchanged=[]
    for row in json.loads((out/'before-manifest.json').read_text(encoding='utf-8')):
        raw=(out/'before'/row['path']).read_bytes()
        if sha(raw)!=row['sha256']:raise RuntimeError('Before source receipt changed')
        if row['path'] not in SOURCES:
            if raw!=(ROOT/row['path']).read_bytes():raise RuntimeError('Frozen/context source changed')
            unchanged.append(row)
    raw=(CN.parent/'XJZ-CN/God2_opt.exe').read_bytes()
    if sha(raw)!=PIN:raise RuntimeError('CN primary file changed')
    pe=pefile.PE(data=raw,fast_load=True);view=FileView(pe,raw);ib=pe.OPTIONAL_HEADER.ImageBase
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
    metadata=(RECOVERY/'functions.tsv').read_bytes()
    rows=list(csv.DictReader(metadata.decode('utf-8-sig').splitlines(),delimiter='\t'))
    entries={r['address'].lower():r for r in rows}
    spans=sorted((int(r['address'],16),int(r['bytes']),r) for r in rows);starts=[r[0] for r in spans]
    def owner(va):
        at=bisect.bisect_right(starts,va)-1
        return spans[at][2]['address'].lower() if at>=0 and va<spans[at][0]+spans[at][1] else None
    def save(rel,data):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    def dump(rel,data):save(rel,(json.dumps(data,indent=2)+'\n').encode('utf-8'))
    original=base/'cn-delete-caller-seh-frontier-01'
    manifest=json.loads((original/'manifest.json').read_text(encoding='utf-8'))
    pins={r['path']:r['sha256'] for r in manifest['files']}
    tables_raw=(original/'qualified-ui-switches.json').read_bytes()
    if not manifest['sealed'] or sha(tables_raw)!=pins['qualified-ui-switches.json']:
        raise RuntimeError('Prior qualified switch receipt changed')
    tables=json.loads(tables_raw);save('retained-source/qualified-ui-switches.json',tables_raw)
    native_index=[];decoded={}
    def capture(entry):
        if entry in decoded:return
        row=entries[entry];low=int(entry,16);size=int(row['bytes']);code=view.read(low-ib,size);switches={}
        for table in tables:
            if table['function']!=entry:continue
            guard=bytes.fromhex(table['guard_bytes'])
            if view.read(int(table['guard'],16)-ib,len(guard))!=guard:raise RuntimeError('Guard primary mismatch')
            values=struct.unpack('<'+'I'*table['entries'],view.read(int(table['table'],16)-ib,4*table['entries']))
            if [f'{v:08x}' for v in values]!=table['targets']:raise RuntimeError('Table primary mismatch')
            switches[int(table['dispatch'],16)]=values
        cfg,asm,instructions=decode_cfg(md,code,low,low+size,switches)
        decoded[entry]=instructions
        save('native/'+entry+'.bin',code);save('native/'+entry+'.asm',asm)
        save('native/'+entry+'.c',(RECOVERY/row['file']).read_bytes());dump('native/'+entry+'.cfg.json',cfg)
        native_index.append({'entry':entry,'metadata_file':row['file'],'metadata_bytes':size,
            'sha256':sha(code),'cfg_instructions':len(instructions),'open_edges':cfg['open_edges'],
            'instruction_overlap_found':cfg['instruction_overlap_found']})
    for entry in FUNCTIONS:capture(entry)
    calls=[];pointers=[];operands=[];sections=[]
    for number,section in enumerate(pe.sections):
        low=ib+section.VirtualAddress;data=raw[section.PointerToRawData:section.PointerToRawData+section.SizeOfRawData]
        executable=bool(section.Characteristics&0x20000000)
        sections.append({'section':number,'va':f'{low:08x}','raw':section.PointerToRawData,
            'raw_bytes':len(data),'executable':executable,'sha256':sha(data)})
        if executable:
            for opcode in (0xe8,0xe9):
                at=0
                while True:
                    at=data.find(bytes([opcode]),at)
                    if at<0:break
                    va=low+at
                    if at+5<=len(data):
                        target=(va+5+struct.unpack_from('<i',data,at+1)[0])&0xffffffff
                        if target in TARGETS:
                            entry=owner(va)
                            if entry:capture(entry)
                            ins=decoded.get(entry,{}).get(va)
                            calls.append({'va':f'{va:08x}','target':f'{target:08x}','opcode':hex(opcode),
                                'section':number,'raw':section.PointerToRawData+at,'metadata_owner':entry,
                                'entry_rooted_instruction':bool(ins and bytes(ins.bytes)==data[at:at+5] and ins.mnemonic in ('call','jmp'))})
                    at+=1
        for target in TARGETS:
            at=0
            while True:
                at=data.find(struct.pack('<I',target),at)
                if at<0:break
                pointers.append({'va':f'{low+at:08x}','target':f'{target:08x}','section':number,
                    'raw':section.PointerToRawData+at,'executable':executable});at+=1
        at=0
        while True:
            at=data.find(struct.pack('<I',0x1612c),at)
            if at<0:break
            va=low+at;entry=owner(va)
            if entry:capture(entry)
            ins=next((i for i in decoded.get(entry,{}).values() if i.address<=va<i.address+i.size),None)
            matched=bool(ins and any(op.type==X86_OP_MEM and op.mem.disp==0x1612c for op in ins.operands))
            operands.append({'va_of_literal':f'{va:08x}','section':number,'raw':section.PointerToRawData+at,
                'metadata_owner':entry,'entry_rooted_memory_operand':matched,
                'instruction':None if ins is None else {'va':f'{ins.address:08x}','bytes':bytes(ins.bytes).hex(),
                    'mnemonic':ins.mnemonic,'operands':ins.op_str},
                'absolute_field_displacement_not_all_alias_writes':True});at+=1
    dump('native-function-index.json',{'native_sha256':PIN,'metadata_sha256':sha(metadata),'functions':native_index})
    save('native/functions.tsv',metadata)
    dump('relative-call-census.json',calls);dump('absolute-pointer-census.json',pointers)
    dump('ui-selector-operand-census.json',operands);dump('section-scan-coverage.json',sections)
    findings={'round':ROUND,'native_sha256':PIN,
        'previous_goal_turn_classification':'progress: full common-account snapshot binding implemented in existing A6/07; catalog85 sealed and web peer handoff ACK sent',
        'targeted_metadata_function_envelopes':len(native_index),'additional_targeted_helper_envelopes':2,
        'ui_selector_literal_references':len(operands),'ui_selector_entry_rooted_memory_operands':sum(r['entry_rooted_memory_operand'] for r in operands),
        'direct_or_tail_target_candidates':len(calls),'entry_rooted_target_references':sum(r['entry_rooted_instruction'] for r in calls),
        'standalone_helpers_direct_or_pointer_reference_candidates':sum(r['target'] in ('0043d580','0043d610','0043d8f0') for r in calls+pointers),
        'native18_local_producer_primitives_in_scoped_census':4,
        'raw_choice_request_semantic_corrections':1,'source_runtime_behavior_changed':False,
        'native_fields_newly_recovered':0,'new_packet_values':0,'new_native_phase_source_bindings':0,
        'new_source_owner_chains':0,'new_complete_bidirectional_routes':0,
        'all_computed_callers_or_alias_field_writes_exhausted':False,'selector_always_zero_proven':False,
        'standalone_helpers_unreachable_proven':False,'whole_game_route_total':None,'whole_game_completion_percent':None,
        'levels_changed':False,'build_run':False,'tests_run':False,'runtime_run':False,'database_access':False,'deployed':False,
        'existing_sources_unchanged':unchanged,
        'remaining':['Computed/indirect/loaded caller roots for43D580/43D610/43D8F0; no absence-to-dead-code or phase inference.',
            'Actual UI selection write/alias lineage and permission/destination/spawn/native18 issuer; zero initialization is not choice1-only authority.',
            'Special1B->18->1A actual shared operation/transaction/issuer and queue owner, separate from ordinary17.',
            'Native07/auth/world/03 sources, durable recovery/configured hosting/all gameplay and whole-game directional/state/variant denominator.']}
    with (ROOT/SOURCES[-1]).open('x',encoding='utf-8') as f:
        f.write('# CN creation-choice producer and selector frontier\n\n'
            'PHASE1 primary file/source analysis only; no native/emulator/server/SQL/build/tests/migrations/deploy. Levels unchanged. Pinned CN '+PIN+'.\n\n'
            'New targeted helper43D610 forwards its caller-supplied BYTE to481440(op18,payload1) and flushes. It does not add1 or read UI+1612C, and has no local reply waiter.43D8F0 constructs ordinary17 and returns47DCC0 status without a local18 send. Full metadata bytes, decompiled text and bounded entry-rooted CFG are retained with the previously scoped ordinary43D280, standalone UI43D580, special448950 and their actual sender/waiter. These are scoped producer primitives, not new opcodes or qualified gameplay owners.\n\n'
            'Executable-section raw E8/E9 target census and all file-backed section DWORD pointer census are saved separately from entry-rooted instruction alignment.43D580/43D610/43D8F0 have no target matches in these two encodings. This does not prove they are unused, inaccessible or in the same connection phase: computed/displaced/relocated/indirect/loaded targets are still open. Actual UI446BD0 guarded32-state switch reaches ordinary43D280 from state24 and special448950 from state30; the pre-existing guarded switch receipt is compared with current primary bytes. Prior special1B and ordinary-state evidence remains prior, not newly recovered fields.\n\n'
            'The UI+1612C full DWORD literal census has7 rooted memory operands.445040 writes zero to the WORD during initialization;43D280/43D580/448950 read only a BYTE and increment it for wire18, while445B40 reads a signed WORD for its48-stride location table accesses. A low-BYTE wire projection and full signed-WORD table index are different domains. The literal census does not cover stores through aliases/computed bases and cannot establish an always-zero selector or a choice1-only server policy.18 table entries are still routing/selector/location projections, not native availability or a shared map/spawn rule.\n\n'
            'Source semantic correction: CnCharacterLocationChoice::Request now names the field raw_choice_byte. read_request still requires exact2-byte18 and retains all256 BYTE values. The existing ordinary creation controller/identity references use the same raw value and still require actual pending17/common created ID/permitted set before the qualified one-based location projection. Native projection Reference::one_based_choice remains unchanged. No handler is added for unknown helper callers or special1B, no domain is broadened/clamped, no success/reply/table/permission is guessed. Runtime behavior is unchanged.\n\n'
            'This delivery narrows next recovery: root computed helper callers and actual selector write/alias lineage; qualify special1B pending operation separately. Native destination/spawn/full18/03/07/auth/world sources, durable replay/queue/crash recovery and configured shared hosting remain incomplete. New opcode/phase/owner/full routes0; whole-game total/percentage null.\n')
    dump('findings.json',findings)
    for rel in SOURCES:save('source/'+rel,(ROOT/rel).read_bytes())
    print(json.dumps({k:findings[k] for k in ('round','targeted_metadata_function_envelopes',
        'ui_selector_literal_references','ui_selector_entry_rooted_memory_operands','entry_rooted_target_references',
        'standalone_helpers_direct_or_pointer_reference_candidates','new_complete_bidirectional_routes')}))


if __name__=='__main__':main()
