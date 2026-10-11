#pragma once
#include "protocol/RecoveredWorldRecords.h"
#include "handlers/OwnedGuildPanelService.h"
#include <algorithm>
namespace god2 {
// CUSTOM-0078: complete-batch qualification precedes all recursive dispatch.
// A notification never grants write authority; help cannot lend authority to79
// in the same batch. Existing guild/chat routing predicates remain unchanged.
struct OwnedGuildAnnouncementBatch {
    using World=RecoveredWorldRecords;
    static bool notification(const World::Record& record) {
        return std::holds_alternative<World::Tick>(record) ||
            std::holds_alternative<World::ClientOpaque74>(record) ||
            std::holds_alternative<World::ClientControl1F>(record) ||
            std::holds_alternative<World::ClientControl6D>(record) ||
            std::holds_alternative<World::ClientOptionsNotification>(record) ||
            std::holds_alternative<World::ContextNotification>(record) ||
            std::holds_alternative<World::TimerNotification>(record) ||
            std::holds_alternative<World::ClientDiagnostic>(record) ||
            std::holds_alternative<RecoveredGuildRoster::PanelReady>(record);
    }
    static bool save_only(std::span<const World::Record> records) {
        return std::all_of(records.begin(),records.end(),[](const auto& record) {
            return notification(record) || std::holds_alternative<RecoveredGuildAnnouncement::Request>(record);
        });
    }
    static bool opener_only(std::span<const World::Record> records) {
        return std::all_of(records.begin(),records.end(),[](const auto& record) {
            if(const auto* help=std::get_if<RecoveredNpcInteraction::Request>(&record))
                return OwnedGuildPanelService::custom_help_entry(*help);
            return notification(record);
        });
    }
};
}
