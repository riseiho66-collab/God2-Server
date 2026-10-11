#pragma once
#include "db/SqliteNativeEquipmentSnapshotRepository.h"
#include "db/SqliteOwnedEquipmentTransaction.h"
#include "cn/world/SharedActorVisibility.h"
#include <memory>
#include <thread>

namespace god2 {
// Actual durable raw delivery witness -> existing singleTW held DA endpoint.
// No equip request/rule/acquisition or item-to-appearance mapping is invented.
// Borrowed database/common sources must outlive this game-owned supplier/drain.
class SharedTaiwanNativeEquipmentPublicationSource final:
    public std::enable_shared_from_this<SharedTaiwanNativeEquipmentPublicationSource> {
public:
    static std::shared_ptr<SharedTaiwanNativeEquipmentPublicationSource> create(
        SqliteNativeEquipmentSnapshotRepository&,AccountRepository&,RecoveredCharacterRepository&,
        std::shared_ptr<SharedWorldPresence>,std::shared_ptr<cn::SharedActorVisibility>,
        SqliteNativeEquipmentSnapshotRepository::Committed);
    // Joint canonical inventory/native snapshot receipt. Every held-DA source
    // reread qualifies BOTH whole populations in one consistent storage scope.
    static std::shared_ptr<SharedTaiwanNativeEquipmentPublicationSource> create(
        std::shared_ptr<SqliteOwnedEquipmentTransaction>,AccountRepository&,RecoveredCharacterRepository&,
        std::shared_ptr<SharedWorldPresence>,std::shared_ptr<cn::SharedActorVisibility>,
        SqliteOwnedEquipmentTransaction::Committed);
    void publish(const cn::SharedActorVisibility::Binding&,
        cn::SharedActorVisibility::TaiwanAppearanceCompletion);
private:
    SharedTaiwanNativeEquipmentPublicationSource(SqliteNativeEquipmentSnapshotRepository&,
        AccountRepository&,RecoveredCharacterRepository&,std::shared_ptr<SharedWorldPresence>,
        std::shared_ptr<cn::SharedActorVisibility>,SqliteNativeEquipmentSnapshotRepository::Committed);
    void owner() const;
    std::optional<cn::SharedActorVisibility::TaiwanAppearanceAfterState> current(const SharedWorldPresence::Lease&);
    SqliteNativeEquipmentSnapshotRepository& repository_;
    AccountRepository& accounts_;
    RecoveredCharacterRepository& characters_;
    std::shared_ptr<SharedWorldPresence> presence_;
    std::shared_ptr<cn::SharedActorVisibility> visibility_;
    SqliteNativeEquipmentSnapshotRepository::Committed committed_;
    std::shared_ptr<SqliteOwnedEquipmentTransaction> joint_repository_;
    std::optional<SqliteOwnedEquipmentTransaction::Committed> joint_committed_;
    const std::thread::id thread_=std::this_thread::get_id();
    bool reading_=false,reentered_=false;
};
}
