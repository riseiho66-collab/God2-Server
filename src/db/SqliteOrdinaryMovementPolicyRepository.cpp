#include "db/SqliteOrdinaryMovementPolicyRepository.h"
#include "db/SqliteSupport.h"
#include <limits>
#include <utility>

namespace god2 {
namespace {
bool profile_key_valid(const std::string& key) noexcept {
    if(key.empty()||key.size()>48||key.front()<'a'||key.front()>'z')return false;
    for(const unsigned char value:key)
        if(!((value>='a'&&value<='z')||(value>='0'&&value<='9')||value=='_'))return false;
    return true;
}
bool strict_boolean(sqlite_detail::Statement& query,int column) {
    const auto value=query.integer(column);
    if(value!=0&&value!=1)throw DatabaseError("Movement policy boolean must be integer zero or one");
    return value==1;
}
}
SqliteOrdinaryMovementPolicyRepository::SqliteOrdinaryMovementPolicyRepository(sqlite3* db):db_(db) {
    if(!db_)throw DatabaseError("Movement policy requires actual SQLite connection");
}
std::string SqliteOrdinaryMovementPolicyRepository::schema() {return R"SQL(
CREATE TABLE main.movement_rules (
 profile_key TEXT COLLATE BINARY NOT NULL PRIMARY KEY
  CHECK(typeof(profile_key)='text' AND length(profile_key) BETWEEN 1 AND 48
   AND length(CAST(profile_key AS BLOB))=length(profile_key)
   AND substr(profile_key,1,1) GLOB '[a-z]' AND profile_key NOT GLOB '*[^a-z0-9_]*'),
 config_version INTEGER NOT NULL CHECK(typeof(config_version)='integer' AND config_version BETWEEN 1 AND 9223372036854775807),
 step_interval_us INTEGER NOT NULL CHECK(typeof(step_interval_us)='integer' AND step_interval_us BETWEEN 1 AND 60000000),
 burst_steps INTEGER NOT NULL CHECK(typeof(burst_steps)='integer' AND burst_steps BETWEEN 1 AND 39),
 initial_credit_steps INTEGER NOT NULL CHECK(typeof(initial_credit_steps)='integer' AND initial_credit_steps BETWEEN 1 AND burst_steps),
 first_sequence INTEGER NOT NULL CHECK(typeof(first_sequence)='integer' AND first_sequence BETWEEN 0 AND 39),
 block_players INTEGER NOT NULL CHECK(typeof(block_players)='integer' AND block_players IN (0,1)),
 forbid_corner_cut INTEGER NOT NULL CHECK(typeof(forbid_corner_cut)='integer' AND forbid_corner_cut IN (0,1)),
 allow_zero INTEGER NOT NULL CHECK(typeof(allow_zero)='integer' AND allow_zero IN (0,1)),
 design_id TEXT COLLATE BINARY NOT NULL CHECK(typeof(design_id)='text' AND design_id='CUSTOM-0150')
);
)SQL";}
void SqliteOrdinaryMovementPolicyRepository::install_schema(sqlite3* db) {
    if(!db||!sqlite3_get_autocommit(db))
        throw DatabaseError("Movement policy fresh schema requires own transaction");
    sqlite_detail::Transaction transaction(db);
    sqlite_detail::execute(db,schema());
    transaction.commit();
}
struct SqliteOrdinaryMovementPolicyRepository::Operation {
    SqliteOrdinaryMovementPolicyRepository& source;
    const std::shared_ptr<const Lifetime> lifetime;
    explicit Operation(SqliteOrdinaryMovementPolicyRepository& owner)
        :source(owner),lifetime(owner.lifetime()) {
        if(!lifetime->available()||source.poisoned_.load(std::memory_order_acquire))
            throw DatabaseError("Movement policy repository retired");
        if(source.busy_.exchange(true,std::memory_order_acq_rel)) {
            source.poisoned_.store(true,std::memory_order_release);
            throw DatabaseError("Movement policy repository reentered");
        }
        // The busy latch serializes assignment of the first actual load owner;
        // Database construction may precede creation of the game executor.
        if(source.thread_==std::thread::id{})source.thread_=std::this_thread::get_id();
        if(source.thread_!=std::this_thread::get_id()) {
            source.poisoned_.store(true,std::memory_order_release);
            source.busy_.store(false,std::memory_order_release);
            throw DatabaseError("Movement policy repository thread mismatch");
        }
    }
    ~Operation(){source.busy_.store(false,std::memory_order_release);}
    void fence() const {
        if(!lifetime->available()||source.poisoned_.load(std::memory_order_acquire)||
           !source.busy_.load(std::memory_order_acquire)||source.thread_!=std::this_thread::get_id())
            throw DatabaseError("Movement policy repository changed during load");
    }
};
struct SqliteOrdinaryMovementPolicyRepository::ReadScope {
    Operation& operation;
    const sqlite3_int64 changes;
    bool owns=false;
    explicit ReadScope(Operation& actual):operation(actual),changes(sqlite3_total_changes64(actual.source.db_)){}
    void begin() {
        operation.fence();
        if(!sqlite3_get_autocommit(operation.source.db_))
            throw DatabaseError("Movement policy load refuses borrowed transaction");
        // Ownership is acquired only after our BEGIN succeeds. A failed BEGIN
        // cannot make destruction roll back a caller's existing transaction.
        sqlite_detail::execute(operation.source.db_,"BEGIN");owns=true;fence();
    }
    void fence() {
        if(sqlite3_get_autocommit(operation.source.db_)) {
            owns=false;throw DatabaseError("Movement policy read transaction ended");
        }
        operation.fence();
        if(sqlite3_total_changes64(operation.source.db_)!=changes)
            throw DatabaseError("Movement policy load observed same-connection write");
    }
    void finish() {
        fence();
        try {sqlite_detail::execute(operation.source.db_,"COMMIT");}
        catch(...) {if(sqlite3_get_autocommit(operation.source.db_))owns=false;throw;}
        owns=false; // A successor transaction is never ours to roll back.
        operation.fence();
        if(!sqlite3_get_autocommit(operation.source.db_)||sqlite3_total_changes64(operation.source.db_)!=changes)
            throw DatabaseError("Movement policy load changed at commit");
    }
    ~ReadScope() {
        if(owns&&!sqlite3_get_autocommit(operation.source.db_))
            sqlite3_exec(operation.source.db_,"ROLLBACK",nullptr,nullptr,nullptr);
    }
};
OrdinaryMovementPolicyRepository::Snapshot SqliteOrdinaryMovementPolicyRepository::load(std::size_t max_profiles) {
    Operation operation(*this);operation.fence();
    if(max_profiles==0||max_profiles>1024)
        throw DatabaseError("Movement policy profile bound must be explicit and within structural limit");
    ReadScope read(operation);read.begin();
    {
        sqlite_detail::Statement shadow(db_,
            "SELECT 1 FROM temp.sqlite_master WHERE name COLLATE NOCASE='movement_rules' "
            "OR tbl_name COLLATE NOCASE='movement_rules' LIMIT 1");
        read.fence();const bool present=shadow.row();read.fence();
        if(present)throw DatabaseError("Movement policy TEMP namespace shadow");
    }
    read.fence();
    {
        sqlite_detail::Statement table(db_,
            "SELECT type FROM main.sqlite_master WHERE name COLLATE NOCASE='movement_rules'");
        read.fence();const bool present=table.row();read.fence();
        if(!present||table.text(0)!="table")throw DatabaseError("Movement policy requires actual main table");
        const bool duplicate=table.row();read.fence();
        if(duplicate)throw DatabaseError("Movement policy table namespace is ambiguous");
    }
    read.fence();Snapshot result{0,{}};
    {
        sqlite_detail::Statement query(db_,
            "SELECT profile_key,config_version,step_interval_us,burst_steps,initial_credit_steps,"
            "first_sequence,block_players,forbid_corner_cut,allow_zero,design_id "
            "FROM main.movement_rules ORDER BY profile_key COLLATE BINARY");
        read.fence();
        for(;;) {
            read.fence();const bool present=query.row();read.fence();if(!present)break;
            if(result.rows.size()>=max_profiles)throw DatabaseError("Movement policy profile bound exceeded");
            auto key=query.text(0);
            if(!profile_key_valid(key)||(!result.rows.empty()&&result.rows.back().profile_key>=key))
                throw DatabaseError("Movement policy profile key is invalid or duplicated");
            const auto version=query.number<std::uint64_t>(1);
            const auto interval=query.number<std::uint32_t>(2);
            const auto burst=query.number<std::uint8_t>(3);
            const auto credit=query.number<std::uint8_t>(4);
            const auto first=query.number<std::uint8_t>(5);
            const bool players=strict_boolean(query,6),corners=strict_boolean(query,7),zero=strict_boolean(query,8);
            if(query.text(9)!="CUSTOM-0150")throw DatabaseError("Movement policy design identity mismatch");
            OwnedOrdinaryMovementPolicy policy(version,interval,burst,credit,first,players,corners,zero);
            if(!policy.valid()||version>static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()))
                throw DatabaseError("Movement policy scalar range invalid");
            if(result.rows.empty())result.version=version;
            else if(result.version!=version)throw DatabaseError("Movement policy snapshot has mixed configuration versions");
            result.rows.push_back(Row{std::move(key),policy});
        }
    }
    read.fence();
    if(result.rows.empty())throw DatabaseError("Movement policy requires explicit nonempty configuration");
    read.finish();operation.fence();return result;
}

std::string SqliteOrdinaryMovementPolicyRepository::mysql80_schema() {return R"MYSQL(
-- CUSTOM-0150; MySQL 8.0.17+ single-table source counterpart only.
-- No execution, data rows, defaults, migration, backend or activation claim.
-- Require strict SQL mode for importing exact values; never IGNORE/REPLACE
-- or disable CHECK enforcement. All rows share one config_version, validated
-- again by the whole-snapshot repository/cache (no cross-row CHECK fiction).
-- Official syntax/semantics:
-- https://dev.mysql.com/doc/refman/8.0/en/create-table-check-constraints.html
-- https://dev.mysql.com/doc/refman/8.0/en/regexp.html
-- https://dev.mysql.com/doc/refman/8.0/en/charset-binary-collations.html
CREATE TABLE movement_rules (
 profile_key VARCHAR(48) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin NOT NULL COMMENT '設定代號：小寫字母開頭，僅 ASCII 小寫字母、數字、底線',
 config_version BIGINT NOT NULL COMMENT '整批設定版本：全表一致，正數，修改時整批遞增',
 step_interval_us INT NOT NULL COMMENT '補充一步額度所需微秒，範圍 1 至 60000000',
 burst_steps TINYINT NOT NULL COMMENT '可累積步數額度上限，範圍 1 至 39',
 initial_credit_steps TINYINT NOT NULL COMMENT '新權限初始步數額度，範圍 1 至額度上限',
 first_sequence TINYINT NOT NULL COMMENT '備援政策第一個預期索引，範圍 0 至 39',
 block_players TINYINT NOT NULL COMMENT '其他人物阻擋目的格：0 關閉，1 開啟',
 forbid_corner_cut TINYINT NOT NULL COMMENT '禁止斜走穿角：0 關閉，1 開啟',
 allow_zero TINYINT NOT NULL COMMENT '允許原地步驟：0 關閉，1 開啟',
 design_id VARCHAR(11) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin NOT NULL COMMENT '自訂規則來源識別，固定 CUSTOM-0150',
 PRIMARY KEY (profile_key),
 CONSTRAINT movement_rules_profile_key_check CHECK (
  CHAR_LENGTH(profile_key) BETWEEN 1 AND 48 AND OCTET_LENGTH(profile_key)=CHAR_LENGTH(profile_key)
  AND REGEXP_LIKE(profile_key,'^[a-z]','c') AND NOT REGEXP_LIKE(profile_key,'[^a-z0-9_]','c')) ENFORCED,
 CONSTRAINT movement_rules_config_version_check CHECK (config_version BETWEEN 1 AND 9223372036854775807) ENFORCED,
 CONSTRAINT movement_rules_step_interval_check CHECK (step_interval_us BETWEEN 1 AND 60000000) ENFORCED,
 CONSTRAINT movement_rules_burst_steps_check CHECK (burst_steps BETWEEN 1 AND 39) ENFORCED,
 CONSTRAINT movement_rules_initial_credit_check CHECK (initial_credit_steps BETWEEN 1 AND burst_steps) ENFORCED,
 CONSTRAINT movement_rules_first_sequence_check CHECK (first_sequence BETWEEN 0 AND 39) ENFORCED,
 CONSTRAINT movement_rules_block_players_check CHECK (block_players IN (0,1)) ENFORCED,
 CONSTRAINT movement_rules_forbid_corner_check CHECK (forbid_corner_cut IN (0,1)) ENFORCED,
 CONSTRAINT movement_rules_allow_zero_check CHECK (allow_zero IN (0,1)) ENFORCED,
 CONSTRAINT movement_rules_design_id_check CHECK (design_id='CUSTOM-0150') ENFORCED
) ENGINE=InnoDB CHARACTER SET=utf8mb4 COLLATE=utf8mb4_0900_bin COMMENT='CUSTOM-0150 一般移動備援設定，非原廠公式或角色存檔';
)MYSQL";}
std::string SqliteOrdinaryMovementPolicyRepository::mysql80_snapshot(std::size_t max_profiles) {
    // load() returns a complete owned, checked, same-version table snapshot.
    // All SQL reads/transactions end before any export string is assembled.
    const auto snapshot=load(max_profiles);
    std::string sql=mysql80_schema();
    sql+="\nINSERT INTO movement_rules (profile_key,config_version,step_interval_us,burst_steps,"
        "initial_credit_steps,first_sequence,block_players,forbid_corner_cut,allow_zero,design_id) VALUES\n";
    bool first_row=true;
    for(const auto& row:snapshot.rows) {
        // Only the already validated ASCII identifier is quoted. No arbitrary
        // caller text, opaque bytes, SQL fragment, hexadecimal or BLOB encoding.
        if(!first_row)sql+=",\n";
        first_row=false;
        const auto& policy=row.policy;
        sql+="('"+row.profile_key+"',"+std::to_string(policy.version)+","+
            std::to_string(policy.step_interval_us)+","+std::to_string(policy.burst_steps)+","+
            std::to_string(policy.initial_credit_steps)+","+std::to_string(policy.first_sequence)+","+
            std::to_string(policy.block_players?1:0)+","+std::to_string(policy.forbid_corner_cut?1:0)+","+
            std::to_string(policy.allow_zero?1:0)+",'CUSTOM-0150')";
    }
    sql+=";\n";
    return sql;
}
}
