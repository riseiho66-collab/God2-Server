"""Compile actual selector hooks against native callees mocked; no client writes."""
from pathlib import Path
import os,shutil,subprocess,tempfile

def main():
    root=Path(__file__).resolve().parent
    vswhere=Path(os.environ.get('ProgramFiles(x86)','C:/Program Files (x86)'))/'Microsoft Visual Studio/Installer/vswhere.exe'
    install=subprocess.check_output([str(vswhere),'-latest','-products','*','-requires','Microsoft.VisualStudio.Component.VC.Tools.x86.x64','-property','installationPath'],text=True).strip()
    vcvars=Path(install)/'VC/Auxiliary/Build/vcvars32.bat'
    values=subprocess.check_output(f'cmd.exe /d /s /c ""{vcvars}" >nul && set"',text=True)
    env=dict(line.split('=',1) for line in values.splitlines() if '=' in line and not line.startswith('='))
    env['VSLANG']='1033'
    compiler=shutil.which('cl.exe',path=next(v for k,v in env.items() if k.lower()=='path'))
    with tempfile.TemporaryDirectory(prefix='god2-selector-test-') as tmp:
        subprocess.run([compiler,'/nologo','/utf-8','/std:c++17','/EHsc','/W4','/WX',str(root/'target_selection_test.cpp'),'/Fe:test.exe','user32.lib'],cwd=tmp,env=env,check=True)
        subprocess.run([str(Path(tmp)/'test.exe')],cwd=tmp,check=True)
if __name__=='__main__':main()
