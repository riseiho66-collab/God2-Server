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
CANDIDATE = BASE / 'application-candidate-v02/build/Release/god2-server.exe'
CANDIDATE_SHA = 'e2ba530bacc2ad6bbb89e810a5cfefda97389bec4c2b393aaa96fa389c2e07c5'
COMPILED = BASE / 'application-candidate-v02/compiled-candidate-v02.json'
COMPILED_SHA = '2ac54673a4fc58cc1fbdc76c23ce961052a7bea89dcb7d1f69aaf81868769691'
PRIVATE_ROOT = BASE / 'application-candidate-v02/shadow'
APPLICATION_SHA = 'b20b3c3c56186521bf602f601d4c4f157f83f9a5521f7b7faa8fdaddb660980e'
BOOTSTRAP49_SHA = '76d9e815628b1736dd013915fb1d42d2cb0e5d5eb49c028d745ac657355b6fa6'
CONTRACT = BASE / 'officer-live-v01/contract.json'

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
    require(contract.get('design') == 'CUSTOM-0082' and contract.get('feature_family') == 'guild-officers0082', 'OFFICER82_CONTRACT_REQUIRED')
    for field in ('formal_config', 'env_lab_false', 'owned_guild_membership_enabled', 'owned_guild_announcements_enabled', 'owned_guild_officers_enabled'):
        require(contract.get(field) is True, 'TRUE_FEATURE_GATE_REQUIRED_' + field)
    require(type(contract.get('schema_version')) is int and contract['schema_version'] == 51, 'EXACT_SCHEMA51_REQUIRED')
    require(resolve(contract['candidate_path']) == CANDIDATE and contract['candidate_sha256'] == CANDIDATE_SHA, 'LATEST_V02_BINARY_REQUIRED')
    require(resolve(contract['helper_path']) == Path(helper_path).resolve(), 'EXACT_SELF_HELPER_PATH_REQUIRED')
    require(contract.get('private_candidate_application_sha256') == APPLICATION_SHA, 'LATEST_V02_APPLICATION_REQUIRED')
    require(resolve(contract['private_candidate_root']) == PRIVATE_ROOT, 'EXACT_PRIVATE_SHADOW_ROOT_REQUIRED')
    require(resolve(contract['compiled_candidate_receipt_path']) == COMPILED and contract['compiled_candidate_receipt_sha256'] == COMPILED_SHA, 'LATEST_V02_COMPILED_RECEIPT_REQUIRED')
    require(contract.get('actual_native_accepted') is None and contract.get('actual_native_runtime_observations') is None, 'UNOBSERVED_NATIVE_FIELDS_MUST_BE_NULL')
    require(contract.get('bootstrap_schema49_candidate_sha256') == BOOTSTRAP49_SHA, 'FROZEN_BOOTSTRAP49_REQUIRED')
    for name, count in [('root_runtime_source_sha256', 1698), ('private_candidate_source_sha256', 446)]:
        validate_source_map(contract[name]);require(len(contract[name]) == count, 'EXACT_PIN_COUNT_REQUIRED_' + name)
    validate_source_map(contract['source_sha256'])
    for name, digest in contract['root_runtime_source_sha256'].items():
        require(contract['source_sha256'].get(name) == digest, 'ROOT_PIN_MUST_HAVE_BEFORE_AFTER_GUARD_' + name)
    for name, digest in contract['private_candidate_source_sha256'].items():
        require(contract['source_sha256'].get(relative(PRIVATE_ROOT / name)) == digest, 'PRIVATE_PIN_MUST_HAVE_BEFORE_AFTER_GUARD_' + name)
    require(contract['private_candidate_source_sha256'].get('src/core/Application.cpp') == APPLICATION_SHA, 'APPLICATION_CLOSURE_REQUIRED')
    tcp_path = resolve(contract['tcp_qualification_receipt_path'])
    require(tcp_path.parent == BASE / 'application-candidate-v02' and tcp_path.suffix == '.json', 'LATEST_V02_TCP_RECEIPT_PATH_REQUIRED')
    digest = contract.get('tcp_qualification_receipt_sha256')
    require(type(digest) is str and len(digest) == 64 and all(c in '0123456789abcdef' for c in digest), 'ACTUAL_COMPLETED_TCP_RECEIPT_REQUIRED')
    for path, digest in [(Path(helper_path), contract['helper_sha256']), (COMPILED, COMPILED_SHA), (tcp_path, digest)]:
        require(contract['source_sha256'].get(relative(path)) == digest, 'RECEIPT_SELF_BEFORE_AFTER_CLOSURE_REQUIRED_' + path.name)

def dependency_pins(helper_path):
    result = {relative(path): digest for path, digest in [(LEGACY, LEGACY_SHA), (KICK, KICK_SHA), (DISBAND_PHASE, DISBAND_PHASE_SHA), (DISBAND_PROOF, DISBAND_PROOF_SHA), (OFFICER_PROOF, OFFICER_PROOF_SHA), (PLAN / 'sealed-result.json', PLAN_SEAL_SHA)]}
    for name, digest in read(PLAN / 'sealed-result.json')['hashes'].items():
        result[relative(PLAN / name)] = digest
    result[relative(helper_path)] = sha(helper_path)
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
    old = read(ROOT / 'artifacts/research/native-guild-management-0081/post-install-v01/contract.json')['source_sha256']
    expected_root = dict(old)
    expected_root['docs/custom-designs.json'] = read(ROOT / 'artifacts/research/native-guild-management-0081/implementation-final-v01/report.json')['postacceptance_documentation_only_delta']['docs/custom-designs.json']['current']
    require(contract['root_runtime_source_sha256'] == expected_root, 'ROOT_PRESERVATION_NOT_REBASEABLE')
    preparation = read(BASE / 'application-candidate-v02/preparation.json')
    require(contract['private_candidate_source_sha256'] == preparation['source_pins'], 'PRIVATE_SOURCE_NOT_REBASEABLE')
    private_actual = {p.relative_to(PRIVATE_ROOT).as_posix(): sha(p) for p in PRIVATE_ROOT.rglob('*') if p.is_file()}
    require(private_actual == preparation['source_pins'], 'PRIVATE_COMPLETE_FILE_SET_CHANGED')
    compiled = read(COMPILED)
    require(sha(COMPILED) == COMPILED_SHA and compiled['candidate_sha256'] == CANDIDATE_SHA
        and resolve(compiled['candidate_path']) == CANDIDATE and compiled['source_count'] == 446
        and compiled['all_private_inputs_exact'] is True and compiled['candidate_root_chat_equal_immutable_baseline'] is True
        and compiled['preparation_sha256'] == sha(BASE / 'application-candidate-v02/preparation.json'), 'REAL_FULL_BUILD_RECEIPT_REQUIRED')
    for kind in ['configure', 'build']:
        path = BASE / ('application-candidate-v02/' + kind + '-v01-result.json')
        require(sha(path) == compiled[kind + '_result_sha256'] and read(path)['exit_code'] == 0, 'ACTUAL_BUILD_CONFIGURE_ZERO_REQUIRED_' + kind)
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
    for path in [BASE / 'application-candidate-v02/preparation.json', BASE / 'application-candidate-v02/configure-v01-result.json',
                 BASE / 'application-candidate-v02/build-v01-result.json', BASE / 'application-candidate-v02/build-v01.log',
                 resolve(tcp['tcp_receipt_path'])]:
        require(actual.get(relative(path)) == sha(path), 'BUILD_TCP_BEFORE_AFTER_CLOSURE_REQUIRED_' + path.name)
    require(sha(BASE / 'application-candidate-v02/build-v01.log') == compiled['build_log_sha256'], 'ACTUAL_BUILD_LOG_CHANGED')
    return contract, actual

def load_context():
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
    return load_context()['main']()

if __name__ == '__main__':
    raise SystemExit(main())
