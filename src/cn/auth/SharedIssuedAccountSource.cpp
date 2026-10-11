#include "cn/auth/SharedIssuedAccountSource.h"
#include <algorithm>
#include <stdexcept>
#include <thread>
#include <utility>

#ifdef _WIN32
#ifndef NOMINMAX
#define NOMINMAX
#endif
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>
#include <bcrypt.h>
#endif

namespace god2::cn {
SharedIssuedAccountSource::Profile::Profile(std::span<const std::uint8_t> metadata,
    std::span<const std::uint8_t> billing,Scope scope,Current current)
    :scope_(scope),current_(std::move(current)) {
    std::copy(metadata.begin(),metadata.end(),metadata_.begin());
    std::copy(billing.begin(),billing.end(),billing_.begin());
}
std::optional<SharedIssuedAccountSource::Profile> SharedIssuedAccountSource::Profile::from_source(
    std::span<const std::uint8_t> metadata,std::span<const std::uint8_t> billing,Scope scope,Current current) {
    if(metadata.size()!=40 || billing.size()!=16 || !scope.account_session ||
       !scope.verified_account || !scope.source_revision || !current)return std::nullopt;
    return Profile(metadata,billing,scope,std::move(current));
}

namespace {
#ifdef _WIN32
std::optional<std::uint32_t> windows_check_key() {
    // Separate4-byte call, never the16-byte transport seed or a derivative.
    std::array<std::uint8_t,4> bytes{};
    const auto status=BCryptGenRandom(nullptr,bytes.data(),static_cast<ULONG>(bytes.size()),
                                     BCRYPT_USE_SYSTEM_PREFERRED_RNG);
    if(!BCRYPT_SUCCESS(status)) {
        SecureZeroMemory(bytes.data(),bytes.size());return std::nullopt;
    }
    std::uint32_t key=0;
    for(unsigned i=0;i<4;++i)key|=std::uint32_t(bytes[i])<<(8*i);
    SecureZeroMemory(bytes.data(),bytes.size());
    return key; // Zero is a possible actual value, not a missing native field.
}
std::uint32_t word32(std::span<const std::uint8_t> bytes,std::size_t offset) {
    std::uint32_t value=0;
    for(unsigned i=0;i<4;++i)value|=std::uint32_t(bytes[offset+i])<<(8*i);
    return value;
}
void append32(god2cn::Bytes& bytes,std::uint32_t value) {
    for(unsigned i=0;i<4;++i)bytes.push_back(static_cast<std::uint8_t>(value>>(8*i)));
}
struct Busy {
    bool& flag;
    explicit Busy(bool& f):flag(f){flag=true;}
    ~Busy(){flag=false;}
};
struct CredentialRecord {
    god2cn::Bytes bytes;
    ~CredentialRecord() {
        volatile std::uint8_t* p=bytes.data();for(std::size_t i=0;i<bytes.size();++i)p[i]=0;
    }
};
#endif
}

SharedIssuedAccountSource::Source SharedIssuedAccountSource::create(Config config) {
    if(config.key_policy!=KeyPolicy::WindowsSystemCngV1 || !config.prepare)
        throw std::invalid_argument("CN issued-account source requires explicit key policy and actual profile source");
#ifdef _WIN32
    struct State {
        const std::thread::id owner=std::this_thread::get_id();
        Prepare prepare;
        std::uint64_t last_session=0;
        bool busy=false;
        explicit State(Prepare p):prepare(std::move(p)) {}
    };
    auto state=std::make_shared<State>(std::move(config.prepare));
    return [state=std::move(state)](std::uint64_t session,CredentialResult verified,const Login& request)
        ->std::optional<Account> {
        if(state->owner!=std::this_thread::get_id())
            throw std::logic_error("CN issued-account source game owner mismatch");
        if(state->busy || !session || session<=state->last_session || !request ||
           verified.outcome!=CredentialOutcome::Verified || !verified.account_id || !verified.source)return std::nullopt;
        // Existing compose_native_login must also bind this token/request to
        // the exact independently verified connection before invoking us.
        state->last_session=session;
        Busy active(state->busy);
        if(!verified.source->current(verified.account_id))return std::nullopt;
        const Native::Scope scope{session,verified.account_id};
        auto prepared=state->prepare(scope);
        if(!prepared)return std::nullopt;
        if(prepared->directory) {
            if(!prepared->catalog.empty() || !prepared->directory->current())return std::nullopt;
            prepared->catalog=prepared->directory->catalog();
        }
        if(!prepared->summaries || prepared->catalog.empty() ||
           prepared->deadline<=SharedWorldAdmission::Clock::now() ||
           prepared->profile.scope_.account_session!=session ||
           prepared->profile.scope_.verified_account!=verified.account_id ||
           !verified.source->current(verified.account_id))return std::nullopt;
        // Keep the supplied directory's own observer through publication, in
        // addition to the composition's independently bound host directory.
        // Allocate this owner before any credential bytes are copied below.
        std::shared_ptr<const SharedAccountDirectorySource::Plan> directory;
        if(prepared->directory)
            directory=std::make_shared<SharedAccountDirectorySource::Plan>(std::move(*prepared->directory));
        auto key=windows_check_key();
        if(!key)return std::nullopt;
        std::shared_ptr<const Profile> profile=std::make_shared<Profile>(std::move(prepared->profile));
        const auto deadline=prepared->deadline;
        Native::Current current=[profile,directory=std::move(directory),
            original=std::weak_ptr<const god2cn::CnAccountWire::Login>(request),
            credentials=verified.source,scope,key=*key,deadline,owner=state->owner](
                const Native::Scope& actual,Native::Check check,const Native::Observation& observation) {
            if(owner!=std::this_thread::get_id())return false;
            if(directory && !directory->current())return false;
            const auto login=original.lock();
            if(actual!=scope || !login || !credentials->current(scope.verified_account) ||
               observation.issued_record.size()!=205 || observation.issued_record[0]!=0x1d ||
               observation.billing_record.size()!=17 || observation.billing_record[0]!=0x0a ||
               word32(observation.issued_record,1+0x9c)!=scope.verified_account ||
               word32(observation.issued_record,1+0xa0)!=key ||
               !std::equal(login->payload.begin(),login->payload.begin()+156,
                           observation.issued_record.begin()+1) ||
               !std::equal(profile->metadata_.begin(),profile->metadata_.end(),
                           observation.issued_record.begin()+1+0xa4) ||
               !std::equal(profile->billing_.begin(),profile->billing_.end(),
                           observation.billing_record.begin()+1))return false;
            if(check==Native::Check::Prepared) {
                if(observation.grant_deadline || !observation.catalog_records.empty())return false;
            } else if(check==Native::Check::BeforeIssue || check==Native::Check::BeforePublish) {
                if(!observation.grant_deadline || *observation.grant_deadline!=deadline ||
                   observation.catalog_records.empty())return false;
                if(directory && !directory->matches(observation.catalog_records))return false;
            } else return false;
            // The real retained owner checks its own revision/entitlement AND
            // literal catalog/deadline. No prepared-source veto after release.
            return profile->current_(profile->scope_,check,observation) &&
                   credentials->current(scope.verified_account) &&
                   (!directory || directory->current());
        };
        // All205 bytes have explicit sources. Echo only the156-byte native
        // credential fields; never echo incoming04's identity/key/metadata.
        // Build Current before copying credentials, so its allocations cannot
        // discard an unwiped temporary record during argument construction.
        CredentialRecord issued;issued.bytes.reserve(205);issued.bytes.push_back(0x1d);
        issued.bytes.insert(issued.bytes.end(),request->payload.begin(),request->payload.begin()+156);
        append32(issued.bytes,verified.account_id);append32(issued.bytes,*key);
        issued.bytes.insert(issued.bytes.end(),profile->metadata_.begin(),profile->metadata_.end());
        god2cn::Bytes billing{0x0a};
        billing.insert(billing.end(),profile->billing_.begin(),profile->billing_.end());
        auto native=Native::from_source(std::move(issued.bytes),std::move(billing),scope,std::move(current));
        if(!native || !verified.source->current(verified.account_id))return std::nullopt;
        return Account{std::move(*native),prepared->deadline,std::move(prepared->catalog),
            std::move(prepared->summaries),std::move(prepared->naming),std::move(prepared->naming_preparation)};
    };
#else
    throw std::runtime_error("CN Windows system CNG account check_key unavailable on this platform");
#endif
}
}
