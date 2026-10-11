#include "cn/auth/SharedLoginComposition.h"
#include "cn/world/SharedWorldPreparation.h"
#include "game/SharedWorldHost.h"
#include <stdexcept>
#include <utility>

namespace god2::cn {
SharedServerPlan::Controllers compose_native_login(const SharedServerPlan::Context& context,
                                                   SharedLoginSources sources) {
    auto common_world=context.common_world;
    if(common_world && !common_world->owns_repository(context.characters))
        throw std::invalid_argument("CN common world differs from actual Context characters");
    const auto common_transports=common_world?common_world->transports():nullptr;
    if(common_world && (!common_transports || !common_transports->owns_presence(common_world->presence())))
        throw std::invalid_argument("CN common world requires its actual same-presence native transport source");
    std::shared_ptr<SharedWorldPreparation> common_preparation;
    bool bind_naming=false;
    if(sources.common_world_preparation) {
        if(!common_world)
            throw std::invalid_argument("CN common preparation requires the actual Context world host");
        auto& selected=*sources.common_world_preparation;
        bind_naming=selected.bind_account_naming_preparation;
        common_preparation=SharedWorldPreparation::create(context.characters,context.maps,
            common_world->presence(),common_world->visibility(),std::move(selected.assets),
            std::move(selected.reserve),selected.encoded_budget,selected.plain_budget,common_transports);
        if(!common_preparation)
            throw std::invalid_argument("CN common preparation requires actual assets/reservation and explicit budgets");
    }
    if(sources.client_groups && sources.startup_client_groups)
        throw std::invalid_argument("CN client configuration has conflicting explicit sources");
    if(sources.startup_client_groups) {
        const auto& selected=*sources.startup_client_groups;
        sources.client_groups=god2cn::CnClientGroupConfiguration::read_from_startup_argument(
            selected.client_root,selected.first_native_argument,selected.encoded_budget,selected.plain_budget);
    }
    if(sources.stored_issued_account_source) {
        if(sources.account || sources.issued_account_source)
            throw std::invalid_argument("CN stored profile conflicts with another account supplier");
        auto& selected=*sources.stored_issued_account_source;
        if(&selected.profile.snapshots.get()!=&context.account_snapshots)
            throw std::invalid_argument("CN stored profile requires the actual Context snapshot source");
        selected.profile.prepare=SharedStoredAccountProfileSource::with_active_directory(
            std::move(selected.profile.prepare),context.listeners,sources.client_groups);
        sources.issued_account_source.emplace(selected.key_policy,
            SharedStoredAccountProfileSource::create(context.accounts,std::move(selected.profile)));
    }
    if(sources.account && sources.issued_account_source)
        throw std::invalid_argument("CN issued-account source conflicts with full native account supplier");
    if(sources.stored_character_summaries) {
        if(sources.common_character_summaries ||
           &sources.stored_character_summaries->snapshots.get()!=&context.character_summaries)
            throw std::invalid_argument("CN stored summary conflicts or differs from actual Context reader");
        sources.common_character_summaries.emplace(SharedStoredCharacterSummarySource::create(
            context.accounts,context.characters,std::move(*sources.stored_character_summaries)));
    }
    if(sources.common_character_summaries) {
        auto summaries=SharedCommonCharacterSummarySource::create(context.characters,
            std::move(*sources.common_character_summaries));
        if(sources.issued_account_source) {
            auto prepare=std::move(sources.issued_account_source->prepare);
            if(!prepare)throw std::invalid_argument("CN issued account requires actual profile preparation");
            sources.issued_account_source->prepare=[prepare=std::move(prepare),summaries=std::move(summaries)](
                const SharedAccountSuccess::NativeData::Scope& scope)->std::optional<SharedIssuedAccountSource::Prepared> {
                auto value=prepare(scope);
                if(!value || value->summaries)return std::nullopt;
                value->summaries=summaries;
                return value;
            };
        } else if(sources.account) {
            auto account=std::move(sources.account);
            sources.account=[account=std::move(account),summaries=std::move(summaries)](
                std::uint64_t session,CredentialResult verified,const SharedLoginSources::Login& login)
                ->std::optional<SharedLoginSources::Account> {
                auto value=account(session,verified,login);
                if(!value || value->summaries)return std::nullopt;
                value->summaries=summaries;
                return value;
            };
        } else throw std::invalid_argument("CN common summary requires an actual account supplier");
    }
    if(sources.selected_character_location && !sources.selected_character_location->prepare)
        throw std::invalid_argument("CN selected location requires actual state1A preparation");
    if(sources.issued_account_source)
        sources.account=SharedIssuedAccountSource::create(std::move(*sources.issued_account_source));
    if(!context.admission || !context.listeners || !sources.account || !sources.world || !sources.client_groups)
        throw std::invalid_argument("Native login requires selected client groups, bound listeners and account/world suppliers");
    if(!sources.client_groups->network_version() ||
       *sources.client_groups->network_version()!=god2cn::CnAccountWire::native_config_version)
        throw std::invalid_argument("CN selected client group version is incompatible with pinned native profile");
    if(sources.seed && sources.operational_seed_policy)
        throw std::invalid_argument("CN transport seed has conflicting explicit sources");
    if(sources.operational_seed_policy)
        sources.seed=make_operational_transport_seed_source(*sources.operational_seed_policy,context.endpoints);
    if(!sources.seed)
        throw std::invalid_argument("CN transport seed source is required");
    auto admission=context.admission;
    auto* characters=&context.characters;
    auto* accounts=&context.accounts;
    auto* character_summaries=&context.character_summaries;
    auto* maps=&context.maps;
    // Retain actual managed bind lifetime, never the temporary Context/plan.
    auto listeners=context.listeners;
    auto selected_location=std::move(sources.selected_character_location);
    SharedServerPlan::Controllers result;
    result.account_configuration=sources.client_groups;
    result.seed=std::move(sources.seed);
    result.account=[source=std::move(sources.account),admission,characters,maps,listeners=std::move(listeners),
                    client_groups=std::move(sources.client_groups),common_world,common_transports,common_preparation,bind_naming,
                    selected_location=std::move(selected_location)](
        std::uint64_t id,const SharedServerPlan::Endpoint& endpoint,
        std::shared_ptr<SharedCredentialConnection> connection,CredentialResult account,
        SharedLoginSources::Login login,SharedCredentialConnection::Transport::Completion done) mutable {
        if(endpoint.role!=SharedServerPlan::Role::Account || endpoint.target || !connection ||
           account.outcome!=CredentialOutcome::Verified || account.account_id!=connection->verified_account_id() ||
            !connection->verified_credentials_current(account.source,login) ||
            (common_world && !common_world->owns_repository(*characters))){done(false);return;}
        auto supplied=source(id,account,login);
        if(!supplied || !supplied->summaries || connection->closing() ||
           account.account_id!=connection->verified_account_id() ||
           !connection->verified_credentials_current(account.source,login) ||
           (common_world && !common_world->owns_repository(*characters))) {done(false);return;}
        const auto bound=listeners->observe();
        if(!bound) {done(false);return;}
        auto directory=SharedAccountDirectorySource::from_catalog(supplied->catalog,*bound,client_groups);
        if(!directory) {done(false);return;}
        if(selected_location) {
            try {
                supplied->summaries=SharedSelectedCharacterLocationSource::bind(account.account_id,*directory,
                    std::move(supplied->summaries),*selected_location);
            } catch(...) {done(false);return;}
        }
        if(!supplied->native.bind_directory_source(std::move(*directory))) {done(false);return;}
        if(supplied->naming) {
            if(bind_naming) {
                if(!common_preparation || supplied->naming_preparation) {done(false);return;}
                supplied->naming_preparation=common_preparation;
            }
            if(!*supplied->naming || !supplied->naming_preparation ||
               !supplied->naming_preparation->owns_sources(*characters,*maps) ||
               (common_world && (!supplied->naming_preparation->owns_registries(
                   common_world->presence(),common_world->visibility()) ||
                   !supplied->naming_preparation->owns_transport_source(common_transports)))) {done(false);return;}
            const auto presence=supplied->naming_preparation->presence_registry();
            if(!presence || !supplied->naming->presence->owns_presence_registry(*presence)) {done(false);return;}
        }
        // Source preparation precedes issue; use current time only after it.
        (void)SharedAccountSuccess::attach(connection,admission,id,login,
            std::move(supplied->native),supplied->deadline,*characters,
            std::move(supplied->catalog),std::move(supplied->summaries),SharedWorldAdmission::Clock::now(),std::move(done),
            std::move(supplied->naming));
    };
    result.world=[source=std::move(sources.world),admission,characters,maps,accounts,character_summaries,
                  common_world,common_transports,common_preparation](
        std::uint64_t id,const SharedServerPlan::Endpoint& endpoint,
        std::shared_ptr<SharedCredentialConnection> connection,CredentialResult account,
        SharedLoginSources::Login login,SharedCredentialConnection::Transport::Completion done) mutable {
        if(endpoint.role!=SharedServerPlan::Role::World || !endpoint.target || !connection ||
           account.outcome!=CredentialOutcome::Verified || account.account_id!=connection->verified_account_id() ||
            !connection->verified_credentials_current(account.source,login) ||
            (common_world && !common_world->owns_repository(*characters))){done(false);return;}
        auto supplied=source(id,*endpoint.target,account,login);
        if(!supplied || connection->closing() || account.account_id!=connection->verified_account_id() ||
           !connection->verified_credentials_current(account.source,login) ||
           (common_world && !common_world->owns_repository(*characters))){done(false);return;}
        if(common_preparation) {
            if(supplied->preparation) {done(false);return;}
            supplied->preparation=common_preparation;
        }
        if(!supplied->preparation || !supplied->preparation->owns_sources(*characters,*maps) ||
           (common_world && (!supplied->preparation->owns_registries(
               common_world->presence(),common_world->visibility()) ||
               !supplied->preparation->owns_transport_source(common_transports)))){done(false);return;}
        if(supplied->deletion.native_summary_removal) {
            const auto& selected=*supplied->deletion.native_summary_removal;
            if(!supplied->deletion || &selected.snapshots.get()!=character_summaries ||
               !selected.snapshots.get().owns_sources(*accounts,*characters) ||
               static_cast<RecoveredCharacterRepository*>(supplied->deletion.characters)!=characters) {
                done(false);return;
            }
        }
        // Read identity from the actual same controller used below. A caller
        // cannot qualify deletion with registryA while preparing in registryB.
        const auto presence=supplied->preparation->presence_registry();
        if(supplied->deletion && (!presence ||
           !supplied->deletion.presence->owns_presence_registry(*presence))) {
            done(false);return;
        }
        auto selected=supplied->preparation->selected(); // Retains this controller.
        (void)SharedWorldSelection::attach(connection,admission,id,*endpoint.target,
            *characters,*maps,std::move(supplied->offer),std::move(selected),
            SharedWorldAdmission::Clock::now(),std::move(done),std::move(supplied->terminal_close),
            std::move(supplied->creation),std::move(supplied->deletion));
    };
    return result;
}
SharedLoginControllerFactory make_native_login_controller_factory(SharedLoginSourceFactory factory) {
    if(!factory)throw std::invalid_argument("CN login controller factory requires actual source preparation");
    return [factory=std::move(factory)](const SharedServerPlan::Context& context) {
        // Validate the actual host inputs before calling external preparation.
        // The returned controllers retain their own required sources, not Context.
        if(!context.account_snapshots.owns_accounts(context.accounts) ||
           !context.character_summaries.owns_sources(context.accounts,context.characters) ||
            !context.admission || !context.listeners ||
            (context.common_world && !context.common_world->owns_repository(context.characters)))
            throw std::invalid_argument("CN login controller factory requires same-account snapshots and host owners");
        auto sources=factory(context);
        return compose_native_login(context,std::move(sources));
    };
}
}
