#pragma once
#include <array>
#include <cstdint>
#include <filesystem>
#include <memory>
#include <optional>
#include <span>
#include <string_view>
#include <vector>

namespace god2 {
// Complete CAN v1.0 original. A tag is retained data, not an entry-kind policy.
class TaiwanNativeCanAsset final {
public:
    static constexpr std::size_t max_files=256,max_scenes=256,record_size=64;
    static constexpr std::size_t max_bytes=16+max_files*record_size+max_scenes*2;
    struct File {
        std::size_t ordinal,source_offset;
        std::array<std::uint8_t,record_size> raw;
        std::uint8_t tag;
        std::vector<std::uint8_t> reference;
    };
    static std::optional<TaiwanNativeCanAsset> from_bytes(
        std::filesystem::path,std::span<const std::uint8_t>,std::string_view expected_sha256);
    static std::optional<TaiwanNativeCanAsset> load_file(
        const std::filesystem::path&,std::string_view expected_sha256);
    // Same native Windows SHA provider as existing catalog digest qualification.
    // Unavailable provider rejects; it never means unchecked success.
    static bool matches_sha256(std::span<const std::uint8_t>,std::string_view);
    const std::filesystem::path& source()const;
    const std::vector<std::uint8_t>& bytes()const;
    const std::vector<File>& files()const;
    const std::vector<std::uint16_t>& scene_indices()const;
    const File* scene(std::size_t)const;
private:
    struct Storage;
    explicit TaiwanNativeCanAsset(std::shared_ptr<const Storage>);
    const Storage& storage()const;
    std::shared_ptr<const Storage> storage_;
};
}
