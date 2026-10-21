#include <iostream>
#include <string>
#include <stdexcept>
void test_packet(); void test_decoder(); void test_dispatcher(); void test_lua();
void test_session_state(); void test_protocol_replay(); void test_database(); void test_network();
void test_config();
void test_session_skill_sequence();
void test_session_battle_service();
void test_post_server_select();
void test_legacy_character_list_candidate();
void test_character_create();
void test_password_hash();
void test_recovered_account_login();
void test_recovered_character_repository();
void test_recovered_character_list();
void test_post_create_select();
void test_recovered_movement_service();
void test_recovered_position_repository();
void test_taiwan_native_hmd_bundle_source();
void test_taiwan_channel_worlds();
void test_taiwan_channel_servers();
void test_application_game_frame();
void test_application_game_sources();
void test_taiwan_channel_character_lists();
void test_taiwan_three_channel_plan();
void test_taiwan_handoff_binding();
void test_shared_guild_channel_directory53();
void test_owned_taiwan_guild_chat_dispatch();
void test_owned_taiwan_guild_actions_dispatch();
void test_world_reply_push_capture();
int main(int argc,char** argv) {
    const std::pair<const char*,void(*)()> suites[]={
        {"packet",test_packet},{"decoder",test_decoder},{"dispatcher",test_dispatcher},{"lua",test_lua},
        {"session_state",test_session_state},{"protocol_replay",test_protocol_replay},{"database",test_database},{"network",test_network},{"config",test_config},
        {"session_skill_sequence",test_session_skill_sequence},
        {"session_battle_service",test_session_battle_service},
        {"post_server_select",test_post_server_select},
        {"legacy_character_list_candidate",test_legacy_character_list_candidate},
        {"character_create",test_character_create},
        {"password_hash",test_password_hash},
        {"recovered_account_login",test_recovered_account_login},
        {"recovered_character_repository",test_recovered_character_repository},
        {"recovered_character_list",test_recovered_character_list},
        {"post_create_select",test_post_create_select},
        {"recovered_movement_service",test_recovered_movement_service},
        {"recovered_position_repository",test_recovered_position_repository},
        {"taiwan_native_hmd_bundle_source",test_taiwan_native_hmd_bundle_source},
        {"taiwan_channel_worlds",test_taiwan_channel_worlds},
        {"taiwan_channel_servers",test_taiwan_channel_servers},
        {"application_game_frame",test_application_game_frame},
        {"application_game_sources",test_application_game_sources},
        {"taiwan_channel_character_lists",test_taiwan_channel_character_lists},
        {"taiwan_three_channel_plan",test_taiwan_three_channel_plan},
        {"taiwan_handoff_binding",test_taiwan_handoff_binding},
        {"shared_guild_channel_directory53",test_shared_guild_channel_directory53},
        {"owned_taiwan_guild_chat_dispatch",test_owned_taiwan_guild_chat_dispatch},
        {"owned_taiwan_guild_actions_dispatch",test_owned_taiwan_guild_actions_dispatch},
        {"world_reply_push_capture",test_world_reply_push_capture}
    };
    try {
        bool found=false;
        for(const auto& [name,test]:suites) if(argc==1 || argv[1]==std::string(name)) { test(); found=true; std::cout<<"PASS "<<name<<'\n'; }
        if(!found) throw std::runtime_error("Unknown suite");
    } catch(const std::exception& e) { std::cerr<<"FAIL: "<<e.what()<<'\n'; return 1; }
    return 0;
}
