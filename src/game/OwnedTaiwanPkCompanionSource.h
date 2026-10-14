#pragma once
#include "handlers/RecoveredOwnedCompanions.h"
#include "db/SqliteSupport.h"
#include "net/Session.h"
#include "protocol/RecoveredWorldFrame.h"
#include <algorithm>
#include <memory>
#include <optional>
#include <stdexcept>
#include <thread>
#include <utility>

namespace god2 {
// CUSTOM-0129 opt-in retained companion publication source for PK admission.
// Exact local writes + saved rows + expected normal-reset DATA prefix, NOT
// remote consumption, selected deity HP/maxHP, skill permission or settlement.
// Borrowed repository/helper/catalog/connection outlive every Observation and
// ticket. Live checks run on the actual game executor outside SQL scopes;
// RESERVED stored checks borrow the room transaction without Session callbacks.
class OwnedTaiwanPkCompanionSource final {
    struct State;
public:
    // Actual callback response coverage only. No per-batch write is invented.
    class WholeResponseCoverage {
    public:
        WholeResponseCoverage(const WholeResponseCoverage&)=default;
        WholeResponseCoverage& operator=(const WholeResponseCoverage&)=default;
        WholeResponseCoverage(WholeResponseCoverage&& other)noexcept:data_(other.data_){}
        WholeResponseCoverage& operator=(WholeResponseCoverage&& other)noexcept{data_=other.data_;return *this;}
        const Session::WorldResponseWrite& receipt()const noexcept{return data_->receipt;}
        const std::vector<std::uint8_t>& wire()const noexcept{return data_->wire;}
        const std::vector<std::uint8_t>& suffix()const noexcept{return data_->suffix;}
        std::size_t suffix_offset()const noexcept{return data_->suffix_offset;}
        std::size_t suffix_size()const noexcept{return data_->suffix.size();}
        std::size_t batch_count()const noexcept{return data_->batch_count;}
        bool operator==(const WholeResponseCoverage&)const=default;
    private:
        friend class OwnedTaiwanPkCompanionSource;
        struct Data {
            Data(Session::WorldResponseWrite receipt_,std::vector<std::uint8_t> wire_,
                    std::vector<std::uint8_t> suffix_,std::size_t count)
                :receipt(std::move(receipt_)),wire(std::move(wire_)),suffix(std::move(suffix_)),
                 suffix_offset(wire.size()-suffix.size()),batch_count(count){}
            Session::WorldResponseWrite receipt;
            std::vector<std::uint8_t> wire,suffix;
            const std::size_t suffix_offset,batch_count;
        };
        explicit WholeResponseCoverage(std::shared_ptr<const Data> data):data_(std::move(data)){}
        std::shared_ptr<const Data> data_;
    };
    struct Material {
        Session::NormalWorldInitialization initialization;
        RecoveredOwnedCompanions::Restoration restoration;
        TaiwanNativeDeityRosterPrefix prefix;
        std::vector<Session::WorldRecordsWrite> writes;
        std::uint64_t session,account,character,battle_generation;
        SessionState phase;
        std::optional<WholeResponseCoverage> whole_response{}; // Absent on the exact legacy path.
    };
    class Observation {
    public:
        Observation(const Observation&)=default;
        Observation& operator=(const Observation&)=default;
        Observation(Observation&&)=default;
        Observation& operator=(Observation&&)=default;
        const Material& material()const noexcept{return *material_;}
        bool current()const;
        bool uses_connection(const sqlite3*)const noexcept;
        bool stored_current_in_room_transaction(sqlite3*)const;
        bool operator==(const Observation&)const=default;
    private:
        friend class OwnedTaiwanPkCompanionSource;
        Observation(std::shared_ptr<State> state,std::shared_ptr<const Material> material)
            :state_(std::move(state)),material_(std::move(material)){}
        std::shared_ptr<State> state_;
        std::shared_ptr<const Material> material_;
    };
    static std::optional<Observation> observe(sqlite3*,SqliteCompanionRepository&,
        RecoveredOwnedCompanions&,const NativeSkillCatalog&,std::shared_ptr<Session>,
        Session::NormalWorldInitialization,RecoveredOwnedCompanions::Restoration,
        std::vector<Session::WorldRecordsWrite>);
    static std::optional<Observation> observe(sqlite3*,SqliteCompanionRepository&,
        RecoveredOwnedCompanions&,const NativeSkillCatalog&,std::shared_ptr<Session>,
        Session::NormalWorldInitialization,RecoveredOwnedCompanions::Restoration,
        Session::WorldResponseWrite,std::vector<std::uint8_t> original_whole_wire);
private:
    static bool whole_current(const WholeResponseCoverage& coverage,const Session& session,
            std::size_t batches){
        const auto& wire=coverage.wire();const auto& suffix=coverage.suffix();
        return batches&&coverage.batch_count()==batches&&!suffix.empty()&&suffix.size()<=wire.size()&&
            coverage.suffix_offset()==wire.size()-suffix.size()&&
            std::equal(suffix.begin(),suffix.end(),wire.begin()+coverage.suffix_offset())&&
            coverage.receipt().wire()==wire&&
            coverage.receipt().status()==Session::WorldResponseWriteStatus::Written&&
            session.world_response_write_current_on_game(coverage.receipt());
    }
    static std::optional<WholeResponseCoverage> cover_whole(Session& session,
            Session::WorldResponseWrite receipt,std::vector<std::uint8_t> wire,
            const std::vector<std::vector<std::uint8_t>>& batches){
        if(batches.empty()||receipt.wire()!=wire||
           receipt.status()!=Session::WorldResponseWriteStatus::Written||
           !session.world_response_write_current_on_game(receipt))return {};
        std::vector<std::uint8_t> suffix;
        for(const auto& batch:batches){
            const auto frame=RecoveredWorldFrame::encode(batch);
            if(frame.size()>suffix.max_size()-suffix.size())return {};
            suffix.insert(suffix.end(),frame.begin(),frame.end());
        }
        if(suffix.empty()||suffix.size()>wire.size()||
           !std::equal(suffix.begin(),suffix.end(),wire.end()-suffix.size()))return {};
        const auto begin=wire.size()-suffix.size();bool boundary=false;
        // The actual WWR mint already validated complete frames/checksums.
        // Walk only length envelopes; never decode/reframe its original prefix.
        for(std::size_t at=0;at<wire.size();){
            if(at==begin)boundary=true;
            if(wire.size()-at<2)return {};
            const auto length=static_cast<std::size_t>(wire[at])+256u*wire[at+1];
            if(length<4||length>wire.size()-at)return {};
            at+=length;
        }
        if(!boundary)return {};
        return WholeResponseCoverage(std::make_shared<const WholeResponseCoverage::Data>(
            std::move(receipt),std::move(wire),std::move(suffix),batches.size()));
    }
    struct State {
        sqlite3* db;
        SqliteCompanionRepository& repository;
        RecoveredOwnedCompanions& helper;
        const NativeSkillCatalog& catalog;
        std::weak_ptr<Session> session;
        const std::thread::id thread=std::this_thread::get_id();
        bool reading=false,reentered=false;
        bool identities()const noexcept{
            return db && repository.uses_connection(db) && helper.owns_repository(repository) &&
                catalog.uses_connection(db);
        }
        struct Read {
            State& state;bool entered=false;
            explicit Read(State& value):state(value){
                if(state.thread!=std::this_thread::get_id())
                    throw std::logic_error("TW PK companion game owner mismatch");
                if(state.reading){state.reentered=true;return;}
                state.reading=true;state.reentered=false;entered=true;
            }
            ~Read(){if(entered)state.reading=false;}
        };
        bool local(const Material& m)const{
            const auto peer=session.lock();
            // Private game-owner receipt BEFORE any mutable Session fields.
            if(reentered || !identities() || !peer ||
               !peer->normal_world_initialization_current_on_game(m.initialization) ||
               !m.initialization.entry_written())return false;
            if((m.phase!=SessionState::CharacterSelected && m.phase!=SessionState::InWorld) ||
               peer->closing() || peer->state()!=m.phase || peer->id()!=m.session ||
               peer->account_id!=m.account || peer->character_id!=m.character ||
               peer->battle_generation()!=m.battle_generation ||
               m.restoration.deity_roster().account()!=m.account ||
               m.restoration.deity_roster().character()!=m.character)return false;
            const auto& batches=m.restoration.batches();
            if(m.whole_response){
                if(!m.writes.empty()||m.prefix.actual_batches()!=batches||
                   !whole_current(*m.whole_response,*peer,batches.size()))return false;
            }else{
                if(m.writes.size()!=batches.size() || m.prefix.actual_batches()!=batches)return false;
                for(std::size_t i=0;i<m.writes.size();++i)
                    if(m.writes[i].logical()!=batches[i] ||
                       !peer->world_records_write_current_on_game(m.writes[i]) ||
                       m.writes[i].status()!=Session::WorldRecordsWriteStatus::Written)return false;
            }
            return !reentered;
        }
        bool current(const Material& m){
            Read read(*this);if(!read.entered || !identities() || !sqlite3_get_autocommit(db))return false;
            const auto changes=sqlite3_total_changes64(db);
            return local(m) && helper.restoration_current(m.restoration) && local(m) &&
                helper.normal_entry_prefix_current(m.restoration,m.prefix,catalog) && local(m) &&
                helper.restoration_current(m.restoration) && local(m) && !reentered &&
                sqlite3_get_autocommit(db) && sqlite3_total_changes64(db)==changes;
        }
        bool stored_current(const Material& m,sqlite3* actual){
            Read read(*this);
            if(!read.entered || actual!=db || !identities() || sqlite3_get_autocommit(db))return false;
            const auto changes=sqlite3_total_changes64(db);
            // Only concrete closed SQL reads. Never invoke live helper Current or
            // Session/presence/world-init callbacks inside the room transaction.
            if(!repository.deity_roster_current_in_transaction(m.restoration.deity_roster()))return false;
            // CUSTOM-0129 / CUSTOM-0148 original learning-present publication
            // includes the complete private inventory/equipment/header/event
            // source, not merely roster/catalog or exposed active skills.
            // This delegates ONLY a closed read on this existing actual scope.
            if(m.restoration.learning_source()&&
               !helper.restoration_learning_current_in_transaction(m.restoration,actual))return false;
            if(reentered||sqlite3_get_autocommit(db)||sqlite3_total_changes64(db)!=changes)return false;
            for(const auto* name:{"native_data_sources","native_skill_catalog"}){
                sqlite_detail::Statement shadow(db,"SELECT 1 FROM temp.sqlite_master WHERE name=? COLLATE NOCASE OR tbl_name=? COLLATE NOCASE LIMIT 1");
                shadow.bind(1,std::string(name));shadow.bind(2,std::string(name));
                if(shadow.row())return false;
                sqlite_detail::Statement base(db,"SELECT 1 FROM main.sqlite_master WHERE type='table' AND name=? COLLATE NOCASE");
                base.bind(1,std::string(name));if(!base.row() || base.row())return false;
            }
            for(const auto& expected:m.prefix.catalog_records()){
                const auto actual_record=catalog.lookup_main_digest_checked(
                    NativeSkillCatalog::current_dataset_id,expected.kind,expected.definition_id);
                if(reentered || !actual_record || *actual_record!=expected)return false;
            }
            return !reentered && !sqlite3_get_autocommit(db) && sqlite3_total_changes64(db)==changes;
        }
    };
};
inline bool OwnedTaiwanPkCompanionSource::Observation::current()const{
    const auto state=state_;const auto material=material_;
    return state && material && state->current(*material);
}
inline bool OwnedTaiwanPkCompanionSource::Observation::uses_connection(const sqlite3* db)const noexcept{
    return state_ && state_->db==db && state_->identities();
}
inline bool OwnedTaiwanPkCompanionSource::Observation::stored_current_in_room_transaction(sqlite3* db)const{
    const auto state=state_;const auto material=material_;
    return state && material && state->stored_current(*material,db);
}
inline std::optional<OwnedTaiwanPkCompanionSource::Observation> OwnedTaiwanPkCompanionSource::observe(
        sqlite3* db,SqliteCompanionRepository& repository,RecoveredOwnedCompanions& helper,
        const NativeSkillCatalog& catalog,std::shared_ptr<Session> session,
        Session::NormalWorldInitialization initialization,RecoveredOwnedCompanions::Restoration restoration,
        std::vector<Session::WorldRecordsWrite> writes){
    if(!db || !repository.uses_connection(db) || !helper.owns_repository(repository) ||
       !catalog.uses_connection(db) || !session ||
       !session->normal_world_initialization_current_on_game(initialization) || !initialization.entry_written())return {};
    // Capture only after the real private receipt qualified game/Session owner.
    const auto phase=session->state();
    const auto id=session->id(),account=session->account_id,character=session->character_id;
    const auto generation=session->battle_generation();
    if((phase!=SessionState::CharacterSelected && phase!=SessionState::InWorld) ||
       !account || !character || session->closing() || !sqlite3_get_autocommit(db) ||
       restoration.deity_roster().account()!=account || restoration.deity_roster().character()!=character ||
       writes.size()!=restoration.batches().size())return {};
    for(std::size_t i=0;i<writes.size();++i)
        if(writes[i].logical()!=restoration.batches()[i] || !session->world_records_write_current_on_game(writes[i]) ||
           writes[i].status()!=Session::WorldRecordsWriteStatus::Written)return {};
    const auto changes=sqlite3_total_changes64(db);
    auto prefix=helper.normal_entry_prefix(restoration,catalog);
    if(!prefix || !sqlite3_get_autocommit(db) || sqlite3_total_changes64(db)!=changes)return {};
    auto state=std::make_shared<State>(State{db,repository,helper,catalog,session});
    auto material=std::make_shared<const Material>(Material{std::move(initialization),std::move(restoration),
        std::move(*prefix),std::move(writes),id,account,character,generation,phase});
    Observation result(std::move(state),std::move(material));
    if(!result.current())return {};
    return result;
}
inline std::optional<OwnedTaiwanPkCompanionSource::Observation> OwnedTaiwanPkCompanionSource::observe(
        sqlite3* db,SqliteCompanionRepository& repository,RecoveredOwnedCompanions& helper,
        const NativeSkillCatalog& catalog,std::shared_ptr<Session> session,
        Session::NormalWorldInitialization initialization,RecoveredOwnedCompanions::Restoration restoration,
        Session::WorldResponseWrite whole,std::vector<std::uint8_t> original_whole_wire){
    if(!db||!repository.uses_connection(db)||!helper.owns_repository(repository)||
       !catalog.uses_connection(db)||!session||
       !session->normal_world_initialization_current_on_game(initialization)||!initialization.entry_written())return {};
    // Own arguments/receipt before any saved source/catalog observer.
    const auto phase=session->state();
    const auto id=session->id(),account=session->account_id,character=session->character_id;
    const auto generation=session->battle_generation();
    if((phase!=SessionState::CharacterSelected&&phase!=SessionState::InWorld)||
       !account||!character||session->closing()||!sqlite3_get_autocommit(db)||
       restoration.deity_roster().account()!=account||restoration.deity_roster().character()!=character)return {};
    auto coverage=cover_whole(*session,std::move(whole),std::move(original_whole_wire),restoration.batches());
    if(!coverage)return {}; // No vacuous suffix/receipt for a genuine NoRecords source.
    auto state=std::make_shared<State>(State{db,repository,helper,catalog,session});
    const auto local=[&]{
        return !state->reentered&&session->normal_world_initialization_current_on_game(initialization)&&
            initialization.entry_written()&&!session->closing()&&session->id()==id&&
            session->account_id==account&&session->character_id==character&&session->state()==phase&&
            session->battle_generation()==generation&&whole_current(*coverage,*session,restoration.batches().size());
    };
    std::optional<TaiwanNativeDeityRosterPrefix> prefix;
    {
        State::Read read(*state);if(!read.entered||!local())return {};
        const auto changes=sqlite3_total_changes64(db);
        prefix=helper.normal_entry_prefix(restoration,catalog);
        if(!prefix||!local()||!sqlite3_get_autocommit(db)||sqlite3_total_changes64(db)!=changes)return {};
    }
    auto material=std::make_shared<const Material>(Material{std::move(initialization),std::move(restoration),
        std::move(*prefix),{},id,account,character,generation,phase,std::move(coverage)});
    Observation result(std::move(state),std::move(material));
    if(!result.current())return {};
    return result;
}
}
