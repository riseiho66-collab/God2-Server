#pragma once
#include "cn/world/SharedNativeBattleCommandGroups.h"
#include "cn/assets/CnSharedSkillCatalog.h"
#include "db/SharedSkillDefinition.h"
#include "cn/protocol/CnBattleInventorySlot.h"
#include "cn/protocol/CnBattleSkillDefinition.h"
#include "cn/world/CnBattleSkillSelectionSource.h"
#include <functional>
#include <map>

namespace god2::cn {
// Real catalog lookup and exact inventory snapshots for actual ordered C35
// requests. Definition/cell existence does not grant learned skills or custody.
class SharedNativeBattleCommandData final:public SharedNativeBattleCommandGroups::Authority {
    struct State;
public:
    using Groups=SharedNativeBattleCommandGroups;
    using Connection=Groups::Connection;
    using Lease=Groups::Lease;
    using Scope=Groups::Scope;
    using Request=Groups::Request;
    using Plan=Groups::Plan;
    using Check=Groups::Check;
    using Result=Groups::Result;
    enum class Domain {Opaque,Skill,Item};
    struct InventorySnapshot {
        Lease lease;
        std::uint64_t actual_generation;
        std::map<std::uint16_t,god2cn::CnBattleInventorySlot::Record> cells;
        // Complete actual dictionary, not an invented38-cell native database.
    };
    class InventorySource {
    public:
        virtual ~InventorySource()=default;
        virtual std::optional<InventorySnapshot> read(Connection&,const Scope&)=0;
        virtual bool current(Connection&,const Scope&,const InventorySnapshot&,const Result*)=0;
        // Read-only/nonyielding actual owner/projection source. Current after
        // settlement may qualify its retained before image via actual Result;
        // no default ownership or silent post-cost reread/rebase.
    };
    struct Row {
        Request request;
        Domain domain;
        std::optional<NativeSkillRecord> skill;
        std::optional<god2cn::CnBattleSkillDefinition::Record> skill_fields;
        std::optional<std::uint16_t> inventory_slot;
        std::optional<god2cn::CnBattleInventorySlot::Record> item;
        // Optional actual recovered list evidence. Absence grants nothing;
        // common learned/actor/current qualification remains DataAuthority.
        std::optional<CnBattleSkillSelectionSource::Snapshot> native_skill_selection;
        // CUSTOM-0142: same-registry owning definition supplied to the actual
        // DataAuthority callbacks. CN raw/native permission fields above remain
        // original; common parameter selection is not learned/cost/actor authority.
        std::optional<SharedSkillDefinition> common_definition{};
    };
    struct Resolved {
        std::vector<Row> rows; // Complete physical arrival order, including opaque rows.
        std::optional<InventorySnapshot> inventory;
    };
    struct CatalogBinding {
        std::shared_ptr<const CnSharedSkillCatalog> skills;
        std::shared_ptr<const NativeSkillCatalog> shared_reader;
        std::shared_ptr<const void> actual_store_lifetime;
    };
    class DataAuthority {
    public:
        virtual ~DataAuthority()=default;
        // Qualify the actual lifetime/reader/catalog relationship BEFORE any
        // borrowed store read; non-null shared pointers are not such proof.
        virtual bool catalog_current(Connection&,const Scope&,const CatalogBinding&)=0;
        // Exact domain per physical request. Actual native command variant
        // and selected resource lineage must qualify each choice; no guessed
        // type stripping/lookup key, permission or cost. All observers pure,
        // nonyielding/read-only/nonreentrant, no retained borrowed arguments.
        virtual std::optional<std::vector<Domain>> domains(Connection&,const Scope&,
            std::span<const Request>)=0;
        // Must establish the supplied actual store lifetime/reader/catalog
        // binding, full source ownership, learned/native skill identity and
        // inventory custody plus grant/expiry/replay/rules. Non-null is no proof.
        virtual bool current(Connection&,Check,const Scope&,const Plan*,const Resolved&,
            const CatalogBinding&,const Result*)=0;
        virtual std::optional<Plan> prepare(Connection&,const Scope&,const Resolved&,const Plan* saved)=0;
        virtual std::optional<Result> execute_group(Connection&,const Scope&,const Plan&,const Resolved&)=0;
    };
    struct Budgets {std::size_t max_requests,max_inventory_records;};
    struct SkillSelectionBinding {
        std::shared_ptr<CnBattleSkillSelectionSource> source;
        using Read=std::function<std::shared_ptr<const god2cn::CnBattleSkillSelection::Snapshot>(
            Connection&,const Scope&,const Request&)>;
        Read read;
        // Optional supplied recovery projection, never a client-memory runtime
        // prerequisite. Actual owner qualifies its native/common actor and
        // command lineage through mandatory DataAuthority.current. Read is
        // pure/nonyielding/nonreentrant and retains no borrowed arguments.
        // Selecting this binding requires both suppliers; failure never falls
        // back to a same-key catalog lookup or substitutes a new selection.
    };
    struct Configuration {
        CatalogBinding catalog;
        std::shared_ptr<InventorySource> inventory;
        std::shared_ptr<DataAuthority> authority;
        Budgets budgets;
        std::optional<SkillSelectionBinding> skill_selection;
    };
    static std::shared_ptr<SharedNativeBattleCommandData> create(const std::shared_ptr<Connection>&,
        const Lease&,std::shared_ptr<SharedNativeWorldTransports>,Configuration);
    ~SharedNativeBattleCommandData();
    std::optional<Plan> prepare(Connection&,const Scope&,const Request&,std::span<const Request>,const Plan*) override;
    bool current(Connection&,Check,const Scope&,const Request&,const Plan&,std::span<const Request>,const Result*) override;
    std::optional<Result> execute_group(Connection&,const Scope&,std::span<const Request>,const Plan&) override;
private:
    explicit SharedNativeBattleCommandData(std::shared_ptr<State>);
    std::shared_ptr<State> state_;
};
}
