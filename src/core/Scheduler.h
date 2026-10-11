#pragma once
#include <asio.hpp>
#include <chrono>
#include <functional>
#include <memory>
namespace god2 {
class Scheduler : public std::enable_shared_from_this<Scheduler> {
public:
    Scheduler(asio::any_io_executor executor, std::chrono::milliseconds interval, std::function<void()> tick);
    void start();
    void stop();
private:
    asio::steady_timer timer_;
    std::chrono::milliseconds interval_;
    std::function<void()> tick_;
    bool stopped_=false;
};
}
