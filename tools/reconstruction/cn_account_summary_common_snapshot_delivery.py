"""Save concrete full common-root binding in existing native A6/07 selection."""
import hashlib
import json
from .cn_wrapper_route_frontier import ROOT, PIN

NAME='cn-account-summary-common-snapshot-01'
ROUND='20261007-cn-account-summary-common-snapshot'
SOURCES=('src/cn/auth/SharedAccountSelection.h','src/cn/auth/SharedAccountSelection.cpp',
    'tools/reconstruction/cn_account_summary_common_snapshot_delivery.py',
    'tools/reconstruction/dual_client_route_catalog.py',
    'docs/research/cn-account-summary-common-snapshot-20261007.md')


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():
        raise RuntimeError('Fresh before snapshot required; preserve prior artifacts')
    unchanged=[]
    for row in json.loads((out/'before-manifest.json').read_text(encoding='utf-8')):
        raw=(out/'before'/row['path']).read_bytes()
        if sha(raw)!=row['sha256']:raise RuntimeError('Before receipt changed')
        if row['path'] not in SOURCES:
            if raw!=(ROOT/row['path']).read_bytes():raise RuntimeError('Frozen/context source changed')
            unchanged.append(row)
    retained=[]
    for name in ('cn-create-post-choice-reconnect-01','cn-summary-local-cache-01'):
        original=base/name
        manifest=json.loads((original/'manifest.json').read_text(encoding='utf-8'))
        pins={r['path']:r['sha256'] for r in manifest['files']}
        if not manifest['sealed']:raise RuntimeError('Prior artifact not sealed')
        paths=('findings.json',)
        if name=='cn-create-post-choice-reconnect-01':
            paths+=('source-relations.json','native/index.json','native/00449310.bin','native/00449310.asm','native/00449310.c','native/00449310.cfg.json')
        for rel in paths:
            raw=(original/rel).read_bytes()
            if sha(raw)!=pins[rel]:raise RuntimeError('Prior native/source receipt changed')
            p=out/'retained-source'/name/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
            retained.append({'artifact':name,'path':rel,'bytes':len(raw),'sha256':sha(raw)})
    findings={'round':ROUND,'native_sha256':PIN,
        'previous_goal_turn_classification':'progress: ordinary reconnect primary chain retained and actual03 mutation-owner binding implemented; catalog84 sealed',
        'existing_account_selection_bindings_strengthened':1,'full_common_account_snapshot_bindings_added':1,
        'native_fields_newly_recovered':0,'new_packet_values':0,'new_source_owner_chains':0,
        'new_native_phase_source_bindings':0,'new_complete_bidirectional_routes':0,
        'whole_game_route_total':None,'whole_game_completion_percent':None,
        'existing_sources_unchanged':unchanged,'levels_changed':False,'build_run':False,
        'tests_run':False,'runtime_run':False,'database_access':False,'deployed':False,
        'remaining':['Actual native07 flags/opaque/inactive rows, visibility and ordered common-ID/native-slot issuer; no guessed40->36 conversion.',
            'Complete native account success/directory/summary/world00-1F source and configured common Application hosting.',
            'Queue/drain/crash and durable semantic replay recovery; cross-process storage/admission exclusion.',
            'Actual choice/spawn/full18/03 authority, standalone variants, all gameplay and complete native denominator.']}
    relations={'route':'existing A6 ->mandatory native07 source with exact account/target/full common account snapshot ->actual common repository root-set recheck ->existing selected grant/raw07 ->existing07 send',
        'native_baseline':'sealed84: ordinary43D280 reconnect ->440CA0->449060->449310;449363 calls481640 A6/full07;4493EE copies network mode account->world',
        'full_root_cas_fields':['id','account_id','slot','profile40','created_at','name_codepage','streamer_privilege'],
        'full_account_row_set':'Includes every common root used by issuer; active07 orderedIDs remain a separate subset. Order of repository enumeration is not identity.',
        'factory':'full75-byte07; scope account/group/server; non-null observing Current; all snapshot IDs unique/owned; active IDs/count/native slots distinct and refer to that snapshot',
        'storage_reads':'current actual list_for_account before and after authority callback, at Prepared and BeforePublish; full field equality and complete row-set size',
        'aggregate':'recheck every prepared summary before any07; recheck each before select so later source preparation cannot silently publish an old root snapshot',
        'identity':'common IDs are never native slots, row ordinals, names or routing-key/map equality',
        'empty_native_summary':'count0 allowed only through real complete07/current source and matching explicit account snapshot; not a generated empty-account success',
        'raw_native_bytes_rewritten':False,'native_level_changed':False,'schema_changed':False,
        'actual_native_issuer_added':False,'sql_transaction_executed':False,
        'limits':'serial source integration policy, not recovered official server rules or cross-process atomicity; old send/grant queue policy unchanged and delivery/recovery remains open'}
    with (ROOT/SOURCES[-1]).open('x',encoding='utf-8') as f:
        f.write('# CN A6/07 full common-account snapshot binding\n\n'
            'PHASE1 file/source work only. No build/test/native/server/SQL execution, migration or deployment. Levels unchanged. New native fields0; existing A6/07 binding strengthened1.\n\n'
            'The sealed ordinary43D280 success18 reconnect chain reaches440CA0->449060->449310. At449363 the actual native client calls481640 with selected group/server and raw07 destination;4493EE copies the resulting network mode from account to world. Prior native75-byte07/low3 slot/cache and opaque-byte receipts are retained, not rediscovered or generalized to all callers.\n\n'
            'Previously NativeSummary exposed only a raw record plus ordered IDs. Qualification checked current ownership of those IDs, so a source prepared from a stale common profile, old account row set or another target had no exact snapshot binding. The source is now a move-only NativeSummary from_native result with explicit account/target Scope, complete native07, ordered active common IDs, the complete common account-root snapshot and mandatory observing Current native-issuer/visibility predicate. Private retained values cannot be replaced between preparation and publication. The factory rejects malformed records, missing authority, foreign/duplicate roots, missing/duplicate active IDs and duplicate native slots. It generates no raw/native fields.\n\n'
            'Actual SharedAccountSelection::qualify now reads the same authoritative RecoveredCharacterRepository used by account/world composition. It compares the entire source account row set against current storage by actual ID, account, common slot, all40 profile bytes, creation timestamp, codepage and streamer privilege. Enumeration order is irrelevant. Checks occur before and after the actual authority callback. Prepared and BeforePublish checks qualify each complete record; the entire aggregate is requalified before publishing any07, then each record immediately before the existing admission select/send. A later preparation changing an earlier account snapshot is therefore rejected. Native target/catalog routing and existing account-owned grant checks remain.\n\n'
            'This snapshot contains all common roots used by the source; active07 IDs are a separate ordered subset because native target/visibility policy is not inferred from account ownership. count0 requires a real full07 and its native source predicate, with a matching explicit common snapshot. No empty-account template, common40->CN36 serializer, native slot=common slot/ID, name join, all-characters-visible policy or flags/row18 values are invented. The issuer must supply the actual native mapping and visibility rules. Callbacks observe only, do not write/yield/pump events or borrow temporary captures.\n\n'
            'This is a serial source freshness policy, not recovered official issuance or a cross-process atomic transaction. Full roots do not include every gameplay/native summary dependency; Current must qualify actual native state. Position/resource/appearance revisions, crash/queue/drain/durable replay and production supplier hosting remain open. Existing grant and fire-and-forget07 send policy is unchanged, so source publication must not be advertised as delivered/accepted gameplay. Application, Session, native account success/authentication/transport/login composition/common admission/SQL/movement are unchanged. No account DB access occurred.\n\n'
            'Increment: full common account snapshot binding1, existing A6/07 source binding strengthened1. Existing owner/phase bindings are not counted twice. New opcode/phase/owner/full routes0; whole-game total and percentage null. Next supply actual native07 mapping/opaque/visibility data and connect the full native auth/world providers; retain standalone18 variant, numeric extension, shared gameplay and denominator work.\n')
    for name,value in (('findings.json',findings),('source-relations.json',relations),('retained-evidence.json',retained)):
        with (out/name).open('x',encoding='utf-8') as f:f.write(json.dumps(value,indent=2)+'\n')
    for rel in SOURCES:
        p=out/'source'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/rel).read_bytes())
    print(json.dumps({k:findings[k] for k in ('round','existing_account_selection_bindings_strengthened','full_common_account_snapshot_bindings_added','new_complete_bidirectional_routes')}))


if __name__=='__main__':main()
