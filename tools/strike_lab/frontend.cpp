#include <windows.h>
#include <iostream>
#include <string>
#ifdef NATIVE_DIALOG
#include "native_dialog.h"
#endif

static std::wstring quote(const std::wstring& value) {
    std::wstring out = L"\"";
    size_t slashes = 0;
    for (wchar_t c : value) {
        if (c == L'\\') { ++slashes; continue; }
        out.append(c == L'"' ? slashes * 2 + 1 : slashes, L'\\');
        out += c;
        slashes = 0;
    }
    out.append(slashes * 2, L'\\');
    return out + L'"';
}

int wmain(int argc, wchar_t** argv) {
#ifdef NATIVE_DIALOG
    int nativeResult=nativeDialogMain(argc,argv);
    if(nativeResult>=0) return nativeResult;
#endif
    std::wstring command = quote(LAB_PYTHON) + L" " + quote(LAB_SCRIPT) + L" " + quote(LAB_TOOL);
    for (int i = 1; i < argc; ++i) command += L" " + quote(argv[i]);
    STARTUPINFOW startup{};
    startup.cb = sizeof(startup);
    PROCESS_INFORMATION process{};
    if (!CreateProcessW(LAB_PYTHON, command.data(), nullptr, nullptr, FALSE, 0, nullptr, nullptr, &startup, &process)) {
        std::wcerr << L"Lab backend launch failed: " << GetLastError() << L'\n';
        return 1;
    }
    CloseHandle(process.hThread);
    WaitForSingleObject(process.hProcess, INFINITE);
    DWORD status = 1;
    GetExitCodeProcess(process.hProcess, &status);
    CloseHandle(process.hProcess);
    return static_cast<int>(status);
}
