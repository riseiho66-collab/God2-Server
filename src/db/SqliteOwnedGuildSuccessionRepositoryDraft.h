#pragma once
// PRIVATE CUSTOM-0083 draft. No factory/Application/registry integration.
// Original governance remains creation history, NEVER a rewritten Leader.
#include "db/SqliteOwnedGuildMembershipRepository.h"
#include <map>
namespace god2 {
class SqliteOwnedGuildSuccessionRepositoryDraft {
public:
    using Original=SqliteOwnedGuildMembershipRepository;
    using Rows=std::vector<std::vector<std::uint8_t>>;
    using TypedLease=std::map<std::string,Rows>;
    struct CurrentOwnership {
        std::uint64_t guild_id{},account_id{},character_id{},membership_revision{},ownership_revision{};
        std::uint8_t account_slot{};
        bool operator==(const CurrentOwnership&) const=default;
    };
    struct SuccessionRecord {
        std::uint64_t guild_id{},revision{},previous_ownership_revision{},guild_revision_before{};
        CurrentOwnership from,to;
        std::uint8_t target_previous_role{};
        bool operator==(const SuccessionRecord&) const=default;
    };
    using History=std::vector<SuccessionRecord>;
    struct EffectiveLeader {
        Original::Guild guild;
        Original::Governance original_creation;
        CurrentOwnership owner;
        StoredGuildMembership owner_membership;
        Original::Identity owner_identity;
        std::vector<GuildRosterMember> roster;
        History succession_history;
        Original::OfficerHistory officer_history;
        TypedLease persistent_guild_lease; // all local opaque typed rows too
        bool operator==(const EffectiveLeader&) const=default;
    };
    struct Transferred {EffectiveLeader before,after;SuccessionRecord appended;};
    explicit SqliteOwnedGuildSuccessionRepositoryDraft(sqlite3*,Original&,bool transfer_enabled=false);
    static std::string schema52_proposal();
    bool succession_present(std::uint64_t guild);
    History history(std::uint64_t guild); // retired rows are audit, not authority
    EffectiveLeader effective_snapshot(std::uint64_t guild); // no nonbattle grant
    EffectiveLeader effective_leader(std::uint64_t account,std::uint64_t character);
    std::vector<Original::Application> applications(std::uint64_t guild);
    std::optional<Original::Guild> find_by_name(const std::string& utf8);
    static std::uint8_t effective_display_role(const EffectiveLeader&,const GuildRosterMember&);
    Transferred transfer(const EffectiveLeader&,const std::vector<Original::Application>&,
        const Original::Identity& target,const StoredGuildMembership&,const Original::Proof&);
    // CUSTOM revised slice: accepted role1 or role2 target, full audience nonbattle,
    // no fee charged and no economy/native cooldown/consent rules claimed.
    // Former owner ordinary1 until an explicitly newer office grant.
    // Proofs MUST be immutable WORLD-only captured actor+target/audience leases,
    // never a fresh governance/panel/role check after the owner has changed.
private:
    sqlite3* db_{};Original& legacy_;bool transfer_enabled_{};
    Original::Governance creation(std::uint64_t guild);
    std::vector<GuildRosterMember> roster(const Original::Guild&);
    void exact_schema52();
};
}
