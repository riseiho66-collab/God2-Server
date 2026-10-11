#include "protocol/PacketReader.h"
#include "protocol/PacketWriter.h"
#include "net/Buffer.h"
#include "protocol/RecoveredSeedExchange.h"
#include "protocol/RecoveredPostSeed.h"
#include "protocol/RecoveredC2S0002.h"
#include "protocol/RecoveredLoginTerminal.h"
#include "protocol/RecoveredServerList.h"
#include <filesystem>
#include <fstream>
#include <iterator>
#include <array>
#include <bit>
#include <limits>
#include <stdexcept>

namespace {
void check(bool value) { if (!value) throw std::runtime_error("test_packet check failed"); }
template<class F> void rejects(F action) {
    try { action(); } catch (const std::runtime_error&) { return; }
    throw std::runtime_error("test_packet expected runtime_error");
}
}
void test_packet() {
    using namespace god2;
    check(RecoveredServerList::one_entry()==std::array<std::uint8_t,8>{8,0,1,1,0xfd,0xfe,0xfe,0xae});
    check(RecoveredLoginTerminal::success()==std::array<std::uint8_t,20>{
        0x14,0,7,7,0xfd,0xfd,0xfd,0xfd,0xfd,0xfd,0xfd,0xfd,0xfd,0xfd,0xfd,0xfd,0xfd,0xfd,0xba,0x15});
    check(RecoveredPostSeed::frame()==std::array<std::uint8_t,5>{5,0,0xfe,0x51,0x99});
    const auto root=std::filesystem::path(__FILE__).parent_path().parent_path();
    std::ifstream fixture(root/"artifacts/golden/post-seed/C2S_0002.bin",std::ios::binary);
    check(fixture.good());
    std::vector<std::uint8_t> captured((std::istreambuf_iterator<char>(fixture)),{});
    const auto parsed=RecoveredC2S0002::parse(captured);
    check(parsed.has_value() && parsed->consumed==176 && parsed->logical[0]==4);
    check(RecoveredC2S0002::encode(parsed->logical)==parsed->raw);
    for(auto length:{0u,1u,175u}) check(!RecoveredC2S0002::parse(std::span(captured).first(length)));
    auto invalid=captured;invalid[0]=177;check(!RecoveredC2S0002::parse(invalid));
    invalid=captured;invalid.push_back(0);check(!RecoveredC2S0002::parse(invalid));
    invalid=captured;invalid.back()^=1;check(!RecoveredC2S0002::parse(invalid));
    for(auto offset:{0u,24u,156u,167u}) {
        auto logical=parsed->logical;logical[offset]^=1;
        check(!RecoveredC2S0002::parse(RecoveredC2S0002::encode(logical)));
    }
    auto logical=parsed->logical;logical[157]^=0x80;
    const auto preserved=RecoveredC2S0002::parse(RecoveredC2S0002::encode(logical));
    check(preserved.has_value() && preserved->logical==logical);
    logical=parsed->logical;logical[165]=0xe8;logical[166]=3;
    check(!RecoveredC2S0002::parse(RecoveredC2S0002::encode(logical)));
    auto acknowledgement=parsed->logical;acknowledgement[0]=29;
    check(RecoveredC2S0002::response(*parsed)==RecoveredC2S0002::encode(acknowledgement));
    const auto seed_hello=RecoveredSeedExchange::hello();
    check(seed_hello.size()==19 && seed_hello[0]==19 && seed_hello[1]==0 && seed_hello[18]==0x4b);
    check(RecoveredSeedExchange::accepts(RecoveredSeedExchange::response));
    auto corrupt=RecoveredSeedExchange::response;corrupt[2]^=1;
    check(!RecoveredSeedExchange::accepts(corrupt));
    check(!RecoveredSeedExchange::accepts(std::span(RecoveredSeedExchange::response).first(18)));
    PacketWriter writer;
    writer.write_u8(0xAB);
    writer.write_u16(0x1234);
    writer.write_u32(0x89ABCDEF);
    writer.write_i32(std::numeric_limits<int32_t>::min());
    writer.write_float(1.5F);
    writer.write_string(std::string_view("a\0b", 3));
    writer.write_fixed_string("xy", 4);
    writer.write_bytes(std::array<uint8_t, 2>{0xFE, 0xFF});
    const std::vector<uint8_t> expected{0xAB,0x34,0x12,0xEF,0xCD,0xAB,0x89,
        0,0,0,0x80,0,0,0xC0,0x3F,3,0,'a',0,'b','x','y',0,0,0xFE,0xFF};
    check(writer.bytes() == expected);
    PacketReader reader(writer.bytes());
    check(reader.read_u8() == 0xAB);
    check(reader.read_u16() == 0x1234);
    check(reader.read_u32() == 0x89ABCDEF);
    check(reader.read_i32() == std::numeric_limits<int32_t>::min());
    check(reader.read_float() == 1.5F);
    check(reader.read_string() == std::string("a\0b", 3));
    check(reader.read_fixed_string(4) == "xy");
    check(reader.read_bytes(2) == std::vector<uint8_t>({0xFE,0xFF}));
    check(reader.remaining() == 0);
    rejects([&] { reader.read_u8(); });
    rejects([&] { reader.read_u16(); });
    rejects([&] { reader.read_u32(); });
    rejects([&] { reader.read_i32(); });
    rejects([&] { reader.read_float(); });
    rejects([&] { reader.read_string(); });
    rejects([&] { reader.read_fixed_string(1); });
    rejects([&] { reader.read_bytes(std::numeric_limits<size_t>::max()); });
    check(reader.remaining() == 0);
    check(reader.read_fixed_string(0).empty() && reader.read_bytes(0).empty());
    reader.reset_cursor();
    check(reader.remaining() == expected.size() && reader.read_u8() == 0xAB);
    const std::array<uint8_t, 3> truncated{3,0,'a'};
    PacketReader short_reader(truncated);
    rejects([&] { short_reader.read_string(); });
    check(short_reader.remaining() == truncated.size());
    for (size_t count = 0; count < 4; ++count) {
        const std::array<uint8_t, 4> scalar{};
        PacketReader partial(std::span<const uint8_t>(scalar).first(count));
        rejects([&] { partial.read_u32(); });
        rejects([&] { partial.read_i32(); });
        rejects([&] { partial.read_float(); });
        if (count < 2) rejects([&] { partial.read_u16(); });
        check(partial.remaining() == count);
    }
    const auto saved = writer.bytes();
    rejects([&] { writer.write_string(std::string(65536, 'x')); });
    rejects([&] { writer.write_fixed_string("abc", 2); });
    check(writer.bytes() == saved);
    PacketWriter edge;
    edge.write_string(""); edge.write_fixed_string("ab", 2); edge.write_string(std::string(65535, 'z'));
    PacketReader edge_reader(edge.bytes());
    check(edge_reader.read_string().empty());
    check(edge_reader.read_fixed_string(2) == "ab");
    check(edge_reader.read_string() == std::string(65535, 'z'));
    PacketWriter floating;
    floating.write_float(std::bit_cast<float>(uint32_t{0x7FC12345}));
    floating.write_float(-0.0F);
    PacketReader float_reader(floating.bytes());
    check(std::bit_cast<uint32_t>(float_reader.read_float()) == 0x7FC12345);
    check(std::bit_cast<uint32_t>(float_reader.read_float()) == 0x80000000);
    check(PacketReader(std::array<uint8_t, 2>{0,255}).hex_dump() == "00 ff");
    Buffer buffer;
    buffer.append(expected);
    buffer.consume(expected.size() - 2);
    buffer.append(buffer.data());
    check(buffer.size() == 4 && buffer.data()[0] == 0xFE && buffer.data()[2] == 0xFE);
    rejects([&] { buffer.consume(5); });
    check(buffer.size() == 4);
    buffer.consume(4);
    check(buffer.data().empty());
    buffer.append(std::span<const uint8_t>{});
    check(buffer.size() == 0);
}
