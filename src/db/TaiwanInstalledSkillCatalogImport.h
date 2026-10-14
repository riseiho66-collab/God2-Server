#pragma once
#include "db/TaiwanInstalledSkillCatalogSource.h"
#include <memory>
#include <thread>

struct sqlite3;
namespace god2 {
// Explicit insertion-only definition import. Installation-thread affinity is
// captured by the real Database Impl; no SQL occurs in this constructor.
// Outcome reports local COMMIT, never installed client banks or learned rights.
class TaiwanInstalledSkillCatalogImport final {
public:
    enum class Result { Inserted, AlreadyPresent };
    struct Outcome {
        Result result;
        bool commit_confirmed;
        bool connection_current;
    };
    explicit TaiwanInstalledSkillCatalogImport(sqlite3*);
    TaiwanInstalledSkillCatalogImport(const TaiwanInstalledSkillCatalogImport&)=delete;
    TaiwanInstalledSkillCatalogImport& operator=(const TaiwanInstalledSkillCatalogImport&)=delete;
    TaiwanInstalledSkillCatalogImport(TaiwanInstalledSkillCatalogImport&&)=delete;
    TaiwanInstalledSkillCatalogImport& operator=(TaiwanInstalledSkillCatalogImport&&)=delete;
    bool uses_connection(const sqlite3* value) const noexcept { return db_==value; }
    Outcome import_source(const std::shared_ptr<const TaiwanInstalledSkillCatalogSource>&);
private:
    struct Operation;
    class Statement;
    void owner() const;
    void require_schema(Operation&);
    bool source_present(Operation&,const NativeSkillSource&);
    void require_records(Operation&,std::span<const NativeSkillRecord>);
    void insert_source(Operation&,const NativeSkillSource&);
    void insert_record(Operation&,const NativeSkillRecord&);
    sqlite3* const db_;
    const std::thread::id thread_;
    bool busy_=false,poisoned_=false;
};
}
