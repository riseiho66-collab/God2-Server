#pragma once
#include "game/TaiwanActorStatusIncarnationSource.h"
#include <memory>
#include <optional>
#include <span>
#include <utility>
#include <vector>

namespace god2 {
class Session;
class TaiwanActorStatusOwnedSource;
// Pure owned-status VERSION/bytes evidence for the real CUSTOM-0133 return
// publication. This is not complete writer permission, exclusion or native ACK.
// No game-affine source, saved input, Profile, callback or observer is retained.
class TaiwanActorStatusPublication final {
    struct UnitData;
    static bool retained_impl(const std::shared_ptr<const UnitData>&) noexcept;
    friend class TaiwanActorStatusOwnedSource;
public:
    class ActorUnit final {
    public:
        ActorUnit(const ActorUnit&) noexcept=default;
        ActorUnit& operator=(const ActorUnit&) noexcept=default;
        bool operator==(const ActorUnit& other) const noexcept{return data_==other.data_;}
        const SharedWorldPresence::Lease& source() const noexcept;
        const SharedWorldPresence::Lease& recipient() const noexcept;
        const std::vector<std::uint8_t>& logical() const noexcept;
        bool retained() const noexcept;
    private:
        friend class TaiwanActorStatusOwnedSource;
        explicit ActorUnit(std::shared_ptr<const UnitData> data) noexcept:data_(std::move(data)){}
        std::shared_ptr<const UnitData> data_;
    };
    class FrameSeal final {
    public:
        FrameSeal(const FrameSeal&) noexcept=default;
        FrameSeal& operator=(const FrameSeal&) noexcept=default;
        bool operator==(const FrameSeal& other) const noexcept{return data_==other.data_;}
    private:
        friend class Session;
        struct Data; // Actual Session plan/frame binding is defined there only.
        explicit FrameSeal(std::shared_ptr<const Data> data) noexcept:data_(std::move(data)){}
        std::shared_ptr<const Data> data_;
    };
};
}
