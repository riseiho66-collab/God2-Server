#pragma once
#include "cn/protocol/CnWorldConsumerRecords.h"
#include "cn/world/CnSubjectPanelOperands.h"
#include <functional>
#include <vector>

namespace god2cn {
class CnWorldConsumerSource {
public:
    struct Scope {
        std::uint32_t actual_world_owner_word,actual_ui_owner_word,actual_related_owner_word;
        std::uint64_t actual_revision;
    };
    using Current=std::function<bool(const Scope&)>;
    using Row31=std::array<std::uint8_t,0x3ec>;
    struct OwnedRowUpdate31 {
        std::uint8_t ordinal;
        std::uint32_t actual_row_word;
        Row31 original_row,projected_row;
        bool any_actual_row_flag_equals_one;
        // Read-only follow-on from the actual WORLD31 projected row. Native
        // UI readiness/current/bonus provenance is the caller's separate scope;
        // this value does not render, grant stats or mutate common state.
        CnSubjectPanelOperands panel_operands(
            std::optional<CnSubjectPanelOperands::InlineUiBonusWords> actual_ui_bonus_words=std::nullopt) const noexcept {
            return CnSubjectPanelOperands::from_actual_row(projected_row,actual_ui_bonus_words);
        }
    };
    class OwnedRows31 {
    public:
        bool current() const;
        // First signedBYTE-to-WORD identity match in the actual active prefix.
        // Full original row retained; no insert/default/stat authority supplied.
        std::optional<OwnedRowUpdate31> project_existing_row(const CnOwnedRowRecord31&) const;
    private:
        friend class CnWorldConsumerSource;
        OwnedRows31(Scope,Current,std::vector<Row31>);
        Scope scope_;
        Current current_;
        std::vector<Row31> rows_;
    };
    struct PanelOperand68 {
        std::int16_t actual_ui_handle,actual_resource_word;
        std::uint16_t native_one_based_index;
        std::optional<std::uint32_t> actual_row_word;
        std::optional<std::array<std::uint8_t,0x8c>> original_resource_row;
        std::uint32_t retained_ui_dword,resource_row_dword4,resource_row_dword10;
        std::int32_t resource_row_signed_dwordC;
        // Negative handle returns before null-row assert/reset/mutation.
        // With valid handle and rejected row, native asserts then returns.
        bool native_handle_qualifies() const noexcept {return actual_ui_handle>=0;}
    };
    class ResourceRows68 {
    public:
        bool current() const;
        // Lookup and write operands only. Actual reset4C4880/4C3800, UI/30
        // resource icon reads and later mutation/publication are not executed.
        std::optional<PanelOperand68> lookup_operand(const CnPanelRecord68&) const;
    private:
        friend class CnWorldConsumerSource;
        ResourceRows68(Scope,Current,std::int16_t,std::int16_t,std::int16_t,
            std::uint32_t,std::vector<std::array<std::uint8_t,0x8c>>);
        Scope scope_;
        Current current_;
        std::int16_t handle_,resource_word_,count_;
        std::uint32_t table_word_;
        std::vector<std::array<std::uint8_t,0x8c>> rows_;
    };
    // UI owner is exactly main+89B26C at these dispatcher callsites.
    // Related31 owner is UI+430A8; its BYTE D4 count/inline D8 rows are real.
    static std::optional<OwnedRows31> read_owned_rows31(Scope,
        std::span<const std::uint8_t> actual_world_bytes,
        std::span<const std::uint8_t> actual_related_bytes,Current);
    // Related68 owner is main+A69F20, not an inferred31 list or game table.
    // Actual signed WORD B2F78 count, WORD B2F76, DWORD B2F7C row-table pointer.
    static std::optional<ResourceRows68> read_resource_rows68(Scope,
        std::span<const std::uint8_t> actual_world_bytes,
        std::span<const std::uint8_t> actual_related_bytes,
        std::uint32_t actual_table_word,std::span<const std::uint8_t> actual_table_bytes,Current);
};
}
