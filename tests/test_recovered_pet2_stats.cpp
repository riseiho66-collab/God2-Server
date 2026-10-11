#include "protocol/RecoveredPet2Stats.h"
#include <iostream>
#include <string>
#include <type_traits>
#include <vector>

using Codec = god2::RecoveredPet2Stats;
static_assert(!Codec::runtime_emission_enabled && !Codec::runtime_mutation_enabled);
static_assert(!std::is_default_constructible_v<Codec::Record>);

int main(int argc, char** argv) {
    const bool progress_only = argc == 2 && std::string(argv[1]) == "--progress";
    const bool progression_only = argc == 2 && std::string(argv[1]) == "--progression";
    if (argc != 1 && !progress_only && !progression_only) return 2;
    const std::string digits = "0123456789abcdef";
    std::string line;
    while (std::getline(std::cin, line)) {
        if (line.size() % 2 || line.size() > 8192) return 2;
        std::vector<std::uint8_t> bytes;
        for (std::size_t i = 0; i < line.size(); i += 2) {
            const auto high = digits.find(line[i]), low = digits.find(line[i + 1]);
            if (high >= 16 || low >= 16) return 2;
            bytes.push_back(static_cast<std::uint8_t>(high * 16 + low));
        }
        const auto record = Codec::parse_logical(bytes);
        if (!record) { std::cout << "reject\n"; continue; }
        const auto before = bytes;
        std::fill(bytes.begin(), bytes.end(), std::uint8_t{0});
        const auto encoded = Codec::encode_logical(*record);
        if (!std::equal(encoded.begin(), encoded.end(), before.begin(), before.end())) return 3;
        if (progress_only) {
            std::cout << record->progress_display_raw24() << '\n';
            continue;
        }
        if (progression_only) {
            const auto v = record->vitals();
            std::cout << static_cast<unsigned>(record->level()) << ' '
                << v.current_hp << ' ' << v.maximum_hp << ' '
                << v.current_mp << ' ' << v.maximum_mp << ' '
                << static_cast<unsigned>(record->star_rank()) << ' '
                << static_cast<unsigned>(record->star_rating()) << '\n';
            continue;
        }
        for (const auto byte : encoded) std::cout << digits[byte >> 4] << digits[byte & 15];
        const auto c = record->combat_values();
        const auto a = record->attributes();
        const auto e = record->elements();
        std::cout << ' ' << record->metadata_key() << ' ' << static_cast<unsigned>(record->slot())
            << ' ' << c.physical_attack << ' ' << c.physical_defense
            << ' ' << c.magical_attack << ' ' << c.magical_defense
            << ' ' << a.strength << ' ' << a.constitution << ' ' << a.intelligence << ' ' << a.speed
            << ' ' << e.metal << ' ' << e.wood << ' ' << e.water << ' ' << e.fire << ' ' << e.earth << '\n';
    }
    return std::cin.eof() ? 0 : 4;
}
