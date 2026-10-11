#include "protocol/RecoveredBattleCommand.h"
#include <algorithm>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
#ifdef _WIN32
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#else
#include <sys/mman.h>
#include <unistd.h>
#endif

namespace {
using Codec = god2::RecoveredBattleCommand;
void require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}
void assertions() {
    std::array<std::uint8_t, 17> bytes{
        0x35,14,1,1,0xa5,1,0x20,1,0x20,0xef,0xcd,0xab,0x89,0x78,0x56,0x34,0x12};
    const auto result = Codec::parse_logical(bytes);
    require(result.has_value(), "Native basic-attack shape rejected");
    require(result->actor_position == 14 && result->side_flag == 1 &&
            result->unwritten_byte3 == 0xa5 && result->target_masks[0] == 0x2001 &&
            result->target_masks[1] == 0x2001 && result->context_storage == 0x89abcdef &&
            result->unwritten_parameter == 0x12345678, "Field width or offset changed");
    for (std::size_t length = 0; length < bytes.size(); ++length)
        require(!Codec::parse_logical(std::span(bytes).first(length)), "Truncation accepted");
    auto extra = std::vector<std::uint8_t>(bytes.begin(), bytes.end());
    extra.push_back(0);
    require(!Codec::parse_logical(extra), "Trailing byte accepted");
    for (const auto offset : {0u, 1u, 2u, 3u}) {
        auto bad = bytes;
        bad[offset] = 0xff;
        require(!Codec::parse_logical(bad), "Unsupported header shape accepted");
    }
    for (unsigned action = 0; action < 256; ++action) {
        auto changed = bytes;
        changed[2] = static_cast<std::uint8_t>(action);
        require(Codec::parse_logical(changed).has_value() == (action == 1),
                "Unqualified action or continuation accepted");
        require(Codec::parse_control_logical(changed).has_value() == (action == 0x0b),
                "Control action domain changed");
    }
    for (const auto offset : {6u, 8u}) {
        auto bad = bytes;
        bad[offset] |= 0x40;
        require(!Codec::parse_logical(bad), "Unsupported target bit accepted");
    }
    bytes[5] = 0xff; bytes[6] = 0x3f; bytes[7] = 0; bytes[8] = 0;
    require(Codec::parse_logical(bytes).has_value(), "Fourteen targets rejected");
    bytes[7] = 1;
    require(!Codec::parse_logical(bytes), "Fifteen distinct targets accepted");
    bytes[5] = bytes[6] = bytes[7] = bytes[8] = 0;
    require(Codec::parse_logical(bytes).has_value(), "Native empty mask rejected");
    require(!Codec::runtime_mutation_enabled, "Unexpected gameplay promotion");
}
std::vector<std::uint8_t> unhex(const std::string& text) {
    require(text.size() % 2 == 0, "Odd hex length");
    std::vector<std::uint8_t> bytes;
    constexpr char digits[] = "0123456789abcdef";
    for (std::size_t i = 0; i < text.size(); i += 2) {
        const auto high = std::string(digits).find(text[i]);
        const auto low = std::string(digits).find(text[i + 1]);
        require(high < 16 && low < 16, "Invalid hex");
        bytes.push_back(static_cast<std::uint8_t>(high * 16 + low));
    }
    return bytes;
}

class GuardedInput {
public:
    GuardedInput() {
#ifdef _WIN32
        SYSTEM_INFO info{};
        GetSystemInfo(&info);
        page_size_ = info.dwPageSize;
        allocation_ = static_cast<std::uint8_t*>(VirtualAlloc(
            nullptr, 3 * page_size_, MEM_RESERVE | MEM_COMMIT, PAGE_NOACCESS));
        require(allocation_ != nullptr, "VirtualAlloc failed");
#else
        const auto size = sysconf(_SC_PAGESIZE);
        require(size > 0, "Page size unavailable");
        page_size_ = static_cast<std::size_t>(size);
        auto* allocation = mmap(nullptr, 3 * page_size_, PROT_NONE,
                                MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
        require(allocation != MAP_FAILED, "mmap failed");
        allocation_ = static_cast<std::uint8_t*>(allocation);
#endif
    }
    ~GuardedInput() {
#ifdef _WIN32
        VirtualFree(allocation_, 0, MEM_RELEASE);
#else
        munmap(allocation_, 3 * page_size_);
#endif
    }
    GuardedInput(const GuardedInput&) = delete;
    GuardedInput& operator=(const GuardedInput&) = delete;

    std::span<const std::uint8_t> place(std::span<const std::uint8_t> bytes,
                                      bool at_end) {
        require(bytes.size() <= page_size_, "Guard input exceeds page");
        protect(true);
        auto* page = allocation_ + page_size_;
        std::memset(page, 0xcc, page_size_);
        auto* start = at_end ? page + page_size_ - bytes.size() : page;
        if (!bytes.empty()) std::memcpy(start, bytes.data(), bytes.size());
        protect(false);
        return {start, bytes.size()};
    }

private:
    void protect(bool writable) {
#ifdef _WIN32
        DWORD previous{};
        require(VirtualProtect(allocation_ + page_size_, page_size_,
                    writable ? PAGE_READWRITE : PAGE_READONLY, &previous) != 0,
                "VirtualProtect failed");
#else
        require(mprotect(allocation_ + page_size_, page_size_,
                    writable ? PROT_READ | PROT_WRITE : PROT_READ) == 0,
                "mprotect failed");
#endif
    }
    std::uint8_t* allocation_ = nullptr;
    std::size_t page_size_ = 0;
};

void require_lossless(const Codec::BasicAttackRequest& result,
                      std::span<const std::uint8_t> bytes) {
    std::array<std::uint8_t, Codec::logical_size> encoded{
        0x35, result.actor_position, 1, result.side_flag, result.unwritten_byte3};
    for (std::size_t group = 0; group < 2; ++group) {
        encoded[5 + group * 2] = static_cast<std::uint8_t>(result.target_masks[group]);
        encoded[6 + group * 2] = static_cast<std::uint8_t>(result.target_masks[group] >> 8);
    }
    for (std::size_t byte = 0; byte < 4; ++byte) {
        encoded[9 + byte] = static_cast<std::uint8_t>(result.context_storage >> (8 * byte));
        encoded[13 + byte] = static_cast<std::uint8_t>(result.unwritten_parameter >> (8 * byte));
    }
    require(std::equal(encoded.begin(), encoded.end(), bytes.begin(), bytes.end()),
            "Accepted basic attack lost or changed bytes");
}

void guarded_batch() {
    GuardedInput memory;
    std::size_t checks = 0;
    std::string line;
    require(!Codec::parse_logical({}), "Default empty span accepted");
    // Expectations arrive from the external native-seeded corpus. Both edges
    // are tested because an individual placement protects only one span edge.
    while (std::getline(std::cin, line)) {
        require(line.size() >= 2 && (line[0] == '0' || line[0] == '1') && line[1] == ' ',
                "Expected acceptance flag and logical hex");
        const auto bytes = unhex(line.substr(2));
        for (const bool at_end : {false, true}) {
            const auto input = memory.place(bytes, at_end);
            const auto result = Codec::parse_logical(input);
            if (result.has_value() != (line[0] == '1'))
                throw std::runtime_error("Guard expectation differs at check " +
                                         std::to_string(checks) + ": " + line);
            if (result) require_lossless(*result, bytes);
            ++checks;
        }
    }
    require(std::cin.eof() && checks != 0, "Missing or unreadable guard corpus");
    std::cout << "Guarded basic-attack checks passed: " << checks << '\n';
}
}
int main(int argc, char** argv) {
    try {
        assertions();
        if (argc == 2 && std::string(argv[1]) == "--guard-batch") {
            guarded_batch();
        } else if (argc == 3 && std::string(argv[1]) == "--decode") {
            const auto result = Codec::parse_logical(unhex(argv[2]));
            if (!result) { std::cout << "reject\n"; return 0; }
            std::cout << unsigned(result->actor_position) << ' ' << unsigned(result->side_flag)
                << ' ' << unsigned(result->unwritten_byte3) << ' ' << result->target_masks[0]
                << ' ' << result->target_masks[1] << ' ' << result->context_storage
                << ' ' << result->unwritten_parameter << '\n';
        } else {
            require(argc == 1, "Expected --decode logical_hex or --guard-batch");
            std::cout << "Recovered basic-attack assertions passed\n";
        }
    } catch (const std::exception& error) { std::cerr << error.what() << '\n'; return 1; }
}
