#pragma once
#include <array>
#include <cstdint>
#include <functional>
#include <memory>
#include <optional>
#include <span>
#include <string>
#include <vector>

namespace god2cn {
// Pinned CN 00543560 -> component+149DF8 ->00561BB0 -> cbspec2.bin.
// Definition bytes/identities only: no learned skills, costs or cast authority.
class CnNativeSkillCatalog final {
public:
    static constexpr char dataset_id[]="cn-native-cbspec2-582f2695-857b52e3-v1";
    static constexpr char client_sha256[]="582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8";
    static constexpr char resource_sha256[]="857b52e36ceb4d08f61a373f2882593dada84ecbb8150da187f8c5553389a004";
    static constexpr char resource_path[]="data2/fight/spg/cbspec2.bin";
    static constexpr std::size_t resource_bytes=112660,record_bytes=110,group_bytes=0x6e04;
    inline static constexpr std::array<std::uint32_t,4> declared_counts={125,130,87,111};
    struct Source {
        std::uint64_t actual_revision;
        std::string actual_client_sha256;
        bool operator==(const Source&) const=default;
    };
    using Current=std::function<bool(const Source&)>; // Actual immutable resource owner, readonly.
    struct Record {
        Source source;
        std::uint8_t kind,definition_id;
        std::uint32_t file_offset;
        std::array<std::uint8_t,record_bytes> raw;
        std::string record_sha256;
        bool operator==(const Record&) const=default;
    };
    // Own supplied plain-file bytes. Computes their SHA256, checks the pinned
    // header/counts/identities, observes actual Current before and after copying.
    // This source implementation uses existing Windows bcrypt linkage. No DB,
    // client memory, resource fallback, MP threshold or native pointer required.
    static std::shared_ptr<const CnNativeSkillCatalog> read_actual_source(
        Source,std::span<const std::uint8_t>,Current);
    bool current() const;
    const Source& source() const noexcept {return source_;}
    // Retained original file payload after four-byte header. Readonly source
    // comparison only, not Current, learned rights or a native memory address.
    std::span<const std::uint8_t> retained_payload_bytes() const noexcept {return {bytes_.data()+4,bytes_.size()-4};}
    std::optional<Record> lookup(std::uint8_t kind,std::uint8_t definition_id) const;
    // Native WORD low byte ID, high byte kind; preserve order and duplicates.
    // Common mapping/eligibility must be decided by the actual gameplay owner.
    std::optional<std::vector<Record>> lookup_words(std::span<const std::uint16_t>) const;
private:
    CnNativeSkillCatalog(Source,std::vector<std::uint8_t>,Current);
    std::optional<Record> retained_lookup(std::uint8_t,std::uint8_t) const;
    Source source_;
    std::vector<std::uint8_t> bytes_;
    Current current_;
};
}
