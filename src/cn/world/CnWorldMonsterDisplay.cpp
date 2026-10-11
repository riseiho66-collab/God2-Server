#include "cn/world/CnWorldMonsterDisplay.h"
#include <utility>

namespace god2::cn {
std::optional<CnWorldMonsterDisplay::Projection> CnWorldMonsterDisplay::prepare(
    const Wire::Record& record,Catalog::Resource catalog,Resources resources) {
    try {
        if(!Catalog::matches(catalog) || !resources.revision || !resources.current ||
           !resources.current(catalog,resources.revision))return std::nullopt;
        auto appearance=Catalog::project(record,catalog);if(!appearance)return std::nullopt;
        auto consumed=record;
        // Any nonzero override invokes00430A50. Out-of-range returns base,
        // but the caller STILL replaces the pose bits with that base's pose.
        if(appearance->override_invoked) {
            auto changed=Wire::with_consumer_pose(consumed,appearance->pose_raw());
            if(!changed)return std::nullopt;
            consumed=std::move(*changed);
        }
        Projection result{record,consumed,std::move(*appearance),catalog.revision,resources.revision,
            std::nullopt,std::nullopt,std::nullopt};
        if(result.appearance.composite()) {
            if(!result.appearance.components || !resources.composite_models)return std::nullopt;
            auto models=resources.composite_models(*result.appearance.components);
            if(!models || std::any_of(models->begin(),models->end(),[](auto value){return value<0;}))return std::nullopt;
            result.composite_models=std::move(models);
        }else {
            if(!resources.single_auxiliary || !resources.single_model)return std::nullopt;
            auto auxiliary=resources.single_auxiliary(result.appearance.single_model_selector);
            if(!auxiliary || !resources.current(catalog,resources.revision))return std::nullopt;
            auto model=resources.single_model(result.appearance.single_model_selector);
            if(!model || *model>=0x200)return std::nullopt;
            result.single_auxiliary=auxiliary;result.single_model=model;
            if(result.appearance.single_model_selector==0x3d)
                result.native_consumed=Wire::with_consumer_override(result.native_consumed,0x3d);
        }
        if(!resources.current(catalog,resources.revision))return std::nullopt;
        return result; // Expected consumed inputs only, not observed native execution.
    }catch(...) {return std::nullopt;}
}
}
