#include "protocol/RecoveredWorldRecords.h"
#include <algorithm>
#include <array>
#include <iostream>
#include <stdexcept>
#include <string_view>
#include <type_traits>

namespace {
using World = god2::RecoveredWorldRecords;
using Quest = god2::RecoveredQuestAction;
using Close = god2::RecoveredQuestClose;
using Npc = god2::RecoveredNpcInteraction;
using Inventory = god2::RecoveredInventoryItemRequest;
using InventoryMove = god2::RecoveredInventoryMoveRequest;
using SelectionItem = god2::RecoveredSelectionItemRequest;
using Movement = god2::RecoveredMovement;
using Battle = god2::RecoveredBattleCommand;
using Skill = god2::RecoveredSkillCommand;
using Frame = god2::RecoveredWorldFrame;
using Bytes = std::vector<std::uint8_t>;

static_assert(World::max_logical_size == 0xa00);
// Keep stable early occurrence alternatives; appended protocol types are covered
// by their own round trips. This fixture explicitly refuses unsupported types.
static_assert(std::is_same_v<std::variant_alternative_t<0,World::Record>,Movement::Request>);
static_assert(std::is_same_v<std::variant_alternative_t<7,World::Record>,Battle::BasicAttackRequest>);
static_assert(std::is_same_v<std::variant_alternative_t<std::variant_size_v<World::Record>-1,World::Record>,god2::RecoveredBattleRowSwapCommand::Request>);
static_assert(Quest::encode({0x1234, 2, 0x9a, 0xa5}) ==
              Quest::LogicalRecord{0x85, 0x34, 0x12, 2, 0, 0x9a, 0xa5});

void require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}

void append(Bytes& target, std::span<const std::uint8_t> source) {
    target.insert(target.end(), source.begin(), source.end());
}

Bytes reconstruct(const std::vector<World::Record>& records) {
    Bytes result;
    for (const auto& record : records) {
        std::visit([&result](const auto& value) {
            using T = std::decay_t<decltype(value)>;
            if constexpr (std::is_same_v<T, Movement::Request>) {
                const auto logical = Frame::decode(Movement::encode(value));
                require(logical.has_value(), "Existing movement encoder rejected");
                append(result, *logical);
            } else if constexpr (std::is_same_v<T, World::Tick>) {
                append(result, std::array<std::uint8_t, 2>{0x30, 0});
            } else if constexpr (std::is_same_v<T, god2::RecoveredGuildRoster::PanelReady>) {
                append(result, std::array<std::uint8_t, 2>{0xb8, 0});
            } else if constexpr (std::is_same_v<T, World::ClientControl1F>) {
                append(result, std::array<std::uint8_t, 2>{0x1f, 0});
            } else if constexpr (std::is_same_v<T, World::ClientControl6D>) {
                append(result, std::array<std::uint8_t, 2>{0x6d, 0});
            } else if constexpr (std::is_same_v<T, World::ClientOpaque74>) {
                append(result, std::array<std::uint8_t, 2>{0x74, value.payload});
            } else if constexpr (std::is_same_v<T, World::ClientPanelOpen88>) {
                result.push_back(0x88);append(result,value.payload);
            } else if constexpr (std::is_same_v<T, World::ClientOptionsNotification>) {
                result.push_back(0x1d);append(result,value.payload);
            } else if constexpr (std::is_same_v<T, World::ClientPoseNotification>) {
                result.push_back(0x66);append(result,value.payload);
            } else if constexpr (std::is_same_v<T, god2::RecoveredPet2Revert::Request>) {
                append(result,god2::RecoveredPet2Revert::encode(value));
            } else if constexpr (std::is_same_v<T, god2::RecoveredRoleText::Request>) {
                const auto logical=god2::RecoveredRoleText::encode_request(value);
                require(logical.has_value(),"Role text reconstruction rejected");
                append(result,*logical);
            } else if constexpr (std::is_same_v<T, god2::RecoveredTeleport::Selection>) {
                append(result, std::array<std::uint8_t,5>{value.opcode,
                    static_cast<std::uint8_t>(value.context),static_cast<std::uint8_t>(value.context>>8),
                    value.destination,value.opaque_tail});
            } else if constexpr (std::is_same_v<T,god2::RecoveredGuildDisband75::Request>) {
                append(result,std::array<std::uint8_t,2>{0x75,value.slot});
            } else if constexpr (std::is_same_v<T,god2::RecoveredGuildLeave::Request>) {
                append(result,std::array<std::uint8_t,2>{0x73,value.slot});
            } else if constexpr (std::is_same_v<T,god2::RecoveredGuildMembership::Request>) {
                const auto raw=god2::RecoveredGuildMembership::encode_request(value);
                require(raw.has_value(),"Guild membership reconstruction rejected");append(result,*raw);
            } else if constexpr (std::is_same_v<T,god2::RecoveredGuildLeadership::Request>) {
                append(result,std::array<std::uint8_t,2>{static_cast<std::uint8_t>(value.action),value.slot});
            } else if constexpr (std::is_same_v<T,god2::RecoveredGuildAnnouncement::Request>) {
                const auto raw=god2::RecoveredGuildAnnouncement::encode_request(value);
                require(raw.has_value(),"Guild announcement reconstruction rejected");append(result,*raw);
            } else if constexpr (std::is_same_v<T, World::TimerNotification>) {
                result.push_back(0x36);
                append(result,value.payload);
            } else if constexpr (std::is_same_v<T, World::ContextNotification>) {
                result.push_back(0x1c);
                append(result,value.payload);
            } else if constexpr (std::is_same_v<T, World::ClientDiagnostic>) {
                append(result,value.bytes);
            } else if constexpr (std::is_same_v<T, god2::RecoveredChat::Request> || std::is_same_v<T, god2::RecoveredPartyChat::Request> || std::is_same_v<T,god2::RecoveredPrivateChat::Request> || std::is_same_v<T,god2::RecoveredGuildChat::Request>) {
                const auto size=value.legacy_text.size()+8;
                result.push_back(0x2f);
                result.push_back(static_cast<std::uint8_t>(size));
                result.push_back(static_cast<std::uint8_t>(size>>8));
                append(result,value.client_header);
                result.insert(result.end(),value.legacy_text.begin(),value.legacy_text.end());
                result.push_back(0);
            } else if constexpr (std::is_same_v<T, Inventory::Request>) {
                append(result, Inventory::encode(value));
            } else if constexpr (std::is_same_v<T, InventoryMove::Request>) {
                append(result, InventoryMove::encode(value));
            } else if constexpr (std::is_same_v<T, god2::RecoveredInventoryDiscard::Request>) {
                append(result,god2::RecoveredInventoryDiscard::encode(value));
            } else if constexpr (std::is_same_v<T, god2::RecoveredParty::Request>) {
                append(result,god2::RecoveredParty::encode(value));
            } else if constexpr (std::is_same_v<T, god2::RecoveredSosSupportRequest::Request>) {
                append(result,god2::RecoveredSosSupportRequest::encode(value));
            } else if constexpr (std::is_same_v<T, god2::RecoveredSosBattleCommand::Request>) {
                append(result,god2::RecoveredSosBattleCommand::encode(value));
            } else if constexpr (std::is_same_v<T, god2::RecoveredBattleRowSwapCommand::Request>) {
                append(result,god2::RecoveredBattleRowSwapCommand::encode(value));
            } else if constexpr (std::is_same_v<T, god2::RecoveredBattleFleeCommand::Request>) {
                append(result,god2::RecoveredBattleFleeCommand::encode(value));
            } else if constexpr (std::is_same_v<T, god2::RecoveredTeamRequest57::Request>) {
                append(result,god2::RecoveredTeamRequest57::encode(value));
            } else if constexpr (std::is_same_v<T, god2::RecoveredPartyExitRequest5A::Request>) {
                append(result,god2::RecoveredPartyExitRequest5A::encode(value));
            } else if constexpr (std::is_same_v<T, god2::RecoveredPartyPositionQuery::Request>) {
                append(result,god2::RecoveredPartyPositionQuery::encode(value));
            } else if constexpr (std::is_same_v<T, god2::RecoveredTrade::Request>) {
                append(result,god2::RecoveredTrade::encode(value));
            } else if constexpr (std::is_same_v<T, god2::RecoveredBank::Request>) {
                append(result,god2::RecoveredBank::encode(value));
            } else if constexpr (std::is_same_v<T, god2::RecoveredBankItems::Request>) {
                append(result,god2::RecoveredBankItems::encode(value));
            } else if constexpr (std::is_same_v<T, god2::RecoveredDeitySelection::Request>) {
                append(result, god2::RecoveredDeitySelection::encode(value));
            } else if constexpr (std::is_same_v<T, World::DailyPanelOpen>) {
                append(result, std::array<std::uint8_t, 2>{0xd7, 0});
            } else if constexpr (std::is_same_v<T, god2::RecoveredAttributeAllocation::Request>) {
                append(result, std::array<std::uint8_t, 2>{0x21, value.selector});
            } else if constexpr (std::is_same_v<T, god2::RecoveredDailyQuestRequest::Request>) {
                std::visit([&result](const auto& daily) {
                    using Daily = std::decay_t<decltype(daily)>;
                    const auto encoded = god2::RecoveredDailyQuestRequest::encode(daily);
                    if constexpr (std::is_same_v<Daily, god2::RecoveredDailyQuestRequest::Selection>) {
                        require(encoded.has_value(), "Daily selection encoder rejected");
                        append(result, *encoded);
                    } else {
                        append(result, encoded);
                    }
                }, value);
            } else if constexpr (std::is_same_v<T, god2::RecoveredTargetItemRequest::Request>) {
                append(result, god2::RecoveredTargetItemRequest::encode(value));
            } else if constexpr (std::is_same_v<T, SelectionItem::Request>) {
                append(result, SelectionItem::encode(value));
            } else if constexpr (std::is_same_v<T, Quest::Request>) {
                append(result, Quest::encode(value));
            } else if constexpr (std::is_same_v<T, Close::Request>) {
                append(result, Close::encode(value));
            } else if constexpr (std::is_same_v<T, Npc::Request>) {
                append(result, Npc::encode(value));
            } else if constexpr (std::is_same_v<T, Skill::Record>) {
                append(result, std::array<std::uint8_t,5>{0x35,value.actor_position,
                       static_cast<std::uint8_t>(value.continuation ? 0x83 : 3),
                       value.side_flag,value.unwritten_byte3});
                for(const auto mask:value.target_masks) {
                    result.push_back(static_cast<std::uint8_t>(mask));
                    result.push_back(static_cast<std::uint8_t>(mask>>8));
                }
                for(unsigned shift=0;shift<32;shift+=8)
                    result.push_back(static_cast<std::uint8_t>(value.context_storage>>shift));
                append(result,std::array<std::uint8_t,4>{value.selection_id_byte,value.selection_kind_byte,0,0});
            } else if constexpr(std::is_same_v<T,Battle::BasicAttackRequest>||std::is_same_v<T,Battle::ControlRequest>||std::is_same_v<T,Battle::Action2Request>) {
                const auto& fields = [&]() -> const Battle::BasicAttackRequest& {
                    if constexpr (std::is_same_v<T, Battle::ControlRequest> || std::is_same_v<T, Battle::Action2Request>) return value.fields;
                    else return value;
                }();
                constexpr std::uint8_t action = std::is_same_v<T, Battle::ControlRequest> ? 0x0b :
                    (std::is_same_v<T, Battle::Action2Request> ? 2 : 1);
                append(result, std::array<std::uint8_t,5>{0x35,fields.actor_position,action,
                       fields.side_flag,fields.unwritten_byte3});
                for(const auto mask:fields.target_masks) {
                    result.push_back(static_cast<std::uint8_t>(mask));
                    result.push_back(static_cast<std::uint8_t>(mask>>8));
                }
                for(const auto word:{fields.context_storage,fields.unwritten_parameter})
                    for(unsigned shift=0;shift<32;shift+=8)
                        result.push_back(static_cast<std::uint8_t>(word>>shift));
            }else throw std::runtime_error("This legacy reconstruction fixture has no encoder for the appended typed grammar");
        }, record);
    }
    return result;
}

void accept(const Bytes& logical, std::size_t count) {
    const auto before = logical;
    const auto decoded = World::decode(logical);
    require(decoded && decoded->size() == count, "Valid logical batch rejected/count changed");
    require(reconstruct(*decoded) == logical, "Logical bytes/order not preserved");
    require(logical == before, "Logical decode mutated input");
    const auto wire = Frame::encode(logical);
    const auto wire_before = wire;
    const auto framed = World::parse_frame(wire);
    require(framed && framed->size() == count, "Valid framed batch rejected/count changed");
    require(reconstruct(*framed) == logical, "Framed bytes/order not preserved");
    require(wire == wire_before, "Frame parse mutated input");
}

void reject(const Bytes& logical) {
    const auto before = logical;
    require(!World::decode(logical), "Malformed batch exposed records");
    require(logical == before, "Rejection mutated logical input");
    if (!logical.empty() && logical.size() <= World::max_logical_size) {
        const auto wire = Frame::encode(logical);
        const auto wire_before = wire;
        require(!World::parse_frame(wire), "Valid envelope bypassed logical rejection");
        require(wire == wire_before, "Rejection mutated framed input");
    }
}

void inventory_move_contract() {
    for(const auto source:{0u,29u,30u,49u,127u,128u,255u}) {
        for(const auto destination:{0u,29u,30u,49u,127u,128u,255u}) {
            const Bytes bytes{0x24,static_cast<std::uint8_t>(source),static_cast<std::uint8_t>(destination)};
            accept(bytes,1);
            const auto decoded=World::decode(bytes);
            require(std::get<InventoryMove::Request>(decoded->front())==InventoryMove::Request{
                static_cast<std::uint8_t>(source),static_cast<std::uint8_t>(destination)},
                "Move wire fields narrowed or swapped");
            for(std::size_t length=0;length<bytes.size();++length) reject(Bytes(bytes.begin(),bytes.begin()+length));
            auto extended=bytes;extended.push_back(0);
            require(!InventoryMove::decode(extended),"Move decoder accepted trailing byte");
            reject(extended);
            Bytes batch{0x30,0};append(batch,bytes);append(batch,std::array<std::uint8_t,2>{0x30,0});
            accept(batch,3); // Framing is structural; service owns callback policy.
            append(batch,bytes);accept(batch,4);
            auto partial=bytes;partial.push_back(0x24);reject(partial);
            partial.push_back(0);reject(partial);
            auto mixed=bytes;append(mixed,Inventory::encode({3107,0,0}));accept(mixed,2);
        }
    }
}

void role_text_and_pet_revert_contract() {
    for(unsigned count=0;count<=15;++count) {
        Bytes text(17,0xa5);text[0]=0x20;
        std::fill(text.begin()+1,text.begin()+1+count,'A');text[1+count]=0;
        accept(text,1);
        auto batch=text;append(batch,std::array<std::uint8_t,4>{0xd6,29,42,4});
        append(batch,std::array<std::uint8_t,2>{0x30,0});accept(batch,3);
        for(std::size_t size=1;size<text.size();++size)reject(Bytes(text.begin(),text.begin()+size));
    }
    Bytes missing_nul(17,0xa5);missing_nul[0]=0x20;reject(missing_nul);
    for(const auto slot:{0u,29u,32u,96u,255u}) {
        const Bytes pet{0xd6,static_cast<std::uint8_t>(slot),43,4};accept(pet,1);
        for(std::size_t size=1;size<pet.size();++size)reject(Bytes(pet.begin(),pet.begin()+size));
    }
}

void allocation_and_daily_contract() {
    for (std::uint8_t selector=1; selector<=4; ++selector) {
        const Bytes request{0x21,selector};
        accept(request,1);
        auto repeated=request;append(repeated,request);accept(repeated,2);
        auto ticked=request;append(ticked,std::array<std::uint8_t,2>{0x30,0});accept(ticked,2);
    }
    reject({0x21});reject({0x21,0});reject({0x21,5});reject({0x21,2,0xff});
    accept({0xd7,0},1);reject({0xd7,1});
    const auto selection=god2::RecoveredDailyQuestRequest::encode(
        god2::RecoveredDailyQuestRequest::Selection{3,2,0xff,0x1234,2,0xa5});
    require(selection.has_value(),"Qualified daily selection rejected");
    accept(Bytes(selection->begin(),selection->end()),1);
    const auto auxiliary=god2::RecoveredDailyQuestRequest::encode(god2::RecoveredDailyQuestRequest::Auxiliary{});
    accept(Bytes(auxiliary.begin(),auxiliary.end()),1);
}

const std::array<Bytes, 4> fixtures{{
    {0x2e, 0x34, 0x12, 0xcd, 0xab, 0xff, 0x85},
    {0x30, 0},
    {0x25, 0x34, 0x92, 0x31, 0xa5},
    // current_quest_action.py::build_report(), native 97DC0 -> 132E0:
    // image SHA256 149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763.
    {0x85, 0x34, 0x12, 2, 0, 0x9a, 0xa5}
}};

void quest_contract() {
    const auto known = Quest::decode(fixtures[3]);
    require(known && known->request_word == 0x1234 && known->reply_word == 2 &&
            known->context_byte == 0x9a && known->opaque_tail == 0xa5,
            "Current native 85341202009aa5 fixture changed");
    for (std::size_t size = 0; size < Quest::logical_size; ++size)
        require(!Quest::decode(std::span(fixtures[3]).first(size)), "Quest truncation accepted");
    auto extended = fixtures[3];
    extended.push_back(0);
    require(!Quest::decode(extended), "Quest extra byte accepted");
    auto concatenated = fixtures[3];
    append(concatenated, fixtures[3]);
    require(!Quest::decode(concatenated), "Quest concatenation accepted as one record");
    for (unsigned opcode = 0; opcode < 256; ++opcode) {
        auto wrong = fixtures[3];
        wrong[0] = static_cast<std::uint8_t>(opcode);
        require(Quest::decode(wrong).has_value() == (opcode == 0x85), "Quest opcode unchecked");
    }
    // Each word takes every 16-bit value, including FFFF and both high bits.
    for (unsigned word = 0; word <= 0xffff; ++word) {
        const Quest::Request expected{static_cast<std::uint16_t>(word),
            static_cast<std::uint16_t>(0xffffu - word),
            static_cast<std::uint8_t>(word >> 8), static_cast<std::uint8_t>(word)};
        const auto bytes = Quest::encode(expected);
        const auto before = bytes;
        const auto actual = Quest::decode(bytes);
        require(actual && actual->request_word == expected.request_word &&
                actual->reply_word == expected.reply_word &&
                actual->context_byte == expected.context_byte &&
                actual->opaque_tail == expected.opaque_tail, "Quest fields normalized/lost");
        require(bytes == before, "Quest decode mutated input");
    }
}

void close_contract() {
    const Bytes native{0x86,0xef,0xbe,0,0x10};
    const auto known=Close::decode(native);
    require(known && known->source_low_word==0xbeef && known->this_high_word==0x1000,
            "Native close fields changed");
    accept(native,1);
    for(std::size_t size=0;size<Close::logical_size;++size) {
        require(!Close::decode(std::span(native).first(size)),"Short close accepted");
        reject(Bytes(native.begin(),native.begin()+static_cast<std::ptrdiff_t>(size)));
    }
    auto extra=native;extra.push_back(0xff);
    require(!Close::decode(extra),"Extended close accepted");reject(extra);
    for(unsigned opcode=0;opcode<256;++opcode) {
        auto wrong=native;wrong[0]=static_cast<std::uint8_t>(opcode);
        require(Close::decode(wrong).has_value()==(opcode==0x86),"Close opcode unchecked");
    }
    for(unsigned word=0;word<65536;++word) {
        const Close::Request request{static_cast<std::uint16_t>(word),
                                     static_cast<std::uint16_t>(word^0xffff)};
        const auto encoded=Close::encode(request);
        const auto parsed=Close::decode(encoded);
        require(parsed && parsed->source_low_word==request.source_low_word &&
                parsed->this_high_word==request.this_high_word,"Close normalized opaque words");
    }
    auto close_action=native;append(close_action,fixtures[3]);accept(close_action,2);
    // Physical NPC click-away capture: close and ground movement share one C2S frame.
    // The capture is a decrypted client frame; decode its logical body.
    const Bytes click_away{0x86,0x01,0x00,0x81,0x1a,
                           0x2e,0x6e,0x00,0x47,0x00,0x01,0xc2};
    const auto click_records=World::decode(click_away);
    require(click_records && click_records->size()==2 &&
            std::holds_alternative<Close::Request>((*click_records)[0]) &&
            std::holds_alternative<Movement::Request>((*click_records)[1]),
            "Physical close/movement frame grammar changed");
    require(std::get<Movement::Request>((*click_records)[1]).x==110 &&
            std::get<Movement::Request>((*click_records)[1]).y==71,
            "Physical click-away movement changed");
    auto actions=fixtures[3];append(actions,fixtures[3]);accept(actions,2);
    // No invented mandatory successor; close, action and tick preserve order.
    append(close_action,native);append(close_action,fixtures[1]);accept(close_action,4);
}

void selection_item_contract() {
    // Synthetic fields exercising the native 96550 record layout. Original
    // MED02 branch selection is checked separately with executed client code.
    const Bytes native_shape{0x28, 0x34, 0x12, 29, 1};
    const auto request=SelectionItem::decode(native_shape);
    require(request && request->client_item_id==0x1234 && request->raw_slot==29,
            "Selection item fields changed");
    require(SelectionItem::encode(*request)==SelectionItem::LogicalRecord{0x28,0x34,0x12,29,1},
            "Selection item reconstruction changed");
    accept(native_shape,1);
    for(std::size_t size=0;size<native_shape.size();++size) {
        require(!SelectionItem::decode(std::span(native_shape).first(size)),
                "Truncated selection item accepted");
        reject(Bytes(native_shape.begin(),native_shape.begin()+static_cast<std::ptrdiff_t>(size)));
    }
    for(const auto tail:{0u,2u,255u}) {
        auto changed=native_shape;changed.back()=static_cast<std::uint8_t>(tail);
        require(!SelectionItem::decode(changed),"Unobserved selection mode accepted");
        reject(changed);
    }
    auto batch=fixtures[1];append(batch,native_shape);append(batch,fixtures[0]);accept(batch,3);
    const auto decoded=World::decode(batch);
    require(decoded && std::holds_alternative<SelectionItem::Request>((*decoded)[1]),
            "Selection item was not dispatched as typed world record");
    auto partial=fixtures[1];append(partial,std::span(native_shape).first(4));reject(partial);
}

void battle_contract() {
    const Bytes skill{0x35,13,3,1,0xa5,1,0,0,0,0x78,0x56,0x34,0x12,7,0,0,0};
    for(const auto action:{3,0x83}) {
        auto raw=skill;raw[2]=static_cast<std::uint8_t>(action);accept(raw,1);
        for(unsigned at=1;at<raw.size();++at) for(unsigned value=0;value<256;++value) {
            auto changed=raw;changed[at]=static_cast<std::uint8_t>(value);
            if(Skill::parse_logical(changed) || Battle::parse_logical(changed) ||
               Battle::parse_control_logical(changed) || Battle::parse_action2_logical(changed)) accept(changed,1);
            else reject(changed);
        }
        for(std::size_t length=1;length<raw.size();++length) {
            auto prefix=fixtures[0];append(prefix,std::span(raw).first(length));reject(prefix);
        }
    }
    auto sequence=skill;sequence[2]=0x83;append(sequence,skill);accept(sequence,2);
    const Bytes logical{0x35,13,1,1,0xa5,1,0,0,0x20,
                        0x78,0x56,0x34,0x12,0xff,0x80,0x86,0x35};
    accept(logical,1);
    auto control=logical;control[2]=0x0b;accept(control,1);
    const auto control_records=World::decode(control);
    require(std::holds_alternative<Battle::ControlRequest>((*control_records)[0]),
            "Control command was aliased to basic attack");
    auto commands=logical;append(commands,control);append(commands,logical);accept(commands,3);
    auto mixed=fixtures[1];append(mixed,logical);append(mixed,fixtures[0]);
    accept(mixed,3);
    const auto parsed=World::decode(mixed);
    const auto& attack=std::get<Battle::BasicAttackRequest>((*parsed)[1]);
    require(attack.actor_position==13 && attack.side_flag==1 &&
            attack.target_masks==std::array<std::uint16_t,2>{1,0x2000} &&
            attack.context_storage==0x12345678 && attack.unwritten_parameter==0x358680ff,
            "Battle fields not preserved");
    for(std::size_t size=0;size<logical.size();++size) {
        reject(Bytes(logical.begin(),logical.begin()+static_cast<std::ptrdiff_t>(size)));
        if(size) {
            auto suffix=fixtures[0];append(suffix,std::span(logical).first(size));reject(suffix);
        }
    }
    for(unsigned at=1;at<logical.size();++at) for(unsigned value=0;value<256;++value) {
        auto changed=logical;changed[at]=static_cast<std::uint8_t>(value);
        if(Battle::parse_logical(changed) || Battle::parse_control_logical(changed) || Battle::parse_action2_logical(changed)) accept(changed,1);
        else reject(changed);
    }
    for(unsigned at=1;at<control.size();++at) for(unsigned value=0;value<256;++value) {
        auto changed=control;changed[at]=static_cast<std::uint8_t>(value);
        if(Battle::parse_logical(changed) || Battle::parse_control_logical(changed) || Battle::parse_action2_logical(changed)) accept(changed,1);
        else reject(changed);
    }
    auto suffix=logical;suffix.push_back(0xff);reject(suffix);
}

void ordering_and_opaque_values() {
    std::array<std::size_t, 4> order{0, 1, 2, 3};
    do {
        Bytes logical;
        for (const auto index : order) append(logical, fixtures[index]);
        accept(logical, order.size());
        const auto records = World::decode(logical);
        for (std::size_t i = 0; i < order.size(); ++i)
            require((*records)[i].index() == std::array<std::size_t,4>{0,1,2,5}[order[i]], "Variant order changed");
    } while (std::next_permutation(order.begin(), order.end()));

    for (unsigned value = 0; value < 256; ++value) {
        const auto byte = static_cast<std::uint8_t>(value);
        const Bytes movement{0x2e, 0xff, 0xff, 0, 0x80, byte, byte};
        const Bytes inventory{0x25, 0, 0, byte, byte};
        const Bytes quest{0x85, 0xff, 0xff, 0xff, 0xff, byte, byte};
        Bytes logical;
        append(logical, quest);
        append(logical, movement);
        append(logical, inventory);
        append(logical, fixtures[1]);
        append(logical, quest);
        accept(logical, 5);
        const auto records = World::decode(logical);
        const auto& m = std::get<Movement::Request>((*records)[1]);
        require(m.x == 65535 && m.y == 32768 && m.sequence == byte && m.opaque_tail == byte,
                "Movement fields filtered or lost");
        const auto& item = std::get<Inventory::Request>((*records)[2]);
        require(item.client_item_id == 0 && item.raw_slot == byte && item.raw_tail == byte,
                "Inventory fields filtered or lost");
        const auto& q = std::get<Quest::Request>((*records)[0]);
        require(q.request_word == 65535 && q.reply_word == 65535 &&
                q.context_byte == byte && q.opaque_tail == byte, "Quest raw values lost");
    }
}

void truncation_and_suffixes() {
    reject({});
    Bytes batch;
    std::vector<std::size_t> boundaries;
    for (const auto& fixture : fixtures) {
        accept(fixture, 1);
        append(batch, fixture);
        boundaries.push_back(batch.size());
        for (std::size_t size = 0; size < fixture.size(); ++size) {
            const Bytes prefix(fixture.begin(), fixture.begin() + size);
            reject(prefix);
            if (!prefix.empty()) {
                auto suffixed = fixtures[0];
                append(suffixed, prefix);
                reject(suffixed);
            }
        }
    }
    for (std::size_t size = 0; size <= batch.size(); ++size) {
        const auto boundary = std::find(boundaries.begin(), boundaries.end(), size);
        const Bytes prefix(batch.begin(), batch.begin() + size);
        if (boundary == boundaries.end()) reject(prefix);
        else accept(prefix, static_cast<std::size_t>(boundary - boundaries.begin()) + 1);
    }
    for (unsigned opcode = 0; opcode < 256; ++opcode) {
        // Seven zero bytes now form structurally valid trade/bank item
        // request. Ownership/quantity rejection belongs to the runtime service.
        if (opcode == 0x2a || opcode == 0x63 || opcode == 0x64 || opcode == 0x65 || opcode == 0x2e || opcode == 0x30 || opcode == 0x25 || opcode == 0x26 || opcode == 0x85 || opcode == 0x86) continue;
        const Bytes unsupported{static_cast<std::uint8_t>(opcode), 0, 0, 0, 0, 0, 0};
        reject(unsupported);
        auto suffixed = batch;
        append(suffixed, unsupported);
        reject(suffixed);
    }
    for (unsigned value = 1; value < 256; ++value) {
        const Bytes tick{0x30, static_cast<std::uint8_t>(value)};
        reject(tick);
        auto suffixed = batch;
        append(suffixed, tick);
        reject(suffixed);
    }
    // Competing record lengths must not leak in from an opposite-direction table.
    for (const auto& fixture : fixtures) {
        for (std::size_t size = 1; size <= 32; ++size) {
            Bytes candidate(size, 0);
            candidate[0] = fixture[0];
            if (size == fixture.size()) accept(candidate, 1);
            else reject(candidate);
        }
    }
    for (const auto opcode : {0x35, 0x41, 0x5d, 0x7a, 0xdb}) {
        for (std::size_t size = 1; size <= 32; ++size) {
            Bytes opposite_or_other_lane(size, 0);
            opposite_or_other_lane[0] = static_cast<std::uint8_t>(opcode);
            reject(opposite_or_other_lane);
        }
    }
}

void maximum_bounds() {
    Bytes ticks;
    for (std::size_t count = 1; count <= World::max_logical_size / 2; ++count) {
        append(ticks, fixtures[1]);
        accept(ticks, count);
    }
    auto mixed = fixtures[2];
    append(mixed, fixtures[3]);
    while (mixed.size() < World::max_logical_size) append(mixed, fixtures[1]);
    accept(mixed, 2 + (World::max_logical_size - 12) / 2);
    auto odd = fixtures[2];
    while (odd.size() < World::max_logical_size - 1) append(odd, fixtures[1]);
    accept(odd, 1 + (World::max_logical_size - 6) / 2);
    append(odd, fixtures[1]); // 0xA01, structurally complete but too large.
    reject(odd);
    append(ticks, fixtures[1]);
    reject(ticks);
    reject(Bytes(65535, 0x30));
    mixed.back() = 1;
    reject(mixed); // Full-capacity valid prefix with a malformed final record.
}

void frame_integrity_and_ownership() {
    const Bytes native_tick_wire{5, 0, 0x2d, 0x2d, 0x22};
    const auto tick = World::parse_frame(native_tick_wire);
    require(tick && tick->size() == 1 && std::holds_alternative<World::Tick>(tick->front()),
            "Native periodic frame fixture changed");
    Bytes logical;
    for (const auto& fixture : fixtures) append(logical, fixture);
    const auto wire = Frame::encode(logical);
    for (std::size_t size = 0; size < wire.size(); ++size)
        require(!World::parse_frame(std::span(wire).first(size)), "Truncated frame accepted");
    for (unsigned value = 1; value < 256; ++value) {
        auto corrupt = wire;
        corrupt.back() ^= static_cast<std::uint8_t>(value);
        const auto before = corrupt;
        require(!World::parse_frame(corrupt), "Corrupt checksum accepted");
        require(corrupt == before, "Corrupt frame mutated");
    }
    for (std::size_t position = 0; position < 2; ++position) {
        for (unsigned value = 1; value < 256; ++value) {
            auto corrupt = wire;
            corrupt[position] ^= static_cast<std::uint8_t>(value);
            require(!World::parse_frame(corrupt), "Corrupt frame length accepted");
        }
    }
    auto corrupt_payload = wire;
    corrupt_payload[2] ^= 1;
    require(!World::parse_frame(corrupt_payload), "Corrupt payload fixture accepted");
    auto extra = wire;
    extra.push_back(0);
    require(!World::parse_frame(extra), "Trailing wire byte accepted");
    auto concatenated = wire;
    append(concatenated, wire);
    require(!World::parse_frame(concatenated), "Concatenated frames accepted as one");
    for (const auto size : {0u, 1u, 2u, 3u, 2564u, 65535u}) {
        Bytes bad(size, 0);
        if (size >= 2) {
            bad[0] = static_cast<std::uint8_t>(size);
            bad[1] = static_cast<std::uint8_t>(size >> 8);
        }
        require(!World::parse_frame(bad), "Out-of-bounds envelope accepted");
    }
    const auto owned = World::parse_frame(Frame::encode(logical));
    auto mutable_input = logical;
    const auto owned_logical = World::decode(mutable_input);
    std::fill(mutable_input.begin(), mutable_input.end(), std::uint8_t{0});
    require(owned && reconstruct(*owned) == logical, "Framed records borrowed destroyed input");
    require(owned_logical && reconstruct(*owned_logical) == logical,
            "Logical records borrowed mutable input");
    require(!World::decode(mutable_input), "Malformed input accepted after successful call");
    require(reconstruct(*owned_logical) == logical, "Failed call changed prior output");
    auto movement_ticks = fixtures[0];
    append(movement_ticks, fixtures[1]);
    const auto old_batch = Movement::parse_world_batch(Frame::encode(movement_ticks));
    require(old_batch && old_batch->movements.size() == 1 && old_batch->ticks == 1,
            "Existing movement world API changed");
    require(!Movement::parse_batch(Frame::encode(movement_ticks)), "Movement-only API changed");
    require(Movement::parse(Frame::encode(fixtures[0])).has_value(), "Movement single API changed");
}

void teleport_contract() {
    using Teleport=god2::RecoveredTeleport;
    for(const auto context:{0u,0x61du,0x61eu,0x61fu,0x620u,0x621u,0x622u,0x623u,0xffffu}) {
        const auto opcode=static_cast<std::uint8_t>(Teleport::special_context(static_cast<std::uint16_t>(context))?0xa9:0x99);
        for(unsigned tail=0;tail<256;++tail) {
            const Bytes bytes{opcode,static_cast<std::uint8_t>(context),static_cast<std::uint8_t>(context>>8),
                static_cast<std::uint8_t>(1+tail%5),static_cast<std::uint8_t>(tail)};
            const auto records=World::parse_frame(Frame::encode(bytes));
            require(records && records->size()==1 &&
                std::holds_alternative<Teleport::Selection>(records->front()),"Teleport selection type missing");
            const auto& selection=std::get<Teleport::Selection>(records->front());
            require(selection.context==context && selection.destination==bytes[3] && selection.opaque_tail==tail &&
                reconstruct(*records)==bytes,"Teleport selection fields changed");
        }
        Bytes bytes{opcode,static_cast<std::uint8_t>(context),static_cast<std::uint8_t>(context>>8),5,0xab};
        for(std::size_t size=0;size<bytes.size();++size)
            require(!World::decode(std::span(bytes).first(size)),"Truncated teleport selection accepted");
        auto wrong=bytes;wrong[0]=opcode==0x99?0xa9:0x99;reject(wrong);
        wrong=bytes;wrong[3]=0;reject(wrong);wrong[3]=6;reject(wrong);
        wrong=bytes;wrong.push_back(0xff);reject(wrong);
        // Grammar remains lossless for structural batches. Service policy must
        // reject mixed teleport actions before invoking any callback.
        append(bytes,Bytes{0x30,0});
        const auto batch=World::decode(bytes);
        require(batch && batch->size()==2 && reconstruct(*batch)==bytes,"Teleport batch grammar changed");
    }
}

Bytes hex(std::string_view value) {
    require(value.size() % 2 == 0 && value.size() <= 2 * (World::max_logical_size + 3),
            "Invalid hex length");
    const auto digit = [](char c) -> unsigned {
        if (c >= '0' && c <= '9') return static_cast<unsigned>(c - '0');
        if (c >= 'a' && c <= 'f') return static_cast<unsigned>(c - 'a' + 10);
        if (c >= 'A' && c <= 'F') return static_cast<unsigned>(c - 'A' + 10);
        throw std::invalid_argument("Invalid hex digit");
    };
    Bytes result;
    for (std::size_t i = 0; i < value.size(); i += 2)
        result.push_back(static_cast<std::uint8_t>(16 * digit(value[i]) + digit(value[i + 1])));
    return result;
}

void print(std::span<const std::uint8_t> bytes) {
    constexpr char digits[] = "0123456789abcdef";
    for (const auto byte : bytes) std::cout << digits[byte >> 4] << digits[byte & 15];
    std::cout << '\n';
}
}

int main(int argc, char** argv) {
    try {
        if (argc == 3) {
            const auto bytes = hex(argv[2]);
            const std::string_view mode = argv[1];
            if (mode == "--quest") {
                const auto request = Quest::decode(bytes);
                require(request.has_value(), "Invalid quest record");
                print(Quest::encode(*request));
            } else {
                require(mode == "--logical" || mode == "--frame", "Unknown mode");
                const auto records = mode == "--logical" ? World::decode(bytes) : World::parse_frame(bytes);
                require(records.has_value(), "Invalid world batch");
                print(reconstruct(*records));
            }
        } else {
            require(argc == 1, "Expected --quest/--logical/--frame HEX");
            const auto chat=hex("2f330000000000b943c0b8c5debfe8a4ceadecabc8a4e1baddaa"
                "baa7deafe0aed1a8cfa5ceac79b57ba97ca5bcb1b5b3716100");
            const auto parsed_chat=World::decode(chat);
            require(parsed_chat && parsed_chat->size()==1 &&
                std::holds_alternative<god2::RecoveredChat::Request>(parsed_chat->front()),
                "Captured original client common chat rejected");
            require(reconstruct(*parsed_chat)==chat,"Captured chat bytes changed");
            auto bad_chat=chat;bad_chat[1]--;reject(bad_chat);
            auto live_chat=chat;
            live_chat[3]=0x80;live_chat[4]=0x76;
            const auto parsed_live_chat=World::decode(live_chat);
            require(parsed_live_chat && parsed_live_chat->size()==1 &&
                std::get<god2::RecoveredChat::Request>(parsed_live_chat->front()).client_header==
                    std::array<std::uint8_t,4>{0x80,0x76,0,0} &&
                reconstruct(*parsed_live_chat)==live_chat,
                "Original client nonzero common-chat header rejected");
            bad_chat=chat;bad_chat.back()='a';reject(bad_chat);
            const auto display=god2::RecoveredChat::display(0x1234,true,"abc");
            require(display.size()==17 && display[0]==0x5c && display[1]==17 &&
                display[5]==0x34 && display[6]==0x12 && display[9]==0x80 &&
                display[13]=='a' && display.back()==0,"Original client chat display layout");
            const auto opening=hex("350002000001000000000000000000000035000b0000010000000000000000000000");
            accept(opening,2);
            const auto commands=*World::decode(opening);
            require(std::holds_alternative<Battle::Action2Request>(commands[0]),"Action2 must not alias attack");
            require(std::holds_alternative<Battle::ControlRequest>(commands[1]),"Opening control missing");
            const auto& fields=std::get<Battle::Action2Request>(commands[0]).fields;
            require(fields.actor_position==0 && fields.side_flag==0 && fields.target_masks==std::array<std::uint16_t,2>{1,0},"Observed action2 fields changed");
            for(std::size_t n=0;n<17;++n)
                require(!Battle::parse_action2_logical(std::span(opening).first(n)),"Truncated action2 accepted");
            auto invalid=opening;invalid[2]=0x82;
            require(!World::decode(invalid),"Unqualified action2 continuation accepted");
            const Bytes timer{0x36,0,0,0,0,1,0,0,0};
            const Bytes context{0x1c,1,0,0,0};
            const Bytes diagnostic_and_move{
                0x9a,10,0,0,'t','e','s','t',0,0,
                0x2e,18,0,12,0,1,0,
                0x30,0};
            const auto mixed_diagnostic=World::decode(diagnostic_and_move);
            require(mixed_diagnostic && mixed_diagnostic->size()==3 &&
                std::holds_alternative<World::ClientDiagnostic>((*mixed_diagnostic)[0]) &&
                std::holds_alternative<Movement::Request>((*mixed_diagnostic)[1]) &&
                std::holds_alternative<World::Tick>((*mixed_diagnostic)[2]) &&
                reconstruct(*mixed_diagnostic)==diagnostic_and_move,
                "Valid 9A diagnostic mixed with movement/tick changed");
            const auto gameplay_only=World::without_client_diagnostics(*mixed_diagnostic);
            require(gameplay_only.size()==2 &&
                std::holds_alternative<Movement::Request>(gameplay_only[0]) &&
                std::holds_alternative<World::Tick>(gameplay_only[1]),
                "Client diagnostic filtering changed gameplay record order");
            const Bytes diagnostic_only_bytes{0x9a,10,0,0,'t','e','s','t',0,0};
            const auto parsed_diagnostic=World::decode(diagnostic_only_bytes);
            require(parsed_diagnostic && World::without_client_diagnostics(*parsed_diagnostic).empty(),
                "Diagnostic-only world batch was not recognized");
            auto bad_diagnostic=diagnostic_only_bytes;bad_diagnostic[8]='x';reject(bad_diagnostic);
            const auto parsed_context=World::decode(context);
            const Bytes control1f{0x1f,0};
            const auto parsed_control=World::parse_frame(Frame::encode(control1f));
            require(parsed_control && parsed_control->size()==1 &&
                std::holds_alternative<World::ClientControl1F>(parsed_control->front()) &&
                reconstruct(*parsed_control)==control1f,"Observed 1F 00 control record changed");
            require(!World::decode(Bytes{0x1f}) && !World::decode(Bytes{0x1f,1}),
                "Malformed 1F control record accepted");
            const Bytes control6d{0x6d,0};
            const auto parsed_control6d=World::parse_frame(Frame::encode(control6d));
            require(parsed_control6d && parsed_control6d->size()==1 &&
                std::holds_alternative<World::ClientControl6D>(parsed_control6d->front()) &&
                reconstruct(*parsed_control6d)==control6d,"Native 6D 00 control record changed");
            require(!World::decode(Bytes{0x6d}) && !World::decode(Bytes{0x6d,1}),
                "Malformed 6D control record accepted");
            for(unsigned raw=0;raw<=255;++raw) {
                const Bytes opaque74{0x74,static_cast<std::uint8_t>(raw)};
                const auto parsed74=World::parse_frame(Frame::encode(opaque74));
                require(parsed74 && parsed74->size()==1 &&
                    std::get_if<World::ClientOpaque74>(&parsed74->front()) &&
                    std::get<World::ClientOpaque74>(parsed74->front()).payload==raw &&
                    reconstruct(*parsed74)==opaque74,
                    "Native74 opaque payload changed during world parsing");
            }
            require(!World::decode(Bytes{0x74}),"Truncated native74 accepted");
            for(const std::uint16_t raw:{std::uint16_t{0},std::uint16_t{0x1234},std::uint16_t{0xffff}}) {
                const Bytes panel88{0x88,static_cast<std::uint8_t>(raw),static_cast<std::uint8_t>(raw>>8)};
                const auto parsed88=World::parse_frame(Frame::encode(panel88));
                require(parsed88 && parsed88->size()==1 &&
                    std::get_if<World::ClientPanelOpen88>(&parsed88->front()) &&
                    reconstruct(*parsed88)==panel88,
                    "Native88 context bytes changed during world parsing");
            }
            require(!World::decode(Bytes{0x88}) && !World::decode(Bytes{0x88,0x34}),
                "Truncated native88 accepted");
            for(unsigned raw=0;raw<65536;++raw) {
                const Bytes options{0x1d,static_cast<std::uint8_t>(raw),static_cast<std::uint8_t>(raw>>8)};
                const auto parsed=World::decode(options);
                require(parsed && parsed->size()==1 &&
                    std::holds_alternative<World::ClientOptionsNotification>(parsed->front()) &&
                    reconstruct(*parsed)==options,"Native1D option bits changed");
            }
            require(!World::decode(Bytes{0x1d}) && !World::decode(Bytes{0x1d,0}),"Truncated1D accepted");
            require(!World::decode(Bytes{0x1d,0,0,0xff}),"Unsupported1D suffix accepted");
            const Bytes pose{0x66,0,0xf7,0xa5};
            const auto parsed_pose=World::parse_frame(Frame::encode(pose));
            require(parsed_pose && parsed_pose->size()==1 &&
                std::holds_alternative<World::ClientPoseNotification>(parsed_pose->front()) &&
                reconstruct(*parsed_pose)==pose,"Native66 payload or opaque tail changed");
            for(std::size_t size=1;size<4;++size)
                require(!World::decode(std::span(pose).first(size)),"Truncated66 accepted");
            auto pose_suffix=pose;pose_suffix.push_back(0xff);
            require(!World::decode(pose_suffix),"Unsupported suffix after66 accepted");
            auto control_with_tick=control1f;append(control_with_tick,Bytes{0x30,0});
            const auto parsed_control_batch=World::decode(control_with_tick);
            require(parsed_control_batch && parsed_control_batch->size()==2 &&
                reconstruct(*parsed_control_batch)==control_with_tick,
                "1F control batch grammar changed");
            require(parsed_context && std::holds_alternative<World::ContextNotification>(parsed_context->front()),"Context1C type");
            require(reconstruct(*parsed_context)==context,"Context1C payload changed");
            // The physical client's doorway handoff can put its first indoor
            // movement in the same logical frame as the context receipt.
            const Bytes context_and_move{0x1c,4,0,1,0,0x2e,17,0,18,0,1,0};
            const auto paired=World::decode(context_and_move);
            require(paired && paired->size()==2 &&
                std::holds_alternative<World::ContextNotification>((*paired)[0]) &&
                std::holds_alternative<Movement::Request>((*paired)[1]),
                "Context followed by destination movement changed");
            const auto& indoor_step=std::get<Movement::Request>((*paired)[1]);
            require(indoor_step.x==17 && indoor_step.y==18 && indoor_step.sequence==1 &&
                reconstruct(*paired)==context_and_move,"Destination step fields changed");
            std::optional<World::UnsupportedRecord> unsupported;
            const Bytes later_unknown{0x30,0,0xff};
            require(!World::decode(later_unknown,&unsupported) && unsupported &&
                unsupported->offset==2 && unsupported->opcode==0xff,
                "Unsupported record after a valid prefix was not located");
            const auto unknown_frame=Frame::encode(later_unknown);
            require(!World::parse_frame(unknown_frame,&unsupported) && unsupported &&
                unsupported->offset==2 && unsupported->opcode==0xff,
                "Framed unsupported record lost its logical offset");
            const Bytes malformed_known{0x30,1};
            require(!World::decode(malformed_known,&unsupported) && !unsupported,
                "Malformed known record misidentified as unsupported");
            auto bad_envelope=unknown_frame;bad_envelope.back()^=1;
            require(!World::parse_frame(bad_envelope,&unsupported) && !unsupported,
                "Corrupt envelope yielded an unsupported-record claim");
            for(std::size_t size=1;size<context.size();++size)
                require(!World::decode(std::span(context).first(size)),"Truncated context accepted");
            const auto notice=World::decode(timer);
            require(notice && notice->size()==1 &&
                std::holds_alternative<World::TimerNotification>(notice->front()),"Timer36 type");
            require(reconstruct(*notice)==timer,"Timer36 opaque payload preserved");
            for(std::size_t size=1;size<timer.size();++size)
                require(!World::decode(std::span(timer).first(size)),"Truncated Timer36 accepted");
            auto opaque=timer;opaque[8]=0xff;
            require(reconstruct(*World::decode(opaque))==opaque,"Timer36 parser invented field semantics");
            const Bytes client_diagnostic{0x9a,10,0,0,'t','e','s','t',0,0x7f};
            accept(client_diagnostic,1);
            auto malformed_diagnostic=client_diagnostic;
            malformed_diagnostic[1]=11;reject(malformed_diagnostic);
            malformed_diagnostic=client_diagnostic;
            malformed_diagnostic[8]='x';reject(malformed_diagnostic);
            malformed_diagnostic=client_diagnostic;
            malformed_diagnostic[3]=2;reject(malformed_diagnostic);
            for(const auto target:{0u,42u,65535u,65536u,0x12345678u,0x7fffffffu,0x80000000u,0xffffffffu}) {
                const auto record=Npc::encode({target});
                require(Npc::decode(record)->raw_target==target,"NPC target narrowed");
                const Bytes bytes(record.begin(),record.end());
                accept(bytes,1);
                for(std::size_t size=0;size<record.size();++size)
                    reject(Bytes(record.begin(),record.begin()+size));
                auto batch=fixtures[3];append(batch,record);accept(batch,2);
                for(std::size_t size=1;size<record.size();++size) {
                    auto partial=fixtures[3];append(partial,std::span(record).first(size));reject(partial);
                }
                batch.push_back(0xff);reject(batch);
                auto extra=bytes;extra.push_back(0);
                require(!Npc::decode(extra),"NPC trailing byte accepted as single record");
            }
            quest_contract();
            inventory_move_contract();
            allocation_and_daily_contract();
            role_text_and_pet_revert_contract();
            teleport_contract();
            close_contract();
            selection_item_contract();
            battle_contract();
            ordering_and_opaque_values();
            truncation_and_suffixes();
            maximum_bounds();
            frame_integrity_and_ownership();
            std::cout << "Recovered world records: all checks passed\n";
        }
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
