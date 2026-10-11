#pragma once
#include "protocol/RecoveredRemoteActor.h"
#include "protocol/RecoveredRoleText.h"

namespace god2 {
// Current6F: logical bytes45..60 -> remote actor+0x14 -> renderer+0x81.
// Repeating6F replaces the complete native actor and clears its movement queue;
// callers must provide the latest owned position/appearance/presence snapshot.
// This adapter preserves every byte outside the secondary field, including the
// three fields' shared source-language bit25. No separate opcode is invented.
struct RecoveredRemoteRoleText {
    using Record=RecoveredRemoteActor::Record;
    using Text=RecoveredRoleText::Text;
    static std::uint16_t source_codepage(const Record& source) noexcept {
        return (RecoveredRemoteActor::encode_logical(source)[4]&2u)?936:950;
    }
    static std::optional<Record> with_source_text(const Record& source,const Text& text) noexcept {
        if(!RecoveredRoleText::update(text))return std::nullopt;
        auto bytes=RecoveredRemoteActor::encode_logical(source);
        std::copy(text.begin(),text.end(),bytes.begin()+45);
        return RecoveredRemoteActor::parse_logical(bytes);
    }
};
}
