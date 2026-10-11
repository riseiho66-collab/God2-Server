#include "protocol/RecoveredRoleAuxiliary.h"
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <string_view>
#include <vector>

static void require(bool value, const char* message) {
    if (!value) { std::cerr << message << '\n'; std::exit(1); }
}
int main(int argc, char** argv) {
    using Codec = god2::RecoveredRoleAuxiliary;
    Codec::Logical wire{};
    wire[0] = 0x2c;
    for (std::size_t i = 1; i < wire.size(); ++i)
        wire[i] = static_cast<std::uint8_t>(i * 37 + 19);
    const auto parsed = Codec::parse(wire);
    require(parsed.has_value(), "valid snapshot rejected");
    require(Codec::encode(*parsed) == wire, "opaque wire bytes not preserved");
    auto read = [&](std::size_t p) {
        return std::uint32_t{wire[p]} | (std::uint32_t{wire[p+1]} << 8) |
            (std::uint32_t{wire[p+2]} << 16) | (std::uint32_t{wire[p+3]} << 24);
    };
    require(Codec::physical_attack(*parsed) == read(49), "physical attack offset");
    require(Codec::physical_defense(*parsed) == read(45), "physical defense offset");
    require(Codec::magical_attack(*parsed) == read(57), "magic attack offset");
    require(Codec::magical_defense(*parsed) == read(53), "magic defense offset");
    for (std::size_t size = 0; size < wire.size(); ++size)
        require(!Codec::parse(std::span(wire).first(size)), "truncated accepted");
    std::vector<std::uint8_t> extra(wire.begin(), wire.end());extra.push_back(0);
    require(!Codec::parse(extra), "trailing data accepted");
    auto wrong = wire;wrong[0] = 0x22;
    require(!Codec::parse(wrong), "wrong opcode accepted");
    // High DWORD bits are retained as raw values; no guessed signed semantics.
    auto extremes = wire;
    for (std::size_t i = 45; i < 61; ++i) extremes[i] = 0xff;
    auto high = Codec::parse(extremes);
    require(high && Codec::physical_attack(*high) == 0xffffffffu &&
        Codec::physical_defense(*high) == 0xffffffffu && Codec::magical_attack(*high) == 0xffffffffu &&
        Codec::magical_defense(*high) == 0xffffffffu, "high raw bits lost");
    if (argc == 2 && std::string_view(argv[1]) == "--emit-native") {
        for (const auto byte : Codec::encode(*parsed))
            std::cout << std::hex << std::setw(2) << std::setfill('0') << unsigned(byte);
        std::cout << '\n';
    } else std::cout << "PASS recovered role auxiliary snapshot\n";
}
