#pragma once
#include "cn/assets/CnNativeSkillBookBindings.h"
#include "cn/world/CnPrebornSubjectState.h"
#include "cn/world/CnWorldPrimarySkillSource.h"

namespace god2::cn {
// Actual native UI predicates -> retained common-operation input facts.
// Facts do not grant learned skills, supply common IDs or replace the source's
// server entitlement/rules/save/replay. No process-memory dependency.
struct CnPrebornSkillChoiceSource {
    using Subject=god2cn::CnPrebornSubjectState::Snapshot;
    using Definitions=std::vector<NativeSkillRecord>;
    using BookBindings=std::vector<CnNativeSkillBookBindings::Binding>;
    struct Entry {
        std::uint16_t raw_word;
        // Request-local equality only. Native5331B0 checks its actual selected
        // UI list; this is not a persisted common replay/ownership check.
        std::optional<std::size_t> earlier_request_duplicate;
        std::optional<std::uint8_t> matched_book_native_12c;
        std::optional<bool> matched_item_in_native_exclusion_ranges;
        // Unknown without optional actual native subject evidence. Membership
        // here describes native534640's list filter, never server authority.
        std::optional<bool> in_supplied_native_filtered_offer;
        // Separate native4D2B50-style projection using this retained word's
        // high/low bytes. Not proof that4DA630 consumed this UI/request word;
        // its signed-WORD mode tables and downstream gate remain distinct.
        std::optional<god2cn::CnWorldPrimarySkillSource::PrimaryOrdinal> supplied_primary_ordinal;
        // Same first lookup plus raw4D3B60 predicate. False does not reject a
        // choice or grant/deny server casting; actual common rules are separate.
        std::optional<god2cn::CnWorldPrimarySkillSource::PrimaryGate> supplied_primary_gate;
    };
    struct Facts {
        std::optional<god2cn::CnPrebornSubjectState::Scope> native_scope;
        std::optional<std::uint16_t> native_inline_role_word;
        std::optional<std::uint8_t> native_family_byte;
        std::optional<std::vector<std::uint16_t>> native_filtered_offer_words;
        // Engaged only from the actual complete owned bank; missing means
        // this stronger source qualification is unknown, not successful.
        // Owned pre-commit values persist into apply/delivery without asking
        // the now-obsolete captured Current after the actual transaction.
        std::optional<god2cn::CnWorldPrimarySkillSource::Scope> native_primary_bank_scope;
        std::optional<std::vector<god2cn::CnWorldPrimarySkillSource::Entry>> native_primary_bank_entries;
        std::vector<Entry> entries;
        // Owning same-registry metadata for actual apply/qualify callbacks.
        // Original raw definitions and native permission facts stay separate;
        // these snapshots survive commit without calling obsolete Current.
        std::vector<SharedSkillDefinition> common_definitions;
    };
    struct Resolved {
        Definitions definitions;
        std::optional<BookBindings> books;
        Facts facts;
    };
    // Resolve actual shared records once, with optional actual SKB source and
    // optional recovery snapshot. Own copies/order/duplicates survive commit.
    static std::optional<Resolved> resolve_actual_selection(
        std::span<const std::uint16_t>,const std::optional<Subject>&,
        const CnSharedSkillCatalog&,const CnNativeSkillBookBindings* optional_books,
        const god2cn::CnWorldPrimarySkillSource* optional_primary=nullptr);
};
}
