#pragma once
#include "cn/world/CnPrebornSubjectState.h"
#include "cn/assets/CnNativeSkillCatalog.h"
#include <memory>
#include <thread>

namespace god2cn {
// Optional captured WORLD selected-row primary list, against the actual owned
// complete skill bank. No native process access, generated pointer, auxiliary
// list substitution, common actor ID, skill ownership or cast authority.
class CnWorldPrimarySkillSource final {
public:
    using Subject=CnPrebornSubjectState::Snapshot;
    using Catalog=CnNativeSkillCatalog;
    struct Scope {
        CnPrebornSubjectState::Scope subject;
        Catalog::Source definitions;
        std::uint32_t actual_selected_row,actual_bank_address;
        bool operator==(const Scope&) const=default;
    };
    struct Bank {std::uint32_t address;std::span<const std::uint8_t> bytes;};
    // Actual same selected-row/bank/resource lifecycle; pure nonyielding and
    // nonreentrant. A matching bank does not prove the initial list's writer.
    using Current=std::function<bool(const Scope&)>;
    struct Entry {
        CnPrebornSubjectState::SkillReference reference;
        Catalog::Record definition;
    };
    struct PrimaryOrdinal {
        // Native4D2B50 compares zeroextended record BYTE1/BYTE0 against the
        // complete DWORD operands. Values outside BYTE range do not match.
        std::uint32_t kind_operand,id_operand;
        // Engaged result with no ordinal is qualified native -1, not stale
        // evidence. First physical duplicate wins, irrespective of flags.
        std::optional<std::uint8_t> first_ordinal;
        bool operator==(const PrimaryOrdinal&) const=default;
    };
    struct PrimaryGate {
        PrimaryOrdinal lookup;
        struct Operands {
            std::uint32_t actual_definition_pointer;
            std::uint8_t native_byte67;
            std::uint16_t native_unsigned_word42;
            std::uint32_t native_inline_unsigned_counter64;
            bool operator==(const Operands&) const=default;
        };
        // Retained raw values, not invented MP/cost/permission semantics.
        // Native4D3B60 reads WORD42/counter64 only after nonzero BYTE67.
        std::optional<Operands> first_definition;
        bool native_predicate;
        bool operator==(const PrimaryGate&) const=default;
    };
    static std::shared_ptr<const CnWorldPrimarySkillSource> read_actual_source(
        const Subject&,Bank,std::shared_ptr<const Catalog>,Current);
    ~CnWorldPrimarySkillSource();
    bool current() const;
    // Selected-row projection only. No initial writer, actual caller mode,
    // downstream4D3B60 gate, cast authority or server learned-skill grant.
    // Null outer result means current qualification failed; never -1 success.
    std::optional<PrimaryOrdinal> find_actual_primary_ordinal(
        std::uint32_t kind_operand,std::uint32_t id_operand) const;
    // Exact4D2B50 ->4D3B60 first-match projection only, not the general gate
    // for arbitrary ordinal. Native gate itself lacks count/role/Current
    // bounds; this source independently qualifies its owned row/bank first.
    // Qualified -1 becomes false, never a search for a later duplicate.
    std::optional<PrimaryGate> project_actual_first_primary_gate(
        std::uint32_t kind_operand,std::uint32_t id_operand) const;
    bool matches_subject(const Subject&) const; //Complete retained identity/bytes only, no observer.
    const Subject& retained_subject() const noexcept {return subject_;}
    const Scope& retained_scope() const noexcept {return scope_;}
    const std::vector<Entry>& retained_entries() const noexcept {return entries_;}
    std::span<const std::uint8_t> retained_bank_bytes() const noexcept {return bank_;}
private:
    CnWorldPrimarySkillSource(Subject,Scope,std::vector<std::uint8_t>,std::shared_ptr<const Catalog>,Current);
    struct Operation;
    bool observe() const;
    PrimaryOrdinal retained_first_ordinal(std::uint32_t,std::uint32_t) const;
    void owner() const;
    const Subject subject_;
    const Scope scope_;
    const std::vector<std::uint8_t> bank_;
    const std::shared_ptr<const Catalog> catalog_;
    const Current current_;
    std::vector<Entry> entries_;
    const std::thread::id thread_=std::this_thread::get_id();
    mutable bool operating_=false,terminal_=false;
};
}
