#include "core/TaiwanSkillImportOperator.h"
#include "db/TaiwanInstalledSkillCatalogFileSource.h"
#include "db/SqliteDatabase.h"
#include <nlohmann/json.hpp>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>
#ifdef _WIN32
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <shellapi.h>
#endif
namespace god2 {
namespace {
#ifdef _WIN32
using Argument=std::wstring;
std::vector<Argument> native_arguments(int argc,char**) {
    int count=0;
    struct Arguments {
        LPWSTR* value=nullptr;
        ~Arguments(){if(value)LocalFree(reinterpret_cast<HLOCAL>(value));}
    } arguments;
    arguments.value=CommandLineToArgvW(GetCommandLineW(),&count);
    if(!arguments.value || count!=argc || count<1)
        throw std::runtime_error("Cannot retain actual Windows import arguments");
    std::vector<Argument> result;result.reserve(static_cast<std::size_t>(count));
    for(int i=0;i<count;++i)result.emplace_back(arguments.value[i]);
    return result;
}
#else
using Argument=std::string;
std::vector<Argument> native_arguments(int argc,char** argv) {
    std::vector<Argument> result;result.reserve(static_cast<std::size_t>(argc));
    for(int i=0;i<argc;++i)result.emplace_back(argv[i]);return result;
}
#endif
bool option(const Argument& value,std::string_view expected) noexcept {
    if(value.size()!=expected.size())return false;
    for(std::size_t i=0;i<value.size();++i)
        if(value[i]!=static_cast<Argument::value_type>(static_cast<unsigned char>(expected[i])))return false;
    return true;
}
std::filesystem::path configured_existing_database(const std::filesystem::path& path) {
    std::ifstream stream(path);
    if(!stream)throw std::runtime_error("Cannot open import configuration");
    const auto config=nlohmann::json::parse(stream);
    const auto& database=config.at("database");
    if(!database.is_object() || database.at("type")!="sqlite" || !database.at("path").is_string())
        throw std::runtime_error("Import configuration requires SQLite database path");
    const auto value=database.at("path").get<std::string>();
    if(value.empty() || value.find(char(0))!=std::string::npos)
        throw std::runtime_error("Invalid import database path");
    // JSON paths are UTF-8; preserve native Windows Unicode without ACP/CP950
    // reinterpretation. The project-root rule is the existing Config rule.
    std::u8string encoded;encoded.reserve(value.size());
    for(const unsigned char byte:value)encoded.push_back(static_cast<char8_t>(byte));
    const std::filesystem::path native(encoded);
    const auto root=std::filesystem::absolute(path).parent_path().parent_path();
    return (root/native).lexically_normal();
}
}
std::optional<TaiwanSkillImportOperator::Options> TaiwanSkillImportOperator::parse_if_requested(
    int argc,char** argv) {
    if(argc<1 || !argv)throw std::runtime_error("Invalid process arguments");
    bool requested=false;
    for(int i=1;i<argc;++i) {
        if(!argv[i])throw std::runtime_error("Invalid process argument");
        const std::string_view arg(argv[i]);
        // Match legacy value consumption before interpreting any opt-in token.
        // A configuration filename may itself spell the new option exactly.
        if((arg=="--config" || arg=="--run-for") && i+1<argc) {
            if(!argv[++i])throw std::runtime_error("Invalid process argument");
            continue;
        }
        if(arg=="--help" && !requested)return std::nullopt;
        if(arg=="--import-tw-installed-skills")requested=true;
    }
    if(!requested)return std::nullopt;
    const auto arguments=native_arguments(argc,argv);
    Options result;bool import_seen=false,root_seen=false,config_seen=false;
    for(std::size_t i=1;i<arguments.size();++i) {
        const auto& arg=arguments[i];
        if(option(arg,"--import-tw-installed-skills")) {
            if(import_seen)throw std::runtime_error("Duplicate skill import flag");import_seen=true;
        } else if(option(arg,"--help"))result.help=true;
        else if(option(arg,"--tw-client-root") || option(arg,"--config")) {
            const bool root=option(arg,"--tw-client-root");
            if((root&&root_seen)||(!root&&config_seen))throw std::runtime_error("Duplicate import path option");
            if(++i>=arguments.size() || arguments[i].empty() ||
               (arguments[i].size()>=2 && arguments[i][0]=='-' && arguments[i][1]=='-'))
                throw std::runtime_error("Import path option requires a value");
            const std::filesystem::path value(arguments[i]);
            if(value.native().find(std::filesystem::path::value_type(0))!=std::filesystem::path::string_type::npos)
                throw std::runtime_error("Import path contains NUL");
            if(root){result.client_root=value;root_seen=true;}
            else {result.config_path=value;config_seen=true;}
        } else {
            // Reject every migration/schema/run-for/unknown combination before
            // any file read, guild selector, database or gameplay owner exists.
            throw std::runtime_error("Skill import is exclusive; use --help for its options");
        }
    }
    if(!import_seen || (!root_seen&&!result.help))
        throw std::runtime_error("Skill import requires --tw-client-root");
    return result;
}
void TaiwanSkillImportOperator::write_help(std::ostream& out) {
    out<<"--import-tw-installed-skills --tw-client-root <existing TW client root> [--config config/server.json]\n"
        "  Verify the pinned installed453 BIN before opening an existing SQLite database; import definitions then exit.\n"
        "  Exclusive with migration/schema/run-for flags. No database creation, schema installation, profile change or skill grants.\n";
}
int TaiwanSkillImportOperator::run(const Options& options) {
    if(options.help){write_help(std::cout);return 0;}
    // The actual file producer owns and pins ALL bytes before ANY DB/SQL.
    const auto source=TaiwanInstalledSkillCatalogFileSource::read_client_root(options.client_root);
    const auto database_path=configured_existing_database(options.config_path);
    // No guild-version selector or migration/game owner construction is used.
    SqliteDatabase database(database_path,std::vector<Migration>{});
    database.initialize_existing_for_taiwan_skill_import();
    const auto outcome=database.import_taiwan_installed_skill_catalog(source);
    if(!outcome.commit_confirmed) {
        std::cerr<<"Skill import has no confirmed local COMMIT. No retry performed.\n";return 2;
    }
    if(!outcome.connection_current) {
        std::cerr<<"Skill import local COMMIT confirmed; subsequent connection qualification failed. No retry performed.\n";return 2;
    }
    std::cout<<(outcome.result==TaiwanInstalledSkillCatalogImport::Result::Inserted?
        "Inserted pinned TW 453 catalog into existing SQLite database.\n":
        "Pinned TW 453 catalog already matches existing SQLite database.\n");
    return 0; // Never continue into logger/Lua/network hosting after import.
}
}
