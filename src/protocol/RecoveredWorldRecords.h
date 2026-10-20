#pragma once
#include "protocol/TaiwanNativeBlacklist.h"
#include "protocol/TaiwanNativePartyMenu.h"
#include "protocol/TaiwanNativeClientOptions.h"
#include "protocol/RecoveredBattleRowPreference.h"
#include "protocol/RecoveredSosSupportRequest.h"
#include "protocol/RecoveredSosBattleCommand.h"
#include "protocol/RecoveredBattleFleeCommand.h"
#include "protocol/RecoveredTeamRequest57.h"
#include "protocol/RecoveredPartyExitRequest5A.h"
#include "protocol/TaiwanNativeSkillCommand.h"
#include "protocol/RecoveredWorldSkillRequest.h"
#include "protocol/RecoveredSkillSelectionRequest.h"
#include "protocol/RecoveredPrebornChoiceRequest.h"
#include "protocol/RecoveredPk69.h"
#include "relations53/RelationsRawCodec.h"
#include "protocol/RecoveredBattleCommand.h"
#include "protocol/RecoveredSkillCommand.h"
#include "protocol/RecoveredInventoryItemRequest.h"
#include "protocol/RecoveredBeastPanel.h"
#include "protocol/RecoveredCompanionControl6B.h"
#include "protocol/RecoveredE4Control.h"
#include "protocol/RecoveredBFRequest.h"
#include "protocol/RecoveredC2Control.h"
#include "protocol/RecoveredSpectator6E.h"
#include "protocol/RecoveredSpectatorClose.h"
#include "protocol/RecoveredMapPanelControl68.h"
#include "protocol/RecoveredBeastExploration.h"
#include "protocol/RecoveredTargetItemRequest.h"
#include "protocol/RecoveredSelectionItemRequest.h"
#include "protocol/RecoveredMovement.h"
#include "protocol/RecoveredQuestAction.h"
#include "protocol/RecoveredQuestClose.h"
#include "protocol/RecoveredNpcInteraction.h"
#include "protocol/RecoveredWorldFrame.h"
#include "protocol/RecoveredChat.h"
#include "protocol/RecoveredPartyChat.h"
#include "protocol/RecoveredPrivateChat.h"
#include "protocol/RecoveredGuildChat.h"
#include "protocol/RecoveredGuildRoster.h"
#include "protocol/RecoveredGuildLeave.h"
#include "protocol/RecoveredGuildMembership.h"
#include "protocol/RecoveredGuildLeadership.h"
#include "protocol/RecoveredGuildDisband75.h"
#include "protocol/RecoveredGuildAnnouncement.h"
#include "protocol/RecoveredTeleport.h"
#include "protocol/RecoveredInventoryMoveRequest.h"
#include "protocol/RecoveredDeitySelection.h"
#include "protocol/RecoveredDailyQuestRequest.h"
#include "protocol/RecoveredAttributeAllocation.h"
#include "protocol/RecoveredPet2Revert.h"
#include "protocol/RecoveredRoleText.h"
#include "protocol/RecoveredInventoryDiscard.h"
#include "protocol/RecoveredParty.h"
#include "protocol/RecoveredPartyPositionQuery.h"
#include "protocol/RecoveredTrade.h"
#include "protocol/RecoveredBank.h"
#include "protocol/RecoveredBankItems.h"
#include <cstddef>
#include <array>
#include <algorithm>
#include <cstdint>
#include <optional>
#include <span>
#include <variant>
#include <vector>

namespace god2 {
// C2S grammar from current producers only, independent of S2C length tables.
// Structural acceptance does not authorize any operation or imply a response.
struct RecoveredWorldRecords {
    struct UnsupportedRecord { std::size_t offset; std::uint8_t opcode; };
    struct Tick {};
    // Native 961A0(1F,1) -> 157D0 emits exactly 1F 00. A later live
    // world-session capture contains the same standalone record. Its effect
    // outside the initializer is not established, so keep it opaque.
    struct ClientControl1F {};
    // Current-image 961A0(6D,1) -> 157D0 -> 132E0 queues exactly 6D 00.
    // The distinct S2C 6D record is 29 bytes; its data authority is open.
    struct ClientControl6D {};
    // Native 473E00 -> 132E0 queues 74 and one unwritten stack byte during
    // a local UI mode transition. Preserve the byte; no gameplay effect or
    // server response has been qualified for this producer.
    struct ClientOpaque74 { std::uint8_t payload; };
    // Native 472BD0 -> 132E0 queues 88 and the two raw bytes read through
    // UI+8688C. Its server-side panel/context effect is not qualified.
    struct ClientPanelOpen88 { std::array<std::uint8_t,2> payload; };
    // Native497D80 ->4132E0 queues1D plus the two bytes at client+449C.
    // UI4F4B50/4C7520 changes these local options before sending. Preserve
    // all bits; this C2S3-byte record is not the unrelated S2C1D173-byte record.
    struct ClientOptionsNotification { std::array<std::uint8_t,2> payload; };
    // Native RVA97E00/97E70 ->132E0 queues66 plus exactly3 bytes.
    // Producer packs direction into low3 bits of payload1 and local pose into
    // its high bits; payload2 can contain unwritten stack data. Preserve all
    // bytes. Parsing establishes framing only, not pose replication authority.
    struct ClientPoseNotification { std::array<std::uint8_t,3> payload; };
    // Current4A6760(0,12) ->4132E0. Open daily panel, exact D7 00.
    struct DailyPanelOpen {};
    // RVA 117B0 queues opcode 36 with eight bytes from timer object+84.
    // Preserve opaque fields; parsing grants no gameplay authority.
    struct TimerNotification { std::array<std::uint8_t,8> payload; };
    // RVA 157F0: caller low WORD plus the 131C10 configuration flag WORD.
    // Also used during initialization; not inherently a battle-exit ACK.
    struct ContextNotification { std::array<std::uint8_t,4> payload; };
    // Native RVA 2B10 -> 132E0 emits 9A, a WORD equal to the logical
    // record size, severity 0/1, a terminated diagnostic string and one
    // trailing byte copied by the original producer. It carries no action.
    struct ClientDiagnostic { std::vector<std::uint8_t> bytes; };
    using Record = std::variant<RecoveredMovement::Request, Tick,
                                RecoveredInventoryItemRequest::Request,
                                RecoveredTargetItemRequest::Request,
                                RecoveredSelectionItemRequest::Request,
                                RecoveredQuestAction::Request,
                                RecoveredQuestClose::Request,
                                RecoveredBattleCommand::BasicAttackRequest,
                                RecoveredBattleCommand::ControlRequest,
                                RecoveredSkillCommand::Record, TimerNotification, ContextNotification,
                                RecoveredBattleCommand::Action2Request, RecoveredNpcInteraction::Request,
                                RecoveredChat::Request, ClientDiagnostic, ClientControl1F,
                                ClientControl6D, RecoveredTeleport::Selection,
                                RecoveredInventoryMoveRequest::Request, RecoveredDeitySelection::Request,
                                RecoveredDailyQuestRequest::Request, DailyPanelOpen,
                                RecoveredAttributeAllocation::Request,ClientPoseNotification,
                                RecoveredPet2Revert::Request,RecoveredRoleText::Request,
                                ClientOpaque74,ClientPanelOpen88,ClientOptionsNotification,
                                RecoveredInventoryDiscard::Request,RecoveredParty::Request,RecoveredTrade::Request,RecoveredBank::Request,RecoveredBankItems::Request,
                                RecoveredPartyPositionQuery::Request,RecoveredPartyChat::Request,RecoveredPrivateChat::Request,RecoveredGuildChat::Request,
                                RecoveredGuildRoster::PanelReady,RecoveredGuildLeave::Request,
                                RecoveredGuildDisband75::Request,RecoveredGuildMembership::Request,RecoveredGuildLeadership::Request,RecoveredGuildAnnouncement::Request,native_relation_private::Action,
                                RecoveredBeastPanel::Request,RecoveredBeastExploration::Close,RecoveredPk69::Request,
                                RecoveredCompanionControl6B::Request,RecoveredBeastExploration::Action,
                                RecoveredE4Control::Request,RecoveredBFRequest::Request,
                                RecoveredC2Control::Request,
                                RecoveredSpectator6E::Request,RecoveredMapPanelControl68::Request,
                                RecoveredSpectatorClose::Request,TaiwanNativeSkillCommand::WireRecord,TaiwanNativeBlacklist::Request,TaiwanNativePartyMenu::Request,TaiwanNativeClientOptions::Control,RecoveredWorldSkillRequest::Request,RecoveredPrebornChoiceRequest::Mask,RecoveredPrebornChoiceRequest::Words,
                                RecoveredSkillSelectionRequest::Request,RecoveredBattleRowPreference::Request,
                                RecoveredSosSupportRequest::Request,RecoveredSosBattleCommand::Request,RecoveredBattleFleeCommand::Request,
                                RecoveredTeamRequest57::Request,RecoveredPartyExitRequest5A::Request>;
    static constexpr std::size_t max_logical_size = RecoveredWorldFrame::max_logical_size;

    // C2S 9A is a client diagnostic/log record, not a gameplay action. Keep
    // parsing and validation in decode(), then let the application remove it
    // before routing the other records in the same logical batch.
    static std::vector<Record> without_client_diagnostics(std::span<const Record> records) {
        std::vector<Record> result;
        result.reserve(records.size());
        for (const auto& record : records)
            if (!std::holds_alternative<ClientDiagnostic>(record)) result.push_back(record);
        return result;
    }

    // The caller validates the envelope first (or uses parse_frame). No record
    // escapes until the entire bounded batch has passed structural validation.
    static std::optional<std::vector<Record>> decode(
        std::span<const std::uint8_t> logical,
        std::optional<UnsupportedRecord>* unsupported=nullptr,bool guild_relations53=false,bool beast_views=false,
        bool pk_invitations=false,bool companion_controls6b=false,bool beast_activity9e=false,
        bool e4_controls=false,bool bf_requests=false,bool spectator6e=false,bool map_panel68=false,
        bool c2_controls=false,bool spectator_close=false,bool native_skill_commands=false,bool owned_blacklist=false,bool owned_party_directory=false,
        bool owned_client_options=false,bool native_world_skill_requests=false,bool native_preborn_requests=false,
        bool native_skill_selection_requests=false,bool owned_battle_row_preference=false) {
        if(unsupported) unsupported->reset();
        if (logical.empty() || logical.size() > max_logical_size)
            return std::nullopt;
        std::vector<Record> records;
        for (std::size_t offset = 0; offset < logical.size();) {
            const auto remaining = logical.subspan(offset);
            switch (remaining[0]) {
            case RecoveredBattleRowPreference::opcode: {
                if(!owned_battle_row_preference){if(unsupported)*unsupported=UnsupportedRecord{offset,remaining[0]};return {};}
                constexpr auto size=RecoveredBattleRowPreference::logical_size;
                if(remaining.size()<size)return {};
                const auto request=RecoveredBattleRowPreference::decode(remaining.first(size));
                if(!request)return {};
                records.emplace_back(*request);offset+=size;break;
            }
            case TaiwanNativeClientOptions::control_opcode: {
                if(!owned_client_options){if(unsupported)*unsupported=UnsupportedRecord{offset,remaining[0]};return {};}
                constexpr auto size=TaiwanNativeClientOptions::control_size;
                if(remaining.size()<size)return {};
                const auto request=TaiwanNativeClientOptions::decode(remaining.first(size));if(!request)return {};
                records.emplace_back(*request);offset+=size;break;
            }
            case 0x8e:case 0x8f:case 0x8d:case 0x92:case 0x90:case 0x91: {
                if(!owned_party_directory){if(unsupported)*unsupported=UnsupportedRecord{offset,remaining[0]};return {};}
                const std::size_t size=(remaining[0]==0x8e || remaining[0]==0x8f)?25:((remaining[0]==0x90 || remaining[0]==0x91)?5:2);
                if(remaining.size()<size)return {};
                const auto request=TaiwanNativePartyMenu::decode(remaining.first(size));if(!request)return {};
                records.emplace_back(*request);offset+=size;break;
            }
            case 0x89:case 0x8a: {
                if(!owned_blacklist){if(unsupported)*unsupported=UnsupportedRecord{offset,remaining[0]};return {};}
                const auto size=remaining[0]==0x89?TaiwanNativeBlacklist::add_size:TaiwanNativeBlacklist::remove_size;
                if(remaining.size()<size)return {};
                const auto request=TaiwanNativeBlacklist::decode(remaining.first(size));
                if(!request)return {};
                records.emplace_back(*request);offset+=size;break;
            }
            case 0xa3:case 0xcb: {
                if(!spectator_close){if(unsupported)*unsupported=UnsupportedRecord{offset,remaining[0]};return {};}
                constexpr auto size=RecoveredSpectatorClose::logical_size;
                if(remaining.size()<size)return {};
                const auto request=RecoveredSpectatorClose::decode(remaining.first(size));
                if(!request)return {};
                records.emplace_back(*request);offset+=size;break;
            }
            case RecoveredMapPanelControl68::opcode: {
                if(!map_panel68){if(unsupported)*unsupported=UnsupportedRecord{offset,remaining[0]};return {};}
                constexpr auto size=RecoveredMapPanelControl68::logical_size;
                if(remaining.size()<size)return {};
                const auto request=RecoveredMapPanelControl68::decode(remaining.first(size));
                if(!request)return {};
                records.emplace_back(*request);offset+=size;break;
            }
            case RecoveredSpectator6E::opcode: {
                if(!spectator6e){if(unsupported)*unsupported=UnsupportedRecord{offset,remaining[0]};return {};}
                constexpr auto size=RecoveredSpectator6E::logical_size;
                if(remaining.size()<size)return {};
                const auto request=RecoveredSpectator6E::decode(remaining.first(size));
                if(!request)return {};
                records.emplace_back(*request);offset+=size;break;
            }
            case RecoveredBFRequest::opcode: {
                if(!bf_requests){if(unsupported)*unsupported=UnsupportedRecord{offset,remaining[0]};return {};}
                constexpr auto size=RecoveredBFRequest::request_size;
                if(remaining.size()<size)return {};
                const auto request=RecoveredBFRequest::decode_request(remaining.first(size));
                if(!request)return {};
                records.emplace_back(*request);offset+=size;break;
            }
            case RecoveredC2Control::opcode: {
                if(!c2_controls){if(unsupported)*unsupported=UnsupportedRecord{offset,remaining[0]};return {};}
                constexpr auto size=RecoveredC2Control::logical_size;
                if(remaining.size()<size)return {};
                const auto request=RecoveredC2Control::decode(remaining.first(size));
                if(!request)return {};
                records.emplace_back(*request);offset+=size;break;
            }
            case RecoveredE4Control::opcode: {
                if(!e4_controls){if(unsupported)*unsupported=UnsupportedRecord{offset,remaining[0]};return {};}
                constexpr auto size=RecoveredE4Control::request_size;
                if(remaining.size()<size)return {};
                const auto request=RecoveredE4Control::decode_request(remaining.first(size));
                if(!request)return {};
                records.emplace_back(*request);offset+=size;break;
            }
            case RecoveredBeastExploration::action_opcode: {
                if(!beast_activity9e){if(unsupported)*unsupported=UnsupportedRecord{offset,remaining[0]};return {};}
                constexpr auto size=RecoveredBeastExploration::action_size;
                if(remaining.size()<size)return {};
                const auto action=RecoveredBeastExploration::decode_action(remaining.first(size));
                if(!action)return {};
                records.emplace_back(*action);offset+=size;break;
            }
            case RecoveredCompanionControl6B::opcode: {
                if(!companion_controls6b){if(unsupported)*unsupported=UnsupportedRecord{offset,remaining[0]};return {};}
                constexpr auto size=RecoveredCompanionControl6B::logical_size;
                if(remaining.size()<size)return {};
                const auto request=RecoveredCompanionControl6B::decode(remaining.first(size));
                if(!request)return {};
                records.emplace_back(*request);offset+=size;break;
            }
            case RecoveredPk69::opcode: {
                if(!pk_invitations){if(unsupported)*unsupported=UnsupportedRecord{offset,remaining[0]};return {};}
                constexpr auto size=RecoveredPk69::logical_size;if(remaining.size()<size)return {};
                const auto request=RecoveredPk69::decode(remaining.first(size));if(!request)return {};
                records.emplace_back(*request);offset+=size;break;
            }
            case RecoveredBeastPanel::control8_opcode: {
                if(!beast_views){if(unsupported)*unsupported=UnsupportedRecord{offset,remaining[0]};return {};}
                constexpr auto size=RecoveredBeastPanel::request_size;if(remaining.size()<size)return {};
                const auto request=RecoveredBeastPanel::decode_request(remaining.first(size));if(!request)return {};
                records.emplace_back(*request);offset+=size;break;
            }
            case RecoveredBeastExploration::close_opcode: {
                if(!beast_views){if(unsupported)*unsupported=UnsupportedRecord{offset,remaining[0]};return {};}
                constexpr auto size=RecoveredBeastExploration::close_size;if(remaining.size()<size)return {};
                const auto request=RecoveredBeastExploration::decode_close(remaining.first(size));if(!request)return {};
                records.emplace_back(*request);offset+=size;break;
            }
            case RecoveredGuildAnnouncement::request_opcode: {
                if(remaining.size()<3)return std::nullopt;
                const auto size=std::size_t{remaining[1]}+(std::size_t{remaining[2]}<<8);
                if(size<RecoveredGuildAnnouncement::minimum_logical_size ||
                   size>RecoveredGuildAnnouncement::maximum_logical_size || size>remaining.size())return std::nullopt;
                const auto request=RecoveredGuildAnnouncement::decode(remaining.first(size));
                if(!request)return std::nullopt;
                records.emplace_back(*request);offset+=size;break;
            }
            case RecoveredGuildDisband75::opcode: {
                constexpr auto size=RecoveredGuildDisband75::request_size;
                if(remaining.size()<size)return std::nullopt;
                const auto request=RecoveredGuildDisband75::decode(remaining.first(size));
                if(!request)return std::nullopt;
                records.emplace_back(*request);offset+=size;break;
            }
            case 0x71:
            case 0x72: {
                constexpr auto size=RecoveredGuildLeadership::request_size;
                if(remaining.size()<size)return std::nullopt;
                const auto request=RecoveredGuildLeadership::decode(remaining.first(size));
                if(!request)return std::nullopt;
                records.emplace_back(*request);offset+=size;break;
            }
            case RecoveredGuildMembership::request_opcode: {
                constexpr auto size=RecoveredGuildMembership::request_size;
                if(remaining.size()<size)return std::nullopt;
                const auto request=RecoveredGuildMembership::decode(remaining.first(size));
                if(!request)return std::nullopt;
                records.emplace_back(*request);offset+=size;break;
            }
            case RecoveredGuildLeave::opcode: {
                constexpr auto size=RecoveredGuildLeave::logical_size;
                if(remaining.size()<size)return std::nullopt;
                const auto request=RecoveredGuildLeave::decode(remaining.first(size));
                if(!request)return std::nullopt;
                records.emplace_back(*request);offset+=size;break;
            }
            case 0xb8: {
                if(remaining.size()<2)return std::nullopt;
                const auto ready=RecoveredGuildRoster::panel_ready(remaining.first(2));
                if(!ready)return std::nullopt;
                records.emplace_back(*ready);offset+=2;break;
            }
            case RecoveredPartyPositionQuery::opcode: {
                constexpr auto size=RecoveredPartyPositionQuery::logical_size;
                if(remaining.size()<size)return std::nullopt;
                const auto request=RecoveredPartyPositionQuery::decode(remaining.first(size));
                if(!request)return std::nullopt;
                records.emplace_back(*request);offset+=size;break;
            }
            case 0x39:
            case 0x61:
            case 0x62: {
                const auto size=RecoveredBank::size(remaining[0]);
                if(remaining.size()<size)return std::nullopt;
                const auto request=RecoveredBank::decode(remaining.first(size));
                if(!request)return std::nullopt;
                records.emplace_back(*request);offset+=size;break;
            }
            case 0x29:case 0x2a:case 0x2b:case 0x2c:case 0x2d: {
                const auto size=RecoveredTrade::size(remaining[0]);
                if(remaining.size()<size)return std::nullopt;
                const auto request=RecoveredTrade::decode(remaining.first(size));
                if(!request)return std::nullopt;
                records.emplace_back(*request);offset+=size;break;
            }
            case RecoveredSosSupportRequest::opcode: {
                constexpr auto size=RecoveredSosSupportRequest::logical_size;
                if(remaining.size()<size)return {};
                const auto request=RecoveredSosSupportRequest::decode(remaining.first(size));if(!request)return {};
                records.emplace_back(*request);offset+=size;break;
            }
            case RecoveredTeamRequest57::opcode: {
                constexpr auto size=RecoveredTeamRequest57::logical_size;
                if(remaining.size()<size)return {};
                const auto request=RecoveredTeamRequest57::decode(remaining.first(size));if(!request)return {};
                records.emplace_back(*request);offset+=size;break;
            }
            case RecoveredPartyExitRequest5A::opcode: {
                constexpr auto size=RecoveredPartyExitRequest5A::logical_size;
                if(remaining.size()<size)return {};
                const auto request=RecoveredPartyExitRequest5A::decode(remaining.first(size));if(!request)return {};
                records.emplace_back(*request);offset+=size;break;
            }
            case 0x58: {
                const auto size=RecoveredParty::size(remaining[0]);
                if(remaining.size()<size)return std::nullopt;
                const auto request=RecoveredParty::decode(remaining.first(size));
                if(!request)return std::nullopt;
                records.emplace_back(*request);offset+=size;break;
            }
            case RecoveredInventoryDiscard::opcode: {
                constexpr auto size=RecoveredInventoryDiscard::logical_size;
                if(remaining.size()<size)return std::nullopt;
                const auto request=RecoveredInventoryDiscard::decode(remaining.first(size));
                if(!request)return std::nullopt;
                records.emplace_back(*request);offset+=size;break;
            }
            case 0x1d: {
                if(remaining.size()<3)return std::nullopt;
                records.emplace_back(ClientOptionsNotification{{remaining[1],remaining[2]}});
                offset+=3;break;
            }
            case RecoveredRoleText::c2s_opcode: {
                constexpr auto size=RecoveredRoleText::logical_size;
                if(remaining.size()<size)return std::nullopt;
                const auto request=RecoveredRoleText::decode(remaining.first(size));
                if(!request)return std::nullopt;
                records.emplace_back(*request);offset+=size;break;
            }
            case RecoveredPet2Revert::opcode: {
                constexpr auto size=RecoveredPet2Revert::logical_size;
                if(remaining.size()<size)return std::nullopt;
                const auto request=RecoveredPet2Revert::decode(remaining.first(size));
                if(!request)return std::nullopt;
                records.emplace_back(*request);offset+=size;break;
            }
            case 0x63: case 0x64: case 0x65: {
                if(remaining.size()<7)return std::nullopt;
                const auto request=RecoveredBankItems::decode(remaining.first(7));
                if(!request)return std::nullopt;
                records.emplace_back(*request);offset+=7;break;
            }
            case 0x66: {
                if(remaining.size()<4)return std::nullopt;
                ClientPoseNotification notification{};
                std::copy_n(remaining.begin()+1,3,notification.payload.begin());
                records.emplace_back(notification);offset+=4;break;
            }
            case RecoveredAttributeAllocation::opcode: {
                constexpr auto size=RecoveredAttributeAllocation::logical_size;
                if(remaining.size()<size)return std::nullopt;
                const auto request=RecoveredAttributeAllocation::decode(remaining.first(size));
                if(!request)return std::nullopt;
                records.emplace_back(*request);offset+=size;break;
            }
            case 0xd7:
                if(remaining.size()<2 || remaining[1]!=0)return std::nullopt;
                records.emplace_back(DailyPanelOpen{});offset+=2;break;
            case RecoveredDailyQuestRequest::opcode: {
                constexpr auto size=RecoveredDailyQuestRequest::logical_size;
                if(remaining.size()<size)return std::nullopt;
                const auto request=RecoveredDailyQuestRequest::decode(remaining.first(size));
                if(!request)return std::nullopt;
                records.emplace_back(*request);offset+=size;break;
            }
            case RecoveredDeitySelection::opcode: {
                constexpr auto size=RecoveredDeitySelection::logical_size;
                if(remaining.size()<size) return std::nullopt;
                const auto request=RecoveredDeitySelection::decode(remaining.first(size));
                if(!request) return std::nullopt;
                records.emplace_back(*request);offset+=size;break;
            }
            case 0x9a: {
                if(remaining.size()<6) return std::nullopt;
                const auto size=static_cast<std::size_t>(remaining[1])+256u*remaining[2];
                if(size<6 || size>519 || size>remaining.size() ||
                   remaining[3]>1 || remaining[size-2]!=0 ||
                   std::find(remaining.begin()+4,remaining.begin()+static_cast<std::ptrdiff_t>(size-2),0)
                       !=remaining.begin()+static_cast<std::ptrdiff_t>(size-2)) return std::nullopt;
                records.emplace_back(ClientDiagnostic{std::vector<std::uint8_t>(remaining.begin(),
                    remaining.begin()+static_cast<std::ptrdiff_t>(size))});
                offset+=size;
                break;
            }
            case RecoveredChat::c2s_opcode: {
                if(remaining.size()<3) return std::nullopt;
                const auto size=static_cast<std::size_t>(remaining[1])+256u*remaining[2];
                if(size>remaining.size()) return std::nullopt;
                const auto request=RecoveredChat::parse_common(remaining.first(size));
                if(!request) return std::nullopt;
                if(RecoveredPartyChat::selected(*request))
                    records.emplace_back(RecoveredPartyChat::Request{request->client_header,request->legacy_text});
                else if(RecoveredPrivateChat::selected(*request))
                    records.emplace_back(RecoveredPrivateChat::Request{request->client_header,request->legacy_text});
                else if(RecoveredGuildChat::selected(*request))
                    records.emplace_back(RecoveredGuildChat::Request{request->client_header,request->legacy_text});
                else records.emplace_back(*request);
                offset+=size;
                break;
            }
            case RecoveredNpcInteraction::opcode: {
                constexpr auto size=RecoveredNpcInteraction::logical_size;
                if(remaining.size()<size) return std::nullopt;
                const auto request=RecoveredNpcInteraction::decode(remaining.first(size));
                if(!request) return std::nullopt;
                records.emplace_back(*request);
                offset+=size;
                break;
            }
            case RecoveredInventoryMoveRequest::opcode: {
                constexpr auto size=RecoveredInventoryMoveRequest::logical_size;
                if(remaining.size()<size) return std::nullopt;
                const auto request=RecoveredInventoryMoveRequest::decode(remaining.first(size));
                if(!request) return std::nullopt;
                records.emplace_back(*request);
                offset+=size;
                break;
            }
            case 0x26: {
                constexpr std::size_t size = 7;
                if (remaining.size() < size) return std::nullopt;
                const auto request = RecoveredTargetItemRequest::decode(remaining.first(size));
                if (!request) return std::nullopt;
                records.emplace_back(*request);
                offset += size;
                break;
            }
            case RecoveredSelectionItemRequest::opcode: {
                constexpr auto size = RecoveredSelectionItemRequest::logical_size;
                if (remaining.size() < size) return std::nullopt;
                const auto request = RecoveredSelectionItemRequest::decode(remaining.first(size));
                if (!request) return std::nullopt;
                records.emplace_back(*request);
                offset += size;
                break;
            }
            case 0x1c: {
                if(remaining.size()<5) return std::nullopt;
                ContextNotification notification{};
                std::copy_n(remaining.begin()+1,4,notification.payload.begin());
                records.emplace_back(notification);
                offset+=5;
                break;
            }
            case 0x1f: {
                if(remaining.size()<2 || remaining[1]!=0) return std::nullopt;
                records.emplace_back(ClientControl1F{});
                offset+=2;
                break;
            }
            case 0x6d: {
                if(remaining.size()<2 || remaining[1]!=0) return std::nullopt;
                records.emplace_back(ClientControl6D{});
                offset+=2;
                break;
            }
            case 0x74: {
                if(remaining.size()<2)return std::nullopt;
                records.emplace_back(ClientOpaque74{remaining[1]});
                offset+=2;
                break;
            }
            case 0x88: {
                if(remaining.size()<3)return std::nullopt;
                records.emplace_back(ClientPanelOpen88{{remaining[1],remaining[2]}});
                offset+=3;
                break;
            }
            case 0x99:
            case 0xa9: {
                // Current F72B0 -> 132E0: context WORD, selected label byte,
                // opaque stack tail. Opcode branch is qualified by F6DA0.
                constexpr std::size_t size=5;
                if(remaining.size()<size) return std::nullopt;
                const auto request=RecoveredTeleport::decode_selection(remaining.first(size));
                if(!request) return std::nullopt;
                records.emplace_back(*request);
                offset+=size;
                break;
            }
            case 0x81:
            case 0x83: {
                // Actual staged UI mask/list grammar only. Complete batch is
                // parsed before any owner runs; do not infer learning or a reply.
                if(!native_preborn_requests){if(unsupported)*unsupported=UnsupportedRecord{offset,remaining[0]};return {};}
                const auto size=RecoveredPrebornChoiceRequest::request_size(remaining);
                if(!size)return {};
                if(remaining[0]==RecoveredPrebornChoiceRequest::mask_opcode) {
                    const auto request=RecoveredPrebornChoiceRequest::decode_mask(remaining.first(*size));
                    if(!request)return {};
                    records.emplace_back(*request);
                }else {
                    auto request=RecoveredPrebornChoiceRequest::decode_words(remaining.first(*size));
                    if(!request)return {};
                    records.emplace_back(std::move(*request));
                }
                offset+=*size;break;
            }
            case RecoveredWorldSkillRequest::opcode: {
                if(!native_world_skill_requests){if(unsupported)*unsupported=UnsupportedRecord{offset,remaining[0]};return {};}
                constexpr auto size=RecoveredWorldSkillRequest::logical_size;
                if(remaining.size()<size)return {};
                const auto request=RecoveredWorldSkillRequest::decode(remaining.first(size));
                if(!request)return {};
                records.emplace_back(*request);offset+=size;break;
            }
            case RecoveredSkillSelectionRequest::opcode: {
                if(!native_skill_selection_requests){if(unsupported)*unsupported=UnsupportedRecord{offset,remaining[0]};return {};}
                const auto size=RecoveredSkillSelectionRequest::record_size(remaining);
                if(!size || remaining.size()<*size)return {};
                auto request=RecoveredSkillSelectionRequest::decode(remaining.first(*size));
                if(!request)return {};
                records.emplace_back(std::move(*request));offset+=*size;break;
            }
            case 0x35: { // Current client commands, not the S2C size table.
                constexpr auto size = RecoveredBattleCommand::logical_size;
                if (remaining.size() < size) return std::nullopt;
                // Explicit actual native skill owner only. Preserve all17
                // bytes; game-owner definition/turn qualification follows.
                // Existing CUSTOM PK/diagnostic grammar remains the default.
                if(remaining[2]==6) {
                    const auto flee=RecoveredBattleFleeCommand::decode(remaining.first(size));
                    if(!flee)return {}; // Whole batch rejects; never fall through as action2/skill.
                    records.emplace_back(*flee);offset+=size;break;
                }
                if(remaining[2]==8) {
                    const auto sos=RecoveredSosBattleCommand::decode(remaining.first(size));
                    if(!sos)return {};
                    records.emplace_back(*sos);offset+=size;break;
                }
                if(native_skill_commands && (remaining[2]==3 || remaining[2]==0x83)) {
                    const auto skill=TaiwanNativeSkillCommand::parse_wire(remaining.first(size));
                    if(!skill)return std::nullopt;
                    records.emplace_back(*skill);offset+=size;break;
                }
                if(const auto action2=RecoveredBattleCommand::parse_action2_logical(remaining.first(size))) {
                    records.emplace_back(*action2);
                    offset+=size;
                    break;
                }
                const auto request = RecoveredBattleCommand::parse_logical(remaining.first(size));
                if (request) records.emplace_back(*request);
                else {
                    const auto control = RecoveredBattleCommand::parse_control_logical(remaining.first(size));
                    if (control) records.emplace_back(*control);
                    else {
                        const auto skill = RecoveredSkillCommand::parse_logical(remaining.first(size));
                        if (!skill) return std::nullopt;
                        // Typed transport only: policy must assemble/validate the
                        // sequence before authorizing any skill or resource use.
                        records.emplace_back(*skill);
                    }
                }
                offset += size;
                break;
            }
            case 0x2e: // Current movement producer 15790: six payload bytes.
                if (remaining.size() < 7) return std::nullopt;
                records.emplace_back(RecoveredMovement::Request{
                    static_cast<std::uint16_t>(remaining[1] + 256u * remaining[2]),
                    static_cast<std::uint16_t>(remaining[3] + 256u * remaining[4]),
                    remaining[5], remaining[6]});
                offset += 7;
                break;
            case 0x30: // Current periodic producer 11750 queues exactly 30 00.
                if (remaining.size() < 2 || remaining[1] != 0) return std::nullopt;
                records.emplace_back(Tick{});
                offset += 2;
                break;
            case 0x36: {
                if (remaining.size()<9) return std::nullopt;
                TimerNotification notification{};
                std::copy_n(remaining.begin()+1,8,notification.payload.begin());
                records.emplace_back(notification);
                offset+=9;
                break;
            }
            case RecoveredInventoryItemRequest::opcode: {
                constexpr auto size = RecoveredInventoryItemRequest::logical_size;
                if (remaining.size() < size) return std::nullopt;
                const auto request = RecoveredInventoryItemRequest::decode(remaining.first(size));
                if (!request) return std::nullopt;
                records.emplace_back(*request);
                offset += size;
                break;
            }
            case RecoveredQuestAction::opcode: {
                constexpr auto size = RecoveredQuestAction::logical_size;
                if (remaining.size() < size) return std::nullopt;
                const auto request = RecoveredQuestAction::decode(remaining.first(size));
                if (!request) return std::nullopt;
                records.emplace_back(*request);
                offset += size;
                break;
            }
            case RecoveredQuestClose::opcode: {
                constexpr auto size = RecoveredQuestClose::logical_size;
                if (remaining.size() < size) return std::nullopt;
                const auto request = RecoveredQuestClose::decode(remaining.first(size));
                if (!request) return std::nullopt;
                records.emplace_back(*request);
                offset += size;
                break;
            }
            case 0x76: {
                if(!guild_relations53){if(unsupported)*unsupported=UnsupportedRecord{offset,remaining[0]};return {};}
                if(remaining.size()<18)return {};const auto action=native_relation_private::decode76(remaining.first(18));if(!action)return {};
                records.emplace_back(*action);offset+=18;break;
            }
            default:
                if(unsupported) *unsupported=UnsupportedRecord{offset,remaining[0]};
                return std::nullopt;
            }
        }
        return records;
    }

    // Exactly one complete zero-seed recovered frame; TCP assembly is external.
    static std::optional<std::vector<Record>> parse_frame(
        std::span<const std::uint8_t> wire,
        std::optional<UnsupportedRecord>* unsupported=nullptr,bool guild_relations53=false,bool beast_views=false,
        bool pk_invitations=false,bool companion_controls6b=false,bool beast_activity9e=false,
        bool e4_controls=false,bool bf_requests=false,bool spectator6e=false,bool map_panel68=false,
        bool c2_controls=false,bool spectator_close=false,bool native_skill_commands=false,bool owned_blacklist=false,bool owned_party_directory=false,
        bool owned_client_options=false,bool native_world_skill_requests=false,bool native_preborn_requests=false,
        bool native_skill_selection_requests=false,bool owned_battle_row_preference=false) {
        if(unsupported) unsupported->reset();
        const auto logical = RecoveredWorldFrame::decode(wire);
        if (!logical) return std::nullopt;
        return decode(*logical,unsupported,guild_relations53,beast_views,pk_invitations,companion_controls6b,
            beast_activity9e,e4_controls,bf_requests,spectator6e,map_panel68,c2_controls,spectator_close,native_skill_commands,owned_blacklist,owned_party_directory,
            owned_client_options,native_world_skill_requests,native_preborn_requests,native_skill_selection_requests,owned_battle_row_preference);
    }
};
}
