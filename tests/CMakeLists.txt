foreach(instance_discard_test IN ITEMS storage_owned_instance_discard_0071 storage_owned_instance_discard_service_0071 storage_owned_instance_discard_adapter_0071)
  add_executable(${instance_discard_test} ${instance_discard_test}.cpp)
  target_link_libraries(${instance_discard_test} PRIVATE god2_core)
  target_compile_definitions(${instance_discard_test} PRIVATE GOD2_SOURCE_DIR="${PROJECT_SOURCE_DIR}")
  add_test(NAME ${instance_discard_test} COMMAND ${instance_discard_test})
  set_tests_properties(${instance_discard_test} PROPERTIES TIMEOUT 180 LABELS "inventory;storage;not-live-acceptance")
endforeach()
foreach(mixed_bank_test IN ITEMS storage_owned_mixed_bank_0070 storage_owned_mixed_bank_service_0070 storage_owned_mixed_bank_adapter_0070)
  add_executable(${mixed_bank_test} ${mixed_bank_test}.cpp)
  target_link_libraries(${mixed_bank_test} PRIVATE god2_core)
  target_compile_definitions(${mixed_bank_test} PRIVATE GOD2_SOURCE_DIR="${PROJECT_SOURCE_DIR}")
  add_test(NAME ${mixed_bank_test} COMMAND ${mixed_bank_test})
  set_tests_properties(${mixed_bank_test} PROPERTIES TIMEOUT 180 LABELS "bank;storage;not-live-acceptance")
endforeach()
foreach(instance_trade_test IN ITEMS storage_owned_instance_trade_0069 storage_owned_instance_trade_service_0069 storage_owned_instance_trade_adapter_0069)
  add_executable(${instance_trade_test} ${instance_trade_test}.cpp)
  target_link_libraries(${instance_trade_test} PRIVATE god2_core)
  target_compile_definitions(${instance_trade_test} PRIVATE GOD2_SOURCE_DIR="${PROJECT_SOURCE_DIR}")
  add_test(NAME ${instance_trade_test} COMMAND ${instance_trade_test})
  set_tests_properties(${instance_trade_test} PROPERTIES TIMEOUT 180 LABELS "trade;storage;not-live-acceptance")
endforeach()
foreach(foreign_bank_test IN ITEMS storage_owned_foreign_bank_0068 storage_owned_foreign_bank_service_0068 storage_owned_foreign_bank_adapter_0068)
  add_executable(${foreign_bank_test} ${foreign_bank_test}.cpp)
  target_link_libraries(${foreign_bank_test} PRIVATE god2_core)
  target_compile_definitions(${foreign_bank_test} PRIVATE GOD2_SOURCE_DIR="${PROJECT_SOURCE_DIR}")
  add_test(NAME ${foreign_bank_test} COMMAND ${foreign_bank_test})
  set_tests_properties(${foreign_bank_test} PROPERTIES TIMEOUT 120 LABELS "bank;storage;not-live-acceptance")
endforeach()
add_executable(storage_owned_guild_membership_0078 storage_owned_guild_membership_0078.cpp)
add_executable(storage_owned_guild_membership_service_0078 storage_owned_guild_membership_service_0078.cpp)
target_link_libraries(storage_owned_guild_membership_service_0078 PRIVATE god2_core)
target_compile_definitions(storage_owned_guild_membership_service_0078 PRIVATE GOD2_SOURCE_DIR="${PROJECT_SOURCE_DIR}")
add_test(NAME storage_owned_guild_membership_service_0078 COMMAND storage_owned_guild_membership_service_0078)
set_tests_properties(storage_owned_guild_membership_service_0078 PROPERTIES TIMEOUT 180 LABELS "guild;storage;lua;not-live-acceptance")
target_link_libraries(storage_owned_guild_membership_0078 PRIVATE god2_core)
add_test(NAME storage_owned_guild_membership_0078 COMMAND storage_owned_guild_membership_0078)
set_tests_properties(storage_owned_guild_membership_0078 PROPERTIES TIMEOUT 180 LABELS "guild;storage;not-live-acceptance")
file(GLOB TEST_SOURCES CONFIGURE_DEPENDS test_*.cpp)
foreach(pve_source_test IN ITEMS test_owned_bank_capacity test_owned_battle_formation test_owned_pve_room_0161 test_owned_pve_world_catalog)
  list(FILTER TEST_SOURCES EXCLUDE REGEX "/${pve_source_test}\\.cpp$")
  add_executable(${pve_source_test} ${pve_source_test}.cpp)
  target_link_libraries(${pve_source_test} PRIVATE god2_core)
  target_compile_definitions(${pve_source_test} PRIVATE GOD2_SOURCE_DIR="${PROJECT_SOURCE_DIR}")
  add_test(NAME ${pve_source_test} COMMAND ${pve_source_test})
  set_tests_properties(${pve_source_test} PROPERTIES TIMEOUT 120 LABELS "source-only;not-native-acceptance")
endforeach()
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_owned_whole_bank_material\\.cpp$")
add_executable(test_owned_whole_bank_material test_owned_whole_bank_material.cpp)
target_link_libraries(test_owned_whole_bank_material PRIVATE god2_core)
add_test(NAME test_owned_whole_bank_material COMMAND test_owned_whole_bank_material)
set_tests_properties(test_owned_whole_bank_material PROPERTIES TIMEOUT 60 LABELS "bank;storage;not-native-acceptance")
foreach(row_test IN ITEMS test_battle_row_preference_0142 test_battle_row_snapshot_fence_0142)
  list(FILTER TEST_SOURCES EXCLUDE REGEX "/${row_test}\\.cpp$")
  add_executable(${row_test} ${row_test}.cpp)
  target_link_libraries(${row_test} PRIVATE god2_core)
  add_test(NAME ${row_test} COMMAND ${row_test})
  set_tests_properties(${row_test} PROPERTIES TIMEOUT 60 LABELS "formation;storage;not-native-acceptance")
endforeach()
# CUSTOM-0082 qualified officer storage/service/runtime/schema gates.
foreach(officer_test IN ITEMS storage_owned_guild_officers_0082 test_owned_guild_officer_service_0082 test_owned_guild_officer_runtime_0082 test_owned_guild_officer_schema_0082)
  list(FILTER TEST_SOURCES EXCLUDE REGEX "/${officer_test}\\.cpp$")
  add_executable(${officer_test} ${officer_test}.cpp)
  target_link_libraries(${officer_test} PRIVATE god2_core)
  target_compile_definitions(${officer_test} PRIVATE GOD2_SOURCE_DIR="${PROJECT_SOURCE_DIR}")
  if(officer_test STREQUAL "test_owned_guild_officer_schema_0082")
    add_test(NAME ${officer_test} COMMAND ${officer_test}
      "${CMAKE_CURRENT_BINARY_DIR}/officer-schema51-private-$<CONFIG>"
      "${PROJECT_SOURCE_DIR}/artifacts/releases/town-chat-welcome-20260924/server-config.json")
  else()
    add_test(NAME ${officer_test} COMMAND ${officer_test})
  endif()
  set_tests_properties(${officer_test} PROPERTIES TIMEOUT 240 LABELS "guild;storage;not-live-acceptance")
endforeach()
foreach(guild_candidate_test IN ITEMS test_recovered_world_records storage_owned_guild_disband_0081 test_owned_guild_disband_service_0081 test_owned_guild_disband_wire_0081 test_owned_guild_kick_0080 storage_owned_guild_kick_0080 test_server_sqlite_migration_selection_0079 test_guild_announcement_world_route_0079 storage_owned_guild_announcement_service_0079 test_owned_guild_announcement_storage_activation_0079 test_owned_guild_entry_0078 test_owned_guild_announcement_wire_0079 storage_owned_guild_announcement_0078 test_owned_guild_formal_config_0078 test_owned_guild_formal_lifecycle_0078)
  list(FILTER TEST_SOURCES EXCLUDE REGEX "/${guild_candidate_test}\\.cpp$")
  add_executable(${guild_candidate_test} ${guild_candidate_test}.cpp)
  target_link_libraries(${guild_candidate_test} PRIVATE god2_core)
  target_compile_definitions(${guild_candidate_test} PRIVATE GOD2_SOURCE_DIR="${PROJECT_SOURCE_DIR}")
  add_test(NAME ${guild_candidate_test} COMMAND ${guild_candidate_test})
  set_tests_properties(${guild_candidate_test} PROPERTIES TIMEOUT 180 LABELS "guild;not-live-acceptance")
endforeach()
add_executable(storage_owned_guild_leader_panel_0078 storage_owned_guild_leader_panel_0078.cpp)
target_link_libraries(storage_owned_guild_leader_panel_0078 PRIVATE god2_core)
target_compile_definitions(storage_owned_guild_leader_panel_0078 PRIVATE GOD2_SOURCE_DIR="${PROJECT_SOURCE_DIR}")
add_test(NAME storage_owned_guild_leader_panel_0078 COMMAND storage_owned_guild_leader_panel_0078)
set_tests_properties(storage_owned_guild_leader_panel_0078 PROPERTIES TIMEOUT 180 LABELS "guild;storage;not-live-acceptance")
add_executable(storage_owned_guild_member_leave_0078 storage_owned_guild_member_leave_0078.cpp)
target_link_libraries(storage_owned_guild_member_leave_0078 PRIVATE god2_core)
target_compile_definitions(storage_owned_guild_member_leave_0078 PRIVATE GOD2_SOURCE_DIR="${PROJECT_SOURCE_DIR}")
add_test(NAME storage_owned_guild_member_leave_0078 COMMAND storage_owned_guild_member_leave_0078)
set_tests_properties(storage_owned_guild_member_leave_0078 PROPERTIES TIMEOUT 180 LABELS "guild;storage;not-live-acceptance")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_owned_guild_leadership_wire_0078\\.cpp$")
add_executable(owned-guild-leadership-wire-0078 test_owned_guild_leadership_wire_0078.cpp)
target_include_directories(owned-guild-leadership-wire-0078 PRIVATE "${PROJECT_SOURCE_DIR}/src")
target_compile_features(owned-guild-leadership-wire-0078 PRIVATE cxx_std_20)
add_test(NAME owned_guild_leadership_wire_0078 COMMAND owned-guild-leadership-wire-0078)
set_tests_properties(owned_guild_leadership_wire_0078 PROPERTIES TIMEOUT 60 LABELS "guild;not-live-acceptance")
foreach(armor_bank_test IN ITEMS storage_owned_armor_bank_0067 storage_owned_armor_bank_adapter_0067 storage_owned_armor_bank_service_0067)
  add_executable(${armor_bank_test} ${armor_bank_test}.cpp)
  target_link_libraries(${armor_bank_test} PRIVATE god2_core)
  target_compile_definitions(${armor_bank_test} PRIVATE GOD2_SOURCE_DIR="${PROJECT_SOURCE_DIR}")
  add_test(NAME ${armor_bank_test} COMMAND ${armor_bank_test})
  set_tests_properties(${armor_bank_test} PROPERTIES TIMEOUT 120 LABELS "bank;storage;not-live-acceptance")
endforeach()
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_owned_party_position_query\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_owned_party_chat\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_owned_private_chat\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_owned_guild_chat\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_sqlite_guild\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_sqlite_guild_roster\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_owned_guild_roster\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_owned_guild_panel\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_owned_guild_membership_0078\\.cpp$")
add_executable(owned-guild-membership-0078 test_owned_guild_membership_0078.cpp)
target_include_directories(owned-guild-membership-0078 PRIVATE "${PROJECT_SOURCE_DIR}/src")
target_compile_features(owned-guild-membership-0078 PRIVATE cxx_std_20)
add_test(NAME owned_guild_membership_0078 COMMAND owned-guild-membership-0078)
set_tests_properties(owned_guild_membership_0078 PROPERTIES TIMEOUT 60 LABELS "guild;not-live-acceptance")
add_executable(owned-guild-panel test_owned_guild_panel.cpp)
add_executable(storage_owned_guild_leave_0077 storage_owned_guild_leave_0077.cpp)
target_link_libraries(storage_owned_guild_leave_0077 PRIVATE god2_core)
add_test(NAME storage_owned_guild_leave_0077 COMMAND storage_owned_guild_leave_0077)
set_tests_properties(storage_owned_guild_leave_0077 PROPERTIES TIMEOUT 60 LABELS "guild;storage;not-live-acceptance")
target_link_libraries(owned-guild-panel PRIVATE god2_core)
add_test(NAME owned_guild_panel COMMAND owned-guild-panel)
set_tests_properties(owned_guild_panel PROPERTIES TIMEOUT 60 LABELS "guild;not-live-acceptance")
add_executable(owned-guild-roster test_owned_guild_roster.cpp)
target_link_libraries(owned-guild-roster PRIVATE god2_core)
add_test(NAME owned_guild_roster COMMAND owned-guild-roster)
set_tests_properties(owned_guild_roster PROPERTIES TIMEOUT 60 LABELS "guild;not-live-acceptance")
add_executable(sqlite-guild-roster test_sqlite_guild_roster.cpp)
target_link_libraries(sqlite-guild-roster PRIVATE god2_core)
add_test(NAME sqlite_guild_roster COMMAND sqlite-guild-roster)
set_tests_properties(sqlite_guild_roster PROPERTIES TIMEOUT 60 LABELS "guild;not-live-acceptance")
add_executable(owned-guild-chat test_owned_guild_chat.cpp)
target_include_directories(owned-guild-chat PRIVATE "${PROJECT_SOURCE_DIR}/src")
target_compile_features(owned-guild-chat PRIVATE cxx_std_20)
add_test(NAME owned_guild_chat COMMAND owned-guild-chat)
add_executable(sqlite-guild test_sqlite_guild.cpp)
target_link_libraries(sqlite-guild PRIVATE god2_core)
add_test(NAME sqlite_guild COMMAND sqlite-guild)
set_tests_properties(owned_guild_chat sqlite_guild PROPERTIES TIMEOUT 60 LABELS "guild;not-live-acceptance")
add_executable(owned-private-chat test_owned_private_chat.cpp)
target_include_directories(owned-private-chat PRIVATE "${PROJECT_SOURCE_DIR}/src")
target_compile_features(owned-private-chat PRIVATE cxx_std_20)
add_test(NAME owned_private_chat COMMAND owned-private-chat)
add_executable(owned-party-chat test_owned_party_chat.cpp)
target_include_directories(owned-party-chat PRIVATE "${PROJECT_SOURCE_DIR}/src")
target_compile_features(owned-party-chat PRIVATE cxx_std_20)
add_test(NAME owned_party_chat COMMAND owned-party-chat)
add_executable(owned-party-position-query test_owned_party_position_query.cpp)
target_include_directories(owned-party-position-query PRIVATE "${PROJECT_SOURCE_DIR}/src")
target_compile_features(owned-party-position-query PRIVATE cxx_std_20)
add_test(NAME owned_party_position_query COMMAND owned-party-position-query)
set_tests_properties(owned_party_position_query PROPERTIES TIMEOUT 45 LABELS "party;not-live-acceptance")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_bank_items_repository\\.cpp$")
add_executable(bank-items-repository test_bank_items_repository.cpp)
target_link_libraries(bank-items-repository PRIVATE god2_core)
add_test(NAME bank_items_repository COMMAND bank-items-repository)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_bank_repository\\.cpp$")
add_executable(bank-repository test_bank_repository.cpp)
target_link_libraries(bank-repository PRIVATE god2_core)
add_test(NAME bank_repository COMMAND bank-repository)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_bank_service\\.cpp$")
add_executable(bank-service test_bank_service.cpp)
target_link_libraries(bank-service PRIVATE god2_core)
add_test(NAME bank_service COMMAND bank-service)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_trade\\.cpp$")
add_executable(recovered-trade test_recovered_trade.cpp)
target_include_directories(recovered-trade PRIVATE "${PROJECT_SOURCE_DIR}/src")
target_compile_features(recovered-trade PRIVATE cxx_std_20)
add_test(NAME recovered_trade COMMAND recovered-trade)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_trade_repository\\.cpp$")
add_executable(trade-repository test_trade_repository.cpp)
target_link_libraries(trade-repository PRIVATE god2_core)
add_test(NAME trade_repository COMMAND trade-repository)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_trade_service\\.cpp$")
add_executable(trade-service test_trade_service.cpp)
target_link_libraries(trade-service PRIVATE god2_core)
add_test(NAME trade_service COMMAND trade-service)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_native_party\\.cpp$")
add_executable(native-party test_native_party.cpp)
target_link_libraries(native-party PRIVATE god2_core)
add_test(NAME native_party COMMAND native-party)
foreach(packet_link_test IN ITEMS peer_role_text recovered_teleport_gem owned_teleport_gem_offer teleport_gem_repository)
  list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_${packet_link_test}\\.cpp$")
  string(REPLACE "_" "-" packet_link_target "${packet_link_test}")
  add_executable(${packet_link_target} test_${packet_link_test}.cpp)
  target_link_libraries(${packet_link_target} PRIVATE god2_core)
  add_test(NAME ${packet_link_test} COMMAND ${packet_link_target})
endforeach()
add_executable(packet-commit-review companion/test_packet_commit_review.cpp)
target_link_libraries(packet-commit-review PRIVATE god2_core)
target_compile_definitions(packet-commit-review PRIVATE GOD2_SOURCE_DIR="${PROJECT_SOURCE_DIR}")
add_test(NAME packet_commit_review COMMAND packet-commit-review)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_pet_reserve_move\\.cpp$")
add_executable(pet-reserve-move test_pet_reserve_move.cpp)
target_link_libraries(pet-reserve-move PRIVATE god2_core)
add_test(NAME pet_reserve_move COMMAND pet-reserve-move)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_role_text\\.cpp$")
add_executable(recovered-role-text test_recovered_role_text.cpp)
target_link_libraries(recovered-role-text PRIVATE god2_core)
add_test(NAME recovered_role_text COMMAND recovered-role-text)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_owned_role_text\\.cpp$")
add_executable(owned-role-text test_owned_role_text.cpp)
target_link_libraries(owned-role-text PRIVATE god2_core)
add_test(NAME owned_role_text COMMAND owned-role-text)
add_executable(role-text-review companion/test_role_text_review.cpp)
target_link_libraries(role-text-review PRIVATE god2_core)
add_test(NAME role_text_review COMMAND role-text-review)
add_executable(pet2-revert companion/test_pet2_revert.cpp)
target_link_libraries(pet2-revert PRIVATE god2_core)
add_test(NAME native_pet2_revert COMMAND pet2-revert)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_streamer_privilege\\.cpp$")
add_executable(streamer-privilege test_streamer_privilege.cpp)
target_link_libraries(streamer-privilege PRIVATE god2_core)
add_test(NAME streamer_privilege COMMAND streamer-privilege)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_pet1_stats\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_character_growth\\.cpp$")
add_executable(character-growth test_character_growth.cpp)
target_link_libraries(character-growth PRIVATE god2_core)
target_compile_definitions(character-growth PRIVATE GOD2_SOURCE_DIR="${PROJECT_SOURCE_DIR}")
add_test(NAME character_growth COMMAND character-growth)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_native_world_results\\.cpp$")
add_executable(native-world-results test_native_world_results.cpp)
target_link_libraries(native-world-results PRIVATE god2_core)
add_test(NAME native_world_results COMMAND native-world-results)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_native_skill_memory_reader\\.cpp$")
add_executable(native-skill-memory-reader test_native_skill_memory_reader.cpp)
target_link_libraries(native-skill-memory-reader PRIVATE god2_core)
foreach(quest_policy_test IN ITEMS inferred_quest_rules fruit_village_quest_rules recovered_quest_reward_notice)
  list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_${quest_policy_test}\\.cpp$")
  add_executable(${quest_policy_test} test_${quest_policy_test}.cpp)
  target_include_directories(${quest_policy_test} PRIVATE "${PROJECT_SOURCE_DIR}/src")
  target_compile_features(${quest_policy_test} PRIVATE cxx_std_20)
  add_test(NAME ${quest_policy_test} COMMAND ${quest_policy_test})
endforeach()
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_fruit_quest_repository\\.cpp$")
add_executable(fruit-quest-repository test_fruit_quest_repository.cpp)
target_link_libraries(fruit-quest-repository PRIVATE god2_core)
target_compile_definitions(fruit-quest-repository PRIVATE GOD2_SOURCE_DIR="${PROJECT_SOURCE_DIR}")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_fruit_navigation\\.cpp$")
add_executable(recovered-fruit-navigation test_recovered_fruit_navigation.cpp)
target_link_libraries(recovered-fruit-navigation PRIVATE god2_core)
target_compile_definitions(recovered-fruit-navigation PRIVATE GOD2_SOURCE_DIR="${PROJECT_SOURCE_DIR}")
add_test(NAME recovered_fruit_navigation COMMAND recovered-fruit-navigation "${PROJECT_SOURCE_DIR}/artifacts/world-atlas/fruit-13-12.json")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_native_npc_display\\.cpp$")
add_executable(native-npc-display test_native_npc_display.cpp)
target_link_libraries(native-npc-display PRIVATE god2_core)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_native_enemy_display_catalog_integrity\\.cpp$")
add_executable(native-enemy-display-integrity test_native_enemy_display_catalog_integrity.cpp)
target_link_libraries(native-enemy-display-integrity PRIVATE god2_core)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_native_supply_catalog_integrity\\.cpp$")
add_executable(native-supply-catalog-integrity test_native_supply_catalog_integrity.cpp)
target_link_libraries(native-supply-catalog-integrity PRIVATE god2_core)
target_compile_definitions(native-supply-catalog-integrity PRIVATE GOD2_SOURCE_DIR="${PROJECT_SOURCE_DIR}")
add_test(NAME native_supply_catalog_integrity COMMAND native-supply-catalog-integrity)
set_tests_properties(native_supply_catalog_integrity PROPERTIES TIMEOUT 60)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_player_appearance_snapshot\\.cpp$")
add_executable(player-appearance-snapshot test_player_appearance_snapshot.cpp)
target_link_libraries(player-appearance-snapshot PRIVATE god2_core)
add_test(NAME player_appearance_snapshot COMMAND player-appearance-snapshot)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_player_appearance_update\\.cpp$")
add_executable(player-appearance-update test_player_appearance_update.cpp)
target_include_directories(player-appearance-update PRIVATE "${PROJECT_SOURCE_DIR}/src")
target_compile_features(player-appearance-update PRIVATE cxx_std_20)
add_test(NAME player_appearance_update COMMAND player-appearance-update)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_owned_weapon_transfer\\.cpp$")
add_executable(owned-weapon-transfer test_owned_weapon_transfer.cpp)
target_link_libraries(owned-weapon-transfer PRIVATE god2_core)
add_test(NAME owned_weapon_transfer COMMAND owned-weapon-transfer)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_weapon_slots\\.cpp$")
add_executable(weapon-slots test_weapon_slots.cpp)
target_link_libraries(weapon-slots PRIVATE god2_core)
add_test(NAME weapon_slots COMMAND weapon-slots)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_armor_slots\\.cpp$")
add_executable(armor-slots test_armor_slots.cpp)
target_link_libraries(armor-slots PRIVATE god2_core)
add_test(NAME armor_slots COMMAND armor-slots)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_owned_armor_transfer\\.cpp$")
add_executable(owned-armor-transfer test_owned_armor_transfer.cpp)
target_link_libraries(owned-armor-transfer PRIVATE god2_core)
add_test(NAME owned_armor_transfer COMMAND owned-armor-transfer)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_owned_bag_projection\\.cpp$")
add_executable(owned-bag-projection test_owned_bag_projection.cpp)
target_link_libraries(owned-bag-projection PRIVATE god2_core)
add_test(NAME owned_bag_projection COMMAND owned-bag-projection)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_armor_source_instance\\.cpp$")
add_executable(recovered-armor-source-instance test_recovered_armor_source_instance.cpp)
target_link_libraries(recovered-armor-source-instance PRIVATE god2_core)
add_test(NAME recovered_armor_source_instance COMMAND recovered-armor-source-instance)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_owned_bank_trade_projection\\.cpp$")
add_executable(owned-bank-trade-projection test_owned_bank_trade_projection.cpp)
target_link_libraries(owned-bank-trade-projection PRIVATE god2_core)
add_test(NAME owned_bank_trade_projection COMMAND owned-bank-trade-projection)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_sqlite_armor_production_adapter\\.cpp$")
add_executable(sqlite-armor-production-adapter test_sqlite_armor_production_adapter.cpp)
target_link_libraries(sqlite-armor-production-adapter PRIVATE god2_core)
target_compile_definitions(sqlite-armor-production-adapter PRIVATE GOD2_SOURCE_DIR="${PROJECT_SOURCE_DIR}")
add_test(NAME sqlite_armor_production_adapter COMMAND sqlite-armor-production-adapter)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_armor_instance\\.cpp$")
add_executable(recovered-armor-instance test_recovered_armor_instance.cpp)
target_link_libraries(recovered-armor-instance PRIVATE god2_core)
target_compile_definitions(recovered-armor-instance PRIVATE GOD2_SOURCE_DIR="${PROJECT_SOURCE_DIR}")
add_test(NAME recovered_armor_instance COMMAND recovered-armor-instance)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_native_armor_catalog\\.cpp$")
add_executable(native-armor-catalog test_native_armor_catalog.cpp)
target_link_libraries(native-armor-catalog PRIVATE god2_core)
target_compile_definitions(native-armor-catalog PRIVATE GOD2_SOURCE_DIR="${PROJECT_SOURCE_DIR}")
add_test(NAME native_armor_catalog COMMAND native-armor-catalog)
set_tests_properties(native_armor_catalog PROPERTIES TIMEOUT 60)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_native_weapon_catalog\\.cpp$")
add_executable(native-weapon-catalog test_native_weapon_catalog.cpp)
target_link_libraries(native-weapon-catalog PRIVATE god2_core)
target_compile_definitions(native-weapon-catalog PRIVATE GOD2_SOURCE_DIR="${PROJECT_SOURCE_DIR}")
add_test(NAME native_weapon_catalog COMMAND native-weapon-catalog)
set_tests_properties(native_weapon_catalog PROPERTIES TIMEOUT 60)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_owned_role_auxiliary\\.cpp$")
add_executable(owned-role-auxiliary test_owned_role_auxiliary.cpp)
target_link_libraries(owned-role-auxiliary PRIVATE god2_core)
add_test(NAME owned_role_auxiliary COMMAND owned-role-auxiliary)

list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_role_auxiliary\\.cpp$")
add_executable(recovered-role-auxiliary test_recovered_role_auxiliary.cpp)
target_include_directories(recovered-role-auxiliary PRIVATE "${PROJECT_SOURCE_DIR}/src")
target_compile_features(recovered-role-auxiliary PRIVATE cxx_std_20)
add_test(NAME recovered_role_auxiliary COMMAND recovered-role-auxiliary)

list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_native_map_item_catalog\\.cpp$")
add_executable(native-map-item-catalog test_native_map_item_catalog.cpp)
target_link_libraries(native-map-item-catalog PRIVATE god2_core)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_owned_map_view\\.cpp$")
add_executable(owned-map-view test_owned_map_view.cpp)
target_link_libraries(owned-map-view PRIVATE god2_core)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_native_multi_message\\.cpp$")
add_executable(native-multi-message test_native_multi_message.cpp)
target_link_libraries(native-multi-message PRIVATE god2_core)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_knowledge_conversation\\.cpp$")
add_executable(knowledge-conversation test_knowledge_conversation.cpp)
target_include_directories(knowledge-conversation PRIVATE "${PROJECT_SOURCE_DIR}/src")
target_compile_features(knowledge-conversation PRIVATE cxx_std_20)
add_test(NAME knowledge_conversation COMMAND knowledge-conversation)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_quest_menu\\.cpp$")
add_executable(recovered-quest-menu test_recovered_quest_menu.cpp)
target_include_directories(recovered-quest-menu PRIVATE "${PROJECT_SOURCE_DIR}/src")
add_test(NAME recovered_quest_menu COMMAND recovered-quest-menu)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_world_clock\\.cpp$")
add_executable(recovered-world-clock test_recovered_world_clock.cpp)
target_include_directories(recovered-world-clock PRIVATE "${PROJECT_SOURCE_DIR}/src")
target_compile_features(recovered-world-clock PRIVATE cxx_std_20)
add_test(NAME recovered_world_clock COMMAND recovered-world-clock)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_quest_journal\\.cpp$")
add_executable(quest-journal test_quest_journal.cpp)
target_link_libraries(quest-journal PRIVATE god2_core)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_daily_quest_request\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_kunlun_birthplace\\.cpp$")
add_executable(kunlun-birthplace test_kunlun_birthplace.cpp)
target_link_libraries(kunlun-birthplace PRIVATE god2_core)
target_compile_definitions(kunlun-birthplace PRIVATE GOD2_SOURCE_DIR="${PROJECT_SOURCE_DIR}")
add_test(NAME kunlun_birthplace COMMAND kunlun-birthplace)
set_tests_properties(kunlun_birthplace PROPERTIES TIMEOUT 20)
foreach(companion_test IN ITEMS recovered_player_snapshot recovered_deity recovered_pet2_lifecycle owned_companions)
  list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_${companion_test}\\.cpp$")
  add_executable(${companion_test} test_${companion_test}.cpp)
  target_link_libraries(${companion_test} PRIVATE god2_core)
  add_test(NAME ${companion_test} COMMAND ${companion_test})
endforeach()
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_native_pet2_categories\\.cpp$")
add_executable(native-pet2-categories test_native_pet2_categories.cpp)
target_link_libraries(native-pet2-categories PRIVATE god2_core)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_inventory_move\\.cpp$")
add_executable(inventory-move test_inventory_move.cpp)
target_link_libraries(inventory-move PRIVATE god2_core)
add_test(NAME inventory_move COMMAND inventory-move)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_inventory_discard\\.cpp$")
add_executable(inventory-discard test_inventory_discard.cpp)
target_link_libraries(inventory-discard PRIVATE god2_core)
add_test(NAME inventory_discard COMMAND inventory-discard)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_inventory_move\\.cpp$")
add_executable(recovered-inventory-move test_recovered_inventory_move.cpp)
target_include_directories(recovered-inventory-move PRIVATE "${PROJECT_SOURCE_DIR}/src")
target_compile_features(recovered-inventory-move PRIVATE cxx_std_20)
add_test(NAME recovered_inventory_move COMMAND recovered-inventory-move)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_login_failure\\.cpp$")
add_executable(recovered-login-failure test_recovered_login_failure.cpp)
target_link_libraries(recovered-login-failure PRIVATE god2_core)
add_test(NAME recovered_login_failure COMMAND recovered-login-failure)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_island_entry_navigation\\.cpp$")
add_executable(recovered-island-entry-navigation test_recovered_island_entry_navigation.cpp)
target_link_libraries(recovered-island-entry-navigation PRIVATE god2_core)
target_compile_definitions(recovered-island-entry-navigation PRIVATE GOD2_SOURCE_DIR="${PROJECT_SOURCE_DIR}")
add_test(NAME recovered_island_entry_navigation COMMAND recovered-island-entry-navigation)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_chinese_text\\.cpp$")
add_executable(chinese-text test_chinese_text.cpp)
target_link_libraries(chinese-text PRIVATE god2_core)
target_compile_definitions(chinese-text PRIVATE GOD2_SOURCE_DIR="${PROJECT_SOURCE_DIR}")
add_test(NAME chinese_text COMMAND chinese-text)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_visibility\\.cpp$")
add_executable(recovered-visibility test_recovered_visibility.cpp)
target_include_directories(recovered-visibility PRIVATE "${PROJECT_SOURCE_DIR}/src")
target_compile_features(recovered-visibility PRIVATE cxx_std_20)
add_test(NAME recovered_visibility COMMAND recovered-visibility)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_remote_actor\\.cpp$")
add_executable(recovered-remote-actor test_recovered_remote_actor.cpp)
target_include_directories(recovered-remote-actor PRIVATE "${PROJECT_SOURCE_DIR}/src")
target_compile_features(recovered-remote-actor PRIVATE cxx_std_20)
add_test(NAME recovered_remote_actor COMMAND recovered-remote-actor)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_diagnostic_door\\.cpp$")
add_executable(diagnostic-door test_diagnostic_door.cpp)
target_link_libraries(diagnostic-door PRIVATE god2_core)
target_compile_definitions(diagnostic-door PRIVATE GOD2_SOURCE_DIR="${PROJECT_SOURCE_DIR}")
add_test(NAME diagnostic_door COMMAND diagnostic-door)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_wilderness_transfers\\.cpp$")
add_executable(wilderness-transfers test_wilderness_transfers.cpp)
target_link_libraries(wilderness-transfers PRIVATE god2_core)
target_compile_definitions(wilderness-transfers PRIVATE GOD2_SOURCE_DIR="${PROJECT_SOURCE_DIR}")
add_test(NAME wilderness_transfers COMMAND wilderness-transfers)
set_tests_properties(wilderness_transfers PROPERTIES TIMEOUT 120 LABELS "movement;source-qualified;not-native-acceptance")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_cross_map_transfers\\.cpp$")
add_executable(cross-map-transfers test_cross_map_transfers.cpp test_config.cpp)
target_link_libraries(cross-map-transfers PRIVATE god2_core)
target_compile_definitions(cross-map-transfers PRIVATE GOD2_SOURCE_DIR="${PROJECT_SOURCE_DIR}")
add_test(NAME cross_map_transfers COMMAND cross-map-transfers)
set_tests_properties(cross_map_transfers PROPERTIES TIMEOUT 120 LABELS "movement;source-qualified;not-native-acceptance")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_world_transfers\\.cpp$")
add_executable(world-transfers test_world_transfers.cpp test_config.cpp)
target_link_libraries(world-transfers PRIVATE god2_core)
target_compile_definitions(world-transfers PRIVATE GOD2_SOURCE_DIR="${PROJECT_SOURCE_DIR}")
add_test(NAME world_transfers COMMAND world-transfers)
set_tests_properties(world_transfers PROPERTIES TIMEOUT 300 LABELS "movement;world;source-qualified;not-native-acceptance")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_owned_npc_teleport_offer\\.cpp$")
add_executable(owned-npc-teleport-offer test_owned_npc_teleport_offer.cpp)
target_link_libraries(owned-npc-teleport-offer PRIVATE god2_core)
add_test(NAME owned_npc_teleport_offer COMMAND owned-npc-teleport-offer)
set_tests_properties(owned_npc_teleport_offer PROPERTIES TIMEOUT 120 LABELS "world;npc;issued-offer;not-native-acceptance")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_parent_route\\.cpp$")
add_executable(recovered-parent-route test_recovered_parent_route.cpp)
target_link_libraries(recovered-parent-route PRIVATE god2_core)
target_compile_definitions(recovered-parent-route PRIVATE GOD2_SOURCE_DIR="${PROJECT_SOURCE_DIR}")
add_test(NAME recovered_parent_route COMMAND recovered-parent-route)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_battle_process_crash\\.cpp$")
add_executable(battle-process-crash test_battle_process_crash.cpp)
target_link_libraries(battle-process-crash PRIVATE god2_core)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_diagnostic_town_npc\\.cpp$")
add_executable(diagnostic-town-npc test_diagnostic_town_npc.cpp)
target_include_directories(diagnostic-town-npc PRIVATE "${PROJECT_SOURCE_DIR}/src")
target_compile_features(diagnostic-town-npc PRIVATE cxx_std_20)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_battle_revival\\.cpp$")
add_executable(battle-revival test_battle_revival.cpp)
target_link_libraries(battle-revival PRIVATE god2_core)
target_compile_definitions(battle-revival PRIVATE GOD2_SOURCE_DIR="${PROJECT_SOURCE_DIR}")
add_test(NAME battle_revival COMMAND battle-revival)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_diagnostic_supply\\.cpp$")
add_executable(diagnostic-supply test_diagnostic_supply.cpp)
target_link_libraries(diagnostic-supply PRIVATE god2_core)
target_compile_definitions(diagnostic-supply PRIVATE GOD2_SOURCE_DIR="${PROJECT_SOURCE_DIR}")
add_test(NAME diagnostic_supply COMMAND diagnostic-supply)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_role_level\\.cpp$")
add_executable(recovered-role-level test_recovered_role_level.cpp)
target_include_directories(recovered-role-level PRIVATE "${PROJECT_SOURCE_DIR}/src")
target_compile_features(recovered-role-level PRIVATE cxx_std_20)
add_test(NAME recovered_role_level COMMAND recovered-role-level)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_progression_lua\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_supply_lua\\.cpp$")
add_executable(supply-lua test_supply_lua.cpp)
target_link_libraries(supply-lua PRIVATE god2_core)
target_compile_definitions(supply-lua PRIVATE GOD2_SOURCE_DIR="${PROJECT_SOURCE_DIR}")
add_test(NAME supply_lua COMMAND supply-lua)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_town_guide_lua\\.cpp$")
add_executable(town-guide-lua test_town_guide_lua.cpp)
target_link_libraries(town-guide-lua PRIVATE god2_core)
target_compile_definitions(town-guide-lua PRIVATE GOD2_SOURCE_DIR="${PROJECT_SOURCE_DIR}")
add_test(NAME town_guide_lua COMMAND town-guide-lua)
add_executable(progression-lua test_progression_lua.cpp)
target_link_libraries(progression-lua PRIVATE god2_core)
target_compile_definitions(progression-lua PRIVATE GOD2_SOURCE_DIR="${PROJECT_SOURCE_DIR}")
add_test(NAME progression_lua COMMAND progression-lua)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_role_progress\\.cpp$")
add_executable(recovered-role-progress test_recovered_role_progress.cpp)
target_include_directories(recovered-role-progress PRIVATE "${PROJECT_SOURCE_DIR}/src")
target_compile_features(recovered-role-progress PRIVATE cxx_std_20)
add_test(NAME recovered_role_progress COMMAND recovered-role-progress)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_battle_service\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_shunying_sanshazhan\\.cpp$")
add_executable(shunying-sanshazhan test_shunying_sanshazhan.cpp)
target_link_libraries(shunying-sanshazhan PRIVATE god2_core)
add_test(NAME shunying_sanshazhan COMMAND shunying-sanshazhan)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_thousand_bulls\\.cpp$")
add_executable(thousand-bulls-blackbox "${PROJECT_SOURCE_DIR}/tools/skills/thousand_bulls_blackbox.cpp")
target_link_libraries(thousand-bulls-blackbox PRIVATE god2_core)
target_compile_definitions(thousand-bulls-blackbox PRIVATE GOD2_SOURCE_DIR="${PROJECT_SOURCE_DIR}")
add_test(NAME thousand_bulls_blackbox COMMAND thousand-bulls-blackbox)
set_tests_properties(thousand_bulls_blackbox PROPERTIES TIMEOUT 60 LABELS "custom0059;tcp-fixture;not-native-ui-acceptance")
add_executable(thousand-bulls test_thousand_bulls.cpp)
target_link_libraries(thousand-bulls PRIVATE god2_core)
add_test(NAME thousand_bulls COMMAND thousand-bulls)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_battle_transaction\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_combat_rule_lua\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_battle_bootstrap\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_world_service\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_fixture_battle\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_fixture_combat_lua\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_server_routes\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_world_entry\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_indoor_grid\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_outdoor_window\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_town_navigation\\.cpp$")
add_executable(recovered-town-navigation test_recovered_town_navigation.cpp)
target_link_libraries(recovered-town-navigation PRIVATE god2_core)
target_compile_definitions(recovered-town-navigation PRIVATE GOD2_SOURCE_DIR="${PROJECT_SOURCE_DIR}")
add_test(NAME recovered_town_navigation COMMAND recovered-town-navigation)
set_tests_properties(recovered_town_navigation PROPERTIES TIMEOUT 15)
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_movement\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_npc_spawn\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_world_frame\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_inventory\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_quest_sync\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_battle_command\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_character_context\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_skill_command\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_battle_experience\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_instance_update\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_pet2_stats\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_battle_vitals_batch\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_npc_record\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_native_map_catalog\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_native_enemy_display_catalog\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_native_supply_catalog\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_native_catalog_lua\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_world_records\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_teleport\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_native_skill_catalog\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_native_skill_book_catalog\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_native_skill_lua\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_native_skill_targeting\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_battle_result_flags\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_battle_participant\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_battle_vitals\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_pk_result_sequence\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_taiwan_world_identity_write_fence\\.cpp$")
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_taiwan_battle_self_view\\.cpp$")
add_executable(god2-tests ${TEST_SOURCES})
add_executable(recovered-battle-service test_recovered_battle_service.cpp)
target_link_libraries(recovered-battle-service PRIVATE god2_core)
target_compile_definitions(recovered-battle-service PRIVATE GOD2_SOURCE_DIR="${PROJECT_SOURCE_DIR}")
add_test(NAME recovered_battle_service COMMAND recovered-battle-service)
set_tests_properties(recovered_battle_service PROPERTIES TIMEOUT 30)
add_executable(battle-transaction test_battle_transaction.cpp)
target_link_libraries(battle-transaction PRIVATE god2_core)
target_compile_definitions(battle-transaction PRIVATE GOD2_SOURCE_DIR="${PROJECT_SOURCE_DIR}")
add_test(NAME battle_transaction COMMAND battle-transaction)
set_tests_properties(battle_transaction PROPERTIES TIMEOUT 30)
add_executable(combat-rule-lua test_combat_rule_lua.cpp)
target_link_libraries(combat-rule-lua PRIVATE god2_core)
target_compile_definitions(combat-rule-lua PRIVATE GOD2_SOURCE_DIR="${PROJECT_SOURCE_DIR}")
add_test(NAME combat_rule_lua COMMAND combat-rule-lua)
set_tests_properties(combat_rule_lua PROPERTIES TIMEOUT 30)
add_executable(recovered-battle-bootstrap test_recovered_battle_bootstrap.cpp)
target_include_directories(recovered-battle-bootstrap PRIVATE "${PROJECT_SOURCE_DIR}/src")
target_compile_features(recovered-battle-bootstrap PRIVATE cxx_std_20)
add_test(NAME recovered_battle_bootstrap COMMAND recovered-battle-bootstrap)
add_executable(recovered-pk-result-sequence test_recovered_pk_result_sequence.cpp)
target_include_directories(recovered-pk-result-sequence PRIVATE "${PROJECT_SOURCE_DIR}/src")
target_compile_features(recovered-pk-result-sequence PRIVATE cxx_std_20)
add_test(NAME recovered_pk_result_sequence COMMAND recovered-pk-result-sequence)
set_tests_properties(recovered_pk_result_sequence PROPERTIES TIMEOUT 15 LABELS "battle;not-native-ui-acceptance")
add_executable(taiwan-world-identity-write-fence test_taiwan_world_identity_write_fence.cpp)
target_include_directories(taiwan-world-identity-write-fence PRIVATE "${PROJECT_SOURCE_DIR}/src")
target_compile_features(taiwan-world-identity-write-fence PRIVATE cxx_std_20)
add_test(NAME taiwan_world_identity_write_fence COMMAND taiwan-world-identity-write-fence)
set_tests_properties(taiwan_world_identity_write_fence PROPERTIES TIMEOUT 15 LABELS "world;source-custody;not-native-ui-acceptance")
add_executable(taiwan-battle-self-view test_taiwan_battle_self_view.cpp)
target_include_directories(taiwan-battle-self-view PRIVATE "${PROJECT_SOURCE_DIR}/src")
target_compile_features(taiwan-battle-self-view PRIVATE cxx_std_20)
add_test(NAME taiwan_battle_self_view COMMAND taiwan-battle-self-view)
set_tests_properties(taiwan_battle_self_view PROPERTIES TIMEOUT 15 LABELS "battle;source-custody;not-native-ui-acceptance")
add_executable(recovered-world-service test_recovered_world_service.cpp)
target_link_libraries(recovered-world-service PRIVATE god2_core)
add_test(NAME recovered_world_service COMMAND recovered-world-service)
set_tests_properties(recovered_world_service PROPERTIES TIMEOUT 30)
target_link_libraries(god2-tests PRIVATE god2_core)
target_compile_definitions(god2-tests PRIVATE GOD2_SOURCE_DIR="${PROJECT_SOURCE_DIR}")
add_test(NAME taiwan_native_hmd_bundle_source COMMAND god2-tests taiwan_native_hmd_bundle_source)
set_tests_properties(taiwan_native_hmd_bundle_source PROPERTIES TIMEOUT 30)
add_test(NAME taiwan_channel_worlds COMMAND god2-tests taiwan_channel_worlds)
set_tests_properties(taiwan_channel_worlds PROPERTIES TIMEOUT 30 LABELS "world;channels;source-custody;not-live-acceptance")
add_test(NAME taiwan_channel_servers COMMAND god2-tests taiwan_channel_servers)
set_tests_properties(taiwan_channel_servers PROPERTIES TIMEOUT 30 LABELS "network;channels;source-custody;not-live-acceptance")
add_test(NAME application_game_frame COMMAND god2-tests application_game_frame)
set_tests_properties(application_game_frame PROPERTIES TIMEOUT 15 LABELS "core;channels;source-lifetime;not-live-acceptance")
add_test(NAME application_game_sources COMMAND god2-tests application_game_sources)
set_tests_properties(application_game_sources PROPERTIES TIMEOUT 15 LABELS "core;channels;source-lifetime;not-live-acceptance")
add_test(NAME taiwan_channel_character_lists COMMAND god2-tests taiwan_channel_character_lists)
set_tests_properties(taiwan_channel_character_lists PROPERTIES TIMEOUT 30 LABELS "network;channels;source-custody;not-live-acceptance")
add_test(NAME taiwan_three_channel_plan COMMAND god2-tests taiwan_three_channel_plan)
set_tests_properties(taiwan_three_channel_plan PROPERTIES TIMEOUT 15 LABELS "core;channels;source-preflight;not-live-acceptance")
add_test(NAME shared_guild_channel_directory53 COMMAND god2-tests shared_guild_channel_directory53)
set_tests_properties(shared_guild_channel_directory53 PROPERTIES TIMEOUT 15 LABELS "guild;channels;source-custody;not-live-acceptance")
add_test(NAME owned_taiwan_guild_chat_dispatch COMMAND god2-tests owned_taiwan_guild_chat_dispatch)
set_tests_properties(owned_taiwan_guild_chat_dispatch PROPERTIES TIMEOUT 15 LABELS "guild;channels;source-custody;not-live-acceptance")
add_test(NAME owned_taiwan_guild_actions_dispatch COMMAND god2-tests owned_taiwan_guild_actions_dispatch)
set_tests_properties(owned_taiwan_guild_actions_dispatch PROPERTIES TIMEOUT 120 LABELS "guild;channels;network;source-custody;not-live-acceptance")
add_test(NAME world_reply_push_capture COMMAND god2-tests world_reply_push_capture)
set_tests_properties(world_reply_push_capture PROPERTIES TIMEOUT 120 LABELS "guild;channels;network;source-custody;not-live-acceptance")
foreach(suite packet decoder dispatcher lua session_state protocol_replay database network config post_server_select legacy_character_list_candidate character_create password_hash recovered_account_login recovered_character_repository recovered_character_list post_create_select recovered_movement_service recovered_position_repository)
  add_test(NAME ${suite} COMMAND god2-tests ${suite})
  set_tests_properties(${suite} PROPERTIES TIMEOUT 30)
endforeach()
set_tests_properties(session_state PROPERTIES TIMEOUT 180)
add_test(NAME session_skill_sequence COMMAND god2-tests session_skill_sequence)
add_test(NAME session_battle_service COMMAND god2-tests session_battle_service)
set_tests_properties(session_battle_service PROPERTIES TIMEOUT 30)
add_executable(fixture-battle test_fixture_battle.cpp)
target_link_libraries(fixture-battle PRIVATE god2_core)
add_test(NAME fixture_battle COMMAND fixture-battle)
set_tests_properties(fixture_battle PROPERTIES TIMEOUT 30)
add_executable(fixture-combat-lua test_fixture_combat_lua.cpp)
target_link_libraries(fixture-combat-lua PRIVATE god2_core)
target_compile_definitions(fixture-combat-lua PRIVATE GOD2_SOURCE_DIR="${PROJECT_SOURCE_DIR}")
add_test(NAME fixture_combat_lua COMMAND fixture-combat-lua)
set_tests_properties(fixture_combat_lua PROPERTIES TIMEOUT 30)
set_tests_properties(session_skill_sequence PROPERTIES TIMEOUT 60)
add_executable(recovered-server-routes test_recovered_server_routes.cpp)
target_include_directories(recovered-server-routes PRIVATE ${PROJECT_SOURCE_DIR}/src)
add_test(NAME recovered_server_routes COMMAND recovered-server-routes)
set_tests_properties(recovered_server_routes PROPERTIES TIMEOUT 10)
add_executable(recovered-world-entry test_recovered_world_entry.cpp)
target_include_directories(recovered-world-entry PRIVATE ${PROJECT_SOURCE_DIR}/src)
add_test(NAME recovered_world_entry COMMAND recovered-world-entry)
set_tests_properties(recovered_world_entry PROPERTIES TIMEOUT 10)
add_executable(recovered-indoor-grid test_recovered_indoor_grid.cpp)
target_include_directories(recovered-indoor-grid PRIVATE ${PROJECT_SOURCE_DIR}/src)
if(MSVC)
  target_compile_options(recovered-indoor-grid PRIVATE /W4 /WX /permissive- /utf-8)
else()
  target_compile_options(recovered-indoor-grid PRIVATE -Wall -Wextra -Wpedantic -Werror)
endif()
add_test(NAME recovered_indoor_grid COMMAND recovered-indoor-grid)
add_executable(recovered-outdoor-window test_recovered_outdoor_window.cpp)
target_include_directories(recovered-outdoor-window PRIVATE ${PROJECT_SOURCE_DIR}/src)
if(MSVC)
  target_compile_options(recovered-outdoor-window PRIVATE /W4 /WX /permissive- /utf-8)
else()
  target_compile_options(recovered-outdoor-window PRIVATE -Wall -Wextra -Wpedantic -Werror)
endif()
add_test(NAME recovered_outdoor_window COMMAND recovered-outdoor-window)
set_tests_properties(recovered_outdoor_window PROPERTIES TIMEOUT 10)
set_tests_properties(recovered_indoor_grid PROPERTIES TIMEOUT 10)
add_executable(recovered-movement test_recovered_movement.cpp)
target_include_directories(recovered-movement PRIVATE ${PROJECT_SOURCE_DIR}/src)
target_compile_features(recovered-movement PRIVATE cxx_std_20)
if(MSVC)
  target_compile_options(recovered-movement PRIVATE /W4 /WX /permissive- /utf-8)
else()
  target_compile_options(recovered-movement PRIVATE -Wall -Wextra -Wpedantic -Werror)
endif()
add_test(NAME recovered_movement COMMAND recovered-movement)
set_tests_properties(recovered_movement PROPERTIES TIMEOUT 10)
add_executable(recovered-npc-spawn test_recovered_npc_spawn.cpp)
target_include_directories(recovered-npc-spawn PRIVATE ${PROJECT_SOURCE_DIR}/src)
target_compile_features(recovered-npc-spawn PRIVATE cxx_std_20)
if(MSVC)
  target_compile_options(recovered-npc-spawn PRIVATE /W4 /WX /permissive- /utf-8)
else()
  target_compile_options(recovered-npc-spawn PRIVATE -Wall -Wextra -Wpedantic -Werror)
endif()
add_test(NAME recovered_npc_spawn COMMAND recovered-npc-spawn)
set_tests_properties(recovered_npc_spawn PROPERTIES TIMEOUT 10)
add_executable(recovered-world-frame test_recovered_world_frame.cpp)
target_include_directories(recovered-world-frame PRIVATE ${PROJECT_SOURCE_DIR}/src)
target_compile_features(recovered-world-frame PRIVATE cxx_std_20)
if(MSVC)
  target_compile_options(recovered-world-frame PRIVATE /W4 /WX /permissive- /utf-8)
else()
  target_compile_options(recovered-world-frame PRIVATE -Wall -Wextra -Wpedantic -Werror)
endif()
add_test(NAME recovered_world_frame COMMAND recovered-world-frame)
set_tests_properties(recovered_world_frame PROPERTIES TIMEOUT 10)
add_executable(recovered-inventory test_recovered_inventory.cpp)
target_include_directories(recovered-inventory PRIVATE ${PROJECT_SOURCE_DIR}/src)
target_compile_features(recovered-inventory PRIVATE cxx_std_20)
if(MSVC)
  target_compile_options(recovered-inventory PRIVATE /W4 /WX /permissive- /utf-8)
else()
  target_compile_options(recovered-inventory PRIVATE -Wall -Wextra -Wpedantic -Werror)
endif()
add_test(NAME recovered_inventory COMMAND recovered-inventory)
set_tests_properties(recovered_inventory PROPERTIES TIMEOUT 10)
foreach(module quest-sync battle-command character-context skill-command battle-experience instance-update npc-record world-records battle-result-flags battle-participant battle-vitals teleport)
  string(REPLACE "-" "_" source_name ${module})
  add_executable(recovered-${module} test_recovered_${source_name}.cpp)
  target_include_directories(recovered-${module} PRIVATE ${PROJECT_SOURCE_DIR}/src)
  target_compile_features(recovered-${module} PRIVATE cxx_std_20)
  if(MSVC)
    target_compile_options(recovered-${module} PRIVATE /W4 /WX /permissive- /utf-8)
  else()
    target_compile_options(recovered-${module} PRIVATE -Wall -Wextra -Wpedantic -Werror)
  endif()
  add_test(NAME recovered_${source_name} COMMAND recovered-${module})
  set_tests_properties(recovered_${source_name} PROPERTIES TIMEOUT 10)
endforeach()
add_executable(native-map-catalog test_native_map_catalog.cpp)
target_link_libraries(native-map-catalog PRIVATE god2_core)
add_test(NAME native_map_catalog COMMAND native-map-catalog)
set_tests_properties(native_map_catalog PROPERTIES TIMEOUT 10)
add_executable(native-enemy-display-catalog test_native_enemy_display_catalog.cpp)
target_link_libraries(native-enemy-display-catalog PRIVATE god2_core)
add_test(NAME native_enemy_display_catalog COMMAND native-enemy-display-catalog)
set_tests_properties(native_enemy_display_catalog PROPERTIES TIMEOUT 10)
add_executable(native-supply-catalog test_native_supply_catalog.cpp)
target_link_libraries(native-supply-catalog PRIVATE god2_core)
add_test(NAME native_supply_catalog COMMAND native-supply-catalog)
set_tests_properties(native_supply_catalog PROPERTIES TIMEOUT 10)
add_executable(native-catalog-lua test_native_catalog_lua.cpp)
target_link_libraries(native-catalog-lua PRIVATE god2_core)
add_test(NAME native_catalog_lua COMMAND native-catalog-lua)
set_tests_properties(native_catalog_lua PROPERTIES TIMEOUT 30)
add_executable(native-skill-catalog test_native_skill_catalog.cpp)
add_executable(native-quest-catalog-reader read_native_quest_catalog.cpp)
target_link_libraries(native-quest-catalog-reader PRIVATE god2_core)
add_executable(recovered-daily-quest-request test_recovered_daily_quest_request.cpp)
target_link_libraries(recovered-daily-quest-request PRIVATE god2_core)
add_test(NAME recovered_daily_quest_request COMMAND recovered-daily-quest-request)
set_tests_properties(recovered_daily_quest_request PROPERTIES TIMEOUT 15)
target_link_libraries(native-skill-catalog PRIVATE god2_core)
add_test(NAME native_skill_catalog COMMAND native-skill-catalog)
set_tests_properties(native_skill_catalog PROPERTIES TIMEOUT 30)
add_executable(native-skill-book-catalog test_native_skill_book_catalog.cpp)
target_link_libraries(native-skill-book-catalog PRIVATE god2_core)
add_test(NAME native_skill_book_catalog COMMAND native-skill-book-catalog)
set_tests_properties(native_skill_book_catalog PROPERTIES TIMEOUT 30)
add_executable(native-skill-lua test_native_skill_lua.cpp)
target_link_libraries(native-skill-lua PRIVATE god2_core)
add_test(NAME native_skill_lua COMMAND native-skill-lua)
set_tests_properties(native_skill_lua PROPERTIES TIMEOUT 30)
add_executable(native-skill-targeting test_native_skill_targeting.cpp)
target_include_directories(native-skill-targeting PRIVATE ${PROJECT_SOURCE_DIR}/src)
if(MSVC)
  target_compile_options(native-skill-targeting PRIVATE /W4 /WX /permissive-)
endif()
add_test(NAME native_skill_targeting COMMAND native-skill-targeting)
set_tests_properties(native_skill_targeting PROPERTIES TIMEOUT 15)
configure_file(smoke.server.json.in ${CMAKE_CURRENT_BINARY_DIR}/config/server.json @ONLY)
add_test(NAME application_startup COMMAND god2-server --config ${CMAKE_CURRENT_BINARY_DIR}/config/server.json --run-for 1)
set_tests_properties(application_startup PROPERTIES TIMEOUT 10)
add_test(NAME cli_invalid_duration COMMAND god2-server --run-for -1)
set_tests_properties(cli_invalid_duration PROPERTIES TIMEOUT 5 WILL_FAIL TRUE)
find_package(Python3 QUIET COMPONENTS Interpreter)
if(Python3_Interpreter_FOUND)
  add_test(NAME import_native_armor
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_import_native_armor_20261002.py -v)
  set_tests_properties(import_native_armor PROPERTIES TIMEOUT 90 WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
  add_test(NAME native_bank_machine COMMAND ${Python3_EXECUTABLE} -B -m tools.strike_lab.current_bank_20261002)
  add_test(NAME native_bank_items_machine COMMAND ${Python3_EXECUTABLE} -B -m tools.strike_lab.current_bank_items_20261002)
  set_tests_properties(native_bank_items_machine PROPERTIES WORKING_DIRECTORY ${PROJECT_SOURCE_DIR} TIMEOUT 45)
  add_test(NAME native_bank_swap_machine COMMAND ${Python3_EXECUTABLE} -B -m tools.strike_lab.current_bank_swap_20261002)
  set_tests_properties(native_bank_swap_machine PROPERTIES WORKING_DIRECTORY ${PROJECT_SOURCE_DIR} TIMEOUT 45)
  add_test(NAME native_bank_items_tcp COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
    -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_native_bank_items_server.py -v)
  set_tests_properties(native_bank_items_tcp PROPERTIES WORKING_DIRECTORY ${PROJECT_SOURCE_DIR} TIMEOUT 90 RUN_SERIAL TRUE
    ENVIRONMENT "GOD2_ROLE_TEXT_TEST_BINARY=$<TARGET_FILE:god2-server-native-results>")
  add_test(NAME native_login_write_order_tcp COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
    -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_native_login_write_order.py -v)
  set_tests_properties(native_login_write_order_tcp PROPERTIES WORKING_DIRECTORY ${PROJECT_SOURCE_DIR} TIMEOUT 90 RUN_SERIAL TRUE
    ENVIRONMENT "GOD2_ROLE_TEXT_TEST_BINARY=$<TARGET_FILE:god2-server-native-results>")
  set_tests_properties(native_bank_machine PROPERTIES WORKING_DIRECTORY ${PROJECT_SOURCE_DIR} TIMEOUT 45)
  add_test(NAME native_bank_tcp COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
    -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_native_bank_server.py -v)
  set_tests_properties(native_bank_tcp PROPERTIES WORKING_DIRECTORY ${PROJECT_SOURCE_DIR} TIMEOUT 90 RUN_SERIAL TRUE
    ENVIRONMENT "GOD2_ROLE_TEXT_TEST_BINARY=$<TARGET_FILE:god2-server-native-results>")
  add_test(NAME native_party_query_tcp
    COMMAND ${Python3_EXECUTABLE} -X utf8 -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_native_party_query_server_20261003.py -v)
  set_tests_properties(native_party_query_tcp PROPERTIES WORKING_DIRECTORY ${PROJECT_SOURCE_DIR} TIMEOUT 150)
  add_test(NAME native_party_query_machine
    COMMAND ${Python3_EXECUTABLE} -X utf8 -B -m tools.strike_lab.current_party_query_20261003)
  set_tests_properties(native_party_query_machine PROPERTIES WORKING_DIRECTORY ${PROJECT_SOURCE_DIR} TIMEOUT 60)
  add_test(NAME native_party_chat_tcp
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_native_party_chat_server_20261003.py -v)
  set_tests_properties(native_party_chat_tcp PROPERTIES WORKING_DIRECTORY ${PROJECT_SOURCE_DIR} TIMEOUT 150)
  add_test(NAME native_party_chat_machine
    COMMAND ${Python3_EXECUTABLE} -B -m tools.strike_lab.current_party_chat_20261003)
  set_tests_properties(native_party_chat_machine PROPERTIES WORKING_DIRECTORY ${PROJECT_SOURCE_DIR} TIMEOUT 60)
  add_test(NAME native_private_chat_tcp
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_native_private_chat_server_20261003.py -v)
  set_tests_properties(native_private_chat_tcp PROPERTIES WORKING_DIRECTORY ${PROJECT_SOURCE_DIR} TIMEOUT 180)
  add_test(NAME native_private_chat_machine
    COMMAND ${Python3_EXECUTABLE} -B -m tools.strike_lab.current_private_chat_20261003)
  set_tests_properties(native_private_chat_machine PROPERTIES WORKING_DIRECTORY ${PROJECT_SOURCE_DIR} TIMEOUT 60)
  add_test(NAME native_guild_chat_tcp
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_native_guild_chat_server_20261003.py -v)
  set_tests_properties(native_guild_chat_tcp PROPERTIES WORKING_DIRECTORY ${PROJECT_SOURCE_DIR} TIMEOUT 180)
  add_test(NAME native_guild_chat_machine
    COMMAND ${Python3_EXECUTABLE} -B -m tools.strike_lab.current_guild_chat_20261003)
  set_tests_properties(native_guild_chat_machine PROPERTIES WORKING_DIRECTORY ${PROJECT_SOURCE_DIR} TIMEOUT 60)
  add_test(NAME native_party_tcp
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_native_party_server.py -v)
  set_tests_properties(native_party_tcp PROPERTIES WORKING_DIRECTORY ${PROJECT_SOURCE_DIR} TIMEOUT 90)
  add_test(NAME native_party_machine
    COMMAND ${Python3_EXECUTABLE} -B -m tools.strike_lab.current_party_20261002)
  set_tests_properties(native_party_machine PROPERTIES WORKING_DIRECTORY ${PROJECT_SOURCE_DIR} TIMEOUT 45)
  add_test(NAME native_trade_machine
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_native_trade_contract.py -v)
  set_tests_properties(native_trade_machine PROPERTIES WORKING_DIRECTORY ${PROJECT_SOURCE_DIR} TIMEOUT 45
    ENVIRONMENT "GOD2_TRADE_CODEC_BINARY=$<TARGET_FILE:recovered-trade>")
  add_test(NAME native_trade_tcp
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_native_trade_server.py -v)
  set_tests_properties(native_trade_tcp PROPERTIES WORKING_DIRECTORY ${PROJECT_SOURCE_DIR} TIMEOUT 90
    ENVIRONMENT "GOD2_ROLE_TEXT_TEST_BINARY=$<TARGET_FILE:god2-server-native-results>")
  add_test(NAME register_thousand_bulls_candidate
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_register_thousand_bulls_skill.py -v)
  add_test(NAME thousand_bulls_native_command
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_thousand_bulls_command.py -v)
  set_tests_properties(register_thousand_bulls_candidate thousand_bulls_native_command PROPERTIES
    TIMEOUT 60 WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}" LABELS "custom0059;candidate-only;not-live-acceptance")
  foreach(packet_suite IN ITEMS pet_reserve_move_server pet2_revert_server owned_role_text_server owned_teleport_gem_server)
    add_test(NAME ${packet_suite}
      COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
        -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_${packet_suite}.py -v)
    set_tests_properties(${packet_suite} PROPERTIES TIMEOUT 90
      WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}" RUN_SERIAL TRUE
      LABELS "packet;isolated-server;not-live-client-acceptance")
  endforeach()
  add_test(NAME native_pet2_categories COMMAND ${CMAKE_COMMAND} -E env
    "GOD2_NATIVE_PET2_CATEGORY_TEST=$<TARGET_FILE:native-pet2-categories>"
    ${Python3_EXECUTABLE} -X utf8 -B -m unittest tests.research.test_native_pet2_categories)
  set_tests_properties(native_pet2_categories PROPERTIES WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}" TIMEOUT 120)
  add_test(NAME bahamut_growth_reference
    COMMAND ${Python3_EXECUTABLE} -B -m unittest tests.research.test_bahamut_growth_reference)
  set_tests_properties(bahamut_growth_reference PROPERTIES TIMEOUT 30
    WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
  add_test(NAME native_enemy_display_integrity
    COMMAND ${Python3_EXECUTABLE} -B ${CMAKE_CURRENT_SOURCE_DIR}/research/run_native_enemy_display_integrity.py
      --executable $<TARGET_FILE:native-enemy-display-integrity>)
  add_test(NAME native_npc_display
    COMMAND ${Python3_EXECUTABLE} -B ${CMAKE_CURRENT_SOURCE_DIR}/research/run_native_npc_display.py
      --executable $<TARGET_FILE:native-npc-display>)
  add_test(NAME fruit_quest_repository
    COMMAND ${Python3_EXECUTABLE} -B ${CMAKE_CURRENT_SOURCE_DIR}/research/run_fruit_quest_repository.py
      --executable $<TARGET_FILE:fruit-quest-repository>)
  # Real pinned current CSVZ import into a disposable database; no fabricated
  # 418-row catalog, existing save, server process or desktop is used.
  file(GENERATE OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/quest_journal_driver.py" CONTENT [=[
import pathlib, sqlite3, subprocess, sys, tempfile
root, executable = pathlib.Path(sys.argv[1]).resolve(), sys.argv[2]
sys.path.insert(0, str(root))
from tools.strike_lab import import_native_quests, import_native_quest_sources
with tempfile.TemporaryDirectory(prefix='god2-quest-journal-') as temporary:
    path = pathlib.Path(temporary) / 'test.sqlite'
    subprocess.run([executable, '--initialize', str(path)], check=True)
    subprocess.run([executable, '--empty-test', str(path)], check=True)
    connection = sqlite3.connect(path)
    try:
        import_native_quests.import_catalog(connection, root.parent / 'God2')
        import_native_quest_sources.import_catalog(connection, root.parent / 'God2')
    finally:
        connection.close()
    subprocess.run([executable, '--test', str(path)], check=True)
]=])
  add_test(NAME quest_journal COMMAND ${Python3_EXECUTABLE} -B
    "${CMAKE_CURRENT_BINARY_DIR}/quest_journal_driver.py" "${PROJECT_SOURCE_DIR}" $<TARGET_FILE:quest-journal>)
  set_tests_properties(quest_journal PROPERTIES TIMEOUT 60 WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
  add_test(NAME inventory_move_server
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_inventory_move_server.py -v)
  set_tests_properties(inventory_move_server PROPERTIES TIMEOUT 90
    WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}"
    ENVIRONMENT "GOD2_INVENTORY_MOVE_TEST_BINARY=$<TARGET_FILE:god2-server>")
  add_test(NAME current_inventory_projection
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_current_inventory_projection.py -v)
  set_tests_properties(current_inventory_projection PROPERTIES TIMEOUT 90
    WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
  add_test(NAME recovered_chat_server
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_recovered_chat_server.py -v)
  set_tests_properties(recovered_chat_server PROPERTIES TIMEOUT 45
    WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}"
    LABELS "native-protocol;socket;not-live-client-acceptance")
  add_test(NAME current_chat_receive
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_current_chat_receive.py -v)
  set_tests_properties(current_chat_receive PROPERTIES TIMEOUT 30
    WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}"
    LABELS "research;original-client;not-rendered-acceptance")
  add_test(NAME current_scene_transfer
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_current_scene_transfer.py -v)
  set_tests_properties(current_scene_transfer PROPERTIES TIMEOUT 30
    WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}" LABELS "research;world;not-live-acceptance")
  add_test(NAME battle_process_crash
    COMMAND ${Python3_EXECUTABLE} -B ${CMAKE_CURRENT_SOURCE_DIR}/research/test_battle_process_crash.py
      $<TARGET_FILE:battle-process-crash> -v)
  set_tests_properties(battle_process_crash PROPERTIES TIMEOUT 120 LABELS "battle;persistence;fault-injection")
  add_test(NAME current_quest_variable_length
    COMMAND ${Python3_EXECUTABLE} -B ${CMAKE_CURRENT_SOURCE_DIR}/research/test_current_quest_variable_length.py)
  set_tests_properties(current_quest_variable_length PROPERTIES TIMEOUT 30
    LABELS "research;quest;not-live-acceptance")
  add_test(NAME current_item_battle_reach
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_current_item_battle_reach.py -v)
  set_tests_properties(current_item_battle_reach PROPERTIES TIMEOUT 90
    WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
  add_test(NAME current_skill_stat_consumers
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_current_skill_stat_consumers.py -v)
  add_test(NAME current_skill_wide_candidates
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_current_skill_wide_candidates.py -v)
  set_tests_properties(current_skill_wide_candidates PROPERTIES TIMEOUT 30
    WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
  set_tests_properties(current_skill_stat_consumers PROPERTIES TIMEOUT 30
    WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
  add_test(NAME current_projection_sink
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_current_projection_sink.py -v)
  add_test(NAME current_projection_gate
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_current_projection_gate.py -v)
  set_tests_properties(current_projection_gate PROPERTIES TIMEOUT 30
    WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
  set_tests_properties(current_projection_sink PROPERTIES TIMEOUT 30
    WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
  add_test(NAME current_projection_arithmetic
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_current_projection_arithmetic.py -v)
  set_tests_properties(current_projection_arithmetic PROPERTIES TIMEOUT 30
    WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
  add_test(NAME fixture_combat_tcp
    COMMAND ${Python3_EXECUTABLE} -B ${PROJECT_SOURCE_DIR}/tools/fixture_combat_client.py
      --self-test --server $<TARGET_FILE:god2-server> --root ${PROJECT_SOURCE_DIR})
  set_tests_properties(fixture_combat_tcp PROPERTIES TIMEOUT 120
    WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
  foreach(suite native_battle_transport battle_transport_validation current_battle_entry current_battle_initializer current_battle_participant
                quest_blackbox_integrity pet_egg_evidence_boundary skill_formula_evidence_boundary battle_participant_codec_validation
                battle_owner_slot_binding current_item_metadata current_damage_formula current_hit_formula current_critical_formula
                current_combat_effect_values current_item_action_binding current_battle_character_binding current_skill_effect_fields current_skill_effect_amount current_skill_book_fields current_skill_book_availability current_skill_book_owner_chain current_skill_description_rules current_skill_book_binding current_skill_mp_gate current_skill_mp_sync
                current_monster_inventory current_battle_learned_skills
                current_monster_combat_stats current_monster_rewards_capture current_skill_catalog_loader
                current_monster_base_stats current_monster_skill_assignments current_monster_drop_rules
                current_monster_variant_identity current_battle_control_positions
                current_monster_other_identity current_monster_numeric_sources
                current_monster_auxiliary_sources current_monster_map_binary_source
                current_battle_scalar_result current_battle_side1_scalars current_battle_vitals
                recovered_battle_vitals_codec current_monster_side_initialization current_owner_map_metadata
                current_participant_metadata_semantics current_monster_complete_attributes
                current_four_stat_ui_binding current_monster_skill_element_experience
                current_monster_inspect_identity current_monster_binary_producer
                current_monster_identity_backtrace current_battle_speed_backtrace
                current_monster_resource_initialization current_offline_monster_probe
                current_stat_packet_return_path
                current_offline_entry_bridge current_offline_run_review current_offline_monster_live
                current_attack_defense_fulltext
                current_battle_identity_cache
                current_packed_attack_display
                current_pet2_stat_labels
                current_pet2_stats_codec
                current_pet1_stats_codec
                current_deity_portrait
                current_deity_portrait_server
                native_deity_metadata native_deity_templates_server native_deity_skill_capacity_server
                native_pet1_metadata owned_pet1_server
                current_battle_vitals_batch
                current_world_clock world_clock_server_native native_multi_message_reader import_native_multi_messages import_native_map_items owned_map_view_server import_native_weapons owned_role_auxiliary_server current_weapon_fresh_tooltip owned_weapon_transfers_server owned_player_appearance_server player_appearance_update_native current_battle_owner_resources current_battle_map_selector
                current_battle_map_coordinates owned_daily_quest_views_server owned_supply_server)
    add_test(NAME ${suite}
      COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
        -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_${suite}.py -v)
    set_tests_properties(${suite} PROPERTIES TIMEOUT 90 WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
  endforeach()
  set_tests_properties(current_pet1_stats_codec PROPERTIES TIMEOUT 180)
  set_tests_properties(owned_map_view_server PROPERTIES
    ENVIRONMENT "GOD2_MAP_VIEW_BINARY=${PROJECT_SOURCE_DIR}/build-town-visibility/Release/god2-server-owned-map-view.exe")
  set_tests_properties(import_native_weapons PROPERTIES
    ENVIRONMENT "GOD2_NATIVE_WEAPON_TEST_EXE=$<TARGET_FILE:native-weapon-catalog>")
  set_tests_properties(owned_role_auxiliary_server PROPERTIES
    ENVIRONMENT "GOD2_OWNED_SERVER_CANDIDATE=${PROJECT_SOURCE_DIR}/build-town-visibility/Release/god2-server-role-auxiliary.exe")
  set_tests_properties(player_appearance_update_native PROPERTIES
    ENVIRONMENT "GOD2_PLAYER_APPEARANCE_TEST_BINARY=$<TARGET_FILE:player-appearance-update>")
  add_test(NAME current_weapon_selector_authority
    COMMAND ${Python3_EXECUTABLE} -B -m tools.strike_lab.current_weapon_selector_authority_20260926)
  set_tests_properties(current_weapon_selector_authority PROPERTIES
    TIMEOUT 180 WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}"
    LABELS "research;appearance;not-live-acceptance")
  set_tests_properties(world_clock_server_native PROPERTIES
    ENVIRONMENT "GOD2_WORLD_CLOCK_CODEC_BINARY=$<TARGET_FILE:recovered-world-clock>")
  set_tests_properties(native_multi_message_reader PROPERTIES
    ENVIRONMENT "GOD2_MULTI_MESSAGE_READER_BINARY=$<TARGET_FILE:native-multi-message>")
  foreach(suite current_revival_state current_revival_live)
    add_test(NAME ${suite}
      COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
        -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_${suite}.py -v)
    set_tests_properties(${suite} PROPERTIES TIMEOUT 90
      WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}"
      LABELS "research;revival;not-live-acceptance")
  endforeach()
  foreach(suite skill_coverage_matrix quest_coverage_matrix pet_egg_coverage_matrix)
    string(REPLACE "_" "-" report_name ${suite})
    add_test(NAME ${suite}_generate
      COMMAND ${Python3_EXECUTABLE} -B -m tools.strike_lab.${suite}
        --output ${PROJECT_SOURCE_DIR}/artifacts/research/${report_name}-20260920.json)
    set_tests_properties(${suite}_generate PROPERTIES
      TIMEOUT 300 WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}"
      FIXTURES_SETUP ${suite}_artifact RESOURCE_LOCK ${suite}_artifact)
    add_test(NAME ${suite}
      COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
        -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_${suite}.py -v)
    set_tests_properties(${suite} PROPERTIES
      TIMEOUT 360 WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}"
      FIXTURES_REQUIRED ${suite}_artifact RESOURCE_LOCK ${suite}_artifact)
  endforeach()
  add_test(NAME current_battle_resources
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_current_battle_resources.py -v)
  set_tests_properties(current_battle_resources PROPERTIES TIMEOUT 240 WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
  add_test(NAME current_battle_bootstrap
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_current_battle_bootstrap.py -v)
  set_tests_properties(current_battle_bootstrap PROPERTIES TIMEOUT 300 WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
  add_test(NAME current_battle_selector_windows
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_current_battle_selector_windows.py -v)
  set_tests_properties(current_battle_selector_windows PROPERTIES TIMEOUT 300 WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
  add_test(NAME current_battle_selector_population
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_current_battle_selector_population.py -v)
  set_tests_properties(current_battle_selector_population PROPERTIES TIMEOUT 300 WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
  add_test(NAME current_battle_participant_controls
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_current_battle_participant_controls.py -v)
  set_tests_properties(current_battle_participant_controls PROPERTIES TIMEOUT 300 WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
  add_test(NAME current_battle_owner_bridge
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_current_battle_owner_bridge.py -v)
  set_tests_properties(current_battle_owner_bridge PROPERTIES TIMEOUT 300 WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
  add_test(NAME current_battle_owner_map_panel
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_current_battle_owner_map_panel.py -v)
  set_tests_properties(current_battle_owner_map_panel PROPERTIES TIMEOUT 300 WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
  add_test(NAME current_battle_owner_clock
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_current_battle_owner_clock.py -v)
  set_tests_properties(current_battle_owner_clock PROPERTIES TIMEOUT 300 WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
  add_test(NAME current_battle_owner_map_metadata
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_current_battle_owner_map_metadata.py -v)
  set_tests_properties(current_battle_owner_map_metadata PROPERTIES TIMEOUT 300 WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
  add_test(NAME current_battle_owner_map_sprite
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_current_battle_owner_map_sprite.py -v)
  set_tests_properties(current_battle_owner_map_sprite PROPERTIES TIMEOUT 600 WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
  add_test(NAME current_battle_owner_map_label
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_current_battle_owner_map_label.py -v)
  set_tests_properties(current_battle_owner_map_label PROPERTIES TIMEOUT 600 WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
  add_test(NAME current_battle_owner_map_completion
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_current_battle_owner_map_completion.py -v)
  set_tests_properties(current_battle_owner_map_completion PROPERTIES TIMEOUT 600 WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
  add_test(NAME current_battle_owner_toolbar
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_current_battle_owner_toolbar.py -v)
  set_tests_properties(current_battle_owner_toolbar PROPERTIES TIMEOUT 600 WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
  add_test(NAME current_battle_owner_vitals
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_current_battle_owner_vitals.py -v)
  set_tests_properties(current_battle_owner_vitals PROPERTIES TIMEOUT 600 WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
  add_test(NAME native_skill_target_validation
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_native_skill_target_validation.py -v)
  set_tests_properties(native_skill_target_validation PROPERTIES TIMEOUT 90 WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
  add_test(NAME battle_result_flags_validation
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_battle_result_flags_validation.py -v)
  set_tests_properties(battle_result_flags_validation PROPERTIES TIMEOUT 90 WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
  add_test(NAME recovered_battle_result_flags_differential
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_recovered_battle_result_flags.py -v)
  set_tests_properties(recovered_battle_result_flags_differential PROPERTIES TIMEOUT 90 WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
  add_test(NAME native_skill_targeting_differential
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_native_skill_targeting.py -v)
  set_tests_properties(native_skill_targeting_differential PROPERTIES TIMEOUT 120 WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
  add_test(NAME native_skill_application
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_native_skill_application.py -v)
  set_tests_properties(native_skill_application PROPERTIES TIMEOUT 60 WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
  add_test(NAME import_native_skills
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_import_native_skills.py -v)
  set_tests_properties(import_native_skills PROPERTIES TIMEOUT 90
    WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}"
    ENVIRONMENT "GOD2_NATIVE_SKILL_READER_TEST=$<TARGET_FILE:native-skill-catalog>")
  add_test(NAME import_native_skill_books
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_import_native_skill_books.py -v)
  set_tests_properties(import_native_skill_books PROPERTIES TIMEOUT 180
    WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
  add_test(NAME import_native_quests
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_import_native_quests.py -v)
  set_tests_properties(import_native_quests PROPERTIES TIMEOUT 60
    WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}" LABELS "quest;not-live-acceptance"
    ENVIRONMENT "GOD2_NATIVE_QUEST_READER=$<TARGET_FILE:native-quest-catalog-reader>")
  add_test(NAME import_native_quest_sources
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_import_native_quest_sources.py -v)
  set_tests_properties(import_native_quest_sources PROPERTIES TIMEOUT 60
    WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}" LABELS "quest;not-live-acceptance"
    ENVIRONMENT "GOD2_NATIVE_QUEST_READER=$<TARGET_FILE:native-quest-catalog-reader>")
  add_test(NAME current_world_records
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_current_world_records.py -v)
  set_tests_properties(current_world_records PROPERTIES TIMEOUT 90 WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
  add_test(NAME current_selection_pending
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_current_selection_pending.py -v)
  set_tests_properties(current_selection_pending PROPERTIES TIMEOUT 45
    WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}" LABELS "item;not-live-acceptance")
  add_test(NAME import_native_catalog
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_import_native_catalog.py -v)
  set_tests_properties(import_native_catalog PROPERTIES TIMEOUT 60 WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
  add_test(NAME import_native_enemy_display
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_import_native_enemy_display.py -v)
  set_tests_properties(import_native_enemy_display PROPERTIES TIMEOUT 90 WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
  add_test(NAME import_native_med02_recovery
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_import_native_med02_recovery.py -v)
  set_tests_properties(import_native_med02_recovery PROPERTIES TIMEOUT 90 WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
  add_test(NAME same_session_battle_supply_server
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_same_session_battle_supply_server.py -v)
  set_tests_properties(same_session_battle_supply_server PROPERTIES TIMEOUT 90
    WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}" LABELS "packet;socket;not-live-acceptance")
  add_test(NAME current_instance_update
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_current_instance_update.py -v)
  set_tests_properties(current_instance_update PROPERTIES TIMEOUT 300)
  add_test(NAME current_battle_experience
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_current_battle_experience.py -v)
  set_tests_properties(current_battle_experience PROPERTIES TIMEOUT 120)
  add_test(NAME current_role_progress_codec
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_current_role_progress_codec.py -v)
  set_tests_properties(current_role_progress_codec PROPERTIES TIMEOUT 120 WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
  add_test(NAME current_role_level_codec
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_current_role_level_codec.py -v)
  set_tests_properties(current_role_level_codec PROPERTIES TIMEOUT 120 WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
  add_test(NAME current_role_auxiliary_projection
    COMMAND ${Python3_EXECUTABLE} -X utf8 -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_current_role_auxiliary_projection_20261002.py -v)
  set_tests_properties(current_role_auxiliary_projection PROPERTIES TIMEOUT 120
    WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}" LABELS "packet;native-consumer;not-live-acceptance")
  # Beta evidence is build-specific and does not qualify current-client gameplay.
  add_test(NAME current_unpacked_protocol_match
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_current_unpacked_protocol_match.py -v)
  set_tests_properties(current_unpacked_protocol_match PROPERTIES
    TIMEOUT 60 WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}" LABELS "research;current-client;not-live-acceptance")
  add_test(NAME beta_client_compare
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_beta_client_compare.py -v)
  add_test(NAME beta_packet_probe
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_beta_packet_probe.py -v)
  add_test(NAME beta_resource_writers
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_beta_resource_writers.py -v)
  # These two tools read raw Desktop/god2-test assets from a retired build.
  # They are historical research, not dependencies of current Taiwan runtime.
  # Opt-in keeps their pin/missing-input checks strict; never skip failures there.
  option(GOD2_ENABLE_RETIRED_BETA_ASSET_RESEARCH "Run historical research requiring retired beta client assets" OFF)
  if(GOD2_ENABLE_RETIRED_BETA_ASSET_RESEARCH)
  add_test(NAME beta_role_stat_labels
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_beta_role_stat_labels.py -v)
  add_test(NAME beta_skill_amount_probe
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_beta_skill_amount_probe.py -v)
  set_tests_properties(beta_role_stat_labels beta_skill_amount_probe PROPERTIES
    TIMEOUT 300 WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}"
    LABELS "research;retired-beta-assets;not-live-acceptance")
  endif()
  set_tests_properties(beta_client_compare beta_packet_probe beta_resource_writers PROPERTIES
    TIMEOUT 300 WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}"
    LABELS "research;beta;not-live-acceptance")
  execute_process(COMMAND ${Python3_EXECUTABLE} -c "import pefile; assert pefile.__version__ == '2024.8.26'"
    RESULT_VARIABLE GOD2_PEFILE_STATUS OUTPUT_QUIET ERROR_QUIET)
  if(GOD2_PEFILE_STATUS EQUAL 0)
    add_test(NAME artifact_vault COMMAND ${Python3_EXECUTABLE} -m unittest discover -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p "test_artifact_vault.py")
    add_test(NAME runtime_evidence COMMAND ${Python3_EXECUTABLE} -m unittest discover -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p "test_runtime_evidence.py")
    set_tests_properties(artifact_vault PROPERTIES TIMEOUT 30)
    set_tests_properties(runtime_evidence PROPERTIES TIMEOUT 60)
    add_test(NAME gate_review COMMAND ${Python3_EXECUTABLE} -m unittest discover -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p "test_gate_review.py")
    set_tests_properties(gate_review PROPERTIES TIMEOUT 120)
    add_test(NAME counter_resolution COMMAND ${Python3_EXECUTABLE} -m unittest discover -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p "test_counter_resolution.py")
    set_tests_properties(counter_resolution PROPERTIES TIMEOUT 180)
    add_test(NAME runtime_environment COMMAND ${Python3_EXECUTABLE} -m unittest discover -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p "test_runtime_environment.py")
    set_tests_properties(runtime_environment PROPERTIES TIMEOUT 30)
  else()
    message(STATUS "Research tests disabled: install tools/research/requirements.txt")
  endif()
endif()
