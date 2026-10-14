#pragma once
#include "game/SharedTaiwanWorldLifecycle.h"
#include <cstddef>
#include <optional>

namespace god2 {
// Explicit actual scene supplier. This does not construct native scene replies,
// choose peers/resources, replace frozen TW handlers, or grant gameplay rules.
class SharedTaiwanWorldEntered {
public:
    using Lease=SharedWorldPresence::Lease;
    // Exclusive ownership of initial deity records only; no player/pet policy.
    enum class InitialDeityPublisher {External,ApplicationOwned};
    struct Scope {
        Lease lease;
        RecoveredWorldEntryView entry;
        std::uint8_t tail_language;
        // Read the same complete entry carried by the actual lifecycle.
        // By-value projection; no independent cache, DB read or default fields.
        // Scene/Selected/presence qualification remains with the existing path.
        RecoveredWorldEntryView::EntryAppearanceBaseline entry_appearance_baseline() const noexcept {
            return entry.entry_appearance_baseline();
        }
        RecoveredWorldEntryView::EntryResourceSelectors entry_resource_selectors() const noexcept {
            return entry.entry_resource_selectors();
        }
        // The actual scene supplier receives the original entry's label request,
        // never a new default or permission to construct NPC/2A bytes.
        bool npc_id_label_requested() const noexcept {return entry.npc_id_label_requested();}
    };
    enum class Check {AfterSupply,BeforeQueue,BeforePublish,AfterInstall,QueueReleased,LocalPublished,BeforeOutward,OutwardPublish,Completed};
    enum class ReplyDecision {CompleteNativeAggregate,ExplicitNoInitialReply};
    using Current=std::function<bool(Check,const Scope&)>;
    using Install=std::function<bool(Session&,const Scope&)>;
    using Cleanup=std::function<void(const Scope&)>;
    struct Native {
        ReplyDecision decision;
        std::vector<std::uint8_t> logical;
        // Exact ordered boundary offsets of every native6F in the aggregate.
        // The pinned TW record grammar supplies all aggregate boundaries; each
        // encountered6F must equal the corresponding staged81-byte model.
        // Other records remain unchanged. Structural parsing does not qualify
        // their phases/content or the issuer's complete actual peer selection.
        std::vector<std::size_t> incoming_offsets;
        std::vector<cn::SharedActorVisibility::InitialTaiwanActor> incoming;
        std::vector<cn::SharedActorVisibility::OutwardRecipient> outward;
        Current current;
        // Real scene owner installs its authoritative scene and InWorld state,
        // without yield/send/DB writes, inside the held publication boundary.
        Install install;
        Cleanup cleanup;
        Native(ReplyDecision,std::vector<std::uint8_t>,std::vector<std::size_t>,
            std::vector<cn::SharedActorVisibility::InitialTaiwanActor>,
            std::vector<cn::SharedActorVisibility::OutwardRecipient>,Current,Install,Cleanup);
    };
    using Source=std::function<std::optional<Native>(Session&,const Scope&)>;
    // All construction, use, cancellation and destruction run on the serial
    // game owner. Mandatory supplier/Current own the complete actual sets and
    // native material, including explicit empty decisions. Absence rejects.
    // Providers must not retain Session/Scope references, yield or pump events.
    static SharedTaiwanWorldLifecycle::AsyncOwner create(
        std::shared_ptr<SharedWorldPresence>,std::shared_ptr<cn::SharedActorVisibility>,Source,
        TaiwanWorldEntryIdentity identity=TaiwanWorldEntryIdentity::SelectedCharacter,
        InitialDeityPublisher deity_publisher=InitialDeityPublisher::External);
};
}
