#include "transaction.h"
#include <cstdio>
#include <cstring>
#include <vector>

using god2::native_lab::Transaction;
using god2::native_lab::UnsafeReason;

#define CHECK(condition) do { if (!(condition)) { \
    std::fprintf(stderr, "FAIL line %d: %s\n", __LINE__, #condition); return 1; \
} } while (0)

// Synthetic known mutation handler. No client code, allocations, or I/O.
static bool SyntheticHandler(volatile BYTE* data, std::size_t page_size, BYTE input) {
    data[3] = static_cast<BYTE>(data[3] + input);
    data[3] ^= 0x5a;
    data[2 * page_size + 17] = static_cast<BYTE>(input ^ 0xa5);
    return (input & 1) == 0;
}

static DWORD WINAPI WrongOwner(void* argument) {
    return static_cast<Transaction*>(argument)->Begin() ? 1 : 0;
}

// SEH confirms foreign faults are propagated, not consumed by the VEH.
static bool ForeignWrite(volatile BYTE* foreign) {
    __try { *foreign = 1; }
    __except (GetExceptionCode() == EXCEPTION_ACCESS_VIOLATION
        ? EXCEPTION_EXECUTE_HANDLER : EXCEPTION_CONTINUE_SEARCH) { return true; }
    return false;
}

int main() {
    Transaction tx;
    CHECK(!tx.Initialize(0, GetCurrentThreadId()));
    CHECK(!tx.Initialize(Transaction::kMaxPages + 1, GetCurrentThreadId()));
    CHECK(tx.Initialize(3, GetCurrentThreadId()));
    Transaction second;
    CHECK(!second.Initialize(1, GetCurrentThreadId()));
    auto* data = static_cast<BYTE*>(tx.data());
    std::memset(data, 0x31, tx.size());
    std::vector<BYTE> baseline(data, data + tx.size());
    LARGE_INTEGER frequency = {}, start = {}, end = {};
    QueryPerformanceFrequency(&frequency);
    QueryPerformanceCounter(&start);
    constexpr unsigned iterations = 256;
    for (unsigned i = 0; i < iterations; ++i) {
        const BYTE input = static_cast<BYTE>(i);
        std::vector<BYTE> expected = baseline;
        expected[3] = static_cast<BYTE>((0x31 + input) ^ 0x5a);
        expected[2 * tx.page_size() + 17] = static_cast<BYTE>(input ^ 0xa5);
        // Repeat each accepted/rejected candidate from an identical baseline.
        for (unsigned repeat = 0; repeat < 2; ++repeat) {
            CHECK(tx.Begin());
            CHECK(!tx.Begin());
            CHECK(tx.dirty_pages() == 0);
            CHECK(data[3] == 0x31 && tx.dirty_pages() == 0);
            CHECK(SyntheticHandler(data, tx.page_size(), input) == ((i & 1) == 0));
            CHECK(tx.dirty_pages() == 2);
            CHECK(std::memcmp(data, expected.data(), tx.size()) == 0);
            CHECK(tx.Rollback());
            CHECK(std::memcmp(data, baseline.data(), tx.size()) == 0);
        }
    }
    QueryPerformanceCounter(&end);
    CHECK(tx.Begin());
    CHECK(tx.Commit());
    CHECK(tx.Begin());
    SyntheticHandler(data, tx.page_size(), 42);
    std::vector<BYTE> committed(data, data + tx.size());
    CHECK(tx.Commit());
    CHECK(tx.Begin());
    SyntheticHandler(data, tx.page_size(), 17);
    CHECK(tx.Rollback());
    CHECK(std::memcmp(data, committed.data(), tx.size()) == 0);
    CHECK(tx.Begin());
    SyntheticHandler(data, tx.page_size(), 3);
    tx.MarkUnsafe();
    CHECK(!tx.Commit());
    CHECK(!tx.Rollback());
    CHECK(!tx.active());
    CHECK(std::memcmp(data, committed.data(), tx.size()) == 0);
    CHECK(!tx.Begin());
    CHECK(tx.Shutdown());
    CHECK(!tx.Initialize(1, GetCurrentThreadId()));

    Transaction foreign_test;
    CHECK(foreign_test.Initialize(1, GetCurrentThreadId()));
    auto* foreign = static_cast<BYTE*>(VirtualAlloc(nullptr, 4096,
        MEM_RESERVE | MEM_COMMIT, PAGE_READONLY));
    CHECK(foreign != nullptr);
    CHECK(foreign_test.Begin());
    CHECK(ForeignWrite(foreign));
    CHECK(foreign_test.unsafe_reason() == UnsafeReason::UnexpectedFault);
    CHECK(!foreign_test.Rollback());
    CHECK(!foreign_test.Begin());
    CHECK(VirtualFree(foreign, 0, MEM_RELEASE));
    CHECK(foreign_test.Shutdown());

    Transaction thread_test;
    CHECK(thread_test.Initialize(1, GetCurrentThreadId()));
    HANDLE thread = CreateThread(nullptr, 0, WrongOwner, &thread_test, 0, nullptr);
    CHECK(thread != nullptr);
    CHECK(WaitForSingleObject(thread, 10000) == WAIT_OBJECT_0);
    DWORD result = 1;
    CHECK(GetExitCodeThread(thread, &result) && result == 0);
    CHECK(CloseHandle(thread));
    CHECK(thread_test.unsafe_reason() == UnsafeReason::WrongThread);
    CHECK(!thread_test.Begin());
    CHECK(thread_test.Shutdown());
    const double seconds = static_cast<double>(end.QuadPart - start.QuadPart) /
        static_cast<double>(frequency.QuadPart);
    std::printf("SYNTHETIC_ONLY PASS: %u deterministic candidates, %.1f candidates/sec\n"
        "Includes verification overhead; client restart comparison NOT measured.\n"
        "No client invocation or client certification.\n", iterations * 2,
        iterations * 2 / seconds);
    return 0;
}
