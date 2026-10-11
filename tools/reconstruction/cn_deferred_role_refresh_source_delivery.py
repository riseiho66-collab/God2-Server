"""Save actual CN retained refresh/frame-source changes; file-only accounting."""
import difflib,hashlib,json
from pathlib import Path
from .cn_wrapper_route_frontier import ROOT,PIN

NAME='cn-deferred-role-refresh-source-01'
ROUND='20261007-cn-deferred-role-refresh-source'
SOURCES=(
    'src/cn/world/CnDeferredRoleRefresh.h','src/cn/world/CnDeferredRoleRefresh.cpp',
    'src/cn/world/SharedNativeMovementScene.h','src/cn/world/SharedNativeMovementScene.cpp',
    'docs/research/cn-deferred-role-refresh-source-20261007.md',
    'tools/reconstruction/cn_deferred_role_refresh_source_delivery.py',
    'tools/reconstruction/dual_client_route_catalog.py')
REMAINING=[
    'Actual live deferred role/renderer/ROM/ACT/clear/path/lifetime suppliers remain unconfigured; source receipt is not native execution or emitted6D.',
    'Full31/68/6D upstream/native consumers and server permission/rules/response/storage remain open; same opcode does not pair directions.',
    'Actual account/world/native appearance issuers, TW common registry, PC/web/WSS hosting, full gameplay/numeric/security and exhaustive state/variant denominator remain open.']

def sha(b):return hashlib.sha256(b).hexdigest()
def main():
    b=ROOT/'artifacts/integration/packet-connections-20261006';out=b/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():
        raise RuntimeError('Fresh source snapshot required')
    def save(rel,data):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(data)
    def dump(rel,v):save(rel,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    before=json.loads((out/'before-manifest.json').read_text(encoding='utf-8'))
    old={x['path']:(out/x['snapshot']).read_bytes() for x in before}
    for row in before:
        if sha(old[row['path']])!=row['sha256']:raise RuntimeError('Before source changed')
    protected=[]
    changed=set(SOURCES)|{'docs/PACKET_CONNECTION_GOAL_20261006.md',
        'artifacts/integration/packet-connections-20261006/packet-route-ledger.json'}
    for row in before:
        if row['path'] not in changed:
            if (ROOT/row['path']).read_bytes()!=old[row['path']]:raise RuntimeError('Protected source differs')
            protected.append(row)
    env=json.loads((out/'native/function-envelopes.json').read_text(encoding='utf-8'))
    if env['sha256']!=PIN:raise RuntimeError('Native identity differs')
    tables=json.loads((out/'native-addendum/primary-table-relations.json').read_text(encoding='utf-8'))
    wrappers=json.loads((out/'native-addendum/scoped-wrapper-branches.json').read_text(encoding='utf-8'))
    # Union primary metadata and additive byte windows; shared table cells within
    # the contiguous wrapper are not separately counted as new bytes.
    ranges=[(int(x['va'],16),x['bytes']) for x in env['ranges']]
    ranges += [(int(x['va'],16),x['bytes']) for x in tables['ranges']]
    ranges.append((0x4815e0,wrappers['emitter_bytes']))
    covered=set()
    for va,n in ranges:covered.update(range(va,va+n))
    variants=[
        dict(id='cn:world:4A:immediate-retained-operand',gate='entry actor state !=8',effect='overwrite+89B240 then immediate5385F0; does not clear pending'),
        dict(id='cn:world:4A:deferred-last-write',gate='entry actor state8',effect='overwrite same+89B240 and set pending1; not FIFO'),
        dict(id='cn:world:4A:step-incomplete',gate='5393B0 return !=1',effect='pending and cursor not consumed by this drain'),
        dict(id='cn:world:4A:step-complete-pending-zero',gate='state8,5393B0=1,pending0',effect='no refresh call; cursor processing continues'),
        dict(id='cn:world:4A:step-complete-pending-nonzero',gate='state8,5393B0=1,pending!=0',effect='refresh current single operand, clear after return, cursor processing continues'),
        dict(id='cn:world:4A:refresh-early-return',gate='pending drain flags first mask02/04/08',effect='refresh returns before6D; enclosing drain still clears pending/proceeds')]
    for x in variants:x.update(source_runtime_connected=False,complete_bidirectional_route=False,native_acceptance=False,server_reply_pairing=None)
    relation=dict(client_sha256=PIN,variants=variants,primary_tables=tables,wrapper_branches=wrappers,
        saved_renderer_state_gate='5385F0 snapshots+a69F4C before reset; only reached normal end and nonzero prior state issues6D00',
        exhaustive_writer_scan=False,high_address_recovery_is_primary=False,actual_source_configured=False)
    dump('native/source-relations.json',relation)
    facts=dict(round=ROUND,previous_goal_turn_classification='no progress: status-only answer; revalidated and pursued native deferred refresh source',
        cn_actual_deferred_refresh_readonly_sources_added=1,cn_existing_frame_source_bindings_strengthened=1,
        scoped_native_receive_drain_variants=6,native_function_envelopes_read=env['functions']+1,
        native_metadata_bytes_read=env['bytes']+wrappers['emitter_bytes'],native_unique_bytes_read=len(covered),
        new_packet_values=0,new_native_phase_source_bindings=0,new_source_owner_chains=0,new_tw_source_owner_chains=0,
        new_complete_bidirectional_routes=0,whole_game_route_total=None,whole_game_completed_routes=None,
        whole_game_completion_percent=None,source_issuer_configured=False,formal_application_hosted=False,
        levels_changed=False,common_storage_changed=False,build_run=False,tests_run=False,runtime_run=False,
        Cplusplus_reader_run=False,database_access=False,deployed=False,protected_contexts=protected,remaining=REMAINING)
    dump('findings.json',facts)
    ledgerpath=b/'packet-route-ledger.json';ledger=json.loads(ledgerpath.read_text(encoding='utf-8'))
    ledger['cn_deferred_role_refresh_source']=dict(facts,evidence=out.relative_to(ROOT).as_posix())
    ledger['dual_client_source_segments'].append(dict(
        name='CN actual retained4A operand/pending owner ->completed frame deferred refresh source receipt ->existing actual path/clock source',
        version_scope='cn-native-frame-source-only',status='Existing conditional frame source strengthened; actual provider/refresh/6D authority unconfigured',
        source_paths=list(SOURCES),native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,
        tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,
        evidence=out.relative_to(ROOT).as_posix(),remaining=REMAINING))
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next_source_frontier']='Continue31/68 native consumer/upstream authority, actual4A refresh/renderer lifetimes and6D source/rules; actual account/world providers and all gameplay/numeric/hosting/denominator remain open. PHASE1 only.'
    ledgerpath.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    goal='docs/PACKET_CONNECTION_GOAL_20261006.md'
    with (ROOT/goal).open('a',encoding='utf-8') as f:
        f.write('\n\n## CN deferred role refresh source ('+ROUND+')\n\n'
            'Primary4A single cached DWORD/last-write behavior, pending drain after actual completed step, outer clear after refresh early returns and31/68/6D exact wrapper table/payload00 scopes recovered. Added actual owner/revision/Current readonly deferred source and strengthened existing completed-frame/path handoff with fresh same-owner pending-clear receipt. No provider, renderer/resource success,6D authority or full path configured. Nine envelopes15707B/15995 uniqueB; six scoped variants are not packets/routes. New opcode/phase/owner/full0; no build/test/native/C++reader/DB/deploy; levels/frozen/shared values unchanged. See research/cn-deferred-role-refresh-source-20261007.md.\n')
    origins=[]
    for rel in sorted(set(SOURCES)|{goal,ledgerpath.relative_to(ROOT).as_posix()}):
        data=(ROOT/rel).read_bytes();snap='source/'+rel;save(snap,data)
        origins.append(dict(path=rel,snapshot=snap,sha256=sha(data),bytes=len(data)))
        if rel in old:
            diff=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),data.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='source/'+rel))
            if diff:save('diff/'+rel+'.diff',diff.encode('utf-8'))
    dump('source/source-origins.json',origins)
    print(json.dumps({k:facts[k] for k in ('round','native_function_envelopes_read','native_unique_bytes_read','cn_existing_frame_source_bindings_strengthened','new_complete_bidirectional_routes')}))
if __name__=='__main__':main()
