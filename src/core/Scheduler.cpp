#include "core/Scheduler.h"
#include <spdlog/spdlog.h>
namespace god2 {
Scheduler::Scheduler(asio::any_io_executor e, std::chrono::milliseconds i, std::function<void()> t):timer_(e),interval_(i),tick_(std::move(t)){}
void Scheduler::start() {
    if(stopped_) return;
    timer_.expires_after(interval_);
    timer_.async_wait([self=shared_from_this()](const asio::error_code& ec) {
        if(ec || self->stopped_) return;
        try { self->tick_(); } catch(const std::exception& e) { spdlog::error("Scheduler: {}",e.what()); }
        self->start();
    });
}
void Scheduler::stop() { stopped_=true; timer_.cancel(); }
}
