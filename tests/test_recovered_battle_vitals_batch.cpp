#include "protocol/RecoveredBattleVitalsBatch.h"
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

int main() {
    using Codec = god2::RecoveredBattleVitalsBatch;
    static_assert(!Codec::runtime_emission_enabled);
    std::string line;
    while (std::getline(std::cin, line)) {
        std::vector<std::uint8_t> raw;
        for (std::size_t i = 0; i + 1 < line.size(); i += 2)
            raw.push_back(static_cast<std::uint8_t>(std::stoul(line.substr(i, 2), nullptr, 16)));
        const auto record = Codec::parse_logical(raw);
        if (!record) { std::cout << "reject\n"; continue; }
        const auto before = raw;
        std::fill(raw.begin(), raw.end(), std::uint8_t{0});
        const auto encoded = Codec::encode_logical(*record);
        if (!std::equal(encoded.begin(), encoded.end(), before.begin(), before.end()) ||
            record->at(14) || record->at(std::numeric_limits<std::size_t>::max()))
            throw std::runtime_error("Owning record/bounds regression");
        for (std::size_t slot = 0; slot < Codec::slots; ++slot) {
            const auto value = record->at(slot);
            std::cout << value->hp << ' ' << value->mp << ' ';
        }
        std::cout << '\n';
    }
}
