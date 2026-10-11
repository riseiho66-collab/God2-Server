#include "net/ConnectionIdentity.h"
#include <atomic>
#include <limits>
#include <stdexcept>

namespace god2 {
std::uint64_t next_connection_identity() {
    static std::atomic<std::uint64_t> next{1};
    auto current=next.load(std::memory_order_relaxed);
    for(;;) {
        if(current==std::numeric_limits<std::uint64_t>::max())
            throw std::overflow_error("Connection identity exhausted");
        if(next.compare_exchange_weak(current,current+1,std::memory_order_relaxed))return current;
    }
}
}
