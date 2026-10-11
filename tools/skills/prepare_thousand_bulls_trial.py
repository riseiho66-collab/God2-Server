"""CUSTOM-0059: assemble a separate native client; never write formal files."""
from pathlib import Path
import hashlib
import json
import shutil
from tools.skills.install_shunying_clone import make_patched_image, INPUT_SHA256

ROOT = Path(__file__).resolve().parents[2]
TRIAL = ROOT / 'artifacts/playtests/private-shunying-manual-thousand-bulls-20260930-01'
SOURCE = ROOT / 'artifacts/playtests/private-shunying-manual-20260930-01/client'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    client = TRIAL / 'client'
    if client.exists():
        raise FileExistsError('Refusing to overwrite an existing trial client')
    raw = (SOURCE / 'God2-shunying-manual.exe').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == INPUT_SHA256
    shutil.copytree(SOURCE, client, ignore=shutil.ignore_patterns('*.exe', '*.log', '*.before-*', '*.bootstrap.json', 'God2ShunyingClone.dll'))
    (client / 'God2-shunying-manual.exe').write_bytes(raw)
    dll = client / 'God2ShunyingClone.dll'
    shutil.copy2(ROOT / 'build-bull-native/bin/God2ShunyingClone.dll', dll)
    patched, bootstrap = make_patched_image(raw, dll)
    exe = client / 'God2-thousand-bulls.exe'
    exe.write_bytes(patched)
    # Native startup requires four command arguments and the same CP950 runtime
    # as the accepted client. Launching the EXE without arguments exits cleanly.
    shutil.copy2(ROOT.parent/'God2/God2.exe.le.config', Path(str(exe)+'.le.config'))
    candidate = ROOT / 'artifacts/custom-skills/thousand-bulls/client-candidate'
    data = json.loads((candidate / 'manifest.json').read_text(encoding='utf-8'))
    for name, pin in data['output_sha256'].items():
        source = candidate / name
        assert digest(source) == pin
        target = client / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    visuals = ROOT / 'artifacts/custom-skills/thousand-bulls/visualpack'
    spec = json.loads((visuals / 'manifest.json').read_text(encoding='utf-8'))
    dest = client / 'Data2/Fight/Custom/Bull150'
    dest.mkdir(parents=True, exist_ok=False)
    pins = {}
    for entry in spec['files'] + spec['audio']:
        source = visuals / entry['path']
        assert digest(source) == entry['sha256']
        shutil.copy2(source, dest / entry['path'])
        pins[entry['path']] = entry['sha256']
    report = dict(status='ISOLATED_CLIENT_ASSEMBLED_NOT_LIVE_ACCEPTED', executable=str(exe),
        bootstrap=bootstrap, dll_sha256=digest(dll), visual_sha256=pins,
        client_data_sha256=data['output_sha256'], ui_shake='all game pixels; OS window remains fixed',
        launch=dict(locale_helper=str(ROOT.parent/'God2/compat-tools/LocaleEmulator/LEProc.exe'),
            arguments=['-run',str(exe),'127.0.0.1','127.0.0.1','6001','1'],working_directory=str(client)))
    (TRIAL / 'client-install.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(dict(status=report['status'], executable=str(exe)), ensure_ascii=False))

if __name__ == '__main__':
    main()
