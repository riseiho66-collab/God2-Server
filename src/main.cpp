#include "relations53/GuildRelations53SelectorDraft.h"
#include "db/GuildSuccessionSqliteMigrationsDraft.h"
#include "db/GuildOfficerSqliteMigrations.h"
#include "core/Application.h"
#include "core/WebMainOptions.h"
#include "net/WebServerPlanConfig.h"
#include "core/TaiwanSkillImportOperator.h"
#include "core/OwnedBankCapacityOperator.h"
#include "core/Logger.h"
#include "db/SqliteDatabase.h"
#include "db/ServerSqliteMigrations.h"
#include <spdlog/spdlog.h>
#include <iostream>
#include <string>
#include <charconv>
int main(int argc,char** argv) {
    try {
        // Explicit Web mode is classified before every DB/schema/import mode.
        // Valid startup retains Application's existing DB initialization; this
        // parser/help branch never probes listeners, creates schema or guesses G.
        if(const auto web=god2::WebMainOptions::parse_if_requested(argc,argv)) {
            if(web->help){god2::WebMainOptions::write_help(std::cout);return 0;}
            const auto plan=god2::WebServerPlanConfig::load(web->web_config_path);
            const auto config=god2::Config::load(web->config_path);
            god2::validate_web_main_host(config,plan);
            god2::initialize_logger(config.log_file,config.log_level);
            return god2::run_server(config,plan,web->run_for_seconds);
        }
        if(const auto capacity=god2::OwnedBankCapacityOperator::parse_if_requested(argc,argv))
            return god2::OwnedBankCapacityOperator::run(*capacity);
        if(const auto skill_import=god2::TaiwanSkillImportOperator::parse_if_requested(argc,argv))
            return god2::TaiwanSkillImportOperator::run(*skill_import);
        std::filesystem::path path="config/server.json";
        unsigned seconds=0;
        bool migrate_only=false;
        bool native_delivery_schema=false;
        bool owned_equipment_schema=false;
        bool owned_blacklist_schema=false;
        bool run_for_supplied=false;
        for(int i=1;i<argc;++i) {
            const std::string arg=argv[i];
            if(arg=="--config" && i+1<argc) path=argv[++i];
            else if(arg=="--migrate-only") migrate_only=true;
            else if(arg=="--native-delivery-schema") native_delivery_schema=true;
            else if(arg=="--owned-equipment-schema") owned_equipment_schema=true;
            else if(arg=="--owned-blacklist-schema") owned_blacklist_schema=true;
            else if(arg=="--run-for" && i+1<argc) {
                run_for_supplied=true;
                const std::string value=argv[++i];
                const auto parsed=std::from_chars(value.data(),value.data()+value.size(),seconds);
                if(parsed.ec!=std::errc{} || parsed.ptr!=value.data()+value.size())
                    throw std::runtime_error("--run-for requires an unsigned integer number of seconds");
            }
            else if(arg=="--help") {
                std::cout<<"god2-server [--config config/server.json] [--run-for seconds] [--migrate-only] [--native-delivery-schema | --owned-equipment-schema | --owned-blacklist-schema]\n"
                    "--migrate-only: apply SQLite migrations without starting networking or Lua.\n"
                    "--native-delivery-schema: schema-only opt-in for 3 native delivery snapshot tables; requires --migrate-only, forbids any --run-for (including 0).\n"
                    "  account_native_snapshots, account_native_character_summaries, account_native_character_summary_rows.\n"
                    "  No networking, Lua, native data import, rights or login/gameplay activation.\n"
                    "--owned-equipment-schema: fresh schema-only opt-in for 4 shared owned-item tables and 1 native equipment witness table.\n"
                    "  Requires --migrate-only, forbids any --run-for (including 0), and is mutually exclusive with --native-delivery-schema.\n"
                    "  Creates all 5 tables in one transaction; existing feature tables cause failure. No item grants, import or gameplay activation.\n";
                std::cout<<"--owned-blacklist-schema: fresh CUSTOM-0096 storage only; requires --migrate-only, forbids any --run-for; mutually exclusive with other schema flags. No population or gameplay activation.\n";
                god2::WebMainOptions::write_help(std::cout);
                god2::TaiwanSkillImportOperator::write_help(std::cout);
                god2::OwnedBankCapacityOperator::write_help(std::cout);
                return 0;
            }
            else throw std::runtime_error("Invalid command line; use --help");
        }
        if(unsigned(native_delivery_schema)+unsigned(owned_equipment_schema)+unsigned(owned_blacklist_schema)>1)
            throw std::runtime_error("Schema installation flags are mutually exclusive");
        if(owned_blacklist_schema) {
            if(!migrate_only)throw std::runtime_error("--owned-blacklist-schema requires --migrate-only");
            if(run_for_supplied)throw std::runtime_error("--owned-blacklist-schema forbids any --run-for, including 0");
        }
        if(owned_equipment_schema) {
            if(!migrate_only)throw std::runtime_error("--owned-equipment-schema requires --migrate-only");
            if(run_for_supplied)throw std::runtime_error("--owned-equipment-schema cannot be combined with any --run-for, including 0");
        }
        if(native_delivery_schema) {
            if(!migrate_only)throw std::runtime_error("--native-delivery-schema requires --migrate-only");
            if(run_for_supplied)throw std::runtime_error("--native-delivery-schema cannot be combined with any --run-for, including 0");
        }
        const auto config=god2::Config::load(path);
        if(migrate_only) {
            if(seconds!=0) throw std::runtime_error("--migrate-only cannot be combined with --run-for");
            god2::SqliteDatabase database(config.database,god2::configured_guild_relations53(
                config.database,{config.owned_guild_membership_enabled,config.owned_guild_announcements_enabled,config.owned_guild_officers_enabled,config.owned_guild_succession_enabled,config.owned_guild_relations53_enabled}));
            database.initialize();
            database.migrate();
            if(native_delivery_schema) {
                database.install_native_delivery_snapshot_schema();
                std::cout<<"Native delivery snapshot schema installation/qualification complete (3 tables; storage only; no native data, rights or login/gameplay activation)\n";
            }
            if(owned_equipment_schema) {
                database.install_owned_equipment_schema();
                std::cout<<"Owned equipment schema installation complete (5 fresh tables in one transaction; storage only; no item grants, import or gameplay activation)\n";
            }
            if(owned_blacklist_schema) {
                database.install_owned_blacklist_schema();
                std::cout<<"Owned blacklist fresh schema installed (storage only; no population or gameplay activation)\n";
            }
            std::cout<<"SQLite migrations complete\n";
            return 0;
        }
        god2::initialize_logger(config.log_file,config.log_level);
        return god2::run_server(config,seconds);
    } catch(const std::exception& e) { std::cerr<<"GOD2 startup/runtime error: "<<e.what()<<'\n'; return 1; }
}
