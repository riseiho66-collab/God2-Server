#pragma once
#include "net/Session.h"
#include "handlers/RecoveredOwnedCompanions.h"
#include "protocol/RecoveredInventoryItemRequest.h"
#include "protocol/RecoveredTargetItemRequest.h"
#include <atomic>
#include <utility>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <map>
#include <memory>
#include <optional>
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
public:
    OwnedSkillBookLearningService(SqliteSkillBookLearningRepository&,LuaEngine&,std::size_t actual_session_capacity);
    ~OwnedSkillBookLearningService();
    // Game-owned immutable provenance; only this actual service publishes it.
    // It is not a native ACK, renewed player/companion source or PK-ready grant.
    class LearningPublication {
        struct Data;
        friend class OwnedSkillBookLearningService;
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
    // Original complete framed aggregate, allocated before any mutation.
    // Projection is not Written. Root captures ONE final whole callback WWR,
    // holds existing input continuation and then binds that actual receipt.
    std::optional<std::vector<std::uint8_t>> bootstrap(Session&,
        const std::shared_ptr<SharedWorldPresence>& presence,const RestorationSupplier& restored);
    void bind_bootstrap_response(Session&,const Session::WorldResponseWrite&);
    void release(Session&);
    void stop();
private:
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
    bool qualify_presence(Session&,const std::shared_ptr<Entry>&,const NativeEquipmentSnapshot&) const;
    void retire(Session&,const std::shared_ptr<Entry>&) noexcept;
    SqliteSkillBookLearningRepository& repository_;
    LuaEngine& lua_;
    const std::size_t capacity_;
    const std::thread::id thread_=std::this_thread::get_id();
    std::map<std::uint64_t,std::shared_ptr<Entry>> entries_;
    bool live_=true,busy_=false,poisoned_=false;
    std::shared_ptr<Lifetime> lifetime_;
    std::weak_ptr<LearningPublication::Data> active_publication_;
};
}
