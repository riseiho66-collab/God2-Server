"""Compile the actual custom timeline against bounded native-call mocks."""
from pathlib import Path
import os,shutil,subprocess,tempfile
ROOT=Path(__file__).resolve().parent
def main():
    vswhere=Path(os.environ.get('ProgramFiles(x86)','C:/Program Files (x86)'))/'Microsoft Visual Studio/Installer/vswhere.exe'
    install=subprocess.check_output([str(vswhere),'-latest','-products','*','-requires','Microsoft.VisualStudio.Component.VC.Tools.x86.x64','-property','installationPath'],text=True).strip()
    vcvars=Path(install)/'VC/Auxiliary/Build/vcvars32.bat'
    values=subprocess.check_output(f'cmd.exe /d /s /c ""{vcvars}" >nul && set"',text=True)
    env=dict(x.split('=',1) for x in values.splitlines() if '=' in x and not x.startswith('='));env['VSLANG']='1033'
    compiler=shutil.which('cl.exe',path=next(v for k,v in env.items() if k.lower()=='path'))
    with tempfile.TemporaryDirectory(prefix='god2-bull-tick-') as tmp:
        subprocess.run([compiler,'/nologo','/std:c++17','/EHsc','/W4','/DWIN32_LEAN_AND_MEAN','/DNOMINMAX',str(ROOT/'bull_native_tick_test.cpp'),'/Fe:test.exe'],cwd=tmp,env=env,check=True)
        subprocess.run([str(Path(tmp)/'test.exe')],cwd=tmp,check=True)
if __name__=='__main__':main()
