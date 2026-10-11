#pragma once
#include "cn/world/SharedWorldReady.h"
#include "cn/world/SharedMovement.h"
#include "cn/world/SharedDirectory.h"
#include "cn/world/SharedGenericDirectory.h"
#include "cn/world/SharedSpecialDirectory.h"
#include "cn/world/SharedNativeChat.h"
#include "cn/world/SharedPostWorldExit.h"
#include "cn/world/SharedPrebornChoices.h"
#include "cn/world/SharedPrebornWindowSource.h"
#include "cn/world/SharedSubjectSkillPublication.h"
#include "cn/world/SharedSubjectStatusPublication.h"
#include "cn/world/SharedSubjectRosterPublication.h"
#include "cn/world/SharedNativeSpectatorSource.h"
#include "cn/world/SharedNativeBattleCommandSource.h"
#include "cn/world/SharedNativeBattleCommandGroups.h"
#include "cn/world/SharedNativeBattleCommandData.h"
#include "cn/world/SharedBattleSkillPublication.h"
#include "cn/world/SharedNativeSkillBookUseSource.h"
#include "cn/world/SharedInlineRoleCountersPublication.h"
#include <functional>

namespace god2::cn {
// Bounded ready-world source composition. Uses proven C2S producer sizes,
// never S2C length tables. Unknown requests/variants remain unconnected.
// Required owners supply actual common data/rules/native replies; this factory
// neither implements those suppliers nor activates an Application plan.
class SharedWorldGameplay:public std::enable_shared_from_this<SharedWorldGameplay> {
public:
    using Connection=SharedCredentialConnection;
    using Lease=SharedWorldPresence::Lease;
    struct Sources {
        SharedWorldReady::Bootstrap bootstrap;
        SharedWorldReady::Entered entered;
        // Real ongoing control authority, independently qualified for ready
        // world state. Do not assume initial bootstrap handlers apply here.
        SharedWorldReady::Background background;
        std::shared_ptr<god2cn::CnMovementRules> movement_rules;
        std::shared_ptr<SharedMovement::WorldOwner> movement;
        // Exactly one eager owner or deferred factory is required. Concrete
        // SharedNativeMovementScene::adopt needs ready, so runs in1C publication.
        // The factory must not yield, send output, write saves or pump events.
        std::function<std::shared_ptr<SharedMovement::WorldOwner>()> prepare_movement;
        std::function<void()> release_world; // Actual reservation, tied to transport cleanup.
        std::shared_ptr<SharedDirectory::WorldOwner> directory;
        // Required only for native mode0. No fake mode1 adapters/default data.
        std::shared_ptr<SharedGenericDirectory::WorldOwner> generic_directory;
        std::shared_ptr<SharedSpecialDirectory::WorldOwner> special_directory;
        std::shared_ptr<SharedNativeChat::WorldOwner> chat;
        std::shared_ptr<const ChineseText> chat_text;
        //Explicit real post-game terminal rule/native03 source. Missing keeps
        //the branch unavailable; pre-world mutation source is not substituted.
        SharedPostWorldExit::Source post_world_exit;
        //Real already-issued preborn window/common rule/save/replay authority.
        //Optional: no native81/83 branch is installed without that owner.
        std::shared_ptr<SharedPrebornChoices::WorldOwner> preborn_choices;
        //Alternative concrete window lifecycle, with required actual issuer
        //and operation callbacks. Bind only; publish from a qualified event.
        //Exactly one preborn source may be selected, never competing owners.
        std::shared_ptr<SharedPrebornWindowSource> preborn_windows;
        //Optional post-commit WORLD34/35 issuer. Same actual ready lease, no
        //startup/default output. Common rule/save/replay owner must configure it.
        std::shared_ptr<SharedSubjectSkillPublication> subject_skills;
        //Optional actual committed WORLD31 issuer, same ready lease. No
        //startup output or inferred same-opcode C2S31 response.
        std::shared_ptr<SharedSubjectStatusPublication> subject_status;
        // Optional real committed inline-role WORLD24 event issuer. The
        // seventeen-byte record has no subject ID: the actual common owner
        // must qualify this ready recipient, raw values/save/replay/order.
        // Independent of selected-roster31/34/35 and of ready1F/C25 requests.
        std::shared_ptr<SharedInlineRoleCountersPublication> inline_role_counters;
        //Alternative single actual event owner for ordered30/31/34/35. Select
        //this or the separate status/skill publishers, never competing issuers.
        std::shared_ptr<SharedSubjectRosterPublication> subject_roster;
        // Optional shared same-presence native endpoint registry. Ready binds
        // only after complete initial/outward publication; Chat receives this
        // exact pointer and may use only explicitly selected real transports.
        std::shared_ptr<SharedNativeWorldTransports> world_transports;
        // Explicit actual native6E owner only. No default battle admission,
        // target namespace or same-opcode reply. Sources must share this exact
        // presence/transport/publication incarnation before selection.
        std::shared_ptr<SharedNativeSpectatorSource::WorldOwner> spectator;
        SharedNativeSpectatorSource::Budgets spectator_budgets{};
        std::shared_ptr<SharedNativeSpectatorPublication> spectator_publication;
        std::shared_ptr<SharedNativeSpectatorTargets> spectator_targets;
        std::shared_ptr<SharedNativeSpectatorSource::CloseOwner> spectator_close_owner;
        // Optional actual CN C2S35 authority. This is independent of WORLD35
        // skill publication, C56 world skills and TW CUSTOM battle owners.
        // No default grant, battle actor, command success or settlement rules.
        std::shared_ptr<SharedNativeBattleCommandSource::WorldOwner> battle_commands;
        SharedNativeBattleCommandSource::Budgets battle_command_budgets{};
        // Alternative actual command-group authority. Native continuation and
        // once-per-group settlement remain explicit authority decisions.
        // Select this or the direct owner; no default battle rules or budgets.
        std::shared_ptr<SharedNativeBattleCommandGroups::Authority> grouped_battle_commands;
        SharedNativeBattleCommandGroups::Budgets battle_command_group_budgets{};
        // Alternative actual shared CN definitions/inventory data wrapper.
        // Exactly one direct, grouped or data authority is selected. Data
        // existence is independent of learned/custody/cost/native permissions.
        std::optional<SharedNativeBattleCommandData::Configuration> battle_command_data;
        // Optional actual POST-COMMIT battle87 publisher. It uses the same
        // host/registry/catalog and original ready lease. Binding emits no
        // skills; actual learned/battle/context/save/replay owner is required.
        std::shared_ptr<SharedBattleSkillPublication> battle_skill_publication;
        // Optional actual ready-world C25 SKB owner. Exact pinned book data
        // supplies no learning or item custody. The owner must supply those
        // rules, atomic save/debit/event evidence and full native replies.
        std::shared_ptr<const CnNativeSkillBookBindings> skill_book_source;
        // Already-qualified actual same-store386 raw source binder. Composition
        // performs pointer checks only; each ready request rechecks exact rows
        // behind the real current store/lifetime fence before owner execution.
        std::shared_ptr<const CnSharedSkillBookSourceCatalog> stored_skill_book_source;
        std::shared_ptr<const CnSharedSkillCatalog> skill_book_catalog;
        std::shared_ptr<SharedNativeSkillBookUseSource::WorldOwner> skill_books;
        SharedNativeSkillBookUseSource::Budgets skill_book_budgets{};
        // Independent ready1F00 owner; never reuse initial login/bootstrap1F
        // or infer a C25 outcome from this conditional native control.
        std::shared_ptr<SharedNativeSkillBookUseSource::ControlOwner> item_control;
    };
    // Call during real world preparation, before initial readiness. Returned
    // ready owner is passed unchanged to install_selected_ingress. Gameplay
    // controllers install inside actual1C publication before held replies leave.
    static std::shared_ptr<SharedWorldReady> compose(const std::shared_ptr<Connection>&,
        std::shared_ptr<SharedWorldPresence>,const Lease&,
        std::shared_ptr<SharedActorVisibility>,Sources);
    ~SharedWorldGameplay();
private:
    enum class Target {Movement,Directory,GenericDirectory,SpecialDirectory,Chat,Background30,Background36,PostWorldExit,PrebornChoices,Spectator,SpectatorClose,BattleCommand,SkillBookUse,ItemControl};
    struct Record {Target target;god2cn::Bytes bytes;};
    struct Batch {
        std::vector<Record> records;
        std::size_t cursor=0;
        bool pumping=false,waiting=false;
        Connection::Transport::Completion done;
    };
    SharedWorldGameplay(const std::shared_ptr<Connection>&,std::shared_ptr<SharedWorldPresence>,
        const Lease&,std::shared_ptr<SharedActorVisibility>,Sources,bool);
    void owner() const;
    bool current() const;
    bool initialize();
    bool split(std::span<const std::uint8_t>,std::vector<Record>&) const;
    void receive(god2cn::Bytes,Connection::Transport::Completion);
    void pump(const std::shared_ptr<Batch>&);
    void dispatch(const Record&,Connection::Transport::Completion);
    void finish(const std::shared_ptr<Batch>&,bool);
    void finish_terminal(const std::shared_ptr<Batch>&,bool);
    std::thread::id thread_=std::this_thread::get_id();
    std::weak_ptr<Connection> connection_;
    std::shared_ptr<SharedWorldPresence> presence_;
    Lease lease_;
    std::shared_ptr<SharedActorVisibility> visibility_;
    Sources sources_; // Own required suppliers while child controllers hold references.
    std::shared_ptr<SharedMovement::WorldOwner> prepared_movement_;
    bool native_mode_,initialized_=false,active_=false;
    Connection::Ingress movement_,directory_,generic_directory_,special_directory_,chat_;
    // Same actual chat child, retained by its initialized ingress. A rejected
    // outer batch invalidates it before requesting transport close (whose
    // request flag is immediately visible, while socket cleanup is deferred).
    // Catching a nested rejection cannot resume the child's queued output.
    std::function<void()> chat_invalidate_;
    // Weak Ready observer, not an owning cycle. Releases only its saved native
    // registry token before this composition tears down common presence.
    std::function<void()> release_native_transport_;
    Connection::Ingress post_world_exit_;
    Connection::Ingress preborn_choices_;
    Connection::Ingress spectator_;
    Connection::Ingress spectator_close_;
    std::function<void()> spectator_invalidate_,spectator_release_;
    Connection::Ingress battle_commands_;
    std::function<void()> battle_command_invalidate_,battle_command_release_;
    std::function<void()> battle_skill_invalidate_,battle_skill_release_;
    std::function<void()> inline_role_invalidate_,inline_role_release_;
    Connection::Ingress skill_books_,item_control_;
    std::function<void()> skill_book_invalidate_,skill_book_release_;
};
}
