#pragma once
#include <chrono>
#include <compare>
#include <cstddef>
#include <cstdint>
#include <map>
#include <optional>
#include <set>
#include <thread>
#include <utility>
#include <vector>

namespace god2 {
// Serial game-owner state shared by protocol adapters. This is server
// integration/security policy, not recovered official key generation or TTL.
// The authoritative success controller supplies a key, deadline and real
// destination catalog; this class never invents packet fields or success bytes.
// AccountRepository/password verification remains a separate prerequisite.
class SharedWorldAdmission {
public:
    using Clock=std::chrono::steady_clock;
    enum class Protocol {Taiwan};
    struct Target {
        std::uint16_t group,server;
        bool operator==(const Target&) const=default;
    };
    struct Key {
        Protocol protocol;
        std::uint64_t account;
        std::uint32_t check_key;
        auto operator<=>(const Key&) const=default;
    };
    struct Grant {Key key;std::uint64_t generation;};
    // Exact serial-registry selection queue attempt, never a wire/native key.
    // Registry must outlive the token. Copies share identity, not authority to
    // publish twice; commit consumes the queued stage. A failed release may
    // cancel that exact selected revision until a world has claimed it.
    class QueuedSelection {
    public:
        QueuedSelection(const QueuedSelection&)=default;
        QueuedSelection& operator=(const QueuedSelection&)=default;
    private:
        friend class SharedWorldAdmission;
        QueuedSelection(const SharedWorldAdmission* issuer,Grant grant,std::uint64_t session,std::uint64_t revision)
            :issuer_(issuer),grant_(grant),account_session_(session),offer_revision_(revision) {}
        const SharedWorldAdmission* issuer_;
        Grant grant_;
        std::uint64_t account_session_,offer_revision_;
    };
    struct Ticket {
        Grant grant;
        std::uint64_t world_session,reservation;
    };
    struct OfferSource {
        // Ordered common IDs paired by the actual account-selection adapter.
        // Native bytes are adapter evidence, never independent permissions or
        // gameplay state. Retain all opaque/inactive bytes, no new DB table.
        std::vector<std::uint64_t> character_ids;
        std::vector<std::uint8_t> adapter_record;
    };
    // Read-only identity of one published account selection. An identical
    // later selection still supersedes this revision. Does not reserve a
    // world, authorize a name mutation or consume an operation.
    class AccountOffer {
    public:
        AccountOffer(const AccountOffer&)=default;
        AccountOffer& operator=(const AccountOffer&)=default;
        const OfferSource& source() const noexcept {return source_;}
        Target target() const noexcept {return target_;}
    private:
        friend class SharedWorldAdmission;
        AccountOffer(const SharedWorldAdmission* issuer,Grant grant,std::uint64_t session,
            std::uint64_t revision,Target target,OfferSource source)
            :issuer_(issuer),grant_(grant),account_session_(session),revision_(revision),
             target_(target),source_(std::move(source)) {}
        const SharedWorldAdmission* issuer_;
        Grant grant_;
        std::uint64_t account_session_,revision_;
        Target target_;
        OfferSource source_;
    };
private:
    enum class Stage {Issued,SelectionQueued,Selected,Reserved,WorldOwned};
    struct Entry {
        std::uint64_t generation,account_session,world_session=0,reservation=0;
        std::vector<Target> allowed;
        std::optional<Target> selected;
        std::vector<std::uint64_t> offered_characters;
        std::vector<std::uint8_t> adapter_record;
        Clock::time_point deadline;
        Stage stage=Stage::Issued;
        std::set<std::uint64_t> invalidated_characters{};
        std::uint64_t offer_revision=0;
        bool operator==(const Entry&) const=default;
    };
public:
    // Storage/in-memory integration policy, not native deletion permission.
    // Prepare before the actual transaction; recheck before its COMMIT; apply
    // after successful COMMIT without yielding the serial game owner. All
    // allocation occurs during prepare. No native record is rewritten here.
    // Registry must outlive the plan. Plans are single-use and registry-bound.
    class CharacterOfferInvalidation {
    public:
        CharacterOfferInvalidation(const CharacterOfferInvalidation&)=delete;
        CharacterOfferInvalidation& operator=(const CharacterOfferInvalidation&)=delete;
        CharacterOfferInvalidation(CharacterOfferInvalidation&& other) noexcept
            :issuer_(std::exchange(other.issuer_,nullptr)),
             account_(std::exchange(other.account_,0)),character_(std::exchange(other.character_,0)),
             consumed_(std::exchange(other.consumed_,true)),changes_(std::move(other.changes_)) {}
        CharacterOfferInvalidation& operator=(CharacterOfferInvalidation&& other) noexcept {
            if(this!=&other) {
                issuer_=std::exchange(other.issuer_,nullptr);
                account_=std::exchange(other.account_,0);character_=std::exchange(other.character_,0);
                consumed_=std::exchange(other.consumed_,true);changes_=std::move(other.changes_);
            }
            return *this;
        }
        std::uint64_t account() const noexcept {return account_;}
        std::uint64_t character() const noexcept {return character_;}
        std::size_t affected_grants() const noexcept {return changes_.size();}
    private:
        friend class SharedWorldAdmission;
        CharacterOfferInvalidation()=default;
        struct Change {Key key;Entry before;std::set<std::uint64_t> after_invalidated;};
        const SharedWorldAdmission* issuer_=nullptr;
        std::uint64_t account_=0,character_=0;
        bool consumed_=false;
        std::vector<Change> changes_;
    };
    // No default lifetime/key issuer. Limits are explicit operational budgets;
    // previously issued keys are retained until this registry is destroyed.
    // Cross-process issuance/revocation persistence remains the owner's duty.
    SharedWorldAdmission(std::size_t live_capacity,std::size_t issued_key_capacity);
    SharedWorldAdmission(const SharedWorldAdmission&)=delete;
    SharedWorldAdmission& operator=(const SharedWorldAdmission&)=delete;
    std::optional<Grant> issue(std::uint64_t account_session,Key,
                              std::vector<Target>,Clock::time_point deadline,Clock::time_point now);
    bool account_owned(const Grant&,std::uint64_t account_session,
                       std::uint64_t verified_account,Clock::time_point now);
    bool account_target_allowed(const Grant&,std::uint64_t account_session,Target,Clock::time_point now);
    // Must identify the ORIGINAL queue publication, not mint a new identity
    // from whatever byte-identical selection happens to be current now.
    std::optional<AccountOffer> selected_account_offer(const QueuedSelection&,
        std::uint64_t verified_account,Clock::time_point now) const;
    bool selected_account_offer_current(const AccountOffer&,Clock::time_point now) const;
    // Common IDs from the actual authoritative character owner. Adapter rows,
    // native slot tokens and names are not common character identities.
    // Empty offers allow a no-character account but authorize no character.
    bool select(const Grant&,std::uint64_t account_session,Target,
                std::vector<std::uint64_t> offered_characters,Clock::time_point now,
                std::vector<std::uint8_t> adapter_record={});
    // Same explicit source qualification as select, but reserve is unavailable
    // until actual transport queue acceptance and current-source rechecks.
    // No yields/callbacks between select's allocation and the queued stage.
    std::optional<QueuedSelection> begin_selection_queue(const Grant&,std::uint64_t account_session,
        Target,std::vector<std::uint64_t>,Clock::time_point now,std::vector<std::uint8_t> adapter_record);
    bool queued_selection_current(const QueuedSelection&,Clock::time_point now) const;
    bool commit_selection_queue(const QueuedSelection&,Clock::time_point now);
    bool cancel_selection_queue(const QueuedSelection&);
    // Endpoint is server-owned listener/route identity. Verified account is
    // independently recovered from credentials, never from claimed Key alone.
    std::optional<Ticket> reserve(Key,std::uint64_t verified_account,
                                  std::uint64_t world_session,Target endpoint,Clock::time_point now);
    bool commit(const Ticket&,Clock::time_point now);
    // Scope check only: does not select/activate a character, load gameplay,
    // or replace current repository ownership/revision checks at entry time.
    bool character_offered(const Ticket&,std::uint64_t character) const;
    // Exact committed generation/session/reservation, independently of an
    // offered character snapshot that a real mutation may invalidate.
    bool world_owned(const Ticket&) const;
    // Common character mutation owner supplies actual IDs, not adapter slots,
    // This does not mutate storage, consume its operation token, revoke another
    // active actor, send a reply or recover native deletion rules.
    std::optional<CharacterOfferInvalidation> prepare_character_offer_invalidation(
        std::uint64_t account,std::uint64_t character) const;
    bool character_offer_invalidation_current(const CharacterOfferInvalidation&) const;
    bool apply_character_offer_invalidation(CharacterOfferInvalidation&);
    // Only this currently committed world's generation/reservation may read
    // the source offered at account selection. Missing source stays absent.
    std::optional<OfferSource> offered_source(const Ticket&) const;
    bool cancel_reservation(const Ticket&);
    bool release_world(const Ticket&);
    bool revoke_pending(const Grant&,std::uint64_t account_session);
    // Closing account transport must not silently revoke a selected handoff
    // needed by the distinct world connection. Pending selection becomes
    // unavailable; retained non-world grants remain bounded by their deadlines.
    void detach_account(std::uint64_t account_session);
    void expire(Clock::time_point now);
private:
    void owner() const;
    bool matches(const Entry&,const Ticket&) const;
    std::thread::id thread_=std::this_thread::get_id();
    std::size_t live_capacity_,issued_capacity_;
    std::uint64_t generation_=0,reservation_=0;
    std::map<Key,Entry> entries_;
    std::set<Key> issued_;
};
}
