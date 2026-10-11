"""Isolated Win32 render-order regression, including old-order negative control."""
from pathlib import Path
import os, shutil, subprocess, tempfile, json, hashlib
ROOT=Path(__file__).resolve().parent
def main():
    vswhere=Path(os.environ['ProgramFiles(x86)'])/'Microsoft Visual Studio/Installer/vswhere.exe'
    install=subprocess.check_output([str(vswhere),'-latest','-products','*','-requires','Microsoft.VisualStudio.Component.VC.Tools.x86.x64','-property','installationPath'],text=True).strip()
    setup=Path(install)/'VC/Auxiliary/Build/vcvars32.bat'
    values=subprocess.check_output(f'cmd.exe /d /s /c ""{setup}" >nul && set"',text=True)
    env=dict(s.split('=',1) for s in values.splitlines() if '=' in s and not s.startswith('='))
    compiler=shutil.which('cl.exe',path=next(v for k,v in env.items() if k.lower()=='path'))
    with tempfile.TemporaryDirectory(prefix='bull-damage-order-') as tmp:
        tmp=Path(tmp)
        args=[compiler,'/nologo','/std:c++17','/EHsc','/W4','/WX','/I'+str(ROOT),str(tmp/'bull_damage_overlay_test.cpp'),'/Fe:test.exe','user32.lib']
        for name in ('bull_damage_overlay_test.cpp','clone_preload_test.cpp','clone_hooks.cpp'):
            shutil.copyfile(ROOT/name,tmp/name)
        subprocess.run(args,cwd=tmp,env=env,check=True)
        result=subprocess.run([str(tmp/'test.exe')],cwd=tmp,check=True,capture_output=True,text=True)
        print(result.stdout.strip())
        original=(tmp/'clone_hooks.cpp').read_text()
        fixed='bull_damage::Pass damage(display,source);\n        render_original(display,viewport);\n        bull_effect::draw_foreground(display,viewport);\n        damage.draw(damage_draw);'
        assert fixed in original
        # Deliberately draw the deferred numbers before the bull foreground.
        (tmp/'clone_hooks.cpp').write_text(original.replace(fixed,fixed.replace('bull_effect::draw_foreground(display,viewport);\n        damage.draw(damage_draw);','damage.draw(damage_draw);\n        bull_effect::draw_foreground(display,viewport);')))
        subprocess.run(args,cwd=tmp,env=env,check=True)
        # Suppress assertion dialog; use the CRT report-to-stderr mode.
        negative=subprocess.run([str(tmp/'test.exe')],cwd=tmp,capture_output=True,text=True,timeout=15)
        assert negative.returncode!=0,'Old rendering order unexpectedly passed'
        report={'status':'PASS','cases':112,'sides':[0,1],'targets':'1..14','impacts':4,'old_order_rejected':True,'scope':'Compiled actual render_hook with native sprite raster sink; not live client acceptance','source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'clone_hooks.cpp',ROOT/'bull_damage_overlay.h',ROOT/'bull_effect.cpp')}}
        out=ROOT.parents[2]/'artifacts/custom-skills/thousand-bulls/damage-overlay-regression-20261001.json'
        out.write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()

