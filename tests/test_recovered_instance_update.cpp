#include "protocol/RecoveredInstanceUpdate.h"
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <utility>
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
using Codec = god2::RecoveredInstanceUpdate;
using Record = Codec::Record;
static_assert(!std::is_default_constructible_v<Record>);
static_assert(!std::is_constructible_v<Record, Codec::LogicalRecord>);
static_assert(!Codec::runtime_emission_enabled && !Codec::runtime_mutation_enabled);
static_assert(std::is_same_v<decltype(std::declval<const Record&>().slot()), std::int8_t>);
static_assert(std::is_same_v<decltype(std::declval<const Record&>().opaque_instance()),
    std::span<const std::uint8_t, 20>>);
static_assert(std::is_same_v<decltype(std::declval<const Record&>().raw_category_bits()),
    std::uint8_t>);
static_assert(std::is_same_v<decltype(std::declval<const Record&>().low_word_lookup_key()),
    std::uint16_t>);
static_assert(std::is_same_v<decltype(std::declval<const Record&>().raw_instance_word8()),
    std::uint16_t>);
static_assert(std::is_same_v<decltype(std::declval<const Record&>().raw_packed_dword_c()),
    std::uint32_t>);

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

void check_accessors(const Record& record, std::span<const std::uint8_t> bytes) {
    require(record.slot() == bytes[2], "Slot differs");
    require(record.raw_category_bits() == (bytes[7] & 63), "Category bits differ");
    require(record.low_word_lookup_key() == bytes[5] + 256u * bytes[6],
            "Lookup WORD differs");
    require(record.raw_instance_word8() == bytes[13] + 256u * bytes[14],
            "Instance WORD +8 differs");
    require(record.raw_packed_dword_c() == bytes[17] + 256u * bytes[18] +
            65536u * bytes[19] + 16777216u * bytes[20], "Packed DWORD +C differs");
    const auto category = bytes[7] & 63;
    const auto requirement = record.display_requirement_reference();
    require(requirement.has_value() == (category == 20), "Requirement category differs");
    if (requirement)
        require(requirement->actmis_serial == bytes[13] + 256u * bytes[14],
                "ACTMIS reference differs");
    const bool attack = category == 1 || category == 25;
    const bool defense = category == 2 || category == 26;
    const auto display = record.display_combat_arguments();
    require(display.has_value() == (attack || defense), "Display category differs");
    if (display) {
        require(display->physical_message_id == (attack ? 520 : 521) &&
                display->magical_message_id == (attack ? 522 : 523), "Display labels differ");
        require(display->physical == bytes[12] + 256u * ((bytes[24] >> 4) & 3u) &&
                display->magical == bytes[17] + 256u * (bytes[24] >> 6),
                "Packed display arguments differ");
    }
    require(std::equal(record.opaque_instance().begin(), record.opaque_instance().end(),
                       bytes.begin() + 5, bytes.end()), "Opaque instance differs");
}

void assertions() {
    Codec::LogicalRecord seed;
    for (std::size_t i = 0; i < seed.size(); ++i)
        seed[i] = static_cast<std::uint8_t>(i * 73 + 19);
    seed[0] = Codec::opcode;
    seed[2] = 49;
    const auto initial = Codec::parse_logical(seed);
    require(initial.has_value(), "Valid record rejected");
    const auto original = seed;
    seed.fill(0);
    require(Codec::encode_logical(*initial) == original, "Record borrows input");
    check_accessors(*initial, original);
    auto encoded_copy = Codec::encode_logical(*initial);
    encoded_copy.fill(0);
    require(Codec::encode_logical(*initial) == original, "Encoder exposes mutable storage");
    seed = original;

    for (unsigned category = 0; category < 64; ++category) {
        for (unsigned high = 0; high < 256; ++high) {
            for (unsigned low : {0u, 255u}) {
                auto changed = seed;
                changed[7] = static_cast<std::uint8_t>(0xc0u | category);
                changed[12] = static_cast<std::uint8_t>(low);
                changed[17] = static_cast<std::uint8_t>(255u - low);
                changed[24] = static_cast<std::uint8_t>(high);
                const auto decoded = Codec::parse_logical(changed);
                require(decoded.has_value(), "Display record rejected");
                check_accessors(*decoded, changed);
                require(Codec::encode_logical(*decoded) == changed, "Display extraction mutates input");
            }
        }
    }

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
                check_accessors(*result, input);
                const auto reparsed = Codec::parse_logical(encoded);
                require(reparsed.has_value() && Codec::encode_logical(*reparsed) == encoded,
                        "Second roundtrip changed bytes");
            }
            require(std::equal(input.begin(), input.end(), bytes.begin(), bytes.end()),
                    "Input changed");
            ++checks;
        }
    };
    require(!Codec::parse_logical({}), "Empty span accepted");
    for (std::size_t begin = 0; begin <= seed.size(); ++begin)
        for (std::size_t end = begin; end <= seed.size(); ++end)
            check(std::span(seed).subspan(begin, end - begin),
                  begin == 0 && end == seed.size());
    std::vector<std::uint8_t> oversized(seed.begin(), seed.end());
    for (std::size_t size = 26; size <= 50; ++size) {
        oversized.push_back(seed[(size - 1) % seed.size()]);
        check(oversized, false);
    }
    // Every byte value at every position also covers unknown header bytes.
    for (std::size_t offset = 0; offset < seed.size(); ++offset) {
        for (unsigned value = 0; value < 256; ++value) {
            auto changed = seed;
            changed[offset] = static_cast<std::uint8_t>(value);
            check(changed, changed[0] == Codec::opcode && changed[2] < 50);
        }
    }
    for (unsigned slot = 0; slot < 50; ++slot) {
        for (unsigned bit = 0; bit < 160; ++bit) {
            auto changed = seed;
            changed[2] = static_cast<std::uint8_t>(slot);
            std::fill(changed.begin() + 5, changed.end(), std::uint8_t{0});
            changed[5 + bit / 8] = static_cast<std::uint8_t>(1u << (bit % 8));
            check(changed, true);
        }
    }
    std::cout << "Guarded instance-update checks passed: " << checks << '\n';
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

void batch(bool requirements = false) {
    std::string line;
    constexpr char digits[] = "0123456789abcdef";
    while (std::getline(std::cin, line)) {
        const auto result = Codec::parse_logical(unhex(line));
        if (!result) { std::cout << "reject\n"; continue; }
        if (requirements) {
            const auto reference = result->display_requirement_reference();
            if (reference) std::cout << reference->actmis_serial << '\n';
            else std::cout << "none\n";
            continue;
        }
        for (const auto byte : Codec::encode_logical(*result))
            std::cout << digits[byte >> 4] << digits[byte & 15];
        std::cout << ' ' << static_cast<int>(result->slot())
            << ' ' << static_cast<unsigned>(result->raw_category_bits())
            << ' ' << result->low_word_lookup_key()
            << ' ' << result->raw_instance_word8()
            << ' ' << result->raw_packed_dword_c() << '\n';
    }
    require(std::cin.eof(), "Unreadable batch input");
}
}

int main(int argc, char** argv) {
    try {
        if (argc == 1) assertions();
        else {
            require(argc == 2 && (std::string(argv[1]) == "--batch" ||
                    std::string(argv[1]) == "--requirements"), "Expected batch mode");
            batch(std::string(argv[1]) == "--requirements");
        }
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
