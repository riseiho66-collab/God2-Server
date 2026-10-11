#pragma once
// PRIVATE CUSTOM-0084: actual C++ storage, no Application/Help permission mint.
#include "Succession53ReaderDraft.h"
#include "RelationsRawCodec.h"
#include "LifecycleCore53.h"
namespace god2 {
class RelationsRepositoryDraft {
public:
    using Effective=Succession53ReaderDraft;
    using Raw=native_relation_private::Action;
    using Typed=Effective::TypedLease;
    struct Authority {
        std::uint64_t session{},account{},character{},world_generation{},position_revision{},battle_generation{},publication_epoch{};
        std::uint16_t codepage{};std::uint8_t slot{};
        // Trusted server adapter must supply an actually accepted explicit Help
        // epoch; visible rank3/entry/cache rows cannot create this capability.
        bool explicit_help_accepted{};
        bool operator==(const Authority&)const=default;
    };
    struct Pair {
        std::uint64_t low{},high{},revision{},inviter{};
        std::uint8_t state{};
        std::array<std::uint64_t,6> owners{};
        bool operator==(const Pair&)const=default;
    };
    struct Lease {
        Authority actor;Raw raw;
        Effective::EffectiveLeader low,high;
        std::optional<Pair> pair;
        std::uint64_t catalog_revision{},next_wire_id{};
        Typed whole_typed;
        std::string action;
    };
    struct Committed {Pair before,after;std::uint64_t revision{};std::string action;};
    static void migrate53_private(sqlite3*);
    explicit RelationsRepositoryDraft(sqlite3*,SqliteOwnedGuildMembershipRepository&,bool enabled=false);
    Lease capture(const Authority&,std::span<const std::uint8_t> raw76);
    Committed apply(const Lease&,const SqliteOwnedGuildMembershipRepository::Proof&);
    std::vector<native_relation_private::Row> projection(std::uint64_t guild,bool simplified);
    std::optional<Pair> pair(std::uint64_t first,std::uint64_t second);
    struct View {Effective::EffectiveLeader leader;std::vector<Effective::Original::Application> applications;std::vector<native_relation_private::Row> rows;Typed whole;bool operator==(const View&)const=default;};
    View view(std::uint64_t guild,bool simplified);
    enum class LifecycleKind {Transfer,Disband};
    struct LifecycleLease {
        Authority actor;LifecycleKind kind{};Effective::EffectiveLeader owner;
        std::vector<Effective::Original::Application> applications;
        std::optional<Effective::Original::Identity> target;
        std::optional<StoredGuildMembership> target_join;
        std::vector<Pair> affected_pairs;
        std::vector<Effective::EffectiveLeader> counterpart_owners;
        Typed whole_typed;std::uint64_t catalog_revision{},next_wire_id{};
    };
    struct LifecycleCommitted {LifecycleKind kind;Effective::Original::Guild guild;std::vector<Committed> retirements;std::optional<Effective::Transferred> transfer;};
    struct CreationLease {
        Authority actor;bool native_creation_prompt_accepted{};
        Effective::Original::Identity identity;Effective::Original::Wallet wallet;
        Effective::Original::Policy policy;std::string name;
        std::uint64_t next_guild_id{},next_guild_revision{},catalog_revision{},next_wire_id{};
        std::vector<std::vector<std::uint8_t>> guild_rows;Typed whole_typed;
    };
    struct Created53 {Effective::EffectiveLeader leader;Effective::Original::Wallet wallet;std::uint32_t wire_id;};
    LifecycleLease capture_transfer(const Authority&,const Effective::Original::Identity&,const StoredGuildMembership&);
    LifecycleLease capture_disband(const Authority&);
    LifecycleCommitted apply_lifecycle(const LifecycleLease&,const Effective::Original::Proof&);
    CreationLease capture_create(const Authority&,bool accepted_native_prompt,const std::string&,const Effective::Original::Policy&);
    Created53 create53(const CreationLease&,const Effective::Original::Proof&);
private:
    sqlite3* db_;Effective effective_;Effective::Original& original_;bool enabled_;
    LifecycleLease capture_lifecycle(const Authority&,LifecycleKind);
    void exact();void validate_relations();
    std::pair<std::uint64_t,std::uint64_t> catalog();
    std::uint32_t wire(std::uint64_t);
};
}
