"""File-only full native login records, transferred billing and UI flag receipts."""
import csv,difflib,hashlib,json
from pathlib import Path
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from .cn_pe_import_directory import FileView
from .cn_wrapper_route_frontier import ROOT,PIN
from tools.strike_lab.omega_assets import decode_csvz
NAME='cn-login-record-source-observation-01'
ROUND='20261007-cn-login-record-source-observation'
SOURCES=('src/cn/auth/SharedAccountSuccess.h','src/cn/auth/SharedAccountSuccess.cpp',
    'src/cn/protocol/CnAccountBilling.h','src/cn/protocol/CnIssuedLoginFlags.h',
    'tools/reconstruction/cn_login_record_source_observation_delivery.py',
    'docs/research/cn-login-record-source-observation-20261007.md')
FUNCTIONS=('0047fe30','00443fa0','00445040','0044aab0','00449440','0043e7e0',
    '0043e260','00446bd0','00422ba0','00422c20','00422c80')
REMAINING=[
    'Literal record observation is not an actual native issuer: full1D/0A/opaque5/A9..CB/seed/key/deadline/entitlement/catalog source remains unconfigured.',
    'Monotonic credential revisions, ABA/external-write/cross-process authority/revocation; full07/world1F/02/2A/6F/equipment/scene/ACT/observer suppliers, TW shared registry and formal PC/web/WSS hosting remain open.',
    'Full directional/state/variant/indirect/deferred denominator and all gameplay/numeric/items/trade/quests/battle/skills/monsters/pets/guilds/recovery remain open; levels unchanged and comprehensive tests follow full source connection.',
]
def sha(data):return hashlib.sha256(data).hexdigest()
def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():raise RuntimeError('Fresh receipt required')
    def save(rel,data):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(data)
    def dump(rel,v):save(rel,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    before=json.loads((out/'before-manifest.json').read_text(encoding='utf-8'));old={};after=[];preserved=[]
    bookkeeping=('docs/PACKET_CONNECTION_GOAL_20261006.md','artifacts/integration/packet-connections-20261006/packet-route-ledger.json')
    for row in before:
        data=(out/row['snapshot']).read_bytes()
        if sha(data)!=row['sha256']:raise RuntimeError('Before snapshot differs')
        old[row['path']]=data;current=(ROOT/row['path']).read_bytes()
        if row['path'] in bookkeeping:continue
        if row['path'] not in SOURCES:
            if data!=current:raise RuntimeError('Frozen context changed: '+row['path'])
            preserved.append(row)
        rel='after/'+row['snapshot'];save(rel,current);after.append(dict(path=row['path'],snapshot=rel,sha256=sha(current),bytes=len(current)))
        if data!=current:save('diff/'+Path(row['path']).name+'.diff',''.join(difflib.unified_diff(data.decode('utf-8-sig').splitlines(True),current.decode('utf-8-sig').splitlines(True),fromfile='before/'+row['path'],tofile='after/'+row['path'])).encode('utf-8'))
    transferred=json.loads((out/'transferred-source/source-origin.json').read_text(encoding='utf-8'));data=(out/'transferred-source/CnAccountBilling.h').read_bytes()
    if sha(data)!=transferred['sha256'] or data!=(ROOT/'src/cn/protocol/CnAccountBilling.h').read_bytes():raise RuntimeError('Transferred billing header differs')
    previous=base/'cn-credential-source-continuity-01';data=(previous/'manifest.json').read_bytes()
    if sha(data)!='ddc5c390e74df931d23b9f055749d0a3cc0ec9c2331afd87b2f1bb66e298a0f3' or not json.loads(data)['sealed']:raise RuntimeError('Previous seal differs')
    save('retained-previous-round/manifest.json',data)
    prior=base/'cn-account-success-publication-source-01';meta=json.loads((prior/'native/function-envelopes.json').read_text(encoding='utf-8'));prior_ranges={r['address']:r for r in meta['ranges']}
    save('retained-native/native-account-envelopes.json',(prior/'native/function-envelopes.json').read_bytes())
    rel='cn-import-20261006-v1/evidence/docs/NATIVE_ACCOUNT_PHASE.md';save('retained-native/NATIVE_ACCOUNT_PHASE.md',(base/rel).read_bytes())
    native=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe');raw=native.read_bytes()
    if sha(raw)!=PIN:raise RuntimeError('Pinned CN primary differs')
    pe=pefile.PE(data=raw,fast_load=True);view=FileView(pe,raw);md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True
    recovery=Path('C:/Users/risei/Desktop/God2-xjz/God2_opt_source_recovery_20260926_055734/decompiled');metadata=(recovery/'functions.tsv').read_bytes();rows={r['address']:r for r in csv.DictReader(metadata.decode('utf-8').splitlines(),delimiter='\t')}
    ranges=[];flag_operands=[];edges=[]
    for address in FUNCTIONS:
        row=rows[address];path=(recovery/row['file']).resolve()
        if not path.is_relative_to(recovery.resolve()):raise RuntimeError('Recovery outside root')
        code=view.read(int(address,16)-pe.OPTIONAL_HEADER.ImageBase,int(row['bytes']));source=path.read_bytes();instructions=list(md.disasm(code,int(address,16)))
        listing=('\n'.join(f'{i.address:08x} {i.bytes.hex():24} {i.mnemonic:8} {i.op_str}' for i in instructions)+'\n').encode('utf-8')
        for extension,data in (('.bin',code),('.asm',listing),('.c',source)):save('native/'+address+extension,data)
        prior_range=prior_ranges.get(address)
        if prior_range and (prior_range['bytes']!=len(code) or prior_range['native_sha256']!=sha(code)):raise RuntimeError('Prior native envelope differs')
        ranges.append(dict(address=address,bytes=len(code),native_sha256=sha(code),metadata=row,recovery_source=str(path),recovery_source_sha256=sha(source),decoded_instruction_bytes=sum(i.size for i in instructions),prior_envelope_identical=bool(prior_range),native_executed=False,all_exceptional_or_indirect_paths_closed=False))
        for i in instructions:
            if any(op.type==3 and op.mem.disp in (0x17aabe,0x40ec,0x2d6d) for op in i.operands):flag_operands.append(dict(function=address,address=f'{i.address:08x}',bytes=i.bytes.hex(),mnemonic=i.mnemonic,operand=i.op_str,owner_requires_separate_dataflow=True))
            if i.mnemonic=='call' and i.operands and i.operands[0].type==2 and f'{i.operands[0].imm:08x}' in FUNCTIONS:edges.append(dict(caller=address,site=f'{i.address:08x}',target=f'{i.operands[0].imm:08x}',bytes=i.bytes.hex(),entry_reachable_or_all_paths_qualified=False))
    pe.close();dump('native/function-envelopes.json',dict(primary=str(native),sha256=PIN,metadata_sha256=sha(metadata),ranges=ranges));dump('native/flag-direct-operands.json',flag_operands);dump('native/scoped-direct-call-references.json',edges)
    resource=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/Data2/Client.csvZ');encoded=resource.read_bytes();decoded=decode_csvz(encoded);save('resources/Client.csvZ',encoded);save('resources/Client.decoded.csv',decoded)
    try:decoded.decode('cp936');error=None
    except UnicodeDecodeError as e:error=dict(encoding='cp936',start=e.start,end=e.end,reason=e.reason,substitution_performed=False)
    versions=[dict(line=n+1,raw_hex=line.hex(),ascii_value=int(line.split(b',')[1])) for n,line in enumerate(decoded.splitlines()) if line.startswith(b'ClientVersion,')]
    dump('resources/source-observation.json',dict(original=str(resource),encoded_bytes=len(encoded),encoded_sha256=sha(encoded),decoded_bytes=len(decoded),decoded_sha256=sha(decoded),ASCII_client_version_rows=versions,strict_cp936_error=error,native_loader_executed=False,live_current_resource_mode_proven=False))
    facts=dict(round=ROUND,cn_native_sha256_context=PIN,previous_goal_turn_classification='progress: real verifier snapshot token bound to two existing held CN success paths; catalog108/75-file immutable seal',
        cn_transferred_billing_views_added=1,cn_issued_login_flag_views_added=1,cn_existing_literal_record_source_observations_strengthened=1,cn_scoped_provider_flag_UI_lineages_saved=1,
        native_function_envelopes_read=len(ranges),native_function_bytes_read=sum(r['bytes'] for r in ranges),prior_native_envelopes_identically_retained=sum(r['prior_envelope_identical'] for r in ranges),
        recovered_old_billing_semantics_claimed_new=False,source_issuer_or_native_values_configured=False,live_credential_records_saved_to_receipts=False,
        new_packet_values=0,new_native_phase_source_bindings=0,new_source_owner_chains=0,new_tw_source_owner_chains=0,new_complete_bidirectional_routes=0,
        whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,formal_application_hosted=False,levels_changed=False,
        build_run=False,tests_run=False,runtime_run=False,database_access=False,deployed=False,preserved_contexts=preserved,remaining=REMAINING)
    dump('findings.json',facts)
    origins=[]
    for rel in SOURCES:
        data=(ROOT/rel).read_bytes();name=Path(rel).name;save('source/'+name,data);origins.append(dict(path=rel,snapshot=name,sha256=sha(data),bytes=len(data)))
    dump('source/source-origins.json',origins)
    path=base/'packet-route-ledger.json';ledger=json.loads(path.read_text(encoding='utf-8'));ledger['cn_login_record_source_observation']=dict(facts,evidence=out.relative_to(ROOT).as_posix())
    ledger['dual_client_source_segments'].append(dict(name='Complete native issued1D/billing0A -> bounded transferred billing/flag observation -> actual issuer current behind held success publication',version_scope='cn-account-source-only',status='Exact raw issued records now available at all issuer checks; no new issuer/default/native values or formal hosting',source_paths=list(SOURCES),native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,evidence=out.relative_to(ROOT).as_posix(),remaining=REMAINING))
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND;plan['next_source_frontier']='Configure qualified complete native1D/0A/seed/key/deadline/catalog/entitlement issuer; literal-record checks do not fill source or opaque5/A9..CB. Trace remaining login aliases and full shared07/world1F/02/2A/6F/equipment/scene/ACT/observer, TW registry and formal PC/web/WSS hosting. Credential monotonic revisions/ABA/external-writes/cross-process/revocation, all gameplay/numeric/denominator remain open; PHASE1 source-only.'
    path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/'docs/PACKET_CONNECTION_GOAL_20261006.md').open('a',encoding='utf-8') as f:f.write('\n\n## CN complete native login record source observation ('+ROUND+')\n\nTransferred original CnAccountBilling header byte-identically; readonly1D A8 view and scoped window040A/network40EC/UI17AABE lineage retained. Actual NativeData issuer Current now sees full literal1D/0A plus typed original billing/flags at Prepared/BeforeIssue/BeforePublish; bounded original native data retained/wiped through existing held IO publication, no guessed native issuer/defaults or post-release veto. Current Data2 Client.csvZ ASCII ClientVersion2 observed file-only, complete strictCP936 comment decode failure retained without substitution; no live profile proof. Opcode/phase/owner/full0; all formal providers/hosting/gameplay/denominator remain open; levels unchanged; no build/test/runtime/DB/deploy. See research/cn-login-record-source-observation-20261007.md.\n')
    for row in before:
        if row['path'] not in bookkeeping:continue
        current=(ROOT/row['path']).read_bytes();rel='after/'+row['snapshot'];save(rel,current);after.append(dict(path=row['path'],snapshot=rel,sha256=sha(current),bytes=len(current)))
        save('diff/'+Path(row['path']).name+'.diff',''.join(difflib.unified_diff(old[row['path']].decode('utf-8-sig').splitlines(True),current.decode('utf-8-sig').splitlines(True),fromfile='before/'+row['path'],tofile='after/'+row['path'])).encode('utf-8'))
    dump('after-manifest.json',after)
    print(json.dumps({k:facts[k] for k in ('round','native_function_envelopes_read','native_function_bytes_read','cn_existing_literal_record_source_observations_strengthened','new_complete_bidirectional_routes')}))
if __name__=='__main__':main()
