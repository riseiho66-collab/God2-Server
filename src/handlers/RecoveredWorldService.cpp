#include "handlers/RecoveredWorldService.h"
#include "protocol/RecoveredCharacterPose.h"
#include <utility>

namespace god2 {
RecoveredWorldService::RecoveredWorldService(Movement movement, Battle battle, Supply supply,
                                             Quest quest, SelectionItem selection_item, Teleport teleport,
                                             InventoryMove inventory_move, DeitySelection deity_selection,
                                             CausalDeitySelection causal_deity_selection)
    : movement_(std::move(movement)), battle_(std::move(battle)), supply_(std::move(supply)),
      quest_(std::move(quest)), selection_item_(std::move(selection_item)),
      teleport_(std::move(teleport)), inventory_move_(std::move(inventory_move)),
      deity_selection_(std::move(deity_selection)),causal_deity_selection_(std::move(causal_deity_selection)) {}

std::optional<std::vector<std::uint8_t>> RecoveredWorldService::handle(
        Session& session, std::span<const RecoveredWorldRecords::Record> records) const {
    auto reply=handle_impl(session,records,false);
    if(!reply)return {};
    return std::move(*reply).take_plain_wire();
}
std::optional<LegacyWorldReply> RecoveredWorldService::handle_reply(
        Session& session,std::span<const RecoveredWorldRecords::Record> records)const {
    return handle_impl(session,records,true);
}
std::optional<LegacyWorldReply> RecoveredWorldService::handle_impl(
        Session& session,std::span<const RecoveredWorldRecords::Record> records,bool causal_allowed)const {
    if (!session.account_id || !session.character_id || records.empty() || records.size() > 8192 ||
        (session.state() != SessionState::CharacterSelected &&
         session.state() != SessionState::InWorld && session.state() != SessionState::InBattle))
        return std::nullopt;
    // CUSTOM-0004: standalone native dialogue request only. The bound service
    // must authorize its conversation/owner and commit all gameplay atomically.
    if(records.size()==1 && session.state()==SessionState::InWorld && quest_) {
        if(const auto* action=std::get_if<RecoveredQuestAction::Request>(&records.front()))
            return quest_(session,QuestRequest{*action});
        if(const auto* close=std::get_if<RecoveredQuestClose::Request>(&records.front()))
            return quest_(session,QuestRequest{*close});
        if(const auto* daily=std::get_if<RecoveredDailyQuestRequest::Request>(&records.front()))
            return quest_(session,QuestRequest{*daily});
    }
    if(records.size()==1 &&
       std::holds_alternative<RecoveredWorldRecords::ClientDiagnostic>(records.front()))
        return std::vector<std::uint8_t>{};
    // CUSTOM-0103: actual battle C66 has symbol semantics distinct from world
    // modes1..3. The installed battle owner must authorize its exact binding;
    // no policy/default means the original battle rejection remains intact.
    if(records.size()==1 && session.state()==SessionState::InBattle &&
       std::holds_alternative<RecoveredWorldRecords::ClientPoseNotification>(records.front()))
        return battle_ ? battle_(session,records) : std::nullopt;
    // The current client emits standalone 1F 00 after a world session as well
    // as during initialization. No post-world reply or state change is proven.
    // Accept only the exact control record and let normal socket lifecycle
    // perform disconnect cleanup; never merge it with a gameplay operation.
    if(records.size()==1 && session.state()!=SessionState::InBattle &&
       std::holds_alternative<RecoveredWorldRecords::ClientControl1F>(records.front()))
        return std::vector<std::uint8_t>{};
    // 6D is also called from inventory/equipment update paths. Its meaning is
    // unresolved: retain authenticated standalone no-reply behavior and do not
    // reinterpret it as a dedicated teleport-menu request.
    if(records.size()==1 &&
       (session.state()==SessionState::InWorld ||
        (session.state()==SessionState::CharacterSelected && session.recovered_world_ready()))) {
        if(const auto* pose=std::get_if<RecoveredWorldRecords::ClientPoseNotification>(&records.front())) {
            // Only503820-owned pose modes are qualified. General pose updates
            // remain opaque and receive no invented animation/state response.
            if(RecoveredCharacterPose::is_qualified_pose(pose->payload)) {
                // Native sessions remain CharacterSelected after the exact
                // world-ready tail; this is their established world lease.
                // The enclosing gate rejects unready selection and battle.
                return RecoveredCharacterPose::synchronize(session.character_id,pose->payload);
            }
            return std::vector<std::uint8_t>{};
        }
        if(std::holds_alternative<RecoveredWorldRecords::ClientControl6D>(records.front()))
            return std::vector<std::uint8_t>{};
        // C2S74 is a native UI-mode notification with an unwritten payload
        // byte. Admit only a standalone ready-world record; it cannot mutate
        // gameplay or imply a fabricated response.
        if(std::holds_alternative<RecoveredWorldRecords::ClientOpaque74>(records.front()))
            return std::vector<std::uint8_t>{};
        // C2S88 precedes a local panel display and carries an actor/context
        // WORD. Keep the exact bytes at transport level; no original server
        // operation or reply has been established for this standalone notice.
        if(std::holds_alternative<RecoveredWorldRecords::ClientPanelOpen88>(records.front()))
            return std::vector<std::uint8_t>{};
        // CUSTOM-0060: ready-world transport admission for the local options
        // notification. No server-owned action/reply is qualified; never echo
        // an unrelated S2C1D or change chat filters/saves on this evidence.
        if(std::holds_alternative<RecoveredWorldRecords::ClientOptionsNotification>(records.front()))
            return std::vector<std::uint8_t>{};
        // CUSTOM-0004: standalone selection only. Authority callback owns its
        // menu/selection validation and transaction; absence rejects selection.
        if(const auto* selection=std::get_if<RecoveredTeleport::Selection>(&records.front()))
            return teleport_ ? teleport_(session,*selection) : std::nullopt;
    }
    // CUSTOM-0037: one inventory transaction may share a TCP batch with native
    // idle ticks. Reject additional mutations before any callback can commit.
    const RecoveredInventoryMoveRequest::Request* inventory_move=nullptr;
    bool only_inventory_and_ticks=true;
    for(const auto& record:records) {
        if(const auto* request=std::get_if<RecoveredInventoryMoveRequest::Request>(&record)) {
            if(inventory_move) return std::nullopt;
            inventory_move=request;
        } else if(!std::holds_alternative<RecoveredWorldRecords::Tick>(record)) {
            only_inventory_and_ticks=false;
        }
    }
    if(inventory_move) {
        if(!only_inventory_and_ticks || !inventory_move_ || session.state()==SessionState::InBattle ||
           !session.recovered_world_ready()) return std::nullopt;
        return inventory_move_(session,*inventory_move);
    }
    // CUSTOM-0039: one owned companion transaction, with only native idle
    // ticks and (for28) its observed trailing1F00. Reject mixed mutations
    // before invoking any authoritative callback.
    const RecoveredDeitySelection::Request* deity=nullptr;
    const RecoveredSelectionItemRequest::Request* pet=nullptr;
    for(const auto& record:records) {
        if(const auto* request=std::get_if<RecoveredDeitySelection::Request>(&record)) {
            if(deity || pet) return std::nullopt;
            deity=request;
        }
        if(const auto* request=std::get_if<RecoveredSelectionItemRequest::Request>(&record);
           request && request->raw_slot>=42 && request->raw_slot<=44) {
            if(pet || deity) return std::nullopt;
            pet=request;
        }
    }
    if(deity || pet) {
        if(session.state()==SessionState::InBattle || !session.recovered_world_ready()) return std::nullopt;
        unsigned controls=0;bool pet_seen=false;
        for(const auto& record:records) {
            if(std::holds_alternative<RecoveredWorldRecords::Tick>(record)) continue;
            if(deity && std::holds_alternative<RecoveredDeitySelection::Request>(record)) continue;
            if(pet && std::get_if<RecoveredSelectionItemRequest::Request>(&record)==pet) {pet_seen=true;continue;}
            if(pet && pet_seen && std::holds_alternative<RecoveredWorldRecords::ClientControl1F>(record) && ++controls<=1) continue;
            return std::nullopt;
        }
        if(deity) {
            if(causal_deity_selection_) {
                // Reject the raw gateway BEFORE the actual producer can commit
                // SQL. A post-commit tag-loss refusal would be too late.
                if(!causal_allowed)return std::nullopt;
                return causal_deity_selection_(session,*deity);
            }
            return deity_selection_?deity_selection_(session,*deity):std::nullopt;
        }
        return selection_item_?selection_item_(session,*pet):std::nullopt;
    }
    std::vector<RecoveredMovement::Request> moves;
    bool combat = false;
    const RecoveredTargetItemRequest::Request* supply = nullptr;
    const RecoveredSelectionItemRequest::Request* selection_item = nullptr;
    std::optional<RecoveredSkillCommand::Record> sequence;
    std::size_t sequence_size = 0;
    for (const auto& record : records) {
        if (const auto* skill = std::get_if<RecoveredSkillCommand::Record>(&record)) {
            combat = true;
            if (!sequence) sequence = *skill;
            if (!RecoveredSkillCommand::same_sequence(*sequence, *skill) ||
                ++sequence_size > RecoveredSkillCommand::max_sequence_records)
                return std::nullopt;
            if (!skill->continuation) { sequence.reset(); sequence_size = 0; }
            continue;
        }
        if (sequence) return std::nullopt;
        if (const auto* item = std::get_if<RecoveredTargetItemRequest::Request>(&record)) {
            if (supply || selection_item) return std::nullopt;
            supply = item;
            continue;
        }
        if (const auto* item = std::get_if<RecoveredSelectionItemRequest::Request>(&record)) {
            if (supply || selection_item) return std::nullopt;
            selection_item = item;
            continue;
        }
        if (const auto* move = std::get_if<RecoveredMovement::Request>(&record))
            moves.push_back(*move);
        else if (std::holds_alternative<RecoveredBattleCommand::BasicAttackRequest>(record) ||
                 std::holds_alternative<RecoveredBattleCommand::ControlRequest>(record) ||
                 std::holds_alternative<RecoveredBattleCommand::Action2Request>(record))
            combat = true;
        else if (!std::holds_alternative<RecoveredWorldRecords::Tick>(record))
            return std::nullopt;
    }
    if (sequence || (combat && !moves.empty())) return std::nullopt;
    if (supply || selection_item) {
        if (combat || !moves.empty() || session.state() == SessionState::InBattle)
            return std::nullopt;
        // Callbacks must validate completed world entry, ownership, inventory,
        // and the response contract. Grammar alone never enables use.
        if (supply) return supply_ ? supply_(session, *supply) : std::nullopt;
        return selection_item_ ? selection_item_(session, *selection_item) : std::nullopt;
    }
    if (combat) {
        if (session.state() != SessionState::InBattle || !battle_) return std::nullopt;
        return battle_(session, records);
    }
    if (moves.empty()) return std::vector<std::uint8_t>{};
    // Native bootstrap retains CharacterSelected; Session gates the completed
    // tail and the movement service validates its own world-ready binding.
    if (session.state() == SessionState::InBattle || !movement_) return std::nullopt;
    if(session.owned_normal_movement_response_custody_enabled()) {
        // CUSTOM-0095 bind this exact original2E+Tick input and original ACK run.
        const auto sender_run=session.movement_response_input_run(records);
        auto reply=movement_(session,moves);
        if(reply.empty() || !session.locate_movement_response_run(0,reply))return std::nullopt;
        return reply; // One joint batch, no synthetic per-request persisted versions.
    }
    auto reply = movement_(session, moves);
    if (reply.empty()) return std::nullopt;
    return reply;
}
}
