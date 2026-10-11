#pragma once

#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <atomic>
#include <cstddef>

namespace god2 { namespace native_lab {

enum class UnsafeReason : LONG {
    None, ExplicitSideEffect, WrongThread, ProtectionFailure, UnexpectedFault,
    InvalidPageState
};

// Windows x86 only. One initialized instance per module. All lifecycle calls
// and all arena access require the explicit owner thread; callers must ensure
// other threads cannot access the arena (including already-writable pages).
// This is memory rollback ONLY: no allocator, I/O, stack, register, game heap,
// or client-state rollback. Integrators must report side effects via MarkUnsafe.
class Transaction final {
public:
    static constexpr std::size_t kMaxPages = 64;
    Transaction() = default;
    ~Transaction();
    Transaction(const Transaction&) = delete;
    Transaction& operator=(const Transaction&) = delete;

    bool Initialize(std::size_t page_count, DWORD owner_thread_id);
    bool Begin();
    // Unsafe rollback still attempts arena cleanup, but returns false and
    // preserves the latch. Discard the experiment; never resume its execution.
    bool Rollback();
    bool Commit();
    bool Shutdown();
    void MarkUnsafe(UnsafeReason reason = UnsafeReason::ExplicitSideEffect);
    UnsafeReason unsafe_reason() const;
    bool active() const { return active_.load(std::memory_order_acquire); }
    void* data() const { return pages_; }
    std::size_t size() const { return count_ * page_size_; }
    std::size_t page_size() const { return page_size_; }
    std::size_t dirty_pages() const { return dirty_count_; }

private:
    static LONG CALLBACK HandleException(EXCEPTION_POINTERS* exception);
    bool Owner();
    bool Finish(bool restore);
    BYTE* pages_ = nullptr;
    BYTE* undo_ = nullptr;
    PVOID veh_ = nullptr;
    DWORD owner_ = 0;
    std::size_t count_ = 0;
    std::size_t page_size_ = 0;
    std::size_t dirty_count_ = 0;
    bool dirty_[kMaxPages] = {};
    // The processwide VEH can inspect this on non-owner threads.
    static_assert(std::atomic<bool>::is_always_lock_free,
        "VEH active flag must be lock-free");
    std::atomic<bool> active_{false};
    volatile LONG unsafe_ = 0;
};

}} // namespace god2::native_lab
