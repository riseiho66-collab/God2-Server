#pragma once
#include "game/SharedTaiwanWorldRecordSource.h"
#include <memory>

namespace god2 {
// CUSTOM-0159: late-installed actual guild-chat callback for the native mixed
// source. This GAME owner supplies custody/reentry fences, never membership,
// renderer, native input or successful output authority. Keep it through full
// host drain and stop it before the callback's borrowed frame locals unwind.
class OwnedTaiwanGuildChatDispatch final {
public:
    using Binding=SharedTaiwanWorldRecordSource::GuildChatBinding;
    using Handler=decltype(Binding::dispatch);
    using Invalidator=std::function<void()>;
    static std::shared_ptr<OwnedTaiwanGuildChatDispatch> create();
    Binding binding();
    void install(Handler,Invalidator={});
    void stop();
    ~OwnedTaiwanGuildChatDispatch();
    OwnedTaiwanGuildChatDispatch(const OwnedTaiwanGuildChatDispatch&)=delete;
    OwnedTaiwanGuildChatDispatch& operator=(const OwnedTaiwanGuildChatDispatch&)=delete;
private:
    struct State;
    explicit OwnedTaiwanGuildChatDispatch(std::shared_ptr<State> state):state_(std::move(state)){}
    std::shared_ptr<State> state_;
};
}
