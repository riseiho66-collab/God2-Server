#pragma once
#include "cn/world/CnPrebornSubjectState.h"
#include "cn/assets/CnNativeSkillCatalog.h"
#include "cn/protocol/CnWorldSubjectSkillUpdate.h"
#include <memory>
#include <thread>

namespace god2cn {
// Optional actual recipient-native roster/bank recovery source. Owns all16
// rows, including inactive/stale bytes; does not select a common actor, grant
// learning, mutate a client or substitute native process access for authority.
class CnWorldSubjectSkillUpdateSource final:public std::enable_shared_from_this<CnWorldSubjectSkillUpdateSource> {
public:
    using Row=CnSelectedSubjectUpdate::Row;
    using Catalog=CnNativeSkillCatalog;
    using Wire=CnWorldSubjectSkillUpdate;
    static constexpr std::size_t row_slots=16,object_bytes=0x4508;
    static constexpr std::size_t max_records_per_projection=0xa00/4; //Existing single WORLD batch bound, not native gameplay cap.
    struct Scope {
        CnPrebornSubjectState::Scope subject;
        Catalog::Source definitions;
        std::uint32_t actual_bank_address,actual_selected_row;
        std::uint8_t actual_roster_count;
        bool operator==(const Scope&) const=default;
    };
    struct Bank {std::uint32_t address;std::span<const std::uint8_t> bytes;};
    // Actual same roster/bank/recipient-native revision; pure, nonyielding and
    // nonreentrant. Independent of the common post-commit publication revision.
    using Current=std::function<bool(const Scope&)>;
    enum class Action {AppendPrimary,DuplicateDiagnostic,CapacityReturn,SetFirstPointerFlag,MissingPointer};
    struct Delta {
        std::uint8_t roster_ordinal;
        Action action;
        Row before,after_primary_aux_stage;
        std::optional<std::uint8_t> primary_ordinal;
        bool auxiliary_rebuilt,selected_refresh_required,menu_refresh_required;
        // Selected35 has a separate actual UI pending/table branch, not owned
        // by this role capture. Duplicate34 stops before the diagnostic call.
        bool selected_pending_table_required;
    };
    struct Step {
        Wire::Record record;
        Catalog::Record definition;
        std::vector<Delta> rows; //ALL equal subject WORD rows, in native order.
    };
    struct Projection {
        Scope scope;
        std::array<Row,row_slots> initial_rows,staged_rows;
        std::vector<Step> steps; //Sequential native record order retained.
        bool requires_unchanged_unmodeled_call_roster=false;
        // These data stages do not certify UI/diagnostic callbacks, role
        // rebindings or complete native packet effects. When the flag is set,
        // staged continuation is conditional on the actual owner qualifying
        // the same row/count/role domain across those calls, never on this
        // source's Current alone. Actual owner must supply that qualification.
    };
    static std::shared_ptr<const CnWorldSubjectSkillUpdateSource> read_actual_source(
        CnPrebornSubjectState::Scope,std::span<const std::uint8_t> actual_ui_members,
        std::span<const std::uint8_t> actual_object,Bank,std::shared_ptr<const Catalog>,Current);
    ~CnWorldSubjectSkillUpdateSource();
    bool current() const;
    std::optional<Projection> project_updates(std::span<const Wire::Record>) const;
    const Scope& retained_scope() const noexcept {return scope_;}
private:
    CnWorldSubjectSkillUpdateSource(Scope,std::vector<std::uint8_t>,std::vector<std::uint8_t>,
        std::shared_ptr<const Catalog>,Current);
    struct Operation;
    void owner() const;
    bool observe() const;
    std::optional<std::size_t> retained_definition_offset(std::uint32_t) const;
    const Scope scope_;
    const std::vector<std::uint8_t> object_,bank_;
    const std::shared_ptr<const Catalog> catalog_;
    const Current current_;
    const std::thread::id thread_=std::this_thread::get_id();
    mutable bool operating_=false,terminal_=false;
};
}
