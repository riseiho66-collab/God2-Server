#include <windows.h>
#include <cstring>
#include <iostream>

int wmain(int argc, wchar_t** argv) {
    if (argc != 2) return 1;
    auto module = LoadLibraryExW(argv[1], nullptr, LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR
                                               | LOAD_LIBRARY_SEARCH_DEFAULT_DIRS);
    if (!module) return 2;
    auto initialize = reinterpret_cast<DWORD(__cdecl*)()>(GetProcAddress(module, "God2LabInitialize"));
    auto status = reinterpret_cast<DWORD(__cdecl*)()>(GetProcAddress(module, "God2LabStatus"));
    auto state = reinterpret_cast<const char*(__cdecl*)()>(GetProcAddress(module, "God2LabGetState"));
    if (!initialize || !status || !state) { FreeLibrary(module); return 3; }
    const bool ok = status() == 0 && initialize() == 1 && status() == 1
        && std::strstr(state(), "\"internal_calls_enabled\":false")
        && std::strstr(state(), "LAB_AGENT_REFUSE_TO_START");
    FreeLibrary(module);
    std::cout << "Non-GOD2 host refusal: " << (ok ? "PASS" : "FAIL") << '\n';
    return ok ? 0 : 4;
}
