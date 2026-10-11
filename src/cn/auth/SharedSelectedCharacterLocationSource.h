#pragma once
#include "cn/auth/SharedAccountDirectorySource.h"
#include "cn/auth/SharedAccountSelection.h"
#include <functional>
#include <span>
#include <utility>

namespace god2::cn {
// Qualified local state0x1A projection from native06 into the selected row.
// Original75-byte07 remains the wire/offer source. No map/scene/default issuer.
class SharedSelectedCharacterLocationSource {
public:
    using Summary=SharedAccountSelection::NativeSummary;
    using Scope=Summary::Scope;
    struct SelectedRow {
        std::uint16_t native_row_ordinal;
        std::uint64_t character;
        bool operator==(const SelectedRow&) const=default;
    };
    struct Location {
        god2cn::CnAccountReplies::Location original;
        std::size_t group_node_ordinal,location_ordinal;
    };
    struct Input {
        Scope scope;
        std::span<const std::uint8_t> native07;
        std::span<const std::uint64_t> ordered_character_ids;
        std::span<const RecoveredCharacter> account_roots;
        std::span<const god2cn::CnAccountReplies::CatalogGroup> catalog;
        Location location;
    };
    struct Observation {
        Input source;
        SelectedRow selected;
        // Separate local result of00445B40 state0x1A only. Never sent07,
        // never stored as a native server-produced snapshot or common map.
        std::span<const std::uint8_t> local_selection07;
    };
    class State1A {
    public:
        // Mandatory real owner checks exact state0x1A, selected row/common ID,
        // account group/server, native source revisions/location and rights at
        // EACH existing stage. Observe only: no mutation/yield/default true.
        using Current=std::function<bool(const Scope&,std::uint64_t,Summary::Check,const Observation&)>;
        static std::optional<State1A> from_source(Scope,std::uint64_t revision,SelectedRow,Current);
        State1A(const State1A&)=delete;
        State1A& operator=(const State1A&)=delete;
        State1A(State1A&&) noexcept=default;
        State1A& operator=(State1A&&)=delete;
    private:
        friend class SharedSelectedCharacterLocationSource;
        State1A(Scope,std::uint64_t,SelectedRow,Current);
        Scope scope_;
        std::uint64_t revision_;
        SelectedRow selected_;
        Current current_;
    };
    // Input borrows only during preparation. Return a retained observing
    // source; do not retain Input spans or infer state/rights from stored07.
    using Prepare=std::function<std::optional<State1A>(const Input&)>;
    struct Config {
        Prepare prepare;
        explicit Config(Prepare actual):prepare(std::move(actual)) {}
    };
    // Bind once to the same verified account and actual qualified directory
    // installed by login composition before SharedAccountSuccess::attach.
    // Existing full summary/Current is mandatory; no competing07 supplier.
    // Retains original issuer, directory and selected-row proof through all
    // selection/name stages. An explicit config has no fallback/default rows.
    // Nested source/current observation or escaping callback exceptions make
    // the entire bound source terminal, including previously retained proofs.
    // A later invocation cannot revive it; a fresh real account bind is needed.
    static SharedAccountSelection::SummarySource bind(std::uint64_t account,
        SharedAccountDirectorySource::Plan,SharedAccountSelection::SummarySource,Config);
};
}
