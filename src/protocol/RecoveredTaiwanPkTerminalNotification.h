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
    // Exact existing scalar result grammar followed by final88, canonical89.
    // Shape alone grants no room/current-source/recipient authority.
    static bool matches_result_sequence(std::span<const std::uint8_t> bytes){
        const auto records=RecoveredTaiwanServerRecords::read(bytes);
        if(!records||records->size()<4||!matches(records->back().bytes))return false;
        const auto end=records->size()-2;
        if(!RecoveredBattleVitalsBatch::parse_logical((*records)[end].bytes))return false;
        std::size_t at=0;unsigned groups=0,seen=0;
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
               (own_mp&&attack->source()!=0)||at>=end)return false;
            const auto side=static_cast<unsigned>(attack->source()/14);
            if(seen&(1u<<side))return false;seen|=1u<<side;
            const auto hp=RecoveredBattleVitals::parse_logical((*records)[at++].bytes);
            if(!hp||hp->resource()!=RecoveredBattleVitals::Resource::Hp||
               hp->position()!=14*(1-side)||++groups>2)return false;
        }
        return at==end&&groups>=1;
    }
private:
    static RecoveredBattleExperience::LogicalRecord encode()noexcept{
        RecoveredBattleExperience::LogicalRecord bytes{};bytes[0]=0x89;bytes[49]=4;return bytes;
    }
};
}
