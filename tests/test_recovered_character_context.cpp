#include "protocol/RecoveredCharacterContext.h"
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
using Codec = god2::RecoveredCharacterContext;
void require(bool result, const char* message) {
    if (!result) throw std::runtime_error(message);
}
void assertions() {
    std::array<std::uint8_t, Codec::logical_size> record{};
    record[0] = Codec::opcode;
    for (unsigned value = 0; value < 256; ++value) {
        for (std::size_t i = 1; i < record.size(); ++i)
            record[i] = static_cast<std::uint8_t>(value + i);
        const auto result = Codec::decode_preselection_reply(record);
        require(result.has_value(), "Opaque payload incorrectly constrained");
        require(std::equal(record.begin() + 1, record.end(), result->opaque_body.begin()),
                "Opaque bytes were altered");
    }
    for (std::size_t length = 0; length < record.size(); ++length)
        require(!Codec::decode_preselection_reply(std::span(record).first(length)),
                "Truncated record accepted");
    for (unsigned opcode = 0; opcode < 256; ++opcode) {
        record[0] = static_cast<std::uint8_t>(opcode);
        require(Codec::decode_preselection_reply(record).has_value() == (opcode == 0x1f),
                "Wrong opcode accepted");
    }
    std::uint32_t seed = 0x146a70;
    for (std::size_t size = 0; size < 4096; ++size) {
        std::vector<std::uint8_t> input(size);
        for (auto& byte : input) {
            seed ^= seed << 13; seed ^= seed >> 17; seed ^= seed << 5;
            byte = static_cast<std::uint8_t>(seed);
        }
        if (!input.empty()) input[0] = 0x1f;
        require(Codec::decode_preselection_reply(input).has_value() == (size == 125),
                "Input bound violated");
    }
}
std::vector<std::uint8_t> unhex(const std::string& text) {
    require(text.size() <= 8192 && text.size() % 2 == 0, "Invalid hex length");
    const std::string digits = "0123456789abcdef";
    std::vector<std::uint8_t> result;
    for (std::size_t i = 0; i < text.size(); i += 2) {
        const auto high = digits.find(text[i]), low = digits.find(text[i + 1]);
        require(high < 16 && low < 16, "Invalid hex byte");
        result.push_back(static_cast<std::uint8_t>(16 * high + low));
    }
    return result;
}
}

int main(int argc, char** argv) {
    try {
        if (argc == 1) {
            assertions();
            std::cout << "Character context shape/bounds assertions passed\n";
        } else {
            require(argc == 3 && std::string(argv[1]) == "--decode", "Expected --decode logical_hex");
            const auto result = Codec::decode_preselection_reply(unhex(argv[2]));
            if (!result) { std::cout << "reject\n"; return 0; }
            constexpr char digits[] = "0123456789abcdef";
            for (auto byte : result->opaque_body)
                std::cout << digits[byte >> 4] << digits[byte & 15];
            std::cout << '\n';
        }
    } catch (const std::exception& error) { std::cerr << error.what() << '\n'; return 1; }
}
