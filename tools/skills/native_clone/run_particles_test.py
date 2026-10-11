"""Separate Win32 adapter ownership test; never opens or modifies the client."""
from pathlib import Path
import os,shutil,subprocess,tempfile,sys
sys.stdout.reconfigure(encoding='utf-8',errors='backslashreplace')
ROOT=Path(__file__).resolve().parent
vswhere=Path(os.environ.get('ProgramFiles(x86)','C:/Program Files (x86)'))/'Microsoft Visual Studio/Installer/vswhere.exe'
installation=subprocess.check_output([str(vswhere),'-latest','-products','*','-requires','Microsoft.VisualStudio.Component.VC.Tools.x86.x64','-property','installationPath'],text=True).strip()
vcvars=Path(installation)/'VC/Auxiliary/Build/vcvars32.bat'
values=subprocess.check_output(f'cmd.exe /d /s /c ""{vcvars}" >nul && set"',text=True)
env=dict(line.split('=',1) for line in values.splitlines() if '=' in line and not line.startswith('='));env['VSLANG']='1033'
compiler=shutil.which('cl.exe',path=next(v for k,v in env.items() if k.lower()=='path'))
output=ROOT.parents[2]/'artifacts/research/shunying-particle-qa-20260930'
output.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory(prefix='god2-clone-particles-test-') as tmp:
    run=subprocess.run([compiler,'/nologo','/utf-8','/std:c++17','/EHsc','/O2','/W4','/WX','/DSHUNYING_PARTICLE_TEST',str(ROOT/'clone_particles.cpp'),str(ROOT/'clone_particles_test.cpp'),'/Fe:particles_test.exe'],cwd=tmp,env=env,capture_output=True,text=True,errors='replace')
    print(run.stdout,run.stderr);run.check_returncode();subprocess.run([str(Path(tmp)/'particles_test.exe'),str(output)],cwd=tmp,check=True)
from PIL import Image
for path in output.glob('*.ppm'):
    Image.open(path).save(path.with_suffix('.png'))
print('Procedural pixel/palette QA:',output)
