#pragma once
#include "cn/auth/SharedAccountSelection.h"
#include "cn/protocol/CnAccountBilling.h"
#include "cn/protocol/CnIssuedLoginFlags.h"
#include "cn/auth/SharedAccountDirectorySource.h"
#include <functional>
#include <optional>

namespace god2::cn {
// Verified Account04 -> complete native data -> owned shared grant -> ordered
// 1D/catalog/0A -> installedA6 dispatcher. Conditional source only: actual
// native value suppliers and Application hosting remain required/open.
class SharedAccountSuccess {
public:
    using Connection=SharedCredentialConnection;
    using Admission=SharedWorldAdmission;
    class NativeData {
    public:
        struct Scope {
            std::uint64_t account_session;
            std::uint32_t verified_account;
            bool operator==(const Scope&) const=default;
        };
        enum class Check {Prepared,BeforeIssue,BeforePublish};
        struct Observation {
            // Exact originals queued by this owner. Views expire on callback
            // return; never retain, log, translate or expose them to Lua.
            // A full1D contains raw credentials, not a password hash.
            std::span<const std::uint8_t> issued_record,billing_record;
            god2cn::CnAccountBilling billing;
            god2cn::CnIssuedLoginFlags flags;
            // Prepared qualifies only the native1D/0A factory inputs: catalog
            // and deadline are explicitly absent then, never default policy.
            // BeforeIssue/BeforePublish expose the exact ordered04/05/06
            // records queued in this aggregate and the actual grant deadline.
            std::span<const god2cn::Bytes> catalog_records;
            std::optional<Admission::Clock::time_point> grant_deadline;
        };
        // Real native issuer observes this exact connection/account source,
        // entitlements/billing/catalog/key/deadline policy and current lifetime.
        // Non-yielding observation only: no saves/sends/events/default true.
        // Qualify the literal issued records against the real native source,
        // not just matching session/account or a desired client gate outcome.
        using Current=std::function<bool(const Scope&,Check,const Observation&)>;
        // Full205-byte1D and17-byte0A from the authenticated native data owner.
        // No padding defaults, reflected04 tail, password-hash replacement,
        // chosen paytype to bypass local mutex, or provider-flag fabrication.
        static std::optional<NativeData> from_source(god2cn::Bytes issued1d,god2cn::Bytes billing0a,Scope,Current);
        // Same actual host snapshot and exact native catalog source, rechecked
        // before grant issue and behind held publication. No late source veto.
        bool bind_directory_source(SharedAccountDirectorySource::Plan);
        NativeData(const NativeData&)=delete;
        NativeData& operator=(const NativeData&)=delete;
        NativeData(NativeData&&) noexcept=default;
        NativeData& operator=(NativeData&&)=delete;
        ~NativeData();
    private:
        friend class SharedAccountSuccess;
        NativeData(god2cn::Bytes,god2cn::Bytes,Scope,Current);
        god2cn::Bytes issued_,billing_;
        Scope scope_;
        Current current_;
    };
    // Returns an installed but suspended selection owner. The mandatory queued
    // callback releases credential ingress only after the ENTIRE native success
    // sequence has crossed the actual held IO queue publication barrier and its
    // grant is still current. Actual native issuer is rechecked before issue and
    // before publication, not a late obsolete source veto after bytes leave.
    // Every failure calls queued(false); it is not a client-success receipt.
    // Deadline is explicit issuer policy, never recovered from client timing.
    // The complete native1D's ID/key is bound to this independent verification;
    // account04's claimed ID/key never supplies grant authority. Exact echoed
    // account/credential bytes are the currently qualified supplier form;
    // native _stricmp case-changing issuer forms remain open, not normalized.
    static std::shared_ptr<SharedAccountSelection> attach(
        const std::shared_ptr<Connection>&,std::shared_ptr<Admission>,
        std::uint64_t account_session,std::shared_ptr<const god2cn::CnAccountWire::Login> authenticated_request,
        NativeData,Admission::Clock::time_point deadline,RecoveredCharacterRepository&,
        std::vector<god2cn::CnAccountReplies::CatalogGroup>,SharedAccountSelection::SummarySource,
        Admission::Clock::time_point now,Connection::Transport::Completion queued,
        std::optional<SharedAccountSelection::NameSources> naming=std::nullopt);
};
}
