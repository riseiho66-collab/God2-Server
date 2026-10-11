#pragma once
namespace god2 {
enum class ProtocolMode { Fixture, God2Recovered, God2PostSeed, God2C2S0002, God2LoginTerminal, God2ServerList, God2PostServerSelect, God2LegacyCharacterListCandidate, God2CharacterConnection };
constexpr bool is_post_select_mode(ProtocolMode mode) {
    return mode==ProtocolMode::God2PostServerSelect || mode==ProtocolMode::God2LegacyCharacterListCandidate;
}
constexpr bool is_server_list_mode(ProtocolMode mode) {
    return mode==ProtocolMode::God2ServerList || is_post_select_mode(mode);
}
constexpr bool is_terminal_mode(ProtocolMode mode) {
    return mode==ProtocolMode::God2LoginTerminal || is_server_list_mode(mode);
}
constexpr bool is_credential_mode(ProtocolMode mode) {
    return mode==ProtocolMode::God2C2S0002 || mode==ProtocolMode::God2CharacterConnection || is_terminal_mode(mode);
}
constexpr bool is_recovered(ProtocolMode mode) {
    return mode==ProtocolMode::God2Recovered || mode==ProtocolMode::God2PostSeed || is_credential_mode(mode);
}
}
