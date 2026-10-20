#pragma once
#include "net/Session.h"
#include "game/SharedTaiwanOwnedDeitySkillSource.h"
#include "game/LegacyTaiwanOwnedDeitySelectionRegistry.h"
#include "handlers/RecoveredOwnedCompanions.h"
#include "protocol/RecoveredInventoryItemRequest.h"
#include "protocol/RecoveredTargetItemRequest.h"
#include <atomic>
#include <array>
#include <utility>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <map>
#include <memory>
#include <optional>
#include <span>
#include <thread>
#include <variant>
#include <vector>
namespace god2 {
class SqliteSkillBookLearningRepository;
class LuaEngine;
class SharedWorldPresence;
struct NativeEquipmentSnapshot;
// CUSTOM-0148 actual shared transaction host. Native C25/C26/S34/S35/S41 layouts
// do not recover eligibility, selected-subject policy, debit or learning order.
// Construct/use/stop on the same serial game owner; borrowed DB/Lua outlive it.
class OwnedSkillBookLearningService final {
    struct Entry;
    struct Operation;
    struct Lifetime;
    struct MaterialEpoch;
public:
    class WrittenLearningSource;
    class MaterialAdmission {
        struct Data;
        friend class OwnedSkillBookLearningService;
    public:
        MaterialAdmission(const MaterialAdmission&)=default;
        MaterialAdmission& operator=(const MaterialAdmission&)=default;
    private:
        explicit MaterialAdmission(std::shared_ptr<Data> data):data_(std::move(data)){}
        std::shared_ptr<Data> data_;
    };
    class WrittenMaterialSource {
        struct Data;
        friend class OwnedSkillBookLearningService;
    public:
        WrittenMaterialSource(const WrittenMaterialSource&)=default;
        WrittenMaterialSource& operator=(const WrittenMaterialSource&)=default;
        bool current(Session&) const;
        const Session::NormalWorldInitialization& initialization() const noexcept;
        const std::shared_ptr<const RecoveredOwnedCompanions::Restoration>& material() const noexcept;
        bool same_source(const WrittenMaterialSource& value) const noexcept{return data_==value.data_;}
    private:
        explicit WrittenMaterialSource(std::shared_ptr<Data> data):data_(std::move(data)){}
        std::shared_ptr<Data> data_;
    };
    OwnedSkillBookLearningService(SqliteSkillBookLearningRepository&,LuaEngine&,std::size_t actual_session_capacity);
    ~OwnedSkillBookLearningService();
    // Game-owned immutable provenance; only this actual service publishes it.
    // It is not a native ACK, renewed player/companion source or PK-ready grant.
    class LearningPublication {
        struct Data;
        friend class OwnedSkillBookLearningService;
        friend class WrittenLearningSource;
    public:
        LearningPublication(const LearningPublication&)=default;
        LearningPublication& operator=(const LearningPublication&)=default;
        LearningPublication(LearningPublication&&)noexcept=default;
        LearningPublication& operator=(LearningPublication&&)noexcept=default;
        const SqliteSkillBookLearningRepository::Restoration& after_source()const noexcept;
        const SqliteSkillBookLearningRepository::Committed& committed()const noexcept;
        const std::shared_ptr<const RecoveredOwnedCompanions::Restoration>& original_restoration()const noexcept;
        const Session::NormalWorldInitialization& initialization()const noexcept;
        bool operator==(const LearningPublication& other)const noexcept{return data_==other.data_;}
    private:
        explicit LearningPublication(std::shared_ptr<Data> data)noexcept:data_(std::move(data)){}
        std::shared_ptr<Data> data_;
    };
    // Owning copy of the actual Bound/Written learning event, not Current by
    // its getters. Only the service mints it after full own-source qualification.
    class WrittenLearningSource {
        friend class OwnedSkillBookLearningService;
    public:
        WrittenLearningSource(const WrittenLearningSource&)=default;
        WrittenLearningSource& operator=(const WrittenLearningSource&)=default;
        // Retain non-null private holders in the moved-from value too.
        WrittenLearningSource(WrittenLearningSource&& value)noexcept
            :publication_(value.publication_),response_(value.response_){}
        WrittenLearningSource& operator=(WrittenLearningSource&& value)noexcept {
            publication_=value.publication_;response_=value.response_;return *this;
        }
        const SqliteSkillBookLearningRepository::Restoration& before_source()const noexcept;
        const SqliteSkillBookLearningRepository::Restoration& after_source()const noexcept;
        const SqliteSkillBookLearningRepository::Committed& committed()const noexcept;
        const LearningPublication& publication()const noexcept{return publication_;}
        const Session::WorldResponseWrite& response()const noexcept{return response_;}
        const std::vector<std::uint8_t>& wire()const noexcept;
        const std::array<std::uint8_t,13>& logical_delta()const noexcept;
        const std::shared_ptr<const RecoveredOwnedCompanions::Restoration>& original_restoration()const noexcept;
        const Session::NormalWorldInitialization& initialization()const noexcept;
        bool follows(const std::optional<LearningPublication>&)const noexcept;
        bool current(Session&)const;
        bool operator==(const WrittenLearningSource& value)const noexcept{return publication_==value.publication_;}
    private:
        WrittenLearningSource(const LearningPublication& p,const Session::WorldResponseWrite& r)noexcept
            :publication_(p),response_(r){}
        LearningPublication publication_;
        Session::WorldResponseWrite response_;
    };
    class UseResult {
        friend class OwnedSkillBookLearningService;
    public:
        UseResult(const UseResult&)=delete;
        UseResult& operator=(const UseResult&)=delete;
        UseResult(UseResult&&)noexcept;
        UseResult& operator=(UseResult&&)noexcept;
        ~UseResult();
        std::vector<std::uint8_t> take_wire()&&noexcept{return std::move(wire_);}
        const std::optional<LearningPublication>& publication()const noexcept{return publication_;}
    private:
        UseResult(std::vector<std::uint8_t>,std::optional<LearningPublication>)noexcept;
        std::vector<std::uint8_t> wire_;
        std::optional<LearningPublication> publication_;
        bool owns_unbound_=false;
    };
    using RestorationSupplier=std::function<std::shared_ptr<const RecoveredOwnedCompanions::Restoration>(Session&)>;
    // Root facade invokes FIRST, before allocation/classification/old handlers.
    // Caught nested non-book callbacks must poison an active learning operation.
    void preflight(Session&);
    bool claims(std::uint16_t item);
    using UseRequest=std::variant<RecoveredInventoryItemRequest::Request,RecoveredTargetItemRequest::Request>;
    std::optional<std::vector<std::uint8_t>> use(Session&,const RecoveredInventoryItemRequest::Request&,
        const std::shared_ptr<SharedWorldPresence>& presence={});
    // C26 retains its original type/target/tail. Only the exact retained own
    // entry actor is qualified; that actor does not select the learning deity.
    std::optional<std::vector<std::uint8_t>> use(Session&,const RecoveredTargetItemRequest::Request&,
        const std::shared_ptr<SharedWorldPresence>& presence={});
    std::optional<UseResult> use_with_source(Session&,const RecoveredInventoryItemRequest::Request&,
        const std::shared_ptr<SharedWorldPresence>& presence={});
    std::optional<UseResult> use_with_source(Session&,const RecoveredTargetItemRequest::Request&,
        const std::shared_ptr<SharedWorldPresence>& presence={});
    void bind_learning_response(Session&,const LearningPublication&,const Session::WorldResponseWrite&);
    bool learning_publication_current(Session&,const LearningPublication&);
    std::optional<LearningPublication> latest_learning_publication(Session&);
    std::optional<WrittenLearningSource> written_learning_source(Session&,const LearningPublication&);
    bool written_learning_source_current(Session&,const WrittenLearningSource&);
    // Original complete framed aggregate, allocated before any mutation.
    // Projection is not Written. Root captures ONE final whole callback WWR,
    // holds existing input continuation and then binds that actual receipt.
    std::optional<std::vector<std::uint8_t>> bootstrap(Session&,
        const std::shared_ptr<SharedWorldPresence>& presence,const RestorationSupplier& restored);
    void bind_bootstrap_response(Session&,const Session::WorldResponseWrite&);
    // Actual Written S31 continuation only. Preserve the last real learning
    // chronology while retiring its Current; selection is never learning.
    // No existing Entry is an explicit no-op, not a new source/publication.
    bool reanchor_selection(Session&,
        std::shared_ptr<const RecoveredOwnedCompanions::Restoration> predecessor,
        std::shared_ptr<const RecoveredOwnedCompanions::Restoration> canonical_after,
        SharedTaiwanOwnedDeitySkillSource::WrittenSelectionSource);
    // Actual legacy callback cohort, not a manufactured whole-response receipt.
    // Uses the identical complete predecessor/commit/history/after checks.
    bool reanchor_selection(Session&,
        std::shared_ptr<const RecoveredOwnedCompanions::Restoration> predecessor,
        std::shared_ptr<const RecoveredOwnedCompanions::Restoration> canonical_after,
        LegacyTaiwanOwnedDeitySelectionRegistry::WrittenSelectionSource);
    // Written exact final original reply + private actual mutation edge only.
    // Preserve original deity/learning history; no restore/replay or new Entry.
    // Capture BEFORE actual original mutation dispatch; never reconstruct this
    // witness after a commit or after Entry release/rebootstrap.
    std::optional<MaterialAdmission> prepare_material(Session&,
        std::shared_ptr<const RecoveredOwnedCompanions::Restoration> predecessor);
    // Actual prepared room entry captures the exact Entry/null-Entry before
    // combat. Release/rebootstrap retires it; return cannot reconstruct it.
    std::optional<MaterialAdmission> prepare_pve_return(Session&,const Session::OwnedPveBinding&,
        std::shared_ptr<const RecoveredOwnedCompanions::Restoration> predecessor);
    bool pve_return_admission_current(Session&,const Session::OwnedPveBinding&,const MaterialAdmission&)const noexcept;
    std::optional<WrittenMaterialSource> reanchor_pve_return(Session&,
        std::shared_ptr<const RecoveredOwnedCompanions::Restoration> predecessor,
        std::shared_ptr<const RecoveredOwnedCompanions::Restoration> canonical_after,
        std::shared_ptr<SqliteOwnedPveRoomRepository>,const SqliteOwnedPveRoomRepository::ReturnContinuation&,
        const Session::OwnedPveReturnSource&,const MaterialAdmission&);
    void abandon_material(const MaterialAdmission&) noexcept;
    std::optional<WrittenMaterialSource> reanchor_material(Session&,
        std::shared_ptr<const RecoveredOwnedCompanions::Restoration> predecessor,
        std::shared_ptr<const RecoveredOwnedCompanions::Restoration> canonical_after,
        std::shared_ptr<SqliteOwnedEquipmentTransaction>,const SqliteOwnedEquipmentTransaction::Committed&,
        const Session::NormalWorldInitialization&,const Session::WorldResponseWrite&,const MaterialAdmission&);
    std::optional<WrittenMaterialSource> reanchor_material_chain(Session&,
        std::shared_ptr<const RecoveredOwnedCompanions::Restoration> predecessor,
        std::shared_ptr<const RecoveredOwnedCompanions::Restoration> canonical_after,
        std::shared_ptr<SqliteOwnedEquipmentTransaction>,std::span<const SqliteOwnedEquipmentTransaction::Committed* const>,
        const Session::NormalWorldInitialization&,const Session::WorldResponseWrite&,const MaterialAdmission&);
    void release(Session&);
    void stop();
private:
    bool material_current(Session&,const std::shared_ptr<WrittenMaterialSource::Data>&);
    bool admit_material_epoch(Session&,const Session::NormalWorldInitialization&);
    using SelectionSource=std::variant<SharedTaiwanOwnedDeitySkillSource::WrittenSelectionSource,
        LegacyTaiwanOwnedDeitySelectionRegistry::WrittenSelectionSource>;
    bool reanchor_selection_impl(Session&,
        std::shared_ptr<const RecoveredOwnedCompanions::Restoration>,
        std::shared_ptr<const RecoveredOwnedCompanions::Restoration>,SelectionSource);
    std::optional<UseResult> use_request(Session&,UseRequest,
        const std::shared_ptr<SharedWorldPresence>& presence,bool with_source);
    bool publication_current(Session&,const std::shared_ptr<LearningPublication::Data>&);
    bool publication_local(Session&,const std::shared_ptr<Entry>&,
        const std::shared_ptr<LearningPublication::Data>&)const;
    void discard_publication(const std::shared_ptr<LearningPublication::Data>&)noexcept;
    static void revoke_publication(const std::shared_ptr<LearningPublication::Data>&,bool close_unsettled)noexcept;
    static void abandon_unbound(const LearningPublication&)noexcept;
    void owner() const;
    bool ready(Session&,const std::shared_ptr<Entry>&,bool written) const;
    bool retained_learning_written(Session&,const std::shared_ptr<Entry>&,
        const std::shared_ptr<LearningPublication::Data>&)const;
    bool qualify_presence(Session&,const std::shared_ptr<Entry>&,const NativeEquipmentSnapshot&) const;
    void retire(Session&,const std::shared_ptr<Entry>&) noexcept;
    SqliteSkillBookLearningRepository& repository_;
    LuaEngine& lua_;
    const std::size_t capacity_;
    const std::thread::id thread_=std::this_thread::get_id();
    std::map<std::uint64_t,std::shared_ptr<Entry>> entries_;
    std::map<std::uint64_t,std::shared_ptr<WrittenMaterialSource::Data>> material_sources_;
    std::map<std::uint64_t,std::shared_ptr<MaterialAdmission::Data>> material_admissions_;
    std::map<std::uint64_t,std::shared_ptr<MaterialEpoch>> material_epochs_;
    // Only bootstrap's owned supplier call may borrow this exact passive
    // source read; SQL callbacks cannot recursively enter material_current.
    std::shared_ptr<WrittenMaterialSource::Data> passive_material_window_;
    std::shared_ptr<Entry> passive_material_entry_;
    bool material_reading_=false;
    bool live_=true,busy_=false,poisoned_=false;
    std::shared_ptr<Lifetime> lifetime_;
    std::weak_ptr<LearningPublication::Data> active_publication_;
};
}
