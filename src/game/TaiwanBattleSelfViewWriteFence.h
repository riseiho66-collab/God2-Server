#pragma once
#include "protocol/RecoveredTaiwanServerRecords.h"
#include "protocol/RecoveredWorldFrame.h"
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <optional>
#include <span>

namespace god2 {
// Actual sender occurrence only: no native adoption, turn/skill permission or
// proof of the receiver's current B51. Unknown phase routing is not exempted.
class TaiwanBattleSelfViewWriteFence final {
public:
    struct Analysis {bool changes_view{};std::optional<std::uint8_t> primary_slot;};
    enum class State {Pending,Written,Revoked};
    class Occurrence final {
    public:
        bool complete(bool exact_whole_write) noexcept {
            if(exact_whole_write){
                auto expected=State::Pending;
                if(state_.compare_exchange_strong(expected,State::Written))return true;
            }
            revoke();return false;
        }
        void revoke() noexcept {state_.store(State::Revoked);}
        bool written() const noexcept {return state()==State::Written;}
        State state() const noexcept {return state_.load();}
    private:
        std::atomic<State> state_{State::Pending};
    };
    std::uint64_t advance() noexcept {
        auto prior=epoch_.load();
        constexpr auto exhausted=std::numeric_limits<std::uint64_t>::max();
        while(prior!=exhausted){
            const auto next=prior+1;
            if(epoch_.compare_exchange_weak(prior,next))return next==exhausted?0:next;
        }
        return 0; // Saturation disables qualification; bytes still follow legacy output.
    }
    bool current(std::uint64_t epoch) const noexcept {
        return epoch && epoch!=std::numeric_limits<std::uint64_t>::max() && epoch_.load()==epoch;
    }
    // Complete ordered frames/records only. A final known primary setter can
    // follow1C/82 in the same whole Write; a later ambiguous writer clears it.
    // World2A/CF, deferred S83/actions6/9 or an unsupported primary slot poison the WHOLE Write: a
    // later grant does not prove reachability across those receiver boundaries.
    // Other parsed records have no writer identified by this bounded classifier,
    // not a claim that every native consumer is harmless in every phase.
    static Analysis inspect(std::span<const std::uint8_t> wire) noexcept {
        try {
            if(wire.empty())return {true,{}};
            Analysis result;bool poisoned=false;
            for(std::size_t offset=0;offset<wire.size();){
                const auto remaining=wire.subspan(offset);
                if(remaining.size()<2)return {true,{}};
                const auto size=std::size_t(remaining[0])+256u*remaining[1];
                if(size<4||size>remaining.size())return {true,{}};
                const auto logical=RecoveredWorldFrame::decode(remaining.first(size));
                if(!logical)return {true,{}};
                if(!inspect_records(*logical,result,poisoned))return {true,{}};
                offset+=size;
            }
            return result;
        }catch(...){return {true,{}};}
    }
    // The corresponding output API already owns complete logical records.
    // Classify its intent before the game-to-strand post, without re-encoding.
    static Analysis inspect_logical(std::span<const std::uint8_t> logical) noexcept {
        try {
            Analysis result;bool poisoned=false;
            if(!inspect_records(logical,result,poisoned))return {true,{}};
            return result;
        }catch(...){return {true,{}};}
    }
private:
    static bool inspect_records(std::span<const std::uint8_t> logical,Analysis& result,bool& poisoned) {
        const auto records=RecoveredTaiwanServerRecords::read(logical);
        if(!records)return false;
        for(const auto& record:*records){
            if(record.opcode==0x2a||record.opcode==0xcf){
                result.changes_view=true;result.primary_slot.reset();poisoned=true;
            }else if(record.opcode==0x83&&record.bytes[1]==6){
                // Current TW aaf0:52C520 action6 -> 52A8D0 state7.
                // Logical BYTE12==2 explicitly selects flee substate4;
                // 529020 -> 526ED0 waits for animation, then 520000
                // removes all six layers and clears the presence bit.
                // Other result flags need not remove an actor. Conservatively
                // retire all retained primary/secondary sender assumptions,
                // never reinterpret flee as a row swap or issue a new grant.
                result.changes_view=true;result.primary_slot.reset();poisoned=true;
            }else if(record.opcode==0x83&&record.bytes[1]==9){
                // Current TW aaf0:52C520 -> state97 -> 525B90 exchanges all
                // six layers and later rewrites primary/secondary slots.
                // Failure may leave them unchanged; conservatively revoke
                // sender custody anyway, without inventing a new slot/grant.
                // A later setter in this same Write does not prove ordering
                // after the deferred native animation/swap completes.
                result.changes_view=true;result.primary_slot.reset();poisoned=true;
            }else if(record.opcode==0x1c||record.opcode==0x82){
                result.changes_view=true;result.primary_slot.reset();
            }else if(record.opcode==0x86&&record.bytes[1]==5&&(record.bytes[3]&1)){
                result.changes_view=true;result.primary_slot.reset();
                const auto slot=static_cast<std::uint8_t>(record.bytes[4]&15);
                if(slot>=14)poisoned=true;
                else if(!poisoned)result.primary_slot=slot;
            }
        }
        return true;
    }
    std::atomic<std::uint64_t> epoch_{0};
};
}
