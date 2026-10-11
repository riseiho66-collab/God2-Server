#pragma once
#include <memory>
#include <thread>

namespace god2 {
class RecoveredCharacterRepository;
class SharedWorldPresence;
class SharedNativeWorldTransports;
class SharedNativeSpectatorPublication;
class SharedNativeSpectatorTargets;
namespace cn {class SharedActorVisibility;}

// One actual game-owner common world context. Creation allocates the presence,
// visibility and native transport registries only; no scene, native records or
// gameplay defaults. Transport tokens/registry retain connections weakly.
// The same repository and game owner must outlive this host AND every retained
// registry/controller/connection copy through drain. Access/destroy on that owner.
class SharedWorldHost final {
public:
    explicit SharedWorldHost(RecoveredCharacterRepository&);
    ~SharedWorldHost();
    SharedWorldHost(const SharedWorldHost&)=delete;
    SharedWorldHost& operator=(const SharedWorldHost&)=delete;
    SharedWorldHost(SharedWorldHost&&)=delete;
    SharedWorldHost& operator=(SharedWorldHost&&)=delete;
    std::shared_ptr<SharedWorldPresence> presence() const;
    std::shared_ptr<cn::SharedActorVisibility> visibility() const;
    std::shared_ptr<SharedNativeWorldTransports> transports() const;
    // Optional actual UI publisher, installed once from this same Context.
    // No native event, window epoch or gameplay authority is created here.
    std::shared_ptr<SharedNativeSpectatorPublication> native_spectator_publication() const;
    void install_native_spectator_publication(std::shared_ptr<SharedNativeSpectatorPublication>);
    std::shared_ptr<SharedNativeSpectatorTargets> native_spectator_targets() const;
    void install_native_spectator_targets(std::shared_ptr<SharedNativeSpectatorTargets>);
    bool owns_repository(const RecoveredCharacterRepository&) const;
private:
    void owner() const;
    RecoveredCharacterRepository& characters_;
    const std::thread::id thread_=std::this_thread::get_id();
    const std::shared_ptr<SharedWorldPresence> presence_;
    const std::shared_ptr<cn::SharedActorVisibility> visibility_;
    const std::shared_ptr<SharedNativeWorldTransports> transports_;
    std::shared_ptr<SharedNativeSpectatorPublication> spectator_publication_;
    std::shared_ptr<SharedNativeSpectatorTargets> spectator_targets_;
};
}
