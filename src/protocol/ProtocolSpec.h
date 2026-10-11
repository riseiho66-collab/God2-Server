#pragma once
#include "net/Buffer.h"
#include "protocol/Packet.h"
#include <string>

namespace god2 {
class Session;
struct DecodeResult {
    bool ok = true;
    std::string error;
};
class ProtocolSpec {
public:
    virtual ~ProtocolSpec() = default;
    virtual size_t header_size() const = 0;
    // Appends complete packets; leaves incomplete or invalid frames buffered.
    virtual DecodeResult try_decode(Buffer& input, std::vector<Packet>& outPackets) = 0;
    virtual std::vector<uint8_t> encode(const Packet& packet) = 0;
    virtual void on_session_created(Session&) {}
    virtual void on_session_authenticated(Session&) {}
};
}
