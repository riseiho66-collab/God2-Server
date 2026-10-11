#include "auth/PasswordHash.h"

#include <array>
#include <stdexcept>

#ifdef _WIN32
#ifndef NOMINMAX
#define NOMINMAX
#endif
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>
#include <bcrypt.h>
#endif

namespace god2 {
namespace {

constexpr std::size_t max_password_bytes = 1024;

#ifdef _WIN32
constexpr std::string_view prefix = "god2$pbkdf2-sha256$v1$600000$";
constexpr ULONGLONG iterations = 600000;
using Salt = std::array<unsigned char, 16>;
using Digest = std::array<unsigned char, 32>;
constexpr std::size_t salt_hex_size = 2 * Salt{}.size();
constexpr std::size_t digest_hex_size = 2 * Digest{}.size();
constexpr std::size_t encoded_size = prefix.size() + salt_hex_size + 1 + digest_hex_size;

struct SecretDigest {
    Digest bytes{};
    ~SecretDigest() { SecureZeroMemory(bytes.data(), bytes.size()); }
};

int hex_value(char value) {
    if (value >= '0' && value <= '9') return value - '0';
    if (value >= 'a' && value <= 'f') return value - 'a' + 10;
    return -1;
}

template<std::size_t N>
bool decode_hex(std::string_view encoded, std::array<unsigned char, N>& bytes) {
    if (encoded.size() != 2 * N) return false;
    for (std::size_t i = 0; i < N; ++i) {
        const int high = hex_value(encoded[2 * i]);
        const int low = hex_value(encoded[2 * i + 1]);
        if (high < 0 || low < 0) return false;
        bytes[i] = static_cast<unsigned char>((high << 4) | low);
    }
    return true;
}

template<std::size_t N>
void append_hex(std::string& encoded, const std::array<unsigned char, N>& bytes) {
    constexpr char alphabet[] = "0123456789abcdef";
    for (const unsigned char byte : bytes) {
        encoded.push_back(alphabet[byte >> 4]);
        encoded.push_back(alphabet[byte & 15]);
    }
}

bool derive(std::string_view password, Salt& salt, Digest& digest) {
    BCRYPT_ALG_HANDLE algorithm = nullptr;
    const NTSTATUS opened = BCryptOpenAlgorithmProvider(
        &algorithm, BCRYPT_SHA256_ALGORITHM, MS_PRIMITIVE_PROVIDER,
        BCRYPT_ALG_HANDLE_HMAC_FLAG);
    if (!BCRYPT_SUCCESS(opened)) return false;

    // CNG declares the password mutable, but documents it as an input byte buffer.
    // The public entry points check the byte limit before this ULONG conversion.
    const NTSTATUS derived = BCryptDeriveKeyPBKDF2(
        algorithm,
        password.empty() ? nullptr : reinterpret_cast<PUCHAR>(const_cast<char*>(password.data())),
        static_cast<ULONG>(password.size()), salt.data(), static_cast<ULONG>(salt.size()),
        iterations, digest.data(), static_cast<ULONG>(digest.size()), 0);
    const NTSTATUS closed = BCryptCloseAlgorithmProvider(algorithm, 0);
    return BCRYPT_SUCCESS(derived) && BCRYPT_SUCCESS(closed);
}

bool equal_digest(const Digest& left, const Digest& right) {
    // Volatile accesses retain every byte comparison, with no mismatch exit.
    volatile unsigned int difference = 0;
    for (std::size_t i = 0; i < left.size(); ++i) {
        difference = difference | static_cast<unsigned int>(left[i] ^ right[i]);
    }
    return difference == 0;
}
#endif

} // namespace

std::string PasswordHash::create(std::string_view password) {
    if (password.size() > max_password_bytes) {
        throw std::invalid_argument("Password exceeds hashing byte limit");
    }
#ifdef _WIN32
    Salt salt{};
    const NTSTATUS random = BCryptGenRandom(
        nullptr, salt.data(), static_cast<ULONG>(salt.size()), BCRYPT_USE_SYSTEM_PREFERRED_RNG);
    if (!BCRYPT_SUCCESS(random)) {
        throw std::runtime_error("Password hash random generation failed");
    }
    SecretDigest digest;
    if (!derive(password, salt, digest.bytes)) {
        throw std::runtime_error("Password hash derivation failed");
    }
    std::string encoded;
    encoded.reserve(encoded_size);
    encoded.append(prefix);
    append_hex(encoded, salt);
    encoded.push_back('$');
    append_hex(encoded, digest.bytes);
    return encoded;
#else
    throw std::runtime_error("Password hashing is unavailable on this platform");
#endif
}

bool PasswordHash::verify(std::string_view password, std::string_view encoded) {
    if (password.size() > max_password_bytes) return false;
#ifdef _WIN32
    // Fully validate the fixed-size format before opening a provider or deriving.
    // Never parse an attacker-controlled iteration count or allocate from input.
    if (encoded.size() != encoded_size || encoded.substr(0, prefix.size()) != prefix ||
        encoded[prefix.size() + salt_hex_size] != '$') {
        return false;
    }
    Salt salt{};
    SecretDigest expected;
    if (!decode_hex(encoded.substr(prefix.size(), salt_hex_size), salt) ||
        !decode_hex(encoded.substr(prefix.size() + salt_hex_size + 1), expected.bytes)) {
        return false;
    }
    SecretDigest actual;
    if (!derive(password, salt, actual.bytes))
        throw std::runtime_error("Password verification provider failed");
    return equal_digest(actual.bytes, expected.bytes);
#else
    (void)encoded;
    return false;
#endif
}

} // namespace god2
