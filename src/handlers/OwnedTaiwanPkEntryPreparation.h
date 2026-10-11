#pragma once
#include "db/SqliteOwnedPkRoomRepository.h"
#include "db/SqliteRoleTextRepository.h"
#include "game/OwnedTaiwanPkVitalSource.h"
#include <array>
#include <functional>
#include <memory>
#include <optional>
#include <stdexcept>
#include <thread>
#include <type_traits>
#include <utility>

namespace god2 {
// CUSTOM-0112 concrete Prepare callback, not an installed RoomAuthority. The
// actual owner supplies Session/private initialization/PK peer resolution and
// a server-owned random seed, never views, stats, raw templates or fake tokens.
// Borrowed repositories/SQLite connection and resolver owners must outlive this
// object and every returned ticket; drain on the actual shared game executor.
class OwnedTaiwanPkEntryPreparation final {
public:
    using Pair=OwnedPkInvitationService::Pair;
    using Peer=OwnedPkInvitationService::Peer;
    using Ticket=SqliteOwnedPkRoomRepository::Ticket;
    using Sessions=std::function<std::shared_ptr<Session>(std::uint64_t)>;
    using Initializations=std::function<std::optional<Session::NormalWorldInitialization>(
        const std::shared_ptr<Session>&)>;
    using Resolve=OwnedPkInvitationService::Resolve;
    // Explicit trusted server supplier. Zero is a supplied uint32 value, not
    // a missing/default seed. No native RNG/clock/context formula is claimed.
    using Seed=std::function<std::optional<std::uint32_t>(const Pair&)>;
    // CUSTOM-0129 actual published restoration observation, never a caller
    // supplied roster, selected-key scalar or empty-on-failure fallback.
    using Companions=std::function<std::optional<OwnedTaiwanPkCompanionSource::Observation>(
        const std::shared_ptr<Session>&,const Session::NormalWorldInitialization&)>;
    OwnedTaiwanPkEntryPreparation(sqlite3* db,SqliteAccountRepository& accounts,
        SqliteRecoveredCharacterRepository& characters,SqliteNativeWorldEntrySnapshotRepository& worlds,
        SqliteRoleAuxiliaryRepository& auxiliary,SqliteRoleTextRepository& texts,
        TaiwanNativeFightCatalog catalog,std::shared_ptr<SharedWorldPresence> presence,
        std::shared_ptr<SqliteOwnedEquipmentTransaction> joint,SqliteOwnedPkRoomRepository& rooms,
        Sessions sessions,Initializations initializations,Resolve peers,Seed seed,Companions companions={})
        :db_(db),accounts_(accounts),characters_(characters),worlds_(worlds),auxiliary_(auxiliary),texts_(texts),
         catalog_(std::move(catalog)),presence_(std::move(presence)),joint_(std::move(joint)),rooms_(rooms),
         sessions_(std::move(sessions)),initializations_(std::move(initializations)),peers_(std::move(peers)),
         seed_(std::move(seed)),companions_(std::move(companions)){
        if(!db_||!accounts_.uses_connection(db_)||!characters_.uses_connection(db_)||
           !worlds_.owns_sources(accounts_,characters_)||!auxiliary_.uses_connection(db_)||
           !texts_.uses_connection(db_)||!rooms_.uses_connection(db_)||!presence_||!joint_||
           !presence_->owns_repository(characters_)||!joint_->owns_sources(accounts_,characters_)||
           !sessions_||!initializations_||!peers_||!seed_)
            throw std::invalid_argument("TW PK preparation requires exact concrete sources and owners");
    }
    OwnedTaiwanPkEntryPreparation(const OwnedTaiwanPkEntryPreparation&)=delete;
    OwnedTaiwanPkEntryPreparation& operator=(const OwnedTaiwanPkEntryPreparation&)=delete;
    std::optional<Ticket> operator()(const Pair& pair){return prepare(pair);}
    std::optional<Ticket> prepare(const Pair& supplied_pair){
        owner();
        if(preparing_){reentered_=true;return {};}
        preparing_=true;reentered_=false;
        struct End {bool& busy;~End(){busy=false;}}end{preparing_};
        // Resolver owners cannot change this attempt through another alias to
        // the caller's Pair while callbacks run.
        const Pair pair=supplied_pair;
        if(!eligible(pair)||!open())return {};
        const std::array<Peer,2> peers{pair.challenger,pair.recipient};
        std::array<std::shared_ptr<Session>,2> sessions;
        std::array<std::optional<Session::NormalWorldInitialization>,2> initializations;
        std::array<SessionState,2> prebattle_phases;
        std::array<std::optional<SharedWorldPresence::Lease>,2> leases;
        std::array<std::optional<OwnedTaiwanPkCompanionSource::Observation>,2> companions;
        for(std::size_t i=0;i<2;++i){
            sessions[i]=callback([&]{return sessions_(peers[i].session);});
            if(!open()||!sessions[i])return {};
            initializations[i]=callback([&]{return initializations_(sessions[i]);});
            // Check real private receipt BEFORE mutable Session identity fields.
            if(!open()||!initializations[i]||
               !sessions[i]->normal_world_initialization_current_on_game(*initializations[i])||
               !initializations[i]->entry_written())return {};
            // CUSTOM-0116 capture once after private game-owner qualification.
            // Rechecks require this exact phase, not either allowed phase anew.
            prebattle_phases[i]=sessions[i]->state();
            if(!session_current(sessions[i],*initializations[i],peers[i],prebattle_phases[i]))return {};
            leases[i]=presence_->ready_lease(peers[i].session,peers[i].account,peers[i].character);
            if(!leases[i]||!lease_current(*leases[i],peers[i]))return {};
        }
        const auto local=[&]{
            if(!open()||!sessions[0]->same_native_pk_game_executor(*sessions[1]))return false;
            for(std::size_t i=0;i<2;++i)
                if(!session_current(sessions[i],*initializations[i],peers[i],prebattle_phases[i])||
                   !lease_current(*leases[i],peers[i]))return false;
            return open();
        };
        const auto exact=[&]{
            if(!local())return false;
            for(std::size_t i=0;i<2;++i){
                const auto session=callback([&]{return sessions_(peers[i].session);});
                if(!local()||session!=sessions[i])return false;
                const auto peer=callback([&]{return peers_(peers[i].session);});
                if(!local()||peer!=std::optional{peers[i]})return false;
            }
            return local();
        };
        if(!exact())return {};
        if(companions_)for(std::size_t i=0;i<2;++i){
            companions[i]=callback([&]{return companions_(sessions[i],*initializations[i]);});
            if(!exact()||!companions[i]||!companions[i]->uses_connection(db_)||!companions[i]->current()||!local())return {};
        }
        const auto companions_current=[&]{
            if(!local())return false;
            if(companions_)for(const auto& source:companions)
                if(!source||!source->current()||!local())return false;
            return local();
        };
        std::array<std::optional<OwnedTaiwanPkCombatSource::Observation>,2> combat;
        std::array<std::optional<OwnedTaiwanPkPlayerEntrySource::Observation>,2> players;
        std::array<std::optional<OwnedTaiwanPkVitalSource::Observation>,2> vitals;
        for(std::size_t i=0;i<2;++i){
            if(!local())return {};
            auto committed=joint_->observe_committed(peers[i].account,peers[i].character);
            if(!committed||!local())return {};
            auto appearance=OwnedTaiwanPkAppearanceSource::observe(joint_,accounts_,characters_,worlds_,presence_,
                sessions[i],*initializations[i],*leases[i],std::move(*committed));
            if(!appearance||!local())return {};
            combat[i]=OwnedTaiwanPkCombatSource::observe(db_,characters_,auxiliary_,std::move(*appearance));
            if(!combat[i]||!local())return {};
            players[i]=OwnedTaiwanPkPlayerEntrySource::observe(db_,texts_,*combat[i]);
            if(!players[i]||!local())return {};
            vitals[i]=OwnedTaiwanPkVitalSource::observe(*combat[i]);
            if(!vitals[i]||!local())return {};
        }
        auto entry=RecoveredPkEntryProjection::prepare_waiting_notification_owned_initial_contexts(
            {*players[0],*players[1]},{*vitals[0],*vitals[1]},catalog_);
        const auto sources_current=[&]{
            if(!companions_current())return false;
            for(const auto& player:*entry.owned_players())if(!player.current()||!local())return false;
            // Full private player Current includes combat/appearance/resources,
            // text/root and the exact joint receipt, not a digest-only check.
            return companions_current();
        };
        if(!exact()||!sources_current())return {};
        const auto seed=callback([&]{return seed_(pair);});
        if(!seed||!exact()||!sources_current())return {};
        // Bounds come from the actual complete two-player Prepared; no caller
        // masks or inferred expected native0B target selection are accepted.
        if(!entry.initial_notification_bounds())return {};
        const auto bounds=*entry.initial_notification_bounds();
        std::optional<Ticket> ticket;
        struct Reservation {
            SqliteOwnedPkRoomRepository& rooms;std::optional<Ticket>& ticket;bool returned=false;
            ~Reservation(){if(ticket&&!returned)rooms.abandon(*ticket);}
        }reservation{rooms_,ticket};
        std::optional<SqliteOwnedPkRoomRepository::OwnedCompanionSources> retained_companions;
        if(companions_)retained_companions.emplace(
            SqliteOwnedPkRoomRepository::OwnedCompanionSources{*companions[0],*companions[1]});
        ticket.emplace(rooms_.prepare_owned(pair,std::move(entry),{*combat[0],*combat[1]},*seed,bounds,
                                           std::move(retained_companions)));
        // The reservation changed only durable room state. No holds, Session
        // state transition, delivery, visibility grant or active room here.
        if(!exact()||!companions_current())return {};
        for(const auto& player:*ticket->input().entry.owned_players())if(!player.current()||!local())return {};
        if(!rooms_.current(*ticket)||!exact()||!companions_current())return {};
        for(const auto& player:*ticket->input().entry.owned_players())if(!player.current()||!local())return {};
        if(!companions_current())return {};
        reservation.returned=true;
        return ticket;
    }
private:
    void owner()const{
        if(thread_!=std::this_thread::get_id())throw std::logic_error("TW PK preparation game owner mismatch");
    }
    bool open()const{owner();return !reentered_&&sqlite3_get_autocommit(db_)!=0;}
    template<class F> auto callback(F&& invoke)->std::invoke_result_t<F>{
        if(!open())throw std::logic_error("TW PK preparation callback source expired");
        const auto changes=sqlite3_total_changes64(db_);
        auto result=std::forward<F>(invoke)();
        if(!open()||sqlite3_total_changes64(db_)!=changes)
            throw std::logic_error("TW PK preparation resolver reentered or changed storage");
        return result;
    }
    static bool eligible(const Pair& pair){
        const auto&a=pair.challenger;const auto&b=pair.recipient;
        return a.session&&b.session&&a.session!=b.session&&a.account&&b.account&&a.character&&b.character&&
            a.character!=b.character&&a.world_generation&&b.world_generation&&a.ready&&b.ready&&
            !a.blocked&&!b.blocked&&a.position.area==b.position.area&&a.position.scene==b.position.scene;
    }
    bool session_current(const std::shared_ptr<Session>& session,
            const Session::NormalWorldInitialization& initialization,const Peer& peer,
            SessionState prebattle_phase)const{
        if(!open()||!session||!session->normal_world_initialization_current_on_game(initialization)||
           !initialization.entry_written())return false;
        return (prebattle_phase==SessionState::CharacterSelected||prebattle_phase==SessionState::InWorld)&&
            !session->closing()&&session->state()==prebattle_phase&&session->id()==peer.session&&
            session->account_id==peer.account&&session->character_id==peer.character&&
            session->battle_generation()==peer.battle_generation;
    }
    bool lease_current(const SharedWorldPresence::Lease& lease,const Peer& peer)const{
        if(!open()||lease.session!=peer.session||lease.account!=peer.account||lease.character!=peer.character||
           presence_->ready_lease(peer.session,peer.account,peer.character)!=std::optional{lease})return false;
        // Initial lease pose and current saved pose differ after movement.
        // PK world_generation is independently reobserved through Resolve.
        return presence_->saved_position(lease)==std::optional{peer.position}&&open();
    }
    sqlite3* db_;
    SqliteAccountRepository& accounts_;
    SqliteRecoveredCharacterRepository& characters_;
    SqliteNativeWorldEntrySnapshotRepository& worlds_;
    SqliteRoleAuxiliaryRepository& auxiliary_;
    SqliteRoleTextRepository& texts_;
    TaiwanNativeFightCatalog catalog_;
    std::shared_ptr<SharedWorldPresence> presence_;
    std::shared_ptr<SqliteOwnedEquipmentTransaction> joint_;
    SqliteOwnedPkRoomRepository& rooms_;
    Sessions sessions_;Initializations initializations_;Resolve peers_;Seed seed_;
    Companions companions_;
    const std::thread::id thread_=std::this_thread::get_id();
    bool preparing_=false,reentered_=false;
};
}
