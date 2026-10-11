#pragma once
#include <cstddef>
#include <cstdint>
#include <functional>
#include <memory>
#include <optional>
#include <span>
#include <string>
#include <thread>
#include <vector>

namespace god2cn {
// Actual pinned resource text, not a runtime GUI pointer table or gameplay
// authority. Keep CP936 bytes at this asset boundary; presentation conversion
// and native GUI readiness remain separate from the resource's identity.
class CnProgramMessageCatalog final {
public:
    static constexpr char client_sha256[]=
        "582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8";
    static constexpr char encoded_sha256[]=
        "9c027fdd114073fe9fc88776f7713c0e60575fbe1a2f15059e9bda01a9ec181e";
    static constexpr char decoded_sha256[]=
        "994088ac79051df74b3569fc102ab39849594409964a674796bd67fd9d4bc054";
    static constexpr char resource_path[]="Data2/Patch/Comm/message.csvZ";
    static constexpr std::size_t record_count=1116;
    struct Source {
        std::uint64_t actual_revision;
        std::string actual_client_sha256;
        bool operator==(const Source&) const=default;
    };
    using Current=std::function<bool(const Source&)>;
    struct Record {
        Source source;
        std::uint16_t native_csv_id,native_zero_based_pointer_index;
        std::uint32_t source_line,decoded_offset;
        std::string record_sha256;
        std::vector<std::uint8_t> raw_line; // Actual ID, all columns and CRLF.
        std::string native_column1_cp936; // Missing/empty column is native empty text.
    };
    // Caller supplies an actual revision/current predicate and both immutable
    // pinned inputs. No native decoder/resource loader/process memory required.
    static std::shared_ptr<const CnProgramMessageCatalog> read_actual_source(
        Source,std::span<const std::uint8_t> encoded,std::span<const std::uint8_t> decoded,Current);
    bool current() const;
    // Explicit ID/index APIs prevent confusing CSV ID165 with pointer index164.
    std::optional<Record> lookup_id(std::uint16_t native_csv_id) const;
    std::optional<Record> lookup_zero_based_index(std::size_t native_pointer_index) const;
private:
    CnProgramMessageCatalog(Source,std::vector<Record>,Current);
    void owner() const;
    Source source_;
    std::vector<Record> records_;
    Current current_;
    std::thread::id thread_=std::this_thread::get_id();
};
}
