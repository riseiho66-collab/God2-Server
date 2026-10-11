"""Immutable source/candidate/helper closure for ordinary member native73 QA."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'artifacts/research/native-guild-membership-0078'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    previous=BASE/'leader-live-v03/contract.json';candidate=ROOT/'build-native-guild-member-leave-20261003/Release/god2-server.exe'
    helper=ROOT/'tools/strike_lab/private_guild_leadership_0078_v04_20261003.py';fields=BASE/'leader-live-v04/field-pins.json'
    assert sha(candidate)=='1be0e7a8e271aaf7f2135d369e66f5bf0a5b09b25053b322ee7ba43e6626fd78'
    assert sha(helper)=='f051d9ed80ea47d2c9c6425649f95c9127b50a15a22b6e5f9f67324dd9cb0393'
    assert sha(fields)=='c8d058d44c4d9044938d18408f45fdcd4911c0cbe7d1f810e09638f6443b7f40'
    keys=set(json.loads(previous.read_text('utf-8'))['source_sha256'])
    for directory in ('src','scripts','tests'):
        keys.update(p.relative_to(ROOT).as_posix() for p in (ROOT/directory).rglob('*')
            if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc')
    keys.update(p.relative_to(ROOT).as_posix() for p in (helper,fields,Path(__file__),
        ROOT/'tools/strike_lab/finalize_guild_member_leave_0078_v01_20261003.py',
        BASE/'entry-v02/native.json',BASE/'member-leave-v01/native.json'))
    result={'design':'CUSTOM-0078','scope':'DISPOSABLE_LOOPBACK_LAB_ONLY_NOT_FORMAL',
        'candidate_sha256':sha(candidate),'helper_sha256':sha(helper),
        'source_sha256':{k:sha(ROOT/k) for k in sorted(keys)},'formal_installed':False,
        'acceptance_scope':'Existing TEST_ONLY8D/6F membership fixtures, native founder71/72 and ordinary accepted member normal help/main16/modal4/C2S73 cancel/confirm; two locales. General non-TEST create/join entry OPEN; no rendered-pixel or formal acceptance claim.',
        'preserved_prior_contract_sha256':sha(previous),'seal_tool_sha256':sha(Path(__file__))}
    destination=BASE/'leader-live-v04/contract.json'
    with destination.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'path':str(destination),'sha256':sha(destination),'source_files':len(keys)}))
if __name__=='__main__':main()
