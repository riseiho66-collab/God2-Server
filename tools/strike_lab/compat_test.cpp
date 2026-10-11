#include <windows.h>
#include <mmsystem.h>
#include <iostream>
#include "compat_bridge.h"

int main() {
    if (sizeof(void*)!=4) { std::cerr<<"Build this ABI test for Win32.\n"; return 2; }
    auto memory=VirtualAlloc(nullptr,4096,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE);
    if (!memory) return 1;
    auto target=GetProcAddress(GetModuleHandleW(L"winmm.dll"),"timeGetTime");
    if (!target) { VirtualFree(memory,0,MEM_RELEASE); return 1; }
    auto code=god2TimerBridge(static_cast<std::uint32_t>(reinterpret_cast<uintptr_t>(memory)),
        static_cast<std::uint32_t>(reinterpret_cast<uintptr_t>(target)));
    std::memcpy(memory,code.data(),code.size());
    DWORD old=0;
    if (!VirtualProtect(memory,4096,PAGE_EXECUTE_READ,&old) || !FlushInstructionCache(GetCurrentProcess(),memory,code.size())) {
        VirtualFree(memory,0,MEM_RELEASE); return 1;
    }
    auto bridge=reinterpret_cast<DWORD (WINAPI*)()>(memory);
    for (int i=0;i<5000;++i) {
        DWORD before=timeGetTime(),value=bridge(),after=timeGetTime();
        if (value-before>after-before) { VirtualFree(memory,0,MEM_RELEASE); return 1; }
    }
    VirtualFree(memory,0,MEM_RELEASE);
    std::cout<<"PASS: 5000 x86 stdcall tail calls, real timeGetTime bounds, unchanged return-address convention.\n";
    return 0;
}
