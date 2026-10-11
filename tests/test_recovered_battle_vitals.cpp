#include "protocol/RecoveredBattleVitals.h"
#include <iostream>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <vector>

namespace {
using Codec = god2::RecoveredBattleVitals;
void require(bool value) {
    if (!value) throw std::runtime_error("Battle vitals codec check failed");
}
void verify(const Codec::Bytes& bytes) {
    const auto record = Codec::parse_logical(bytes);
    require(record.has_value());
    require(Codec::encode_logical(*record) == bytes);
    require(static_cast<unsigned>(record->resource()) == bytes[1]);
    require(record->position() == bytes[2] && record->side() == bytes[2] / 14 && record->slot() == bytes[2] % 14);
    std::uint32_t current = 0, maximum = 0;
    for (unsigned i = 0; i < 4; ++i) {
        current |= std::uint32_t{bytes[9 + i]} << (8 * i);
        maximum |= std::uint32_t{bytes[5 + i]} << (8 * i);
    }
    require(record->current() == current && record->maximum() == maximum);
    require(record->native_actor_write_supported() == (bytes[1] == 0 || bytes[2] < 14));
    require(std::equal(record->opaque_word().begin(), record->opaque_word().end(), bytes.begin() + 3));
    require(std::equal(record->opaque_tail().begin(), record->opaque_tail().end(), bytes.begin() + 13));
}
void checks() {
    static_assert(!std::is_default_constructible_v<Codec::Record>);
    static_assert(!Codec::runtime_emission_enabled && !Codec::runtime_mutation_enabled);
    Codec::Bytes bytes{};
    bytes[0] = 0x86;
    for (unsigned kind = 0; kind < 2; ++kind) {
        bytes[1] = static_cast<std::uint8_t>(kind);
        for (unsigned position = 0; position < 256; ++position) {
            bytes[2] = static_cast<std::uint8_t>(position);
            require(Codec::parse_logical(bytes).has_value() == (position < 28));
            if (position < 28) verify(bytes);
        }
        for (const unsigned position : {0u, 14u, 27u}) {
            bytes[2] = static_cast<std::uint8_t>(position);
            for (unsigned offset = 3; offset < 17; ++offset) {
                for (unsigned value = 0; value < 256; ++value) {
                    auto probe = bytes;
                    probe[offset] = static_cast<std::uint8_t>(value);
                    verify(probe);
                }
            }
        }
    }
    for (unsigned kind = 0; kind < 256; ++kind) {
        auto probe = bytes;
        probe[1] = static_cast<std::uint8_t>(kind);
        require(Codec::parse_logical(probe).has_value() == (kind <= 1));
    }
    for (unsigned opcode = 0; opcode < 256; ++opcode) {
        auto probe = bytes;
        probe[0] = static_cast<std::uint8_t>(opcode);
        require(Codec::parse_logical(probe).has_value() == (opcode == 0x86));
    }
    for (std::size_t length = 0; length < 17; ++length)
        require(!Codec::parse_logical(std::span(bytes).first(length)));
    std::vector<std::uint8_t> joined(bytes.begin(), bytes.end());
    joined.insert(joined.end(), bytes.begin(), bytes.end());
    for (std::size_t length = 18; length <= joined.size(); ++length)
        require(!Codec::parse_logical(std::span(joined).first(length)));
    const auto retained = Codec::parse_logical(bytes);
    require(retained.has_value());
    const auto expected = bytes;
    bytes.fill(0);
    require(Codec::encode_logical(*retained) == expected);
    auto copy = Codec::encode_logical(*retained);
    copy.fill(0xff);
    require(Codec::encode_logical(*retained) == expected);
    std::cout << "Battle vitals codec checks passed\n";
}
void batch() {
    const std::string digits = "0123456789abcdef";
    std::string line;
    while (std::getline(std::cin, line)) {
        require(line.size() % 2 == 0 && line.size() <= 4096);
        std::vector<std::uint8_t> bytes;
        for (std::size_t i = 0; i < line.size(); i += 2) {
            const auto a = digits.find(line[i]), b = digits.find(line[i + 1]);
            require(a < 16 && b < 16);
            bytes.push_back(static_cast<std::uint8_t>(a * 16 + b));
        }
        const auto record = Codec::parse_logical(bytes);
        if (!record) { std::cout << "reject\n"; continue; }
        for (const auto byte : Codec::encode_logical(*record)) std::cout << digits[byte >> 4] << digits[byte & 15];
        std::cout << ' ' << static_cast<unsigned>(record->resource())
                  << ' ' << static_cast<unsigned>(record->position())
                  << ' ' << static_cast<unsigned>(record->side())
                  << ' ' << static_cast<unsigned>(record->slot())
                  << ' ' << record->current() << ' ' << record->maximum()
                  << ' ' << record->native_actor_write_supported() << '\n';
    }
    require(std::cin.eof());
}
}
int main(int argc, char** argv) {
    try {
        if (argc == 1) checks();
        else { require(argc == 2 && std::string(argv[1]) == "--batch"); batch(); }
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
