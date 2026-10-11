"""Seal conditional CN account-success source and native spans, without execution."""
import hashlib
import json
from pathlib import Path
import pefile
from .archive_inputs import SERVER
from .cn_wrapper_route_frontier import CN,PIN

ROOT=SERVER/'artifacts/integration/packet-connections-20261006'
NAME='cn-account-success-owner-01'
ROUND='20261006-cn-account-success-owner'
SOURCES=[
    'src/cn/auth/SharedAccountSuccess.h','src/cn/auth/SharedAccountSuccess.cpp',
    'src/cn/auth/SharedAccountSelection.h','src/cn/auth/SharedAccountSelection.cpp',
    'src/cn/net/SharedCredentialConnection.h','src/cn/net/SharedCredentialConnection.cpp',
    'src/cn/protocol/CnAccountWire.h','docs/research/cn-account-success-owner-20261006.md',
]

def sha(raw):return hashlib.sha256(raw).hexdigest()
def dump(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def main():
    out=ROOT/NAME
    if out.exists():raise RuntimeError('Preserve previous immutable delivery')
    exe=CN.parent/'XJZ-CN/God2_opt.exe';raw=exe.read_bytes()
    if sha(raw)!=PIN:raise ValueError('Native pin changed')
    pe=pefile.PE(data=raw,fast_load=True)
    old=ROOT/'cn-admission-contract-agent-01'
    native=json.loads((old/'native-manifest.json').read_text(encoding='utf8'))
    if native['sha256']!=PIN:raise ValueError('Original evidence build differs')
    spans=[]
    for address,size in [('0047fe30',2009),('0047f310',250)]:
        previous=next(row for row in native['functions'] if row['va']==address)
        code=pe.get_data(int(address,16)-pe.OPTIONAL_HEADER.ImageBase,size)
        if len(code)!=size or sha(code)!=previous['code_sha256']:
            raise ValueError('Native span differs from original evidence')
        source=(old/(address+'.c')).read_bytes()
        if sha(source)!=previous['source_sha256']:raise ValueError('Native C differs')
        spans.append({'address':address,'bytes':size,'native_sha256':sha(code),'source_sha256':sha(source),
            'raw':code,'source':source})
    ledger_path=ROOT/'packet-route-ledger.json';prior=ledger_path.read_bytes();ledger=json.loads(prior.decode('utf8'))
    out.mkdir();snapshots=[]
    def save(rel,data,original):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        snapshots.append({'path':rel,'bytes':len(data),'sha256':sha(data),'original':str(original)})
    for rel in SOURCES:save(rel,(SERVER/rel).read_bytes(),SERVER/rel)
    for row in spans:
        address=row['address'];save('native/'+address+'.bin',row.pop('raw'),exe)
        save('native/'+address+'.c',row.pop('source'),old/(address+'.c'))
        save('native/'+address+'.asm',(old/(address+'.asm')).read_bytes(),old/(address+'.asm'))
    for directory,files in [
        (old,['native-manifest.json','findings.json']),
        (ROOT/'cn-billing-byte5-agent-01',['findings.json']),
    ]:
        for rel in files:save('prior-evidence/'+directory.name+'/'+rel,(directory/rel).read_bytes(),directory/rel)
    save('prior-ledger.json',prior,ledger_path)
    for rel in ['AGENTS.md','docs/PACKET_CONNECTION_GOAL_20261006.md']:
        save('directives/'+Path(rel).name,(SERVER/rel).read_bytes(),SERVER/rel)
    save('delivery-tool.py',Path(__file__).read_bytes(),__file__)
    gaps=[
        'Complete native1D/0A data suppliers/issuer remain required: flags, billingbyte5 and opaque tails must not be filled from incoming04 or fabricated defaults.',
        'Exact byte echo is the bounded supplier form; native_stricmp case-changing forms and longer/nonterminated disconnect names remain open.',
        'Actual Application listeners/Verified success composition, credential revision on delayed issuance and cross-process key/revocation authority remain open.',
        'Common character07/fullworld1F/02/2A suppliers and authenticated row/alias/grant lineage remain incomplete.',
        'Actual shared scene/actor/placement, TW registry enrollment, bootstrap/control/publication and later gameplay remain incomplete.',
        'All TW/CN directional/state/variant/deferred and whole-game denominator remain open; no route completion or native acceptance claimed.',
    ]
    manifest={
        'kind':'verified connection snapshot -> native issued data -> common grant -> account selection and ordered native success output',
        'client_sha256':PIN,'source_paths':SOURCES,'snapshots':snapshots,'native_spans':spans,
        'source_owner_chains_added':1,'new_source_files':2,'new_phase_opcode_bindings':7,
        'unique_new_phase_opcode_binding_values':3,
        'bounded_forms':['exact-byte issuer echo','NUL-terminated exact connection-name C2S0A'],
        'native_success_output':['1D','ordered04/05/06','0A'],
        'output_order_origin':'integration order supported by receiver, not asserted official emission order',
        'authority':'verified original sharedLogin pointer; independent shared account ID; issued key; explicit deadline; enabled actual catalog destinations',
        'cleanup':'failed issued grant revoked; disconnect affects its own account session only, preserves selected/world handoff',
        'native_values_supplied':False,'formal_application_hosted':False,'new_complete_routes':0,
        'previous_goal_turn_classification':'progress: initial-ready source/shared stored-position lease and266 pinned evidence files sealed',
        'remaining':gaps,'whole_game_route_total':None,'whole_game_completion_percent':None,
        'build_run':False,'tests_run':False,'runtime_run':False,'deployed':False,
        'production_database_read_or_modified':False,'client_modified':False,'font_modified':False,'text_conversion_modified':False,
    }
    dump(out/'integration-manifest.json',manifest)
    ledger['dual_client_source_segments'].append({
        'name':'CN complete native success data to verified shared grant/A6 and connection-owned0A disconnect',
        'status':'完整資料前提下的1D／目錄／0A→共用grant與A6來源已接；本連線0A斷線已接；原生供應器與Application未掛載',
        'native_c2s_by_phase':{'account':['04','0A']},
        'native_s2c_by_phase':{'account':['1D','04','05','06','0A']},
        'source_paths':SOURCES,'source_owner_chains_added':1,'formal_application_hosted':False,
        'complete_gameplay_routes_added':0,'storage_writes':False,
        'shared_storage':['shared verified accounts ID','SharedWorldAdmission issued grant','RecoveredCharacterRepository / recovered_characters'],
        'native_form_qualifications':{'exact_byte_issuer_echo':True,'connection_owned_nul_disconnect':True,'whole_opcode_variants_complete':False},
        'evidence':out.relative_to(SERVER).as_posix(),'remaining':gaps,
    })
    ledger['cn_account_admission_evidence'][NAME]={
        'root':out.relative_to(SERVER).as_posix(),
        'artifact_sha256':{p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()},
    }
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next']=[
        'Recover actual native1D/0A issuer fields and full07/world1F/02/2A providers; retain exact byte source binding and issuer/data/alias lineage.',
        'Connect actual Application account/world listeners and Verified success controller to the existing common ownership/credential source; do not use empty/fake success providers.',
        'Complete common actor allocator/native first placement/TW enrollment/bootstrap/control/world publication and later scene-ready/gameplay dispatcher.',
        'Continue all TW/CN phase/state/variants/deferred/world/gameplay and shared content; conversion/native fonts/saves preserved; no phase1 build/tests/runtime/deploy.',
    ]
    dump(ledger_path,ledger)
    print(json.dumps({'artifact':str(out),'snapshots':len(snapshots),'new_source_files':2,
        'new_phase_bindings':7,'new_complete_routes':0,'tests_run':False}))

if __name__=='__main__':main()
