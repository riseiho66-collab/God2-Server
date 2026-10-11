#include "cn/auth/SharedStoredAccountProfileSource.h"
#include "cn/auth/SharedAccountDirectorySource.h"
#include <stdexcept>
#include <thread>

namespace god2::cn {
namespace {
constexpr std::string_view client="582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8";
struct Preparing {
    bool& busy;
    explicit Preparing(bool& flag):busy(flag){busy=true;}
    ~Preparing(){busy=false;}
};
}
SharedStoredAccountProfileSource::Prepare SharedStoredAccountProfileSource::with_active_directory(
    Prepare actual_prepare,std::shared_ptr<const SharedListenerRegistry> listeners,
    std::shared_ptr<const god2cn::CnClientGroupConfiguration> client_groups) {
    if(!actual_prepare || !listeners || !client_groups)
        throw std::invalid_argument("CN deferred directory requires actual plan and listener/config owners");
    struct State {
        Prepare prepare;
        std::shared_ptr<const SharedListenerRegistry> listeners;
        std::shared_ptr<const god2cn::CnClientGroupConfiguration> client_groups;
        const std::thread::id owner=std::this_thread::get_id();
        bool busy=false;
        State(Prepare actual,std::shared_ptr<const SharedListenerRegistry> registry,
              std::shared_ptr<const god2cn::CnClientGroupConfiguration> groups)
            :prepare(std::move(actual)),listeners(std::move(registry)),client_groups(std::move(groups)) {}
    };
    auto state=std::make_shared<State>(std::move(actual_prepare),std::move(listeners),std::move(client_groups));
    return [state=std::move(state)](const Native::Scope& scope,
                                  const NativeAccountSnapshot& snapshot)->std::optional<Plan> {
        if(state->owner!=std::this_thread::get_id())
            throw std::logic_error("CN deferred directory game owner mismatch");
        if(state->busy)return std::nullopt;
        Preparing active(state->busy);
        const auto bound=state->listeners->observe();
        if(!bound)return std::nullopt;
        auto plan=state->prepare(scope,snapshot);
        if(!plan || !bound->current())return std::nullopt;
        if(plan->directory && (!plan->catalog.empty() || !plan->directory->current()))return std::nullopt;
        const auto& catalog=plan->directory?plan->directory->catalog():plan->catalog;
        auto qualified=SharedAccountDirectorySource::from_catalog(catalog,*bound,state->client_groups);
        if(!qualified || !qualified->current() || !bound->current())return std::nullopt;
        if(plan->directory) {
            // Qualification must not replace a valid supplied source with the
            // host's source, or discard an ambiguous competing raw catalog.
            if(!plan->directory->current())return std::nullopt;
        } else {
            plan->directory.emplace(std::move(*qualified));
            plan->catalog.clear(); // Existing issuer requires exactly one form.
        }
        return plan;
    };
}
SharedIssuedAccountSource::Prepare SharedStoredAccountProfileSource::create(AccountRepository& accounts,Config config) {
    if(!config.prepare || !config.authority || !config.snapshots.get().owns_accounts(accounts))
        throw std::invalid_argument("CN stored profile requires same account backend and actual plan/authority");
    struct State {
        AccountRepository& accounts;
        NativeAccountSnapshotRepository& snapshots;
        Prepare prepare;
        Authority authority;
        const std::thread::id owner=std::this_thread::get_id();
        bool busy=false;
        State(AccountRepository& backend,Config config):accounts(backend),snapshots(config.snapshots.get()),
            prepare(std::move(config.prepare)),authority(std::move(config.authority)) {}
    };
    auto state=std::make_shared<State>(accounts,std::move(config));
    return [state=std::move(state)](const Native::Scope& scope)->std::optional<SharedIssuedAccountSource::Prepared> {
        if(state->owner!=std::this_thread::get_id())throw std::logic_error("CN stored profile game owner mismatch");
        if(state->busy || !scope.account_session || !scope.verified_account ||
           !state->snapshots.owns_accounts(state->accounts))return std::nullopt;
        Preparing active(state->busy);
        auto value=state->snapshots.load(scope.verified_account,client);
        if(!value || value->account!=scope.verified_account || value->client_sha256!=client ||
           !value->revision || value->metadata.size()!=40 || value->billing.size()!=16)return std::nullopt;
        const auto snapshot=std::make_shared<const NativeAccountSnapshot>(std::move(*value));
        auto plan=state->prepare(scope,*snapshot);
        if(!plan || state->snapshots.load(scope.verified_account,client)!=std::optional{*snapshot})return std::nullopt;
        const Profile::Scope profile_scope{scope.account_session,scope.verified_account,snapshot->revision};
        Profile::Current current=[state,snapshot,profile_scope](const Profile::Scope& actual,
            Native::Check check,const Native::Observation& observation) {
            if(state->owner!=std::this_thread::get_id() || state->busy || actual.account_session!=profile_scope.account_session ||
               actual.verified_account!=profile_scope.verified_account || actual.source_revision!=profile_scope.source_revision ||
               !state->snapshots.owns_accounts(state->accounts))return false;
            Preparing active(state->busy);
            if(state->snapshots.load(actual.verified_account,client)!=std::optional{*snapshot})return false;
            // Real authority observes exact native credentials/ID/key/catalog/
            // deadline only within this callback; never persist/log them here.
            if(!state->authority(*snapshot,actual,check,observation))return false;
            return state->snapshots.owns_accounts(state->accounts) &&
                   state->snapshots.load(actual.verified_account,client)==std::optional{*snapshot};
        };
        auto profile=Profile::from_source(snapshot->metadata,snapshot->billing,profile_scope,std::move(current));
        if(!profile)return std::nullopt;
        return SharedIssuedAccountSource::Prepared{std::move(*profile),plan->deadline,std::move(plan->catalog),
            std::move(plan->summaries),std::move(plan->naming),std::move(plan->naming_preparation),std::move(plan->directory)};
    };
}
}
