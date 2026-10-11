#include "db/MySqlDatabase.h"
#include "db/DbTypes.h"
namespace god2 {
namespace {
[[noreturn]] void unsupported() { throw UnsupportedDatabaseError("MySQL/MariaDB backend is not implemented"); }
}
void MySqlDatabase::initialize() { unsupported(); }
void MySqlDatabase::migrate() { unsupported(); }
AccountRepository& MySqlDatabase::accounts() { unsupported(); }
CharacterRepository& MySqlDatabase::characters() { unsupported(); }
RecoveredCharacterRepository& MySqlDatabase::recovered_characters() { unsupported(); }
}
