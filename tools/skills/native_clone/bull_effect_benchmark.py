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
    with tempfile.TemporaryDirectory(prefix='god2-bull-perf-') as tmp:
        source=Path(tmp)/'benchmark.cpp'
        prefix=(ROOT/'bull_effect_test.cpp').read_text().split('int main(')[0]
        prefix=prefix.replace('std::array<Byte,64> pixels{}','std::vector<Byte> pixels=std::vector<Byte>(800*600*2)')
        prefix=prefix.replace('d->dwWidth=5;d->dwHeight=3;d->lPitch=f.negative?-16:16','d->dwWidth=800;d->dwHeight=600;d->lPitch=1600')
        prefix=prefix.replace('+(f.negative?32:0)','')
        source.write_text(prefix+r'''
#include <chrono>
int main(int,char** argv){
 std::array<void*,45> table{};table[1]=reinterpret_cast<void*>(ref_fake);table[2]=reinterpret_cast<void*>(ref_fake);table[25]=reinterpret_cast<void*>(lock_fake);table[32]=reinterpret_cast<void*>(unlock_fake);Fake f{};f.table=table.data();
 std::array<Byte,0xc0> renderer{},cdx{};void* display=reinterpret_cast<void*>(123);put(renderer,0xa0,cdx.data());put(renderer,0xa8,display);put(cdx,0x80,&f);
 cast.war=reinterpret_cast<void*>(234);cast.display=display;cast.started=cast.ready=true;cast.start=100;drawing_renderer=renderer.data();
 auto dir=std::filesystem::path(argv[1]);assert(cast.ground.open((dir/L"player-ground.bfx").wstring()));assert(cast.foreground.open((dir/L"player-foreground.bfx").wstring()));
 double draw=0,shake=0,maxdraw=0,maxshake=0;unsigned frames=0;
 for(unsigned tick=25;tick<233;++tick){cast.tick=tick;cast.shake[tick*2]=4;cast.shake[tick*2+1]=3;
  auto a=std::chrono::steady_clock::now();draw_ground(display,0);draw_foreground(display,0);auto b=std::chrono::steady_clock::now();before_present(renderer.data());after_present();auto c=std::chrono::steady_clock::now();
  auto d=std::chrono::duration<double,std::milli>(b-a).count(),s=std::chrono::duration<double,std::milli>(c-b).count();draw+=d;shake+=s;maxdraw=std::max(maxdraw,d);maxshake=std::max(maxshake,s);++frames;
 }
 std::cout<<"actual Pack decode+paint avg_ms="<<draw/frames<<" max_ms="<<maxdraw<<" whole UI shake avg_ms="<<shake/frames<<" max_ms="<<maxshake<<" frames="<<frames<<"\n";
}
''',encoding='utf-8')
        subprocess.run([compiler,'/nologo','/std:c++20','/EHsc','/O2','/DWIN32_LEAN_AND_MEAN','/DNOMINMAX','/I'+str(ROOT),str(source),'/Fe:test.exe','winmm.lib'],cwd=tmp,env=env,check=True)
        subprocess.run([str(Path(tmp)/'test.exe'),str(ROOT.parents[2]/'artifacts/custom-skills/thousand-bulls/visualpack')],cwd=tmp,check=True)
if __name__=='__main__':main()
