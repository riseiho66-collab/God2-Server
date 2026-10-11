#include <windows.h>
#include <bcrypt.h>
#include <array>
#include <atomic>
#include <cstdint>
#include <string>
#include <vector>

static_assert(sizeof(void*) == 4, "LabAgent is x86 only");

namespace {
enum Status : DWORD { NotInitialized, PathMismatch, FileHashMismatch,
    ImageMismatch, CodeMismatch, LayoutAndActionUnproven, InternalError };
std::atomic<DWORD> status{NotInitialized};
SRWLOCK guard = SRWLOCK_INIT;
constexpr char executableHash[] =
    "fb72296cab5950b74d8f7c98155145f7c5f58749c3011adb0540325b60749dd1";

struct Hash {
    BCRYPT_ALG_HANDLE algorithm{};
    BCRYPT_HASH_HANDLE hash{};
    std::vector<unsigned char> object;
    Hash() {
        DWORD length{}, returned{};
        if (BCryptOpenAlgorithmProvider(&algorithm, BCRYPT_SHA256_ALGORITHM, nullptr, 0) < 0
            || BCryptGetProperty(algorithm, BCRYPT_OBJECT_LENGTH,
                reinterpret_cast<PUCHAR>(&length), sizeof(length), &returned, 0) < 0)
            return;
        object.resize(length);
        if (BCryptCreateHash(algorithm, &hash, object.data(), length, nullptr, 0, 0) < 0)
            hash = nullptr;
    }
    ~Hash() {
        if (hash) BCryptDestroyHash(hash);
        if (algorithm) BCryptCloseAlgorithmProvider(algorithm, 0);
    }
    bool add(const unsigned char* bytes, DWORD size) {
        return hash && BCryptHashData(hash, const_cast<PUCHAR>(bytes), size, 0) >= 0;
    }
    std::string finish() {
        std::array<unsigned char, 32> result{};
        if (!hash || BCryptFinishHash(hash, result.data(), DWORD(result.size()), 0) < 0)
            return {};
        constexpr char hex[] = "0123456789abcdef";
        std::string value;
        for (auto byte : result) { value += hex[byte >> 4]; value += hex[byte & 15]; }
        return value;
    }
};

DWORD verify() {
    wchar_t current[32768]{}, expected[32768]{};
    const auto length = GetModuleFileNameW(nullptr, current, DWORD(std::size(current)));
    const auto expectedLength = GetFullPathNameW(GOD2_LAB_WORKING_COPY,
        DWORD(std::size(expected)), expected, nullptr);
    if (!length || length >= std::size(current) || !expectedLength
        || expectedLength >= std::size(expected) || _wcsicmp(current, expected))
        return PathMismatch;
    // No write/delete sharing while the original-file identity is checked.
    HANDLE file = CreateFileW(current, GENERIC_READ, FILE_SHARE_READ, nullptr,
                              OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (file == INVALID_HANDLE_VALUE) return FileHashMismatch;
    Hash hash;
    std::array<unsigned char, 16384> bytes{};
    DWORD count{};
    bool ok = true;
    while (true) {
        if (!ReadFile(file, bytes.data(), DWORD(bytes.size()), &count, nullptr)) { ok = false; break; }
        if (!count) break;
        if (!hash.add(bytes.data(), count)) { ok = false; break; }
    }
    CloseHandle(file);
    if (!ok || hash.finish() != executableHash) return FileHashMismatch;
    const auto base = reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
    if (base != 0x400000) return ImageMismatch;
    struct Pin { std::uintptr_t rva; const char* sha; };
    constexpr Pin pins[] = {
        {0x12506, "07d1ad5d1659874a49b59de6ce1904549bc20ad60447faa9020c9cf9daae54b6"},
        {0x147d0, "8b7cec073bedddeb892341c472c6545eccd3cf29660b29d8d80e7d3154c6c073"},
        {0xb490, "45c5736f1854e1505662b57be4e8951b98057c34a18cdedf60006edc976b4991"},
        {0x7030, "a014d60a5fa01f01f53f133919c51d688cb790e6d765dd81372baeb200042a07"}
    };
    for (const auto& pin : pins) {
        std::array<unsigned char, 16> code{};
        SIZE_T read{};
        if (!ReadProcessMemory(GetCurrentProcess(), reinterpret_cast<void*>(base + pin.rva),
                               code.data(), code.size(), &read) || read != code.size())
            return CodeMismatch;
        Hash codeHash;
        if (!codeHash.add(code.data(), DWORD(code.size())) || codeHash.finish() != pin.sha)
            return CodeMismatch;
    }
    // Passing byte pins is not proof of object lifetime, thread affinity,
    // action equivalence, allocator closure or reversible side effects.
    return LayoutAndActionUnproven;
}
}

extern "C" __declspec(dllexport) DWORD __cdecl God2LabInitialize() noexcept {
    AcquireSRWLockExclusive(&guard);
    try { status.store(verify()); } catch (...) { status.store(InternalError); }
    ReleaseSRWLockExclusive(&guard);
    return status.load();
}

extern "C" __declspec(dllexport) DWORD __cdecl God2LabStatus() noexcept {
    return status.load();
}

extern "C" __declspec(dllexport) const char* __cdecl God2LabGetState() noexcept {
    return "{\"lane\":\"LAB_ONLY\",\"internal_calls_enabled\":false,"
           "\"transaction_client_enabled\":false,\"action_equivalent\":false,"
           "\"status\":\"LAB_AGENT_REFUSE_TO_START\"}";
}

// Explicit initialization is outside loader lock. Loading has no hooks,
// process injection, threads, IPC, UI or network effects.
BOOL WINAPI DllMain(HINSTANCE, DWORD, LPVOID) { return TRUE; }
