#include "auth/PasswordHash.h"

#include <stdexcept>
#include <string>
#include <string_view>

#ifdef GOD2_PASSWORD_HASH_STANDALONE
#include <iostream>
#endif

namespace {

void require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}

constexpr std::string_view prefix = "god2$pbkdf2-sha256$v1$600000$";
constexpr std::size_t salt_offset = prefix.size();
constexpr std::size_t digest_offset = salt_offset + 32 + 1;
constexpr std::size_t encoded_size = digest_offset + 64;

// Independently computed with Python hashlib.pbkdf2_hmac('sha256', ...).
constexpr std::string_view known_hash =
    "god2$pbkdf2-sha256$v1$600000$000102030405060708090a0b0c0d0e0f$"
    "459a332cb9ab2b5549552e7f7a355f83c7b7bee21e4dc36dd45126422a6fd532";
constexpr char binary_password[] = "pass\0word\x80\xff";
constexpr std::string_view binary_view{binary_password, sizeof(binary_password) - 1};

} // namespace

void test_password_hash() {
    using god2::PasswordHash;

    const std::string too_long(1025, 'x');
    bool rejected = false;
    try {
        (void)PasswordHash::create(too_long);
    } catch (const std::invalid_argument&) {
        rejected = true;
    }
    require(rejected, "oversized create must reject input");
    require(!PasswordHash::verify(too_long, known_hash), "oversized verify must reject input");
    require(!PasswordHash::verify(binary_view, std::string(1024 * 1024, 'x')),
            "oversized encoding must reject input");

    for (std::size_t length = 0; length < known_hash.size(); ++length) {
        require(!PasswordHash::verify(binary_view, known_hash.substr(0, length)),
                "truncated encoding must reject input");
    }
    for (const std::string_view invalid : {"", "plaintext", "$2b$12$legacy", "pass"}) {
        require(!PasswordHash::verify(binary_view, invalid), "unknown encoding must reject input");
    }
    constexpr std::string_view suffixes[] = {"x", "$", "\n", std::string_view("\0", 1)};
    for (const auto suffix : suffixes) {
        require(!PasswordHash::verify(binary_view, std::string(known_hash) + std::string(suffix)),
                "trailing bytes must reject input");
    }
    // Every fixed header byte is significant, including algorithm/version/rounds.
    for (std::size_t i = 0; i < prefix.size(); ++i) {
        std::string malformed(known_hash);
        malformed[i] = '!';
        require(!PasswordHash::verify(binary_view, malformed), "modified header must reject input");
    }
    for (const std::string_view rounds : {"0", "1", "0600000", "600001", "999999",
                                         "-600000", "18446744073709551615"}) {
        std::string malformed(known_hash);
        malformed.replace(prefix.size() - 7, 6, rounds);
        require(!PasswordHash::verify(binary_view, malformed), "noncanonical rounds must reject input");
    }
    for (const std::size_t index : {salt_offset, salt_offset + 31, salt_offset + 32,
                                   digest_offset, encoded_size - 1}) {
        for (const char invalid : {'g', 'A', '\0', '\n', static_cast<char>(0xff)}) {
            std::string malformed(known_hash);
            malformed[index] = invalid;
            require(!PasswordHash::verify(binary_view, malformed), "invalid hex or separator must reject input");
        }
    }
    std::string short_salt(known_hash);
    short_salt.erase(salt_offset, 2);
    short_salt.append("00");
    require(!PasswordHash::verify(binary_view, short_salt), "wrong salt width must reject input");
    std::string long_salt(known_hash);
    long_salt.insert(salt_offset, "00");
    long_salt.resize(encoded_size);
    require(!PasswordHash::verify(binary_view, long_salt), "wrong digest width must reject input");

#ifdef _WIN32
    require(PasswordHash::verify(binary_view, known_hash), "independent PBKDF2 vector must match");
    require(!PasswordHash::verify("pass", known_hash), "embedded NUL must not truncate password");
    std::string changed(binary_view);
    changed.back() = static_cast<char>(0xfe);
    require(!PasswordHash::verify(changed, known_hash), "high password bytes must be significant");

    const auto first = PasswordHash::create("matching password");
    const auto second = PasswordHash::create("matching password");
    require(first.size() == encoded_size && first.substr(0, prefix.size()) == prefix,
            "created hash must have canonical format");
    require(second.size() == encoded_size, "created hash must have fixed length");
    require(first.substr(salt_offset, 32) != second.substr(salt_offset, 32),
            "independent hashes must use random salts");
    require(PasswordHash::verify("matching password", first), "matching password must verify");
    require(PasswordHash::verify("matching password", second), "second salt must verify");
    require(!PasswordHash::verify("wrong password", first), "wrong password must fail");
    for (const std::size_t index : {digest_offset, encoded_size - 1}) {
        std::string changed_hash(first);
        changed_hash[index] = changed_hash[index] == '0' ? '1' : '0';
        require(!PasswordHash::verify("matching password", changed_hash), "digest mismatch must fail");
    }

    const auto binary_hash = PasswordHash::create(binary_view);
    require(PasswordHash::verify(binary_view, binary_hash), "binary password must round trip");
    require(!PasswordHash::verify("pass", binary_hash), "binary round trip must preserve NUL suffix");
    const auto empty_hash = PasswordHash::create(std::string_view{});
    require(PasswordHash::verify(std::string_view{}, empty_hash), "empty password must round trip");
    require(!PasswordHash::verify("x", empty_hash), "nonmatching empty password must fail");
    const std::string at_limit(1024, 'x');
    const auto limit_hash = PasswordHash::create(at_limit);
    require(PasswordHash::verify(at_limit, limit_hash), "maximum password size must round trip");
    require(!PasswordHash::verify(too_long, limit_hash), "oversized password must not be truncated");
    require(!PasswordHash::verify(std::string_view(at_limit).substr(0, 1023), limit_hash),
            "password length must be significant");
#else
    bool unavailable = false;
    try {
        (void)PasswordHash::create("password");
    } catch (const std::runtime_error&) {
        unavailable = true;
    }
    require(unavailable, "unsupported platform must fail closed on create");
    require(!PasswordHash::verify(binary_view, known_hash), "unsupported platform must fail closed on verify");
#endif
}

#ifdef GOD2_PASSWORD_HASH_STANDALONE
int main() {
    try {
        test_password_hash();
    } catch (const std::exception& error) {
        std::cerr << "FAIL password_hash: " << error.what() << '\n';
        return 1;
    }
    std::cout << "PASS password_hash\n";
    return 0;
}
#endif
