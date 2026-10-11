#pragma once
#include "cn/net/SharedCredentialServer.h"
#include "cn/net/OperationalTransportSeed.h"
#include "cn/auth/SharedAccountSuccess.h"
#include "cn/auth/SharedIssuedAccountSource.h"
#include "cn/auth/SharedCommonCharacterSummarySource.h"
#include "cn/auth/SharedStoredAccountProfileSource.h"
#include "cn/auth/SharedStoredCharacterSummarySource.h"
#include "cn/auth/SharedSelectedCharacterLocationSource.h"
#include "cn/auth/SharedWorldSelection.h"
#include "cn/world/SharedWorldPreparation.h"
#include <functional>
#include <utility>

namespace god2::cn {
// Qualified supplier outputs only. This connects the real existing controllers
// to the listener; it does not implement missing native values/entitlements.
struct SharedLoginSources {
    using Account=SharedIssuedAccountSource::Account;
    struct World {
        SharedWorldSelection::NativeOffer offer;
        // Actual common preparation controller, not an unrelated callback plus
        // a claimed registry. Composition derives Selected and its exact
        // presence from this same retained object, after checking host sources.
        // Native reservation/assets/bootstrap/gameplay suppliers remain required
        // by SharedWorldPreparation; this pointer never invents those inputs.
        std::shared_ptr<SharedWorldPreparation> preparation;
        // Complete native03 and actual current pre-world operation state.
        // No default issuer; an absent source leaves close controls unavailable.
        SharedWorldSelection::TerminalSource terminal_close;
        // Real ordinary17 transaction/native02 and owned18/native18 suppliers.
        // Absent inputs leave creation unavailable; no TW profile/defaults.
        SharedCharacterCreateOperation::Sources creation;
        // Actual native deletion authority/full02 and the same common SQLite
        // backend. Missing source leaves19 unavailable;1E remains open.
        // Explicit native_summary_removal must use actual Context summary
        // repository plus real all-account invalidation issuer; never default.
        SharedCharacterDeleteOperation::Sources deletion;
    };
    using Login=std::shared_ptr<const god2cn::CnAccountWire::Login>;
    SharedServerPlan::Controllers::Seed seed;
    // Synchronous game-owner source preparation; do not retain credentials or
    // endpoint/context references. Missing source returns nullopt, no success.
    std::function<std::optional<Account>(std::uint64_t,CredentialResult,const Login&)> account;
    std::function<std::optional<World>(std::uint64_t,SharedWorldAdmission::Target,
        CredentialResult,const Login&)> world;
    // Explicit own-server transport policy. Mutually exclusive with seed;
    // missing both is rejected. No default policy or official RNG claim.
    // Composition binds it to the copied ACTUAL Context listener endpoints.
    std::optional<OperationalTransportSeedPolicy> operational_seed_policy;
    // Optional explicit1D/key assembly from actual profile/billing/catalog
    // sources. Mutually exclusive with account; no missing values are filled.
    std::optional<SharedIssuedAccountSource::Config> issued_account_source;
    // Actual selected, immutable native config resources for this qualified
    // client profile. Missing inputs cannot be replaced with guessed slots.
    std::shared_ptr<const god2cn::CnClientGroupConfiguration> client_groups;
    struct StartupClientGroups {
        std::filesystem::path client_root;
        std::vector<std::uint8_t> first_native_argument;
        std::size_t encoded_budget;
        std::size_t plain_budget;
        StartupClientGroups(std::filesystem::path root,std::vector<std::uint8_t> argument,
            std::size_t encoded,std::size_t plain):client_root(std::move(root)),
            first_native_argument(std::move(argument)),encoded_budget(encoded),plain_budget(plain) {}
    };
    // Actual pinned normal-startup operands ->actual selected resource; exactly
    // one form with client_groups. No raw command-line parsing or default root.
    std::optional<StartupClientGroups> startup_client_groups;
    // Optional actual common-name supplier on Context.characters. In this
    // form the selected account/issued preparation must leave summaries empty;
    // a second full07 supplier conflicts rather than silently being replaced.
    // Missing native metadata/visibility inputs never imply an empty account.
    std::optional<SharedCommonCharacterSummarySource::Config> common_character_summaries;
    // Explicit persisted full07/ordered mapping/native22 form on the exact
    // Context reader, with real visibility/rights Current. Conflicts with the
    // direct common metadata supplier. No schema install, rows or defaults.
    std::optional<SharedStoredCharacterSummarySource::Config> stored_character_summaries;
    // Explicit actual state0x1A/selected-row/rights observer. After a verified
    // account supplies full07, bind to its exact qualified current directory.
    // Local Location projection is observed only; original07 bytes stay intact.
    // Absence preserves the existing source path. No default phase/row/rights.
    std::optional<SharedSelectedCharacterLocationSource::Config> selected_character_location;
    struct StoredIssuedAccount {
        SharedIssuedAccountSource::KeyPolicy key_policy;
        SharedStoredAccountProfileSource::Config profile;
        StoredIssuedAccount(SharedIssuedAccountSource::KeyPolicy policy,SharedStoredAccountProfileSource::Config source)
            :key_policy(policy),profile(std::move(source)) {}
    };
    // Third explicit account supplier form: actual common snapshot ->native
    // Profile ->existing issuer. Conflicts with account/issued_account_source;
    // never selected automatically and does not install/populate its schema.
    std::optional<StoredIssuedAccount> stored_issued_account_source;
    struct CommonWorldPreparation {
        std::shared_ptr<const god2cn::CnSceneAssets> assets;
        SharedWorldPreparation::Reserve reserve;
        std::size_t encoded_budget,plain_budget;
        bool bind_account_naming_preparation;
        CommonWorldPreparation(std::shared_ptr<const god2cn::CnSceneAssets> actual_assets,
            SharedWorldPreparation::Reserve actual_reserve,std::size_t encoded,std::size_t plain,
            bool bind_naming):assets(std::move(actual_assets)),reserve(std::move(actual_reserve)),
            encoded_budget(encoded),plain_budget(plain),bind_account_naming_preparation(bind_naming) {}
    };
    // Explicit same-host creation only: actual assets/reservation and budgets
    // remain mandatory. World supplier must leave preparation empty. Naming
    // binds an absent preparation only with explicit bind_naming intent; a
    // competing pointer is rejected. Legacy supplied controllers remain valid
    // but a nonnull Context.common_world requires its exact pair in both paths.
    // Retain sources on the same game owner through controller/operation drain.
    std::optional<CommonWorldPreparation> common_world_preparation;
};

SharedServerPlan::Controllers compose_native_login(const SharedServerPlan::Context&,SharedLoginSources);
// Assign to SharedServerPlan::controllers. The host invokes this source factory
// on its game owner after actual bind/listen, before accepting connections.
// Build sources from that exact Context; never retain Context or endpoint refs.
// Retain repository pointers/shared owners and copy endpoint values when needed.
// The selected stored profile must use Context.account_snapshots itself.
// Real metadata/rights/world callbacks remain mandatory; no default plan/data.
using SharedLoginSourceFactory=std::function<SharedLoginSources(const SharedServerPlan::Context&)>;
using SharedLoginControllerFactory=decltype(SharedServerPlan::controllers);
SharedLoginControllerFactory make_native_login_controller_factory(SharedLoginSourceFactory);
}
