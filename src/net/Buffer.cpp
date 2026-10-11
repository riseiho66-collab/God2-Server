#include "net/Buffer.h"
#include <stdexcept>

namespace god2 {
void Buffer::append(std::span<const uint8_t> bytes) {
    if (bytes.empty()) return;
    // Snapshot first: callers may append a view of this buffer itself.
    std::vector<uint8_t> copy(bytes.begin(), bytes.end());
    if (offset_ != 0 && offset_ >= storage_.size() / 2) {
        storage_.erase(storage_.begin(), storage_.begin() + static_cast<std::ptrdiff_t>(offset_));
        offset_ = 0;
    }
    storage_.insert(storage_.end(), copy.begin(), copy.end());
}
void Buffer::consume(size_t count) {
    if (count > size()) throw std::runtime_error("Buffer consume exceeds available bytes");
    offset_ += count;
    if (offset_ == storage_.size()) {
        storage_.clear();
        offset_ = 0;
    }
}
}
