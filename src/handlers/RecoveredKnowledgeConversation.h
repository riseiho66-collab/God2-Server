#pragma once
#include "protocol/RecoveredQuestAction.h"
#include "protocol/RecoveredQuestDialogue.h"
#include <map>
#include <optional>

namespace god2 {
// CUSTOM-0043: bounded dialogue lifecycle, not original quest/event authority.
// Game-executor confined. Opening requires the caller's scene/NPC authority;
// isolated menu tests use explicit synthetic authority and never spawn an NPC.
class RecoveredKnowledgeConversation {
    struct Bound {
        std::uint64_t account,character;
        std::uint16_t request;
        std::uint8_t context;
        bool consumed=false;
        bool closed=false;
    };
    std::map<std::uint64_t,Bound> bound_;
public:
    std::optional<RecoveredQuestDialogue::KnowledgeMenu> open(
        std::uint64_t session,std::uint64_t account,std::uint64_t character,
        std::uint32_t request,std::uint32_t context,std::uint32_t source_count) {
        if(!session || !account || !character || bound_.contains(session))return std::nullopt;
        const auto wire=RecoveredQuestDialogue::kunlun_knowledge_menu(request,context,source_count);
        if(!wire)return std::nullopt;
        bound_.emplace(session,Bound{account,character,static_cast<std::uint16_t>(request),
            static_cast<std::uint8_t>(context)});
        return wire;
    }
    std::optional<std::uint16_t> consume(std::uint64_t session,std::uint64_t account,
        std::uint64_t character,const RecoveredQuestAction::Request& action) {
        const auto it=bound_.find(session);
        if(it==bound_.end())return std::nullopt;
        auto& state=it->second;
        if(state.consumed || state.account!=account || state.character!=character ||
           state.request!=action.request_word || state.context!=action.context_byte ||
           action.reply_word>6)return std::nullopt;
        // The last native byte is uninitialized stack residue, never authority.
        state.consumed=true;
        return action.reply_word;
    }
    bool contains(std::uint64_t session) const {return bound_.contains(session);}
    bool close(std::uint64_t session,std::uint64_t account,std::uint64_t character) {
        const auto it=bound_.find(session);
        if(it==bound_.end() || it->second.account!=account || it->second.character!=character ||
           it->second.closed)return false;
        it->second.closed=true;it->second.consumed=true;return true;
    }
    void remove(std::uint64_t session) {bound_.erase(session);}
};
}
