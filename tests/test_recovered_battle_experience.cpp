#include "protocol/RecoveredBattleExperience.h"
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <string>
#include <type_traits>
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
using Codec = god2::RecoveredBattleExperience;
static_assert(!std::is_default_constructible_v<Codec::Record>);
static_assert(std::is_same_v<decltype(std::declval<const Codec::Record&>()
    .character_received_exp_display()), std::uint32_t>);
static_assert(!Codec::runtime_emission_enabled && !Codec::runtime_mutation_enabled);

void require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
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

void assertions() {
    Codec::LogicalRecord seed;
    for (std::size_t i = 0; i < seed.size(); ++i)
        seed[i] = static_cast<std::uint8_t>(i * 73 + 19);
    seed[0] = Codec::opcode;
    const auto initial = Codec::parse_logical(seed);
    require(initial.has_value(), "Valid record rejected");
    const auto original = seed;
    seed.fill(0);
    require(Codec::encode_logical(*initial) == original, "Parser did not own input bytes");
    seed = original;

    GuardedInput memory;
    std::size_t checks = 0;
    const auto check = [&](std::span<const std::uint8_t> bytes, bool accepted) {
        for (bool at_end : {false, true}) {
            const auto input = memory.place(bytes, at_end);
            const auto result = Codec::parse_logical(input);
            require(result.has_value() == accepted, "Guarded acceptance differs");
            if (result) {
                const auto encoded = Codec::encode_logical(*result);
                require(std::equal(encoded.begin(), encoded.end(), input.begin(), input.end()),
                        "Logical roundtrip changed bytes");
                const auto reparsed = Codec::parse_logical(encoded);
                require(reparsed.has_value() && Codec::encode_logical(*reparsed) == encoded,
                        "Second roundtrip changed bytes");
            }
            ++checks;
        }
    };
    require(!Codec::parse_logical({}), "Empty span accepted");
    for (std::size_t begin = 0; begin <= seed.size(); ++begin)
        for (std::size_t end = begin; end <= seed.size(); ++end)
            check(std::span(seed).subspan(begin, end - begin),
                  begin == 0 && end == seed.size());
    std::vector<std::uint8_t> oversized(seed.begin(), seed.end());
    for (std::size_t size = 58; size <= 114; ++size) {
        oversized.push_back(seed[(size - 1) % seed.size()]);
        check(oversized, false);
    }
    // Exhaust every byte value at every position, including all opaque bytes.
    for (std::size_t offset = 0; offset < seed.size(); ++offset) {
        for (unsigned value = 0; value < 256; ++value) {
            auto changed = seed;
            changed[offset] = static_cast<std::uint8_t>(value);
            check(changed, offset != 0 || value == Codec::opcode);
        }
    }
    constexpr std::array<std::uint32_t, 6> values{
        0, 1, 0x12345678u, 0x7fffffffu, 0x80000000u, 0xffffffffu};
    for (std::size_t rotation = 0; rotation < values.size(); ++rotation) {
        auto changed = seed;
        constexpr std::array<std::size_t, 5> offsets{5, 9, 13, 53, 49};
        for (std::size_t field = 0; field < offsets.size(); ++field)
            for (std::size_t byte = 0; byte < 4; ++byte)
                changed[offsets[field] + byte] = static_cast<std::uint8_t>(
                    values[(rotation + field) % values.size()] >> (8 * byte));
        const auto result = Codec::parse_logical(changed);
        require(result.has_value(), "DWORD bit pattern rejected");
        const std::array<std::uint32_t, 5> actual{
            result->character_received_exp_display(), result->companion_received_exp_display(),
            result->pet_received_exp_display(), result->cave_received_exp_display(),
            result->branch_selector()};
        for (std::size_t field = 0; field < offsets.size(); ++field)
            require(actual[field] == values[(rotation + field) % values.size()],
                    "Unsigned field value, width or offset differs");
        check(changed, true);
    }
    std::cout << "Guarded battle-experience checks passed: " << checks << '\n';
}

std::vector<std::uint8_t> unhex(const std::string& text) {
    require(text.size() <= 4096 * 2 && text.size() % 2 == 0, "Invalid hex size");
    std::vector<std::uint8_t> bytes;
    const std::string digits = "0123456789abcdef";
    for (std::size_t i = 0; i < text.size(); i += 2) {
        const auto high = digits.find(text[i]);
        const auto low = digits.find(text[i + 1]);
        require(high < 16 && low < 16, "Invalid hex digit");
        bytes.push_back(static_cast<std::uint8_t>(high * 16 + low));
    }
    return bytes;
}

void batch() {
    std::string line;
    constexpr char digits[] = "0123456789abcdef";
    while (std::getline(std::cin, line)) {
        const auto result = Codec::parse_logical(unhex(line));
        if (!result) { std::cout << "reject\n"; continue; }
        const auto encoded = Codec::encode_logical(*result);
        for (const auto byte : encoded)
            std::cout << digits[byte >> 4] << digits[byte & 15];
        std::cout << ' ' << result->character_received_exp_display()
            << ' ' << result->companion_received_exp_display()
            << ' ' << result->pet_received_exp_display()
            << ' ' << result->cave_received_exp_display()
            << ' ' << result->branch_selector() << '\n';
    }
    require(std::cin.eof(), "Unreadable batch input");
}
}

int main(int argc, char** argv) {
    try {
        if (argc == 1) assertions();
        else {
            require(argc == 2 && std::string(argv[1]) == "--batch", "Expected --batch");
            batch();
        }
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
