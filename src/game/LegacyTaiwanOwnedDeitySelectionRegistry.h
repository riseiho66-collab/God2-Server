#pragma once
#include "game/LegacyWorldReply.h"
#include "handlers/RecoveredOwnedCompanions.h"
#include <memory>
#include <span>

namespace god2 {
// Actual legacy C67 private commits and their causal original output. This
// supplies no common-world lease, native ACK, learning or casting permission.
class LegacyTaiwanOwnedDeitySelectionRegistry {
    struct Impl;
    struct Data;
public:
    class Callback {
    public:
        Callback(const Callback&)=default;
        Callback& operator=(const Callback&)=default;
    private:
        friend class LegacyTaiwanOwnedDeitySelectionRegistry;
        explicit Callback(std::shared_ptr<Data> value):data_(std::move(value)){}
        std::shared_ptr<Data> data_;
    };
    class WrittenSelectionSource {
    public:
        WrittenSelectionSource(const WrittenSelectionSource&)=default;
        WrittenSelectionSource& operator=(const WrittenSelectionSource&)=default;
        std::span<const RecoveredOwnedCompanions::SelectionPublication> publications() const noexcept;
        const Session::NormalWorldInitialization& initialization() const noexcept;
        const Session::WorldCallbackOutput& output() const noexcept;
        bool current(Session&) const;
        bool same_source(const WrittenSelectionSource& other) const noexcept{return data_==other.data_;}
    private:
        friend class LegacyTaiwanOwnedDeitySelectionRegistry;
        explicit WrittenSelectionSource(std::shared_ptr<Data> value):data_(std::move(value)){}
        std::shared_ptr<Data> data_;
    };
    LegacyTaiwanOwnedDeitySelectionRegistry(std::size_t actual_session_capacity,RecoveredOwnedCompanions&);
    Callback begin(Session&,const Session::NormalWorldInitialization&,const Session::WorldCallbackOutput&);
    // Only this method obtains the real helper publication; callers cannot
    // install an earlier idempotent commit or supply arbitrary tagged bytes.
    std::optional<LegacyWorldReply> select(Session&,const RecoveredDeitySelection::Request&,std::function<bool()> current={});
    void finish(Session&,const Callback&,bool callback_returned_value);
    void abandon(const Callback&) noexcept;
    std::optional<WrittenSelectionSource> observe(Session&);
    void release(Session&);
private:
    std::shared_ptr<Impl> state_;
};
}
