#pragma once
#include <cstddef>
#include <cstdint>
#include <span>
#include <vector>

namespace god2 {
class Buffer {
public:
    void append(std::span<const uint8_t> bytes);
    [[nodiscard]] size_t size() const noexcept { return storage_.size() - offset_; }
    [[nodiscard]] std::span<const uint8_t> data() const noexcept {
        return std::span<const uint8_t>(storage_).subspan(offset_);
    }
    void consume(size_t count);
private:
    std::vector<uint8_t> storage_;
    size_t offset_ = 0;
};
}
