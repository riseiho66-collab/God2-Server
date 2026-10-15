#pragma once
#include "game/TaiwanCustomFullActorProfile.h"
#include <array>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <optional>
#include <thread>
#include <utility>

namespace god2 {
// Concrete ordinary Hero/Drv and independent DrvDoll asset owner. Never a native client cache/window,
// manager, action-choice, equip permission, status or ACK attestation.
class TaiwanNativeActorResourceSource final : public std::enable_shared_from_this<TaiwanNativeActorResourceSource> {
    struct Identity {};
    struct Data;
    struct CurrentCarrier;
public:
    using SavedInput=OwnedTaiwanReturnActorSavedSource::PopulationInput;
    using Equipment=OwnedTaiwanReturnActorSavedSource::ProfileEquipment;
    using ResourceInput=TaiwanCustomFullActorProfile::ResourceInput;
    using NativeRomContext=TaiwanNativeActorResourceBank::NativeRomContext;
    using TailNativeRomContext=TaiwanNativeDrvDoll::NativeRomContext;
    enum class Scope {CurrentServerImmutableAssetGeneration,WholePhysicalSelection};
    class DrvRom final {
    public:
        DrvRom(NativeRomContext input_context,std::uint32_t actual_full_action)
            :context(std::move(input_context)),full_action(actual_full_action){}
        const NativeRomContext context;
        // Explicit CUSTOM host choice; never Drv ActType/preload or Hero action.
        const std::uint32_t full_action;
    };
    class TailRom final {
    public:
        TailRom(TailNativeRomContext input_context,std::uint32_t actual_full_action)
            :context(std::move(input_context)),full_action(actual_full_action){}
        // Distinct native direct-ROM tail context; no Hero model prefix.
        const TailNativeRomContext context;
        const std::uint32_t full_action; // Explicit CUSTOM host choice, not a native cached action.
    };
    class Configuration final {
    public:
        Configuration(std::array<NativeRomContext,4>,std::array<std::uint32_t,4> actual_full_actions,
            std::size_t max_encoded_bytes,std::size_t max_plain_bytes,Scope,
            std::optional<TaiwanNativeActorArgumentSource::CustomSelectors> selectors={},
            std::optional<DrvRom> drv={},std::optional<TailRom> tail={});
        const std::array<NativeRomContext,4> contexts;
        // Explicit CUSTOM host action choices, not inferred native first actions.
        const std::array<std::uint32_t,4> full_actions;
        const std::size_t max_encoded_bytes,max_plain_bytes;
        const Scope scope;
        const std::optional<TaiwanNativeActorArgumentSource::CustomSelectors> selectors;
        const std::optional<DrvRom> drv;
        const std::optional<TailRom> tail; // LAST: independent136B DrvDoll source.
    };
    static std::shared_ptr<TaiwanNativeActorResourceSource> create(
        std::shared_ptr<SharedWorldPresence>,std::shared_ptr<TaiwanNativeActorArgumentSource>,Configuration);
    TaiwanNativeActorResourceSource(const TaiwanNativeActorResourceSource&)=delete;
    TaiwanNativeActorResourceSource& operator=(const TaiwanNativeActorResourceSource&)=delete;
    ~TaiwanNativeActorResourceSource();
    std::optional<ResourceInput> observe(std::shared_ptr<const SavedInput>,std::size_t,const Equipment&) const;
    bool current(const ResourceInput&) const;
    bool owns_presence(const std::shared_ptr<SharedWorldPresence>&) const noexcept;
    bool owns_argument_source(const std::shared_ptr<TaiwanNativeActorArgumentSource>&) const noexcept;
    Scope scope() const noexcept{return configuration_.scope;}
private:
    struct Operation;
    TaiwanNativeActorResourceSource(std::shared_ptr<SharedWorldPresence>,
        std::shared_ptr<TaiwanNativeActorArgumentSource>,Configuration);
    const std::shared_ptr<SharedWorldPresence> presence_;
    const std::shared_ptr<TaiwanNativeActorArgumentSource> arguments_;
    const Configuration configuration_;
    const std::shared_ptr<const Identity> identity_=std::make_shared<const Identity>();
    const std::thread::id thread_=std::this_thread::get_id();
    mutable bool busy_=false,poisoned_=false;
    bool stopped_=false;
    mutable std::uint64_t next_epoch_=1;
    // Allocation bound of this source, not a recovered native capacity. Weak
    // entries retain neither old inputs nor ROMs after their consumers leave.
    static constexpr std::size_t cache_capacity=4096;
    mutable std::array<std::weak_ptr<const Data>,cache_capacity> cache_;
    bool retained(const Data&) const noexcept;
    bool same_material(const ResourceInput&,const Data&) const noexcept;
    bool physical_current(const Data&) const;
    bool qualify_current(const Data&) const;
    bool current_for(const ResourceInput&,const std::shared_ptr<const Data>&) const;
    ResourceInput material(const std::shared_ptr<const Data>&) const;
};
}
