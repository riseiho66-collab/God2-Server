#include "protocol/RecoveredNpcRecord.h"

#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using Record = god2::RecoveredNpcRecord;

static void require(bool condition) {
    if (!condition)
        throw std::runtime_error("NPC record contract check failed");
}

static std::vector<std::uint8_t> unhex(const std::string& text) {
    if (text == "-")
        return {};
    if (text.size() % 2)
        throw std::runtime_error("Odd hex length");
    std::vector<std::uint8_t> result;
    for (std::size_t i = 0; i < text.size(); i += 2) {
        const auto pair = text.substr(i, 2);
        if (pair.find_first_not_of("0123456789abcdefABCDEF") != std::string::npos)
            throw std::runtime_error("Invalid hex digit");
        result.push_back(static_cast<std::uint8_t>(std::stoul(pair, nullptr, 16)));
    }
    return result;
}

static void emit(const Record& record) {
    std::cout << record.rawSelector() << ' ' << record.primarySelector() << ' '
              << record.secondarySelector() << ' ' << record.x() << ' ' << record.y()
              << ' ' << static_cast<unsigned>(record.opaquePositionLowBits()) << ' ';
    for (const auto value : record.encode())
        std::cout << std::hex << std::setw(2) << std::setfill('0')
                  << static_cast<unsigned>(value);
    std::cout << std::dec << '\n';
}

static void selfTest() {
    Record::Bytes source;
    for (std::size_t i = 0; i < source.size(); ++i)
        source[i] = static_cast<std::uint8_t>(i * 11 + 7);
    source[0] = 0x72;
    source[17] |= 3;
    auto record = Record::parse(source);
    require(record.has_value());
    const auto original = source;
    source.fill(0);
    require(record->encode() == original); // Owned copy, independent input lifetime.
    auto encoded = record->encode();
    encoded.fill(0);
    require(record->encode() == original);
    for (std::size_t size = 0; size <= 64; ++size) {
        std::vector<std::uint8_t> input(size, 0xa5);
        if (size)
            input[0] = 0x72;
        require(Record::parse(input).has_value() == (size == 21));
    }
    for (unsigned opcode = 0; opcode < 256; ++opcode) {
        auto bytes = original;
        bytes[0] = static_cast<std::uint8_t>(opcode);
        require(Record::parse(bytes).has_value() == (opcode == 0x72));
    }
    for (const auto invalid : {0x8000ULL, 0x10000ULL, 0x100000000ULL,
                              std::numeric_limits<unsigned long long>::max()}) {
        require(!record->setPosition(invalid, 0));
        require(!record->setPosition(0, invalid));
        require(record->encode() == original);
    }
    require(!record->setRawSelector(0x100000000ULL));
    require(!record->setRawSelector(std::numeric_limits<std::uint64_t>::max()));
    require(record->encode() == original);
    require(record->setRawSelector(0xffffffffULL));
    require(record->rawSelector() == 0xffffffffU);
    require(record->primarySelector() == 65535 && record->secondarySelector() == 65535);
    require(record->setPosition(32767, 32767));
    require(record->packedPosition() == 0xffffffffU);
    require(record->setPosition(0, 0));
    require(record->packedPosition() == 3);
    const auto changed = record->encode();
    for (std::size_t i = 5; i < 17; ++i)
        require(changed[i] == original[i]);
    require(changed[0] == 0x72);
}

int main(int argc, char** argv) {
    try {
        if (argc == 1) {
            selfTest();
            std::cout << "NPC record C++20 checks passed\n";
            return 0;
        }
        const std::string mode = argv[1];
        if (argc != 2 || (mode != "--decode-lines" && mode != "--edit-lines"))
            return 2;
        std::string line;
        while (std::getline(std::cin, line)) {
            std::istringstream input(line);
            std::string hex;
            if (!(input >> hex))
                return 2;
            const auto bytes = unhex(hex);
            auto record = Record::parse(bytes);
            if (!record) {
                std::cout << "reject\n";
                continue;
            }
            if (mode == "--edit-lines") {
                std::uint64_t selector, x, y;
                if (!(input >> selector >> x >> y))
                    return 2;
                const auto before = record->encode();
                auto edited = *record;
                if (!edited.setRawSelector(selector) || !edited.setPosition(x, y)) {
                    require(record->encode() == before);
                    std::cout << "reject\n";
                    continue;
                }
                record = edited;
            }
            emit(*record);
        }
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
