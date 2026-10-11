#include "protocol/RecoveredSkillCommand.h"
#include <algorithm>
#include <cstring>
#include <fstream>
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
using Codec = god2::RecoveredSkillCommand;
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
        const auto page_size = sysconf(_SC_PAGESIZE);
        require(page_size > 0, "Page size unavailable");
        page_size_ = static_cast<std::size_t>(page_size);
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

void require_lossless(const Codec::Record& record,
                      std::span<const std::uint8_t> bytes) {
    std::array<std::uint8_t, Codec::logical_size> encoded{
        0x35, record.actor_position,
        static_cast<std::uint8_t>(record.continuation ? 0x83 : 3),
        record.side_flag, record.unwritten_byte3};
    for (std::size_t group = 0; group < 2; ++group) {
        encoded[5 + group * 2] = static_cast<std::uint8_t>(record.target_masks[group]);
        encoded[6 + group * 2] = static_cast<std::uint8_t>(record.target_masks[group] >> 8);
    }
    for (std::size_t byte = 0; byte < 4; ++byte)
        encoded[9 + byte] = static_cast<std::uint8_t>(record.context_storage >> (byte * 8));
    encoded[13] = record.selection_id_byte;
    encoded[14] = record.selection_kind_byte;
    require(std::equal(encoded.begin(), encoded.end(), bytes.begin(), bytes.end()),
            "Accepted record lost or changed bytes");
}

void guarded_sequences(std::span<const std::uint8_t> seed) {
    require(Codec::parse_sequence(seed).has_value(), "Guard seed must be a valid sequence");
    require(!Codec::runtime_mutation_enabled, "Unexpected gameplay promotion");
    GuardedInput memory;
    std::size_t checks = 0;
    auto check = [&](std::span<const std::uint8_t> bytes, bool accepted) {
        for (const bool at_end : {false, true}) {
            const auto input = memory.place(bytes, at_end);
            const auto result = Codec::parse_sequence(input);
            if (result.has_value() != accepted)
                throw std::runtime_error("Guard sequence expectation differs at case " +
                                         std::to_string(checks));
            if (result) {
                require(result->count == bytes.size() / Codec::logical_size,
                        "Guard sequence count differs");
                for (std::size_t index = 0; index < result->count; ++index)
                    require_lossless(result->records[index],
                        bytes.subspan(index * Codec::logical_size, Codec::logical_size));
            }
            const auto record = Codec::parse_logical(input);
            if (bytes.size() != Codec::logical_size)
                require(!record, "Guard record accepted wrong span length");
            if (record) require_lossless(*record, bytes);
            ++checks;
        }
    };
    require(!Codec::parse_sequence({}) && !Codec::parse_logical({}),
            "Default empty span accepted");

    // Every prefix of every record-aligned suffix ends directly at a guard page.
    // Removing whole prefix records is intentionally invisible to this contract.
    for (std::size_t start = 0; start <= seed.size(); start += Codec::logical_size) {
        const auto suffix = seed.subspan(start);
        for (std::size_t length = 0; length <= suffix.size(); ++length)
            check(suffix.first(length), length != 0 && length == suffix.size());
    }
    check(seed, true);
    for (std::size_t offset = 0; offset < seed.size(); ++offset) {
        for (unsigned bit = 0; bit < 8; ++bit) {
            auto changed = std::vector<std::uint8_t>(seed.begin(), seed.end());
            changed[offset] ^= static_cast<std::uint8_t>(1u << bit);
            // In multi-record seeds only the unwritten byte may differ freely.
            if (seed.size() > Codec::logical_size)
                check(changed, offset % Codec::logical_size == 4);
        }
    }
    for (std::size_t seam = Codec::logical_size; seam < seed.size();
         seam += Codec::logical_size) {
        for (unsigned value = 0; value < 256; ++value) {
            auto changed = std::vector<std::uint8_t>(seed.begin(), seed.end());
            changed[seam - 1] = static_cast<std::uint8_t>(value);
            changed[seam] = static_cast<std::uint8_t>(value ^ 0x35);
            check(changed, value == 0);
        }
        for (const auto offset : {seam - 1, seam, seam + 1}) {
            auto changed = std::vector<std::uint8_t>(seed.begin(), seed.end());
            changed.erase(changed.begin() + static_cast<std::ptrdiff_t>(offset));
            check(changed, false);
            changed.assign(seed.begin(), seed.end());
            changed.insert(changed.begin() + static_cast<std::ptrdiff_t>(offset), 0x35);
            check(changed, false);
        }
    }
    // Exhaust opaque byte values independently per record, and vary the entire
    // shared context/selection without inventing a meaning for either field.
    for (unsigned value = 0; value < 256; ++value) {
        auto changed = std::vector<std::uint8_t>(seed.begin(), seed.end());
        for (std::size_t start = 0; start < seed.size(); start += Codec::logical_size) {
            changed[start + 4] = static_cast<std::uint8_t>(value + start / Codec::logical_size);
            for (std::size_t byte = 0; byte < 4; ++byte)
                changed[start + 9 + byte] = static_cast<std::uint8_t>(value + byte * 67);
            changed[start + 13] = static_cast<std::uint8_t>(value);
        }
        check(changed, true);
    }
    auto overlong = std::vector<std::uint8_t>(seed.begin(), seed.end());
    overlong.insert(overlong.end(), seed.begin(), seed.end());
    check(overlong, false);
    // Reach the size cap without an earlier malformed continuation.
    overlong.assign(seed.begin(), seed.begin() + Codec::logical_size);
    overlong[2] = 0x83;
    const auto first = overlong;
    while (overlong.size() < Codec::max_sequence_records * Codec::logical_size)
        overlong.insert(overlong.end(), first.begin(), first.end());
    overlong.insert(overlong.end(), seed.end() - Codec::logical_size, seed.end());
    check(overlong, false);
    std::cout << "Guarded sequence checks passed: " << checks << '\n';
}
void print_record(const Codec::Record& record) {
    std::cout << unsigned(record.actor_position) << ' ' << record.continuation
        << ' ' << unsigned(record.side_flag) << ' ' << unsigned(record.unwritten_byte3)
        << ' ' << record.target_masks[0] << ' ' << record.target_masks[1]
        << ' ' << record.context_storage << ' ' << unsigned(record.selection_id_byte)
        << '\n';
}
void assertions() {
    const std::array<std::uint8_t, 17> bytes{
        0x35,14,0x83,1,0xa5,0,0,0,0x20,0xef,0xcd,0xab,0x89,0x9b,0,0,0};
    const auto result = Codec::parse_logical(bytes);
    require(result && result->actor_position == 14 && result->continuation &&
            result->side_flag == 1 && result->unwritten_byte3 == 0xa5 &&
            result->target_masks == std::array<std::uint16_t, 2>{0, 0x2000} &&
            result->context_storage == 0x89abcdef && result->selection_id_byte == 0x9b,
            "Kind-0 continuation fields differ");
    for (std::size_t length = 0; length < bytes.size(); ++length)
        require(!Codec::parse_logical(std::span(bytes).first(length)), "Truncation accepted");
    for (unsigned value = 0; value < 256; ++value) {
        for (const auto offset : {0u, 1u, 2u, 3u, 4u, 13u, 14u, 15u, 16u}) {
            auto changed = bytes;
            changed[offset] = static_cast<std::uint8_t>(value);
            const bool accepted = offset == 0 ? value == 0x35 :
                offset == 1 ? value <= 14 : offset == 2 ? value == 3 || value == 0x83 :
                offset == 3 ? value <= 1 : offset == 4 || offset == 13 ? true :
                offset == 14 ? value==0 || value==1 || value==3 : value == 0;
            require(Codec::parse_logical(changed).has_value() == accepted,
                    "Byte boundary contract differs");
        }
    }
    // Exhaust every word value in each target group, including unused high bits.
    for (const auto offset : {5u, 7u}) {
        for (unsigned mask = 0; mask <= 0xffff; ++mask) {
            auto changed = bytes;
            changed[5] = changed[6] = changed[7] = changed[8] = 0;
            changed[offset] = static_cast<std::uint8_t>(mask);
            changed[offset + 1] = static_cast<std::uint8_t>(mask >> 8);
            require(Codec::parse_logical(changed).has_value() ==
                    (mask < 0x4000 && std::popcount(mask) == 1),
                    "Single-target mask contract differs");
        }
    }
    auto changed = bytes;
    changed[5] = 1;
    require(!Codec::parse_logical(changed), "Two target groups accepted together");
    auto extra = std::vector<std::uint8_t>(bytes.begin(), bytes.end());
    extra.push_back(0);
    require(!Codec::parse_logical(extra), "Trailing byte accepted");
    extra.insert(extra.end(), bytes.begin(), bytes.end());
    require(!Codec::parse_logical(extra), "Multiple records accepted");
    require(!god2::RecoveredBattleCommand::parse_logical(bytes),
            "Skill record entered basic-attack contract");
    require(!Codec::parse_sequence(bytes), "Lone continuation accepted as sequence");
    auto terminal = bytes;
    terminal[2] = 3;
    const auto single = Codec::parse_sequence(terminal);
    require(single && single->count == 1 && !single->records[0].continuation,
            "Terminal single-record sequence rejected");
    std::vector<std::uint8_t> sequence;
    for (std::size_t i = 0; i < Codec::max_sequence_records; ++i) {
        sequence.insert(sequence.end(), terminal.begin(), terminal.end());
        const auto parsed = Codec::parse_sequence(sequence);
        require(parsed && parsed->count == i + 1, "Bounded duplicate sequence rejected");
        sequence[i * Codec::logical_size + 2] = 0x83;
        require(!Codec::parse_sequence(sequence), "Unterminated sequence accepted");
    }
    sequence.insert(sequence.end(), terminal.begin(), terminal.end());
    require(!Codec::parse_sequence(sequence), "Fifteen-record sequence accepted");
    require(!Codec::runtime_mutation_enabled, "Unexpected gameplay promotion");
}
std::vector<std::uint8_t> unhex(const std::string& text) {
    require(text.size() % 2 == 0, "Odd hex length");
    std::vector<std::uint8_t> bytes;
    const std::string digits = "0123456789abcdef";
    for (std::size_t i = 0; i < text.size(); i += 2) {
        const auto high = digits.find(text[i]);
        const auto low = digits.find(text[i + 1]);
        require(high < 16 && low < 16, "Invalid hex");
        bytes.push_back(static_cast<std::uint8_t>(high * 16 + low));
    }
    return bytes;
}
}
int main(int argc, char** argv) {
    try {
        if (argc == 3 && std::string(argv[1]) == "--identity-batch") {
            std::ifstream input(argv[2], std::ios::binary | std::ios::ate);
            require(input.good(), "Cannot open definition source");
            require(input.tellg() == static_cast<std::streamoff>(Codec::definition_file_size),
                    "Definition source size differs");
            input.seekg(0);
            std::vector<std::uint8_t> source(Codec::definition_file_size);
            input.read(reinterpret_cast<char*>(source.data()),
                       static_cast<std::streamsize>(source.size()));
            require(input.good(), "Truncated definition source read");
            std::string line;
            while (std::getline(std::cin, line)) {
                const auto bytes = unhex(line);
                const auto identity = Codec::parse_state_word(bytes);
                const auto offset = Codec::definition_offset(bytes, source);
                if (!identity) { std::cout << "reject\n"; continue; }
                std::cout << identity->raw << ' ' << unsigned(identity->id) << ' '
                          << unsigned(identity->kind) << ' ' << identity->alternate_table
                          << ' ' << identity->state_bit << ' ';
                if (offset) std::cout << *offset;
                else std::cout << "reject";
                std::cout << '\n';
            }
        } else if (argc == 3 && std::string(argv[1]) == "--decode") {
            const auto result = Codec::parse_logical(unhex(argv[2]));
            if (!result) { std::cout << "reject\n"; return 0; }
            print_record(*result);
        } else if (argc == 3 && std::string(argv[1]) == "--decode-sequence") {
            const auto result = Codec::parse_sequence(unhex(argv[2]));
            if (!result) { std::cout << "reject\n"; return 0; }
            for (std::size_t i = 0; i < result->count; ++i)
                print_record(result->records[i]);
        } else if (argc == 3 && std::string(argv[1]) == "--guard-sequence") {
            guarded_sequences(unhex(argv[2]));
        } else {
            require(argc == 1, "Expected --decode, --decode-sequence or --guard-sequence logical_hex");
            assertions();
            std::cout << "Recovered kind-0 skill record assertions passed\n";
        }
    } catch (const std::exception& error) { std::cerr << error.what() << '\n'; return 1; }
}
