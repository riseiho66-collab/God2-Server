#pragma once
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace god2 {
// Exact character-name identity at the existing common14-byte boundary.
// Encoding qualification only: no permission, uniqueness, script/display
// conversion, normalization, truncation, default replacement or native rule.
class OwnedCharacterNameText {
public:
    static std::optional<OwnedCharacterNameText> from_encoded(std::string_view,std::uint16_t codepage);
    static std::optional<OwnedCharacterNameText> from_utf8(std::string_view,std::uint16_t codepage);
    std::string_view encoded_bytes() const noexcept {return encoded_;}
    std::string_view original_utf8() const noexcept {return utf8_;}
    std::uint16_t codepage() const noexcept {return codepage_;}
private:
    OwnedCharacterNameText(std::string,std::string,std::uint16_t);
    std::string encoded_,utf8_;
    std::uint16_t codepage_;
};
}
