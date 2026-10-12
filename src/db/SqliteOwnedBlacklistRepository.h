#pragma once
#include <sqlite3.h>
#include <cstdint>
#include <utility>
#include <memory>
#include <functional>
#include <optional>
#include <string>
#include <string_view>
#include <vector>
namespace god2 {
class OwnedBlacklistService;
class SqliteOwnedBlacklistRepository final {
public:
    // CUSTOM-0096: max10 active /4096 lifetime captured CP950 names.
    // IDs0 and FFFFFFFF are reserved; row IDs1..FFFFFFFE are global committed
    // contact-row DWORDs, not common IDs. Future contact authorities must share
    // this allocator or qualify a disjoint namespace before coexistence.
    struct Row {
        std::uint32_t row_id;
        std::uint64_t account,character,target_character;
        std::string name;
        bool active;
        bool operator==(const Row&) const=default;
    };
    explicit SqliteOwnedBlacklistRepository(sqlite3* db):db_(db) {}
    SqliteOwnedBlacklistRepository(const SqliteOwnedBlacklistRepository&)=delete;
    SqliteOwnedBlacklistRepository& operator=(const SqliteOwnedBlacklistRepository&)=delete;
    static void install_schema(sqlite3*);
    using Current=std::function<bool()>; // Actual pure Session/feature current; no SQL writes or transaction operations.
    struct Snapshot {bool supported;std::vector<Row> rows;bool operator==(const Snapshot&) const=default;};
    Snapshot load(std::uint64_t account,std::uint64_t character,Current);
    // Exact material from this actual owned operation, allocated and qualified
    // inside its one transaction before COMMIT. No observation or public mint.
    // changed=false retains the original idempotent reply, never a fanout event.
    class CommittedChange {
    public:
        CommittedChange(const CommittedChange&)=delete;
        CommittedChange& operator=(const CommittedChange&)=delete;
        CommittedChange(CommittedChange&&) noexcept=default;
        CommittedChange& operator=(CommittedChange&&) noexcept=default;
        const Snapshot& before() const noexcept{return data_->before;}
        const Snapshot& after() const noexcept{return data_->after;}
        // Aliases the already-owned pre-COMMIT Data; refcount only, no allocation.
        std::shared_ptr<const Snapshot> before_ptr() const noexcept{return {data_,&data_->before};}
        std::shared_ptr<const Snapshot> after_ptr() const noexcept{return {data_,&data_->after};}
        const Row& row() const noexcept{return data_->row;}
        const std::vector<std::uint8_t>& logical() const noexcept{return data_->logical;}
        bool changed() const noexcept{return data_->changed;}
    private:
        friend class SqliteOwnedBlacklistRepository;
        friend class OwnedBlacklistService;
        struct Data {
            const Snapshot before,after;
            Row row;
            std::vector<std::uint8_t> logical;
            const bool changed;
            const sqlite3_int64 staged_changes;
            Data(Snapshot b,Snapshot a,Row r,std::vector<std::uint8_t> l,bool c,sqlite3_int64 changes) noexcept
                :before(std::move(b)),after(std::move(a)),row(std::move(r)),logical(std::move(l)),changed(c),staged_changes(changes) {}
        };
        explicit CommittedChange(std::shared_ptr<Data> data) noexcept:data_(std::move(data)) {}
        std::shared_ptr<Data> data_;
    };
    std::optional<CommittedChange> add_committed(std::uint64_t account,std::uint64_t character,std::string_view name,Current);
    std::optional<CommittedChange> remove_committed(std::uint64_t account,std::uint64_t character,std::uint32_t row_id,Current);
    std::optional<Row> add(std::uint64_t account,std::uint64_t character,std::string_view name,Current);
    std::optional<Row> remove(std::uint64_t account,std::uint64_t character,std::uint32_t row_id,Current);
private:
    struct Operation;
    struct Root;
    sqlite3* db_;
    bool active_=false,reentered_=false;
    void qualify(bool installed);
    Root owner(std::uint64_t account,std::uint64_t character);
    std::vector<Row> rows(std::uint64_t account,std::uint64_t character);
    CommittedChange prepare_committed_change(const Snapshot&,Row,bool,Operation&,const Root&,const Root*);
    void check_committed_change(const CommittedChange&);
};
}
