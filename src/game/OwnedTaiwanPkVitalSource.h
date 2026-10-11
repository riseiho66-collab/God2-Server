#pragma once
#include "game/OwnedTaiwanPkCombatSource.h"
#include "protocol/RecoveredBattleVitals.h"
#include <optional>
#include <stdexcept>
#include <utility>

namespace god2 {
// CUSTOM-0109 complete owned ordinary HP/MP records. Current149c handlers
// 517230/5173A0 do not read logical3..4/13..16 on the qualified paths and
// do not forward the packet pointer. Zeroing those six bytes is an explicit
// server serialization policy, NOT original padding or a native producer.
// Values and lifetime retain the exact private268 combat/source incarnation.
class OwnedTaiwanPkVitalSource final {
public:
    class Observation {
    public:
        Observation(const Observation&)=default;
        Observation& operator=(const Observation&)=default;
        Observation(Observation&&)=default;
        Observation& operator=(Observation&&)=default;
        const OwnedTaiwanPkCombatSource::Observation& combat()const noexcept{return combat_;}
        RecoveredBattleVitals::Record hp()const{return record(RecoveredBattleVitals::Resource::Hp);}
        RecoveredBattleVitals::Record mp()const{return record(RecoveredBattleVitals::Resource::Mp);}
        bool current()const{return combat_.current();}
        bool uses_connection(const sqlite3* db)const noexcept{return combat_.uses_connection(db);}
        bool stored_current_in_room_transaction(sqlite3* db)const{
            return combat_.stored_current_in_room_transaction(db);
        }
        bool operator==(const Observation&)const=default;
    private:
        friend class OwnedTaiwanPkVitalSource;
        explicit Observation(OwnedTaiwanPkCombatSource::Observation combat):combat_(std::move(combat)){}
        RecoveredBattleVitals::Record record(RecoveredBattleVitals::Resource kind)const{
            const auto& saved=combat_.material().resources;
            const auto values=saved.legacy_vitals();
            if(!values||!saved.hp||saved.hp>saved.max_hp||saved.mp>saved.max_mp)
                throw std::invalid_argument("PK owned vitals require exact coherent legacy DWORD resources");
            const bool hp=kind==RecoveredBattleVitals::Resource::Hp;
            const auto current=(*values)[hp?0:2],maximum=(*values)[hp?1:3];
            RecoveredBattleVitals::Bytes bytes{};
            bytes[0]=0x86;bytes[1]=static_cast<std::uint8_t>(kind);bytes[2]=0;
            // CUSTOM-0109 logical3..4/13..16 canonical zero ONLY for the
            // bounded qualified ordinary consumer. No S88/counter policy.
            for(unsigned i=0;i<4;++i){
                bytes[5+i]=static_cast<std::uint8_t>(maximum>>(8*i));
                bytes[9+i]=static_cast<std::uint8_t>(current>>(8*i));
            }
            return *RecoveredBattleVitals::parse_logical(bytes);
        }
        OwnedTaiwanPkCombatSource::Observation combat_;
    };
    static std::optional<Observation> observe(OwnedTaiwanPkCombatSource::Observation combat){
        if(!combat.current())return {};
        Observation source(std::move(combat));
        (void)source.hp();(void)source.mp(); // Checked conversion before publication.
        if(!source.current())return {};
        return source;
    }
};
}
