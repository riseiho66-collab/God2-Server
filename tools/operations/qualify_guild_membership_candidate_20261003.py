"""Write-once source/build contract for the disposable CUSTOM-0078 live run."""
import hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'artifacts/research/native-guild-membership-0078/live-v01'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    executable=ROOT/'build-native-guild-membership-20261003/Release/god2-server.exe'
    helper=ROOT/'tools/strike_lab/private_guild_membership_0078_v01_20261003.py'
    assert executable.is_file() and helper.is_file()
    paths=[ROOT/'CMakeLists.txt']
    for directory,suffixes in (('src',{'.h','.cpp'}),('scripts',{'.lua'}),
                               ('tests',{'.cpp','.py','.txt'}),('tools',{'.py'})):
        paths.extend(p for p in (ROOT/directory).rglob('*') if p.is_file() and p.suffix in suffixes)
    contract={'design':'CUSTOM-0078','scope':'DISPOSABLE_LOOPBACK_LAB_ONLY_NOT_FORMAL',
        'candidate_sha256':sha(executable),'helper_sha256':sha(helper),
        'source_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(set(paths))},
        'native_entry_claim':False,'fixture_auto_prompt':True}
    OUT.mkdir(parents=True,exist_ok=True)
    with (OUT/'contract.json').open('x',encoding='utf-8') as stream:
        json.dump(contract,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print(json.dumps({'candidate_sha256':contract['candidate_sha256'],
        'helper_sha256':contract['helper_sha256'],'source_files':len(contract['source_sha256']),
        'contract_sha256':sha(OUT/'contract.json')}))
if __name__=='__main__':main()
