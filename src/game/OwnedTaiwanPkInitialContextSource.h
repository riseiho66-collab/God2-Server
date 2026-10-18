#pragma once
#include "game/OwnedTaiwanPkPlayerEntrySource.h"
#include "game/OwnedTaiwanPkVitalSource.h"
#include "protocol/RecoveredBattleEntry.h"
#include "protocol/RecoveredBattleVitalsBatch.h"
#include <limits>
#include <optional>
#include <stdexcept>
#include <utility>

namespace god2 {
// CUSTOM-0111 complete initial82/88 producer from exact private owned sources.
// ContextA is a checked future Session battle generation, NOT a global nonce
// or recovered native timestamp. Native82 contexts feed B+3C/B+40; B+48
// separately captures current World R0, qualified named2A low14 at its write.
// This producer does not supply that native identity or a native selfslot receipt.
// Counter/window/display/empty slots are explicit initial-only server policy,
// never original defaults or packet padding. See round469 identity v2 in
// tw-battle-identity-and-signed-loss-boundary-20261019.md.
class OwnedTaiwanPkInitialContextSource final {
public:
    class Observation {
    public:
        Observation(const Observation&)=default;
        Observation& operator=(const Observation&)=default;
        Observation(Observation&&)=default;
        Observation& operator=(Observation&&)=default;
        const OwnedTaiwanPkPlayerEntrySource::Observation& player()const noexcept{return player_;}
        const OwnedTaiwanPkVitalSource::Observation& vital()const noexcept{return vital_;}
        const RecoveredBattleEntry::Bytes& context_bytes()const noexcept{return context_;}
        const RecoveredBattleVitalsBatch::Bytes& bulk_bytes()const noexcept{return bulk_;}
        RecoveredBattleEntry::Record context()const{return *RecoveredBattleEntry::parse_logical(context_);}
        RecoveredBattleVitalsBatch::Record bulk()const{return *RecoveredBattleVitalsBatch::parse_logical(bulk_);}
        // Existing private player/vital Current fences only. Their prebattle
        // epoch validity does not silently transfer across InBattle transition;
        // it does not attest current native R0, selfslot or client adoption.
        bool current()const{return player_.current()&&vital_.current()&&player_.current();}
        bool uses_connection(const sqlite3* db)const noexcept{
            return player_.uses_connection(db)&&vital_.uses_connection(db);
        }
        bool stored_current_in_room_transaction(sqlite3* db)const{
            return player_.stored_current_in_room_transaction(db)&&vital_.stored_current_in_room_transaction(db);
        }
        bool operator==(const Observation&)const=default;
    private:
        friend class OwnedTaiwanPkInitialContextSource;
        Observation(OwnedTaiwanPkPlayerEntrySource::Observation player,
                    OwnedTaiwanPkVitalSource::Observation vital)
            :player_(std::move(player)),vital_(std::move(vital)){
            const auto generation=player_.combat().appearance().material().battle_generation;
            if(generation>=std::numeric_limits<std::uint32_t>::max())
                throw std::invalid_argument("PK initial context exceeds checked Session generation DWORD");
            context_=RecoveredBattleEntry::encode_logical({static_cast<std::uint32_t>(generation+1),0x00001400});
            bulk_[0]=0x88;
            // CUSTOM-0111 initial counter0 is not sentinelFFFFFFFF or replay
            // authority. Own friendly0 consumes exact checked private271 HP/MP.
            const auto hp=vital_.hp().current(),mp=vital_.mp().current();
            for(unsigned i=0;i<4;++i){
                bulk_[5+i]=static_cast<std::uint8_t>(hp>>(8*i));
                bulk_[9+i]=static_cast<std::uint8_t>(mp>>(8*i));
            }
            // Friendly1..13 are reset arena placeholders, not invented actors.
            // Their zero values require successful normal initialization. Raw
            //118=0 disables qualified displaybits08/04/02/01;117/119/120 are
            // explicit serialization choices, not global unused-field claims.
        }
        OwnedTaiwanPkPlayerEntrySource::Observation player_;
        OwnedTaiwanPkVitalSource::Observation vital_;
        RecoveredBattleEntry::Bytes context_{};
        RecoveredBattleVitalsBatch::Bytes bulk_{};
    };
    static std::optional<Observation> observe(OwnedTaiwanPkPlayerEntrySource::Observation player,
                                              OwnedTaiwanPkVitalSource::Observation vital){
        if(player.combat()!=vital.combat()||!player.current()||!vital.current())return {};
        Observation source(std::move(player),std::move(vital));
        if(!source.current())return {};
        return source;
    }
};
}
