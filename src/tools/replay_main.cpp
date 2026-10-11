#include "protocol/God2ProtocolSpec.h"
#include "tools/ProtocolReplayTool.h"
#include <fstream>
#include <iostream>
#include <iterator>
#include <stdexcept>
#include <string>

int main(int argc, char** argv) {
    try {
        std::string hex;
        if (argc == 2 && std::string(argv[1]) == "--help") {
            std::cout << "PLACEHOLDER - waiting for real GOD2 reverse engineering result\n"
                      << "Usage: protocol_replay [HEX ... | --file PATH]\n"
                      << "With no arguments, reads hex text from stdin.\n";
            return 0;
        }
        if (argc > 1 && std::string(argv[1]) == "--file") {
            if (argc != 3) throw std::runtime_error("--file requires exactly one path");
            std::ifstream input(argv[2], std::ios::binary);
            if (!input) throw std::runtime_error("Cannot open hex input file");
            hex.assign(std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>());
            if (input.bad()) throw std::runtime_error("Cannot read hex input file");
        } else if (argc > 1) {
            for (int i = 1; i < argc; ++i) {
                if (i != 1) hex += ' ';
                hex += argv[i];
            }
        } else {
            hex.assign(std::istreambuf_iterator<char>(std::cin), std::istreambuf_iterator<char>());
            if (std::cin.bad()) throw std::runtime_error("Cannot read stdin");
        }
        god2::God2ProtocolSpec spec;
        god2::ProtocolReplayTool tool(spec);
        const auto result = tool.replay_hex(hex);
        god2::ProtocolReplayTool::print(result, std::cout);
        return result.status.ok ? 0 : 1;
    } catch (const std::exception& error) {
        std::cerr << "parse error: " << error.what() << '\n';
        return 1;
    }
}
