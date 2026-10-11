#include "tools/ProtocolReplayTool.h"
#include "protocol/God2ProtocolSpec.h"
#include <sstream>
#include <stdexcept>

namespace {
void check(bool value) { if (!value) throw std::runtime_error("test_protocol_replay check failed"); }
}
void test_protocol_replay() {
    using namespace god2;
    God2ProtocolSpec spec;
    ProtocolReplayTool tool(spec);
    check(ProtocolReplayTool::parse_hex("\tAa00 ff\r\n") == std::vector<uint8_t>({0xAA,0,0xFF}));
    const auto result = tool.replay_hex("07 00 01 10 aa bb cc\n04000510");
    check(result.status.ok && result.packets.size() == 2 && result.remaining_bytes == 0);
    check(result.packets[0].opcode == 0x1001 && result.packets[0].payload == std::vector<uint8_t>({0xAA,0xBB,0xCC}));
    check(result.lengths == std::vector<size_t>({7,4}));
    std::ostringstream output;
    ProtocolReplayTool::print(result, output);
    check(output.str() == "length=7 opcode=0x1001 payload=aa bb cc\nlength=4 opcode=0x1005 payload=\n");
    for (auto invalid : {"0", "0g", "0x04", "0 4", "04,00", "04:00"}) {
        check(!tool.replay_hex(invalid).status.ok);
        bool threw = false;
        try { ProtocolReplayTool::parse_hex(invalid); } catch (const std::runtime_error&) { threw = true; }
        check(threw);
    }
    const auto truncated = tool.replay_hex("04000510 07000110aa");
    check(!truncated.status.ok && truncated.packets.size() == 1 && truncated.remaining_bytes == 5);
    check(truncated.status.error.find("Truncated") != std::string::npos);
    const auto malformed = tool.replay_hex("03000110");
    check(!malformed.status.ok && malformed.status.error.find("header") != std::string::npos);
    std::ostringstream error;
    ProtocolReplayTool::print(malformed, error);
    check(error.str().find("parse error:") == 0);
    check(tool.replay_hex("").status.ok && tool.replay_hex(" \n\t").packets.empty());
    check(tool.replay_hex("04000510").status.ok);
}
