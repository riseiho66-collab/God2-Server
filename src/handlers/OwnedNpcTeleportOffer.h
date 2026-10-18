#pragma once
#include "game/RecoveredPosition.h"
#include "protocol/RecoveredNpcInteraction.h"
#include "protocol/RecoveredQuestAction.h"
#include "protocol/RecoveredQuestClose.h"
#include "protocol/RecoveredTeleport.h"
#include "protocol/RecoveredWorldRecords.h"
#include <chrono>
#include <cstdint>
#include <map>
#include <memory>
#include <optional>
#include <span>
#include <string>
#include <variant>
#include <vector>

namespace god2 {
// CUSTOM-0156: game-executor confined, owned NPC travel offer lifecycle only.
// Empty/disabled definitions grant nothing. No guessed NPC, fee, arrival, DB
// mutation or packet encoding is supplied here. Authority is a private host
// adapter to actual published NPC/scene and condition/cost observations; callers
// must never construct its observations from client packet fields.
class OwnedNpcTeleportOffer final {
public:
    using Clock=std::chrono::steady_clock;
    using Time=Clock::time_point;
    enum class Reason {
        Ok, NoDefinition, DisabledDefinition, IncompleteDefinition,
        InvalidDefinition, DuplicateDefinition, DuplicateNpcBinding,
        AuthorityUnavailable, MenuProjectionUnavailable, Reentered, NoOffer, WrongOwner, WrongNpc,
        NotReady, InBattle, TransferPending, PositionChanged, WorldChanged,
        NpcChanged, PolicyChanged, PolicyDenied, Expired, ClockRollback,
        WrongMenu, WrongContext, ChoiceNotOffered, AlreadyPrepared,
        TokenExhausted, ClockOverflow, Cancelled, Invalidated
    };
    static const char* reason_name(Reason) noexcept;
    template<class T> struct Result {
        Reason reason=Reason::NoOffer;
        std::optional<T> value;
        explicit operator bool() const noexcept {return reason==Reason::Ok && value.has_value();}
    };
    struct Identity {
        std::uint64_t session{},account{},character{};
        bool operator==(const Identity&) const = default;
    };
    struct Npc {
        std::uint32_t instance{}; // Exact published interaction identity, not a model ordinal.
        std::uint16_t catalog_key{},area{},scene{},x{},y{};
        std::uint8_t kind{};
        std::uint64_t generation{};
        bool operator==(const Npc&) const = default;
    };
    struct DialogueMenu {
        std::uint8_t mode=4; // 1/2/3 NPCMission; 4 MultiMessage.
        std::uint16_t text_key{},request{},reply_control{};
        std::uint8_t context{},option_count{};
        bool operator==(const DialogueMenu&) const = default;
    };
    using Menu=std::variant<DialogueMenu,RecoveredTeleport::Menu>;
    struct Choice {
        std::uint16_t wire_value{}; // 85 reply or 99/A9 row ID, never a destination selector.
        std::string route_id;       // Exact separately qualified world-catalog route.
        bool operator==(const Choice&) const = default;
    };
    enum class CostPolicy { Unqualified, ExplicitNoCost, QualifiedResources };
    struct Definition {
        std::string id;
        std::uint64_t revision{},policy_revision{};
        bool enabled=false;
        Npc source; // generation is observed, and must be zero in a static definition.
        Menu menu=DialogueMenu{};
        std::vector<Choice> choices;
        std::chrono::seconds lifetime{}; // No invented default expiration rule.
        std::uint16_t interaction_range{}; // Explicit host policy, not an official radius.
        std::string source_evidence,condition_evidence,cost_evidence;
        CostPolicy cost_policy=CostPolicy::Unqualified;
        bool operator==(const Definition&) const = default;
    };
    struct PolicyState {
        std::uint64_t policy_revision{},readset_revision{};
        // Availability/eligibility observations only. costs_satisfied NEVER
        // means payment has occurred; the caller still needs a joint cost and
        // position transaction before committed().
        bool conditions_satisfied=false,costs_satisfied=false;
        bool operator==(const PolicyState&) const = default;
    };
    struct Observation {
        Identity owner;
        bool ready=false,in_battle=false,transfer_pending=false;
        std::optional<RecoveredPosition> position;
        std::uint64_t world_generation{};
        std::optional<std::uint16_t> actor_identity; // Zero remains a representable native handle.
        // Native86 sends WORD(*[UI+8688C]); its equivalence to a published
        // actor/NPC identity is not assumed. Only an independently qualified
        // private host source may supply this optional cancellation proof.
        std::optional<std::uint16_t> close_source_low_word;
        Npc npc;
        PolicyState policy;
    };
    struct MenuProjection {
        std::vector<std::uint8_t> logical;
        std::string source_evidence;
    };
    class Authority {
    public:
        virtual ~Authority()=default;
        // Return nullopt when any actual publication, source, condition or cost
        // authority is unavailable. This method may observe, never grant travel.
        virtual std::optional<Observation> observe(const Identity&,const Definition&) const=0;
        // The host must supply a separately qualified complete7A projection,
        // including any actual formatting bytes. There is no universal27/28
        // byte dialogue encoder or guessed zero tail in this service.
        virtual std::optional<MenuProjection> project_dialogue(
            const Definition&,const DialogueMenu&,const Observation&) const {return std::nullopt;}
    };
    struct Issued {
        std::uint64_t token{};
        std::string definition_id;
        Menu menu;
        std::vector<std::uint8_t> logical_menu;
    };
    struct Prepared {
        std::uint64_t token{};
        std::string definition_id,route_id;
        RecoveredPosition expected_position;
        Npc issuer;
        std::uint64_t definition_revision{},policy_revision{},world_generation{},npc_generation{},policy_readset_revision{};
        CostPolicy cost_policy=CostPolicy::Unqualified;
        std::string cost_evidence;
        bool operator==(const Prepared&) const = default;
    };

    explicit OwnedNpcTeleportOffer(std::shared_ptr<const Authority> authority={});
    // Whole-candidate validation. Invalid enabled rows retain the previous
    // snapshot; successful replacement revokes old offers. Disabled incomplete
    // rows remain inspectable but can never be claimed or opened.
    Reason install(std::vector<Definition>);
    static Reason definition_status(const Definition&) noexcept;
    bool claims(std::uint64_t session,std::span<const RecoveredWorldRecords::Record>,Time now=Clock::now()) const;
    // Identity-aware overload additionally checks a new37 against the private
    // actual host source. The session-only form claims issued replies only.
    bool claims(const Identity&,std::span<const RecoveredWorldRecords::Record>,Time now=Clock::now());
    Result<Issued> open(const Identity&,const RecoveredNpcInteraction::Request&,Time now=Clock::now());
    Result<Prepared> select_dialogue(const Identity&,const RecoveredQuestAction::Request&,Time now=Clock::now());
    Result<Prepared> select_city(const Identity&,const RecoveredTeleport::Selection&,Time now=Clock::now());
    // Must precede the host's actual joint resource/position transaction.
    // QualifiedResources cannot be committed through a position-only supplier.
    Result<CostPolicy> revalidate(const Identity&,const Prepared&,Time now=Clock::now());
    Reason cancel(const Identity&,const RecoveredQuestClose::Request&,Time now=Clock::now());
    // Call on movement, scene/world-generation replacement, battle or NPC
    // retirement. Select/cancel independently repeat the same host observation.
    Reason observe(const Identity&,Time now=Clock::now());
    bool committed(std::uint64_t session,std::uint64_t token);
    void forget(std::uint64_t session);
    bool has_offer(std::uint64_t session) const noexcept;

private:
    struct Offer {
        Identity owner;
        Observation baseline;
        Definition definition;
        Menu menu;
        Time opened{},expires{};
        std::uint64_t token{};
        std::optional<Prepared> prepared;
    };
    struct Operation;
    static Reason eligible(const Identity&,const Definition&,const Observation&) noexcept;
    Result<Observation> current(const Identity&,const Definition&);
    Reason check(const Identity&,Time);
    Result<Prepared> prepare(const Identity&,std::uint16_t);
    std::shared_ptr<const Authority> authority_;
    std::map<std::string,Definition> definitions_;
    std::map<std::uint64_t,Offer> offers_;
    std::uint64_t next_token_{};
    // Native85/99 WORD correlations cycle; A9 has a fixed special context.
    // Full private tokens distinguish Prepared plans across legitimate opens.
    // Native wire has no nonce: an identical old payload during a fresh valid
    // offer is indistinguishable from a new choice of that same offered row.
    std::uint32_t next_dialogue_request_{},next_city_context_{};
    bool busy_=false,reentered_=false;
};
}
