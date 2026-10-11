#include "core/Config.h"
#include "handlers/OwnedGuildAnnouncementBatch.h"
#include <nlohmann/json.hpp>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <source_location>
#include <stdexcept>
namespace {
using namespace god2;
using Bytes=std::vector<std::uint8_t>;
using W=RecoveredWorldRecords;
using A=RecoveredGuildAnnouncement;
unsigned checks=0;
void check(bool value,const std::source_location at=std::source_location::current()) {
    ++checks;if(!value)throw std::runtime_error("Announcement world check at "+std::to_string(at.line()));
}
Bytes joined(Bytes a,const Bytes& b){a.insert(a.end(),b.begin(),b.end());return a;}
void rejects(const Bytes& raw) {
    check(!W::decode(raw));check(!W::decode(joined({0x30,0},raw)));
}
void batches() {
    const Bytes chat{0x2f,9,0,0,0,0,0,'x',0};
    const Bytes help{0x37,0x7b,8,0,0};
    const auto text=A::text_request("公告 100%",950);
    const auto encoded=*A::encode_request(text);
    for(const auto page:{950,936}) {
        const auto request=A::text_request("公告 100%",page);
        const auto raw=*A::encode_request(request);
        const auto records=W::decode(joined(raw,chat));check(records && records->size()==2);
        check(std::get<A::Request>(records->front())==request);
        const auto* common=std::get_if<RecoveredChat::Request>(&records->back());check(common && common->legacy_text=="x");
        check(!OwnedGuildAnnouncementBatch::save_only(*records));
        check(!OwnedGuildAnnouncementBatch::opener_only(*records));
        check(A::text_utf8(request,page)=="公告 100%");
    }
    const auto simple=W::decode(joined({0x30,0},encoded));check(simple && simple->size()==2);
    check(OwnedGuildAnnouncementBatch::save_only(*simple));
    for(const auto& prefix:std::vector<Bytes>{help,{0x71,1},{0x72,1},{0x73,0},chat}) {
        const auto batch=W::decode(joined(prefix,encoded));check(bool(batch));
        check(!OwnedGuildAnnouncementBatch::save_only(*batch));
        check(!OwnedGuildAnnouncementBatch::opener_only(*batch));
        const auto suffix=W::decode(joined(encoded,prefix));check(bool(suffix));
        check(!OwnedGuildAnnouncementBatch::save_only(*suffix));
    }
    const auto opening=W::decode(joined(help,{0x30,0}));check(bool(opening));
    check(OwnedGuildAnnouncementBatch::opener_only(*opening));check(!OwnedGuildAnnouncementBatch::save_only(*opening));
    const auto maximum=*A::encode_request({Bytes(1040,'q')});check(maximum.size()==1044);
    const auto maxbatch=W::decode(joined(maximum,{0x30,0}));check(maxbatch && maxbatch->size()==2);
    check(std::get<A::Request>(maxbatch->front()).text.size()==1040);
    const auto clear=W::decode(Bytes{0x79,4,0,0});check(clear && std::get<A::Request>(clear->front()).text.empty());
    const auto duplicates=W::decode(joined(encoded,encoded));check(duplicates && duplicates->size()==2);
    check(OwnedGuildAnnouncementBatch::save_only(*duplicates)); // authorization remains single-use in service tests.
    for(const auto& raw:std::vector<Bytes>{{0x79},{0x79,4},{0x79,4,0},{0x79,0,0,0},{0x79,3,0,0},{0x79,5,0,0},
        {0x79,4,0,'x'},{0x79,6,0,'x',0,0},joined(maximum,{0xff})})rejects(raw);
    for(unsigned size=0;size<=65535;++size) {
        if(size==4)continue;
        rejects({0x79,static_cast<std::uint8_t>(size),static_cast<std::uint8_t>(size>>8),0});
    }
    auto partial=encoded;partial.pop_back();check(!W::decode(joined(chat,partial)));
    auto nul=encoded;nul[3]=0;check(!W::decode(joined(chat,nul)));
    for(std::size_t i=1;i<maximum.size();++i)
        check(!W::decode(joined(chat,Bytes(maximum.begin(),maximum.begin()+i))));
}
void config() {
    const auto temp=std::filesystem::canonical(std::filesystem::temp_directory_path());
    const auto path=temp/("god2-announcement-config-"+std::to_string(std::chrono::steady_clock::now().time_since_epoch().count())+".json");
    check(!std::filesystem::exists(path));
    struct Cleanup{std::filesystem::path path;~Cleanup(){std::error_code e;std::filesystem::remove(path,e);}} cleanup{path};
    std::ifstream input(std::filesystem::path(GOD2_SOURCE_DIR)/"artifacts/releases/town-chat-welcome-20260924/server-config.json");
    check(bool(input));const auto base=nlohmann::json::parse(input);
    const auto load=[&](const nlohmann::json& value){std::ofstream f(path,std::ios::binary);f<<value.dump();f.close();return Config::load(path);};
    auto value=base;value["world"].erase("owned_guild_announcements");check(!load(value).owned_guild_announcements_enabled);
    value["world"]["owned_guild_announcements"]={{"enabled",true}};check(load(value).owned_guild_announcements_enabled);
    const auto rejected=[&](const nlohmann::json& v){bool failed=false;try{load(v);}catch(const std::exception&){failed=true;}check(failed);};
    auto missing=value;missing["world"].erase("owned_guild_membership");rejected(missing);
    auto disabled=value;disabled["world"]["owned_guild_membership"]["enabled"]=false;rejected(disabled);
    for(const auto& wrong:nlohmann::json::array({true,1,"enabled",nullptr,nlohmann::json::array(),nlohmann::json::object(),nlohmann::json{{"enabled",1}}})) {
        auto bad=base;bad["world"]["owned_guild_announcements"]=wrong;rejected(bad);
    }
    value["world"]["owned_guild_announcements"]["enabled"]=false;check(!load(value).owned_guild_announcements_enabled);
}
}
int main(){try{batches();config();std::cout<<checks<<" announcement grammar/batch/config checks PASS; no live-client claim\n";return 0;}
catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
