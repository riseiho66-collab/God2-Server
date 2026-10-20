#include "core/OwnedBankCapacityOperator.h"
#include "db/SqliteDatabase.h"
#include <nlohmann/json.hpp>
#include <algorithm>
#include <charconv>
#include <fstream>
#include <iostream>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>
#ifdef _WIN32
#include <windows.h>
#include <shellapi.h>
#else
#include <fcntl.h>
#include <unistd.h>
#endif
namespace god2 {
namespace {
#ifdef _WIN32
using Arg=std::wstring;
std::vector<Arg> arguments(int argc,char**) {
    int count=0;struct End{LPWSTR* value=nullptr;~End(){if(value)LocalFree(value);}} end;
    end.value=CommandLineToArgvW(GetCommandLineW(),&count);
    if(!end.value||count!=argc)throw std::runtime_error("Cannot retain actual Windows capacity arguments");
    return {end.value,end.value+count};
}
#else
using Arg=std::string;
std::vector<Arg> arguments(int argc,char** argv){return {argv,argv+argc};}
#endif
std::string ascii(const Arg& value) {
    std::string out;for(const auto c:value){if(c<0||c>127)return {};out.push_back(static_cast<char>(c));}return out;
}
std::uint64_t id(const Arg& value) {
    const auto text=ascii(value);std::uint64_t result=0;
    const auto parsed=std::from_chars(text.data(),text.data()+text.size(),result);
    if(text.empty()||!result||parsed.ec!=std::errc{}||parsed.ptr!=text.data()+text.size()||result>0x7fffffffffffffffULL)
        throw std::runtime_error("Capacity owner requires a positive common64 integer");
    return result;
}
std::string read(const std::filesystem::path& path) {
    std::ifstream in(path,std::ios::binary|std::ios::ate);
    if(!in)throw std::runtime_error("Cannot read capacity input");
    const auto size=in.tellg();if(size<=0||size>64*1024*1024)throw std::runtime_error("Capacity input exceeds bounded file size");
    std::string result(static_cast<std::size_t>(size),'\0');in.seekg(0);in.read(result.data(),static_cast<std::streamsize>(result.size()));
    if(!in||in.peek()!=std::char_traits<char>::eof())throw std::runtime_error("Capacity input changed during bounded read");
    return result;
}
std::filesystem::path configured_database(const std::filesystem::path& path) {
    const auto config=nlohmann::json::parse(read(path));const auto& database=config.at("database");
    if(!database.is_object()||database.at("type")!="sqlite"||!database.at("path").is_string())
        throw std::runtime_error("Capacity requires an explicit existing SQLite configuration");
    const auto value=database.at("path").get<std::string>();
    if(value.empty()||value.find('\0')!=std::string::npos)throw std::runtime_error("Invalid capacity database path");
    return (std::filesystem::absolute(path).parent_path().parent_path()/std::filesystem::u8path(value)).lexically_normal();
}
void write_new(const std::filesystem::path& path,const std::string& bytes) {
#ifdef _WIN32
    struct End{HANDLE value=INVALID_HANDLE_VALUE;~End(){if(value!=INVALID_HANDLE_VALUE)CloseHandle(value);}} end;
    end.value=CreateFileW(path.c_str(),GENERIC_WRITE,0,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);
    if(end.value==INVALID_HANDLE_VALUE)throw std::runtime_error("Capacity draft output must be a new file");
    std::size_t offset=0;
    while(offset<bytes.size()) {DWORD count=0;const auto part=static_cast<DWORD>((std::min)(bytes.size()-offset,std::size_t(1024*1024)));
        if(!WriteFile(end.value,bytes.data()+offset,part,&count,nullptr)||count!=part)throw std::runtime_error("Capacity draft write failed; partial file retained");offset+=count;}
    if(!FlushFileBuffers(end.value))throw std::runtime_error("Capacity draft flush failed; file retained");
#else
    struct End{int value=-1;~End(){if(value>=0)close(value);}} end;
    end.value=open(path.c_str(),O_WRONLY|O_CREAT|O_EXCL|O_CLOEXEC,0600);
    if(end.value<0)throw std::runtime_error("Capacity draft output must be a new file");
    std::size_t offset=0;while(offset<bytes.size()){const auto count=write(end.value,bytes.data()+offset,bytes.size()-offset);
        if(count<=0)throw std::runtime_error("Capacity draft write failed; partial file retained");offset+=static_cast<std::size_t>(count);}
    if(fsync(end.value))throw std::runtime_error("Capacity draft flush failed; file retained");
#endif
}
}
std::optional<OwnedBankCapacityOperator::Options> OwnedBankCapacityOperator::parse_if_requested(int argc,char** argv) {
    if(argc<1||!argv)throw std::runtime_error("Invalid capacity process arguments");
    bool requested=false;
    for(int i=1;i<argc;++i) {
        if(!argv[i])throw std::runtime_error("Invalid capacity argument");const std::string arg=argv[i];
        if(arg=="--config"||arg=="--run-for"||arg=="--tw-client-root"||arg=="--manifest"||arg=="--output"||arg=="--account-id"||arg=="--character-id") {if(i+1<argc)++i;continue;}
        if(arg=="--help"&&!requested)return std::nullopt;
        if(arg=="--provision-owned-bank-capacity"||arg=="--export-owned-bank-capacity")requested=true;
    }
    if(!requested)return std::nullopt;
    const auto args=arguments(argc,argv);Options result;std::set<std::string> seen;bool mode=false;
    for(std::size_t i=1;i<args.size();++i) {
        const auto arg=ascii(args[i]);if(arg.empty()||!seen.insert(arg).second)throw std::runtime_error("Invalid or duplicate capacity option");
        if(arg=="--provision-owned-bank-capacity"||arg=="--export-owned-bank-capacity") {
            if(mode)throw std::runtime_error("Capacity modes are exclusive");mode=true;result.provision=arg=="--provision-owned-bank-capacity";
        } else if(arg=="--help")result.help=true;
        else if(arg=="--config"||arg=="--manifest"||arg=="--output"||arg=="--account-id"||arg=="--character-id") {
            if(++i>=args.size()||args[i].empty()||(args[i].size()>=2&&args[i][0]=='-'&&args[i][1]=='-'))
                throw std::runtime_error("Capacity option requires an explicit value");
            if(arg=="--account-id")result.account=id(args[i]);else if(arg=="--character-id")result.character=id(args[i]);
            else {const std::filesystem::path value(args[i]);
                if(arg=="--config")result.config_path=value;else if(arg=="--manifest")result.manifest_path=value;else result.output_path=value;}
        } else throw std::runtime_error("Capacity operation is exclusive with all gameplay/migration/import options");
    }
    if(!result.help&&((result.provision&&(result.manifest_path.empty()||!result.output_path.empty()||result.account||result.character))||
       (!result.provision&&(result.output_path.empty()||!result.account||!result.character||!result.manifest_path.empty()))))
        throw std::runtime_error("Incomplete/extraneous capacity mode options; use --help");
    return result;
}
void OwnedBankCapacityOperator::write_help(std::ostream& out) {
    out<<"--export-owned-bank-capacity --account-id N --character-id N --output <new JSON> [--config path]\n"
        "--provision-owned-bank-capacity --manifest <approved JSON> [--config path]\n"
        "  CUSTOM-0163 existing full0092 material only; explicit empty bank cells, no item/initial material/native unlock grants.\n"
        "  Both modes require all current server/import processes for this actual DB to be stopped. Exclusive with other modes.\n"
        "  Draft has approved=false and no requested cells. Review/edit exact English fields before explicit provision.\n";
}
int OwnedBankCapacityOperator::run(const Options& options) {
    if(options.help){write_help(std::cout);return 0;}
    // Freeze/validate all supplied manifest bytes before ANY database/SQL.
    std::optional<nlohmann::json> manifest;
    if(options.provision)manifest=OwnedBankCapacityProvision::parse(read(options.manifest_path));
    SqliteDatabase database(configured_database(options.config_path),std::vector<Migration>{});
    database.initialize_existing_for_owned_bank_capacity();
    if(!options.provision) {
        const auto bytes=database.owned_bank_capacity_draft(options.account,options.character).dump(2)+"\n";
        if(bytes.size()>64u*1024u*1024u)throw std::runtime_error("Complete capacity draft exceeds supported manifest bound; no output written");
        write_new(options.output_path,bytes);
        std::cout<<"Wrote unapproved CUSTOM-0163 full-before draft; no cells/items changed.\n";return 0;
    }
    const auto outcome=database.provision_owned_bank_capacity(*manifest);
    if(!outcome.commit_confirmed){std::cerr<<"Capacity has no confirmed COMMIT; no retry performed.\n";return 2;}
    if(!outcome.connection_current){std::cerr<<"Capacity COMMIT confirmed; later qualification failed. Do not replay this manifest.\n";return 2;}
    std::cout<<"CUSTOM-0163 explicitly enumerated empty bank cells committed; existing items/native witness retained.\n";
    return 0; // Never continue into migrations/logger/Lua/network.
}
}
