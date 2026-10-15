#pragma once
#include "game/SharedTaiwanWorldLifecycle.h"
#include "game/OwnedTaiwanReturnActorSavedSource.h"
#include <cstddef>
#include <optional>

namespace god2 {
// Explicit actual scene supplier. This does not construct native scene replies,
// choose peers/resources, replace frozen TW handlers, or grant gameplay rules.
class SharedTaiwanWorldEntered {
public:
    using Lease=SharedWorldPresence::Lease;
    // External/deity-only defaults; explicit saved player/deity ownership.
    // No pet ownership or native ordering guarantee is implied.
    enum class InitialDeityPublisher {External,ApplicationOwned,ApplicationOwnedPlayerAndDeities};
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
        // LAST: actual entered owner captures the whole ready population plus
        // this exact prepared joining actor before invoking the scene source.
        // Only its held publication can consume the private activation step.
        std::optional<SharedWorldPresence::InitialPopulation> population{};
        // LAST: only the same-Database initial issuer attaches this owned input
        // to the genuine supplier/callback Scope; the Entered base stays empty.
        std::shared_ptr<const OwnedTaiwanReturnActorSavedSource::PopulationInput> actor_input{};
    };
    enum class Check {AfterSupply,BeforeQueue,BeforePublish,AfterInstall,QueueReleased,LocalPublished,BeforeOutward,OutwardPublish,Completed,
        BeforeDeferredOutward,AfterDeferredOutward};
    enum class ReplyDecision {CompleteNativeAggregate,ExplicitNoInitialReply};
    enum class OutwardDecision {Supplied,AfterInitialPublication};
    using Current=std::function<bool(Check,const Scope&)>;
    using Install=std::function<bool(Session&,const Scope&)>;
    using Cleanup=std::function<void(const Scope&)>;
    using OutwardProvider=std::function<std::optional<std::vector<cn::SharedActorVisibility::OutwardRecipient>>(
        Session&,const Scope&)>;
    struct Native {
        ReplyDecision decision;
        // Complete ordered scene aggregate, bounded separately from one frame.
        // Session partitions complete records into native frames and holds the
        // entire cohort before the single real install/publication callback.
        // This never permits record truncation or a partial actor population.
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
        // LAST: the explicit deferred mode owns its immutable callback box.
        // Its vector is produced once after actual install/activation/delivery
        // and initial queue release; nullopt fails, an empty vector is explicit.
        OutwardDecision outward_decision=OutwardDecision::Supplied;
        std::shared_ptr<const OutwardProvider> outward_provider{};
        Native(ReplyDecision,std::vector<std::uint8_t>,std::vector<std::size_t>,
            std::vector<cn::SharedActorVisibility::InitialTaiwanActor>,
            std::vector<cn::SharedActorVisibility::OutwardRecipient>,Current,Install,Cleanup);
        Native(ReplyDecision,std::vector<std::uint8_t>,std::vector<std::size_t>,
            std::vector<cn::SharedActorVisibility::InitialTaiwanActor>,
            OutwardDecision,OutwardProvider,Current,Install,Cleanup);
    };
    using Source=std::function<std::optional<Native>(Session&,const Scope&)>;
    // All construction, use, cancellation and destruction run on the serial
    // game owner. Mandatory supplier/Current own the complete actual sets and
    // native material, including explicit empty decisions. Absence rejects.
    // Providers must not retain Session/Scope references, yield or pump events.
    // CUSTOM-0149 ApplicationOwnedPlayerAndDeities additionally requires the
    // actual Source/Current to qualify that no earlier companion/pet binding
    // or HP-loss side effect precedes the saved player publication, including
    // opaque descendants. The exact overlap check is not that semantic proof.
    static SharedTaiwanWorldLifecycle::AsyncOwner create(
        std::shared_ptr<SharedWorldPresence>,std::shared_ptr<cn::SharedActorVisibility>,Source,
        TaiwanWorldEntryIdentity identity=TaiwanWorldEntryIdentity::SelectedCharacter,
        InitialDeityPublisher deity_publisher=InitialDeityPublisher::External);
};
}
