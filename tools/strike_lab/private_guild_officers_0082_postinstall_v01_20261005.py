"""NEW bounded native0082 runner draft: inherited full79, officer82, full72, full75.

Import/static inspection does not start processes. Root must promote byte-exact
to a NEW tools helper, seal the strict contract, then authorize its normal owner
runner. All actual observations remain null until that future native run.
"""
import ast
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

# Deliberately independent of artifact/tools depth; always the formal workspace.
ROOT = Path('C:/Users/risei/Desktop/God2/God2-Server').resolve()
BASE = ROOT / 'artifacts/research/native-guild-officers-0082'
PLAN = BASE / 'native-helper-plan-v01'
PLAN_SEAL_SHA = '5fe588c5f1de36721366a41c31d35612e01c42796b7e66c78742475305cbc4c5'
LEGACY = ROOT / 'tools/strike_lab/private_guild_disband_0081_v02_20261005.py'
LEGACY_SHA = '78ad91b6abde621ac81080b2ec891fa1c77f37cd8d76e42df79fcf3a54c8711f'
KICK = ROOT / 'tools/strike_lab/private_guild_kick_0080_v02_20261005.py'
KICK_SHA = '129ffd3161d0690f0de3e20a74721e71a9b6eaf7154659e901f12f199fe4d1f6'
DISBAND_PHASE = ROOT / 'artifacts/research/native-guild-management-0081/helper-static-v02/disband_phase.py'
DISBAND_PHASE_SHA = '7082260525db3a1775ec5be37b035992c2d04fe67db9443860907e68aa746180'
DISBAND_PROOF = ROOT / 'artifacts/research/native-guild-management-0081/disband-plan-v01/report.json'
DISBAND_PROOF_SHA = '09ee3082f567a8a7c24d3c3adae7b829451d409c3a97012d9949dbffdcb0799e'
OFFICER_PROOF = BASE / 'plan-v01/native-evidence.json'
OFFICER_PROOF_SHA = '25af2e8ea2594da5e3908f9abc4a0b956568b07f623918496a638712ec7b2413'
CANDIDATE = BASE / 'application-candidate-v03/build/Release/god2-server.exe'
CANDIDATE_SHA = '1062075f3d2063650a28adc4c9053ac5a68c646dbbb4ea0229af28bfdb8251c9'
COMPILED = BASE / 'application-candidate-v03/compiled-candidate-v03.json'
COMPILED_SHA = 'c70cad0a81b75b66be0edbce678af86acc1372338c4984d7808b7f166d77a508'
PRIVATE_ROOT = BASE / 'application-candidate-v03/shadow'
APPLICATION_SHA = 'b20b3c3c56186521bf602f601d4c4f157f83f9a5521f7b7faa8fdaddb660980e'
BOOTSTRAP49_SHA = '76d9e815628b1736dd013915fb1d42d2cb0e5d5eb49c028d745ac657355b6fa6'
CONTRACT = BASE / 'officer-live-v02/contract.json'
TCP_QUALIFICATION = BASE / 'application-candidate-v03/tcp-qualified-v03.json'
TCP_SHA = '0e6f22270d948e8126e07ef142181d7afb59e082d4ed2a45acebe2e818c37089'
STRICT_QUALIFICATION = BASE / 'schema51strict-extension-v02/report.json'
STRICT_SHA = '8b1a4600c93c6c20355125c71f859b5ab822339b05335a881db62143ed8a90b4'
STRICT_SEAL = BASE / 'schema51strict-extension-v02/sealed-result.json'
STRICT_SEAL_SHA = '91176236b0362f33013b53e815f3edf0a556befedc4b8421104e4386c55bd683'
BINDINGS_READY = True
BUILD_ADAPTER = Path('C:\\Users\\risei\\Desktop\\God2\\God2-Server\\artifacts\\research\\native-guild-officers-0082\\native-runner-v02-preparation-v01\\qualified-v01\\build_adapter.py').resolve()
BUILD_ADAPTER_SHA = '058e9f6957f17a0b3226cfca828e2f4257fdbee62e692ff981a2d0acd9e2203f'
STRICT_ADAPTER = Path('C:\\Users\\risei\\Desktop\\God2\\God2-Server\\artifacts\\research\\native-guild-officers-0082\\native-runner-v02-preparation-v01\\qualified-v01\\strict_adapter.py').resolve()
STRICT_ADAPTER_SHA = 'e6d4855682bb1e942c6fdc2979d9206fa33ecb8d141efa79b7d8585e89888970'
STRICT_SOURCE_SHA = '27105bf01cae9f4f7058ba3dc3863b062aa6d77d48857b9328203e6e74d769b3'
STRICT_EXPECTED_CASES = 16
REFERENCE_PINS = {'artifacts/research/native-guild-officers-0082/application-candidate-v02/preparation.json': 'fb10f972ec2765a7524d44a6fcf66942e26443819f2474eb541779d5727bdfe4', 'artifacts/research/native-guild-officers-0082/application-candidate-v02/shadow/src/db/GuildOfficerSqliteMigrations.cpp': '0650729f467cab6de65ae82f452249592d5a384742671fbc9a1754c31c5f9c43', 'artifacts/research/native-guild-management-0081/post-install-v01/contract.json': 'f4c17a5d1e0919b2899462d744753cf1c1919906a9e496fac3dbb151be8bc95b', 'artifacts/research/native-guild-management-0081/implementation-final-v01/report.json': 'cf68b1accb9650aed487b1e690b8c796a16063a83a69985d1f5c7c6fcfeefd1a', 'artifacts/research/native-guild-officers-0082/officer-live-v01/contract.json': 'e4f4f3d8455485f954491fcd563ef9344444390f83c88de80975cc445946e284'}
RUNTIME_IMPORT_PINS = {'artifacts/tooling/crypto-oracle-python/unicorn/__init__.py': '0e8ac7115c755994a968fa865bd1b2f2075edea715c17e91d62af2cc52c13392', 'artifacts/tooling/crypto-oracle-python/unicorn/arm64_const.py': 'ddadd814eccd0a312bb43da7b4f2298690660bd5698c27edc306b1d981cff972', 'artifacts/tooling/crypto-oracle-python/unicorn/arm_const.py': 'ace0c3e49f61649034a1bec4279576b67e064df146ea8062c67e68dc14e6eb7b', 'artifacts/tooling/crypto-oracle-python/unicorn/lib/unicorn.dll': '010d85dce84b8f6ffaec3d5420f1b5f7768f859eb831be574c7da23e656ee8f1', 'artifacts/tooling/crypto-oracle-python/unicorn/m68k_const.py': 'af95f32f2810fe19888ac723db70c74c7fb1df2bc8ba3578ede0a28b8eca94a7', 'artifacts/tooling/crypto-oracle-python/unicorn/mips_const.py': '087925a25a128662e095bb861af3c38a2a6c522fc21e222e31b71aeacaaa63d3', 'artifacts/tooling/crypto-oracle-python/unicorn/ppc_const.py': '11e0c52a1c137874352119fb3d1621639079feda6574ee575271ef683a0a8f17', 'artifacts/tooling/crypto-oracle-python/unicorn/riscv_const.py': '86e08d5f6327d154306d5d02899331892de6f44020ff86900a84d2b212205925', 'artifacts/tooling/crypto-oracle-python/unicorn/s390x_const.py': '4f6194d1697d8684921782a81f494458dc859f8ebf2f78e30f673bd5f7cd590f', 'artifacts/tooling/crypto-oracle-python/unicorn/sparc_const.py': '9dd58fa5aeab225a0f8186f653f5c8fc5fd161b75ccc6a541e5af79f36af2698', 'artifacts/tooling/crypto-oracle-python/unicorn/tricore_const.py': '88310f61e12b731b2550031eb6423fbf815e66428b483132d3df47614c9d53ae', 'artifacts/tooling/crypto-oracle-python/unicorn/unicorn.py': '2aed71e6d5bc60807198cdcc3ed43a485a7acae1f41f08d986137afc55df2029', 'artifacts/tooling/crypto-oracle-python/unicorn/unicorn_const.py': 'c21d7c49f62296591a5f09ed0119ef95083b82f5f3f66b829578784c7b164368', 'artifacts/tooling/crypto-oracle-python/unicorn/unicorn_py2.py': 'b82ccc7c00762e10f0326e8d8ad4381872cf531799d5e003ad52c9d7ac61ae42', 'artifacts/tooling/crypto-oracle-python/unicorn/unicorn_py3/__init__.py': '2cd4a0d95ef236b5b9e3efb68b20fb6a6d1fb4190db2e9cc0a6447eb2c0aa755', 'artifacts/tooling/crypto-oracle-python/unicorn/unicorn_py3/arch/__init__.py': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', 'artifacts/tooling/crypto-oracle-python/unicorn/unicorn_py3/arch/arm.py': 'd486ff4a9c3f797e5e57a5201a1e2304b97a54b6bc61e320062f1290f4e3dc33', 'artifacts/tooling/crypto-oracle-python/unicorn/unicorn_py3/arch/arm64.py': '2e393f3f863da1576619e03abcbda2a2e2e54d673aac98979cf0b6caed8926b4', 'artifacts/tooling/crypto-oracle-python/unicorn/unicorn_py3/arch/intel.py': 'b3b8338a85ac74623e7a67dfb4f44dc9933786a329e64d772987490dbf751637', 'artifacts/tooling/crypto-oracle-python/unicorn/unicorn_py3/arch/types.py': '525ed179db874a13291f9469bd6243e7293aba17454de9b10a9227106d093787', 'artifacts/tooling/crypto-oracle-python/unicorn/unicorn_py3/unicorn.py': 'b4de7d560790a587157b17edd71c83b4f2d2bade2447d1a5433c497468ac8aeb', 'artifacts/tooling/crypto-oracle-python/unicorn/x86_const.py': 'd7663db6425f52838f3e79e45a8fe22b6c02be7edb44367ea2118aec04ee5728'}
TCP_RUNNER_SHA = 'b296cc379b20eb60d331a479d6e88f6a5ab092a9c13288c7e8c28ed240c46ac1'
TCP_QUALIFIER_SOURCE_SHA = '920b50e7720f568b32ac8310896cc6b09f12fd7bca49db4ac118aba0fb8eb895'


AUTHORITY_ADAPTER=Path('C:\\Users\\risei\\Desktop\\God2\\God2-Server\\artifacts\\research\\native-guild-officers-0082\\postinstall-native-runner-final-v01\\runtime_authority_adapter.py').resolve()
AUTHORITY_ADAPTER_SHA='a32f6ab19bbe2931620a780975a12cff2e5b25822c75a76498aef00f80c2fea3'
RAW_OWNER_READER=Path('C:\\Users\\risei\\Desktop\\God2\\God2-Server\\artifacts\\research\\native-guild-officers-0082\\postinstall-native-runner-final-v01\\raw_owner_readonly.py').resolve()
RAW_OWNER_READER_SHA='e5ee959744a834af9c15d14e4b293d8f03909b9f0e46dbf8c855dffc768f563e'

def authority_adapter():
    return load_evidence_adapter(AUTHORITY_ADAPTER,AUTHORITY_ADAPTER_SHA)

# This draft has no runnable placeholder entrypoint: both public runtime routes
# deny before the inherited Windows/runtime context can be loaded.
def require_binding_ready():
    global CANDIDATE, CONTRACT
    view=authority_adapter().approved_view() # absent root report -> deny before load_context
    CANDIDATE=view["candidate"]
    CONTRACT=BASE/("officer-postinstall-native-v01" if view["stage"]=="POSTINSTALL" else "officer-postintegration-native-v01")/"contract.json"
    require(BINDINGS_READY is True, 'V03_ACTUAL_QUALIFICATION_BINDINGS_NOT_READY')
    for name,digest in {**REFERENCE_PINS,**RUNTIME_IMPORT_PINS}.items():
        require((ROOT/name).is_file() and sha(ROOT/name)==digest,'EXACT_REFERENCE_OR_RUNTIME_SOURCE_CHANGED_'+name)
    for path, digest in ((CANDIDATE,CANDIDATE_SHA),(COMPILED,COMPILED_SHA),
            (TCP_QUALIFICATION,TCP_SHA),(STRICT_QUALIFICATION,STRICT_SHA),(STRICT_SEAL,STRICT_SEAL_SHA)):
        require(type(digest) is str and len(digest)==64 and all(x in '0123456789abcdef' for x in digest), 'V03_ACTUAL_HASH_REQUIRED_'+path.name)
        require(path.is_file() and sha(path)==digest, 'V03_REQUIRED_QUALIFICATION_CHANGED_'+path.name)
    require(STRICT_EXPECTED_CASES is not None, 'V03_REVIEWED_STRICT_CASE_SHAPE_REQUIRED')
    # Real compiled-ledger and strict 16 CLI evidence, before any runtime import.
    build = load_evidence_adapter(BUILD_ADAPTER, BUILD_ADAPTER_SHA)
    build.validate(COMPILED, COMPILED_SHA, CANDIDATE_SHA)
    strict = load_evidence_adapter(STRICT_ADAPTER, STRICT_ADAPTER_SHA)
    strict.validate(STRICT_QUALIFICATION, STRICT_SEAL, CANDIDATE_SHA, COMPILED_SHA,
        read(BASE/'application-candidate-v03/preparation.json')['source_pins'])


def load_evidence_adapter(path, digest):
    require(path.is_file() and sha(path)==digest, 'ACTUAL_EVIDENCE_ADAPTER_CHANGED_'+path.name)
    spec=importlib.util.spec_from_file_location('_pure_'+path.stem, path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module



def validate_v03_delta():
    predecessor=read(BASE/'application-candidate-v02/preparation.json')
    preparation=read(BASE/'application-candidate-v03/preparation.json')
    require(len(predecessor['source_pins'])==len(preparation['source_pins'])==446 and
        set(predecessor['source_pins'])==set(preparation['source_pins']), 'V03_FULL446_SOURCE_NAMES_REQUIRED')
    changed={n for n,h in predecessor['source_pins'].items() if preparation['source_pins'][n]!=h}
    require(changed=={'src/db/GuildOfficerSqliteMigrations.cpp'}, 'V03_ONLY_STRICT_SCHEMA_GUARD_DELTA_ALLOWED')
    require(preparation['source_pins']['src/core/Application.cpp']==APPLICATION_SHA and
        preparation['source_pins']['src/db/GuildOfficerSqliteMigrations.cpp']==STRICT_SOURCE_SHA,
        'V03_APPLICATION_AND_STRICT_SOURCE_PIN_REQUIRED')
    require(preparation['remove_addition_restores_v02_bytes'] is True, 'V03_SQL_GUARD_ONLY_REVERSAL_REQUIRED')
    old=BASE/'application-candidate-v02/shadow/src/db/GuildOfficerSqliteMigrations.cpp'
    new=PRIVATE_ROOT/'src/db/GuildOfficerSqliteMigrations.cpp'
    addition=preparation['addition_utf8'].encode('utf-8')
    require(new.read_bytes().count(addition)==1 and new.read_bytes().replace(addition,b'',1)==old.read_bytes(),
        'V03_SOLE_ADDITION_REVERSAL_BYTES_REQUIRED')
    return preparation


def strict_dependency_pins():
    require_binding_ready()
    module=load_evidence_adapter(STRICT_ADAPTER,STRICT_ADAPTER_SHA)
    return module.validate(STRICT_QUALIFICATION,STRICT_SEAL,CANDIDATE_SHA,COMPILED_SHA,
        validate_v03_delta()['source_pins'])


def build_dependency_pins():
    require_binding_ready()
    module=load_evidence_adapter(BUILD_ADAPTER,BUILD_ADAPTER_SHA)
    return module.validate(COMPILED,COMPILED_SHA,CANDIDATE_SHA)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def require(value, label):
    if not value:
        raise AssertionError(label)

def resolve(value):
    path = Path(value)
    return (path if path.is_absolute() else ROOT / path).resolve()

def relative(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()

def validate_source_map(pins):
    require(type(pins) is dict and bool(pins), 'EXPLICIT_SOURCE_MAP_REQUIRED')
    for name, digest in pins.items():
        require(type(name) is str and name == Path(name).as_posix() and not Path(name).is_absolute() and not Path(name).anchor
                and '..' not in Path(name).parts and type(digest) is str and len(digest) == 64
                and all(c in '0123456789abcdef' for c in digest), 'STRICT_RELATIVE_HASH_PIN_REQUIRED')

def validate_contract_structure(contract, helper_path):
    require_binding_ready()
    require(contract.get('design') == 'CUSTOM-0082' and contract.get('feature_family') == 'guild-officers0082', 'OFFICER82_CONTRACT_REQUIRED')
    for field in ('formal_config', 'env_lab_false', 'owned_guild_membership_enabled', 'owned_guild_announcements_enabled', 'owned_guild_officers_enabled'):
        require(contract.get(field) is True, 'TRUE_FEATURE_GATE_REQUIRED_' + field)
    require(type(contract.get('schema_version')) is int and contract['schema_version'] == 51, 'EXACT_SCHEMA51_REQUIRED')
    require(resolve(contract['candidate_path']) == CANDIDATE and contract['candidate_sha256'] == CANDIDATE_SHA, 'LATEST_V03_BINARY_REQUIRED')
    require(resolve(contract['helper_path']) == Path(helper_path).resolve(), 'EXACT_SELF_HELPER_PATH_REQUIRED')
    require(contract.get('private_candidate_application_sha256') == APPLICATION_SHA, 'LATEST_V03_APPLICATION_REQUIRED')
    require(resolve(contract['private_candidate_root']) == PRIVATE_ROOT, 'EXACT_PRIVATE_SHADOW_ROOT_REQUIRED')
    require(resolve(contract['compiled_candidate_receipt_path']) == COMPILED and contract['compiled_candidate_receipt_sha256'] == COMPILED_SHA, 'LATEST_V03_COMPILED_RECEIPT_REQUIRED')
    require(contract.get('actual_native_accepted') is None and contract.get('actual_native_runtime_observations') is None, 'UNOBSERVED_NATIVE_FIELDS_MUST_BE_NULL')
    require(contract.get('bootstrap_schema49_candidate_sha256') == BOOTSTRAP49_SHA, 'FROZEN_BOOTSTRAP49_REQUIRED')
    for name, count in [('root_runtime_source_sha256', 1707), ('private_candidate_source_sha256', 446)]:
        validate_source_map(contract[name]);require(len(contract[name]) == count, 'EXACT_PIN_COUNT_REQUIRED_' + name)
    validate_source_map(contract['source_sha256'])
    for name, digest in contract['root_runtime_source_sha256'].items():
        require(contract['source_sha256'].get(name) == digest, 'ROOT_PIN_MUST_HAVE_BEFORE_AFTER_GUARD_' + name)
    for name, digest in contract['private_candidate_source_sha256'].items():
        require(contract['source_sha256'].get(relative(PRIVATE_ROOT / name)) == digest, 'PRIVATE_PIN_MUST_HAVE_BEFORE_AFTER_GUARD_' + name)
    require(contract['private_candidate_source_sha256'].get('src/core/Application.cpp') == APPLICATION_SHA, 'APPLICATION_CLOSURE_REQUIRED')
    tcp_path = resolve(contract['tcp_qualification_receipt_path'])
    require(tcp_path==TCP_QUALIFICATION and contract.get('tcp_qualification_receipt_sha256')==TCP_SHA, 'V03_EXACT_TCP_QUALIFICATION_BINDING_REQUIRED')
    require(resolve(contract['strict_schema_qualification_path'])==STRICT_QUALIFICATION and contract['strict_schema_qualification_sha256']==STRICT_SHA, 'V03_EXACT_STRICT_QUALIFICATION_BINDING_REQUIRED')
    require(resolve(contract['strict_schema_seal_path'])==STRICT_SEAL and contract['strict_schema_seal_sha256']==STRICT_SEAL_SHA, 'V03_EXACT_STRICT_SEAL_BINDING_REQUIRED')
    require(tcp_path.parent == BASE / 'application-candidate-v03' and tcp_path.suffix == '.json', 'LATEST_V03_TCP_RECEIPT_PATH_REQUIRED')
    digest = contract.get('tcp_qualification_receipt_sha256')
    require(type(digest) is str and len(digest) == 64 and all(c in '0123456789abcdef' for c in digest), 'ACTUAL_COMPLETED_TCP_RECEIPT_REQUIRED')
    for path, digest in [(Path(helper_path), contract['helper_sha256']), (COMPILED, COMPILED_SHA), (tcp_path, digest)]:
        require(contract['source_sha256'].get(relative(path)) == digest, 'RECEIPT_SELF_BEFORE_AFTER_CLOSURE_REQUIRED_' + path.name)
    authority_adapter().validate_structure(contract,helper_path)

def dependency_pins(helper_path):
    require_binding_ready()
    result = {relative(path): digest for path, digest in [(LEGACY, LEGACY_SHA), (KICK, KICK_SHA), (DISBAND_PHASE, DISBAND_PHASE_SHA), (DISBAND_PROOF, DISBAND_PROOF_SHA), (OFFICER_PROOF, OFFICER_PROOF_SHA), (PLAN / 'sealed-result.json', PLAN_SEAL_SHA)]}
    for name, digest in read(PLAN / 'sealed-result.json')['hashes'].items():
        result[relative(PLAN / name)] = digest
    result[relative(helper_path)] = sha(helper_path)
    result.update(strict_dependency_pins())
    result.update(build_dependency_pins())
    for name,digest in REFERENCE_PINS.items():
        require(sha(ROOT/name)==digest,'EXACT_REFERENCE_SOURCE_CHANGED_'+name)
        result[name]=digest
    tcp_runner=BASE/'tcp-execution-v03/run.py'
    require(sha(tcp_runner)==TCP_RUNNER_SHA,'ACTUAL_TCP_EXECUTOR_SOURCE_CHANGED')
    result[relative(tcp_runner)]=TCP_RUNNER_SHA
    qualifier=BASE/'application-candidate-v03/qualify_tcp.py'
    require(sha(qualifier)==TCP_QUALIFIER_SOURCE_SHA,'ACTUAL_TCP_QUALIFIER_SOURCE_CHANGED')
    result[relative(qualifier)]=TCP_QUALIFIER_SOURCE_SHA
    for name,digest in RUNTIME_IMPORT_PINS.items():
        require(sha(ROOT/name)==digest,'BUNDLED_RUNTIME_SOURCE_CHANGED_'+name)
        result[name]=digest
    raw=read(resolve(read(TCP_QUALIFICATION)['tcp_receipt_path']))
    log=resolve(raw['log_path']);require(sha(log)==raw['log_sha256'],'ACTUAL_TCP_LOG_CHANGED')
    result[relative(log)]=raw['log_sha256']
    manifest=BASE/'tcp-harness-v01/manifest.json'
    require(sha(manifest)==raw['harness_manifest_sha256'],'ACTUAL_TCP_HARNESS_MANIFEST_CHANGED')
    result[relative(manifest)]=raw['harness_manifest_sha256']
    result.update(authority_adapter().dependency_pins(helper_path))
    return result

def load_plan():
    require(sha(PLAN / 'sealed-result.json') == PLAN_SEAL_SHA, 'OFFICER_PLAN_SEAL_CHANGED')
    for name, digest in read(PLAN / 'sealed-result.json')['hashes'].items():
        require(sha(PLAN / name) == digest, 'OFFICER_PLAN_ARTIFACT_CHANGED_' + name)
    for path, digest in [(LEGACY, LEGACY_SHA), (KICK, KICK_SHA), (DISBAND_PHASE, DISBAND_PHASE_SHA)]:
        require(sha(path) == digest, 'IMMUTABLE_NATIVE_DEPENDENCY_CHANGED_' + path.name)
    spec = importlib.util.spec_from_file_location('_sealed_officer82_plan', PLAN / 'wrapper_plan.py')
    plan = importlib.util.module_from_spec(spec);spec.loader.exec_module(plan)
    return plan

def transformed_tree():
    plan = load_plan()
    tree, edits = plan.transformed_tree(KICK.read_text(encoding='utf-8'), DISBAND_PHASE.read_text(encoding='utf-8'), (PLAN / 'officer_phase.py').read_text(encoding='utf-8'))
    roots = [n for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'ROOT' for t in n.targets)]
    require(len(roots) == 1 and ast.unparse(roots[0].value) == 'Path(__file__).resolve().parents[2]', 'EXACT_INHERITED_ROOT_ASSIGNMENT_REQUIRED')
    roots[0].value = ast.parse('Path(' + repr(str(ROOT)) + ').resolve()', mode='eval').body
    # No native lifecycle functions or cleanup instructions are overridden.
    return ast.fix_missing_locations(tree), edits

def contract_guard(args, context):
    require_binding_ready()
    validate_v03_delta()
    contract = read(args.contract)
    helper = Path(__file__).resolve()
    validate_contract_structure(contract, helper)
    require(args.server_candidate.resolve() == CANDIDATE and sha(CANDIDATE) == CANDIDATE_SHA, 'ACTUAL_CANDIDATE_EXACT_REQUIRED')
    require(contract['helper_sha256'] == sha(helper), 'ACTUAL_SELF_HASH_REQUIRED')
    args.bootstrap_candidate = resolve(contract['bootstrap_schema49_candidate_path'])
    require(sha(args.bootstrap_candidate) == BOOTSTRAP49_SHA == context['BOOTSTRAP49_SHA'], 'ACTUAL_BOOTSTRAP49_REQUIRED')
    actual = {name: sha(ROOT / name) for name in contract['source_sha256']}
    require(actual == contract['source_sha256'], 'COMPLETE_BEFORE_AFTER_SOURCE_CLOSURE_CHANGED')
    for name, digest in dependency_pins(helper).items():
        require(actual.get(name) == digest, 'FULL_NATIVE_DEPENDENCY_CLOSURE_REQUIRED_' + name)
    view=authority_adapter().validate_structure(contract,helper)
    require(contract["root_runtime_source_sha256"]==view["root"], "ROOT_EXACT19_KNOWN_DELTA_AND_APPROVED_INSTALL_PHASE_REQUIRED")
    preparation = read(BASE / 'application-candidate-v03/preparation.json')
    require(contract['private_candidate_source_sha256'] == preparation['source_pins'], 'PRIVATE_SOURCE_NOT_REBASEABLE')
    private_actual = {p.relative_to(PRIVATE_ROOT).as_posix(): sha(p) for p in PRIVATE_ROOT.rglob('*') if p.is_file()}
    require(private_actual == preparation['source_pins'], 'PRIVATE_COMPLETE_FILE_SET_CHANGED')
    # V03 actual five-step ledger has its own schema; no fabricated V02 keys.
    for name,digest in build_dependency_pins().items():
        require(actual.get(name)==digest,'ACTUAL_V03_BUILD_FULL_CLOSURE_REQUIRED_'+name)
    tcp_path = resolve(contract['tcp_qualification_receipt_path']);tcp = read(tcp_path)
    require(sha(tcp_path) == contract['tcp_qualification_receipt_sha256'] and tcp['candidate_sha256'] == CANDIDATE_SHA
        and tcp['compiled_receipt_sha256'] == COMPILED_SHA and tcp['tests_run'] == 10 and tcp['all_selected_cases_passed'] is True
        and tcp['source_closures_exact'] is True and tcp['private2599_released'] is True
        and tcp['candidate_and_formal_chat_equal_frozen_baseline'] is True, 'LATEST_COMPLETE_TCP10_REQUIRED')
    require(sha(resolve(tcp['tcp_receipt_path'])) == tcp['tcp_receipt_sha256'], 'RAW_TCP_RECEIPT_CHANGED')
    raw = read(resolve(tcp['tcp_receipt_path']))
    require(raw['accepted'] is True and raw['candidate_sha256'] == CANDIDATE_SHA and raw['tests_run'] == 10
        and raw['failures'] == 0 and raw['errors'] == 0 and len(raw['records']) == 10
        and all(row['status'] == 'PASS' for row in raw['records']), 'ACTUAL_RAW_TCP10_REQUIRED')
    for field, hash_field in [('sealed_input_harness_path', 'harness_sha256'),
                             ('actual_executed_harness_path', 'actual_executed_harness_sha256'),
                             ('executed_source_proof_path', 'executed_source_proof_sha256')]:
        path = resolve(tcp[field])
        require(sha(path) == tcp[hash_field] and actual.get(relative(path)) == tcp[hash_field], 'ACTUAL_TCP_EXECUTED_SOURCE_CLOSURE_REQUIRED_' + field)
    require(tcp['output_literal_only_reverse_bytes_and_full_AST_exact'] is True, 'ACTUAL_TCP_OUTPUT_ONLY_SOURCE_PROOF_REQUIRED')
    for path in [BASE / 'application-candidate-v03/preparation.json', BASE / 'application-candidate-v03/configure-v01-result.json',
                 BASE / 'application-candidate-v03/build-v01-result.json', BASE / 'application-candidate-v03/build-v01.log',
                 resolve(tcp['tcp_receipt_path'])]:
        require(actual.get(relative(path)) == sha(path), 'BUILD_TCP_BEFORE_AFTER_CLOSURE_REQUIRED_' + path.name)
    require(tcp['strict_schema51_actual_qualification_sha256']==STRICT_SHA and tcp['candidate_final_build_reopen_report_sha256']==sha(BASE/'application-candidate-v03/final-report.json'), 'ACTUAL_V03_TCP_STRICT_BUILD_BINDINGS_REQUIRED')
    if view["stage"]=="POSTINSTALL":
        reader=load_evidence_adapter(RAW_OWNER_READER,RAW_OWNER_READER_SHA)
        context["approved_raw_owner_proof"]=authority_adapter().verify_owned_host(view,context,reader.consistent_identity)
    return contract, actual

def load_context():
    require_binding_ready()
    tree, _ = transformed_tree()
    # All inherited Windows helpers resolve from their actual immutable location.
    sys.path[:0] = [str(ROOT / 'tools/strike_lab'), str(ROOT), str(ROOT / 'artifacts/tooling/crypto-oracle-python')]
    context = {'__name__': '_private_officer82_inherited', '__file__': str(Path(__file__).resolve())}
    exec(compile(tree, str(Path(__file__).resolve()), 'exec'), context)
    plan = load_plan();legacy = plan.legacy_module()
    context['CONTRACT'] = CONTRACT
    context['validate_retirement'] = legacy.validate_retirement
    inherited_qualify = context['qualify']
    def qualify():
        inherited_qualify()  # All old native membership/announcement/kick/current-client gates.
        for path, digest in dependency_pins(Path(__file__)).items():
            require(sha(ROOT / path) == digest, 'NATIVE82_DEPENDENCY_CHANGED_' + path)
        base = context['base'];mapped = context['pefile'].PE(str(base.LIVE)).get_memory_mapped_image()
        disband = read(DISBAND_PROOF)
        require(disband['client']['sha256'] == base.CLIENT_SHA and disband['original_mapped_image']['sha256'] == base.MAPPED_SHA, 'FULL75_BUILD_IDENTITY_REQUIRED')
        officer = read(OFFICER_PROOF)
        require(officer['client']['sha256'] == base.CLIENT_SHA and officer['original']['sha256'] == base.MAPPED_SHA and len(officer['native_spans']) == 19, 'OFFICER19_BUILD_IDENTITY_REQUIRED')
        for pins, label in [(disband['actual_machine_spans'], 'DISBAND75'), (officer['native_spans'], 'OFFICER82')]:
            for pin in pins:
                lo = int(pin['start'], 16) - 0x400000;hi = int(pin['end_exclusive'], 16) - 0x400000
                require(pin['current_equal_original'] is True and 0 <= lo < hi <= len(mapped)
                    and hashlib.sha256(mapped[lo:hi]).hexdigest() == pin['sha256'], label + '_ACTUAL_NATIVE_SPAN_CHANGED')
        return officer
    context['qualify'] = qualify
    context['contract_guard'] = lambda args: contract_guard(args, context)
    return context

def main():
    require_binding_ready()
    return load_context()['main']()

if __name__ == '__main__':
    raise SystemExit(main())
