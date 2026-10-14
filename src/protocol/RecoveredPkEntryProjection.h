#pragma once
#include "protocol/RecoveredBattlePlayerAppearance.h"
#include "game/TaiwanNativeFightCatalog.h"
#include "game/OwnedTaiwanPkAppearanceSource.h"
#include "game/OwnedTaiwanPkPlayerEntrySource.h"
#include "game/OwnedTaiwanPkVitalSource.h"
#include "game/OwnedTaiwanPkInitialGrantSource.h"
#include "game/OwnedTaiwanPkInitialContextSource.h"
#include "protocol/RecoveredBattleBootstrap.h"
#include "protocol/RecoveredBattlePlayerGrant.h"
#include <algorithm>
#include <optional>
#include <stdexcept>
#include <utility>
namespace god2 {
// CUSTOM-0086 explicit TWO-viewer PK entry projection. Format/presentation
// source only; no room creation, actor authority, grants, formulas or writes.
// All raw input records must come from owned, build-qualified snapshots.
// Never fill them from diagnostic constants or guessed world->battle mapping.
struct RecoveredPkEntryProjection {
    using ControlMasks=std::array<std::array<std::uint16_t,2>,2>;
    // Viewer0 own/other, then viewer1 own/other; side-qualified AFTER rebind.
    using FightSources=std::array<TaiwanNativeFightCatalog::Selection,4>;
    using OwnedAppearances=std::array<OwnedTaiwanPkAppearanceSource::Observation,2>;
    using OwnedPlayers=std::array<OwnedTaiwanPkPlayerEntrySource::Observation,2>;
    using OwnedVitals=std::array<OwnedTaiwanPkVitalSource::Observation,2>;
    using OwnedInitialGrants=std::array<OwnedTaiwanPkInitialGrantSource::Observation,2>;
    using OwnedInitialContexts=std::array<OwnedTaiwanPkInitialContextSource::Observation,2>;
    // Owner0 HP/MP then owner1 HP/MP, all complete position0 source records.
    using VitalTemplates=std::array<std::array<RecoveredBattleVitals::Bytes,2>,2>;
    // Viewer0 own/other, then viewer1 own/other; strings are encoded for the
    // actual recipient, not merely position-rebound from a shared byte field.
    using PlayerIdentities=std::array<RecoveredBattleIdentity::Bytes,4>;
    struct Player {
        std::uint64_t character;
        RecoveredBattleIdentity::Record identity;
        RecoveredBattlePlayerAppearance::Record appearance;
        RecoveredBattleVitals::Record hp,mp;
    };
    struct View {
        RecoveredBattleEntry::Record context;
        RecoveredBattleVitalsBatch::Record friendly_bulk;
        std::array<std::uint8_t,17> initial_control;
    };
    struct InitialGrantView {
        RecoveredBattleEntry::Record context;
        RecoveredBattleVitalsBatch::Record friendly_bulk;
    };
    struct PlayerVitals {
        // Complete qualified templates; opaque WORD/tail remain supplied.
        // Current/max must equal the actual private268 source, never guessed.
        RecoveredBattleVitals::Record hp,mp;
    };
    class Prepared {
    public:
        const std::array<std::vector<std::uint8_t>,2>& records()const noexcept{return records_;}
        const std::array<std::uint64_t,2>& characters()const noexcept{return characters_;}
        // Present only on the actual owned-player independent scene path.
        const std::optional<std::array<std::uint16_t,2>>& native_actor_handles()const noexcept{return native_actor_handles_;}
        // Exact validated raw-vital values retained for shared-room admission;
        // an actor cannot enter with resources different from its wire view.
        const std::array<std::array<std::uint32_t,4>,2>& resources()const noexcept{return resources_;}
        const std::array<std::uint16_t,2>& levels()const noexcept{return levels_;}
        const std::array<RecoveredBattlePlayerGrant::Bytes,2>& grants()const noexcept{return grants_;}
        const std::array<std::uint32_t,2>& command_contexts()const noexcept{return command_contexts_;}
        bool waiting_control()const noexcept{return waiting_control_;}
        // CUSTOM-0104 allowed roster bounds, NEVER an expected native mask.
        const std::optional<ControlMasks>& initial_notification_bounds()const noexcept{return notification_bounds_;}
        const std::optional<FightSources>& fight_sources()const noexcept{return fight_sources_;}
        const std::optional<OwnedAppearances>& owned_appearances()const noexcept{return owned_appearances_;}
        const std::optional<OwnedPlayers>& owned_players()const noexcept{return owned_players_;}
        const std::optional<PlayerIdentities>& player_identities()const noexcept{return player_identities_;}
        const std::optional<OwnedVitals>& owned_vitals()const noexcept{return owned_vitals_;}
        const std::optional<VitalTemplates>& vital_templates()const noexcept{return vital_templates_;}
        const std::optional<OwnedInitialGrants>& owned_initial_grants()const noexcept{return owned_initial_grants_;}
        const std::optional<OwnedInitialContexts>& owned_initial_contexts()const noexcept{return owned_initial_contexts_;}
        bool operator==(const Prepared&)const=default;
    private:
        friend struct RecoveredPkEntryProjection;
        Prepared(std::array<std::vector<std::uint8_t>,2> records,std::array<std::uint64_t,2> characters,
                 std::array<std::array<std::uint32_t,4>,2> resources,std::array<std::uint16_t,2> levels,
                 std::array<RecoveredBattlePlayerGrant::Bytes,2> grants,
                 std::array<std::uint32_t,2> contexts,bool waiting,
                 std::optional<ControlMasks> notification_bounds)
            :records_(std::move(records)),characters_(characters),resources_(resources),levels_(levels),
             grants_(grants),command_contexts_(contexts),waiting_control_(waiting),
             notification_bounds_(notification_bounds){}
        std::array<std::vector<std::uint8_t>,2> records_;
        std::array<std::uint64_t,2> characters_;
        std::optional<std::array<std::uint16_t,2>> native_actor_handles_;
        std::array<std::array<std::uint32_t,4>,2> resources_;
        std::array<std::uint16_t,2> levels_;
        std::array<RecoveredBattlePlayerGrant::Bytes,2> grants_;
        std::array<std::uint32_t,2> command_contexts_;
        bool waiting_control_;
        std::optional<ControlMasks> notification_bounds_;
        std::optional<FightSources> fight_sources_;
        std::optional<OwnedAppearances> owned_appearances_;
        std::optional<OwnedPlayers> owned_players_;
        std::optional<PlayerIdentities> player_identities_;
        std::optional<OwnedVitals> owned_vitals_;
        std::optional<VitalTemplates> vital_templates_;
        std::optional<OwnedInitialGrants> owned_initial_grants_;
        std::optional<OwnedInitialContexts> owned_initial_contexts_;
    };
    static Prepared prepare(const std::array<Player,2>& players,const std::array<View,2>& views){
        return prepare_impl(players,views,false,false);
    }
    // Persistent collection rooms withhold the17-byte grant until BOTH
    // initial0B notifications. Initial0B may clear A/B in119200; an opening
    // grant must not be consumed before any collected command is possible.
    // This scheduling is CUSTOM-0086, not an official-server ACK claim.
    static Prepared prepare_waiting(const std::array<Player,2>& players,const std::array<View,2>& views){
        return prepare_impl(players,views,true,false);
    }
    // CUSTOM-0104 opt-in non-authorizing initial notification. Conditional
    // native pre-0B input can change targets; do not guess an initial count.
    static Prepared prepare_waiting_notification(const std::array<Player,2>& players,const std::array<View,2>& views){
        return prepare_impl(players,views,true,true);
    }
    // Explicit resource-row-qualified variant. Still requires actual complete
    // owned player records; no world8 producer, renderer or owner grant follows.
    // Old factories/bytes/readsets remain unchanged when this is not requested.
    static Prepared prepare_waiting_notification_catalogued(const std::array<Player,2>& players,
            const std::array<View,2>& views,const TaiwanNativeFightCatalog& catalog){
        auto prepared=prepare_impl(players,views,true,true);
        const auto select=[&](std::size_t player,std::uint8_t position){
            const auto record=RecoveredBattlePlayerAppearance::at_position(players[player].appearance,position);
            auto source=catalog.select(record);
            if(!source)throw std::invalid_argument("PK ordinary appearance lacks exact Fight resource rows");
            return std::move(*source);
        };
        prepared.fight_sources_=FightSources{select(0,0),select(1,14),select(1,0),select(0,14)};
        return prepared;
    }
    // CUSTOM-0105: concrete owned Current + complete private provenance,
    // consumed by the room's reserved admission preflight/readset. Existing
    // complete identity/vitals/profile/grants remain separately required.
    static Prepared prepare_waiting_notification_owned(std::array<Player,2> players,
            const std::array<View,2>& views,const TaiwanNativeFightCatalog& catalog,OwnedAppearances owned){
        for(std::size_t i=0;i<2;++i){
            const auto& m=owned[i].material();
            if(!owned[i].current()||players[i].character!=m.lease.character||
               players[i].identity.identity_word()!=m.lease.actor_handle)
                throw std::invalid_argument("PK appearance requires exact current owned identity");
            // Consume the minted producer's record, not an unused caller bool.
            players[i].appearance=m.appearance;
        }
        auto prepared=prepare_waiting_notification_catalogued(players,views,catalog);
        for(const auto& source:owned)if(!source.current())
            throw std::invalid_argument("PK owned appearance source changed during projection");
        prepared.owned_appearances_=std::move(owned);
        return prepared;
    }
    // CUSTOM-0107 actual owned complete S1C producer. Missing saved secondary
    // text is not an empty title; both strings are projected independently for
    // each recipient's private accepted language. Raw82/88/grants and complete
    // vital opaque bytes still require separately qualified supplied material.
    static Prepared prepare_waiting_notification_owned_players(OwnedPlayers sources,
            const std::array<PlayerVitals,2>& vitals,const std::array<View,2>& views,
            const TaiwanNativeFightCatalog& catalog){
        for(std::size_t i=0;i<2;++i){
            const auto& r=sources[i].combat().material().resources;
            if(!sources[i].current()||vitals[i].hp.resource()!=RecoveredBattleVitals::Resource::Hp||
               vitals[i].mp.resource()!=RecoveredBattleVitals::Resource::Mp||
               vitals[i].hp.current()!=r.hp||vitals[i].hp.maximum()!=r.max_hp||
               vitals[i].mp.current()!=r.mp||vitals[i].mp.maximum()!=r.max_mp)
                throw std::invalid_argument("PK player vitals require exact privately retained saved resources");
        }
        const auto page0=sources[0].recipient_codepage(),page1=sources[1].recipient_codepage();
        const auto player=[&](std::size_t i,std::uint16_t page){
            const auto& appearance=sources[i].combat().appearance().material();
            return Player{appearance.lease.character,sources[i].identity(0,page),appearance.appearance,
                vitals[i].hp,vitals[i].mp};
        };
        std::array players{player(0,page0),player(1,page0)};
        OwnedAppearances appearances{sources[0].combat().appearance(),sources[1].combat().appearance()};
        const bool independent=std::any_of(sources.begin(),sources.end(),[](const auto& source){
            return source.identity_profile()==TaiwanWorldEntryIdentity::QualifiedSceneHandle;
        });
        auto prepared=[&](){
            if(!independent)return prepare_waiting_notification_owned(players,views,catalog,std::move(appearances));
            // No public raw/scalar factory receives this private source route.
            auto result=prepare_impl(players,views,true,true,&sources);
            const auto select=[&](std::size_t i,std::uint8_t position){
                const auto record=RecoveredBattlePlayerAppearance::at_position(players[i].appearance,position);
                auto source=catalog.select(record);
                if(!source)throw std::invalid_argument("PK ordinary appearance lacks exact Fight resource rows");
                return std::move(*source);
            };
            result.fight_sources_=FightSources{select(0,0),select(1,14),select(1,0),select(0,14)};
            for(const auto& source:appearances)if(!source.current())
                throw std::invalid_argument("PK owned appearance source changed during projection");
            result.owned_appearances_=std::move(appearances);
            result.native_actor_handles_=std::array<std::uint16_t,2>{
                players[0].identity.identity_word(),players[1].identity.identity_word()};
            return result;
        }();
        // The second recipient may use a different page. Rebuild the complete
        // relative view before publication; never relabel the first view bytes.
        players={player(0,page1),player(1,page1)};
        auto second=one(players[1],players[0],views[1]);
        second.resize(second.size()-17); // Same explicit waiting grant schedule.
        prepared.records_[1]=std::move(second);
        prepared.player_identities_=PlayerIdentities{
            RecoveredBattleIdentity::encode_logical(sources[0].identity(0,page0)),
            RecoveredBattleIdentity::encode_logical(sources[1].identity(14,page0)),
            RecoveredBattleIdentity::encode_logical(sources[1].identity(0,page1)),
            RecoveredBattleIdentity::encode_logical(sources[0].identity(14,page1))};
        for(const auto& source:sources)if(!source.current())
            throw std::invalid_argument("PK owned player source changed during projection");
        prepared.owned_players_=std::move(sources);
        return prepared;
    }
    // CUSTOM-0109 consumes exact private268 saved HP/MP, not caller templates.
    // Existing supplied S88/context/grant bytes retain their separate authority.
    // Only own MP is emitted; the native side1 MP handler ignores that update.
    static Prepared prepare_waiting_notification_owned_vitals(OwnedPlayers players,OwnedVitals sources,
            const std::array<View,2>& views,const TaiwanNativeFightCatalog& catalog){
        for(std::size_t i=0;i<2;++i)
            if(sources[i].combat()!=players[i].combat()||!players[i].current()||!sources[i].current())
                throw std::invalid_argument("PK vitals require the exact current private player combat source");
        const std::array<PlayerVitals,2> vitals{{{sources[0].hp(),sources[0].mp()},
                                               {sources[1].hp(),sources[1].mp()}}};
        VitalTemplates raw{{{RecoveredBattleVitals::encode_logical(vitals[0].hp),
                                RecoveredBattleVitals::encode_logical(vitals[0].mp)},
                               {RecoveredBattleVitals::encode_logical(vitals[1].hp),
                                RecoveredBattleVitals::encode_logical(vitals[1].mp)}}};
        auto prepared=prepare_waiting_notification_owned_players(std::move(players),vitals,views,catalog);
        for(const auto& source:sources)if(!source.current())
            throw std::invalid_argument("PK owned vital source changed during projection");
        // Vital Current includes the actual shared live source fences. Recheck
        // the complete retained player/text receipts after those observations.
        for(const auto& source:*prepared.owned_players_)if(!source.current())
            throw std::invalid_argument("PK owned player source changed during vital projection");
        prepared.vital_templates_=std::move(raw);
        prepared.owned_vitals_=std::move(sources);
        return prepared;
    }
    // CUSTOM-0110 internally produces the complete initial17-byte grant from
    // exact private player receipts. S82 and S88 remain complete supplied data;
    // the existing waiting/both0B schedule withholds these grants from entry.
    static Prepared prepare_waiting_notification_owned_initial_grants(OwnedPlayers players,OwnedVitals vitals,
            const std::array<InitialGrantView,2>& views,const TaiwanNativeFightCatalog& catalog){
        auto first=OwnedTaiwanPkInitialGrantSource::observe(players[0]);
        auto second=OwnedTaiwanPkInitialGrantSource::observe(players[1]);
        if(!first||!second)throw std::invalid_argument("PK initial grant requires current private player sources");
        OwnedInitialGrants sources{std::move(*first),std::move(*second)};
        const std::array<View,2> supplied{{
            {views[0].context,views[0].friendly_bulk,RecoveredBattlePlayerGrant::encode(sources[0].grant())},
            {views[1].context,views[1].friendly_bulk,RecoveredBattlePlayerGrant::encode(sources[1].grant())}}};
        auto prepared=prepare_waiting_notification_owned_vitals(std::move(players),std::move(vitals),supplied,catalog);
        for(std::size_t i=0;i<2;++i)
            if(sources[i].player()!=(*prepared.owned_players_)[i]||
               sources[i].player().combat()!=(*prepared.owned_vitals_)[i].combat()||!sources[i].current())
                throw std::invalid_argument("PK initial grant lost its exact current player/combat source");
        for(const auto& player:*prepared.owned_players_)if(!player.current())
            throw std::invalid_argument("PK owned player changed during initial grant projection");
        prepared.owned_initial_grants_=std::move(sources);
        return prepared;
    }
    // CUSTOM-0111 no caller82/88/grant templates: complete initial presentation
    // derives from exact private players/vitals and explicit bounded policy.
    // Old factories retain absent source and their original byte/readset paths.
    static Prepared prepare_waiting_notification_owned_initial_contexts(OwnedPlayers players,OwnedVitals vitals,
            const TaiwanNativeFightCatalog& catalog){
        auto first=OwnedTaiwanPkInitialContextSource::observe(players[0],vitals[0]);
        auto second=OwnedTaiwanPkInitialContextSource::observe(players[1],vitals[1]);
        if(!first||!second)throw std::invalid_argument("PK initial context requires exact current private sources");
        OwnedInitialContexts sources{std::move(*first),std::move(*second)};
        const std::array<InitialGrantView,2> views{{{sources[0].context(),sources[0].bulk()},
                                                  {sources[1].context(),sources[1].bulk()}}};
        auto prepared=prepare_waiting_notification_owned_initial_grants(std::move(players),std::move(vitals),views,catalog);
        for(std::size_t i=0;i<2;++i)
            if(sources[i].player()!=(*prepared.owned_players_)[i]||
               sources[i].vital()!=(*prepared.owned_vitals_)[i]||!sources[i].current())
                throw std::invalid_argument("PK initial context lost its exact owned source incarnation");
        for(const auto& player:*prepared.owned_players_)if(!player.current())
            throw std::invalid_argument("PK owned player changed during initial context projection");
        prepared.owned_initial_contexts_=std::move(sources);
        return prepared;
    }
private:
    static Prepared prepare_impl(const std::array<Player,2>& players,const std::array<View,2>& views,bool waiting,bool notification,
            const OwnedPlayers* owned_players=nullptr){
        std::array<std::array<std::uint32_t,4>,2> resources{};
        std::array<std::uint16_t,2> levels{};
        for(std::size_t i=0;i<2;++i){
            resources[i]={players[i].hp.current(),players[i].hp.maximum(),players[i].mp.current(),players[i].mp.maximum()};
            levels[i]=players[i].identity.displayed_level();
        }
        for(const auto& view:views)if(!RecoveredBattlePlayerGrant::parse(view.initial_control))
            throw std::invalid_argument("PK requires a qualified primary owner-slot0 grant");
        auto records=owned_players?logical_owned(players,views,*owned_players):logical(players,views);
        if(waiting)for(auto& bytes:records)bytes.resize(bytes.size()-17);
        std::optional<ControlMasks> bounds;
        if(notification){
            bounds.emplace();
            // logical() validated BOTH complete players; each actual relative
            // entry contains own0 and other14 and has no additional actors.
            for(auto& view:*bounds)for(const auto position:{0u,14u})
                view[position/14]|=static_cast<std::uint16_t>(1u<<(position%14));
        }
        return Prepared(std::move(records),{players[0].character,players[1].character},resources,levels,
            {views[0].initial_control,views[1].initial_control},
            {views[0].context.context_a,views[1].context.context_a},waiting,bounds);
    }
public:
    // Each viewer sees their owned role at0 and the opponent at14. The shared
    // room owns canonical controller/side assignments; these are wire views.
    // Native side1 MP does not write the opponent actor, so emit only own MP.
    static std::array<std::vector<std::uint8_t>,2> logical(
        const std::array<Player,2>& players,const std::array<View,2>& views){
        for(const auto&p:players)validate(p);
        if(players[0].character==players[1].character)throw std::invalid_argument("PK requires distinct owned roles");
        return {one(players[0],players[1],views[0]),one(players[1],players[0],views[1])};
    }
private:
    // Only the owning-player factory calls this path. Each profile retains
    // its own full saved owner and exact private native actor proof.
    static std::array<std::vector<std::uint8_t>,2> logical_owned(
            const std::array<Player,2>& players,const std::array<View,2>& views,const OwnedPlayers& sources){
        for(std::size_t i=0;i<2;++i){
            const auto& source=sources[i];const auto& m=source.combat().appearance().material();
            if(!source.current()||players[i].character!=m.lease.character||
               !qualified_taiwan_scene_handle(m.lease.actor_handle)||
               players[i].identity.identity_word()!=m.lease.actor_handle||
               !valid_taiwan_world_entry_identity(source.identity_profile()))
                throw std::invalid_argument("PK native identity requires the exact owned player source");
            if(source.identity_profile()==TaiwanWorldEntryIdentity::SelectedCharacter)validate(players[i]);
            else{
                // Validation-only local wire namespace. Original characters
                // are never rewritten in Prepared or supplied room identity.
                auto native=players[i];native.character=m.lease.actor_handle;validate(native);
            }
        }
        if(players[0].character==players[1].character||
           players[0].identity.identity_word()==players[1].identity.identity_word())
            throw std::invalid_argument("PK requires distinct owned roles and native actors");
        return {one(players[0],players[1],views[0]),one(players[1],players[0],views[1])};
    }
    static void validate(const Player&p){
        // Native world FC1C0 uses low12-bit identity; FAC70's lookup is exact.
        // Do not fabricate a cache alias for a wider saved/server role ID.
        if(!p.character||p.character>0xfff||p.identity.identity_word()!=p.character||
           (p.identity.variant()&0x6000)!=0x2000||!p.identity.displayed_level()||
           !p.appearance.ordinary_mode1()||p.hp.resource()!=RecoveredBattleVitals::Resource::Hp||
           p.mp.resource()!=RecoveredBattleVitals::Resource::Mp||!p.hp.current()||
           p.hp.current()>p.hp.maximum()||p.mp.current()>p.mp.maximum())
            throw std::invalid_argument("Unqualified owned PK player projection");
    }
    static RecoveredBattleIdentity::Record identity_at(const Player&p,std::uint8_t position){
        auto bytes=RecoveredBattleIdentity::encode_logical(p.identity);bytes[1]=position;
        return *RecoveredBattleIdentity::parse_logical(bytes);
    }
    static RecoveredBattleVitals::Record vital_at(const RecoveredBattleVitals::Record&r,std::uint8_t position){
        auto bytes=RecoveredBattleVitals::encode_logical(r);bytes[2]=position;
        return *RecoveredBattleVitals::parse_logical(bytes);
    }
    static std::vector<std::uint8_t> one(const Player&own,const Player&other,const View&view){
        if(view.initial_control[4]!=0)throw std::invalid_argument("PK opening grant must target owned slot0");
        // 82 second context lowFF selects observation mode in1113BF.
        // Keep opaque contexts caller-supplied; never derive them from a room
        // ID or overwrite the original initializer's local character context.
        if((view.context.context_b&0xff)==0xff)throw std::invalid_argument("PK participant cannot use observer entry context");
        const std::array actors{
            RecoveredBattleBootstrap::Actor{identity_at(own,0),vital_at(own.hp,0),vital_at(own.mp,0)},
            RecoveredBattleBootstrap::Actor{identity_at(other,14),vital_at(other.hp,14),std::nullopt}};
        // ready_logical enforces one actor per slot, coherent owned88 vitals,
        // non-sentinel counter and complete native86/5 opening grant grammar.
        auto result=RecoveredBattleBootstrap::ready_logical(view.context.context_a,view.context.context_b,
            actors,view.friendly_bulk,view.initial_control);
        // Native82 normal initialization calls11FC40 and fills168 pointers.
        // Their renderer handles start-1; ordinary86/4 must precede player1C.
        // Insert both prepared records AFTER82 and BEFORE either1C, retaining
        // all opaque bytes and all packed appearance bits from owned inputs.
        const auto own_appearance=RecoveredBattlePlayerAppearance::encode(
            RecoveredBattlePlayerAppearance::at_position(own.appearance,0));
        const auto other_appearance=RecoveredBattlePlayerAppearance::encode(
            RecoveredBattlePlayerAppearance::at_position(other.appearance,14));
        result.insert(result.begin()+RecoveredBattleEntry::logical_size,other_appearance.begin(),other_appearance.end());
        result.insert(result.begin()+RecoveredBattleEntry::logical_size,own_appearance.begin(),own_appearance.end());
        return result;
    }
};
}
