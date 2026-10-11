#include "db/SqliteCharacterRepository.h"
#include "db/SqliteSupport.h"
namespace god2 {
namespace {
Character read_character(sqlite_detail::Statement& s) {
    Character c;
    c.id = s.number<std::uint64_t>(0);
    c.account_id = s.number<std::uint64_t>(1);
    c.name = s.text(2);
    c.level = s.number<std::uint32_t>(3);
    c.job = s.number<std::uint32_t>(4);
    c.hp = s.number<std::uint32_t>(5);
    c.mp = s.number<std::uint32_t>(6);
    c.map_id = s.number<std::uint32_t>(7);
    c.x = s.number<std::int32_t>(8);
    c.y = s.number<std::int32_t>(9);
    c.created_at = s.text(10);
    return c;
}
void bind_character(sqlite_detail::Statement& s, const Character& c) {
    if (c.name.empty()) throw DatabaseError("Character name must not be empty");
    s.bind(1, c.name);
    s.bind(2, c.level);
    s.bind(3, c.job);
    s.bind(4, c.hp);
    s.bind(5, c.mp);
    s.bind(6, c.map_id);
    s.bind(7, c.x);
    s.bind(8, c.y);
    s.bind_id(9, c.account_id);
}
}
Character SqliteCharacterRepository::create(const Character& character) {
    sqlite_detail::Transaction transaction(db_);
    sqlite_detail::Statement statement(db_,
        "INSERT INTO characters(name,level,job,hp,mp,map_id,x,y,account_id) VALUES(?,?,?,?,?,?,?,?,?)");
    bind_character(statement, character);
    statement.done();
    auto created = find_by_id(static_cast<std::uint64_t>(sqlite3_last_insert_rowid(db_)));
    if (!created) throw DatabaseError("Inserted character missing");
    transaction.commit();
    return *created;
}
std::optional<Character> SqliteCharacterRepository::find_by_id(std::uint64_t id) {
    sqlite_detail::Statement statement(db_,
        "SELECT id,account_id,name,level,job,hp,mp,map_id,x,y,created_at FROM characters WHERE id=?");
    statement.bind_id(1, id);
    if (!statement.row()) return std::nullopt;
    return read_character(statement);
}
std::vector<Character> SqliteCharacterRepository::list_for_account(std::uint64_t account_id) {
    sqlite_detail::Statement statement(db_,
        "SELECT id,account_id,name,level,job,hp,mp,map_id,x,y,created_at FROM characters WHERE account_id=? ORDER BY id");
    statement.bind_id(1, account_id);
    std::vector<Character> result;
    while (statement.row()) result.push_back(read_character(statement));
    return result;
}
void SqliteCharacterRepository::save(const Character& character) {
    sqlite_detail::Statement statement(db_,
        "UPDATE characters SET name=?,level=?,job=?,hp=?,mp=?,map_id=?,x=?,y=? WHERE account_id=? AND id=?");
    bind_character(statement, character);
    statement.bind_id(10, character.id);
    statement.done();
    if (sqlite3_changes(db_) != 1) throw DatabaseError("Character does not exist or account ownership differs");
}
}
