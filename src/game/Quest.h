#pragma once
#include <cstdint>
namespace god2 {
enum class QuestState { Available, Accepted, Completed };
// Placeholder only; no quest database schema is implied.
struct Quest {
    std::uint32_t id = 0;
    QuestState state = QuestState::Available;
};
}
