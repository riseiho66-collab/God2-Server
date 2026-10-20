#pragma once
#include <filesystem>
#include <memory>
#include <string>

namespace god2 {
// CUSTOM-0163. A lifetime lock on the actual database file, not a pathname
// sidecar or a process-wide fcntl lock. All SqliteDatabase hosts participate.
// Shared permits normal hosts; Exclusive permits the dedicated offline CLI.
// SQLite itself does not participate in this additional ownership namespace.
class SqliteProcessOwnership final {
public:
    enum class Mode { Shared,Exclusive };
    static std::unique_ptr<SqliteProcessOwnership> acquire(
        const std::filesystem::path&,Mode,bool allow_create=false);
    ~SqliteProcessOwnership();
    SqliteProcessOwnership(const SqliteProcessOwnership&)=delete;
    SqliteProcessOwnership& operator=(const SqliteProcessOwnership&)=delete;
    const std::filesystem::path& path() const noexcept{return path_;}
    const std::string& file_identity() const noexcept{return identity_;}
    bool exclusive() const noexcept{return exclusive_;}
    // Pure retained lifetime; no SQL, filesystem lookup, callback or provider.
    bool current() const noexcept;
    bool path_current() const; // Direct OS identity check, never a SQL callback.
private:
    struct Impl;
    SqliteProcessOwnership();
    std::unique_ptr<Impl> impl_;
    std::filesystem::path path_;
    std::string identity_;
    bool exclusive_=false;
};
}
