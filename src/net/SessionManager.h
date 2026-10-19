#pragma once

#include <cstddef>
#include <cstdint>
#include <memory>
#include <unordered_map>

namespace god2 {
class Session;

// All operations belong to the TcpServer acceptor strand.
class SessionManager {
public:
    explicit SessionManager(std::size_t capacity);
    bool add(const std::shared_ptr<Session>& session);
    // Completion may remove only this exact accepted incarnation.
    bool remove(const std::shared_ptr<Session>& session);
    void close_all();
    std::size_t size() const noexcept;
private:
    std::size_t capacity_;
    std::unordered_map<std::uint64_t, std::shared_ptr<Session>> sessions_;
};
} // namespace god2
