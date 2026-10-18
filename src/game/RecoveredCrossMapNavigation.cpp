#include "game/RecoveredCrossMapNavigation.h"
#include <algorithm>
#include <array>
#include <fstream>
#include <nlohmann/json.hpp>
#include <set>
#include <stdexcept>
#ifdef _WIN32
#include <windows.h>
#include <bcrypt.h>
#endif

namespace god2 {
namespace {
void require(bool value) {if(!value)throw std::invalid_argument("Cross-map navigation source/structure mismatch");}
int number(const nlohmann::json& j,int maximum) {
    require(j.is_number_integer());
    const auto value=j.get<std::int64_t>();require(value>=0 && value<=maximum);return static_cast<int>(value);
}
void verify(const std::string& bytes) {
#ifdef _WIN32
    BCRYPT_ALG_HANDLE algorithm=nullptr;BCRYPT_HASH_HANDLE hash=nullptr;
    std::array<unsigned char,32> digest{};
    auto status=BCryptOpenAlgorithmProvider(&algorithm,BCRYPT_SHA256_ALGORITHM,MS_PRIMITIVE_PROVIDER,0);
    if(BCRYPT_SUCCESS(status))status=BCryptCreateHash(algorithm,&hash,nullptr,0,nullptr,0,0);
    if(BCRYPT_SUCCESS(status))status=BCryptHashData(hash,reinterpret_cast<PUCHAR>(const_cast<char*>(bytes.data())),static_cast<ULONG>(bytes.size()),0);
    if(BCRYPT_SUCCESS(status))status=BCryptFinishHash(hash,digest.data(),static_cast<ULONG>(digest.size()),0);
    const auto destroyed=hash?BCryptDestroyHash(hash):0;
    const auto closed=algorithm?BCryptCloseAlgorithmProvider(algorithm,0):0;
    if(!BCRYPT_SUCCESS(status)||!BCRYPT_SUCCESS(destroyed)||!BCRYPT_SUCCESS(closed))throw std::runtime_error("Cross-map navigation SHA256 failed");
    std::string actual;for(auto byte:digest){actual+="0123456789abcdef"[byte>>4];actual+="0123456789abcdef"[byte&15];}
    require(actual=="ab8364ffb02a762383f9becd4721bad85673c4b8f49b3da42e042b17ad819b57");
#else
    (void)bytes;throw std::runtime_error("Cross-map navigation requires qualified SHA256 backend");
#endif
}
}
RecoveredCrossMapNavigation::RecoveredCrossMapNavigation(const std::filesystem::path& path) {
    std::ifstream file(path,std::ios::binary);if(!file)throw std::invalid_argument("Cross-map navigation unavailable");
    constexpr std::size_t limit=20*1024*1024;
    std::string bytes(limit+1,'\0');file.read(bytes.data(),static_cast<std::streamsize>(bytes.size()));
    require(!file.bad() && file.gcount()>0 && static_cast<std::size_t>(file.gcount())<=limit);
    bytes.resize(static_cast<std::size_t>(file.gcount()));verify(bytes);
    const auto j=nlohmann::json::parse(bytes);
    require(j.at("schema")=="god2-tw-cross-map-navigation-v1" && j.at("custom_design")=="CUSTOM-0154");
    const auto& exceptions=j.at("explicit_nonzero_trigger_exceptions");
    require(exceptions.is_array() && exceptions.size()==2);
    std::set<std::array<std::uint16_t,4>> exception_points;
    for(const auto& row:exceptions) {
        require(row.at("values")==nlohmann::json::array({"01","02"}) && row.at("observations").size()==9);
        require(exception_points.insert({static_cast<std::uint16_t>(number(row.at("area"),63)),
            static_cast<std::uint16_t>(number(row.at("scene"),1023)),
            static_cast<std::uint16_t>(number(row.at("x"),0x3fff)),
            static_cast<std::uint16_t>(number(row.at("y"),0x7fff))}).second);
    }
    require(exception_points==std::set<std::array<std::uint16_t,4>>{{2,0,394,96},{2,2,60,77}});
    // Only these audited maps are admitted; a future map needs new provenance
    // and a new whole-file pin, never a user-editable selector or filename scan.
    require(j.at("scenes").is_array() && j.at("scenes").size()==4);
    for(const auto& row:j.at("scenes")) {
        const auto area=static_cast<std::uint16_t>(number(row.at("area"),63));
        const auto scene=static_cast<std::uint16_t>(number(row.at("scene"),1023));
        require(supported_scene(area,scene) && row.at("kind")==3 && row.at("dynamic_occupancy_included")==false);
        const int columns=number(row.at("block_width"),64),rows=number(row.at("block_height"),64);
        require(columns>0 && rows>0);
        Scene grid{3,columns*21,rows*21,{},{}};
        grid.cells.assign(static_cast<std::size_t>(grid.width*grid.height),255);
        grid.observed_masks.assign(grid.cells.size(),0);
        const auto& windows=row.at("windows");require(windows.is_array() && windows.size()==static_cast<std::size_t>(columns*rows));
        for(std::size_t i=0;i<windows.size();++i) {
            const auto& window=windows[i];const int bx=static_cast<int>(i%columns),by=static_cast<int>(i/columns);
            require(window.at("block_x")==bx && window.at("block_y")==by &&
                window.at("origin_x")==bx*21-21 && window.at("origin_y")==by*21-21 && window.at("block_present").is_boolean());
            const bool present=window.at("block_present").get<bool>();
            const auto encoded=window.at("cells_hex").get<std::string>();require(encoded.size()==63*63*2);
            for(int y=0;y<63;++y)for(int x=0;x<63;++x) {
                const auto offset=static_cast<std::size_t>((y*63+x)*2);
                if(encoded[offset]=='?' && encoded[offset+1]=='?')continue;
                require(encoded[offset]=='0' && encoded[offset+1]>='0' && encoded[offset+1]<='2');
                if(!present)continue;
                const int wx=bx*21-21+x,wy=by*21-21+y;
                if(wx<0||wy<0||wx>=grid.width||wy>=grid.height)continue;
                const auto value=static_cast<std::uint8_t>(encoded[offset+1]-'0');
                grid.observed_masks[static_cast<std::size_t>(wy*grid.width+wx)]|=static_cast<std::uint8_t>(1u<<value);
                auto& previous=grid.cells[static_cast<std::size_t>(wy*grid.width+wx)];
                if(previous==255)previous=value;else if(previous!=value)previous=254;
            }
        }
        require(scenes_.emplace(std::pair{area,scene},std::move(grid)).second);
    }
    require(j.at("routes").is_array() && !j.at("routes").empty() && j.at("routes").size()<=256);
    std::set<std::array<std::uint16_t,4>> source_points;
    for(const auto& row:j.at("routes")) {
        const auto field=[&](const char* name,int maximum){return static_cast<std::uint16_t>(number(row.at(name),maximum));};
        Route route{field("area",63),field("source_scene",1023),field("source_x",0x3fff),field("source_y",0x7fff),
            field("target_scene",1023),field("target_x",0x3fff),field("target_y",0x7fff)};
        require(route.area==2 && ((route.source_scene==0 && supported_scene(route.area,route.target_scene)) ||
            (supported_scene(route.area,route.source_scene) && route.target_scene==0)));
        require(source_points.insert({route.area,route.source_scene,route.source_x,route.source_y}).second);
        routes_.push_back(route);
    }
    for(const auto& route:routes_) {
        // Cross-MDL triggers and landings may use different native marker
        // slots. Require an independently qualified return scene edge, never
        // invent its coordinates by swapping this tuple's endpoints.
        require(std::any_of(routes_.begin(),routes_.end(),[&](const Route& other) {
            return other.area==route.area && other.source_scene==route.target_scene && other.target_scene==route.source_scene;
        }));
    }
}
std::optional<std::uint16_t> RecoveredCrossMapNavigation::kind(std::uint16_t area,std::uint16_t scene) const noexcept {
    const auto found=scenes_.find({area,scene});return found==scenes_.end()?std::nullopt:std::optional{found->second.kind};
}
std::optional<std::uint8_t> RecoveredCrossMapNavigation::cell(std::uint16_t area,std::uint16_t scene,int x,int y) const noexcept {
    const auto found=scenes_.find({area,scene});if(found==scenes_.end())return std::nullopt;
    const auto& grid=found->second;if(x<0||y<0||x>=grid.width||y>=grid.height)return std::nullopt;
    const auto value=grid.cells[static_cast<std::size_t>(y*grid.width+x)];
    return value>2?std::nullopt:std::optional<std::uint8_t>{value};
}
bool RecoveredCrossMapNavigation::consistently_walkable(std::uint16_t area,std::uint16_t scene,int x,int y) const noexcept {
    const auto found=scenes_.find({area,scene});if(found==scenes_.end())return false;
    const auto& grid=found->second;if(x<0||y<0||x>=grid.width||y>=grid.height)return false;
    const auto mask=grid.observed_masks[static_cast<std::size_t>(y*grid.width+x)];
    return mask!=0 && !(mask&1u);
}
bool RecoveredCrossMapNavigation::contains(const Route& route) const noexcept {
    return std::find(routes_.begin(),routes_.end(),route)!=routes_.end();
}
}
