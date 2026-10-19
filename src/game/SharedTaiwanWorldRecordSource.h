#pragma once
#include "game/SharedTaiwanMovementSource.h"
#include "protocol/RecoveredGuildChat.h"

namespace god2 {
class SharedTaiwanOwnedDeitySkillSource;
// Ordered mixed native world-record source, using the actual same movement
// binding. Typed grammar alone grants no remaining opcode/phase authority.
class SharedTaiwanWorldRecordSource final {
public:
    using Lease=SharedWorldPresence::Lease;
    using Record=RecoveredWorldRecords::Record;
    enum class Kind {Movement,Others,SelectionItem,InventoryMove,NativeSkill,DeitySelection,OwnedGuildChat};
    struct Run {std::size_t offset,count;Kind kind;};
    struct Scope {
        Lease lease;
        RecoveredPosition saved_position;
        SessionState phase;
        std::uint64_t battle_generation;
        std::size_t run_index,completed_records,output_bytes,output_frames;
    };
    enum class Check {BeforeBatch,BeforeRun,AfterRun,BeforeReturn};
    struct Budgets {std::size_t max_records,max_runs,max_output_bytes,max_output_frames;};
    class Reply final {
    public:
        // Actual complete encrypted native envelopes; no decode/repack here.
        static Reply wire(std::vector<std::uint8_t>);
        // Explicit native decision supplied by the real Others handler only.
        static Reply no_reply();
        bool native_no_reply() const noexcept;
        const std::vector<std::uint8_t>& bytes() const noexcept;
        std::vector<std::uint8_t> take_bytes() && noexcept;
    private:
        Reply(bool,std::vector<std::uint8_t>);
        bool no_reply_;
        std::vector<std::uint8_t> bytes_;
    };
    using Others=std::function<std::optional<Reply>(Session&,std::span<const Record>)>;
    struct SelectionBinding {
        std::function<std::optional<Reply>(Session&,const Session::NativeWorldSelectionInput&)> dispatch;
        std::function<void(Session&)> release;
        std::function<void()> invalidate_active;
    };
    struct InventoryMoveBinding {
        std::function<std::optional<Reply>(Session&,const RecoveredInventoryMoveRequest::Request&)> dispatch;
        std::function<void(Session&)> release;
        std::function<void()> invalidate_active;
    };
    struct SkillBinding {
        // One complete ordered C35 command, with raw duplicates retained.
        // Real definition/learned/grant/cost/settlement/reply belong to owner.
        std::function<std::optional<Reply>(Session&,std::span<const TaiwanNativeSkillCommand::WireRecord>)> dispatch;
        std::function<void(Session&)> release;
        std::function<void()> invalidate_active;
    };
    struct DeitySelectionBinding {
        std::function<std::optional<Reply>(Session&,const RecoveredDeitySelection::Request&)> dispatch;
        std::function<void(Session&)> release;
        std::function<void()> invalidate_active;
        std::weak_ptr<SharedTaiwanOwnedDeitySkillSource> source;
    };
    struct GuildChatBinding {
        // Explicit existing owned guild policy; no other chat/control grammar.
        std::function<std::optional<Reply>(Session&,std::span<const RecoveredGuildChat::Request>)> dispatch;
        std::function<void(Session&)> release;
        std::function<void()> invalidate_active;
    };
    struct OtherBinding {
        // This sender's native encrypted output returns in original run order;
        // do not submit it directly ahead of earlier accumulated batch replies.
        Others records;
        std::function<void(Session&)> release;
        // Required propagation into the real remaining handlers. A provider
        // catching a rejected outer facade call must not continue publication.
        std::function<void()> invalidate_active;
        // Installed typed native framing only; grants no battle permission.
        bool spectator6e=false;
        bool spectator_close=false; // Separately installed actual native close owner.
        // Intercept actual original C28 before chat's copied Others segments.
        // No fallback after a typed owner rejects; legacy absent behavior stays.
        std::optional<SelectionBinding> selection_item;
        // Dedicated original-run C24 interception before chat copies Others.
        // This game-only binding is not a private native input receipt.
        std::optional<InventoryMoveBinding> inventory_move;
        std::optional<SkillBinding> native_skills;
        // Actual mandatory Others owner explicitly advertises lossless C56
        // input support. It still supplies Current/action/reply or refusal.
        bool native_world_skill_requests=false;
        std::optional<DeitySelectionBinding> deity_selection={};
        // Actual mandatory Others explicitly advertises raw WORLD81/83 support.
        // Issued window, stage/apply, shared rules/save and reply remain its duty.
        bool native_preborn_requests=false;
        // Independent lossless D5 input; actual mandatory Others owns the
        // issued selection window, validation, save and reply or refusal.
        bool native_skill_selection_requests=false;
        std::optional<GuildChatBinding> guild_chat={};
    };
    // Mandatory real opcode/whole-batch/run-phase qualification. Current is a
    // pure observer; saved position, phase and battle generation are read again
    // after it. AfterRun obtains the real advanced prefix, never a stale pose.
    // Observe original full record/run order and actual encrypted output; no
    // borrowed arguments may be retained, yielded or pumped through callbacks.
    using Current=std::function<bool(Session&,Check,const Scope&,
        std::span<const Record>,std::span<const Run>,std::span<const std::uint8_t>)>;
    struct Binding {
        decltype(Session::RecoveredCharacterHandlers::world_records) records;
        // Exact record bookkeeping and real Others cleanup. Application next
        // cleans movement/resources; no common/controller cleanup is repeated.
        std::function<void(Session&)> release;
        std::function<void()> invalidate_active;
        bool spectator6e=false;
        bool spectator_close=false;
        bool native_selection_input=false;
        bool native_skill_commands=false;
        bool native_world_skill_requests=false; // Separate C56 grammar, never C35 authority.
        std::weak_ptr<SharedTaiwanOwnedDeitySkillSource> deity_selection_source={};
        bool native_preborn_requests=false;
        bool native_skill_selection_requests=false;
        bool app_owned_guild_chat=false;
    };
    static Binding create(std::shared_ptr<SharedWorldPresence>,SharedTaiwanMovementSource::Binding,
        OtherBinding,Current,Budgets,std::size_t actual_session_capacity);
};
}
