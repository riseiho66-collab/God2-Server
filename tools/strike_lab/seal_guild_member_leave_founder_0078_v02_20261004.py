"""Seal the founder-independent native member-leave candidate and private QA."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'artifacts/research/native-guild-membership-0078'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    previous=BASE/'leader-live-v04/contract-v02.json';candidate=ROOT/'build-native-guild-member-leave-founder-20261004/Release/god2-server.exe'
    helper=ROOT/'tools/strike_lab/private_guild_leadership_0078_v05_20261004.py'
    fields=BASE/'leader-founder-battle-live-v01/field-pins.json'
    assert sha(candidate)=='832fffaf51b6febb1c18af300442c835539e1c8efbbe70ec9a8250560f37d2fc'
    assert sha(helper)=='3749930d314924842a33df5be9bb18dd86cdd9db6638915d31ac323371966560'
    assert sha(fields)=='ff8c34682b836888bef7c8b66b6e4a5cb37d33526891768087b455facba80588'
    keys=set(json.loads(previous.read_text('utf-8'))['source_sha256'])
    extra=[helper,fields,Path(__file__),ROOT/'tools/strike_lab/finalize_guild_member_leave_founder_0078_v01_20261004.py',
        BASE/'member-leave-founder-battle-v01/storage-probe.cpp',BASE/'member-leave-founder-battle-v01/tcp-probe.py',
        BASE/'member-leave-founder-battle-v01/verification-final.json',BASE/'leave-founder-battle-storage-v01/report.json']
    keys.update(p.relative_to(ROOT).as_posix() for p in extra)
    contract={'design':'CUSTOM-0078','scope':'DISPOSABLE_LOOPBACK_LAB_ONLY_NOT_FORMAL',
        'candidate_sha256':sha(candidate),'helper_sha256':sha(helper),'formal_installed':False,
        'source_sha256':{k:sha(ROOT/k) for k in sorted(keys)},'preserved_prior_contract_sha256':sha(previous),
        'acceptance_scope':'Native create/apply/founder approve/reject plus ordinary member cancellation/self-leave while legal TEST_ONLY founder reservation remains unsettled. Two locales, hidden WM/VM_READ/SQL. No actual rendered founder battle, original NPC mapping, general non-TEST create/join entry or formal installation claim.',
        'superseded_before_execution_contract_sha256':sha(BASE/'leader-founder-battle-live-v01/contract.json'),'supersession_reason':'Pure qualifier actor/cleanup integer validation tightened before any UI execution; candidate/helper unchanged','seal_tool_sha256':sha(Path(__file__))}
    destination=BASE/'leader-founder-battle-live-v01/contract-v02.json'
    with destination.open('x',encoding='utf-8') as f:json.dump(contract,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'path':str(destination),'sha256':sha(destination),'source_files':len(keys)}))
if __name__=='__main__':main()
