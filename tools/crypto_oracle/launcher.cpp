#include <windows.h>
#include <iostream>
#include <string>

static std::wstring quote(const std::wstring& value) {
    std::wstring result=L"\"";
    std::size_t slashes=0;
    for(auto character:value) {
        if(character==L'\\') { ++slashes; continue; }
        result.append(character==L'"'?slashes*2+1:slashes,L'\\');
        result+=character;slashes=0;
    }
    result.append(slashes*2,L'\\');
    return result+L'"';
}

int wmain(int argc,wchar_t** argv) {
    std::wstring command=quote(ORACLE_PYTHON)+L" "+quote(ORACLE_SCRIPT);
    for(int i=1;i<argc;++i) command+=L" "+quote(argv[i]);
    STARTUPINFOW startup{};startup.cb=sizeof(startup);
    startup.dwFlags=STARTF_USESTDHANDLES;
    startup.hStdInput=GetStdHandle(STD_INPUT_HANDLE);
    startup.hStdOutput=GetStdHandle(STD_OUTPUT_HANDLE);
    startup.hStdError=GetStdHandle(STD_ERROR_HANDLE);
    PROCESS_INFORMATION process{};
    if(!CreateProcessW(ORACLE_PYTHON,command.data(),nullptr,nullptr,TRUE,CREATE_NO_WINDOW,
                       nullptr,nullptr,&startup,&process)) {
        std::wcerr<<L"Local oracle tool could not start: "<<GetLastError()<<L'\n';return 1;
    }
    CloseHandle(process.hThread);
    WaitForSingleObject(process.hProcess,INFINITE);
    DWORD status=1;GetExitCodeProcess(process.hProcess,&status);CloseHandle(process.hProcess);
    return static_cast<int>(status);
}
