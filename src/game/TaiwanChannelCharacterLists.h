#pragma once
#include "net/Session.h"
#include <array>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <utility>

namespace god2 {
// CUSTOM-0159 routes actual L callbacks to one of three supplied native list
// issuers. A6/advertisement chooses an issuer only; it grants no list, target,
// authentication or G handoff authority. Keep this owner on GAME through full
// NET/GAME drain; copied transport bindings retain it weakly.
class TaiwanChannelCharacterLists final {
public:
    struct Source {
        decltype(Session::RecoveredCharacterHandlers::native_list) native_list;
        decltype(Session::RecoveredCharacterHandlers::native_list_current) native_list_current;
        decltype(Session::RecoveredCharacterHandlers::native_list_complete) native_list_complete;
        Session::DisconnectHandler on_disconnect;
        decltype(Session::RecoveredCharacterHandlers::native_select) native_select;
    };
    struct Binding {
        decltype(Source::native_list) list;
        decltype(Source::native_list_current) current;
        decltype(Source::native_list_complete) complete;
        Session::DisconnectHandler disconnected;
        decltype(Source::native_select) select;
    };
    // Bound includes completed L records until exact disconnect, so subsequent
    // select/cleanup cannot substitute a latest selection or a reused scalar ID.
    static std::shared_ptr<TaiwanChannelCharacterLists> create(std::array<Source,3>,
        std::uint8_t expected_group,std::size_t actual_session_capacity);
    TaiwanChannelCharacterLists(const TaiwanChannelCharacterLists&)=delete;
    TaiwanChannelCharacterLists& operator=(const TaiwanChannelCharacterLists&)=delete;
    ~TaiwanChannelCharacterLists();
    Binding binding();
private:
    struct State;
    explicit TaiwanChannelCharacterLists(std::shared_ptr<State> state):state_(std::move(state)){}
    std::shared_ptr<State> state_;
};
}
