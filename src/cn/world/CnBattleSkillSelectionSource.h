#pragma once
#include "cn/protocol/CnBattleSkillSelection.h"
#include "cn/assets/CnSharedSkillCatalog.h"
#include <memory>
#include <optional>
#include <vector>

namespace god2::cn {
// Actual supplied primary/secondary battle list -> exact original pointer and
// complete shared definition. Neither membership nor flags grant learned skills.
class CnBattleSkillSelectionSource final {
    struct State;
    struct Storage;
public:
    using Native=god2cn::CnBattleSkillSelection;
    struct Entry {
        Native::Entry native;
        NativeSkillRecord definition;
    };
    class Snapshot final {
    public:
        const Native::Snapshot& native() const;
        const std::vector<Entry>& entries() const;
    private:
        friend class CnBattleSkillSelectionSource;
        explicit Snapshot(std::shared_ptr<const Storage>);
        std::shared_ptr<const Storage> storage_;
    };
    // No borrowed database read at composition. The actual caller must qualify
    // its catalog/reader/store lifetime relationship before resolve/current or
    // selected; nonnull pointers alone do not qualify that relationship.
    static std::shared_ptr<CnBattleSkillSelectionSource> create(
        std::shared_ptr<const CnSharedSkillCatalog>);
    bool owns_catalog(const std::shared_ptr<const CnSharedSkillCatalog>&) const;
    std::optional<Snapshot> resolve(const Native::Snapshot&);
    bool current(const Snapshot&);
    // Exact current signed native list index only. Does not search an equal key
    // elsewhere, mask a DWORD, interpret flags as entitlement, or rebase state.
    std::optional<Entry> selected(const Snapshot&,std::uint32_t full_operand);
    ~CnBattleSkillSelectionSource();
private:
    explicit CnBattleSkillSelectionSource(std::shared_ptr<State>);
    std::shared_ptr<State> state_;
};
}
