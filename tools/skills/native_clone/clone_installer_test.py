# Execute the real hook installer in an isolated Win32 memory fixture.
# Inject a cardinality static_assert only in a temporary copy. Historical
# 15-slot protection storage must fail compile; the current installer must run.
from pathlib import Path
import os, re, shutil, subprocess, tempfile, sys
sys.stdout.reconfigure(encoding="utf-8",errors="replace")
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[2]

def main():
    original=(ROOT/'clone_hooks.cpp').read_text(encoding='utf-8')
    marker=re.search(r'(std::array<DWORD,[^;]+>\s+protections\s*\{\};)',original)
    if not marker:raise AssertionError('Cannot instrument protection storage: inspect installer changes')
    instrumented=original[:marker.end()]+ '\n    static_assert(protections.size()==hooks.size(), "Installer protection storage must match every hook");'+original[marker.end():]
    negative=instrumented[:marker.start()]+'std::array<DWORD,15> protections{};'+instrumented[marker.end():]
    entries=re.findall(r'base\+(0x[0-9a-f]+)\),reinterpret_cast<void\*>\([^)]+\),(\d+),\{([^}]+)\}',original)
    if len(entries)<17:raise AssertionError('Current installer unexpectedly lost bull hooks')
    vswhere=Path(os.environ.get('ProgramFiles(x86)','C:/Program Files (x86)'))/'Microsoft Visual Studio/Installer/vswhere.exe'
    installation=subprocess.check_output([str(vswhere),'-latest','-products','*','-requires','Microsoft.VisualStudio.Component.VC.Tools.x86.x64','-property','installationPath'],text=True).strip()
    vcvars=Path(installation)/'VC/Auxiliary/Build/vcvars32.bat'
    values=subprocess.check_output(f'cmd.exe /d /s /c ""{vcvars}" >nul && set"',text=True)
    env=dict(line.split('=',1) for line in values.splitlines() if '=' in line and not line.startswith('='));env['VSLANG']='1033'
    compiler=shutil.which('cl.exe',path=next(v for k,v in env.items() if k.lower()=='path'))
    with tempfile.TemporaryDirectory(prefix='god2-installer-test-') as tmp:
        tmp=Path(tmp)
        preload=(ROOT/'clone_preload_test.cpp').read_text(encoding='utf-8')
        end=preload.rfind('}')
        (tmp/'clone_preload_test.cpp').write_text(preload[:end]+'return 0;\n'+preload[end:],encoding='utf-8')
        checks='\n'.join('    assert(fixture['+rva+']==0xe9);' for rva,_,_ in entries)
        source=r"""
#include <windows.h>
#include <fstream>
#include <cassert>
unsigned char* fixture{};
HMODULE WINAPI fixture_module(LPCWSTR name){assert(!name);return reinterpret_cast<HMODULE>(fixture);}
#define GetModuleHandleW fixture_module
#define main previous_preload_test_main
#include "clone_preload_test.cpp"
#undef main
#undef GetModuleHandleW
int main(int argc,char** argv){
 assert(argc==2);fixture=static_cast<unsigned char*>(VirtualAlloc(nullptr,0x190000,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE));assert(fixture);
 std::ifstream file(argv[1],std::ios::binary);file.read(reinterpret_cast<char*>(fixture),0x190000);assert(file);
 assert(install());
 auto* entry=reinterpret_cast<unsigned char*>(renderer_present_original);
 std::int32_t call_delta{},return_delta{};
 std::memcpy(&call_delta,entry+4,4);std::memcpy(&return_delta,entry+9,4);
 assert(entry[3]==0xe8 && entry+8+call_delta==fixture+0x3900);
 assert(entry[8]==0xe9 && entry+13+return_delta==fixture+0x32a28);
""" +checks+r"""
 std::cout<<"actual installer all hooks installed; protection cardinality statically verified\n";
}
"""
        (tmp/'installer.cpp').write_text(source,encoding='utf-8')
        args=[compiler,'/nologo','/utf-8','/std:c++20','/EHsc','/O2','/GS','/W4','/I'+str(ROOT),str(tmp/'installer.cpp'),'/Fe:hook_probe.exe','user32.lib']
        (tmp/'clone_hooks.cpp').write_text(negative,encoding='utf-8')
        result=subprocess.run(args,cwd=tmp,env=env,capture_output=True,text=True,errors='replace')
        if result.returncode==0 or 'Installer protection storage must match every hook' not in result.stdout+result.stderr:
            raise AssertionError('Historical15-slot bug was not rejected: '+result.stdout+result.stderr)
        print('Historical15-slot protection overflow: compile-time regression rejected')
        (tmp/'clone_hooks.cpp').write_text(instrumented,encoding='utf-8')
        result=subprocess.run(args,cwd=tmp,env=env,capture_output=True,text=True,errors='replace')
        print(result.stdout,result.stderr);result.check_returncode()
        subprocess.run([str(tmp/'hook_probe.exe'),str(REPO/'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin')],cwd=tmp,check=True)
if __name__=='__main__':main()
