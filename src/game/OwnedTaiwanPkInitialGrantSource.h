#pragma once
#include "game/OwnedTaiwanPkPlayerEntrySource.h"
#include "protocol/RecoveredBattlePlayerGrant.h"
#include <optional>
#include <utility>

namespace god2 {
// CUSTOM-0110 initial owned primary grant serialization. The full149c
// 517590..5177B8 readset qualifies the fields, not original server values or
// action authority. This source retains the exact private269 player receipt.
class OwnedTaiwanPkInitialGrantSource final {
public:
    class Observation {
    public:
        Observation(const Observation&)=default;
        Observation& operator=(const Observation&)=default;
        Observation(Observation&&)=default;
        Observation& operator=(Observation&&)=default;
        const OwnedTaiwanPkPlayerEntrySource::Observation& player()const noexcept{return player_;}
        RecoveredBattlePlayerGrant::Record grant()const{
            RecoveredBattlePlayerGrant::Bytes bytes{};
            bytes[0]=0x86;bytes[1]=5;bytes[3]=1;bytes[4]=0;
            // CUSTOM-0110 WORD5=0 renders raw label001 via unsigned+1;
            // NOT a command window, clock, round number or original default.
            // Raw2/7..16 canonical0 only for this bounded qualified consumer;
            // not global padding. Mask01 grants own0, does not clear secondary.
            return *RecoveredBattlePlayerGrant::parse(bytes);
        }
        bool current()const{return player_.current();}
        bool uses_connection(const sqlite3* db)const noexcept{return player_.uses_connection(db);}
        bool stored_current_in_room_transaction(sqlite3* db)const{
            return player_.stored_current_in_room_transaction(db);
        }
        bool operator==(const Observation&)const=default;
    private:
        friend class OwnedTaiwanPkInitialGrantSource;
        explicit Observation(OwnedTaiwanPkPlayerEntrySource::Observation player):player_(std::move(player)){}
        OwnedTaiwanPkPlayerEntrySource::Observation player_;
    };
    static std::optional<Observation> observe(OwnedTaiwanPkPlayerEntrySource::Observation player){
        if(!player.current())return {};
        Observation source(std::move(player));
        (void)source.grant();
        if(!source.current())return {};
        return source;
    }
};
}
