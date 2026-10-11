#include <windows.h>
#include <dbgeng.h>
#include <array>
#include <cstring>
#include <cstdint>
#include "compat_bridge.h"

namespace {
DWORD owner = 0, original = 0, bridge = 0;
constexpr ULONG64 slot = 0x5707bc;
}

extern "C" __declspec(dllexport) HRESULT CALLBACK DebugExtensionInitialize(PULONG version, PULONG flags) {
    *version = DEBUG_EXTENSION_VERSION(1,0); *flags = 0; return S_OK;
}

extern "C" __declspec(dllexport) HRESULT CALLBACK install(PDEBUG_CLIENT client, PCSTR) {
    IDebugDataSpaces* data=nullptr; IDebugControl* control=nullptr;
    IDebugSystemObjects* systems=nullptr; IDebugSymbols* symbols=nullptr;
    if (FAILED(client->QueryInterface(__uuidof(IDebugControl),reinterpret_cast<void**>(&control)))) return E_FAIL;
    HRESULT hr=E_FAIL;
    HANDLE process=nullptr;
    void* allocation=nullptr;
    bool published=false;
    do {
        if (owner) break;
        if (FAILED(client->QueryInterface(__uuidof(IDebugDataSpaces),reinterpret_cast<void**>(&data)))) break;
        if (FAILED(client->QueryInterface(__uuidof(IDebugSystemObjects),reinterpret_cast<void**>(&systems)))) break;
        if (FAILED(client->QueryInterface(__uuidof(IDebugSymbols),reinterpret_cast<void**>(&symbols)))) break;
        ULONG pid=0, read=0; systems->GetCurrentProcessSystemId(&pid);
        std::array<unsigned char,5> check{};
        if (FAILED(data->ReadVirtual(0x45b662,check.data(),5,&read)) || read!=5 ||
            check!=std::array<unsigned char,5>{0x80,0x38,0x83,0x74,0x38}) break;
        DWORD target=0;
        if (FAILED(data->ReadVirtual(slot,&target,4,&read)) || read!=4) break;
        char name[256]{}; ULONG64 displacement=0;
        if (FAILED(symbols->GetNameByOffset(target,name,sizeof(name),nullptr,&displacement)) ||
            displacement!=0 || _stricmp(name,"winmm!timeGetTime")!=0) break;
        std::array<unsigned char,2> exportBytes{};
        if (FAILED(data->ReadVirtual(target,exportBytes.data(),2,&read)) || read!=2 ||
            exportBytes!=std::array<unsigned char,2>{0xff,0x25}) break;
        process=OpenProcess(PROCESS_VM_OPERATION|PROCESS_VM_WRITE|PROCESS_VM_READ|PROCESS_QUERY_INFORMATION,FALSE,pid);
        if (!process) break;
        wchar_t executable[1024]{}; DWORD executableLength=1024;
        if (!QueryFullProcessImageNameW(process,0,executable,&executableLength) ||
            _wcsicmp(executable,L"C:\\Users\\risei\\Desktop\\God2\\God2-Server\\artifacts\\capture_work\\host-20260918-1430\\client\\God2.exe")!=0) break;
        allocation=VirtualAllocEx(process,nullptr,4096,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE);
        auto address=reinterpret_cast<uintptr_t>(allocation);
        if (!allocation || address>0xfffff000ULL) break;
        // x86 no-argument stdcall tail bridge: unchanged ESP, return address and real API result.
        auto code=god2TimerBridge(static_cast<DWORD>(address),target);
        SIZE_T written=0;
        if (!WriteProcessMemory(process,allocation,code.data(),code.size(),&written) || written!=code.size()) break;
        DWORD previous=0;
        if (!VirtualProtectEx(process,allocation,4096,PAGE_EXECUTE_READ,&previous)) break;
        if (!FlushInstructionCache(process,allocation,code.size())) break;
        DWORD redirect=static_cast<DWORD>(address); ULONG count=0;
        if (FAILED(data->WriteVirtual(slot,&redirect,4,&count)) || count!=4) {
            data->WriteVirtual(slot,&target,4,&count); break;
        }
        published=true; owner=pid; original=target; bridge=redirect;
        DWORD verify=0;
        if (FAILED(data->ReadVirtual(slot,&verify,4,&read)) || read!=4 || verify!=bridge) break;
        control->Output(DEBUG_OUTPUT_NORMAL,"GOD2_COMPAT installed pid=%x slot=%x original=%x bridge=%x bytes=83ec00e9%02x%02x%02x%02x\n",
            owner,static_cast<ULONG>(slot),original,bridge,code[4],code[5],code[6],code[7]);
        hr=S_OK;
    } while(false);
    if (FAILED(hr)) {
        control->Output(DEBUG_OUTPUT_NORMAL,"GOD2_COMPAT REFUSED_OR_FAILED error=%lu published=%u\n",GetLastError(),published);
        if (published && data) { ULONG n=0; data->WriteVirtual(slot,&original,4,&n); }
        if (allocation && process) VirtualFreeEx(process,allocation,0,MEM_RELEASE);
        owner=original=bridge=0;
    }
    if (process) CloseHandle(process);
    if (symbols) symbols->Release(); if (systems) systems->Release(); if (data) data->Release();
    control->Release(); return hr;
}

extern "C" __declspec(dllexport) HRESULT CALLBACK restore(PDEBUG_CLIENT client, PCSTR) {
    IDebugDataSpaces* data=nullptr; IDebugControl* control=nullptr; IDebugSystemObjects* systems=nullptr;
    if (FAILED(client->QueryInterface(__uuidof(IDebugControl),reinterpret_cast<void**>(&control)))) return E_FAIL;
    HRESULT hr=E_FAIL;
    if (SUCCEEDED(client->QueryInterface(__uuidof(IDebugDataSpaces),reinterpret_cast<void**>(&data))) &&
        SUCCEEDED(client->QueryInterface(__uuidof(IDebugSystemObjects),reinterpret_cast<void**>(&systems)))) {
        ULONG pid=0,n=0; DWORD current=0; systems->GetCurrentProcessSystemId(&pid);
        if (owner && pid==owner && SUCCEEDED(data->ReadVirtual(slot,&current,4,&n)) && n==4 && current==bridge) {
            hr=data->WriteVirtual(slot,&original,4,&n);
            control->Output(DEBUG_OUTPUT_NORMAL,"GOD2_COMPAT restore pid=%x original=%x hr=%x written=%u\n",pid,original,hr,n);
            // Leave the private page until process exit: another thread may be inside it.
        }
    }
    if (systems) systems->Release(); if (data) data->Release(); control->Release(); return hr;
}
