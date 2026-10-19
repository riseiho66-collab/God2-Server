#pragma once
#include "db/NativeMapCatalog.h"
#include "game/SharedTaiwanNativeMovementHost.h"
#include "game/TaiwanNativeCanAsset.h"
#include "game/TaiwanNativeHmdPreparedBundle.h"

namespace god2 {
// CUSTOM-0158 publishes complete immutable server assets. Native HMD/ROM
// bytes/prefix/composition remain original; root/tag selection is explicit
// server policy, not a recovered native dispatcher or remote window attestation.
class TaiwanNativeHmdBundleSource final:public std::enable_shared_from_this<TaiwanNativeHmdBundleSource> {
public:
    using Scene=SharedTaiwanNativeMovementScene;
    using Input=TaiwanNativeSceneResourceOwner::Input;
    struct AreaConfiguration {
        std::uint16_t area=0;
        std::filesystem::path actual_can_file;
        std::string expected_can_sha256;
        std::optional<std::uint8_t> expected_hmd_tag; // Explicit subset, no implicit tag1 rule.
    };
    struct Limits {
        std::size_t hmd_encoded=0,hmd_plain=0,rom_encoded=0,rom_plain=0,max_cached_maps=0;
    };
    struct Configuration {
        NativeMapSource expected_catalog;
        std::filesystem::path actual_client_directory;
        std::vector<AreaConfiguration> areas;
        Limits limits;
    };
    struct InitialPose {
        RecoveredPosition position{};
        std::uint8_t direction=8; // Unqualified until the actual pose supplier fills it.
        std::function<bool(Session&,const Scene::FactoryScope&,const RecoveredPosition&,std::uint8_t)> current;
    };
    using PoseSource=std::function<std::optional<InitialPose>(Session&,const Scene::FactoryScope&)>;
    static std::shared_ptr<TaiwanNativeHmdBundleSource> create(const NativeMapCatalog&,
        std::shared_ptr<SharedWorldPresence>,std::size_t actual_session_capacity,Configuration,PoseSource);
    ~TaiwanNativeHmdBundleSource();
    SharedTaiwanNativeMovementHost::InputSource input_source();
    // Validate all CAN publications and rebuild all currently cached maps
    // before whole-version publication. Failure retains the prior whole version.
    // Success revokes old supplies; caller coordinates actual host replacement.
    bool publish(Configuration);
    void stop();
private:
    struct State;
    explicit TaiwanNativeHmdBundleSource(std::shared_ptr<State>);
    std::optional<Input> read(Session&,const Scene::FactoryScope&);
    static std::shared_ptr<TaiwanNativeSceneSourceLifetime> lifetime(const std::shared_ptr<Session>&,const Scene::Lease&);
    static std::shared_ptr<const TaiwanNativeHmdPreparedBundle> prepared(TaiwanNativeSceneResourceOwner::Sources,
        TaiwanNativeMapAsset::RomBound,Scene::Resources,std::shared_ptr<TaiwanNativeSceneSourceLifetime>,const Limits&);
    std::shared_ptr<State> state_;
};
}
