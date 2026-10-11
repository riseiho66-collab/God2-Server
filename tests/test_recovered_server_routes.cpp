// Standalone: compile with C++20 and -I src; no server or shared build required.
#include "protocol/RecoveredServerRoutes.h"
#include "protocol/RecoveredServerList.h"
#include "protocol/RecoveredCharacterListCandidate.h"
#include <iostream>
#include <algorithm>
#include <string>

namespace {
using Routes = god2::RecoveredServerRoutes;
using List = god2::RecoveredCharacterListCandidate;
constexpr Routes::Address loopback{127, 0, 0, 1};
template<std::size_t N> constexpr std::array<std::uint8_t, N> part(
        const std::array<std::uint8_t, 28>& wire, std::size_t start) {
    std::array<std::uint8_t, N> result{};
    std::copy_n(wire.begin() + start, N, result.begin());
    return result;
}
void require(bool value, const char* message) {
    if (!value) throw std::runtime_error(message);
}
template<class F> void rejects(F call) {
    try { call(); } catch (const std::invalid_argument&) { return; }
    throw std::runtime_error("Invalid route accepted");
}
template<std::size_t N>
void check_codec(const std::array<std::uint8_t, N>& plain,
                 const std::array<std::uint8_t, N>& wire) {
    require(plain[0] + 256u * plain[1] == N, "Frame length");
    require(wire[0] == plain[0] && wire[1] == plain[1], "Clear length changed");
    std::uint8_t previous = 0, sum = 0;
    for (std::size_t i = 0; i < N; ++i) {
        if (i >= 2) {
            previous = static_cast<std::uint8_t>(wire[i] + 3 - previous) ^
                       god2::recovered_zero_seed_key[i - 2];
            require(previous == plain[i], "Zero-seed codec changed");
        }
        if (i + 1 < N) sum = static_cast<std::uint8_t>(sum + plain[i] + 0x3c);
    }
    require(sum == plain.back(), "Checksum mismatch");
}
std::array<god2::RecoveredCharacter, 2> characters() {
    std::array<god2::RecoveredCharacter, 2> result{};
    for (std::size_t i = 0; i < result.size(); ++i) {
        result[i].slot = static_cast<std::uint8_t>(i);
        result[i].profile[0] = static_cast<std::uint8_t>('A' + i);
        result[i].profile[29] = 1;
        result[i].profile[31] = 1;
    }
    return result;
}
template<class Frame> void print_hex(const Frame& frame) {
    constexpr char digits[] = "0123456789abcdef";
    for (auto byte : frame) std::cout << digits[byte >> 4] << digits[byte & 15];
    std::cout << '\n';
}
void assertions() {
    constexpr auto plain = Routes::decoded(loopback, 2593);
    constexpr auto wire = Routes::wire(loopback, 2593);
    static_assert(plain.group == std::array<std::uint8_t, 8>{8,0,4,0,0,1,0,0xb1});
    static_assert(plain.endpoint == std::array<std::uint8_t, 12>{12,0,5,0,0,127,0,0,1,0x21,0x0a,0x50});
    static_assert(plain.route == std::array<std::uint8_t, 8>{8,0,6,1,0,0,0,0xb3});
    static_assert(part<8>(wire, 0) == god2::RecoveredServerList::one_entry());
    static_assert(part<12>(wire, 8) == std::array<std::uint8_t, 12>{12,0,2,2,0xfd,0x7c,0x7c,0xfd,0xfe,0x1f,0x28,0x57});
    static_assert(part<8>(wire, 20) == std::array<std::uint8_t, 8>{8,0,3,4,0xfe,0xfd,0xfd,0xb0});
    constexpr auto separate = Routes::wire(2593, 1, loopback);
    static_assert(separate.group == part<8>(wire, 0));
    static_assert(separate.endpoint == part<12>(wire, 8));
    static_assert(separate.route == part<8>(wire, 20));
    for (std::uint16_t port : std::array<std::uint16_t, 3>{1, 2593, 65535}) {
        for (std::uint8_t id : std::array<std::uint8_t, 3>{1, 127, 255}) {
            const auto p = Routes::decoded({127,23,45,67}, port, id);
            const auto w = Routes::wire({127,23,45,67}, port, id);
            check_codec(p.group, part<8>(w, 0));
            check_codec(p.endpoint, part<12>(w, 8));
            check_codec(p.route, part<8>(w, 20));
            require(p.endpoint[9] + 256u * p.endpoint[10] == port, "Port truncation");
            require(p.route[3] == id, "Route ID truncation");
        }
    }
    rejects([] { Routes::decoded(loopback, 0); });
    rejects([] { Routes::wire(loopback, 0); });
    rejects([] { Routes::decoded(loopback, 2593, 0); });
    rejects([] { Routes::wire(loopback, 2593, 0); });
    for (const Routes::Address address : {Routes::Address{0,0,0,0},
             Routes::Address{126,0,0,1}, Routes::Address{128,0,0,1},
             Routes::Address{192,168,1,1}, Routes::Address{255,255,255,255}}) {
        rejects([&] { Routes::decoded(address, 2593); });
        rejects([&] { Routes::wire(address, 2593); });
    }
    const auto records = characters();
    const auto baseline = List::decoded(records);
    require(baseline == List::decoded(records, 0), "Default list changed");
    require(List::wire({}) == god2::LegacyCharacterListCandidate::wire(), "Empty default changed");
    require(List::wire({}, 255) == List::wire({}), "Empty route changes legacy bytes");
    for (std::uint8_t id : std::array<std::uint8_t, 2>{1, 255}) {
        auto expected = baseline;
        expected[5+32] = expected[5+36+32] = static_cast<std::uint8_t>(id);
        expected.back() = static_cast<std::uint8_t>(expected.back() + 2 * id);
        const auto populated = List::decoded(records, id);
        require(populated == expected, "Route changed unrelated character bytes");
        check_codec(populated, List::wire(records, id));
    }
}
}

int main(int argc, char** argv) {
    try {
        assertions();
        // The Unicorn suite consumes these exact C++ wire bytes, never a server.
        if (argc == 8 && std::string(argv[1]) == "--dump") {
            const auto port = std::stoul(argv[2]), id = std::stoul(argv[3]);
            Routes::Address address{};
            for (std::size_t i = 0; i < 4; ++i) {
                const auto octet = std::stoul(argv[4+i]);
                require(octet <= 255, "IPv4 octet overflow");
                address[i] = static_cast<std::uint8_t>(octet);
            }
            require(port <= 65535 && id <= 255, "Dump argument overflow");
            const auto wire = Routes::wire(address, static_cast<std::uint16_t>(port), static_cast<std::uint8_t>(id));
            print_hex(part<8>(wire, 0));
            print_hex(part<12>(wire, 8));
            print_hex(part<8>(wire, 20));
            print_hex(List::wire(characters(), static_cast<std::uint8_t>(id)));
        } else {
            require(argc == 1, "Expected --dump port route_id a b c d");
            std::cout << "Recovered route header assertions passed\n";
        }
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
