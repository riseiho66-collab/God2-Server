#pragma once
#include "cn/net/SharedCredentialConnection.h"
#include "cn/protocol/CnCharacterSummary.h"
#include "db/RecoveredCharacterRepository.h"
#include "db/NativeMapCatalog.h"
#include "game/RecoveredPosition.h"
#include "cn/world/SharedWorldReady.h"
#include "cn/auth/SharedCharacterDeleteIdentity.h"
#include "cn/auth/SharedPreWorldCloseReply.h"
#include "cn/auth/SharedCharacterCreateOperation.h"
#include "cn/auth/SharedCharacterDeleteOperation.h"
#include <array>
#include <functional>
#include <optional>
#include <span>
#include <string_view>
#include <vector>

namespace god2::cn {
class SharedInitialScene;
// World00 credential continuation -> required complete native1F offer ->1A
// -> current shared owner/offer -> required real world-preparation controller.
// No default world owner or success data. Application/native data providers
// remain open; this conditional source is not a completed playable route.
class SharedWorldSelection:public std::enable_shared_from_this<SharedWorldSelection> {
public:
    using Connection=SharedCredentialConnection;
    using Admission=SharedWorldAdmission;
    struct Binding {
        std::uint8_t enter_slot;
        std::uint64_t character;
    };
    // Required authenticated producer-source snapshots for this session.
    // Native transfer/reconnect1A may use pre1D/UI strings while world00 uses
    // a newer record/cache. Do not manufacture aliases by case folding,
    // conversion or reading the incoming1A. This is integration policy;
    // client alias evidence does not recover official second-auth rules.
    class CredentialAlias {
    public:
        CredentialAlias(std::string_view account,std::string_view credential);
        ~CredentialAlias();
        bool matches(std::string_view account,std::string_view credential) const;
    private:
        std::array<std::uint8_t,16> account_{},credential_{};
    };
    class NativeOffer {
    public:
        enum class Path {Normal,Transfer};
        // Complete07/1F must be from this selected grant's authoritative
        // native data supplier, with explicitly supplied common IDs in07 row
        // order. It must prove1F row identity on transfer; ordinal reuse alone
        // is a client fact, not that proof. No names/profile or DB-ID joins.
        static std::optional<NativeOffer> from_native(Path,
            const god2cn::CnCharacterSummary&,std::vector<std::uint64_t> common_row_ids,
            god2cn::Bytes world_list,std::vector<CredentialAlias>);
    private:
        friend class SharedWorldSelection;
        explicit NativeOffer(Path path):path_(path){}
        Path path_;
        god2cn::Bytes list; // exact125-byte native1F, no07/TW profile template
        // Server-owned, native-qualified slot/common-ID associations for this
        // connection's normal/transfer path. Never infer IDs from names,
        // ordinal, raw124-byte capacity or the client's invalid-slot->0 clamp.
        std::vector<Binding> bindings;
        // Same account A6 source, retained in exact07 row order. Membership
        // alone cannot authorize a supplier swapping two offered common IDs.
        god2cn::Bytes summary_record;
        std::vector<std::uint64_t> source_character_ids;
        std::vector<CredentialAlias> credential_aliases;
    };
    struct Choice {
        std::uint64_t account,character;
        std::uint8_t enter_slot;
        NativeOffer::Path path;
    };
    // Real shared-world owner must prepare actor/storage/rules/bootstrap and
    // provide complete native02/2A plus the actual next dispatcher. This
    // callback gets only qualified IDs, never account/credential bytes.
    using Selected=std::function<void(std::shared_ptr<SharedWorldSelection>,Choice,
                                      Connection::Transport::Completion)>;
    enum class PublicationCheck {BeforePublish,QueueAccepted};
    // Actual preparation/reservation lease, observe only, no yield/writes or
    // event pumping. QueueAccepted runs behind the real native IO barrier.
    using Publication=std::function<bool(PublicationCheck)>;
    // Synchronous actual pre-world operation/rule/reply source, not inferred
    // from0200/0203/0204. It must not retain the passed scope reference. Missing
    // source keeps this branch unavailable; no synthesized03 or blanket ACK.
    using TerminalSource=std::function<std::optional<SharedPreWorldCloseReply>(
        const SharedPreWorldCloseReply::Scope&)>;
    static std::shared_ptr<SharedWorldSelection> attach(
        const std::shared_ptr<Connection>&,std::shared_ptr<Admission>,
        std::uint64_t world_session,Admission::Target,
        RecoveredCharacterRepository&,const NativeMapCatalog&,NativeOffer,Selected,
        Admission::Clock::time_point now,Connection::Transport::Completion queued,
        TerminalSource terminal_source={},SharedCharacterCreateOperation::Sources creation_sources={},
        SharedCharacterDeleteOperation::Sources deletion_sources={});
    // Complete1F/common offer is qualified behind the actual IO barrier;
    // offer state publishes before bytes leave, then local queue completion
    // releases the suspended read without a late obsolete offer check.
    // Only the currently pending, server-selected choice may obtain this
    // connection for real world preparation. Does not install or authorize ready.
    std::shared_ptr<Connection> connection_for_choice(const Choice&,
        const RecoveredCharacterRepository&,const NativeMapCatalog&) const;
    // Identity resolution for the conditional pre-world deletion operation.
    // This value alone never permits/deletes storage or issues a reply.
    // Current full07 row-to-common-ID lineage is independent of1A's slots.
    std::optional<SharedCharacterDeleteIdentity> resolve_deletion_identity(
        std::span<const std::uint8_t> record);
    // Called on the game owner by Selected after actual world preparation.
    // Complete opaque bytes must come from its qualified native data source.
    // Both records are queued in one aggregate,02 before2A; no zero fill.
    // The mandatory initial-ready owner must be bound to this exact connection,
    // actual stored-position lease and2A handle before the replies are queued.
    // Position must be from this character's actual shared preparation, not
    // decoded client claims. Reads the shared NativeMapCatalog now and checks
    // exact source/row bytes; replies must match that reserved location.
    // Previous owner position is required for transfer, absent for normal.
    // CF's same-map bit16 behavior must not be applied to a normal initial2A.
    // Normal selection additionally requires the exact prepared asset snapshot.
    // CF must not reuse normal initial geometry; its lifecycle remains separate.
    // True transfers completion to the publication/send owner; caller keeps1A
    // suspended until queued runs on game. False keeps failure with caller.
    // Required actual preparation predicate is checked before scheduling and
    // behind the IO barrier; exact ready/scene ingress installs only there.
    bool install_selected_ingress(std::uint64_t character,const RecoveredPosition&,
                                  const std::optional<RecoveredPosition>& previous,
                                  god2cn::Bytes status02,
                                  god2cn::Bytes begin2a,const std::shared_ptr<SharedWorldReady>&,
                                  const std::shared_ptr<SharedInitialScene>& normal_scene,
                                  Publication current_preparation,
                                  Connection::Transport::Completion queued);
private:
    SharedWorldSelection(const std::shared_ptr<Connection>&,
        std::shared_ptr<Admission>,
        RecoveredCharacterRepository&,const NativeMapCatalog&,NativeOffer,Selected,TerminalSource,
        SharedCharacterCreateOperation::Sources,SharedCharacterDeleteOperation::Sources);
    void owner() const;
    bool owns(std::uint64_t character) const;
    bool qualify_offer() const;
    bool terminal_scope_current(const SharedPreWorldCloseReply::Scope&) const;
    bool create_scope_current(const SharedCharacterCreateOperation::Scope&) const;
    bool delete_scope_current(const SharedCharacterDeleteOperation::Scope&) const;
    void receive_delete(std::optional<SharedCharacterDeleteIdentity>,Connection::Transport::Completion);
    void receive_create(god2cn::CnCharacterCreate,Connection::Transport::Completion);
    void receive_close(god2cn::CnPreWorldCloseControl,Connection::Transport::Completion);
    void receive(god2cn::Bytes,Connection::Transport::Completion);
    std::thread::id thread_=std::this_thread::get_id();
    std::weak_ptr<Connection> connection_;
    std::shared_ptr<Admission> admission_;
    RecoveredCharacterRepository& characters_;
    const NativeMapCatalog& maps_;
    std::uint64_t account_=0,pending_character_=0;
    NativeOffer offer_;
    Selected selected_;
    TerminalSource terminal_source_;
    SharedCharacterCreateOperation::Sources creation_sources_;
    std::shared_ptr<SharedCharacterCreateOperation> creation_operation_;
    SharedCharacterDeleteOperation::Sources deletion_sources_;
    std::shared_ptr<SharedCharacterDeleteOperation> deletion_operation_;
    Connection::Ingress selected_ingress_;
    std::shared_ptr<SharedWorldReady> selected_ready_;
    std::shared_ptr<SharedInitialScene> normal_scene_; // Retain selected resource/lease snapshot.
    bool started_=false,offer_queued_=false,terminal_started_=false,selected_publication_pending_=false;
};
}
