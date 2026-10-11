#include <windows.h>
#include <cwchar>
#include <cstdint>
#include <iterator>
#include <string>
#include <vector>
#include <iostream>

namespace {
std::wstring quote(const wchar_t* value) {
    // The current game parses its raw command line instead of using CRT argv.
    // Quoting arguments without whitespace changes that parser's result.
    if(wcspbrk(value,L" \t\r\n\"")==nullptr) return value;
    std::wstring result=L"\"";
    unsigned slashes=0;
    for(const wchar_t* p=value;*p;++p) {
        if(*p==L'\\') {++slashes;continue;}
        result.append(*p==L'"'?slashes*2+1:slashes,L'\\');
        result+=*p;slashes=0;
    }
    result.append(slashes*2,L'\\');
    return result+L'"';
}
std::wstring name(HDESK desktop) {
    DWORD bytes=0;
    GetUserObjectInformationW(desktop,UOI_NAME,nullptr,0,&bytes);
    if(!bytes) return {};
    std::wstring result(bytes/sizeof(wchar_t),L'\0');
    if(!GetUserObjectInformationW(desktop,UOI_NAME,result.data(),bytes,&bytes)) return {};
    result.resize(wcslen(result.c_str()));
    return result;
}
}

int wmain(int argc,wchar_t** argv) {
    if(argc<2) return 2;
    HDESK input=OpenInputDesktop(0,FALSE,DESKTOP_READOBJECTS);
    if(!input) return 3;
    const std::wstring before=name(input);
    CloseDesktop(input);
    if(before.empty()) return 4;
    const std::wstring private_name=L"God2Lab-"+std::to_wstring(GetCurrentProcessId())+L"-"+
        std::to_wstring(GetTickCount64());
    constexpr DWORD desktop_access=STANDARD_RIGHTS_REQUIRED|0x01ff;
    HDESK desktop=CreateDesktopW(private_name.c_str(),nullptr,nullptr,0,desktop_access,nullptr);
    if(!desktop) {std::wcerr<<L"CreateDesktop failed "<<GetLastError()<<L'\n';return 5;}
    const std::wstring desktop_path=L"WinSta0\\"+private_name;
    STARTUPINFOW startup{};startup.cb=sizeof(startup);
    startup.lpDesktop=const_cast<wchar_t*>(desktop_path.c_str());
    // Keep the console debugger's inherited pipe endpoints connected to the
    // Python driver while its child game window remains on the private desktop.
    startup.dwFlags=STARTF_USESTDHANDLES;
    startup.hStdInput=GetStdHandle(STD_INPUT_HANDLE);
    startup.hStdOutput=GetStdHandle(STD_OUTPUT_HANDLE);
    startup.hStdError=GetStdHandle(STD_ERROR_HANDLE);
    std::wstring command;
    for(int i=1;i<argc;++i) {if(i>1)command+=L' ';command+=quote(argv[i]);}
    PROCESS_INFORMATION child{};
    const bool trace_exceptions=GetEnvironmentVariableW(L"GOD2_PRIVATE_TRACE_EXCEPTIONS",nullptr,0)>0;
    if(!CreateProcessW(argv[1],command.data(),nullptr,nullptr,TRUE,CREATE_NO_WINDOW|
            (trace_exceptions?DEBUG_ONLY_THIS_PROCESS:0),
            nullptr,nullptr,&startup,&child)) {
        std::wcerr<<L"CreateProcess failed "<<GetLastError()<<L'\n';
        CloseDesktop(desktop);return 6;
    }
    CloseHandle(child.hThread);
    // A test-only observer may inspect windows on this same private desktop.
    // It never switches the input desktop used by the owner.
    wchar_t sidecar_command[32768]{};
    const DWORD sidecar_length=GetEnvironmentVariableW(L"GOD2_PRIVATE_SIDECAR_COMMAND",
        sidecar_command,static_cast<DWORD>(std::size(sidecar_command)));
    PROCESS_INFORMATION sidecar{};
    bool sidecar_started=false;
    if(sidecar_length && sidecar_length<std::size(sidecar_command)) {
        STARTUPINFOW observer_startup{};observer_startup.cb=sizeof(observer_startup);
        observer_startup.lpDesktop=const_cast<wchar_t*>(desktop_path.c_str());
        sidecar_started=CreateProcessW(nullptr,sidecar_command,nullptr,nullptr,FALSE,
            CREATE_NO_WINDOW,nullptr,nullptr,&observer_startup,&sidecar)!=FALSE;
        if(sidecar_started) CloseHandle(sidecar.hThread);
        else std::wcerr<<L"Private sidecar failed "<<GetLastError()<<L'\n';
    }
    if(trace_exceptions) {
        // Isolated child only. No breakpoints, memory writes, code injection,
        // or swallowed application exceptions. Log the actual fault address.
        DEBUG_EVENT event{};bool running=true;bool first_breakpoint=true;
        while(running && WaitForDebugEvent(&event,INFINITE)) {
            DWORD continuation=DBG_CONTINUE;
            if(event.dwDebugEventCode==EXCEPTION_DEBUG_EVENT) {
                const auto& detail=event.u.Exception;
                const auto& record=detail.ExceptionRecord;
                if(record.ExceptionCode==EXCEPTION_BREAKPOINT && first_breakpoint) first_breakpoint=false;
                else {
                    continuation=DBG_EXCEPTION_NOT_HANDLED;
                    std::cerr<<"CHILD_EXCEPTION code="<<std::hex<<record.ExceptionCode
                        <<" address="<<reinterpret_cast<std::uintptr_t>(record.ExceptionAddress)
                        <<" first_chance="<<std::dec<<detail.dwFirstChance;
                    for(DWORD i=0;i<record.NumberParameters;++i)
                        std::cerr<<" parameter"<<i<<"="<<std::hex<<record.ExceptionInformation[i];
                    std::cerr<<std::dec<<'\n'<<std::flush;
                    if(record.ExceptionCode==EXCEPTION_ACCESS_VIOLATION) {
                        HANDLE thread=OpenThread(THREAD_GET_CONTEXT,FALSE,event.dwThreadId);
                        WOW64_CONTEXT context{};context.ContextFlags=WOW64_CONTEXT_FULL;
                        if(thread && Wow64GetThreadContext(thread,&context)) {
                            std::cerr<<"CHILD_REGISTERS eax="<<std::hex<<context.Eax<<" ebx="<<context.Ebx
                                <<" ecx="<<context.Ecx<<" edx="<<context.Edx<<" esi="<<context.Esi
                                <<" edi="<<context.Edi<<" ebp="<<context.Ebp<<" esp="<<context.Esp<<'\n';
                            DWORD words[64]{};SIZE_T copied=0;
                            if(ReadProcessMemory(child.hProcess,reinterpret_cast<LPCVOID>(static_cast<std::uintptr_t>(context.Esp)),words,sizeof(words),&copied)) {
                                std::cerr<<"CHILD_STACK";for(const auto word:words) std::cerr<<' '<<word;std::cerr<<'\n';
                            }
                            DWORD maps[8]{};
                            if(ReadProcessMemory(child.hProcess,reinterpret_cast<LPCVOID>(0x5b6f70),maps,sizeof(maps),&copied)) {
                                std::cerr<<"CHILD_SKILL_ICON_MAP";for(const auto word:maps) std::cerr<<' '<<word;std::cerr<<'\n';
                            }
                            std::cerr<<std::dec<<std::flush;
                        }
                        if(thread) CloseHandle(thread);
                    }
                }
            } else if(event.dwDebugEventCode==CREATE_PROCESS_DEBUG_EVENT) {
                if(event.u.CreateProcessInfo.hFile) CloseHandle(event.u.CreateProcessInfo.hFile);
            } else if(event.dwDebugEventCode==LOAD_DLL_DEBUG_EVENT) {
                if(event.u.LoadDll.hFile) CloseHandle(event.u.LoadDll.hFile);
            } else if(event.dwDebugEventCode==EXIT_PROCESS_DEBUG_EVENT) running=false;
            ContinueDebugEvent(event.dwProcessId,event.dwThreadId,continuation);
        }
    } else WaitForSingleObject(child.hProcess,INFINITE);
    DWORD status=1;GetExitCodeProcess(child.hProcess,&status);
    CloseHandle(child.hProcess);
    if(sidecar_started) {
        wchar_t wait_text[16]{};
        DWORD wait_length=GetEnvironmentVariableW(L"GOD2_PRIVATE_SIDECAR_WAIT_MS",
            wait_text,static_cast<DWORD>(std::size(wait_text)));
        DWORD sidecar_wait=5000;
        if(wait_length&&wait_length<std::size(wait_text)) {
            wchar_t* end=nullptr;
            const unsigned long requested=wcstoul(wait_text,&end,10);
            if(end&&*end==0&&requested>=5000&&requested<=120000)
                sidecar_wait=static_cast<DWORD>(requested);
        }
        if(WaitForSingleObject(sidecar.hProcess,sidecar_wait)==WAIT_TIMEOUT)
            TerminateProcess(sidecar.hProcess,8);
        CloseHandle(sidecar.hProcess);
    }
    HDESK after_input=OpenInputDesktop(0,FALSE,DESKTOP_READOBJECTS);
    const std::wstring after=after_input?name(after_input):std::wstring{};
    if(after_input)CloseDesktop(after_input);
    CloseDesktop(desktop);
    if(after!=before) {std::wcerr<<L"Input desktop changed unexpectedly\n";return 7;}
    return static_cast<int>(status);
}
