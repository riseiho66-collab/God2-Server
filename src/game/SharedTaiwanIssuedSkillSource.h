#pragma once
#include "protocol/TaiwanNativePrimarySkillList.h"
#include "game/SharedWorldPresence.h"
#include "net/Session.h"
#include <memory>

namespace god2 {
// Game-owned concrete primary and optional independent secondary issued-list
// observation registry. Only a real
// server publisher may install/advance its actual complete state; no C2S,
// saved learned list or catalog membership calls these mutation APIs.
// A real issuer may publish supported complete update aggregates through the
// concrete native battle write lifecycle. The registry does not choose initial
// lists, grant turns or charge MP. Its actual issuer/actor/grant is mandatory.
class SharedTaiwanIssuedSkillSource final : public std::enable_shared_from_this<SharedTaiwanIssuedSkillSource>,
    public Session::NativeBattleSkillPublicationOwner {
    struct State;
    struct Storage;
    struct PublicationStorage;
public:
    using Model=TaiwanNativePrimarySkillList;
    class Ticket {
    public:
        Ticket(const Ticket&)=default;
        Ticket& operator=(const Ticket&)=default;
        Ticket(Ticket&& other) noexcept:storage_(other.storage_) {}
        Ticket& operator=(Ticket&& other) noexcept {storage_=other.storage_;return *this;}
        const Model& model() const;
        std::uint64_t revision() const;
    private:
        friend class SharedTaiwanIssuedSkillSource;
        explicit Ticket(std::shared_ptr<const Storage> value):storage_(std::move(value)) {}
        std::shared_ptr<const Storage> storage_;
    };
    class Selection {
    public:
        const Model::Lookup& lookup() const noexcept {return lookup_;}
        const Ticket& ticket() const noexcept {return ticket_;}
    private:
        friend class SharedTaiwanIssuedSkillSource;
        Selection(Ticket ticket,Model::Lookup lookup):ticket_(std::move(ticket)),lookup_(std::move(lookup)) {}
        Ticket ticket_;
        Model::Lookup lookup_;
    };
    enum class PublicationStatus {Pending,Written,Failed};
    class Publication {
    public:
        Publication(const Publication&)=default;
        Publication& operator=(const Publication&)=default;
        Publication(Publication&& other) noexcept:storage_(other.storage_) {}
        Publication& operator=(Publication&& other) noexcept {storage_=other.storage_;return *this;}
    private:
        friend class SharedTaiwanIssuedSkillSource;
        explicit Publication(std::shared_ptr<PublicationStorage> value):storage_(std::move(value)) {}
        std::shared_ptr<PublicationStorage> storage_;
    };
    struct PublicationObservation {
        PublicationStatus status;
        // Present only after the transport pending barrier has retired and the
        // exact resulting source ticket is still current. Written is a local
        // socket-write/source observation, never a client processing ACK.
        std::optional<Ticket> current_ticket;
    };
    static std::shared_ptr<SharedTaiwanIssuedSkillSource> create(
        std::shared_ptr<SharedWorldPresence>,const NativeSkillCatalog&,std::size_t actual_session_capacity);
    bool owns_sources(const std::shared_ptr<SharedWorldPresence>&,const NativeSkillCatalog&) const;
    // Actual server-owned primary/auxiliary/control and optional full secondary
    // projection from
    // the publisher; complete main provenance (also for empty models) and all
    // referenced full110-byte rows with recomputed digests are re-read in this
    // registry, including present inactive secondary pointer rows. No synthetic
    // zero state, native addresses or bit15 grants; secondary is never primary.
    std::optional<Ticket> install_from_issued(Session&,Model::Snapshot);
    // Concrete51BB80 primary data-prefix materialization plus the SAME full
    // catalog/ready-lease/private installation path. Real issuer must bind
    // actual initial event/roster/control sources; no ordinary entry caller,
    // client constructor completion, wire write receipt or grant is invented.
    std::optional<Ticket> install_from_initialization_prefix(Session&,Model::InitializationPrefix);
    // Actual observed stable same-roster4A9750 rebuild material -> the real
    // prefix/private install pipeline. Full source tails stay in the Ticket
    // and every present definition is re-read. Not an ordinary admission,
    // S34-to-main shortcut, client processing ACK, learned permission or grant.
    std::optional<Ticket> install_from_roster_rebuild_initialization_prefix(
        Session&,Model::RosterInitializationPrefix);
    // Exact previous private ticket CAS; full replacement for real state
    // changes outside87/38. Own revision is local observation freshness only,
    // not a native nonce, durable event ID, publication receipt or grant epoch.
    std::optional<Ticket> replace_from_issued(Session&,const Ticket&,Model::Snapshot);
    std::optional<Ticket> apply87_from_issued(Session&,const Ticket&,std::span<const std::uint8_t>);
    std::optional<Ticket> apply38_from_issued(Session&,const Ticket&,std::span<const std::uint8_t>);
    // Same exact-ticket observation replacement for the direct86/5 control and
    // actor subset. Retains all17 bytes; no server grant, time, UI rearm, local
    // command consumption or full86 consumer state is inferred from it.
    std::optional<Ticket> apply86_control_from_issued(Session&,const Ticket&,std::span<const std::uint8_t>);
    // Real issuer-observed51C4B0/51C4F0 local clear only. Exact previous
    // private ticket and full source requalification; never synthesize a
    // packet or infer this local event merely because a C2S action arrived.
    std::optional<Ticket> apply_enable_clear_from_issued(Session&,const Ticket&,Model::EnableClear);
    // Complete ordered aggregate of supported87/38/direct86-5 updates from a
    // real issuer, not a C2S-derived grant. Stages the exact previous ticket,
    // blocks source consumers and uses the actual common-battle write path.
    // No user callback is carried into a strand or invoked before its barrier
    // retires. The real game owner observes the private handle on game.
    std::optional<Publication> publish_updates(Session&,const Ticket&,std::span<const std::uint8_t>);
    std::optional<PublicationObservation> observe_publication(Session&,const Publication&);
    std::optional<Selection> select(Session&,std::uint32_t full_operand);
    bool current(Session&,const Selection&);
    void release(Session&);
    void invalidate_active();
private:
    bool before_native_battle_write(Session&,const Session::NativeBattleSkill&) override;
    bool complete_native_battle_write(Session&,const Session::NativeBattleSkill&,bool written) override;
    explicit SharedTaiwanIssuedSkillSource(std::shared_ptr<State> value):state_(std::move(value)) {}
    std::shared_ptr<State> state_;
};
}
