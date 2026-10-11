#pragma once
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace god2 {
// Native6F 52F170/52F330 script conversion, qualified for a15-byte role field.
// Predicts the destination bytes; rejects malformed input, substitutions,
// best-fit losses and original intermediate/output capacity overflow.
// Does not change the bytes sent in6F or any shared chat/name codec.
struct NativePeerRoleTextCodec {
    static std::optional<std::string> project(std::string_view source,
        std::uint16_t source_codepage,std::uint16_t recipient_codepage);
};
}
