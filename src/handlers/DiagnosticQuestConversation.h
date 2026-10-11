#pragma once
#include "protocol/RecoveredQuestAction.h"
#include "protocol/DiagnosticTownNpc.h"
#include "game/RecoveredPosition.h"
#include <cstdint>
#include <map>
#include <optional>

namespace god2 {
// CUSTOM-0018: diagnostic dialogue with cancellation/reopen, no rewards.
// Game-executor confined. Native request words are not authoritative quest IDs.
class DiagnosticQuestConversation {
    struct Bound {
        std::uint64_t account, character;
        bool opened=false, consumed=false, npc_spawned=false;
        bool cancelled=false;
        bool followup=false;
        std::uint16_t request_word=0x1234;
    };
    std::map<std::uint64_t,Bound> bound_;
public:
    bool bind(std::uint64_t session,std::uint64_t account,std::uint64_t character) {
        return session && account && character &&
            bound_.try_emplace(session,Bound{account,character}).second;
    }
    bool open(std::uint64_t session,std::uint64_t account,std::uint64_t character) {
        const auto word=next_request_word(session,account,character);
        if(!word) return false;
        const auto it=bound_.find(session);
        it->second.request_word=*word;
        it->second.opened=true;
        it->second.consumed=false;it->second.cancelled=false;it->second.followup=false;
        return true;
    }
    std::optional<std::uint16_t> next_request_word(std::uint64_t session,std::uint64_t account,
                                                  std::uint64_t character) const {
        const auto it=bound_.find(session);
        if(it==bound_.end() || it->second.account!=account || it->second.character!=character)
            return std::nullopt;
        const auto& state=it->second;
        if(!state.opened) return state.request_word;
        if((!state.cancelled && !state.followup) || state.request_word==0xffff) return std::nullopt;
        return static_cast<std::uint16_t>(state.request_word+1);
    }
    bool spawn(std::uint64_t session,std::uint64_t account,std::uint64_t character) {
        const auto it=bound_.find(session);
        if(it==bound_.end() || it->second.account!=account || it->second.character!=character ||
           it->second.npc_spawned || (it->second.opened && !it->second.cancelled)) return false;
        it->second.npc_spawned=true;return true;
    }
    // CUSTOM-0025: scene-local NPCs disappear; retain request history against replay.
    bool leave_scene(std::uint64_t session,std::uint64_t account,std::uint64_t character) {
        const auto it=bound_.find(session);
        if(it==bound_.end() || it->second.account!=account || it->second.character!=character)
            return false;
        auto& state=it->second;
        state.npc_spawned=false;
        if(state.opened) {
            state.consumed=true;state.cancelled=true;state.followup=false;
        }
        return true;
    }
    bool open_npc(std::uint64_t session,std::uint64_t account,std::uint64_t character,
                  std::uint32_t target,const RecoveredPosition& position) {
        const auto it=bound_.find(session);
        // Server policy mirrors observed per-axis range, not an original server rule.
        if(it==bound_.end() || !it->second.npc_spawned || target!=531 ||
           position.area!=2 || position.scene!=15 || position.x<14 || position.x>20 ||
           position.y<9 || position.y>15) return false;
        return open(session,account,character);
    }
    bool consume(std::uint64_t session,std::uint64_t account,std::uint64_t character,
                 const RecoveredQuestAction::Request& request) {
        return consume_after_commit(session,account,character,request,[]{});
    }
    bool can_consume(std::uint64_t session,std::uint64_t account,std::uint64_t character,
                     const RecoveredQuestAction::Request& request) const {
        const auto it=bound_.find(session);
        if(it==bound_.end()) return false;
        const auto& bound=it->second;
        return bound.account==account && bound.character==character && bound.opened &&
            !bound.consumed && request.request_word==bound.request_word &&
            request.reply_word==2 && request.context_byte==0x9a;
    }
    // CUSTOM-0020: explicit town test placements, no native spawn/quest claim.
    bool open_town_npc(std::uint64_t session,std::uint64_t account,std::uint64_t character,
                       std::uint32_t target,const RecoveredPosition& position) {
        const auto it=bound_.find(session);
        if(it==bound_.end() || !it->second.npc_spawned || position.area!=2 || position.scene!=4)
            return false;
        return DiagnosticTownNpc::nearby(target,position.x,position.y) && open(session,account,character);
    }
    // Callback must commit atomically and must not re-enter this confined service.
    // A failed commit leaves the confirmation available for an explicit retry.
    template<class Commit>
    bool consume_after_commit(std::uint64_t session,std::uint64_t account,std::uint64_t character,
                 const RecoveredQuestAction::Request& request,Commit&& commit) {
        if(!can_consume(session,account,character,request)) return false;
        auto& bound=bound_.at(session);
        // Native opaque_tail is stack residue and cannot authorize a conversation.
        commit();
        bound.consumed=true;
        return true;
    }
    void remove(std::uint64_t session) { bound_.erase(session); }
    // CUSTOM-0021: explicitly rearm only after a successfully committed response.
    // Old confirmations remain consumed; open assigns the next request word.
    bool allow_followup(std::uint64_t session,std::uint64_t account,std::uint64_t character) {
        const auto it=bound_.find(session);
        if(it==bound_.end() || it->second.account!=account || it->second.character!=character ||
           !it->second.opened || !it->second.consumed || it->second.cancelled || it->second.followup)
            return false;
        it->second.followup=true;
        return true;
    }
    // CUSTOM-0018: cancellation is authorized by the bound conversation only.
    // Neither opaque close word grants quest or reward authority.
    bool can_cancel(std::uint64_t session,std::uint64_t account,std::uint64_t character) const {
        const auto it=bound_.find(session);
        return it!=bound_.end() && it->second.account==account && it->second.character==character &&
            it->second.opened && !it->second.consumed;
    }
    bool cancel(std::uint64_t session,std::uint64_t account,std::uint64_t character) {
        if(!can_cancel(session,account,character)) return false;
        const auto it=bound_.find(session);
        it->second.consumed=true;it->second.cancelled=true;return true;
    }
};
}
