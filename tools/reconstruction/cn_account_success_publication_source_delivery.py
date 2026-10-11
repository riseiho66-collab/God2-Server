"""File-only CN issuer scope and held account publication source receipts."""
import csv,hashlib,json
from pathlib import Path
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from .cn_pe_import_directory import FileView
from .cn_wrapper_route_frontier import ROOT,PIN
NAME='cn-account-success-publication-source-01'
ROUND='20261007-cn-account-success-publication-source'
SOURCES=('src/cn/auth/SharedAccountSuccess.h','src/cn/auth/SharedAccountSuccess.cpp',
    'src/cn/net/SharedCredentialConnection.h','src/cn/net/SharedCredentialConnection.cpp',
    'tools/reconstruction/cn_account_success_publication_source_delivery.py',
    'docs/research/cn-account-success-publication-source-20261007.md')
FUNCTIONS=('0047fe30','0047f310','00443fa0','0047c830')
REMAINING=[
    'Actual configured native seed/1D/0A/billing/entitlement/catalog/deadline/key issuer/current policy, delayed credential revision and cross-process authority remain open; no guessed source is installed.',
    'Complete native07/1F/02/2A/full6F/equipment/scene/ACT/observer sources, real TW shared registry enrollment and CN/native PC/web Application/WSS hosting remain open.',
    'All directional/state/variant/indirect/deferred denominator and numeric/items/trade/quests/battle/skills/monsters/pets/guilds/gameplay/recovery remain open; levels unchanged, comprehensive tests follow full source connection.',
]
def sha(data):return hashlib.sha256(data).hexdigest()
def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():raise RuntimeError('Fresh source receipt required')
    def save(rel,data):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(data)
    def dump(rel,value):save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    before=json.loads((out/'before-manifest.json').read_text(encoding='utf-8'));old={};preserved=[]
    for row in before:
        data=(out/row['snapshot']).read_bytes()
        if sha(data)!=row['sha256']:raise RuntimeError('Original source receipt differs')
        old[row['path']]=data
        if row['path'] not in SOURCES and row['path'] not in ('docs/PACKET_CONNECTION_GOAL_20261006.md',
            'artifacts/integration/packet-connections-20261006/packet-route-ledger.json'):
            if data!=(ROOT/row['path']).read_bytes():raise RuntimeError('Frozen context changed: '+row['path'])
            preserved.append(row)
    def body(data,signature):
        start=data.index(signature);at=data.index(b'{',start);depth=1;end=at+1
        while depth:depth+=(data[end]==123)-(data[end]==125);end+=1
        return data[start:end]
    preserved_bodies=[];path='src/cn/net/SharedCredentialConnection.cpp'
    for signature in (b'bool SharedCredentialConnection::install_account_ingress(',
        b'bool SharedCredentialConnection::confirm_account_success_queue(',b'bool SharedCredentialConnection::install_world_ingress(',
        b'void SharedCredentialConnection::send_account_batch_with_publication(',b'bool SharedCredentialConnection::owns_verified_login('):
        a=body(old[path],signature);b=body((ROOT/path).read_bytes(),signature)
        if a!=b:raise RuntimeError('Existing connection body changed: '+signature.decode())
        preserved_bodies.append({'path':path,'signature':signature.decode(),'sha256':sha(a),'exact_bytes_retained':True})
    dump('preserved-connection-bodies.json',preserved_bodies)
    native=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe');raw=native.read_bytes()
    if sha(raw)!=PIN:raise RuntimeError('CN primary differs')
    pe=pefile.PE(data=raw,fast_load=True);view=FileView(pe,raw);md=Cs(CS_ARCH_X86,CS_MODE_32)
    recovery=Path('C:/Users/risei/Desktop/God2-xjz/God2_opt_source_recovery_20260926_055734/decompiled')
    metadata=(recovery/'functions.tsv').read_bytes();rows={r['address']:r for r in csv.DictReader(metadata.decode('utf-8').splitlines(),delimiter='\t')}
    previous=base/'cn-account-success-owner-01';prior_manifest=json.loads((previous/'integration-manifest.json').read_text(encoding='utf-8'))
    prior_spans={r['address']:r for r in prior_manifest['native_spans']};ranges=[]
    save('retained-prior-account-source/integration-manifest.json',(previous/'integration-manifest.json').read_bytes())
    for address in FUNCTIONS:
        row=rows[address];path=(recovery/row['file']).resolve();size=int(row['bytes'])
        if not path.is_relative_to(recovery.resolve()):raise RuntimeError('Recovery outside root')
        code=view.read(int(address,16)-pe.OPTIONAL_HEADER.ImageBase,size);source=path.read_bytes();instructions=list(md.disasm(code,int(address,16)))
        listing=('\n'.join(f'{i.address:08x} {i.bytes.hex():24} {i.mnemonic:8} {i.op_str}' for i in instructions)+'\n').encode()
        for extension,data in (('.bin',code),('.asm',listing),('.c',source)):save('native/'+address+extension,data)
        old_span=prior_spans.get(address)
        if old_span and (old_span['bytes']!=size or old_span['native_sha256']!=sha(code)):raise RuntimeError('Prior native span differs')
        ranges.append({'address':address,'bytes':size,'native_sha256':sha(code),'metadata':row,
            'recovery_source':str(path),'recovery_source_sha256':sha(source),'decoded_instruction_bytes':sum(i.size for i in instructions),
            'prior_account_native_envelope_identical':bool(old_span),'native_executed':False,'all_exceptional_or_indirect_paths_closed':False})
    pe.close();dump('native/function-envelopes.json',{'primary':str(native),'sha256':PIN,'metadata_sha256':sha(metadata),'ranges':ranges})
    previous_round=base/'cn-appearance-cache-owner-source-01';data=(previous_round/'manifest.json').read_bytes()
    if sha(data)!='5f86856c57f2e774b1df3f1f2bf56978401fb257c3e56769644f0b0c64c8f70a' or not json.loads(data)['sealed']:raise RuntimeError('Previous round seal differs')
    save('retained-previous-round/manifest.json',data)
    peer=base/'cn-cache-owner-source-peer-handoff-01';data=(peer/'manifest.json').read_bytes();manifest=json.loads(data)
    if not manifest['sealed']:raise RuntimeError('Peer read receipt unsealed')
    save('retained-peer-read/manifest.json',data)
    for row in manifest['files']:
        data=(peer/row['path']).read_bytes()
        if sha(data)!=row['sha256']:raise RuntimeError('Peer read receipt differs')
        save('retained-peer-read/'+row['path'],data)
    facts={'round':ROUND,'cn_native_sha256_context':PIN,
        'previous_goal_turn_classification':'progress: actual native cache owner init/current bank source binding, catalog106/141-file seal and separate prior peer ACK read receipt saved',
        'cn_actual_native_account_success_scopes_added':1,'cn_existing_account_success_held_publication_bindings_strengthened':1,
        'cn_read_only_published_account_grant_checks_added':1,'native_function_envelopes_read':len(ranges),
        'native_function_bytes_read':sum(r['bytes'] for r in ranges),'native_values_or_issuer_configured':False,
        'credentials_or_native_account_records_saved_to_receipts':False,'new_packet_values':0,'new_native_phase_source_bindings':0,
        'new_source_owner_chains':0,'new_tw_source_owner_chains':0,'new_complete_bidirectional_routes':0,
        'whole_game_route_total':None,'whole_game_completed_routes':None,'whole_game_completion_percent':None,
        'formal_application_hosted':False,'levels_changed':False,'build_run':False,'tests_run':False,'runtime_run':False,
        'database_access':False,'deployed':False,'preserved_contexts':preserved,'remaining':REMAINING}
    dump('findings.json',facts)
    for rel in SOURCES:save('source/'+Path(rel).name,(ROOT/rel).read_bytes())
    dump('source/source-origins.json',[{'path':rel,'snapshot':Path(rel).name,'sha256':sha((ROOT/rel).read_bytes())} for rel in SOURCES])
    path=base/'packet-route-ledger.json';ledger=json.loads(path.read_text(encoding='utf-8'))
    ledger['cn_account_success_publication_source']=dict(facts,evidence=out.relative_to(ROOT).as_posix())
    ledger['web_native_cn_world_appearance_handoff']['new_ACK_read_confirmed']=True
    ledger['web_native_cn_world_appearance_handoff']['ACK_read_confirmation_evidence']=peer.relative_to(ROOT).as_posix()+'/server-ACK-read-confirmation.json'
    ledger['cn_appearance_bank_source_binding']['peer_read_confirmed']=True
    ledger['cn_appearance_bank_source_binding']['peer_read_confirmation_evidence']=peer.relative_to(ROOT).as_posix()+'/native-full-appearance-peer-read.json'
    ledger['dual_client_source_segments'].append({'name':'CN actual native account issuer scope ->held complete1D/catalog/0A publication ->exact current shared grant/read release',
        'version_scope':'cn-account-verified-success-source-only','status':'Actual issuer/current scope required before grant issue and behind held IO barrier; original complete success order retained; native issuer and formal providers/hosting remain unconfigured',
        'source_paths':list(SOURCES),'native_c2s_by_phase':{},'native_s2c_by_phase':{},'source_owner_chains_added':0,
        'tw_source_owner_chains_added':0,'formal_application_hosted':False,'complete_gameplay_routes_added':0,
        'evidence':out.relative_to(ROOT).as_posix(),'remaining':REMAINING})
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next_source_frontier']='Recover and connect actual native seed/issued1D/billing0A/catalog/key/deadline/current source policy and delayed credential revision; shared07/1F/02/2A/full6F/equipment/scene/ACT/observer suppliers, actual TW registry enrollment and formal PC/web Application hosting remain open. All gameplay/numeric/denominator, levels unchanged; PHASE1 source-only.'
    path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/'docs/PACKET_CONNECTION_GOAL_20261006.md').open('a',encoding='utf-8') as f:f.write(
        '\n\n## CN account native issuer scope/held success publication ('+ROUND+')\n\n'
        'Existing verified account→compose_native_login→SharedAccountSuccess now requires actual native issuer scope/current at prepared/beforeissue/beforepublish. Complete1D/ordered original catalog/0A stays behind existing IO encode/capacity publication barrier until exact connection/login/grant confirmation; after local release only current published grant checked, not obsolete issuer predicates. Bounded original request retains wiping deleter, no credential logging/saving. Scope1/existing success publication strengthened1/read-only grant observation1; real seed/1D/0A/entitlement/key/catalog/deadline/provider/host and full gameplay/denominator remain missing. TW auth/codec/selection/admission/core source bodies retained; levels unchanged; opcode/phase/owner/full0, no build/test/runtime/DB/deploy. See research/cn-account-success-publication-source-20261007.md.\n')
    print(json.dumps({k:facts[k] for k in ('round','native_function_envelopes_read','native_function_bytes_read','cn_existing_account_success_held_publication_bindings_strengthened','new_complete_bidirectional_routes')}))
if __name__=='__main__':main()
