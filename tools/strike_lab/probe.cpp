#include <windows.h>
#include <dbgeng.h>
#include <nlohmann/json.hpp>

extern "C" __declspec(dllexport) HRESULT CALLBACK DebugExtensionInitialize(PULONG version, PULONG flags) {
    *version = DEBUG_EXTENSION_VERSION(1, 0);
    *flags = 0;
    return S_OK;
}

// Runs in the debugger host. No target writes, allocation, calls, or register changes.
extern "C" __declspec(dllexport) HRESULT CALLBACK snapshot(PDEBUG_CLIENT client, PCSTR) {
    IDebugControl* control = nullptr;
    IDebugDataSpaces* memory = nullptr;
    IDebugSystemObjects* systems = nullptr;
    IDebugRegisters* registers = nullptr;
    HRESULT hr = client->QueryInterface(__uuidof(IDebugControl), reinterpret_cast<void**>(&control));
    if (FAILED(hr)) return hr;
    hr = client->QueryInterface(__uuidof(IDebugDataSpaces), reinterpret_cast<void**>(&memory));
    if (SUCCEEDED(hr)) hr = client->QueryInterface(__uuidof(IDebugSystemObjects), reinterpret_cast<void**>(&systems));
    if (SUCCEEDED(hr)) hr = client->QueryInterface(__uuidof(IDebugRegisters), reinterpret_cast<void**>(&registers));
    if (SUCCEEDED(hr)) {
        ULONG pid = 0, tid = 0;
        ULONG machine = 0;
        control->GetEffectiveProcessorType(&machine);
        ULONG64 pc = 0, sp = 0;
        systems->GetCurrentProcessSystemId(&pid);
        systems->GetCurrentThreadSystemId(&tid);
        registers->GetInstructionOffset(&pc);
        registers->GetStackOffset(&sp);
        FILETIME timestamp{};
        GetSystemTimeAsFileTime(&timestamp);
        ULARGE_INTEGER ticks{};
        ticks.LowPart = timestamp.dwLowDateTime;
        ticks.HighPart = timestamp.dwHighDateTime;
        nlohmann::json value{{"event_type", "STRING_TABLE_SNAPSHOT"}, {"pid",pid}, {"tid",tid},
            {"pc",pc}, {"sp",sp}, {"timestamp_filetime",ticks.QuadPart}, {"object_base",0x5e053c},
            {"effective_machine",machine}, {"execution_mode_proof",false},
            {"count_offset",0xb2c64}, {"pointer_offset",0xb2c60}, {"identity", "FB72296_WORKING_COPY_CANDIDATE"}};
        for (auto [name, address, length] : {std::tuple{"count",0x6931a0ULL,2UL}, std::tuple{"pointer",0x69319cULL,4UL}}) {
            ULONG data = 0, read = 0;
            HRESULT readHr = memory->ReadVirtual(address, &data, length, &read);
            value[name] = SUCCEEDED(readHr) && read == length ? nlohmann::json(data) : nlohmann::json(nullptr);
        }
        control->Output(DEBUG_OUTPUT_NORMAL, "GOD2_PROBE %s\n", value.dump().c_str());
    }
    if (registers) registers->Release();
    if (systems) systems->Release();
    if (memory) memory->Release();
    control->Release();
    return hr;
}
