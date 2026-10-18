#pragma once
#include "protocol/RecoveredBattleExperience.h"
#include "protocol/RecoveredBattleAttackPresentation.h"
#include "protocol/RecoveredBattleVitals.h"
#include "protocol/RecoveredBattleVitalsBatch.h"
#include "protocol/RecoveredTaiwanServerRecords.h"

namespace god2 {
class OwnedTaiwanPkTerminalSource;
// CUSTOM-0126 explicit TW no-message terminal notification. Current149c
// complete518BF0: unsigned selector>3 has no other direct record reads or
// explicit packet-pointer forwarding in that body, then joins its common
// cleanup/exit-latch tail. Opaque callees/global aliases remain open. Choose4;
// canonical zero ignored bytes are CUSTOM, not original server padding/awards.
// No saved EXP/HP policy, win/loss message or WORLD-return authority follows.
class RecoveredTaiwanPkTerminalNotification final {
    friend class OwnedTaiwanPkTerminalSource;
public:
    static bool matches(std::span<const std::uint8_t> bytes)noexcept{
        if(bytes.size()!=RecoveredBattleExperience::logical_size)return false;
        for(std::size_t i=0;i<bytes.size();++i)
            if(bytes[i]!=(i==0?0x89:i==49?4:0))return false;
        return true;
    }
    // New results follow each actual native consumer: direct-HP83 omits HP86,
    // pose-only83 requires it. The final88 waits behind the animation groups.
    // Shape alone grants no room/current-source/recipient authority.
    static bool matches_output_sequence(std::span<const std::uint8_t> bytes){
        return sequence(bytes,false,false);
    }
    // Read/publication compatibility only: preserve byte-exact saved outputs
    // whose old projection emitted HP86 for EVERY group. Do not accept a
    // hybrid of that old policy and the current per-consumer policy.
    static bool matches_retained_output_sequence(std::span<const std::uint8_t> bytes){
        return sequence(bytes,true,false);
    }
    static bool matches_result_sequence(std::span<const std::uint8_t> bytes){
        return sequence(bytes,false,true);
    }
    static bool matches_retained_result_sequence(std::span<const std::uint8_t> bytes){
        return sequence(bytes,true,true);
    }
private:
    static bool sequence(std::span<const std::uint8_t> bytes,bool retained,bool require_terminal){
        const auto records=RecoveredTaiwanServerRecords::read(bytes);
        if(!records||records->size()<2)return false;
        const bool terminal=records->back().opcode==0x89;
        if((require_terminal&&!terminal)||(terminal&&!matches(records->back().bytes))||
           records->size()<2+(terminal?1u:0u))return false;
        const auto end=records->size()-1-(terminal?1u:0u);
        if(!RecoveredBattleVitalsBatch::parse_logical((*records)[end].bytes))return false;
        std::size_t at=0;unsigned groups=0,seen=0;
        bool fresh=true,legacy=true;
        while(at<end){
            bool own_mp=false;
            if((*records)[at].opcode==0x86){
                const auto mp=RecoveredBattleVitals::parse_logical((*records)[at].bytes);
                if(!mp||mp->resource()!=RecoveredBattleVitals::Resource::Mp||mp->position()!=0)return false;
                own_mp=true;++at;
            }
            if(at>=end)return false;
            const auto& animation=(*records)[at++];
            const auto attack=RecoveredBattleAttackPresentation::parse(animation.bytes);
            if(!attack||(attack->source()!=0&&attack->source()!=14)||
               (animation.bytes[5]&~1u)||animation.bytes[6]||(animation.bytes[7]&~1u)||animation.bytes[8]||
               (own_mp&&attack->source()!=0))return false;
            const auto side=static_cast<unsigned>(attack->source()/14);
            if(seen&(1u<<side))return false;seen|=1u<<side;
            bool absolute_hp=false;
            if(at<end&&(*records)[at].opcode==0x86){
                const auto hp=RecoveredBattleVitals::parse_logical((*records)[at].bytes);
                // MP86 here may begin the next source0 group. Only an HP86
                // belongs to this group; malformed86 must not be skipped.
                if(!hp)return false;
                if(hp->resource()==RecoveredBattleVitals::Resource::Hp){
                    if(hp->position()!=14*(1-side))return false;
                    absolute_hp=true;++at;
                }
            }
            fresh=fresh&&(absolute_hp==attack->requires_absolute_hp_update());
            legacy=legacy&&absolute_hp;
            if(++groups>2)return false;
        }
        return at==end&&groups>=1&&(fresh||(retained&&legacy));
    }
    static RecoveredBattleExperience::LogicalRecord encode()noexcept{
        RecoveredBattleExperience::LogicalRecord bytes{};bytes[0]=0x89;bytes[49]=4;return bytes;
    }
};
}
