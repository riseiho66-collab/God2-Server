"""Seal NEW immutable CUSTOM0078 candidate evidence; never deploy or refresh old pins."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    previous=ROOT/'artifacts/research/native-guild-membership-0078/live-v03/contract.json'
    destination=ROOT/'artifacts/research/native-guild-membership-0078/leader-live-v01/contract.json'
    candidate=ROOT/'build-native-guild-leadership-20261003/Release/god2-server.exe'
    helper=ROOT/'tools/strike_lab/private_guild_leadership_0078_v01_20261003.py'
    assert sha(candidate)=='afc73979f7da5e3db5cf31496821be101f6cdeb0daf72f6cdcc6df13e2148f4e'
    keys=set(json.loads(previous.read_text('utf-8'))['source_sha256'])
    keys.update(('src/handlers/OwnedGuildLeaderPanelService.h','src/protocol/RecoveredGuildLeadership.h',
        'tests/test_owned_guild_leadership_wire_0078.cpp','tests/storage_owned_guild_leader_panel_0078.cpp',
        'tests/research/test_native_guild_leadership_server_20261003.py','tests/CMakeLists.txt',
        'artifacts/research/native-guild-membership-0078/leader-live-v01/field-pins-v02.json',
        str(helper.relative_to(ROOT)).replace('\\','/')))
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
