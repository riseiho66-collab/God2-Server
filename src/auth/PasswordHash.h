#pragma once

#include <string>
#include <string_view>

namespace god2 {

class PasswordHash {
public:
    // Passwords are raw bytes (including NUL), at most 1024 bytes; empty is valid.
    // Format: god2$pbkdf2-sha256$v1$600000$<32 lowercase hex>$<64 lowercase hex>.
    // create throws invalid_argument for oversized input and runtime_error if
    // secure hashing is unavailable or fails. No plaintext fallback is provided.
    static std::string create(std::string_view password);

    // Invalid input, unsupported platforms and crypto failures return false.
    // Only the exact version, fixed rounds and canonical encoding above are valid.
    static bool verify(std::string_view password, std::string_view encoded);
};

} // namespace god2
