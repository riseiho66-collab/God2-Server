#pragma once
#include "cn/auth/SharedAccountSuccess.h"
#include <utility>

namespace god2::cn {
class SharedWorldPreparation;
// Exact native record assembly plus explicitly selected OWN-server check_key
// generation. Official key generation/entitlement/opaque serialization is not
// inferred from the client; all remaining literal payloads require a real owner.
class SharedIssuedAccountSource {
public:
    enum class KeyPolicy { WindowsSystemCngV1 };
    using Native=SharedAccountSuccess::NativeData;
    using Login=std::shared_ptr<const god2cn::CnAccountWire::Login>;
    class Profile {
    public:
        struct Scope {
            std::uint64_t account_session;
            std::uint32_t verified_account;
            std::uint64_t source_revision;
        };
        // Actual profile/entitlement/catalog/deadline source, observational only.
        // Observe exact outgoing originals, including the independently issued
        // key. Revision must be checked against the real source; no default true.
        using Current=std::function<bool(const Scope&,Native::Check,const Native::Observation&)>;
        // Native1D payloadA4..CB (40 bytes) and0A payload0..15, including all
        // opaque values. No credentials, wire-supplied identity/key or padding
        // defaults are taken from the authenticated04 metadata tail.
        static std::optional<Profile> from_source(std::span<const std::uint8_t> metadata40,
            std::span<const std::uint8_t> billing16,Scope,Current);
        Profile(const Profile&)=delete;
        Profile& operator=(const Profile&)=delete;
        Profile(Profile&&) noexcept=default;
        Profile& operator=(Profile&&)=delete;
    private:
        friend class SharedIssuedAccountSource;
        Profile(std::span<const std::uint8_t>,std::span<const std::uint8_t>,Scope,Current);
        std::array<std::uint8_t,40> metadata_;
        std::array<std::uint8_t,16> billing_;
        Scope scope_;
        Current current_;
    };
    struct Account {
        Native native;
        SharedWorldAdmission::Clock::time_point deadline;
        std::vector<god2cn::CnAccountReplies::CatalogGroup> catalog;
        SharedAccountSelection::SummarySource summaries;
        // Optional native naming needs the same preparation/presence owner;
        // existing composition still checks its storage/catalog/registry.
        std::optional<SharedAccountSelection::NameSources> naming;
        std::shared_ptr<SharedWorldPreparation> naming_preparation;
    };
    struct Prepared {
        Profile profile;
        SharedWorldAdmission::Clock::time_point deadline;
        std::vector<god2cn::CnAccountReplies::CatalogGroup> catalog;
        SharedAccountSelection::SummarySource summaries;
        std::optional<SharedAccountSelection::NameSources> naming;
        std::shared_ptr<SharedWorldPreparation> naming_preparation;
        // Optional actual bound-listener form instead of a manually assembled
        // catalog. Exactly one form; composition rebinds its own host snapshot.
        std::optional<SharedAccountDirectorySource::Plan> directory;
    };
    // No raw password/Login is exposed to profile storage or entitlement rules.
    using Prepare=std::function<std::optional<Prepared>(const Native::Scope&)>;
    using Source=std::function<std::optional<Account>(std::uint64_t,CredentialResult,const Login&)>;
    struct Config {
        KeyPolicy key_policy;
        Prepare prepare;
        Config(KeyPolicy policy,Prepare source):key_policy(policy),prepare(std::move(source)) {}
    };
    // Construct/call on the serial game owner. Same source state across copies;
    // consumes a verified connection once. No default/profile/key fallback.
    static Source create(Config);
};
}
