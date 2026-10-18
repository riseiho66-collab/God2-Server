#pragma once
#include "protocol/RecoveredTaiwanServerRecords.h"
#include "protocol/RecoveredWorldFrame.h"
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <span>

namespace god2 {
// Sender custody of one actual original world-entry Write only. This is not
// current client R0, native selfslot, a remote ACK or battle permission.
class TaiwanWorldIdentityWriteFence final {
public:
    enum class State {Unbound,BaselineQueued,BaselineWritten,Revoked};
    TaiwanWorldIdentityWriteFence()=default;
    TaiwanWorldIdentityWriteFence(const TaiwanWorldIdentityWriteFence&)=delete;
    TaiwanWorldIdentityWriteFence& operator=(const TaiwanWorldIdentityWriteFence&)=delete;

    bool admit_original() noexcept {
        auto expected=State::Unbound;
        if(state_.compare_exchange_strong(expected,State::BaselineQueued))return true;
        revoke();return false; // Duplicate admission cannot replace its source.
    }
    bool complete_original(bool exact_whole_write) noexcept {
        if(exact_whole_write){
            auto expected=State::BaselineQueued;
            if(state_.compare_exchange_strong(expected,State::BaselineWritten))return true;
        }
        revoke();return false; // Failed, duplicate or late completion never revives.
    }
    void revoke() noexcept {state_.store(State::Revoked);}
    bool eligible() const noexcept {return state()==State::BaselineWritten;}
    State state() const noexcept {return state_.load();}

    // The actual Session calls this only while it retains a live original
    // world Entry, including CharacterSelected and InBattle. Complete Net-to-
    // receiver phase routing is unqualified; current phase grants no exemption.
    // Inspect complete framed records, never opcode-looking opaque substrings.
    // World1C/battle1C and86/5 are deliberately not selfslot claims here.
    static bool conflicts_with_world_identity(std::span<const std::uint8_t> wire) noexcept {
        try {
            if(wire.empty())return true;
            for(std::size_t offset=0;offset<wire.size();){
                const auto remaining=wire.subspan(offset);
                if(remaining.size()<2)return true;
                const auto size=std::size_t(remaining[0])+256u*remaining[1];
                if(size<4||size>remaining.size())return true;
                const auto logical=RecoveredWorldFrame::decode(remaining.first(size));
                if(!logical)return true;
                const auto records=RecoveredTaiwanServerRecords::read(*logical);
                if(!records)return true;
                for(const auto& record:*records)
                    if(record.opcode==0x2a||record.opcode==0xcf)return true;
                offset+=size;
            }
            return false;
        }catch(...){return true;} // Unknown framing/allocation fails closed for custody only.
    }
private:
    std::atomic<State> state_{State::Unbound};
};
}
