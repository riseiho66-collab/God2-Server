#pragma once
#include "game/TaiwanNativeSceneResourceOwner.h"

namespace god2 {
class TaiwanNativeHmdBundleSource;
// Only the actual CAN-selected parser/binder issues this immutable bundle.
// Existing host still supplies the sole movement Authority and position CAS.
class TaiwanNativeHmdPreparedBundle final {
public:
    bool matches(const TaiwanNativeSceneResourceOwner::Input&)const;
    const TaiwanNativeSceneResourceOwner::Sources& sources()const{return sources_;}
    const TaiwanNativeMapAsset::RomBound& binding()const{return binding_;}
    const SharedTaiwanNativeMovementScene::Resources& resources()const{return resources_;}
private:
    friend class TaiwanNativeHmdBundleSource;
    TaiwanNativeHmdPreparedBundle(TaiwanNativeSceneResourceOwner::Sources,TaiwanNativeMapAsset::RomBound,
        SharedTaiwanNativeMovementScene::Resources,std::shared_ptr<TaiwanNativeSceneSourceLifetime>,std::size_t,std::size_t);
    const TaiwanNativeSceneResourceOwner::Sources sources_;
    const TaiwanNativeMapAsset::RomBound binding_;
    const SharedTaiwanNativeMovementScene::Resources resources_;
    const std::shared_ptr<TaiwanNativeSceneSourceLifetime> lifetime_;
    const std::size_t hmd_limit_,rom_limit_;
};
}
