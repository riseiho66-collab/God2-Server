"""File-only common credential source and held CN publication receipts."""
import difflib,hashlib,json
from pathlib import Path
from .cn_wrapper_route_frontier import ROOT,PIN

NAME='cn-credential-source-continuity-01'
ROUND='20261007-cn-credential-source-continuity'
SOURCES=('src/cn/auth/SharedAccountVerifier.h','src/cn/auth/SharedAccountVerifier.cpp',
    'src/cn/net/SharedCredentialConnection.h','src/cn/net/SharedCredentialConnection.cpp',
    'src/cn/auth/SharedAccountSuccess.cpp','src/cn/auth/SharedWorldSelection.cpp',
    'src/cn/auth/SharedLoginComposition.cpp',
    'tools/reconstruction/cn_credential_source_continuity_delivery.py',
    'docs/research/cn-credential-source-continuity-20261007.md')
REMAINING=[
    'Current-value equality is not a monotonic credential revision: ABA, external writes, cross-process authority, revocation/entitlement/session policy remain open.',
    'Actual native seed/issued1D/billing0A/catalog/key/deadline/current policy and complete07/1F/02/2A/6F/equipment/scene/ACT/observer providers, TW registry and formal PC/web/WSS hosting remain open.',
    'Gameplay/numeric/items/trade/quests/battle/skills/monsters/pets/guilds/recovery and complete directional/state/variant/indirect/deferred denominator remain open; levels unchanged; comprehensive tests follow full source connection.',
]
def sha(data):return hashlib.sha256(data).hexdigest()
def body(data,signature):
    start=data.index(signature);at=data.index(b'{',start);depth=1;end=at+1
    while depth:depth+=(data[end]==123)-(data[end]==125);end+=1
    return data[start:end]
def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():raise RuntimeError('Fresh receipt required')
    def save(rel,data):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(data)
    def dump(rel,v):save(rel,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    rows=json.loads((out/'before-manifest.json').read_text(encoding='utf-8'));old={};preserved=[];after=[]
    for row in rows:
        data=(out/row['snapshot']).read_bytes()
        if sha(data)!=row['sha256']:raise RuntimeError('Before snapshot differs')
        old[row['path']]=data;current=(ROOT/row['path']).read_bytes()
        if row['path'] in ('docs/PACKET_CONNECTION_GOAL_20261006.md','artifacts/integration/packet-connections-20261006/packet-route-ledger.json'):continue
        if row['path'] not in SOURCES and row['path'] not in ('docs/PACKET_CONNECTION_GOAL_20261006.md','artifacts/integration/packet-connections-20261006/packet-route-ledger.json'):
            if data!=current:raise RuntimeError('Frozen context changed: '+row['path'])
            preserved.append(row)
        rel='after/'+row['snapshot'];save(rel,current);after.append(dict(path=row['path'],snapshot=rel,sha256=sha(current),bytes=len(current)))
        if data!=current:
            delta=''.join(difflib.unified_diff(data.decode('utf-8-sig').splitlines(True),current.decode('utf-8-sig').splitlines(True),fromfile='before/'+row['path'],tofile='after/'+row['path']))
            save('diff/'+Path(row['path']).name+'.diff',delta.encode('utf-8'))
    kept=[]
    checks={'src/cn/net/SharedCredentialConnection.cpp':[
        'bool SharedCredentialConnection::install_account_ingress(',
        'bool SharedCredentialConnection::confirm_account_success_queue(',
        'bool SharedCredentialConnection::account_success_current(',
        'bool SharedCredentialConnection::install_world_ingress(',
        'void SharedCredentialConnection::send_account_batch_with_publication(',
        'void SharedCredentialConnection::send_world_batch_with_publication(',
        'bool SharedCredentialConnection::owns_verified_login('],
        'src/cn/auth/SharedAccountVerifier.cpp':[
        'SharedAccountVerifier::SharedAccountVerifier(',
        'SharedAccountVerifier::~SharedAccountVerifier()']}
    for path,signatures in checks.items():
        current=(ROOT/path).read_bytes()
        for signature in signatures:
            a=body(old[path],signature.encode());b=body(current,signature.encode())
            if a!=b:raise RuntimeError('Preserved body differs: '+signature)
            kept.append(dict(path=path,signature=signature,sha256=sha(a),exact_bytes_retained=True))
    path='src/cn/auth/SharedWorldSelection.cpp';signature=b'std::shared_ptr<SharedWorldSelection::Connection> SharedWorldSelection::connection_for_choice('
    a=old[path][old[path].index(signature):];current=(ROOT/path).read_bytes();b=current[current.index(signature):]
    if a!=b:raise RuntimeError('World selection gameplay/CRUD tail changed')
    kept.append(dict(path=path,signature='all methods from connection_for_choice onward',sha256=sha(a),exact_bytes_retained=True))
    path='src/cn/auth/SharedAccountVerifier.cpp';start=b'void SharedAccountVerifier::verify_raw_ui(';end=b'                if(outcome==CredentialOutcome::Verified)done('
    a=old[path][old[path].index(start):old[path].index(end)];current=(ROOT/path).read_bytes();b=current[current.index(start):current.index(b'                if(outcome==CredentialOutcome::Verified) {\n                    // This is the exact snapshot')]
    if a!=b:raise RuntimeError('Original credential lookup/worker/final comparison prefix changed')
    kept.append(dict(path=path,signature='verify_raw_ui through original lookup/worker/repository recheck',sha256=sha(a),exact_bytes_retained=True))
    dump('preserved-source-bodies.json',kept)
    native=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe')
    if sha(native.read_bytes())!=PIN:raise RuntimeError('Pinned CN primary differs')
    previous=base/'cn-account-success-publication-source-01';data=(previous/'manifest.json').read_bytes();manifest=json.loads(data)
    if sha(data)!='3d41cf81ee9268913446e198d665c600c8701d53d664767a0d0f8e609ba4d3f4' or not manifest['sealed']:raise RuntimeError('Previous seal differs')
    save('retained-previous-round/manifest.json',data)
    rel='native/function-envelopes.json';data=(previous/rel).read_bytes();entry=next(r for r in manifest['files'] if r['path']==rel)
    if sha(data)!=entry['sha256']:raise RuntimeError('Retained account metadata differs')
    save('retained-previous-round/'+rel,data)
    peer=json.loads((out/'peer-handoff/source-receipt.json').read_text(encoding='utf-8'))
    for row in peer['saved_originals']:
        if sha((out/'peer-handoff'/row['snapshot']).read_bytes())!=row['sha256']:raise RuntimeError('Peer original differs')
    facts=dict(round=ROUND,cn_native_sha256_context=PIN,
        previous_goal_turn_classification='no progress: owner status response only; revalidated current source and took next CN credential continuity integration',
        cn_private_verifier_source_tokens_added=1,cn_existing_held_success_paths_strengthened=2,
        cn_credential_current_checks_are_monotonic_revisions=False,native_function_envelopes_newly_read=0,native_function_bytes_newly_read=0,
        prior_native_account_envelopes_retained=4,native_values_or_issuer_configured=False,
        new_packet_values=0,new_native_phase_source_bindings=0,new_source_owner_chains=0,new_tw_source_owner_chains=0,
        new_complete_bidirectional_routes=0,whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,
        formal_application_hosted=False,levels_changed=False,build_run=False,tests_run=False,runtime_run=False,database_access=False,deployed=False,
        credentials_or_password_hashes_logged_or_saved_to_receipts=False,preserved_contexts=preserved,remaining=REMAINING)
    dump('findings.json',facts)
    origins=[]
    for rel in SOURCES:
        data=(ROOT/rel).read_bytes();name=Path(rel).name;save('source/'+name,data);origins.append(dict(path=rel,snapshot=name,sha256=sha(data),bytes=len(data)))
    dump('source/source-origins.json',origins)
    path=base/'packet-route-ledger.json';ledger=json.loads(path.read_text(encoding='utf-8'))
    ledger['cn_credential_source_continuity']=dict(facts,evidence=out.relative_to(ROOT).as_posix())
    ledger['web_native_full_appearance_handoff']=dict(round='20261007-native-full-appearance',saved_originals=peer['saved_originals'],
        evidence=out.relative_to(ROOT).as_posix()+'/peer-handoff',originals_file_read=True,all_peer_manifest_files_individually_read=False,
        renderReady=False,releaseEligible=False,new_complete_gameplay_routes=0,server_native_acceptance=False,
        peer_reported_sealed_files=29780,peer_reported_capacity_bytes=42213693455,server_capacity_remeasured=False,
        new_ACK_sent=False,new_ACK_read_confirmed=False)
    ledger['dual_client_source_segments'].append(dict(name='Actual shared verifier snapshot -> exact suspended CN Account04/World00 -> held1D/catalog/0A or initial1F publication',
        version_scope='cn-account-world-source-only',status='Private real verifier source checked before publication; current equality is not monotonic revision; actual native issuer/providers and formal hosting open',
        source_paths=list(SOURCES),native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,tw_source_owner_chains_added=0,
        formal_application_hosted=False,complete_gameplay_routes_added=0,evidence=out.relative_to(ROOT).as_posix(),remaining=REMAINING))
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next_source_frontier']='Actual native seed/issued1D/billing0A/catalog/key/deadline/entitlement issuer; monotonic credential revision/revocation/cross-process authority remain open. Connect full shared07/1F/02/2A/6F/equipment/scene/ACT/observer and actual TW registry/PC/web/WSS hosting; all gameplay/numeric/denominator open; PHASE1 source-only.'
    path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/'docs/PACKET_CONNECTION_GOAL_20261006.md').open('a',encoding='utf-8') as f:f.write(
        '\n\n## CN verified credential source through login publication ('+ROUND+')\n\n'
        'Real shared verifier now privately issues a bounded original-row current token; same CN connection/original Login binds it weakly, and compose_native_login plus held account1D/catalog/0A and independently verified World001F publication observe same repository row before bytes leave. No obsolete source veto after release; no raw password in token/receipts; owned new encoded hash copies explicitly cleared. Current-value equality is not monotonic revision/ABA/external-write/cross-process authority. Existing TW auth/Application/repository/admission/native codecs retained; levels unchanged. New opcode/phase/owner/full0; no build/test/runtime/DB/deploy. Full-appearance peer three originals saved, renderReady/releaseEligiblefalse and full0; report checks not rerun. See research/cn-credential-source-continuity-20261007.md.\n')
    for row in rows:
        if row['path'] not in ('docs/PACKET_CONNECTION_GOAL_20261006.md','artifacts/integration/packet-connections-20261006/packet-route-ledger.json'):continue
        current=(ROOT/row['path']).read_bytes();rel='after/'+row['snapshot'];save(rel,current)
        after.append(dict(path=row['path'],snapshot=rel,sha256=sha(current),bytes=len(current)))
        delta=''.join(difflib.unified_diff(old[row['path']].decode('utf-8-sig').splitlines(True),current.decode('utf-8-sig').splitlines(True),fromfile='before/'+row['path'],tofile='after/'+row['path']))
        save('diff/'+Path(row['path']).name+'.diff',delta.encode('utf-8'))
    dump('after-manifest.json',after)
    print(json.dumps({k:facts[k] for k in ('round','cn_private_verifier_source_tokens_added','cn_existing_held_success_paths_strengthened','new_complete_bidirectional_routes')}))
if __name__=='__main__':main()
