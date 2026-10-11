#include "net/IoContextPool.h"
#include <stdexcept>

namespace god2 {
IoContextPool::IoContextPool() : work_(asio::make_work_guard(context_)) {}
IoContextPool::~IoContextPool() {
    stop();
    context_.stop();
    join();
}
asio::io_context& IoContextPool::context() noexcept { return context_; }
void IoContextPool::start(std::size_t workers) {
    if (workers == 0) throw std::invalid_argument("network worker count must be positive");
    if (!workers_.empty()) throw std::logic_error("IoContextPool already started");
    context_.restart();
    if (!work_) work_.emplace(asio::make_work_guard(context_));
    try {
        for (std::size_t i = 0; i < workers; ++i)
            workers_.emplace_back([this] { context_.run(); });
    } catch (...) {
        context_.stop();
        join();
        throw;
    }
}
void IoContextPool::stop() { work_.reset(); }
void IoContextPool::join() {
    for (auto& worker : workers_) if (worker.joinable()) worker.join();
    workers_.clear();
}
} // namespace god2
