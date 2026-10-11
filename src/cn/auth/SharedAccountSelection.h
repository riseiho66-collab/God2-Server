#pragma once
#include "cn/net/SharedCredentialConnection.h"
#include "cn/protocol/CnAccountReplies.h"
#include "cn/protocol/CnSelectionNameSubmission.h"
#include "cn/auth/CnSelectionNameProjection.h"
#include "db/RecoveredCharacterRepository.h"
#include "auth/SharedCharacterNameReplacement.h"
#include <functional>
#include <optional>
#include <string>
#include <vector>

namespace god2::cn {
// Post-success Account ingress. Native00481640 sends A6(group,server) and
// consumes75-byte07;0047D1C0 routes each active row through the selected
// group's/server's catalog06 byte0. This is a partial source controller:
// Application hosting and native1D/0A success/data qualification remain open.
class SharedAccountSelection:public std::enable_shared_from_this<SharedAccountSelection> {
public:
    using Admission=SharedWorldAdmission;
    using Connection=SharedCredentialConnection;
    class NativeSummary {
    public:
        struct Scope {
            std::uint64_t account;
            Admission::Target target;
            bool operator==(const Scope&) const=default;
        };
        enum class Check {Prepared,BeforePublish,QueueAccepted,NameSubmission};
        // Observe the actual native issuer/visibility state; no mutation, yield,
        // event pumping or borrowed source captures. Storage identity alone
        // does not recover the native07 flags, opaque bytes or row mapping.
        using Current=std::function<bool(const Scope&,Check)>;
        // Complete server-owned native07, INCLUDING flags/opaque/inactive bytes.
        // Never a client claim, zero template, TW raw row or CUSTOM-0003 projection.
        // Identity mapping comes from authoritative storage, never a name join.
        // Snapshot is the ENTIRE common account row set used by this issuer;
        // character_ids separately preserves the active native07 row order.
        static std::optional<NativeSummary> from_native(Scope,god2cn::Bytes,
            std::vector<std::uint64_t> character_ids,std::vector<RecoveredCharacter> account_snapshot,Current);
        NativeSummary(const NativeSummary&)=delete;
        NativeSummary& operator=(const NativeSummary&)=delete;
        NativeSummary(NativeSummary&&)=default;
        NativeSummary& operator=(NativeSummary&&)=default;
    private:
        friend class SharedAccountSelection;
        friend class SharedSelectedCharacterLocationSource;
        NativeSummary(Scope,god2cn::Bytes,std::vector<std::uint64_t>,std::vector<RecoveredCharacter>,Current);
        Scope scope_;
        god2cn::Bytes record_;
        std::vector<std::uint64_t> character_ids_;
        std::vector<RecoveredCharacter> account_snapshot_;
        Current current_;
    };
    // Required data owner; no default/fallback issuer. A missing snapshot is an
    // unresolved source contract, not an empty-account successful response.
    using SummarySource=std::function<std::optional<NativeSummary>(
        std::uint64_t account,Admission::Target)>;
    // Identity only, from this controller's actually published full07 and
    // complete common root snapshot. No permission/rule/reply/mutation owner
    // is supplied by a D3 request or its submitted name. Host keeps repository
    // alive and supplies the actual observing account name-operation phase.
    class NameIdentity {
    public:
        std::uint64_t account() const noexcept {return account_;}
        std::uint64_t character() const noexcept {return character_;}
        std::uint16_t native_row_ordinal() const noexcept {return ordinal_;}
        std::vector<RecoveredCharacter> expected_roots() const;
        // Full original-root proof before mutation. After staged replacement,
        // use actual operation-owner staged-root/lease checks at BeforeCommit;
        // this intentionally cannot certify the changed roots as the old07.
        bool current() const;
    private:
        friend class SharedAccountSelection;
        NameIdentity(std::weak_ptr<SharedAccountSelection>,std::shared_ptr<const NativeSummary>,
            Admission::AccountOffer,std::uint64_t account,std::uint64_t character,std::uint16_t ordinal,
            std::function<bool()> actual_phase);
        std::weak_ptr<SharedAccountSelection> controller_;
        std::shared_ptr<const NativeSummary> summary_;
        Admission::AccountOffer offer_;
        std::uint64_t account_,character_;
        std::uint16_t ordinal_;
        std::function<bool()> phase_;
    };
    std::optional<NameIdentity> resolve_name_submission(const god2cn::CnSelectionNameSubmission&,
        std::function<bool()> actual_phase);
    class NameAttempt {
        friend class SharedAccountSelection;
        NameAttempt()=default;
    };
    struct NameScope {
        std::uint64_t account,account_session,character;
        Admission::Target target;
        std::uint16_t native_row_ordinal;
        std::shared_ptr<const NameAttempt> attempt;
        bool operator==(const NameScope&) const=default;
    };
    enum class NameCheck {BeforeReplace,BeforeCommit,BeforePublish,QueueAccepted};
    class NameDecision {
    public:
        // Observe actual native name rules/equivalence/unique scope/replay and
        // operation lease. BeforeCommit sees staged NEW common roots; after
        // COMMIT checks cannot require membership in the invalidated old07.
        // No writes, yields, events, nested SQL or borrowed supplier captures.
        using Current=std::function<bool(const NameScope&,NameCheck)>;
        static std::optional<NameDecision> from_native_success(NameScope,
            CnSelectionNameProjection,NativeSummary refreshed07,Current);
        // Complete native1E, including its actual source-provided selector.
        // Formatter text is not a rule authorizing a chosen error value.
        static std::optional<NameDecision> from_native_failure(NameScope,god2cn::Bytes complete1e,Current);
        NameDecision(const NameDecision&)=delete;
        NameDecision& operator=(const NameDecision&)=delete;
        NameDecision(NameDecision&&)=default;
        NameDecision& operator=(NameDecision&&)=default;
    private:
        friend class SharedAccountSelection;
        NameDecision(NameScope,std::optional<CnSelectionNameProjection>,
            std::shared_ptr<const NativeSummary>,god2cn::Bytes,Current);
        bool current(const NameScope&,NameCheck) const;
        NameScope scope_;
        std::optional<CnSelectionNameProjection> candidate_;
        std::shared_ptr<const NativeSummary> summary_;
        god2cn::Bytes failure_;
        Current current_;
    };
    struct NameSources {
        SqliteRecoveredCharacterRepository* characters=nullptr;
        std::shared_ptr<const SharedCharacterRemovalPresence> presence;
        // Actual authenticated account name-prompt phase, observing only.
        std::function<bool()> current_phase;
        // Prepare explicit common name + complete native result BEFORE SQL.
        // raw request bytes stay identity/encoding-preserved; no credentials.
        std::function<std::optional<NameDecision>(const NameScope&,
            const god2cn::CnSelectionNameSubmission&,const std::vector<RecoveredCharacter>&)> prepare;
        explicit operator bool() const noexcept {return characters && presence && current_phase && prepare;}
    };
    // Once, from the actual account host, using the SAME common repository and
    // actual occupancy registries. No provider/default is manufactured here.
    bool install_name_sources(NameSources);
    static std::shared_ptr<SharedAccountSelection> attach(
        const std::shared_ptr<Connection>&,std::shared_ptr<Admission>,
        Admission::Grant,std::uint64_t account_session,std::string authenticated_account_echo,RecoveredCharacterRepository&,
        std::vector<god2cn::CnAccountReplies::CatalogGroup>,SummarySource,
        Admission::Clock::time_point now);
private:
    SharedAccountSelection(std::shared_ptr<Admission>,Admission::Grant,
        std::uint64_t,std::string,RecoveredCharacterRepository&,
        std::vector<god2cn::CnAccountReplies::CatalogGroup>,SummarySource);
    void receive(god2cn::Bytes,Connection::Transport::Completion);
    const god2cn::CnAccountReplies::CatalogGroup* catalog_group(Admission::Target) const;
    bool snapshot_current(const NativeSummary&);
    bool qualify(Admission::Target,const NativeSummary&,NativeSummary::Check);
    bool name_identity_current(const NameIdentity&);
    std::vector<RecoveredCharacter> name_identity_roots(const NameIdentity&) const;
    void receive_name(god2cn::Bytes,Connection::Transport::Completion);
    bool name_operation_current(const NameScope&,const std::optional<Admission::QueuedSelection>&);
    bool name_roots_current(const std::vector<RecoveredCharacter>&);
    std::thread::id thread_=std::this_thread::get_id();
    std::weak_ptr<Connection> connection_;
    std::shared_ptr<Admission> admission_;
    Admission::Grant grant_;
    std::uint64_t account_session_;
    std::string account_echo_; // Exact authenticated native bytes; no conversion.
    // Same owner/IDs used by Application's live TW recovered-character route.
    // Never alias IDs from the independent legacy skeleton characters table.
    RecoveredCharacterRepository& characters_;
    std::vector<god2cn::CnAccountReplies::CatalogGroup> catalog_;
    SummarySource source_;
    bool selection_queue_pending_=false;
    // Aliases the immutable source retained through actual queue publication.
    // No copy/projection from D3 or common40-byte profile can replace this07.
    std::shared_ptr<const NativeSummary> published_summary_;
    std::optional<Admission::QueuedSelection> published_ticket_;
    std::optional<NameSources> name_sources_;
    std::shared_ptr<const NameScope> active_name_;
};
}
