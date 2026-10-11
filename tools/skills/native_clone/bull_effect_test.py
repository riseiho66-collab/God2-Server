"""Build the actual backdrop recovery code against a fake COM surface (Win32)."""
from pathlib import Path
import os, shutil, subprocess, tempfile
ROOT=Path(__file__).resolve().parent
def main():
    vswhere=Path(os.environ.get('ProgramFiles(x86)','C:/Program Files (x86)'))/'Microsoft Visual Studio/Installer/vswhere.exe'
    installation=subprocess.check_output([str(vswhere),'-latest','-products','*','-requires','Microsoft.VisualStudio.Component.VC.Tools.x86.x64','-property','installationPath'],text=True).strip()
    vcvars=Path(installation)/'VC/Auxiliary/Build/vcvars32.bat'
    values=subprocess.check_output(f'cmd.exe /d /s /c ""{vcvars}" >nul && set"',text=True)
    env=dict(line.split('=',1) for line in values.splitlines() if '=' in line and not line.startswith('='))
    env['VSLANG']='1033'
    compiler=shutil.which('cl.exe',path=next(v for k,v in env.items() if k.lower()=='path'))
    with tempfile.TemporaryDirectory(prefix='god2-bull-test-') as tmp:
        subprocess.run([compiler,'/nologo','/std:c++20','/EHsc','/O2','/W4','/WX','/DWIN32_LEAN_AND_MEAN','/DNOMINMAX',str(ROOT/'bull_effect_test.cpp'),'/Fe:test.exe','winmm.lib'],cwd=tmp,env=env,check=True)
        subprocess.run([str(Path(tmp)/'test.exe'),str(ROOT.parents[2]/'artifacts/custom-skills/thousand-bulls/visualpack')],cwd=tmp,check=True)
if __name__=='__main__':main()
