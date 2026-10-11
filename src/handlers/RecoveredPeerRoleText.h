#pragma once
#include "db/SqliteRoleTextRepository.h"
#include "protocol/RecoveredRemoteRoleText.h"
#include "text/NativePeerRoleTextCodec.h"

namespace god2 {
// CUSTOM-0056: project owned secondary text without changing the primary name,
// third text, common language flag, appearance or location. A failed projection
// clears only secondary display; the stored Unicode/source bytes remain intact.
struct RecoveredPeerRoleText {
    struct Projection {
        RecoveredRemoteActor::Record spawn;
        std::optional<RecoveredRoleText::Text> recipient_text;
        bool displayed=false;
    };
    static Projection per_recipient(const RecoveredRemoteActor::Record& source,
        const std::optional<StoredRoleText>& saved,std::uint16_t recipient_codepage) {
        if(recipient_codepage!=936 && recipient_codepage!=950)
            throw std::invalid_argument("Peer role recipient codepage rejected");
        RecoveredRoleText::Text blank{};
        Projection result{RecoveredRemoteRoleText::with_source_text(source,blank).value(),blank,false};
        if(!saved)return result;
        const auto page=RecoveredRemoteRoleText::source_codepage(source);
        const auto projected=SqliteRoleTextRepository::project(*saved,page);
        if(!projected) {result.recipient_text.reset();return result;}
        const auto end=std::find(projected->begin(),projected->end(),0);
        const std::string_view bytes(reinterpret_cast<const char*>(projected->data()),static_cast<std::size_t>(end-projected->begin()));
        const auto decoded=NativePeerRoleTextCodec::project(bytes,page,recipient_codepage);
        if(!decoded) {result.recipient_text.reset();return result;}
        result.spawn=RecoveredRemoteRoleText::with_source_text(source,*projected).value();
        RecoveredRoleText::Text receiver{};
        std::copy(decoded->begin(),decoded->end(),receiver.begin());result.recipient_text=receiver;result.displayed=true;
        return result;
    }
};
}
