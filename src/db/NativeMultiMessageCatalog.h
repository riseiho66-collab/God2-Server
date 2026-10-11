#pragma once
#include <cstdint>
struct sqlite3;
namespace god2 {
// Source display only; no original NPC/event/quest transition authority.
class NativeMultiMessageCatalog {
    sqlite3* db_;
public:
    explicit NativeMultiMessageCatalog(sqlite3* db):db_(db){}
    bool populated() const;
    // Validate complete pinned catalog and exact key1434 bytes before encoding.
    std::uint32_t knowledge_menu_count() const;
};
}
