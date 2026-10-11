#include "protocol/God2ProtocolSpec.h"
#include "protocol/PacketDecoder.h"
#include "protocol/PacketEncoder.h"
#include <array>
#include <stdexcept>

namespace {
void check(bool value) { if (!value) throw std::runtime_error("test_decoder check failed"); }
template<class F> void rejects(F action) {
    try { action(); } catch (const std::runtime_error&) { return; }
    throw std::runtime_error("test_decoder expected runtime_error");
}
}
void test_decoder() {
    using namespace god2;
    God2ProtocolSpec spec;
    PacketEncoder encoder(spec);
    PacketDecoder decoder(spec);
    const Packet packet{0x1001, {0xAA, 0xBB, 0xCC}};
    const auto wire = encoder.encode(packet);
    check(wire == std::vector<uint8_t>({7,0,1,0x10,0xAA,0xBB,0xCC}));
    for (size_t split = 0; split <= wire.size(); ++split) {
        Buffer input;
        std::vector<Packet> out;
        input.append(std::span<const uint8_t>(wire).first(split));
        check(decoder.decode(input, out).ok);
        if (split < wire.size()) check(out.empty() && input.size() == split);
        input.append(std::span<const uint8_t>(wire).subspan(split));
        check(decoder.decode(input, out).ok);
        check(out.size() == 1 && out[0].opcode == packet.opcode && out[0].payload == packet.payload);
        check(input.size() == 0);
    }
    Buffer input;
    std::vector<Packet> out;
    for (const uint8_t byte : wire) {
        input.append(std::span<const uint8_t>(&byte, 1));
        check(decoder.decode(input, out).ok);
    }
    check(out.size() == 1);
    out.clear();
    const auto empty = encoder.encode(Packet{0xFFFF, {}});
    input.append(wire); input.append(empty); input.append(std::span<const uint8_t>(wire).first(3));
    check(decoder.decode(input, out).ok);
    check(out.size() == 2 && out[1].opcode == 0xFFFF && out[1].payload.empty() && input.size() == 3);
    input.append(std::span<const uint8_t>(wire).subspan(3));
    check(decoder.decode(input, out).ok && out.size() == 3 && input.size() == 0);
    for (uint8_t length = 0; length < 4; ++length) {
        Buffer bad;
        bad.append(std::array<uint8_t, 2>{length, 0});
        const auto status = decoder.decode(bad, out);
        check(!status.ok && !status.error.empty() && bad.size() == 2);
    }
    Buffer mixed;
    mixed.append(wire); mixed.append(std::array<uint8_t, 2>{1,0});
    out.clear();
    check(!decoder.decode(mixed, out).ok && out.size() == 1 && mixed.size() == 2);
    Packet maximum{0x1234, std::vector<uint8_t>(65531, 0xA5)};
    Buffer large;
    large.append(encoder.encode(maximum));
    out.clear();
    check(decoder.decode(large, out).ok && out.size() == 1 && out[0].payload == maximum.payload);
    maximum.payload.push_back(0);
    rejects([&] { encoder.encode(maximum); });
    God2ProtocolSpec small(6);
    Buffer over;
    over.append(wire);
    check(!small.try_decode(over, out).ok && over.size() == wire.size());
    rejects([&] { small.encode(packet); });
    rejects([] { God2ProtocolSpec invalid(3); });
    rejects([] { God2ProtocolSpec invalid(65536); });
    rejects([] { CryptoPipeline invalid("xor"); });
    rejects([] { CompressionPipeline invalid("zlib"); });
    rejects([] { God2ProtocolSpec invalid(65535, "xor"); });
    rejects([] { God2ProtocolSpec invalid(65535, "none", "zlib"); });
    CryptoPipeline crypto;
    CompressionPipeline compression;
    check(crypto.encrypt(wire) == wire && crypto.decrypt(wire) == wire);
    check(compression.compress(wire) == wire && compression.decompress(wire) == wire);
}
