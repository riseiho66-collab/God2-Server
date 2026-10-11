#include "net/SessionManager.h"
#include "net/Session.h"

namespace god2 {
SessionManager::SessionManager(std::size_t capacity) : capacity_(capacity) {}
bool SessionManager::add(const std::shared_ptr<Session>& session) {
    if (!session || sessions_.size() >= capacity_) return false;
    return sessions_.emplace(session->id(), session).second;
}
void SessionManager::remove(std::uint64_t id) { sessions_.erase(id); }
void SessionManager::close_all() {
    for (const auto& [id, session] : sessions_) session->close();
}
std::size_t SessionManager::size() const noexcept { return sessions_.size(); }
} // namespace god2
