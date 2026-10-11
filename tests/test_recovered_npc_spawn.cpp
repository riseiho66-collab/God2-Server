#include "protocol/RecoveredNpcSpawn.h"
#include <iostream>
#include <limits>
#include <string>

namespace {
void require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}
void assertions() {
    using Codec = god2::RecoveredNpcSpawn;
    constexpr Codec::Record dialog{
        0x72,0xd1,0x0e,0,0,0x58,0x60,0,0,0xa1,0,0,0,0xcf,1,0,0,4,1,0x7a,0};
    constexpr Codec::Record merchant{
        0x72,0x72,0x0f,0,0,0x52,0x60,0,0,0x81,0,0,0,0xcf,1,0,0,0xc0,3,0x6c,0};
    require(Codec::logical(3793) == dialog, "Retained dialog bytes changed");
    require(Codec::logical(3954) == merchant, "Retained merchant bytes changed");
    for (auto id : {3793u, 3954u}) {
        const auto baseline = Codec::logical(id);
        const auto edge = Codec::logical(id, 32767, 32767);
        for (unsigned i = 0; i < 17; ++i)
            require(edge[i] == baseline[i], "Unowned NPC field changed");
        require(edge[17] == 0xfc && edge[18] == 0xff && edge[19] == 0xff && edge[20] == 0xff,
                "NPC coordinate packing changed");
    }
    for (auto id : {0ull, 1ull, 65535ull, 65536ull, std::numeric_limits<unsigned long long>::max()}) {
        bool rejected = false;
        try { (void)Codec::logical(id); } catch (const std::invalid_argument&) { rejected = true; }
        require(rejected, "Unqualified selector accepted");
    }
    for (auto value : {32768ull, std::numeric_limits<unsigned long long>::max()}) {
        for (bool x : {false, true}) {
            bool rejected = false;
            try { (void)Codec::logical(3793, x ? value : 0, x ? 0 : value); }
            catch (const std::invalid_argument&) { rejected = true; }
            require(rejected, "Coordinate overflow accepted");
        }
    }
}
}
int main(int argc, char** argv) {
    try {
        assertions();
        if ((argc == 3 || argc == 5) && std::string(argv[1]) == "--dump") {
            const auto selector = std::stoull(argv[2]);
            const auto record = argc == 3 ? god2::RecoveredNpcSpawn::logical(selector) :
                god2::RecoveredNpcSpawn::logical(selector, std::stoull(argv[3]), std::stoull(argv[4]));
            constexpr char digits[] = "0123456789abcdef";
            for (auto b : record) std::cout << digits[b >> 4] << digits[b & 15];
            std::cout << '\n';
        } else {
            require(argc == 1, "Expected --dump selector [x y]");
            std::cout << "Recovered NPC logical-record assertions passed\n";
        }
    } catch (const std::exception& error) { std::cerr << error.what() << '\n'; return 1; }
}
