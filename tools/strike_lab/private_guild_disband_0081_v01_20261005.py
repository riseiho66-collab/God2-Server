"""CUSTOM-0081 static scaffold: full native79/72 regression then native75.

Run only after root seals a new candidate/source/helper contract. Imports the
immutable native72 helper in an isolated namespace; only this NEW wrapper's
worker AST receives an additive nested phase. No changes to the old helper.
Hidden native WM input / VM_READ only; existing formal preservation gates stay
intact. SQL observations are read-only; inherited fixture setup is private.
"""
import ast
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
DEPENDENCY=ROOT/'tools/strike_lab/private_guild_kick_0080_v02_20261005.py'
DEPENDENCY_SHA='129ffd3161d0690f0de3e20a74721e71a9b6eaf7154659e901f12f199fe4d1f6'
PHASE=ROOT/'artifacts/research/native-guild-management-0081/helper-static-v01/disband_phase.py'
PHASE_SHA='37dc25e12ea2ca9fa81eb9f9ce54c95fd00125604c3c30b5d11a26cee26102e1'
DISBAND_PROOF=ROOT/'artifacts/research/native-guild-management-0081/disband-plan-v01/report.json'
PROOF_SHA='09ee3082f567a8a7c24d3c3adae7b829451d409c3a97012d9949dbffdcb0799e'
CONTRACT=ROOT/'artifacts/research/native-guild-management-0081/disband-live-v01/contract.json'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def validate_retirement(before,after,guild_id,revision):
    """Full tuples preserve null/blob/provenance; foreign rows remain exact."""
    names=('owned_guilds','owned_guild_members','owned_guild_governance_0078','owned_guild_applications_0078')
    if set(before)!=set(names) or set(after)!=set(names):raise AssertionError('DISBAND_TABLE_SET_WRONG')
    target=[r for r in before['owned_guilds'] if r[0]==guild_id]
    if len(target)!=1 or type(revision) is not int or revision<=target[0][2]:raise AssertionError('DISBAND_IDENTITY_REVISION_WRONG')
    expected=[(r[0],r[1],revision,*r[3:]) if r[0]==guild_id else r for r in before['owned_guilds']]
    if after['owned_guilds']!=expected:raise AssertionError('DISBAND_RETAINED_OR_FOREIGN_GUILD_CHANGED')
    for table,guild_index in (('owned_guild_members',1),('owned_guild_governance_0078',0),('owned_guild_applications_0078',1)):
        if after[table]!=[r for r in before[table] if r[guild_index]!=guild_id]:raise AssertionError('DISBAND_TARGET_NOT_REMOVED_OR_FOREIGN_CHANGED_'+table)
    return True

def transformed_tree(source,phase_source):
    """Auditable AST edit: add phase/call, extend total runtime only."""
    tree=ast.parse(source);phase=ast.parse(phase_source)
    functions=[n for n in phase.body if isinstance(n,ast.FunctionDef)]
    if len(functions)!=1 or functions[0].name!='disband_exercise':raise AssertionError('ONE_BOUNDED_PHASE_REQUIRED')
    workers=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='worker']
    if len(workers)!=1:raise AssertionError('ONE_IMMUTABLE_WORKER_REQUIRED')
    worker=workers[0];tries=[n for n in worker.body if isinstance(n,ast.Try)]
    if len(tries)!=1:raise AssertionError('ONE_OUTER_WORKER_TRY_REQUIRED')
    outer=tries[0];worker.body.insert(worker.body.index(outer),functions[0])
    hits=[i for i,n in enumerate(outer.body) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call)
        and isinstance(n.value.func,ast.Name) and n.value.func.id=='kick_exercise']
    if len(hits)!=1:raise AssertionError('EXACT_KICK_ANCHOR_REQUIRED')
    at=hits[0]+2 # preserve the original immediately following kick require
    outer.body[at:at]=ast.parse("disband_exercise(guild)\nrequire(result.get('disband_actual_client_accepted') is True,'NATIVE_DISBAND_ACCEPTANCE_REQUIRED')").body
    owners=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='owner_case']
    if len(owners)!=1:raise AssertionError('ONE_OWNER_REQUIRED')
    hits960=hits940=0
    for n in ast.walk(owners[0]):
        if isinstance(n,ast.Constant) and n.value=='960':n.value='1500';hits960+=1
        elif isinstance(n,ast.keyword) and n.arg=='timeout' and isinstance(n.value,ast.Constant) and n.value.value==940:n.value.value=1480;hits940+=1
    if (hits960,hits940)!=(1,1):raise AssertionError('TOTAL_BOUND_ANCHOR_CHANGED')
    return ast.fix_missing_locations(tree)

def load_context():
    if sha(DEPENDENCY)!=DEPENDENCY_SHA:raise AssertionError('IMMUTABLE_KICK_DEPENDENCY_CHANGED')
    if sha(PHASE)!=PHASE_SHA:raise AssertionError('DISBAND_PHASE_CHANGED')
    tree=transformed_tree(DEPENDENCY.read_text('utf-8'),PHASE.read_text('utf-8'))
    context={'__name__':'_private_disband0081_inherited','__file__':str(Path(__file__).resolve())}
    exec(compile(tree,str(Path(__file__).resolve()),'exec'),context)
    context['CONTRACT']=CONTRACT;context['validate_retirement']=validate_retirement
    inherited_qualify=context['qualify'];require=context['require'];base=context['base']
    def qualify():
        inherited_qualify()
        require(sha(DEPENDENCY)==DEPENDENCY_SHA,'IMMUTABLE_KICK_DEPENDENCY_CHANGED')
        require(sha(DISBAND_PROOF)==PROOF_SHA,'DISBAND_PROOF_CHANGED')
        proof=json.loads(DISBAND_PROOF.read_text('utf-8'))
        require(proof['client']['sha256']==base.CLIENT_SHA and proof['original_mapped_image']['sha256']==base.MAPPED_SHA,'DISBAND_NATIVE_BUILD_CHANGED')
        mapped=context['pefile'].PE(str(base.LIVE)).get_memory_mapped_image()
        for pin in proof['actual_machine_spans']:
            lo=int(pin['start'],16)-0x400000;hi=int(pin['end_exclusive'],16)-0x400000
            require(pin['current_equal_original'] is True and 0<=lo<hi<=len(mapped) and hashlib.sha256(mapped[lo:hi]).hexdigest()==pin['sha256'],'DISBAND_NATIVE_CODE_PIN_CHANGED')
        return proof
    def contract_guard(args):
        contract=json.loads(args.contract.read_text('utf-8'))
        require(contract['design']=='CUSTOM-0081' and contract.get('feature_family')=='guild-disband0081','DISBAND_CONTRACT_REQUIRED')
        require(contract.get('formal_config') is True and contract.get('env_lab_false') is True,'FORMAL_CONTRACT_REQUIRED')
        require(contract['candidate_sha256']==base.sha(args.server_candidate),'QUALIFIED_CANDIDATE_REQUIRED')
        def resolve(value):
            path=Path(value);return (path if path.is_absolute() else ROOT/path).resolve()
        require(resolve(contract['candidate_path'])==args.server_candidate.resolve(),'EXACT_CANDIDATE_PATH_REQUIRED')
        require(resolve(contract['helper_path'])==Path(__file__).resolve() and contract['helper_sha256']==sha(Path(__file__)),'QUALIFIED_HELPER_REQUIRED')
        args.bootstrap_candidate=resolve(contract['bootstrap_schema49_candidate_path'])
        require(contract['bootstrap_schema49_candidate_sha256']==context['BOOTSTRAP49_SHA']==sha(args.bootstrap_candidate),'BOOTSTRAP49_EXACT_CANDIDATE_REQUIRED')
        actual={p:sha(ROOT/p) for p in contract['source_sha256']}
        require(actual==contract['source_sha256'],'CANDIDATE_SOURCE_CLOSURE_CHANGED')
        for path,pin in ((DEPENDENCY,DEPENDENCY_SHA),(DISBAND_PROOF,PROOF_SHA),(PHASE,PHASE_SHA),(Path(__file__),sha(Path(__file__)))):
            require(actual.get(path.relative_to(ROOT).as_posix())==pin,'DISBAND_DEPENDENCY_CLOSURE_REQUIRED_'+path.name)
        return contract,actual
    context['qualify']=qualify;context['contract_guard']=contract_guard
    return context

def main():return load_context()['main']()

if __name__=='__main__':raise SystemExit(main())
