#pragma once
#include "game/SharedTaiwanWorldRecordSource.h"
#include <memory>
namespace god2 {
// CUSTOM-0159 late GAME owner. Private batches retain exact Session and original
// selected-index custody, never gameplay grants. Stop before borrowed locals die.
class OwnedTaiwanGuildActionsDispatch final {
public:
    using Binding=SharedTaiwanWorldRecordSource::GuildActionsBinding;
    static std::shared_ptr<OwnedTaiwanGuildActionsDispatch> create();
    Binding binding();
    void install(Binding);
    void stop();
    ~OwnedTaiwanGuildActionsDispatch();
    OwnedTaiwanGuildActionsDispatch(const OwnedTaiwanGuildActionsDispatch&)=delete;
    OwnedTaiwanGuildActionsDispatch& operator=(const OwnedTaiwanGuildActionsDispatch&)=delete;
private:
    struct State;
    explicit OwnedTaiwanGuildActionsDispatch(std::shared_ptr<State> s):state_(std::move(s)){}
    std::shared_ptr<State> state_;
};
}
