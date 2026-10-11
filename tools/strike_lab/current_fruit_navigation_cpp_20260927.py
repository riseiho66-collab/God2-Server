"""Private standalone FruitNavigation gate; no shared build or DB mutation."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
ROOT=Path(__file__).resolve().parents[2]

def require(ok,message):
    if not ok:raise ValueError(message)

def main():
    out=ROOT/'artifacts/research/fruit-navigation-cpp-20260927';out.mkdir(parents=True,exist_ok=True)
    where=Path(os.environ.get('ProgramFiles(x86)','C:/Program Files (x86)'))/'Microsoft Visual Studio/Installer/vswhere.exe'
    install=subprocess.check_output([str(where),'-latest','-products','*','-requires','Microsoft.VisualStudio.Component.VC.Tools.x86.x64',
        '-property','installationPath'],text=True,timeout=30).strip();require(bool(install),'MSVC missing')
    setup=Path(install)/'VC/Auxiliary/Build/vcvars64.bat'
    setting=subprocess.check_output(f'cmd.exe /d /s /c ""{setup}" >nul && set"',text=True,timeout=30)
    env=dict(line.split('=',1) for line in setting.splitlines() if '=' in line and not line.startswith('='))
    cl=shutil.which('cl.exe',path=next(v for k,v in env.items() if k.lower()=='path'));require(bool(cl),'Compiler missing')
    common=[cl,'/nologo','/std:c++20','/EHsc','/W4','/WX','/I'+str(ROOT/'src'),'/I'+str(ROOT/'build/_deps/json-src/include')]
    log=[]
    def run(cmd):
        r=subprocess.run(cmd,cwd=out,env=env,capture_output=True,text=True,errors='replace',timeout=90)
        log.append({'command':list(map(str,cmd)),'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
        require(r.returncode==0,r.stdout+r.stderr)
    exe=out/'fruit-navigation.exe'
    run(common+[str(ROOT/'src/game/RecoveredFruitNavigation.cpp'),str(ROOT/'tests/test_recovered_fruit_navigation.cpp'),
        '/Fe:'+str(exe),'/Fo:'+str(out)+'/', '/link','bcrypt.lib'])
    # Compile only the changed integration translation unit; no shared .lib.
    run(common+['/c',str(ROOT/'src/handlers/RecoveredMovementService.cpp'),'/Fo:'+str(out/'movement.obj')])
    source=ROOT/'artifacts/world-atlas/fruit-13-12.json';run([str(exe),str(source)])
    original=source.read_bytes()
    for name,data in [('changed',original+b' '),('truncated',original[:-1]),('empty',b''),('oversized',b'X'*(1024*1024+1))]:
        fixture=out/(name+'.json');fixture.write_bytes(data);run([str(exe),'--reject',str(fixture)])
    run([str(exe),'--reject',str(out/'nonexistent.json')])
    result={'status':'PASS','source_sha256':hashlib.sha256(original).hexdigest(),'logs':log,
        'scope':'35721 cells+constructor/load equivalence, unknown/conflict/OOB fail closed, five source rejection cases, movement translation unit compile. Root owns DB/runtime integration tests.'}
    (out/'evidence.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':'PASS','commands':len(log),'output':str(out)}))
if __name__=='__main__':main()
