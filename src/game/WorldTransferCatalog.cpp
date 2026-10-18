#include "game/WorldTransferCatalog.h"
#include <array>
#include <fstream>
#include <nlohmann/json.hpp>
#include <stdexcept>
#ifdef _WIN32
#include <windows.h>
#include <bcrypt.h>
#endif

namespace god2 {
namespace {
void require(bool ok){if(!ok)throw std::invalid_argument("World transfer catalog source/structure mismatch");}
int number(const nlohmann::json& j,int high){require(j.is_number_integer());const auto n=j.get<std::int64_t>();require(n>=0&&n<=high);return static_cast<int>(n);}
std::string read(const std::filesystem::path& path,std::size_t maximum) {
    std::ifstream file(path,std::ios::binary);if(!file)throw std::invalid_argument("World transfer input unavailable");
    file.seekg(0,std::ios::end);const auto size=file.tellg();
    require(size>0&&static_cast<std::uint64_t>(size)<=maximum);file.seekg(0,std::ios::beg);
    std::string bytes(static_cast<std::size_t>(size),'\0');file.read(bytes.data(),static_cast<std::streamsize>(bytes.size()));
    require(!file.bad()&&static_cast<std::size_t>(file.gcount())==bytes.size()&&file.peek()==std::char_traits<char>::eof());return bytes;
}
std::string sha256(const std::string& bytes) {
#ifdef _WIN32
    BCRYPT_ALG_HANDLE algorithm=nullptr;BCRYPT_HASH_HANDLE hash=nullptr;std::array<unsigned char,32> digest{};
    auto status=BCryptOpenAlgorithmProvider(&algorithm,BCRYPT_SHA256_ALGORITHM,MS_PRIMITIVE_PROVIDER,0);
    if(BCRYPT_SUCCESS(status))status=BCryptCreateHash(algorithm,&hash,nullptr,0,nullptr,0,0);
    if(BCRYPT_SUCCESS(status))status=BCryptHashData(hash,reinterpret_cast<PUCHAR>(const_cast<char*>(bytes.data())),static_cast<ULONG>(bytes.size()),0);
    if(BCRYPT_SUCCESS(status))status=BCryptFinishHash(hash,digest.data(),static_cast<ULONG>(digest.size()),0);
    const auto destroyed=hash?BCryptDestroyHash(hash):0;const auto closed=algorithm?BCryptCloseAlgorithmProvider(algorithm,0):0;
    if(!BCRYPT_SUCCESS(status)||!BCRYPT_SUCCESS(destroyed)||!BCRYPT_SUCCESS(closed))throw std::runtime_error("World transfer SHA256 failed");
    std::string out;for(auto byte:digest){out+="0123456789abcdef"[byte>>4];out+="0123456789abcdef"[byte&15];}return out;
#else
    (void)bytes;throw std::runtime_error("World transfer catalog requires qualified SHA256 backend");
#endif
}
WorldTransferCatalog::SceneKey key(const nlohmann::json& row,const char* area,const char* scene) {
    auto a=static_cast<std::uint16_t>(number(row.at(area),16));require(a>0);
    return {a,static_cast<std::uint16_t>(number(row.at(scene),1023))};
}
WorldTransferCatalog::Point point(const nlohmann::json& row,const char* area,const char* scene,const char* x,const char* y) {
    return {key(row,area,scene),static_cast<std::uint16_t>(number(row.at(x),0x3fff)),static_cast<std::uint16_t>(number(row.at(y),0x7fff))};
}
}
WorldTransferCatalog::WorldTransferCatalog(const std::filesystem::path& path) {
    const auto bytes=read(path,64*1024*1024);
    require(sha256(bytes)=="0146feeb50d96a99ca5a494900b652b010532295f6f64e4da8addfbb22561c53");
    const auto j=nlohmann::json::parse(bytes);
    require(j.at("schema")=="god2-tw-world-transfer-catalog-v1"&&j.at("custom_design")=="CUSTOM-0155");
    const auto& rows=j.at("scenes");require(rows.is_array()&&!rows.empty()&&rows.size()<=2048);
    std::size_t total_cells=0;
    for(const auto& row:rows) {
        const auto identity=key(row,"area","scene");
        const auto width=static_cast<std::uint16_t>(number(row.at("width"),2048));
        const auto height=static_cast<std::uint16_t>(number(row.at("height"),2048));require(width&&height);
        const auto kind=static_cast<std::uint16_t>(number(row.at("kind"),3));
        const auto expected=row.at("grid_sha256").get<std::string>();require(expected.size()==64);
        const auto relative=std::filesystem::path(row.at("grid_file").get<std::string>());
        require(!relative.empty()&&!relative.is_absolute()&&!relative.has_root_name()&&!relative.has_root_directory());for(const auto& part:relative)require(part!=".."&&part!=".");
        const auto source=read(path.parent_path()/relative,9*1024*1024);require(sha256(source)==expected);
        const auto grid=nlohmann::json::parse(source);
        require(grid.at("schema")=="god2-tw-world-mask-v1"&&grid.at("width")==width&&grid.at("height")==height&&
            grid.at("dynamic_occupancy_included")==false);
        const auto encoded=grid.at("masks_hex").get<std::string>();
        const auto count=static_cast<std::size_t>(width)*height;require(encoded.size()==count*2);
        total_cells+=count;require(total_cells<=128*1024*1024);
        Grid value{{identity,kind,width,height,expected},{}};value.masks.reserve(count);
        for(std::size_t i=0;i<count;++i){require(encoded[2*i]=='0'&&encoded[2*i+1]>='0'&&encoded[2*i+1]<='7');value.masks.push_back(static_cast<std::uint8_t>(encoded[2*i+1]-'0'));}
        scene_definitions_.push_back(value.definition);
        require(scenes_.emplace(std::pair{identity.area,identity.scene},std::move(value)).second);
    }
    const auto& exceptions=j.at("exceptions");require(exceptions.is_array()&&exceptions.size()<=1024);
    for(const auto& row:exceptions) {
        const auto p=point(row,"area","scene","x","y");const auto mask=number(row.at("observed_mask"),7);
        require(mask==6&&observed_mask(p)==6&&!row.at("custom_design").get<std::string>().empty());
        require(exceptions_.emplace(std::array{p.scene.area,p.scene.scene,p.x,p.y},6).second);
    }
    const auto& routes=j.at("routes");require(routes.is_array()&&routes.size()<=65536);
    for(const auto& row:routes) {
        auto id=row.at("id").get<std::string>();require(!id.empty()&&id.size()<=256);
        const auto type=row.at("trigger").get<std::string>();
        const auto trigger=type=="displaced_point"?Trigger::DisplacedPoint:type=="directed_step"?Trigger::DirectedStep:Trigger::NpcOffer;
        require(type=="displaced_point"||type=="directed_step"||type=="npc_offer");
        const auto source=point(row,"source_area","source_scene","source_x","source_y");
        const auto target=point(row,"target_area","target_scene","target_x","target_y");
        const auto approach=static_cast<std::uint8_t>(number(row.at("approach_mask"),255));
        require(scene(source.scene)&&available(target));
        if(trigger!=Trigger::NpcOffer)require(approach&&available(source));
        const auto ordinal=routes_.size();require(route_ids_.emplace(id,ordinal).second);
        if(trigger!=Trigger::NpcOffer)require(point_routes_.emplace(std::array{source.scene.area,source.scene.scene,source.x,source.y},ordinal).second);
        routes_.push_back({std::move(id),trigger,source,target,approach});
    }
}
const WorldTransferCatalog::Scene* WorldTransferCatalog::scene(SceneKey key) const noexcept {
    const auto found=scenes_.find({key.area,key.scene});return found==scenes_.end()?nullptr:&found->second.definition;
}
std::optional<std::uint8_t> WorldTransferCatalog::observed_mask(Point p) const noexcept {
    const auto found=scenes_.find({p.scene.area,p.scene.scene});if(found==scenes_.end())return std::nullopt;
    const auto& grid=found->second;if(p.x>=grid.definition.width||p.y>=grid.definition.height)return std::nullopt;
    return grid.masks[static_cast<std::size_t>(p.y)*grid.definition.width+p.x];
}
bool WorldTransferCatalog::available(Point p) const noexcept {
    const auto mask=observed_mask(p);if(!mask)return false;if(*mask==2||*mask==4)return true;
    const auto found=exceptions_.find({p.scene.area,p.scene.scene,p.x,p.y});return found!=exceptions_.end()&&*mask==found->second;
}
const WorldTransferCatalog::Route* WorldTransferCatalog::route(std::string_view id) const noexcept {
    const auto found=route_ids_.find(id);return found==route_ids_.end()?nullptr:&routes_[found->second];
}
const WorldTransferCatalog::Route* WorldTransferCatalog::route_for_step(SceneKey key,std::uint16_t before_x,std::uint16_t before_y,std::uint16_t x,std::uint16_t y) const noexcept {
    const int dx=int(before_x)-x,dy=int(before_y)-y;if((!dx&&!dy)||dx<-1||dx>1||dy<-1||dy>1)return nullptr;
    const auto found=point_routes_.find({key.area,key.scene,x,y});if(found==point_routes_.end())return nullptr;
    const unsigned index=static_cast<unsigned>((dy+1)*3+dx+1);const auto bit=index<4?index:index-1;
    const auto& route=routes_[found->second];return route.approach_mask&(1u<<bit)?&route:nullptr;
}
}
