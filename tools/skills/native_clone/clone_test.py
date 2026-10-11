"""Build/run a separate Win32 fake-renderer regression; no game/process writes."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import sys
sys.stdout.reconfigure(encoding='utf-8',errors='backslashreplace')

ROOT=Path(__file__).resolve().parent

def main():
    vswhere=Path(os.environ.get('ProgramFiles(x86)','C:/Program Files (x86)'))/'Microsoft Visual Studio/Installer/vswhere.exe'
    installation=subprocess.check_output([str(vswhere),'-latest','-products','*','-requires','Microsoft.VisualStudio.Component.VC.Tools.x86.x64','-property','installationPath'],text=True).strip()
    vcvars=Path(installation)/'VC/Auxiliary/Build/vcvars32.bat'
    values=subprocess.check_output(f'cmd.exe /d /s /c ""{vcvars}" >nul && set"',text=True)
    env=dict(line.split('=',1) for line in values.splitlines() if '=' in line and not line.startswith('='))
    env['VSLANG']='1033'
    path=next(v for k,v in env.items() if k.lower()=='path')
    compiler=shutil.which('cl.exe',path=path)
    with tempfile.TemporaryDirectory(prefix='god2-clone-native-test-') as tmp:
        run=subprocess.run([compiler,'/nologo','/utf-8','/std:c++17','/EHsc','/W4','/WX','/DSHUNYING_CLONE_TEST',str(ROOT/'clone_visuals.cpp'),str(ROOT/'clone_visuals_test.cpp'),'/Fe:clone_test.exe'],cwd=tmp,env=env,capture_output=True,text=True,errors='replace')
        print(run.stdout,run.stderr)
        run.check_returncode()
        subprocess.run([str(Path(tmp)/'clone_test.exe')],cwd=tmp,check=True)

if __name__=='__main__':main()
