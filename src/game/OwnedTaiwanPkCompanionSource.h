#pragma once
#include "handlers/RecoveredOwnedCompanions.h"
#include "handlers/OwnedSkillBookLearningService.h"
#include "db/SqliteSupport.h"
#include "net/Session.h"
#include "protocol/RecoveredWorldFrame.h"
#include "game/OwnedTaiwanPkPlayerEntrySource.h"
#include "protocol/RecoveredRoleVitals.h"
#include <functional>
#include <algorithm>
#include <memory>
#include <optional>
#include <stdexcept>
#include <thread>
#include <utility>

namespace god2 {
class TaiwanInitialPlayerPublicationIssuer; // Sole mint bridge is defined only in Application.cpp.
// CUSTOM-0129 opt-in retained companion publication source for PK admission.
// Exact local writes + saved rows + expected normal-reset DATA prefix, NOT
// remote consumption, selected deity HP/maxHP, skill permission or settlement.
// Borrowed repository/helper/catalog/connection outlive every Observation and
// ticket. Live checks run on the actual game executor outside SQL scopes;
// RESERVED stored checks borrow the room transaction without Session callbacks.
class OwnedTaiwanPkCompanionSource final {
    struct State;
public:
    // Minted ONLY by the actual Application.cpp one-shot publisher bridge.
    // Original Written22/24 and its complete response remain owning inputs;
    // absence of deity records is not an empty frame, receipt or native ACK.
    class ZeroPublication {
    public:
        using OriginCurrent=std::function<bool()>;
        ZeroPublication(const ZeroPublication&)=default;
        ZeroPublication& operator=(const ZeroPublication&)=default;
        ZeroPublication(ZeroPublication&& other)noexcept:data_(other.data_){}
        ZeroPublication& operator=(ZeroPublication&& other)noexcept{data_=other.data_;return *this;}
        const OwnedTaiwanPkPlayerEntrySource::Observation& player()const noexcept{return data_->player;}
        const Session::WorldResponseWrite& receipt()const noexcept{return data_->receipt;}
        const std::vector<std::uint8_t>& wire()const noexcept{return data_->wire;}
        const std::vector<std::uint8_t>& player_frame()const noexcept{return data_->frame;}
        std::size_t player_offset()const noexcept{return data_->offset;}
        bool operator==(const ZeroPublication&)const=default;
        bool current()const {
            const auto data=data_;
            if(data->thread!=std::this_thread::get_id())
                throw std::logic_error("Zero deity publication game owner mismatch");
            if(data->reading){data->reentered=true;return false;}
            data->reading=true;data->reentered=false;
            struct End{bool& busy;~End(){busy=false;}}end{data->reading};
            return data->receipt.status()==Session::WorldResponseWriteStatus::Written&&
                data->origin_current()&&!data->reentered&&data->player.current()&&!data->reentered&&
                data->origin_current()&&!data->reentered&&
                data->receipt.status()==Session::WorldResponseWriteStatus::Written;
        }
    private:
        friend class TaiwanInitialPlayerPublicationIssuer; // Definition/mint only in Application.cpp.
        struct Data {
            const OwnedTaiwanPkPlayerEntrySource::Observation player;
            const Session::WorldResponseWrite receipt;
            const std::vector<std::uint8_t> wire,frame;
            const std::size_t offset;
            const OriginCurrent origin_current;
            const std::thread::id thread=std::this_thread::get_id();
            bool reading=false,reentered=false;
            Data(OwnedTaiwanPkPlayerEntrySource::Observation p,Session::WorldResponseWrite w,
                    std::vector<std::uint8_t> whole,std::vector<std::uint8_t> actual_frame,
                    std::size_t actual_offset,OriginCurrent current)
                :player(std::move(p)),receipt(std::move(w)),wire(std::move(whole)),frame(std::move(actual_frame)),
                 offset(actual_offset),origin_current(std::move(current)){}
        };
        ZeroPublication(OwnedTaiwanPkPlayerEntrySource::Observation player,Session::WorldResponseWrite whole,
                std::vector<std::uint8_t> wire,std::vector<std::uint8_t> frame,
                std::size_t offset,OriginCurrent current)
            :data_(std::make_shared<Data>(std::move(player),std::move(whole),std::move(wire),
                std::move(frame),offset,std::move(current))) {
            const auto& d=*data_;
            if(!d.origin_current||d.wire.empty()||d.frame.empty()||d.receipt.wire()!=d.wire||
               d.receipt.status()!=Session::WorldResponseWriteStatus::Written||
               d.offset>d.wire.size()||d.frame.size()!=d.wire.size()-d.offset||
               !std::equal(d.frame.begin(),d.frame.end(),d.wire.begin()+d.offset))
                throw std::invalid_argument("Zero deity publication requires actual original Written player response");
            bool boundary=false;
            for(std::size_t at=0;at<d.wire.size();) {
                if(d.wire.size()-at<2)throw std::invalid_argument("Zero deity response frame truncated");
                const auto length=static_cast<std::size_t>(d.wire[at])+256u*d.wire[at+1];
                if(length<4||length>d.wire.size()-at)
                    throw std::invalid_argument("Zero deity response frame envelope invalid");
                if(at==d.offset)boundary=length==d.frame.size();
                at+=length;
            }
            const auto logical=RecoveredWorldFrame::decode(d.frame);
            const auto& saved=d.player.combat().material();
            std::vector<std::uint8_t> expected(saved.role.logical.begin(),saved.role.logical.end());
            const auto vitals=RecoveredRoleVitals::encode(saved.resources.hp,saved.resources.mp,
                saved.resources.max_hp,saved.resources.max_mp);
            expected.insert(expected.end(),vitals.begin(),vitals.end());
            if(!boundary||!logical||*logical!=expected)
                throw std::invalid_argument("Zero deity publication player22/24 differs from original saved graph");
        }
        std::shared_ptr<Data> data_;
    };
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
    class Observation;
    class LearningSuccessor {
    public:
        const Observation& predecessor()const noexcept{return *data_->before;}
        const OwnedSkillBookLearningService::WrittenLearningSource& publication()const noexcept{return data_->publication;}
        const OwnedTaiwanPkPlayerEntrySource::Observation& player()const noexcept{return data_->player;}
    private:
        friend class OwnedTaiwanPkCompanionSource;
        struct Data {
            const std::shared_ptr<const Observation> before;
            const OwnedSkillBookLearningService::WrittenLearningSource publication;
            const OwnedTaiwanPkPlayerEntrySource::Observation player;
            Data(std::shared_ptr<const Observation> b,
                    OwnedSkillBookLearningService::WrittenLearningSource p,
                    OwnedTaiwanPkPlayerEntrySource::Observation actual_player)
                :before(std::move(b)),publication(std::move(p)),player(std::move(actual_player)){}
        };
        explicit LearningSuccessor(std::shared_ptr<const Data> data):data_(std::move(data)){}
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
        std::optional<ZeroPublication> zero_publication{}; // Original one-shot zero mode only.
        std::optional<LearningSuccessor> learning_successor{}; // Distinct actual Written learning lineage only.
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
        // Pure exact private node join for the actual Prepared player;
        // absence preserves legacy Room behavior, successors require the node.
        bool learning_player_matches(const OwnedTaiwanPkPlayerEntrySource::Observation&)const noexcept;
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
    static std::optional<Observation> observe_zero(sqlite3*,SqliteCompanionRepository&,
        RecoveredOwnedCompanions&,const NativeSkillCatalog&,std::shared_ptr<Session>,
        Session::NormalWorldInitialization,RecoveredOwnedCompanions::Restoration,ZeroPublication);
    static std::optional<Observation> observe_learning(sqlite3*,SqliteCompanionRepository&,
        RecoveredOwnedCompanions&,const NativeSkillCatalog&,std::shared_ptr<Session>,
        Session::NormalWorldInitialization,const Observation& predecessor,
        const OwnedTaiwanPkPlayerEntrySource::Observation& successor_player,
        OwnedSkillBookLearningService::WrittenLearningSource);
private:
    static bool learning_shape(const Material& m) {
        if(!m.learning_successor || m.zero_publication || m.whole_response || !m.writes.empty() ||
           !m.restoration.learning_source())return false;
        const auto& lineage=*m.learning_successor;const auto& before=lineage.predecessor().material();
        const auto& publication=lineage.publication();const auto& player=lineage.player();
        const auto& appearance=player.combat().appearance();const auto& shape=appearance.material();
        const auto& delta=publication.logical_delta();const auto& history=m.restoration.batches();
        const auto& prior=before.restoration.batches();
        std::optional<OwnedSkillBookLearningService::LearningPublication> previous;
        if(before.learning_successor)previous.emplace(before.learning_successor->publication().publication());
        if(!publication.follows(previous) || !player.matches_learning_source(publication) ||
           !publication.initialization().same_initialization(m.initialization) ||
           !before.initialization.same_initialization(m.initialization) ||
           before.session!=m.session || before.account!=m.account || before.character!=m.character ||
           before.battle_generation!=m.battle_generation || before.phase!=m.phase ||
           m.prefix.profile()!=before.prefix.profile() || history.size()!=prior.size()+1 ||
           m.prefix.actual_batches()!=history || history.back().size()!=delta.size() ||
           !std::equal(delta.begin(),delta.end(),history.back().begin()) ||
           publication.wire()!=publication.response().wire() ||
           !appearance.owns_initialization(m.initialization) ||
           shape.lease.session!=m.session || shape.lease.account!=m.account ||
           shape.lease.character!=m.character || shape.battle_generation!=m.battle_generation ||
           shape.inventory!=publication.after_source().inventory() ||
           shape.equipment!=publication.after_source().equipment())return false;
        for(std::size_t i=0;i<prior.size();++i)if(history[i]!=prior[i])return false;
        return true; // Private factories retain the exact committed fullafter State.
    }
    static bool zero_shape(const Material& m) {
        if(!m.zero_publication||!m.whole_response||!m.writes.empty()||
           !m.restoration.learning_source()||!m.restoration.learning_source()->activations().empty()||
           !m.restoration.deity_roster().rows().empty()||m.restoration.deity_roster().selection()||
           !m.restoration.batches().empty()||!m.prefix.actual_batches().empty()||
           m.prefix.roster_count()!=0||m.prefix.selected_row()!=-1||!m.prefix.catalog_records().empty())return false;
        const auto& publication=*m.zero_publication;const auto& coverage=*m.whole_response;
        const auto& player=publication.player();const auto& appearance=player.combat().appearance();
        const auto& shape=appearance.material();
        // observe_zero alone constructs this immutable coverage from THAT token's private receipt.
        return !coverage.wire().empty()&&coverage.wire()==publication.wire()&&
            coverage.receipt().wire()==publication.receipt().wire()&&
            coverage.receipt().status()==Session::WorldResponseWriteStatus::Written&&
            coverage.suffix().empty()&&coverage.suffix_offset()==coverage.wire().size()&&coverage.batch_count()==0&&
            appearance.owns_initialization(m.initialization)&&shape.lease.session==m.session&&
            shape.lease.account==m.account&&shape.lease.character==m.character&&shape.battle_generation==m.battle_generation&&
            NativeEquipmentSnapshot::same_root(shape.equipment.root,m.restoration.learning_source()->equipment().root)&&
            shape.equipment==m.restoration.learning_source()->equipment()&&
            shape.inventory==m.restoration.learning_source()->inventory();
    }
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
    static bool transport_history_current(const Material& latest,const Session& peer) {
        const Material* node=&latest;
        // Immutable single-predecessor private construction is acyclic. This
        // loop retains all original receipts without recursively querying old
        // saved tuples or requiring an earlier publication to remain latest.
        while(node->learning_successor) {
            if(!learning_shape(*node))return false;
            const auto& lineage=*node->learning_successor;const auto& written=lineage.publication().response();
            if(written.status()!=Session::WorldResponseWriteStatus::Written ||
               !peer.world_response_write_current_on_game(written))return false;
            node=&lineage.predecessor().material();
        }
        if(node->zero_publication)
            return zero_shape(*node) && node->zero_publication->receipt().status()==Session::WorldResponseWriteStatus::Written &&
                peer.world_response_write_current_on_game(node->zero_publication->receipt());
        const auto& batches=node->restoration.batches();
        if(node->whole_response)
            return node->writes.empty() && node->prefix.actual_batches()==batches &&
                whole_current(*node->whole_response,peer,batches.size());
        if(node->writes.size()!=batches.size() || node->prefix.actual_batches()!=batches)return false;
        for(std::size_t i=0;i<node->writes.size();++i)
            if(node->writes[i].logical()!=batches[i] ||
               node->writes[i].status()!=Session::WorldRecordsWriteStatus::Written ||
               !peer.world_records_write_current_on_game(node->writes[i]))return false;
        return true;
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
            if(reentered || !identities() || m.prefix.profile()!=catalog.taiwan_profile() || !peer ||
               !peer->normal_world_initialization_current_on_game(m.initialization) ||
               !m.initialization.entry_written())return false;
            if((m.phase!=SessionState::CharacterSelected && m.phase!=SessionState::InWorld) ||
               peer->closing() || peer->state()!=m.phase || peer->id()!=m.session ||
               peer->account_id!=m.account || peer->character_id!=m.character ||
               peer->battle_generation()!=m.battle_generation ||
               m.restoration.deity_roster().account()!=m.account ||
               m.restoration.deity_roster().character()!=m.character)return false;
            if(m.learning_successor) {
                const auto& lineage=*m.learning_successor;
                return learning_shape(m) && lineage.predecessor().uses_connection(db) &&
                    lineage.player().uses_connection(db) && lineage.publication().current(*peer) &&
                    !reentered && transport_history_current(m,*peer) &&
                    lineage.player().current() && !reentered &&
                    peer->normal_world_initialization_current_on_game(m.initialization) &&
                    m.initialization.entry_written() && !peer->closing() && peer->state()==m.phase &&
                    peer->id()==m.session && peer->account_id==m.account && peer->character_id==m.character &&
                    peer->battle_generation()==m.battle_generation;
            }
            if(m.zero_publication) {
                if(!zero_shape(m)||!m.zero_publication->player().uses_connection(db)||
                   !m.zero_publication->current()||reentered||
                   !peer->world_response_write_current_on_game(m.zero_publication->receipt())||
                   m.zero_publication->receipt().status()!=Session::WorldResponseWriteStatus::Written)return false;
                return !reentered&&peer->normal_world_initialization_current_on_game(m.initialization)&&
                    m.initialization.entry_written()&&!peer->closing()&&peer->state()==m.phase&&
                    peer->id()==m.session&&peer->account_id==m.account&&peer->character_id==m.character&&
                    peer->battle_generation()==m.battle_generation;
            }
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
        bool learning_catalog_current(const Material& m) {
            if(m.prefix.profile()!=catalog.taiwan_profile())return false;
            for(const auto& expected:m.prefix.catalog_records()) {
                const auto actual=catalog.lookup_main_digest_checked(catalog.taiwan_dataset_id(),
                    expected.kind,expected.definition_id);
                if(reentered || !actual || *actual!=expected)return false;
            }
            return !reentered;
        }
        bool current(const Material& m){
            Read read(*this);if(!read.entered || !identities() || !sqlite3_get_autocommit(db))return false;
            const auto changes=sqlite3_total_changes64(db);
            if(m.learning_successor)
                return local(m) && helper.restoration_current(m.restoration) && local(m) &&
                    learning_catalog_current(m) && local(m) &&
                    helper.restoration_current(m.restoration) && local(m) && !reentered &&
                    sqlite3_get_autocommit(db) && sqlite3_total_changes64(db)==changes;
            return local(m) && helper.restoration_current(m.restoration) && local(m) &&
                helper.normal_entry_prefix_current(m.restoration,m.prefix,catalog) && local(m) &&
                helper.restoration_current(m.restoration) && local(m) && !reentered &&
                sqlite3_get_autocommit(db) && sqlite3_total_changes64(db)==changes;
        }
        bool stored_current(const Material& m,sqlite3* actual){
            Read read(*this);
            if(!read.entered || actual!=db || !identities() ||
               m.prefix.profile()!=catalog.taiwan_profile() || sqlite3_get_autocommit(db))return false;
            const auto changes=sqlite3_total_changes64(db);
            // Immutable successor identity only. Do not call carrier/service/
            // Session/player Current or inspect old HP here; Reserved checks the
            // SAME Prepared player separately, Active/Finished use their ledger.
            if(m.learning_successor && (!learning_shape(m) ||
               !m.learning_successor->player().uses_connection(actual)))return false;
            // Only concrete closed SQL reads. Never invoke live helper Current or
            // Session/presence/world-init callbacks inside the room transaction.
            if(!repository.deity_roster_current_in_transaction(m.restoration.deity_roster()))return false;
            // CUSTOM-0129 / CUSTOM-0148 original learning-present publication
            // includes the complete private inventory/equipment/header/event
            // source, not merely roster/catalog or exposed active skills.
            // This delegates ONLY a closed read on this existing actual scope.
            if(m.restoration.learning_source()&&
               !helper.restoration_learning_current_in_transaction(m.restoration,actual))return false;
            // The actual Reserved room path separately checks this SAME Prepared player.
            // Generic companion custody retains admitted identity after terminal HP/MP save.
            if(m.zero_publication&&(!zero_shape(m)||!m.zero_publication->player().uses_connection(actual)))return false;
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
                    catalog.taiwan_dataset_id(),expected.kind,expected.definition_id);
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
inline bool OwnedTaiwanPkCompanionSource::Observation::learning_player_matches(
        const OwnedTaiwanPkPlayerEntrySource::Observation& player)const noexcept {
    if(!material_)return false;
    if(!material_->learning_successor)return true; // Exact legacy Room behavior remains unchanged.
    return material_->learning_successor->player()==player &&
        player.matches_learning_source(material_->learning_successor->publication());
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
inline std::optional<OwnedTaiwanPkCompanionSource::Observation> OwnedTaiwanPkCompanionSource::observe_zero(
        sqlite3* db,SqliteCompanionRepository& repository,RecoveredOwnedCompanions& helper,
        const NativeSkillCatalog& catalog,std::shared_ptr<Session> session,
        Session::NormalWorldInitialization initialization,RecoveredOwnedCompanions::Restoration restoration,
        ZeroPublication publication) {
    if(!db||!repository.uses_connection(db)||!helper.owns_repository(repository)||!catalog.uses_connection(db)||
       !session||!session->normal_world_initialization_current_on_game(initialization)||!initialization.entry_written()||
       !publication.player().uses_connection(db)||!sqlite3_get_autocommit(db)||
       !restoration.learning_source()||!restoration.deity_roster().rows().empty()||restoration.deity_roster().selection()||
       !restoration.batches().empty()||!restoration.learning_source()->activations().empty())return {};
    const auto phase=session->state();const auto id=session->id(),account=session->account_id,character=session->character_id;
    const auto generation=session->battle_generation();
    if((phase!=SessionState::CharacterSelected&&phase!=SessionState::InWorld)||!account||!character||session->closing()||
       restoration.deity_roster().account()!=account||restoration.deity_roster().character()!=character||
       !publication.player().combat().appearance().owns_initialization(initialization))return {};
    auto state=std::make_shared<State>(State{db,repository,helper,catalog,session});
    std::optional<TaiwanNativeDeityRosterPrefix> prefix;
    {
        State::Read read(*state);if(!read.entered)return {};
        const auto changes=sqlite3_total_changes64(db);
        const auto local=[&] {
            return !state->reentered&&session->normal_world_initialization_current_on_game(initialization)&&
                initialization.entry_written()&&!session->closing()&&session->state()==phase&&session->id()==id&&
                session->account_id==account&&session->character_id==character&&session->battle_generation()==generation&&
                session->world_response_write_current_on_game(publication.receipt())&&
                publication.receipt().status()==Session::WorldResponseWriteStatus::Written;
        };
        if(!local()||!publication.current()||!local())return {};
        prefix=helper.normal_entry_prefix(restoration,catalog);
        if(!prefix||!local()||!publication.current()||!local()||state->reentered||
           !sqlite3_get_autocommit(db)||sqlite3_total_changes64(db)!=changes)return {};
    }
    // The REAL nonempty complete Written response exists. Zero bytes mean
    // no deity suffix at its terminal boundary, never an encoded empty frame.
    WholeResponseCoverage coverage(std::make_shared<const WholeResponseCoverage::Data>(
        publication.receipt(),publication.wire(),std::vector<std::uint8_t>{},0));
    auto material=std::make_shared<const Material>(Material{std::move(initialization),std::move(restoration),
        std::move(*prefix),{},id,account,character,generation,phase,std::move(coverage),std::move(publication)});
    Observation result(std::move(state),std::move(material));
    if(!zero_shape(result.material())||!result.current())return {};
    return result;
}
inline std::optional<OwnedTaiwanPkCompanionSource::Observation> OwnedTaiwanPkCompanionSource::observe_learning(
        sqlite3* db,SqliteCompanionRepository& repository,RecoveredOwnedCompanions& helper,
        const NativeSkillCatalog& catalog,std::shared_ptr<Session> session,
        Session::NormalWorldInitialization initialization,const Observation& predecessor,
        const OwnedTaiwanPkPlayerEntrySource::Observation& successor_player,
        OwnedSkillBookLearningService::WrittenLearningSource publication) {
    const auto before=predecessor;const auto player=successor_player; // Own private nodes before observers.
    if(!db || !repository.uses_connection(db) || !helper.owns_repository(repository) ||
       !catalog.uses_connection(db) || !session || !before.uses_connection(db) ||
       !player.uses_connection(db) || !player.matches_learning_source(publication) ||
       !sqlite3_get_autocommit(db) || !initialization.entry_written() ||
       !session->normal_world_initialization_current_on_game(initialization))return {};
    const auto& original=before.material();
    const auto phase=session->state();const auto id=session->id(),account=session->account_id,character=session->character_id;
    const auto battle=session->battle_generation();
    if((phase!=SessionState::CharacterSelected && phase!=SessionState::InWorld) ||
       !account || !character || original.session!=id || original.account!=account ||
       original.character!=character || original.battle_generation!=battle || original.phase!=phase ||
       !original.initialization.same_initialization(initialization) ||
       !publication.initialization().same_initialization(initialization) ||
       original.prefix.profile()!=catalog.taiwan_profile() || !original.restoration.learning_source())return {};
    std::optional<OwnedSkillBookLearningService::LearningPublication> previous;
    if(original.learning_successor)previous.emplace(original.learning_successor->publication().publication());
    if(!publication.follows(previous))return {};
    const auto& delta=publication.logical_delta();
    const auto framed=RecoveredWorldFrame::encode(delta);
    if(framed!=publication.wire() || publication.response().wire()!=publication.wire())return {};
    auto state=std::make_shared<State>(State{db,repository,helper,catalog,session});
    std::optional<RecoveredOwnedCompanions::Restoration> restoration;
    std::optional<TaiwanNativeDeityRosterPrefix> prefix;
    {
        State::Read read(*state);if(!read.entered)return {};
        const auto changes=sqlite3_total_changes64(db);
        const auto local=[&] {
            return !state->reentered && state->identities() && sqlite3_get_autocommit(db) &&
                sqlite3_total_changes64(db)==changes && !session->closing() && session->state()==phase &&
                session->id()==id && session->account_id==account && session->character_id==character &&
                session->battle_generation()==battle && initialization.entry_written() &&
                session->normal_world_initialization_current_on_game(initialization) &&
                player.matches_learning_source(publication);
        };
        if(!local() || !publication.current(*session) || !local() ||
           !transport_history_current(original,*session) || !local())return {};
        auto history=original.restoration.batches();
        history.emplace_back(delta.begin(),delta.end());
        restoration=helper.learning_successor_from_committed(original.restoration,publication.committed(),std::move(history));
        if(!restoration || !local() || !publication.current(*session) || !local())return {};
        const auto definition=catalog.lookup_main_digest_checked(catalog.taiwan_dataset_id(),delta[2],delta[3]);
        if(!definition || !local())return {};
        prefix=TaiwanNativeDeityRosterPrefix::advance_written_learning(original.prefix,delta,*definition);
        if(!prefix || prefix->actual_batches()!=restoration->batches() || !local() ||
           !publication.current(*session) || !local() || !player.current() || !local())return {};
    }
    LearningSuccessor lineage(std::make_shared<const LearningSuccessor::Data>(
        std::make_shared<const Observation>(before),std::move(publication),player));
    auto material=std::make_shared<const Material>(Material{std::move(initialization),std::move(*restoration),
        std::move(*prefix),{},id,account,character,battle,phase,{},{},std::move(lineage)});
    Observation result(std::move(state),std::move(material));
    if(!learning_shape(result.material()) || !result.learning_player_matches(player) || !result.current())return {};
    return result;
}
}
