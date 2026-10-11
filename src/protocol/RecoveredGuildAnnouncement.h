#pragma once
#include "text/LegacyChineseCodec.h"
#include <algorithm>
#include <cstdint>
#include <optional>
#include <span>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace god2 {
// NATIVE_VERIFIED current149c/currentc5d8: main27 ->4F2C10 edit;
// main28 ->4F2CE0 ->419090 native text rows ->4132E0 C2S79.
// S2C98 ->468C9E ->4F2D50 consumes a variable-U16 announcement.
// Evidence: artifacts/research/native-guild-membership-0078/
// guild-announcement-native-v01/native.json. These layouts grant no authority.
//
// Native4F2D50 copies WORD bytes from body (one byte past the logical record),
// clamped at1044. This codec emits a safe canonical subset: logical4..1044,
// WORD==logical size and a single final NUL. Do not append the consumer's
// overread as another wire byte. Native user-edit geometry limit is unqualified.
// Strict encoding/canonicality and optional bilingual representability are
// server validation, not recovered original server moderation/gameplay rules.
struct RecoveredGuildAnnouncement {
    static constexpr std::uint8_t request_opcode=0x79, update_opcode=0x98;
    static constexpr std::size_t minimum_logical_size=4, maximum_logical_size=1044;
    static constexpr std::size_t maximum_text_bytes=maximum_logical_size-minimum_logical_size;
    using Logical=std::vector<std::uint8_t>;
    struct Request {
        std::vector<std::uint8_t> text; // Bytes excluding NUL; empty clears, spaces remain spaces.
        bool operator==(const Request&) const=default;
    };
    struct BilingualText {
        Request traditional, simplified;
        bool operator==(const BilingualText&) const=default;
    };
    static bool canonical(const Request& request) noexcept {
        return request.text.size()<=maximum_text_bytes &&
            std::find(request.text.begin(),request.text.end(),0)==request.text.end();
    }
    static std::optional<Request> decode(std::span<const std::uint8_t> logical) {
        if(logical.size()<minimum_logical_size || logical.size()>maximum_logical_size ||
           logical[0]!=request_opcode || logical.back()!=0)return {};
        const auto size=std::size_t{logical[1]}+(std::size_t{logical[2]}<<8);
        if(size!=logical.size())return {};
        const auto text=logical.subspan(3,logical.size()-minimum_logical_size);
        if(std::find(text.begin(),text.end(),0)!=text.end())return {};
        return Request{{text.begin(),text.end()}};
    }
    static std::optional<Logical> encode_request(const Request& request) {
        return encode(request,request_opcode);
    }
    static std::optional<Logical> update(const Request& request) {
        return encode(request,update_opcode);
    }
    // Only selected-codepage canonical roundtrip; this does not imply the
    // same text is representable in the other locale. No replacements/truncation.
    static std::string text_utf8(const Request& request,std::uint16_t codepage) {
        const auto simplified=locale(codepage);
        if(!canonical(request))throw std::invalid_argument("Invalid announcement bytes");
        const auto bytes=byte_string(request);
        const auto utf8=LegacyChineseCodec::decode(bytes,simplified);
        if(LegacyChineseCodec::encode(utf8,simplified)!=bytes)
            throw std::invalid_argument("Announcement encoding is not lossless canonical text");
        return utf8;
    }
    static Request text_request(std::string_view utf8,std::uint16_t codepage) {
        const auto simplified=locale(codepage);
        if(utf8.find('\0')!=std::string_view::npos)
            throw std::invalid_argument("Announcement text contains NUL");
        // Bytes are bounded before passing into Win32's int-sized conversion.
        // Any representable CP950/936 text has UTF8 length <=3*legacy bytes.
        if(utf8.size()>maximum_text_bytes*3)
            throw std::invalid_argument("Announcement text exceeds native byte bounds");
        const auto bytes=LegacyChineseCodec::encode(utf8,simplified);
        if(bytes.size()>maximum_text_bytes || LegacyChineseCodec::decode(bytes,simplified)!=utf8)
            throw std::invalid_argument("Announcement text lacks a bounded lossless encoding");
        Request request{{bytes.begin(),bytes.end()}};
        if(!canonical(request))throw std::invalid_argument("Invalid announcement text");
        return request;
    }
    // Use only if the storage contract explicitly requires identical Unicode
    // across both locales. This is not traditional/simplified phrase conversion.
    static BilingualText bilingual_text(std::string_view utf8) {
        return {text_request(utf8,950),text_request(utf8,936)};
    }
private:
    static bool locale(std::uint16_t codepage) {
        if(codepage!=950 && codepage!=936)
            throw std::invalid_argument("Announcement codepage must be950 or936");
        return codepage==936;
    }
    static std::string byte_string(const Request& request) {
        if(request.text.empty())return {};
        return {reinterpret_cast<const char*>(request.text.data()),request.text.size()};
    }
    static std::optional<Logical> encode(const Request& request,std::uint8_t opcode) {
        if(!canonical(request))return {};
        const auto size=request.text.size()+minimum_logical_size;
        Logical result{opcode,static_cast<std::uint8_t>(size),static_cast<std::uint8_t>(size>>8)};
        result.reserve(size);result.insert(result.end(),request.text.begin(),request.text.end());
        result.push_back(0);return result;
    }
};
}
