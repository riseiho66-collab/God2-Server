#pragma once
#include "db/Database.h"
namespace god2 {
class MySqlDatabase final : public Database {
public:
    void initialize() override;
    void migrate() override;
    AccountRepository& accounts() override;
    CharacterRepository& characters() override;
    RecoveredCharacterRepository& recovered_characters() override;
};
}
