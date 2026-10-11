"""Static CN account D3 -> actual common-name CAS -> full native07 publication receipt."""
import csv
import hashlib
import json
import struct
import capstone
import pefile
from .cn_wrapper_route_frontier import ROOT,CN,RECOVERY,PIN
from .cn_pe_import_directory import FileView
from .cn_delete_caller_seh_frontier import decode_cfg

NAME='cn-selection-name-operation-01'
ROUND='20261007-cn-selection-name-operation'
FUNCTIONS=('0047f750','00481440','00440b20','00446bd0','00480650','00567b50')
SOURCES=('src/cn/auth/SharedAccountSelection.h','src/cn/auth/SharedAccountSelection.cpp',
    'src/cn/auth/SharedAccountNameOperation.cpp','src/cn/auth/SharedAccountSuccess.h',
    'src/cn/auth/SharedAccountSuccess.cpp','src/cn/auth/SharedLoginComposition.h',
    'src/cn/auth/SharedLoginComposition.cpp','tools/reconstruction/cn_selection_name_operation_delivery.py',
    'tools/reconstruction/dual_client_route_catalog.py','docs/research/cn-selection-name-operation-20261007.md')

def sha(raw):return hashlib.sha256(raw).hexdigest()

def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():
        raise RuntimeError('Fresh before receipt required')
    def save(rel,raw):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(raw)
    def dump(rel,value):save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    unchanged=[]
    for row in json.loads((out/'before-manifest.json').read_text(encoding='utf-8')):
        data=(out/'before'/row['path']).read_bytes()
        if sha(data)!=row['sha256']:raise RuntimeError('Before bytes changed')
        if row['path'] not in SOURCES and row['path'] not in (
            'artifacts/integration/packet-connections-20261006/packet-route-ledger.json',
            'docs/PACKET_CONNECTION_GOAL_20261006.md'):
            if data!=(ROOT/row['path']).read_bytes():raise RuntimeError('Preserved source changed')
            unchanged.append(row)
    prior=base/'cn-selection-name-identity-01'
    seal=json.loads((prior/'manifest.json').read_text(encoding='utf-8'))
    pins={r['path']:r['sha256'] for r in seal['files']}
    data=(prior/'qualified-switches.json').read_bytes()
    if not seal['sealed'] or sha(data)!=pins['qualified-switches.json']:raise RuntimeError('Prior switch receipt differs')
    switches=json.loads(data);save('retained-source/qualified-switches.json',data)
    raw=(CN.parent/'XJZ-CN/God2_opt.exe').read_bytes()
    if sha(raw)!=PIN:raise RuntimeError('Native pin changed')
    pe=pefile.PE(data=raw,fast_load=True);view=FileView(pe,raw);ib=pe.OPTIONAL_HEADER.ImageBase
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
    metadata=(RECOVERY/'functions.tsv').read_bytes();save('native/functions.tsv',metadata)
    rows={r['address']:r for r in csv.DictReader(metadata.decode('utf-8-sig').splitlines(),delimiter='\t')}
    length_rows=json.loads((CN/'artifacts/native/20261006-cn-baseline/s2c-lengths.json').read_text(encoding='utf-8'))
    length_evidence=[]
    for r in length_rows:
        if r['opcode'] not in (7,30):continue
        table=view.read(int(r['table_va'],16)-ib,4);target=struct.unpack('<I',table)[0]
        branch=view.read(target-ib,len(bytes.fromhex(r['branch_bytes'])))
        if target!=int(r['branch_va'],16) or branch.hex()!=r['branch_bytes']:raise RuntimeError('Primary length differs')
        save(f'native/length-{r["opcode"]:02x}-table.bin',table)
        save(f'native/length-{r["opcode"]:02x}-branch.bin',branch)
        length_evidence.append({**r,'primary_table_hex':table.hex(),'primary_branch_hex':branch.hex(),
            'whole_phase_variants_proven':False})
    dump('native/scoped-length-evidence.json',length_evidence)
    native=[];qualified=[];decoded={}
    for entry in FUNCTIONS:
        row=rows[entry];va=int(entry,16);code=view.read(va-ib,int(row['bytes']));tables={}
        for t in [t for t in switches if t['function']==entry and 'table' in t]:
            guard=bytes.fromhex(t['guard_bytes'])
            if view.read(int(t['guard'],16)-ib,len(guard))!=guard:raise RuntimeError('Primary guard differs')
            data=view.read(int(t['table'],16)-ib,t['entries']*4);targets=struct.unpack('<'+'I'*t['entries'],data)
            if [f'{x:08x}' for x in targets]!=t['targets']:raise RuntimeError('Primary switch differs')
            tables[int(t['dispatch'],16)]=targets;qualified.append(t);save('native/tables/'+t['table']+'.bin',data)
        if entry=='00480650':
            data=view.read(0x480aa4-ib,72);tables[0x480669]=struct.unpack('<18I',data)
            save('native/tables/00480aa4.bin',data);save('native/tables/00480aec.bin',view.read(0x480aec-ib,35))
        cfg,asm,ins=decode_cfg(md,code,va,va+len(code),tables);decoded[entry]=ins
        save('native/'+entry+'.bin',code);save('native/'+entry+'.asm',asm)
        save('native/'+entry+'.c',(RECOVERY/row['file']).read_bytes());dump('native/'+entry+'.cfg.json',cfg)
        native.append({'entry':entry,'metadata_file':row['file'],'bytes':len(code),'sha256':sha(code),
            'rooted_instructions':len(ins),'open_edges':cfg['open_edges'],'overlap':cfg['instruction_overlap_found']})
    dump('native/index.json',native);dump('qualified-switches.json',qualified)
    dump('source-relations.json',{
        'actual_chain':'native normal name UI ->ACCOUNT D3 logical25 ->SharedAccountSelection receive_name ->published full07 identity ->actual NameDecision/native rule lease ->SharedCharacterNameReplacement ->same common SQL full-root CAS ->all TW/CN old offers invalidated ->source full refreshed07 ->exact queued selection/IO publication barrier ->native47F750 raw74 copy/state4',
        'failure':'source complete native1E logical2 ->unchanged full common roots/current original offer ->same actual IO publication barrier; no guessed selector or saved-name write',
        'identity':'native row ordinal from exact published07/source generation/session/revision, not slot/name/commonID claim',
        'BeforeReplace':'full original identity/root set and native operation lease',
        'BeforeCommit':'staged new full root set and actual native lease; deliberately no old name-root current check',
        'BeforePublish':'real committed common root set, actual native source/phase/occupancy and complete75-byte native07',
        'QueueAccepted':'same real roots/current native sources/exact new queued revision, then commit before IO release',
        'late_completion':'local queue acceptance only; no stale old-offer veto or world-ticket revocation after a fast valid world claim',
        'hosting':'compose_native_login binds optional actual naming source via same preparation/storage/catalog/presence identity, thenSharedAccountSuccess installs it BEFORE native success publication and read release. Actual rules/data/configured host still absent.',
        'qualified_scope':'one complete D3 aggregate and exact raw submitted-name echo in refreshed07; other aggregate/canonicalization forms remain open',
        'durability':'queue failure after real name COMMIT retains saved change; durable operation receipt/recovery not completed'})
    # Retain peer originals already SHA-compared on receipt. Only file-based CN
    # range comparison here; no peer frontend/GPU/runtime fixtures are run.
    peer=out/'peer-handoff';s=json.loads((peer/'native-world-loop-source.json').read_text(encoding='utf-8'))
    r=json.loads((peer/'native-world-loop-verification.json').read_text(encoding='utf-8'));ranges=[]
    for version,blocks in s['blocks'].items():
        for name,row in blocks.items():
            data=bytes.fromhex(row['bytes'])
            if len(data)!=row['length'] or sha(data)!=row['sha256']:raise RuntimeError('Peer block hash differs')
            compared=version=='cn'
            if compared and view.read(int(row['va'],16)-ib,len(data))!=data:raise RuntimeError('Peer CN primary differs')
            ranges.append({'version':version,'name':name,'va':row['va'],'bytes':len(data),'sha256':sha(data),
                'current_primary_file_compared':compared})
    for version,table in s['tables'].items():
        for name in ('indices','targets'):
            row=table[name];data=bytes.fromhex(row['bytes'])
            if len(data)!=row['length'] or sha(data)!=row['sha256']:raise RuntimeError('Peer table hash differs')
            compared=version=='cn'
            if compared and view.read(int(row['va'],16)-ib,len(data))!=data:raise RuntimeError('Peer CN primary table differs')
            ranges.append({'version':version,'name':'table:'+name,'va':row['va'],'bytes':len(data),'sha256':sha(data),
                'current_primary_file_compared':compared})
    dump('peer-handoff/server-file-source-receipt.json',{'round':r['round'],'ranges':ranges,
        'source_blocks':sum(len(v) for v in s['blocks'].values()),'separate_table_ranges':4,
        'cn_primary_file_ranges_compared':sum(x['current_primary_file_compared'] for x in ranges),
        'tw_original_mapped_image_recovered':False,'tw_scope':'peer historical source bytes; mapped original unavailable, not reread',
        'qualification':s['qualification'],'normalDispatch':s['normalDispatch'],'scope':s['scope'],
        'renderReady':r['renderReady'],'peer_capacity_point_in_time':r['capacity'],'server_capacity_remeasured':False,
        'server_tests_or_fixtures_run':False,'peer_frontend_results_are_server_native_acceptance':False,
        'server_previous_raster_ack_read_confirmed':True,'new_complete_routes':0,'remaining':r['limits']})
    findings={'round':ROUND,'native_sha256':PIN,'previous_goal_turn_classification':'progress: sealed actual published07 ordinal/common full-root name identity source',
        'native_metadata_envelopes_retained':len(native),'new_conditional_source_owner_chains':1,
        'account_D3_ingress_source_handlers_added':1,'shared_name_CAS_to_native07_publication_bindings_added':1,
        'account_login_name_source_composition_bindings_added':1,'new_native_phase_source_bindings':3,
        'new_packet_values':0,'new_complete_bidirectional_routes':0,'whole_game_route_total':None,'whole_game_completion_percent':None,
        'levels_changed':False,'build_run':False,'tests_run':False,'runtime_run':False,'database_access':False,'deployed':False,
        'existing_sources_unchanged':unchanged,'remaining':[
            'Actual native naming permissions/equivalence/uniqueness/replay/lease, explicit common-name projection and source-issued full07/errors; no configured provider/production hosting.',
            'Semantic replay/durable operation receipts, crash/cross-process recovery and committed name without delivered07 recovery.',
            'Native mixed/aggregate D3 and case/canonicalization forms beyond this exact raw-echo normal prompt branch.',
            'Full auth/catalog/world providers, all gameplay/numeric wire/object/display and directional/state/variant/indirect/deferred denominator.']}
    dump('findings.json',findings)
    with (ROOT/SOURCES[-1]).open('x',encoding='utf-8') as f:
        f.write('# CN account naming operation: common CAS and full native07 publication\n\n'
            'PHASE1 static primary PE/source accounting only. No build/tests/native/emulator/server/SQL/deployment. Previous sealed published07 name identity turn was progress. Levels remain unchanged.\n\n'
            'Six pinned metadata envelopes retain primary bytes, assembly, entry CFG and navigation C. Prior scoped UI switches remain primary-checked. Current native length-table entries independently resolve07 to75 bytes and1E to2 bytes, with primary target/branch bytes retained.47F750 scoped ACCOUNT UI callers supply nativeD3 logical25; its accepted07 full74-payload copy and1E formatter are unchanged native consumers. Length/helper entries are not the whole-game denominator or official server emission rules.\n\n'
            'SharedAccountSelection now dispatches one complete nativeD3 aggregate to receive_name. Trailing/mixed mutation aggregates are rejected before any write and remain unqualified native variants. Required NameSources are actual same SQLite repository, actual prepared/active occupancy observer, observing native account phase and source prepare callback. No source is installed by default; missing rules/results are not generic success. Exact scope retains verified account/account-session/target/common character/ordinal and a private server attempt identity. Submitted name never selects a database row.\n\n'
            'A source NameDecision supplies either explicit qualified common16-byte name/codepage plus a COMPLETE native refreshed07 and mandatory native lease observer, or complete2-byte1E and observer. It is move-only. Successful full07 must map the exact same common character, echo submitted raw native bytes in that mapped row and carry the complete expected common account root set with only the actual name/codepage changed. Flags/opaque/inactive native bytes are retained; no zero-padding reply or40-to36 profile synthesis is performed. Exact echo is the bounded supported form, not proof that all native canonicalization forms are exhausted.\n\n'
            'Real shared writer path: full original offered identity ->same repository/full-account-root BEGIN IMMEDIATE CAS ->mandatory BeforeReplace original identity/native lease ->BeforeCommit staged NEW common roots/native lease ->real COMMIT ->prepared all-TW/CN old-offer invalidation without yield. The actual coordinator enforces prepared/active occupancy. Unrelated fields, IDs/slots/creation times/style/levels/save descendants and other characters stay intact. BeforeCommit never wrongly demands the old name snapshot. No schema/import/new table/storage API is added.\n\n'
            'After real COMMIT the operation checks actual changed full roots/presence/native lease and qualifies source full07 before beginning a NEW exact selection queue. Native07 is held behind the actual transport IO publication barrier. QueueAccepted again reads complete changed roots, observes mandatory actual rules/summary issuer and exact queued token; commit publishes its source/revision before IO release.1E uses the same barrier with unchanged roots/original identity and no saved mutation/new selection. Callback completion is local queue acceptance, not native client acceptance. A fast valid world claim is not vetoed by a late old-offer check or revoked here. Failure after saved COMMIT keeps the changed save; no fake rollback or invented error reply. Durable receipt/recovery remains open.\n\n'
            'Actual login composition now forwards optional naming sources into SharedAccountSuccess BEFORE success publication/read release. When present, composition requires the same actual SharedWorldPreparation common repository/catalog and its exact presence registry; Selection independently requires the same concrete SQL repository/presence owner. Actual native source callbacks, configured Application hosting and persistent replay/recovery remain missing. This is a conditional source owner chain, not deployed/native accepted gameplay. Existing credential/font/chat/IME/conversion/ordinary transport/shared save behavior is preserved.\n\n'
            'Increment: D3 account ingress handler1, common CAS-to-full07 publication binding1, login naming-source composition binding1; conditional CN owner chain1 and phase source bindings3 (ACCOUNT C2SD3/S2C07/S2C1E). Existing packet values remain unchanged; complete bidirectional routes0. Continue actual rule/data owners and all whole-game source/numeric/inventory work.\n')
    for rel in SOURCES:save('source/'+rel,(ROOT/rel).read_bytes())
    print(json.dumps({k:findings[k] for k in ('round','native_metadata_envelopes_retained','new_conditional_source_owner_chains','new_native_phase_source_bindings','new_complete_bidirectional_routes')}))

if __name__=='__main__':main()
