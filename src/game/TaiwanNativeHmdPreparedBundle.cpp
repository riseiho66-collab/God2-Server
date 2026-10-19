#include "game/TaiwanNativeHmdPreparedBundle.h"
#include <stdexcept>
#include <utility>

namespace god2 {
TaiwanNativeHmdPreparedBundle::TaiwanNativeHmdPreparedBundle(TaiwanNativeSceneResourceOwner::Sources sources,
        TaiwanNativeMapAsset::RomBound binding,SharedTaiwanNativeMovementScene::Resources images,
        std::shared_ptr<TaiwanNativeSceneSourceLifetime> lifetime,std::size_t hmd_limit,std::size_t rom_limit)
    :sources_(std::move(sources)),binding_(std::move(binding)),resources_(std::move(images)),
     lifetime_(std::move(lifetime)),hmd_limit_(hmd_limit),rom_limit_(rom_limit){}
bool TaiwanNativeHmdPreparedBundle::matches(const TaiwanNativeSceneResourceOwner::Input& input)const {
    try{
        const auto& a=sources_;const auto& b=input.sources;
        if(input.prepared_bundle.get()!=this||!lifetime_||input.source_lifetime!=lifetime_||!lifetime_->current()||
           input.max_hmd_plain_bytes!=hmd_limit_||input.max_rom_plain_bytes!=rom_limit_||
           input.actual_resource_generation!=resources_.actual_resource_generation||
           input.actual_initial_scene_generation!=resources_.actual_initial_scene_generation||
           &a.hmd.encoded_bytes()!=&b.hmd.encoded_bytes()||a.actual_hmd_generation!=b.actual_hmd_generation||
           a.actual_rom_prefix!=b.actual_rom_prefix||a.roms.size()!=b.roms.size()||!resources_.complete())return false;
        for(std::size_t i=0;i<a.roms.size();++i)
            if(a.roms[i].ordinal!=b.roms[i].ordinal||a.roms[i].actual_resource_generation!=b.roms[i].actual_resource_generation||
               &a.roms[i].selected.encoded_bytes()!=&b.roms[i].selected.encoded_bytes())return false;
        return true;
    }catch(const std::logic_error&){return false;}
}
}
