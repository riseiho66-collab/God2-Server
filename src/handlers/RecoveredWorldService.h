#pragma once
#include "net/Session.h"
#include <functional>

namespace god2 {

// CUSTOM-0004: policy routing, not an original gameplay or turn rule.
// Callbacks own authorization and all-or-nothing domain transactions.
class RecoveredWorldService {
public:
    using Movement = decltype(Session::RecoveredCharacterHandlers::movement);
    using Battle = decltype(Session::RecoveredCharacterHandlers::world_records);
    using Supply = std::function<std::optional<std::vector<std::uint8_t>>(
        Session&, const RecoveredTargetItemRequest::Request&)>;
    using QuestRequest = std::variant<RecoveredQuestAction::Request,RecoveredQuestClose::Request,
                                     RecoveredDailyQuestRequest::Request>;
    using Quest = std::function<std::optional<std::vector<std::uint8_t>>(Session&,const QuestRequest&)>;
    using SelectionItem = std::function<std::optional<std::vector<std::uint8_t>>(
        Session&, const RecoveredSelectionItemRequest::Request&)>;
    using Teleport = std::function<std::optional<std::vector<std::uint8_t>>(
        Session&, const RecoveredTeleport::Selection&)>;
    using InventoryMove = std::function<std::optional<std::vector<std::uint8_t>>(
        Session&, const RecoveredInventoryMoveRequest::Request&)>;
    using DeitySelection = std::function<std::optional<std::vector<std::uint8_t>>(
        Session&, const RecoveredDeitySelection::Request&)>;
    explicit RecoveredWorldService(Movement movement, Battle battle = {}, Supply supply = {},
                                   Quest quest = {}, SelectionItem selection_item = {}, Teleport teleport = {},
                                   InventoryMove inventory_move = {}, DeitySelection deity_selection = {});
    std::optional<std::vector<std::uint8_t>> handle(
        Session& session, std::span<const RecoveredWorldRecords::Record> records) const;
private:
    Movement movement_;
    Battle battle_;
    Supply supply_;
    Quest quest_;
    SelectionItem selection_item_;
    Teleport teleport_;
    InventoryMove inventory_move_;
    DeitySelection deity_selection_;
};
}
