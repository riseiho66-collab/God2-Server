#pragma once
#include "db/Migration.h"
namespace god2 {
class MySqlMigrationManager final : public MigrationManager {
public:
    void migrate() override;
};
}
