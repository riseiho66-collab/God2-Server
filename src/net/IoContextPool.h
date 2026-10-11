#pragma once

#include <asio.hpp>
#include <cstddef>
#include <optional>
#include <thread>
#include <vector>

namespace god2 {
// Lifecycle methods are called by the owner, never by a worker thread.
class IoContextPool {
public:
    IoContextPool();
    ~IoContextPool();
    IoContextPool(const IoContextPool&) = delete;
    IoContextPool& operator=(const IoContextPool&) = delete;
    asio::io_context& context() noexcept;
    void start(std::size_t workers);
    // Release the work guard; outstanding asynchronous work drains normally.
    // Close servers/sessions before calling stop(), then join().
    void stop();
    void join();
private:
    asio::io_context context_;
    std::optional<asio::executor_work_guard<asio::io_context::executor_type>> work_;
    std::vector<std::thread> workers_;
};
} // namespace god2
