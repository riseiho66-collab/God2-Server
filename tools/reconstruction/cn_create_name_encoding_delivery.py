"""Static ordinary CN17/common creation name identity and retained web handoff.

Source and primary file receipts only. No codec/native/DLL/API, SQL, server,
build, tests, browser fixtures or deployment. Earlier sealed receipts retained.
"""
import csv
import hashlib
import json
import capstone
import pefile
from .cn_wrapper_route_frontier import ROOT,CN,RECOVERY,PIN
from .cn_pe_import_directory import FileView
from .cn_delete_caller_seh_frontier import decode_cfg

NAME='cn-create-name-encoding-01'
ROUND='20261007-cn-create-name-encoding'
FUNCTIONS=('0043d8b0','00433b00','0047e900')
SOURCES=('src/cn/auth/CnCreationNameProjection.h','src/cn/auth/CnCreationNameProjection.cpp',
    'src/cn/auth/SharedCharacterCreateOperation.h','src/cn/auth/SharedCharacterCreateOperation.cpp',
    'src/cn/protocol/CnCharacterCreate.h','tools/reconstruction/cn_create_name_encoding_delivery.py',
    'tools/reconstruction/dual_client_route_catalog.py','docs/research/cn-create-name-encoding-20261007.md')
REMAINING=[
    'Actual native ordinary17 common non-name profile/slot/default resources/roles/fees/native choices and full02 issuer; no configured native providers or production host.',
    'Native canonicalized/aliased names and other producer variants, cross-encoding uniqueness, permission/replay/operation leases and actual codec/NLS qualification remain open.',
    'Atomic native non-root initialization, durable create/choice receipts, cross-process invalidation and committed-root/publication recovery remain open.',
    'Complete native auth/world, all TW/CN/web gameplay and extended numeric wire/object/display, whole-game phase/state/variant/indirect/deferred denominator. Levels unchanged.']
DOCUMENT='''# CN ordinary creation: original-name request/common snapshot binding

PHASE1 static primary PE/source accounting. No build, tests, codec/native/API/DLL/emulator/server/SQL execution, migration or deployment. The preceding sealed D3 name encoding turn was progress. Levels remain native and unchanged. This strengthens existing ordinary17 paths, not a new gameplay route or opcode.

Primary metadata envelopes43D8B0/433B00/47E900 retain bytes, entry-rooted assembly/CFG and navigation C.43D8B0 passes max14 to433B00, calls existing458C70 filter and requires nonempty UI bytes; calls/filter are not reinterpreted as recovered server permission/uniqueness.433B00 bounded raw copy may truncate the UI input; this new server projection never truncates or replaces name bytes.47E900 observes existing connected-byte state, writes payload40=4, invokes481440 with17/payload44 and flushes through47F430. These existing producer facts do not prove all producers, canonicalization or original server create rules. Current native02/18 layouts and prior common CAS/operation receipts remain historical sealed inputs; no baseline is overwritten.

CnCharacterCreate now exposes all45 original logical bytes as an immutable copied record; unknown payload bytes are retained. CnCreationNameProjection privately binds that complete17 record to an explicitly supplied NewOwnedCharacter: slot, ALL40 common profile bytes, name_codepage and style. The normal UI name must fit the prior14-byte/noNUL common boundary, decode exactly as936 and have the same originalUTF8 as the candidate's explicitly encoded common-name prefix. It reuses OwnedCharacterNameText's strict byte/Unicode roundtrip. Explicit936/950 or unbound0 ASCII are admitted; no CP_ACP/display preference/fallback/script conversion/normalization/case folding/name lookup. All supplied common bytes, including postNUL and non-name fields, are preserved. No44-to40 copy, slot allocation, progression/default-stat or style entitlement is synthesized. Invalid or unrepresentable remains absent; missing codec/runtime errors reach the actual ingress failure boundary. Codec/NLS is not executed or accepted here.

Actual common CAS path: NativeCreatePlan success requires this typed projection and an exact match to its pointer-qualified Scope request, before any INSERT. start again observes full request binding, passes precisely storage_candidate to the existing same-repository create_owned_snapshot, and checks all supplied candidate fields against the actual returned created row. Existing full-account-root CAS, real ID/created_at, BeforeInsert/BeforeCommit native rule observers and actual COMMIT remain unchanged. Whole profile bytes do not become recovered native field meanings merely because they are bound; complete native source providers still own those fields and rules.

Both existing source modes now qualify created-name identity in CreateResult::from_native: the concrete CAS mode and the direct real transaction callback must return a common row whose original name matches the full request's normal UI name. Existing account owner/new-ID/full-root/choices and mandatory current predicate checks remain. Native02 success cannot publish an unrelated stored name. Direct callbacks still own prewrite/atomic semantics; this result check occurs after their transaction and cannot undo a COMMIT. Missing/different results close through the existing failure boundary without pretending the save was rolled back or manufacturing a native error. Nonzero source-issued full02 still requires no candidate/created/choices and performs no CAS write. Native18 choice, full request pointer lifetime, immutable result snapshots and queue acceptance checks stay intact; no new canonicalization/replay authority is inferred.

Saved accounts/characters, SQL schema, old rows, request field meanings and native levels are preserved. Existing common SQL writer, shared name codec, text conversion, login/selection/choice controllers, Application, frozen TW creation, fonts/chat/IME/portraits are unchanged. API change is additive in this unhosted source layer; no configured NativeCreatePlan provider was present. Actual native defaults/resources/non-root creation, all permission/equivalence/unique/lease/replay/full02 providers, cross-process/receipt/publication recovery and mixed/canonicalized variants remain open.

Increment: CN typed normal creation-name projection1, existing17 common CAS binding strengthened1, both-mode created-name result qualification1 and existing immutable request snapshot accessor1. New owner chains/phase bindings/opcode values/complete bidirectional routes0. Shared strict original-name boundary is reused, not counted twice. Whole-game total/completed/percentage unknown.

Peer handoff20261007-native-world-controller: three exact SHA-pinned original files saved, with53 hashed ranges. CN27 compared to the current primary pinned PE; TW26 retained as peer historical source, with the specified historical mapped-original path absent and no original restoration/current reread claim. Controller status/branch comes from local UI/operation input fields, never socket/packet/transport state. Actual local ACT precedes the counter, final update return precedes the clock/FP sample, and at most one extra dispatch follows. Peer14 frontend regressions and fixture assertions remain peer records, not server/native acceptance. Complete UI/world/time/FP/browser driver/ticked raster/cache/scene/peer/actions/CN assets and four WS/WSS authority/replay acceptance remain open, renderReady=false/new gameplay0. Previous loop ACK and local-controller correction were read by the peer; this new SHA ACK is sent and its read confirmation is pending. No new server clock/animation packet, competing browser server or client edit is introduced. Peer capacity is its recorded point-in-time measurement, not a server remeasurement.
'''

def sha(data):return hashlib.sha256(data).hexdigest()

def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():
        raise RuntimeError('Require fresh before receipt')
    def save(rel,data):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(data)
    def dump(rel,value):save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    unchanged=[]
    for row in json.loads((out/'before-manifest.json').read_text(encoding='utf-8')):
        data=(out/'before'/row['path']).read_bytes()
        if sha(data)!=row['sha256']:raise RuntimeError('Before bytes changed')
        if row['path'] not in SOURCES and row['path'] not in (
            'docs/PACKET_CONNECTION_GOAL_20261006.md',
            'artifacts/integration/packet-connections-20261006/packet-route-ledger.json'):
            if data!=(ROOT/row['path']).read_bytes():raise RuntimeError('Preserved source changed')
            unchanged.append(row)
    for name in ('cn-selection-name-encoding-01','cn-create-common-cas-01','cn-character-create-operation-01'):
        prior=base/name;seal=json.loads((prior/'manifest.json').read_text(encoding='utf-8'))
        pins={row['path']:row['sha256'] for row in seal['files']};data=(prior/'findings.json').read_bytes()
        if not seal['sealed'] or sha(data)!=pins['findings.json']:raise RuntimeError('Prior source receipt differs')
        save('retained-source/'+name+'/findings.json',data)
    raw=(CN.parent/'XJZ-CN/God2_opt.exe').read_bytes()
    if sha(raw)!=PIN:raise RuntimeError('Native pin changed')
    pe=pefile.PE(data=raw,fast_load=True);view=FileView(pe,raw);ib=pe.OPTIONAL_HEADER.ImageBase
    metadata=(RECOVERY/'functions.tsv').read_bytes()
    rows={r['address']:r for r in csv.DictReader(metadata.decode('utf-8-sig').splitlines(),delimiter='\t')}
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True;native=[]
    for entry in FUNCTIONS:
        row=rows[entry];va=int(entry,16);code=view.read(va-ib,int(row['bytes']))
        cfg,asm,ins=decode_cfg(md,code,va,va+len(code),{})
        save('native/'+entry+'.bin',code);save('native/'+entry+'.asm',asm)
        dump('native/'+entry+'.cfg.json',cfg);save('native/'+entry+'.c',(RECOVERY/row['file']).read_bytes())
        native.append({'entry':entry,'metadata':row,'bytes':len(code),'sha256':sha(code),
            'rooted_instructions':len(ins),'open_edges':cfg['open_edges'],'calls_followed':False,'whole_program_closed':False})
    dump('native/index.json',native)
    dump('native/metadata-provenance.json',{'original':str(RECOVERY/'functions.tsv'),'sha256':sha(metadata),
        'selected_rows':[rows[e] for e in FUNCTIONS],'navigation_C_is_primary_bytes':False})
    # Handoff source was already pinned/saved/compared and ACKed without running
    # any peer fixtures. Retain its exact prior file receipt in this source turn.
    peer=out/'peer-handoff';receipt=json.loads((peer/'server-file-source-receipt.json').read_text(encoding='utf-8'))
    for row in json.loads((peer/'input-manifest.json').read_text(encoding='utf-8')):
        if sha((peer/row['snapshot']).read_bytes())!=row['sha256']:raise RuntimeError('Peer original changed')
    if receipt['cn_current_primary_ranges']!=27 or receipt['tw_peer_historical_ranges']!=26 or receipt['renderReady']:
        raise RuntimeError('Peer qualification differs')
    relations={'cas':'full native17 ->typed original-name/common40 snapshot projection ->NativeCreatePlan ->same existing full-root shared SQLite CAS ->actual matching created row ->CreateResult ->complete source-issued02 ->pending ordinary18',
        'direct_mode':'actual create callback ->real created row ->same original-name result qualification ->existing full native02/current checks; callback owns prewrite semantics',
        'full_candidate_binding':['native logical45','common slot','common profile40','explicit codepage','style'],
        'shared_name_boundary':'OwnedCharacterNameText reused from sealed previous turn; unchanged originalUTF8/explicit encoding, no display/script mapping',
        'common_fields':'ALL40 explicitly supplied bytes retained, no native44->common40 map, defaults or level field changes',
        'direct_or_after_COMMIT_failure':'retain actual saved row; no fake rollback/error/native acceptance',
        'native_authority':'all actual permission/unique/choice/default/replay/issuer leases and providers remain mandatory',
        'web_controller':'local UI/operation, not transport; original sources retained, no server clock packet'}
    dump('source-relations.json',relations)
    findings={'round':ROUND,'native_sha256':PIN,'previous_goal_turn_classification':'progress: sealed typed CN D3 same-original-name/common encoding source integration, catalog93',
        'native_metadata_envelopes_retained':len(native),'cn_creation_name_projections_added':1,
        'existing_cn17_CAS_source_bindings_strengthened':1,'created_name_result_qualifications_added':1,
        'existing_read_only_request_snapshot_accessors_added':1,'shared_name_boundary_reused_not_recounted':True,
        'new_source_owner_chains':0,'new_native_phase_source_bindings':0,'new_packet_values':0,'new_complete_bidirectional_routes':0,
        'whole_game_route_total':None,'whole_game_completion_percent':None,'native_rules_or_defaults_invented':False,
        'configured_native_provider_installed':False,'formal_application_hosted':False,'levels_changed':False,
        'build_run':False,'tests_run':False,'runtime_run':False,'database_access':False,'deployed':False,
        'existing_sources_unchanged':unchanged,'web_peer_ranges_retained':53,'web_CN_primary_ranges_compared':27,
        'web_TW_historical_ranges_retained':26,'web_renderReady':False,'peer_frontend_results_are_server_native_acceptance':False,
        'remaining':REMAINING}
    dump('findings.json',findings)
    with (ROOT/SOURCES[-1]).open('x',encoding='utf-8') as f:f.write(DOCUMENT)
    for rel in SOURCES:save('source/'+rel,(ROOT/rel).read_bytes())
    print(json.dumps({k:findings[k] for k in ('round','cn_creation_name_projections_added',
        'existing_cn17_CAS_source_bindings_strengthened','created_name_result_qualifications_added',
        'web_CN_primary_ranges_compared','new_complete_bidirectional_routes')}))

if __name__=='__main__':main()
