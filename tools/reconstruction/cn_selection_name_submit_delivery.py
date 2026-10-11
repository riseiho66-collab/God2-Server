"""Static CN D3/07 selection-name lineage and common name CAS source receipt."""
import csv
import hashlib
import io
import json
import struct
import capstone
import pefile
from .cn_wrapper_route_frontier import ROOT,CN,RECOVERY,PIN
from .cn_pe_import_directory import FileView
from .cn_delete_caller_seh_frontier import decode_cfg

NAME='cn-selection-name-submit-01'
ROUND='20261007-cn-selection-name-submit'
FUNCTIONS=('0047f750','00440b20','00446bd0','00440ae0','00440ac0',
    '00433b00','00481440','00480650')
SOURCES=('src/cn/protocol/CnSelectionNameSubmission.h',
    'src/db/SqliteRecoveredCharacterRepository.h','src/db/SqliteOwnedCharacterName.cpp',
    'src/auth/SharedCharacterNameReplacement.h','src/auth/SharedCharacterNameReplacement.cpp',
    'tools/reconstruction/cn_selection_name_submit_delivery.py',
    'tools/reconstruction/dual_client_route_catalog.py','docs/research/cn-selection-name-submit-20261007.md')


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():
        raise RuntimeError('Fresh before source receipt required')
    def save(rel,raw):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    def dump(rel,value):save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    unchanged=[]
    for row in json.loads((out/'before-manifest.json').read_text(encoding='utf-8')):
        raw=(out/'before'/row['path']).read_bytes()
        if sha(raw)!=row['sha256']:raise RuntimeError('Before receipt changed')
        if row['path'] not in SOURCES:
            if raw!=(ROOT/row['path']).read_bytes():raise RuntimeError('Frozen/context source changed')
            unchanged.append(row)
    original=base/'cn-delete-caller-seh-frontier-01'
    manifest=json.loads((original/'manifest.json').read_text(encoding='utf-8'))
    pins={r['path']:r['sha256'] for r in manifest['files']}
    raw=(original/'qualified-ui-switches.json').read_bytes()
    if not manifest['sealed'] or sha(raw)!=pins['qualified-ui-switches.json']:raise RuntimeError('Prior switch receipt changed')
    switches=json.loads(raw);save('retained-source/qualified-ui-switches.json',raw)
    raw=(CN.parent/'XJZ-CN/God2_opt.exe').read_bytes()
    if sha(raw)!=PIN:raise RuntimeError('Pinned CN image changed')
    pe=pefile.PE(data=raw,fast_load=True);view=FileView(pe,raw);ib=pe.OPTIONAL_HEADER.ImageBase
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
    metadata=(RECOVERY/'functions.tsv').read_bytes();save('native/functions.tsv',metadata)
    rows={r['address'].lower():r for r in csv.DictReader(metadata.decode('utf-8-sig').splitlines(),delimiter='\t')}
    native=[];decoded={};contexts=[];qualified=[]
    for entry in FUNCTIONS:
        row=rows[entry];va=int(entry,16);code=view.read(va-ib,int(row['bytes']));tables={}
        selected=[t for t in switches if t['function']==entry]
        if entry=='00440b20':
            selected.append({'function':entry,'dispatch':'00440b90','table':'00440c8c',
                'guard':'00440b87','guard_bytes':'83f803','entries':4,
                'selector_relation':'signed WORD event ID then unsigned EAX<=3'})
        for t in selected:
            guard=bytes.fromhex(t['guard_bytes'])
            if view.read(int(t['guard'],16)-ib,len(guard))!=guard:raise RuntimeError('Primary guard changed')
            data=view.read(int(t['table'],16)-ib,4*t['entries']);targets=struct.unpack('<'+'I'*t['entries'],data)
            if 'targets' in t and [f'{x:08x}' for x in targets]!=t['targets']:raise RuntimeError('Prior primary switch differs')
            t={**t,'targets':[f'{x:08x}' for x in targets]};qualified.append(t)
            tables[int(t['dispatch'],16)]=targets;save('native/tables/'+t['table']+'.bin',data)
        cfg,asm,ins=decode_cfg(md,code,va,va+len(code),tables);decoded[entry]=ins
        save('native/'+entry+'.bin',code);save('native/'+entry+'.asm',asm)
        save('native/'+entry+'.c',(RECOVERY/row['file']).read_bytes());dump('native/'+entry+'.cfg.json',cfg)
        native.append({'entry':entry,'metadata_file':row['file'],'bytes':len(code),'sha256':sha(code),
            'rooted_instructions':len(ins),'open_edges':cfg['open_edges'],'overlap':cfg['instruction_overlap_found']})
        ordered=sorted(ins.values(),key=lambda i:i.address)
        for n,i in enumerate(ordered):
            target=any(op.type==capstone.x86_const.X86_OP_IMM and op.imm in
                (0x47f750,0x481440,0x433b00,0x480650) for op in i.operands)
            mode=entry=='0047f750' and (0x47f760<=i.address<=0x47f7b1 or
                any(op.type==capstone.x86_const.X86_OP_MEM and op.mem.disp in (0x4200,0x2cc4) for op in i.operands))
            if target or mode:contexts.append({'entry':entry,'site':f'{i.address:08x}','context':[
                {'site':f'{j.address:08x}','bytes':j.bytes.hex(),'mnemonic':j.mnemonic,'operand':j.op_str}
                for j in ordered[max(0,n-12):n+7]]})
    dump('native/index.json',native);dump('qualified-switches.json',qualified);dump('native/producer-caller-contexts.json',contexts)
    # Raw relative references are bounded encodings, not whole-program absence.
    references=[]
    for number,section in enumerate(pe.sections):
        if not section.Characteristics&0x20000000:continue
        data=raw[section.PointerToRawData:section.PointerToRawData+section.SizeOfRawData];low=ib+section.VirtualAddress
        for opcode in (0xe8,0xe9):
            at=0
            while True:
                at=data.find(bytes([opcode]),at)
                if at<0:break
                if at+5<=len(data) and (low+at+5+struct.unpack_from('<i',data,at+1)[0])&0xffffffff==0x47f750:
                    va=low+at;owners=[e for e,ins in decoded.items() if va in ins and
                        ins[va].mnemonic in ('call','jmp') and ins[va].operands[0].type==capstone.x86_const.X86_OP_IMM]
                    references.append({'site':f'{va:08x}','section':number,'encoding':data[at:at+5].hex(),
                        'entry_rooted_owners':owners,'whole_program_reachability':False})
                at+=1
    dump('relative-helper-reference-census.json',{'target':'0047f750','references':references,
        'scope':'Executable raw E8/E9 only; alias/computed/loaded callbacks not exhausted'})
    resource=base/'cn-directory-display-fields-01/native/resources'
    receipt_raw=(resource/'account-phase-evidence.json').read_bytes();receipt=json.loads(receipt_raw)
    packed=(CN.parent/'XJZ-CN/Data2/Patch/Comm/message.csvZ').read_bytes();plain=(resource/'message.csv').read_bytes()
    if receipt['client_sha256']!=PIN or sha(packed)!=receipt['asset']['sha256'] or sha(plain)!=receipt['asset']['decoded_sha256']:
        raise RuntimeError('Pinned resource differs')
    save('resources/message.csvZ',packed);save('resources/message.csv',plain);save('resources/prior-resource-receipt.json',receipt_raw)
    cr=list(csv.reader(io.StringIO(plain.decode('cp936'))));start=next(i for i,r in enumerate(cr) if r and r[0]=='SystemMessage')
    dump('resources/selected-system-messages.json',{
        r[0]:{'csv_row':i+1,'cells':r,'cp936_hex':[c.encode('cp936').hex() for c in r]}
        for i,r in enumerate(cr) if start<i<=start+int(cr[start][1]) and r[0] in ('185','195')})
    relations={'route':'normal selection UI name prompt ->account network UI1617C ->47F750 ->C2SD3 logical25 ->wait07/raw74copy ->same UI summary ->state4',
        'wire':{'record_bytes':25,'payload_bytes':24,'opcode':'D3',
            'payload0_3':'zero-initialized DWORD, meaning unresolved',
            'payload4_19':'16-byte raw name storage, strncpy15 into zero buffer',
            'payload20_21':'selected raw07 row ordinal WORD from UI1792D4',
            'payload22_23':'zero initialized WORD, meaning unresolved'},
        'scoped_producers':'440B20 event0 (flags bit1 clear/bit0 set);446BD0 same inlined UI1792C8 event0 branch. Each433B00 extracts max14 raw name bytes with NUL and requires nonempty. No incoming ID/name join.',
        'ordinal_not_slot':'UI1792D4 indexes raw07 rows in normal character selection/name prompt. Do not use D3 WORD directly as common ID or native_slot.',
        'callee_argument2':'Both callers pass literal2 as a separate helper argument; no primary load/use in this bounded callee; not on-wire target or transport role.',
        'success':'full74-byte07 payload copied into caller raw summary; optional local124 cache unchanged baseline; flags&1 to receiver network4200; local success return0',
        'errors':'1E takes480650 native error formatter and returns failure; timeout>=30000ms uses SystemMessage185; unexpected records use195 and continue. Resource text/local return is not server emission/rule evidence.',
        'common_source':'SharedCharacterNameReplacement ->same repository/full-account-root SQLite CAS ->real updated saved row ->same prepared admission invalidation after COMMIT. Native handler/issuer not installed.',
        'preservation':'Only profile first16/name_bytes/explicit codepage updated; exact ID/account/slot/created_at/style and profile16..39 preserved. All saved descendants remain; no table import/schema rewrite/level change.',
        'rule_boundary':'Qualified native owner must supply current offered row-to-common-ID mapping, name equivalence/unique scope/rules/operation/lease/replay and explicit common candidate; no fabricated normalization or success07.'}
    dump('source-relations.json',relations)
    findings={'round':ROUND,'native_sha256':PIN,'previous_goal_turn_classification':'progress: prior native SystemMessage correction/read-only state4 source sealed and current',
        'native_metadata_envelopes_retained':len(native),'scoped_entry_rooted_D3_caller_contexts':sum(bool(r['entry_rooted_owners']) for r in references),
        'native_D3_record_bytes':25,'native_read_only_request_views_added':1,
        'common_name_snapshot_cas_writers_added':1,'common_name_offer_coordinators_added':1,
        'new_native_phase_source_bindings':0,'new_source_owner_chains':0,'new_packet_values':0,
        'new_complete_bidirectional_routes':0,'whole_game_route_total':None,'whole_game_completion_percent':None,
        'levels_changed':False,'build_run':False,'tests_run':False,'runtime_run':False,'database_access':False,'deployed':False,
        'existing_sources_unchanged':unchanged,'remaining':[
            'Actual D3 name-operation phase/permission/name-equivalence/uniqueness/replay owner and offered07 ordinal-to-common-ID mapping.',
            'Source-backed full success07/errors, explicit common name conversion and durable recovery/refresh; no guessed reply.',
            'Actual full native auth/catalog/world00-1F providers and configured common Application hosting.',
            'All CN/TW gameplay, numeric wire/object/display and directional/state/variant/indirect/deferred denominator.']}
    dump('findings.json',findings)
    doc=ROOT/SOURCES[-1]
    with doc.open('x',encoding='utf-8') as f:
        f.write('# CN selection-name D3/07 lineage and common saved-name CAS\n\n'
            'PHASE1 static PE/entry CFG/resource/source work only. No build/tests/native/emulator/server/SQL/migration/deploy. Levels remain unchanged. Previous sealed normal-selection SystemMessage correction was progress.\n\n'
            'Eight pinned metadata envelopes retain primary bytes, assembly, entry CFG and navigation C. The normal UI1792C8 name-prompt event0 has an out-of-line440B20 and inlined446BD0 path. Guarded event switches and the existing UI state switches are reread from primary tables. Both callers get up to14 raw input bytes through433B00, require a nonempty name, copy UI1792D4 WORD and call47F750 using the ACCOUNT network UI+1617C. The literal2 helper argument is not a wire/role field; this callee has no proved local use for it. Bounded rawE8/E9 census records actual rooted references separately from aliases/computed/loaded callers.\n\n'
            '47F750 produces native D3 with24 payload bytes, logical25 total. It zeros its payload storage, strncpy15 bytes into payload4..19 and places the caller selection WORD at20..21; prefix0..3 and tail22..23 are observed zero initialization, their meanings unresolved. The input is a raw07 row ordinal, not native slot or common ID. CnSelectionNameSubmission preserves all bytes and exposes structural fields plus the scoped observed UI shape; it does not create a packet, resolve identity or grant name-change permission.\n\n'
            'The waiter accepts07 and copies its full74-byte payload back into the same caller summary, optionally rebuilds the existing124-byte local cache, and projects flags&1 to network4200. Both UI callers return to normal state4 unless stateB. Native1E calls480650 error formatting; local timeout>=30000ms selects SystemMessage185 and an unexpected record selects195. These text/return paths are not permission rules or proof of what the official server sends. This is distinct from A6/group/server, world17 creation,19 deletion and1A selection.\n\n'
            'Additive shared source: SqliteRecoveredCharacterRepository::replace_owned_name_snapshot requires actual account/common ID, a complete expected common account-root set, explicit16-byte common name/codepage candidate and mandatory observing operation checks BeforeReplace/BeforeCommit. BEGIN IMMEDIATE rereads exact roots, compares ID/account/slot/profile40/created_at/codepage/style, performs a fully qualified UPDATE then reads the staged full roots back before COMMIT. Only first16 profile/name_bytes/codepage change; identity, profile16..39 including level fields, all save descendants and other account characters stay unchanged. Name equivalence/unique scope/permissions are mandatory actual rule-source work, not inferred from SQLite raw uniqueness. Common storage max14 is an existing storage boundary, not a native field limit or truncation license.\n\n'
            'SharedCharacterNameReplacement connects this actual CAS writer with the existing same-repository/common prepared-active occupancy observer and prepared TW/CN offer invalidation. It checks actual occupancy and exact invalidation before/after the observing operation callback, then applies prepared invalidation immediately after real COMMIT without callback/allocation/yield. Old raw07 offers become stale; no replacement07 or world actor mutation is fabricated. No source handler calls it yet: actual native ordinal mapping/operation owner/full reply and fresh offer issuer remain missing. It is not completed gameplay, cross-process atomicity or durable recovery. No schema/TW CUSTOM/CN database import or change to frozen Application/Session/auth/font/chat/IME/conversion occurs.\n\n'
            'Increment: read-only D3 request view1; common saved-name CAS writer1; common storage-offer coordinator1. Existing D3 value and07 consumer are not new packet inventory or a new qualified phase/owner/full route. Whole-game total/completed/percent remain unknown. Continue native name-rule/07 issuer/hosting, all gameplay/numeric extensions and full denominator work.\n')
    for rel in SOURCES:save('source/'+rel,(ROOT/rel).read_bytes())
    # Peer-only initial raster evidence; current CN file ranges reread, TW old
    # mapped image unavailable. Do not execute any frontend/GPU fixtures.
    peer=ROOT.parent/'God2/output/web-prototype';dest=out/'peer-handoff';dest.mkdir()
    expected={
        'reports/client-goal-20261007/native-world-raster-source.json':'e839845183f5f1b8f33ec7feb42854e98f3e2226344f03b6b9d7eb90d1d8ed8b',
        'reports/client-goal-20261007/native-world-raster-verification.json':'19246646784d8fb91bead52c023538a8a18111f7aa0ff0bd7dc1bbd239c6d1d7',
        'WEB_SERVER_INTEGRATION.md':'448271f0cf881ea6b5deee287b54ace50905935cf9126b17c8d07cc30058c57e'}
    files=[];values={}
    for rel,pin in expected.items():
        data=(peer/rel).read_bytes()
        if sha(data)!=pin:raise RuntimeError('Peer original differs')
        save('peer-handoff/'+(peer/rel).name,data);files.append({'original':str(peer/rel),'path':'peer-handoff/'+(peer/rel).name,'sha256':pin,'bytes':len(data)})
        if rel.endswith('.json'):values[(peer/rel).name]=json.loads(data)
    source=values['native-world-raster-source.json'];receipt=values['native-world-raster-verification.json'];ranges=[]
    for version,blocks in source['blocks'].items():
        for name,row in blocks.items():
            data=bytes.fromhex(row['bytes'])
            if len(data)!=row['length'] or sha(data)!=row['sha256']:raise RuntimeError('Peer raw range differs')
            current=version=='cn'
            if current and view.read(int(row['va'],16)-ib,len(data))!=data:raise RuntimeError('Peer CN range primary mismatch')
            ranges.append({'version':version,'name':name,'va':row['va'],'bytes':len(data),'sha256':sha(data),
                'current_primary_file_compared':current,'scope':'CN pinned primary file' if current else 'TW historical peer-provided range; original mapped image unavailable, not reread'})
    dump('peer-handoff/server-file-source-receipt.json',{'round':receipt['round'],'files':files,'ranges':ranges,
        'source_ranges':len(ranges),'cn_primary_file_ranges_compared':sum(r['current_primary_file_compared'] for r in ranges),
        'tw_historical_mapped_original_recovered':False,'prior_tile_queue_ack_read_confirmed_by_peer_message':True,
        'initial_drawing_scope':source['scope'],'guard_contract':source['guards'],'renderReady':receipt['renderReady'],
        'peer_capacity_point_in_time':receipt['capacity'],'server_capacity_remeasured':False,
        'peer_frontend_GPU_results_are_server_acceptance':False,'server_tests_or_fixture_run':False,
        'new_complete_routes':0,'remaining':receipt['limits']})
    print(json.dumps({k:findings[k] for k in ('round','native_metadata_envelopes_retained','scoped_entry_rooted_D3_caller_contexts','common_name_snapshot_cas_writers_added','common_name_offer_coordinators_added','new_complete_bidirectional_routes')}))


if __name__=='__main__':main()
