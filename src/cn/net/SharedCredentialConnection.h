#pragma once
#include "cn/auth/SharedCredentialStage.h"
#include "auth/SharedWorldAdmission.h"
#include <thread>

namespace god2::cn {
// Per-connection CN raw-UI ingress bound to the shared game's executor/storage.
// No listener or default success controller: Application must supply the real
// next account/world controller, own this object, and close it before shutdown.
class SharedCredentialConnection:public std::enable_shared_from_this<SharedCredentialConnection> {
public:
    using Transport=god2cn::CnTransportSession;
    using Ingress=Transport::OnLogical;
    using Verified=std::function<void(std::shared_ptr<SharedCredentialConnection>,CredentialResult,
        std::shared_ptr<const god2cn::CnAccountWire::Login>,Transport::Completion)>;
    static std::shared_ptr<SharedCredentialConnection> create(
        asio::ip::tcp::socket,asio::any_io_executor game,std::array<std::uint8_t,16> seed,
        Transport::Role,std::shared_ptr<const god2cn::CnClientGroupConfiguration>,
        SharedAccountVerifier&,Verified,std::function<void()> closed);
    ~SharedCredentialConnection();
    void start();
    void close();
    void send(god2cn::Bytes);
    void send_batch(std::vector<god2cn::Bytes>,Transport::Completion queued);
    void send_account_batch_with_publication(std::vector<god2cn::Bytes>,std::function<bool()> publish,
        Transport::Completion queued);
    // Actual world-phase owner supplies observing qualification/publication.
    // Same verified account/world session and admission are checked around it;
    // held native bytes leave only after publication, not queue completion.
    void send_world_batch_with_publication(std::vector<god2cn::Bytes>,std::function<bool()> publish,
        Transport::Completion queued);
    // Explicit mutation owner, separate from observing publication above.
    // Native encoding/capacity/callback preparation succeeds behind the
    // transport barrier BEFORE commit runs on the serial game executor.
    // Caller must recheck its exact operation/storage at this asynchronous
    // boundary and perform its own synchronous transaction without yielding.
    // Same world ticket surrounds commit; true releases the held reply.
    // Post-COMMIT executor/write failures still require durable recovery.
    void send_world_batch_with_commit(std::vector<god2cn::Bytes>,std::function<bool()> commit,
        Transport::Completion queued);
    // Drain already queued native account replies for a real terminal0A.
    // Adds no0A reply; completion is local write/close, not client acceptance.
    void drain_account_replies_and_close(Transport::Completion written);
    // Actual pre-world terminal owner only, with a complete native03 supplied
    // by its real source. Preserves both opaque bytes, queues through native
    // framing, then drains writes before this connection's existing cleanup.
    // No inferred reason/save policy or03 issuer; written is local TCP only.
    // The actual phase/operation owner must hold its ingress suspended and
    // supply a current-owner predicate through queue acceptance. Role/account
    // identity alone does not authorize this terminal reply.
    void close_after_native_world_reply(god2cn::Bytes native03,
        std::function<bool()> current_terminal_owner,Transport::Completion written);
    // Game thread only, once, from the authoritative Verified continuation.
    // Account role only, with a real issued grant and server connection ID.
    // Caller must prepare native success/selection controller before releasing
    // the suspended read. No generic unbound world/account ingress is allowed.
    bool install_account_ingress(std::shared_ptr<SharedWorldAdmission>,
                                 const SharedWorldAdmission::Grant&,std::uint64_t account_session,
                                 Ingress,SharedWorldAdmission::Clock::time_point now);
    // After actual whole-success queue acceptance only. Until this exact
    // connection/grant is confirmed, transport close revokes its unpublished
    // grant before detach; a published selected handoff keeps native lifetime.
    bool confirm_account_success_queue(const SharedWorldAdmission::Grant&,
                                       std::uint64_t account_session,SharedWorldAdmission::Clock::time_point now);
    // Read-only exact account grant after held success publication. Does not
    // reconfirm/clear another pending grant or rerun an obsolete issuer plan.
    bool account_success_current(const SharedWorldAdmission::Grant&,
                                 std::uint64_t account_session,SharedWorldAdmission::Clock::time_point now) const;
    // Required qualified world-success controller and server-owned endpoint
    // identity; this method does not generate1F or select a character.
    // world_session must be a lifetime-unique server connection ID.
    bool install_world_ingress(std::shared_ptr<SharedWorldAdmission>,std::uint64_t world_session,
                               SharedWorldAdmission::Target endpoint,Ingress,
                               SharedWorldAdmission::Clock::time_point now);
    // For the required later world-selection controller. Only a committed,
    // current world's ticket can consult the shared IDs offered at AccountA6.
    // Does not infer an ID from native slot/name or replace current ownership.
    bool world_character_offered(std::uint64_t character) const;
    std::optional<SharedWorldAdmission::OfferSource> world_offer_source() const;
    std::uint64_t world_session_id() const;
    bool world_admission_current() const;
    // One actual world owner's generation-qualified release. Transport owns
    // cleanup independently of this wrapper, including after wrapper expiry.
    bool install_world_cleanup(std::function<void()>);
    // Serial game-owner identity, obtained from common credential verification.
    // Returns0 while unverified/closing. Claimed wire account IDs are separate.
    std::uint32_t verified_account_id() const;
    // Exact login snapshot passed to this connection's Verified continuation.
    // Pointer identity prevents a caller supplying another request's echo.
    // Weak ownership does not extend credential retention after continuation.
    bool owns_verified_login(const std::shared_ptr<const god2cn::CnAccountWire::Login>&) const;
    // Exact verifier-issued token for this original suspended login only.
    // Connection holds it weakly; the account/world publication owns bounded
    // retention and rechecks before success bytes leave, never after release.
    std::shared_ptr<const VerifiedCredentialSource> retain_verified_credentials(
        const std::shared_ptr<const god2cn::CnAccountWire::Login>&) const;
    // The initial world-list owner has no borrowed Login argument. Acquire
    // this same wiping snapshot for its bounded held publication only.
    std::shared_ptr<const god2cn::CnAccountWire::Login> retain_verified_login_for_publication() const;
    bool verified_credentials_current(const std::shared_ptr<const VerifiedCredentialSource>&,
        const std::shared_ptr<const god2cn::CnAccountWire::Login>&) const;
    Transport::Role role() const noexcept {return transport_->role();}
    // Read on the serial game executor, like admitted ingress installation.
    bool closing() const noexcept {return closed_ || transport_->closing();}
private:
    SharedCredentialConnection()=default;
    void owner() const;
    std::thread::id thread_=std::this_thread::get_id();
    std::shared_ptr<Transport> transport_;
    std::shared_ptr<SharedCredentialStage> stage_;
    struct AdmissionCleanup;
    std::shared_ptr<AdmissionCleanup> admission_cleanup_;
    Ingress admitted_;
    std::weak_ptr<const god2cn::CnAccountWire::Login> verified_login_;
    std::weak_ptr<const VerifiedCredentialSource> verified_credential_source_;
    bool established_=false,credentials_verified_=false,closed_=false;
    bool terminal_world_reply_pending_=false;
    std::uint32_t verified_account_=0,claimed_account_=0,claimed_key_=0;
};
}
