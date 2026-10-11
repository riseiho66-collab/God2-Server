#include "protocol/RecoveredInventoryMoveRequest.h"
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

static void require(bool condition) {
    if (!condition) throw std::runtime_error("inventory move codec mismatch");
}
int main() {
    using Codec=god2::RecoveredInventoryMoveRequest;
    for (unsigned source=0; source<256; ++source) {
        for (unsigned destination=0; destination<256; ++destination) {
            const Codec::Request expected{static_cast<std::uint8_t>(source),
                                          static_cast<std::uint8_t>(destination)};
            const auto wire=Codec::encode(expected);
            require(wire[0]==0x24 && wire[1]==source && wire[2]==destination);
            const auto actual=Codec::decode(wire);
            require(actual && *actual==expected);
        }
    }
    for (unsigned opcode=0; opcode<256; ++opcode) {
        const std::array<std::uint8_t,3> bytes{static_cast<std::uint8_t>(opcode),5,12};
        require(Codec::decode(bytes).has_value()==(opcode==0x24));
    }
    for (std::size_t size=0; size<=8; ++size) {
        const std::vector<std::uint8_t> bytes(size,0x24);
        require(Codec::decode(bytes).has_value()==(size==3));
    }
    // Batch interface lets the native oracle test this exact production header.
    std::string hex;
    while (std::cin >> hex) {
        if (hex.size()!=6 || hex.find_first_not_of("0123456789abcdefABCDEF")!=std::string::npos)
            return 2;
        std::array<std::uint8_t,3> bytes{};
        for (std::size_t i=0; i<bytes.size(); ++i)
            bytes[i]=static_cast<std::uint8_t>(std::stoul(hex.substr(i*2,2),nullptr,16));
        const auto request=Codec::decode(bytes);
        if (!request) return 3;
        std::cout << static_cast<unsigned>(request->source_slot) << ' '
                  << static_cast<unsigned>(request->destination_slot) << '\n';
    }
    return 0;
}
