#include "transaction.h"
#include <cstring>

static_assert(sizeof(void*) == 4, "Native transaction requires Windows x86");

namespace god2 { namespace native_lab {
namespace {
PVOID volatile instance = nullptr;
}

Transaction::~Transaction() {
    // A registered VEH must never outlive its object, even on misuse.
    if (!Shutdown()) RaiseFailFastException(nullptr, nullptr, 0);
}

void Transaction::MarkUnsafe(UnsafeReason reason) {
    if (reason == UnsafeReason::None) reason = UnsafeReason::ExplicitSideEffect;
    InterlockedCompareExchange(&unsafe_, static_cast<LONG>(reason), 0);
}

UnsafeReason Transaction::unsafe_reason() const {
    return static_cast<UnsafeReason>(InterlockedCompareExchange(
        const_cast<volatile LONG*>(&unsafe_), 0, 0));
}

bool Transaction::Owner() {
    if (GetCurrentThreadId() == owner_) return true;
    MarkUnsafe(UnsafeReason::WrongThread);
    return false;
}

bool Transaction::Initialize(std::size_t page_count, DWORD owner_thread_id) {
    if (pages_ || veh_ || page_count == 0 || page_count > kMaxPages ||
        owner_thread_id != GetCurrentThreadId() ||
        unsafe_reason() != UnsafeReason::None) return false;
    if (InterlockedCompareExchangePointer(&instance, this, nullptr)) return false;
    owner_ = owner_thread_id;
    SYSTEM_INFO info = {};
    GetSystemInfo(&info);
    page_size_ = info.dwPageSize;
    count_ = page_count;
    pages_ = static_cast<BYTE*>(VirtualAlloc(nullptr, size(),
        MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE));
    undo_ = static_cast<BYTE*>(VirtualAlloc(nullptr, size(),
        MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE));
    if (pages_ && undo_) {
        // Touch the entire undo allocation before any tracked page is protected.
        std::memset(undo_, 0, size());
        veh_ = AddVectoredExceptionHandler(1, HandleException);
    }
    if (!pages_ || !undo_ || !veh_) {
        Shutdown();
        return false;
    }
    return true;
}

bool Transaction::Begin() {
    if (!pages_ || !Owner() || active() ||
        unsafe_reason() != UnsafeReason::None) return false;
    for (std::size_t i = 0; i < count_; ++i) {
        MEMORY_BASIC_INFORMATION memory = {};
        if (!VirtualQuery(pages_ + i * page_size_, &memory, sizeof(memory)) ||
            memory.AllocationBase != pages_ || memory.State != MEM_COMMIT ||
            memory.Type != MEM_PRIVATE || memory.Protect != PAGE_READWRITE) {
            MarkUnsafe(UnsafeReason::InvalidPageState);
            return false;
        }
    }
    std::memset(dirty_, 0, sizeof(dirty_));
    dirty_count_ = 0;
    active_.store(true, std::memory_order_release);
    DWORD previous = 0;
    if (!VirtualProtect(pages_, size(), PAGE_READONLY, &previous)) {
        MarkUnsafe(UnsafeReason::ProtectionFailure);
        Finish(true);
        return false;
    }
    return true;
}

LONG CALLBACK Transaction::HandleException(EXCEPTION_POINTERS* exception) {
    auto* self = static_cast<Transaction*>(
        InterlockedCompareExchangePointer(&instance, nullptr, nullptr));
    if (!self || !exception || !exception->ExceptionRecord || !self->active())
        return EXCEPTION_CONTINUE_SEARCH;
    const auto* record = exception->ExceptionRecord;
    if (record->ExceptionCode != EXCEPTION_ACCESS_VIOLATION)
        return EXCEPTION_CONTINUE_SEARCH;
    const ULONG_PTR base = reinterpret_cast<ULONG_PTR>(self->pages_);
    const ULONG_PTR address = record->NumberParameters >= 2
        ? record->ExceptionInformation[1] : 0;
    const bool tracked = address >= base && address - base < self->size();
    if (GetCurrentThreadId() != self->owner_) {
        if (tracked) self->MarkUnsafe(UnsafeReason::WrongThread);
        return EXCEPTION_CONTINUE_SEARCH;
    }
    if (!tracked || record->NumberParameters < 2 ||
        record->ExceptionInformation[0] != 1) {
        self->MarkUnsafe(UnsafeReason::UnexpectedFault);
        return EXCEPTION_CONTINUE_SEARCH;
    }
    if (self->unsafe_reason() != UnsafeReason::None)
        return EXCEPTION_CONTINUE_SEARCH;
    const std::size_t index = (address - base) / self->page_size_;
    if (self->dirty_[index]) {
        self->MarkUnsafe(UnsafeReason::UnexpectedFault);
        return EXCEPTION_CONTINUE_SEARCH;
    }
    BYTE* page = self->pages_ + index * self->page_size_;
    // No allocation, locks, logging, or external callbacks in the VEH.
    std::memcpy(self->undo_ + index * self->page_size_, page, self->page_size_);
    self->dirty_[index] = true;
    ++self->dirty_count_;
    DWORD previous = 0;
    if (!VirtualProtect(page, self->page_size_, PAGE_READWRITE, &previous)) {
        self->MarkUnsafe(UnsafeReason::ProtectionFailure);
        return EXCEPTION_CONTINUE_SEARCH;
    }
    return EXCEPTION_CONTINUE_EXECUTION;
}

bool Transaction::Finish(bool restore) {
    if (!pages_ || !Owner() || !active()) return false;
    DWORD previous = 0;
    if (!VirtualProtect(pages_, size(), PAGE_READWRITE, &previous)) {
        MarkUnsafe(UnsafeReason::ProtectionFailure);
        return false;
    }
    if (restore) {
        for (std::size_t i = 0; i < count_; ++i)
            if (dirty_[i]) std::memcpy(pages_ + i * page_size_,
                undo_ + i * page_size_, page_size_);
    }
    active_.store(false, std::memory_order_release);
    return unsafe_reason() == UnsafeReason::None;
}

bool Transaction::Rollback() { return Finish(true); }

bool Transaction::Commit() {
    if (unsafe_reason() != UnsafeReason::None) return false;
    return Finish(false);
}

bool Transaction::Shutdown() {
    if (!pages_ && !undo_ && !veh_) {
        InterlockedCompareExchangePointer(&instance, nullptr, this);
        return true;
    }
    if (!Owner()) return false;
    if (active()) {
        Finish(true);
        if (active()) return false;
    }
    if (veh_ && !RemoveVectoredExceptionHandler(veh_)) return false;
    veh_ = nullptr;
    InterlockedCompareExchangePointer(&instance, nullptr, this);
    if (undo_ && !VirtualFree(undo_, 0, MEM_RELEASE)) return false;
    undo_ = nullptr;
    if (pages_ && !VirtualFree(pages_, 0, MEM_RELEASE)) return false;
    pages_ = nullptr;
    count_ = 0;
    return true;
}

}} // namespace god2::native_lab
