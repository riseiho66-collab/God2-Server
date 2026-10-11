#pragma once
#include "db/DbTypes.h"
#include <sqlite3.h>
#include <cstdint>
#include <limits>
#include <span>
#include <string>

namespace god2::sqlite_detail {
inline void check(sqlite3* db, int code) {
    if (code != SQLITE_OK) throw DatabaseError(sqlite3_errmsg(db));
}
inline void execute(sqlite3* db, const std::string& sql) {
    check(db, sqlite3_exec(db, sql.c_str(), nullptr, nullptr, nullptr));
}
class Statement {
public:
    Statement(sqlite3* db, const char* sql) : db_(db) {
        check(db_, sqlite3_prepare_v2(db_, sql, -1, &statement_, nullptr));
    }
    ~Statement() { sqlite3_finalize(statement_); }
    Statement(const Statement&) = delete;
    Statement& operator=(const Statement&) = delete;
    void bind(int index, const std::string& value) {
        if (value.size() > static_cast<std::size_t>(std::numeric_limits<int>::max()))
            throw DatabaseError("Text exceeds SQLite binding limit");
        check(db_, sqlite3_bind_text(statement_, index, value.data(), static_cast<int>(value.size()), SQLITE_TRANSIENT));
    }
    void bind(int index, std::int64_t value) { check(db_, sqlite3_bind_int64(statement_, index, value)); }
    void bind_blob(int index, std::span<const std::uint8_t> value) {
        if (value.size() > static_cast<std::size_t>(std::numeric_limits<int>::max()))
            throw DatabaseError("Blob exceeds SQLite binding limit");
        const void* data = value.empty() ? static_cast<const void*>("") : value.data();
        check(db_, sqlite3_bind_blob(statement_, index, data, static_cast<int>(value.size()), SQLITE_TRANSIENT));
    }
    std::span<const std::uint8_t> blob(int column, std::size_t min_size, std::size_t max_size) const {
        if (sqlite3_column_type(statement_, column) != SQLITE_BLOB)
            throw DatabaseError("Expected blob database column");
        const auto size = static_cast<std::size_t>(sqlite3_column_bytes(statement_, column));
        if (size < min_size || size > max_size) throw DatabaseError("Database blob size out of range");
        const auto* data = static_cast<const std::uint8_t*>(sqlite3_column_blob(statement_, column));
        if (!data && size != 0) throw DatabaseError("Unable to read database blob");
        return {data, size};
    }
    void bind_id(int index, std::uint64_t value) {
        if (value > static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()))
            throw DatabaseError("ID exceeds SQLite signed 64-bit range");
        bind(index, static_cast<std::int64_t>(value));
    }
    bool row() {
        const int result = sqlite3_step(statement_);
        if (result == SQLITE_ROW) return true;
        if (result == SQLITE_DONE) return false;
        throw DatabaseError(sqlite3_errmsg(db_));
    }
    void done() { if (row()) throw DatabaseError("Unexpected result row"); }
    std::int64_t integer(int column) const {
        if (sqlite3_column_type(statement_, column) != SQLITE_INTEGER)
            throw DatabaseError("Expected integer database column");
        return sqlite3_column_int64(statement_, column);
    }
    template<class T> T number(int column) const {
        const auto value = integer(column);
        if constexpr (std::numeric_limits<T>::is_signed) {
            if (value < std::numeric_limits<T>::min() || value > std::numeric_limits<T>::max())
                throw DatabaseError("Database integer out of range");
        } else {
            if (value < 0 || static_cast<std::uint64_t>(value) > std::numeric_limits<T>::max())
                throw DatabaseError("Database integer out of range");
        }
        return static_cast<T>(value);
    }
    std::string text(int column) const {
        if (sqlite3_column_type(statement_, column) != SQLITE_TEXT)
            throw DatabaseError("Expected text database column");
        const auto* value = sqlite3_column_text(statement_, column);
        if (!value) throw DatabaseError("Unable to read database text");
        return {reinterpret_cast<const char*>(value), static_cast<std::size_t>(sqlite3_column_bytes(statement_, column))};
    }
private:
    sqlite3* db_;
    sqlite3_stmt* statement_ = nullptr;
};
class Transaction {
public:
    explicit Transaction(sqlite3* db) : db_(db) { execute(db_, "BEGIN IMMEDIATE"); }
    ~Transaction() { if (!committed_) sqlite3_exec(db_, "ROLLBACK", nullptr, nullptr, nullptr); }
    Transaction(const Transaction&) = delete;
    Transaction& operator=(const Transaction&) = delete;
    void commit() { execute(db_, "COMMIT"); committed_ = true; }
private:
    sqlite3* db_;
    bool committed_ = false;
};
}
