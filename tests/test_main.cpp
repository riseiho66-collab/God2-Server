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
        {"recovered_position_repository",test_recovered_position_repository}
    };
    try {
        bool found=false;
        for(const auto& [name,test]:suites) if(argc==1 || argv[1]==std::string(name)) { test(); found=true; std::cout<<"PASS "<<name<<'\n'; }
        if(!found) throw std::runtime_error("Unknown suite");
    } catch(const std::exception& e) { std::cerr<<"FAIL: "<<e.what()<<'\n'; return 1; }
    return 0;
}
