#pragma once
#include "db/SqliteWorldDisplayRepository.h"
#include <optional>
namespace god2 {
// CUSTOM-0064: explicit bank-role evidence is separate from a display/name.
// No row is inferred, inserted or moved by constructor/load/startup.
class SqliteBankAccessRepository {
public:
    explicit SqliteBankAccessRepository(sqlite3* db):db_(db){}
    void install_schema();
    std::optional<StoredWorldDisplay> lookup(std::uint16_t area,std::uint16_t scene,
        std::uint16_t identity,bool isolated=false) const;
private:
    sqlite3* db_;
};
}
