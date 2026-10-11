#include "protocol/RecoveredBattleParticipant.h"

#include <iostream>
#include <limits>
#include <random>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <vector>

namespace {
using Codec = god2::RecoveredBattleParticipant;
void require(bool value) {
    if (!value) throw std::runtime_error("Battle participant codec check failed");
}
std::uint16_t word(const Codec::Bytes& bytes, std::size_t at) {
    return static_cast<std::uint16_t>(bytes[at] + 256u * bytes[at + 1]);
}
void verify(const Codec::Bytes& bytes) {
    const auto record = Codec::parse_logical(bytes);
    require(record.has_value());
    require(Codec::encode_logical(*record) == bytes);
    const bool is83 = bytes[0] == 0x83;
    const auto position = bytes[is83 ? 2 : 5];
    require(record->opcode() == bytes[0] && record->position() == position);
    require(record->side() == position / 14 && record->slot() == position % 14);
    require(record->marker() == bytes[is83 ? 3 : 8]);
    require(record->target_masks() == std::array<std::uint16_t, 2>{
        word(bytes, is83 ? 5 : 1), word(bytes, is83 ? 7 : 3)});
    for (std::size_t at = 0; at < 32; ++at) {
        const bool raw = at == 9 || (!is83 && (at == 11 || at == 13));
        const bool action = is83 ? (at == 11 || at == 12) : (at == 6 || at == 7);
        require(record->raw_word_at(at).has_value() == raw);
        require(record->action_byte_at(at).has_value() == action);
        if (raw) require(*record->raw_word_at(at) == word(bytes, at));
        if (action) require(*record->action_byte_at(at) == bytes[at]);
    }
    require(!record->raw_word_at(std::numeric_limits<std::size_t>::max()));
    require(!record->action_byte_at(std::numeric_limits<std::size_t>::max()));
    auto output = Codec::encode_logical(*record);
    output.fill(0);
    require(Codec::encode_logical(*record) == bytes);
}
void checks() {
    static_assert(!std::is_default_constructible_v<Codec::Record>);
    static_assert(!Codec::runtime_emission_enabled && !Codec::runtime_mutation_enabled);
    std::mt19937 rng(830120);
    for (const auto opcode : {0x83, 0x84}) {
        Codec::Bytes bytes{};
        bytes[0] = static_cast<std::uint8_t>(opcode);
        bytes[1] = 1;
        const std::size_t position_at = opcode == 0x83 ? 2 : 5;
        for (unsigned position = 0; position < 256; ++position) {
            bytes[position_at] = static_cast<std::uint8_t>(position);
            require(Codec::parse_logical(bytes).has_value() == (position < 28));
            if (position < 28) verify(bytes);
        }
        bytes[position_at] = 27;
        for (std::size_t at = 1; at < bytes.size(); ++at) {
            if (at == position_at || (opcode == 0x83 && at == 1)) continue;
            for (unsigned value = 0; value < 256; ++value) {
                auto probe = bytes;
                probe[at] = static_cast<std::uint8_t>(value);
                verify(probe);
            }
        }
        for (unsigned code = 0; code < 256; ++code) {
            auto probe = bytes;
            probe[0] = static_cast<std::uint8_t>(code);
            if (code != 0x83 && code != 0x84) require(!Codec::parse_logical(probe));
        }
        if (opcode == 0x83) for (unsigned subtype = 0; subtype < 256; ++subtype) {
            auto probe = bytes;
            probe[1] = static_cast<std::uint8_t>(subtype);
            require(Codec::parse_logical(probe).has_value() == (subtype == 1));
        }
        std::vector<std::uint8_t> joined(bytes.begin(), bytes.end());
        joined.insert(joined.end(), bytes.begin(), bytes.end());
        for (std::size_t length = 0; length <= joined.size(); ++length)
            require(Codec::parse_logical(std::span(joined).first(length)).has_value() ==
                (length == Codec::logical_size));
        const auto retained = Codec::parse_logical(bytes);
        const auto expected = bytes;
        bytes.fill(0);
        require(Codec::encode_logical(*retained) == expected);
        for (unsigned trial = 0; trial < 512; ++trial) {
            for (auto& byte : bytes) byte = static_cast<std::uint8_t>(rng());
            bytes[0] = static_cast<std::uint8_t>(opcode);
            if (opcode == 0x83) bytes[1] = 1;
            bytes[position_at] = static_cast<std::uint8_t>(rng() % 28);
            verify(bytes);
        }
    }
    std::cout << "Battle participant codec checks passed\n";
}
void roundtrip(const std::string& hex) {
    const std::string digits = "0123456789abcdef";
    require(hex.size() % 2 == 0 && hex.size() <= 4096);
    std::vector<std::uint8_t> bytes;
    for (std::size_t at = 0; at < hex.size(); at += 2) {
        const auto a = digits.find(hex[at]), b = digits.find(hex[at + 1]);
        require(a < 16 && b < 16);
        bytes.push_back(static_cast<std::uint8_t>(a * 16 + b));
    }
    const auto record = Codec::parse_logical(bytes);
    if (!record) { std::cout << "reject\n"; return; }
    for (const auto byte : Codec::encode_logical(*record))
        std::cout << digits[byte >> 4] << digits[byte & 15];
    std::cout << '\n';
}
}
int main(int argc, char** argv) {
    try {
        if (argc == 1) checks();
        else if (argc == 3 && std::string(argv[1]) == "--roundtrip") roundtrip(argv[2]);
        else {
            require(argc == 2 && std::string(argv[1]) == "--batch");
            std::string line;
            while (std::getline(std::cin, line)) roundtrip(line);
            require(std::cin.eof());
        }
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
