"""Seal native mouse-hit semantics fix while preserving both failed helpers."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    previous=ROOT/'artifacts/research/native-guild-membership-0078/leader-live-v02/contract.json'
    destination=ROOT/'artifacts/research/native-guild-membership-0078/leader-live-v03/contract.json'
    candidate=ROOT/'build-native-guild-leadership-20261003/Release/god2-server.exe'
    helper=ROOT/'tools/strike_lab/private_guild_leadership_0078_v03_20261003.py'
    assert sha(candidate)=='c0a6c1a530685ef45d869853a969b04078371edbbf94be3ac5d163da671cdc0a'
    assert sha(helper)=='01c3e6721c75f734a9a67b5a77a0173ba95591a02eae82ef0a4e3c7eee04b492'
    keys=set(json.loads(previous.read_text('utf-8'))['source_sha256'])
    keys.update(('tools/strike_lab/private_guild_leadership_0078_v03_20261003.py',
        'artifacts/research/native-guild-membership-0078/leader-live-v03/field-pins.json',
        'artifacts/research/native-guild-membership-0078/leader-live-v03/mouse-hit-machine.json'))
    result={'design':'CUSTOM-0078','scope':'DISPOSABLE_LOOPBACK_LAB_ONLY_NOT_FORMAL',
        'candidate_sha256':sha(candidate),'helper_sha256':sha(helper),
        'source_sha256':{key:sha(ROOT/key) for key in sorted(keys)},
        'acceptance_scope':'Native8D/6F create and pending; native help/91 role3 + role0;71 approve and72 reject. No original NPC mapping or full guild completion claim.',
        'preserved_prior_contract_sha256':sha(previous),'seal_tool_sha256':sha(Path(__file__)),
        'formal_installed':False}
    destination.parent.mkdir(parents=True,exist_ok=True)
    with destination.open('x',encoding='utf-8') as stream:json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print(json.dumps({'path':str(destination),'sha256':sha(destination),'source_files':len(keys),'helper_sha256':sha(helper)}))
if __name__=='__main__':main()
