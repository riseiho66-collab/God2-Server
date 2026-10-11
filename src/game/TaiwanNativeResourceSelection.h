#pragma once
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <memory>
#include <optional>
#include <vector>

namespace god2 {
// TW00429820 binary /00402530 text original-file selection. This is not a
// resource lifecycle issuer, ROM decoder, native FILE*, or gameplay authority.
class TaiwanNativeResourceSelection final {
public:
    enum class Kind { RomBinary, TextFile };
    struct Request {
        Kind kind;
        std::vector<std::uint8_t> original_reference;
        // Actual model object+1C prefix for ROMFILE, or the actual text caller
        // prefix. Native concatenates bytes without inserting a separator.
        std::vector<std::uint8_t> native_prefix;
        // Explicit current-directory context for relative native ANSI names.
        // Never taken implicitly from the process's current directory.
        std::filesystem::path actual_working_directory;
        std::uint32_t full_bank_operand;
    };
    enum class Probe { OpenFailed, Non0516, Marker0516 };
    enum class Branch { Candidate0516, OriginalAfterOpenFailed, OriginalAfterNon0516 };
    // ASCII filename domain only: preserve all request bytes, reject unproved
    // CP950->filesystem mappings, embedded NULs and native local-buffer excess.
    // max_encoded_bytes is a source allocation bound, never a native fallback.
    static std::optional<TaiwanNativeResourceSelection> select(
        const Request&,std::size_t max_encoded_bytes);
    const Request& request() const;
    const std::vector<std::uint8_t>& request_bytes() const;
    const std::vector<std::uint8_t>& candidate_bytes() const;
    const std::filesystem::path& candidate_source() const;
    const std::filesystem::path& actual_source() const;
    const std::vector<std::uint8_t>& encoded_bytes() const;
    // Full opened candidate original, including a rejected non0516 candidate.
    // OpenFailed has no original candidate bytes; no fake empty success asset.
    const std::optional<std::vector<std::uint8_t>>& candidate_original() const;
    Probe probe() const;
    Branch branch() const;
private:
    struct Storage;
    explicit TaiwanNativeResourceSelection(std::shared_ptr<const Storage>);
    const Storage& storage() const;
    std::shared_ptr<const Storage> storage_;
};
}
