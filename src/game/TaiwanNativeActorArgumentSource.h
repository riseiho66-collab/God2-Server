#pragma once
#include "game/OwnedTaiwanReturnActorSavedSource.h"
#include "game/TaiwanNativeActorResourceBank.h"
#include "game/TaiwanNativeDrvDoll.h"
#include <array>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <optional>
#include <thread>
#include <utility>

namespace god2 {
// Original149c ordinary461270 argument computation over a private saved input.
// Stored delivery witnesses are not live native actor/cache/window observations.
// No resource load, ROM action, equip permission, status or wire is issued here.
class TaiwanNativeActorArgumentSource final {
    struct Identity {};
    struct Data;
public:
    using SavedInput=OwnedTaiwanReturnActorSavedSource::PopulationInput;
    using Equipment=OwnedTaiwanReturnActorSavedSource::ProfileEquipment;
    using Lookup=TaiwanNativeActorResourceBank::HeroLookup;
    enum class Origin {CurrentSavedWorldWitness,Custom0133Selectors};
    class CustomSelectors final {
    public:
        explicit CustomSelectors(std::uint32_t first,std::uint32_t second);
        std::uint8_t first_selector() const noexcept{return first_;}
        std::uint8_t second_selector() const noexcept{return second_;}
    private:
        const std::uint8_t first_,second_;
    };
    class Observation final {
    public:
        Observation(const Observation&)=default;
        Observation& operator=(const Observation&)=default;
        const std::shared_ptr<const SavedInput>& saved_input() const noexcept;
        std::size_t row_index() const noexcept;
        const Equipment& equipment() const noexcept;
        std::uint8_t first_selector() const noexcept;
        std::uint8_t second_selector() const noexcept;
        std::uint32_t full_drv_ordinal() const noexcept;
        std::uint8_t act_type() const noexcept;
        const std::array<Lookup,4>& lookups() const noexcept;
        const std::shared_ptr<const TaiwanNativeActorResourceBank>& bank() const noexcept;
        const std::shared_ptr<const TaiwanNativeDrvDoll>& drv_doll_bank() const noexcept;
        Origin origin() const noexcept;
        const TaiwanNativeDrvDoll::Record& actual_tail_source() const noexcept;
        const Lookup& head_modifier_lookup() const noexcept;
        std::uint8_t foot_sixth_argument() const noexcept;
        std::uint8_t foot_modifier() const noexcept;
        bool operator==(const Observation& other) const noexcept{return data_==other.data_;}
    private:
        friend class TaiwanNativeActorArgumentSource;
        explicit Observation(std::shared_ptr<const Data> data):data_(std::move(data)){}
        std::shared_ptr<const Data> data_;
    };
    static std::shared_ptr<TaiwanNativeActorArgumentSource> create(
        std::shared_ptr<SharedWorldPresence>,std::shared_ptr<const TaiwanNativeActorResourceBank>,
        std::shared_ptr<const TaiwanNativeDrvDoll>);
    TaiwanNativeActorArgumentSource(const TaiwanNativeActorArgumentSource&)=delete;
    TaiwanNativeActorArgumentSource& operator=(const TaiwanNativeActorArgumentSource&)=delete;
    ~TaiwanNativeActorArgumentSource();
    std::optional<Observation> observe(std::shared_ptr<const SavedInput>,std::size_t,
        const Equipment&,std::optional<CustomSelectors> selectors={}) const;
    bool current(const Observation&) const;
    // Pure same-owner/node fences. No SQL, parsing, provider or live observer.
    bool owns_observation(const Observation&) const noexcept;
    bool matches_inputs(const Observation&,const std::shared_ptr<const SavedInput>&,
        std::size_t,const Equipment&) const noexcept;
    bool owns_presence(const std::shared_ptr<SharedWorldPresence>&) const noexcept;
    bool owns_resource_bank(const std::shared_ptr<const TaiwanNativeActorResourceBank>&) const noexcept;
    bool owns_drv_doll_bank(const std::shared_ptr<const TaiwanNativeDrvDoll>&) const noexcept;
private:
    TaiwanNativeActorArgumentSource(std::shared_ptr<SharedWorldPresence>,
        std::shared_ptr<const TaiwanNativeActorResourceBank>,std::shared_ptr<const TaiwanNativeDrvDoll>);
    struct Operation;
    bool retained(const Data&) const noexcept;
    const std::shared_ptr<SharedWorldPresence> presence_;
    const std::shared_ptr<const TaiwanNativeActorResourceBank> bank_;
    const std::shared_ptr<const TaiwanNativeDrvDoll> drv_doll_bank_;
    const std::shared_ptr<const Identity> identity_=std::make_shared<const Identity>();
    const std::thread::id thread_=std::this_thread::get_id();
    mutable bool busy_=false,poisoned_=false;
    bool stopped_=false;
};
}
