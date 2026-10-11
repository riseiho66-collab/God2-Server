#pragma once
#include <string>
#include <string_view>
#include <cstddef>

namespace god2 {
// Explicit code pages used by the original Windows client, independent of the
// server host's system locale. Throws on malformed input or output overflow.
struct LegacyChineseCodec {
    struct DisplayText {
        std::string bytes;
        std::size_t replacements=0;
        bool truncated=false;
    };
    static std::string decode(std::string_view bytes,bool simplified);
    static std::string encode(std::string_view utf8,bool simplified);
    // Encode a client display field without disconnecting the sender for a
    // character unavailable in the recipient code page or an expanded phrase.
    static DisplayText encode_display(std::string_view utf8,bool simplified,
        std::size_t max_bytes=254);
};
}
