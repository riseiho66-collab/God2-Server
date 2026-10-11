#pragma once
#include "db/SqliteGuildRosterRepository.h"
#include "db/SqliteTradeRepository.h"
#include <functional>

namespace god2 {
// CUSTOM-0078: gameplay membership operations, not maintenance admin grants.
// Policy inputs must come from the reviewed gameplay rule. Native roster50 is
// only the technical ceiling; this repository does not choose production costs.
class SqliteOwnedGuildMembershipRepository {
public:
    using Identity=GuildRosterMember; // membership_revision must be zero here.
    using Wallet=SqliteTradeRepository::Wallet;
    struct Guild {
        std::uint64_t id{},revision{};
        std::string name_utf8;
        bool operator==(const Guild&) const=default;
    };
    struct Governance {
        std::uint64_t guild_id{},owner_account{},owner_character{},created_revision{};
        std::uint32_t created_cost{};
        std::uint8_t capacity{};
        bool operator==(const Governance&) const=default;
    };
    struct Policy {std::uint32_t creation_fee{};std::uint8_t minimum_level{},initial_capacity{};};
    struct Leader {
        StoredGuildMembership membership;
        Governance governance;
        Identity identity;
        std::vector<GuildRosterMember> roster;
        bool operator==(const Leader&) const=default;
    };
    struct Application {
        std::uint64_t id{};
        Guild target;
        Identity applicant;
        bool operator==(const Application&) const=default;
    };
    struct Created {Leader leader;Wallet wallet;};
    struct Approved {Leader leader;StoredGuildMembership joined;};
    struct Left {Guild guild;Leader leader;};
    // CUSTOM-0080 founder removal of an ordinary accepted member. The target
    // identity is a read lease, never action authority. No character is deleted.
    struct Kicked {Guild guild;Leader leader;Identity removed;StoredGuildMembership removed_membership;};
    // Both callbacks are mandatory, and execute inside the same SQL transaction.
    // Caller closes over immutable session readiness/scene/projection leases.
    struct Proof {std::function<void()> before_write,after_write;};
    explicit SqliteOwnedGuildMembershipRepository(sqlite3* db);
    static std::string schema(); // Explicit migration only. No implicit installs.
    Identity identity(std::uint64_t account,std::uint64_t character);
    Identity nonmember(std::uint64_t account,std::uint64_t character);
    Guild guild(std::uint64_t id);
    std::optional<Guild> find_by_name(const std::string& name_utf8);
    Governance governance(std::uint64_t guild);
    // Presence only, not authority: corrupt governance still counts as present
    // so callers cannot fall back to legacy maintenance-only permissions.
    bool player_created(std::uint64_t guild_id);
    Leader leader(std::uint64_t account,std::uint64_t character);
    // Read-only founder/governance/complete-roster lease. Identical SQL identity
    // qualification to leader(), without founder battle readiness. This is not
    // officer/leader action authority; approve/reject still recheck leader().
    Leader governance_snapshot(std::uint64_t account,std::uint64_t character);
    std::optional<Application> pending(std::uint64_t account,std::uint64_t character);
    std::vector<Application> applications(std::uint64_t guild_id);
    Created create(const Identity& expected,const Wallet& wallet,const std::string& name,
                   const Policy& policy,const Proof& proof);
    Application apply(const Identity& expected,const Guild& target,const Proof& proof);
    Approved approve(const Leader& expected,const Application& application,const Proof& proof);
    void reject(const Leader& expected,const Application& application,const Proof& proof);
    void cancel(const Identity& expected,const Application& application,const Proof& proof);
    // CUSTOM-0078 authenticated ordinary self-member departure. Caller supplies
    // the complete published native panel SQL lease and paired immutable world
    // proof. Founder departure/disband/officer mutation are not authorized.
    Left member_leave(const Identity& self,const StoredGuildMembership& membership,
                      const Leader& leader,const std::vector<Application>& applications,
                      const Proof& proof);
    // CUSTOM-0080: both founder and target require persisted nonbattle state;
    // caller additionally proves exact authenticated world/readiness leases.
    Kicked member_kick(const Leader& founder,const std::vector<Application>& applications,
                       const Identity& target,const StoredGuildMembership& membership,
                       const Proof& proof);
    // CUSTOM-0081 retained guild retirement; native75 authority is separate.
struct Disbanded {
    Guild retained;
    Leader former_leader;
    std::vector<Application> former_applications;
};
// No original disband economy/name-reuse/battle policy is claimed.
// Every accepted member AND pending applicant must be persisted nonbattle.
// Both immutable proof callbacks additionally qualify all connected audience.
Disbanded disband(const Leader& founder,const std::vector<Application>& applications,
                 const Proof& proof);

// REVIEW DRAFT ONLY. Insert inside SqliteOwnedGuildMembershipRepository public:
// CUSTOM-0082 PROPOSED; register only upon reviewed integration, not yet active.
// Existing readers and stored founder identity stay unchanged.
struct OfficerRow {
    std::uint64_t guild_id{},account_id{},character_id{},membership_revision{},revision{};
    std::uint8_t account_slot{},role{}; // persisted role 1 or 2; NEVER role3/role0
    bool operator==(const OfficerRow&) const=default;
};
using OfficerHistory=std::vector<OfficerRow>;
enum class OfficerAction {Appoint,RemoveOffice};
struct OfficerChanged {Guild guild;Leader leader;OfficerHistory history;};
static std::string officer_schema(); // proposed EXPLICIT migration51, no install here
OfficerHistory officer_history(std::uint64_t guild_id);
// Retained rows for prior joins are audit history, never display/action authority.
static std::uint8_t officer_display_role(const Leader&,const GuildRosterMember&,const OfficerHistory&);
OfficerChanged change_officer(const Leader&,const std::vector<Application>&,
    const OfficerHistory&,const Identity&,const StoredGuildMembership&,OfficerAction,const Proof&);
// Delegates to the frozen nonfounder member_leave transaction with additional
// paired rank-history/G0/G1/G2 proofs. History is retained, membership disappears.
Left officer_leave(const Identity&,const StoredGuildMembership&,const Leader&,
    const std::vector<Application>&,const OfficerHistory&,const Proof&);

private:
    sqlite3* db_;
    std::vector<GuildRosterMember> roster(const Guild& guild);
};
}
