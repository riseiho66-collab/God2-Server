#pragma once
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <span>
#include <stdexcept>
#ifdef _WIN32
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#else
#include <sys/mman.h>
#include <unistd.h>
#endif

// Inventory fixture only: a read-only record abutting either inaccessible page.
class InventoryGuardedRecord {
public:
    InventoryGuardedRecord(std::span<const std::uint8_t> bytes, bool at_end) {
#ifdef _WIN32
        SYSTEM_INFO info{};
        GetSystemInfo(&info);
        page_size_ = info.dwPageSize;
#else
        const auto page_size = sysconf(_SC_PAGESIZE);
        if (page_size <= 0) throw std::runtime_error("Cannot query page size");
        page_size_ = static_cast<std::size_t>(page_size);
#endif
        if (bytes.size() > page_size_)
            throw std::runtime_error("Inventory fixture exceeds one page");
#ifdef _WIN32
        memory_ = static_cast<std::uint8_t*>(VirtualAlloc(
            nullptr, 3 * page_size_, MEM_RESERVE | MEM_COMMIT, PAGE_NOACCESS));
        if (!memory_) throw std::runtime_error("Cannot allocate guard pages");
        DWORD previous = 0;
        if (!VirtualProtect(memory_ + page_size_, page_size_, PAGE_READWRITE, &previous))
            fail();
#else
        auto* allocation = mmap(nullptr, 3 * page_size_, PROT_NONE,
                                MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
        if (allocation == MAP_FAILED) throw std::runtime_error("Cannot allocate guard pages");
        memory_ = static_cast<std::uint8_t*>(allocation);
        if (mprotect(memory_ + page_size_, page_size_, PROT_READ | PROT_WRITE) != 0)
            fail();
#endif
        auto* record = memory_ + page_size_ + (at_end ? page_size_ - bytes.size() : 0);
        if (!bytes.empty()) std::memcpy(record, bytes.data(), bytes.size());
#ifdef _WIN32
        if (!VirtualProtect(memory_ + page_size_, page_size_, PAGE_READONLY, &previous))
            fail();
#else
        if (mprotect(memory_ + page_size_, page_size_, PROT_READ) != 0) fail();
#endif
        record_ = {record, bytes.size()};
    }

    ~InventoryGuardedRecord() { release(); }
    InventoryGuardedRecord(const InventoryGuardedRecord&) = delete;
    InventoryGuardedRecord& operator=(const InventoryGuardedRecord&) = delete;
    std::span<const std::uint8_t> bytes() const noexcept { return record_; }

private:
    void release() noexcept {
#ifdef _WIN32
        VirtualFree(memory_, 0, MEM_RELEASE);
#else
        munmap(memory_, 3 * page_size_);
#endif
    }
    [[noreturn]] void fail() {
        release();
        throw std::runtime_error("Cannot protect inventory guard pages");
    }
    std::uint8_t* memory_ = nullptr;
    std::size_t page_size_ = 0;
    std::span<const std::uint8_t> record_;
};
