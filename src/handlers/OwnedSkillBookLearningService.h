#pragma once
#include "net/Session.h"
#include "handlers/RecoveredOwnedCompanions.h"
#include "protocol/RecoveredInventoryItemRequest.h"
#include "protocol/RecoveredTargetItemRequest.h"
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
public:
    OwnedSkillBookLearningService(SqliteSkillBookLearningRepository&,LuaEngine&,std::size_t actual_session_capacity);
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
    // Original complete framed aggregate, allocated before any mutation.
    // Projection is not Written. Root captures ONE final whole callback WWR,
    // holds existing input continuation and then binds that actual receipt.
    std::optional<std::vector<std::uint8_t>> bootstrap(Session&,
        const std::shared_ptr<SharedWorldPresence>& presence,const RestorationSupplier& restored);
    void bind_bootstrap_response(Session&,const Session::WorldResponseWrite&);
    void release(Session&);
    void stop();
private:
    std::optional<std::vector<std::uint8_t>> use_request(Session&,UseRequest,
        const std::shared_ptr<SharedWorldPresence>& presence);
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
};
}
