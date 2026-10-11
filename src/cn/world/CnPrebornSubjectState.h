#pragma once
#include "cn/protocol/CnSelectedSubjectUpdate.h"
#include <cstddef>
#include <cstdint>
#include <functional>
#include <optional>
#include <span>
#include <vector>

namespace god2cn {
//Pinned mode0 source: UI+430AC=object, UI+430A8=object+90;
//object+160 and inline-role+D0 are the same selected-entry pointer.
//Reads supplied actual bytes only, never native process memory/pointers.
class CnPrebornSubjectState {
public:
    struct Scope {
        std::uint32_t actual_ui_owner_word,actual_object_word;
        std::uint64_t actual_revision;
        bool operator==(const Scope&) const=default;
    };
    using Current=std::function<bool(const Scope&)>;
    struct SkillReference {
        std::uint32_t actual_native_pointer_word;
        std::uint8_t actual_native_flags;
    };
    struct Selection {
        std::uint32_t actual_entry_pointer_word;
        std::uint16_t actual_native_identifier;
        std::uint8_t native_5b_operand;
        std::vector<SkillReference> skills;
        CnSelectedSubjectUpdate::Row actual_native_row; //All original3EC bytes, not a reconstructed zero row.
        // Actual row+5C BYTE and row+60 DWORD prefix. Preserve stale, duplicate
        // and null pointer words; WORLD30 can clear primary count without
        // clearing this prefix. None is an out-of-view prefix; an engaged
        // empty vector is an actual empty one. No lifecycle/grant is inferred.
        std::optional<std::vector<std::uint32_t>> native_auxiliary_pointers;
        // Only a relationship among captured bytes, NOT proof4D5830 just ran
        // or a battle list, learned/cast permission or common skill identity.
        bool native_auxiliary_matches_flag_projection=false;
        //Pointers/flags are source operands, not common IDs or cast permission.
    };
    class Snapshot {
    public:
        const Scope& scope() const noexcept {return scope_;}
        bool current() const;
        //Retained identity for an actual operation/post-commit observation.
        //These accessors do not make an obsolete snapshot current again.
        std::uint16_t retained_subject_identifier() const noexcept {return subject_identifier_;}
        // Actual WORD at object+90, reached through UI+430A8. Distinct from
        // object+0; preserves the operand used by native534640's family gate.
        std::uint16_t retained_inline_role_word() const noexcept {return inline_role_word_;}
        // Original inline offsets5C/64/60/68, in WORLD24 wire order. Raw
        // unsigned32 source operands, not selected-row2C/30 or HP/MP labels.
        const std::array<std::uint32_t,4>& retained_inline_role_unsigned_counters() const noexcept {return inline_counters_;}
        std::uint8_t retained_list_count() const noexcept {return count_;}
        std::int8_t retained_selected_index() const noexcept {return index_;}
        std::uint32_t retained_selected_pointer() const noexcept {return selected_;}
        std::uint32_t retained_skill_bank_pointer() const noexcept {return bank_;}
        const std::optional<Selection>& retained_selection() const noexcept {return selection_;}
        //Optional qualified native-source handoff, never an operational
        //process-memory requirement or common mutation authority. Invalid/null
        //selection remains absent; a real native null pointer is a consumer no-op.
        std::optional<CnSelectedSubjectUpdate::Projection> project_selected_update(
            const CnSelectedSubjectUpdate&) const;
    private:
        friend class CnPrebornSubjectState;
        Snapshot(Scope,Current,std::uint16_t,std::uint16_t,std::array<std::uint32_t,4>,std::uint8_t,std::int8_t,
            std::uint32_t,std::uint32_t,std::optional<Selection>);
        Scope scope_;
        Current current_;
        std::uint16_t subject_identifier_;
        std::uint16_t inline_role_word_;
        std::array<std::uint32_t,4> inline_counters_;
        std::uint8_t count_;
        std::int8_t index_;
        std::uint32_t selected_,bank_;
        std::optional<Selection> selection_;
    };
    //ui_members is the actual8-byte view starting at UI+430A8.
    //object starts at actual_object_word, owning at least bytes[0,4508).
    //List/memory bounds are captured native layout, not server progression caps.
    static std::optional<Snapshot> read_actual_source(Scope,
        std::span<const std::uint8_t> ui_members,std::span<const std::uint8_t> object,Current);
};
}
