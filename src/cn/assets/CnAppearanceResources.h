#pragma once
#include "cn/assets/CnResourceBytes.h"
#include "cn/protocol/CnRemoteActor.h"
#include "cn/protocol/CnWorldEntry.h"
#include "cn/protocol/CnCharacterSummary.h"
#include <array>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <memory>
#include <optional>
#include <string>
#include <unordered_map>
#include <utility>
#include <variant>
#include <vector>

namespace god2cn {
struct CnHeroDollResourceRow {
    std::size_t source_line, native_row;
    std::string native_key, native_filename;
    std::uint8_t face_variant_base;
};
struct CnDriverResourceRow {
    std::size_t source_line, native_row;
    std::string declared_id_bytes, native_filename;
    std::uint16_t act_type_word, field3_word;
    std::array<std::uint16_t,4> fields4_to7;
};
struct CnAppearanceTableFile {
    CnSelectedResource selected;
    std::vector<std::uint8_t> decoded; // Original CP936 bytes, including comments.
};
class CnAppearanceResources;
//00443080's selection preview is a distinct consumer: ActType is literal0,
// no Drv/auxiliary/alternate-key operand is taken from07. Keep the full raw07
// and explicit local-row stage; never synthesize a2A/6F or driver0 actor.
class CnSelectionAppearanceRows {
public:
    enum class RowStage {ReceivedBeforePanel,AfterPanel};
    const auto& parts() const noexcept {return parts_;}
    const auto& part_resource_paths() const noexcept {return paths_;}
    const auto& source_summary() const noexcept {return source_;}
    unsigned source_row_ordinal() const noexcept {return row_;}
    RowStage row_stage() const noexcept {return stage_;}
    const auto& consumer_row_bytes() const noexcept {return consumer_row_;}
    const auto& profile() const noexcept {return profile_;}
    //00443313/00443325: selected takes each component's high3 bits;
    // unselected uses7. Caller supplies actual selection, not a server rule.
    std::array<std::uint8_t,4> palette_operands(bool selected) const noexcept {
        std::array<std::uint8_t,4> result;
        for(unsigned part=0;part<4;++part)
            result[part]=selected?static_cast<std::uint8_t>(consumer_row_[25+part*2]>>5):7;
        return result;
    }
private:
    friend class CnAppearanceResources;
    CnSelectionAppearanceRows(std::shared_ptr<const CnAppearanceResources>,
        std::array<CnHeroDollResourceRow,4>,std::array<std::filesystem::path,4>,
        CnCharacterSummary,unsigned,RowStage,std::array<std::uint8_t,36>);
    std::shared_ptr<const CnAppearanceResources> profile_;
    std::array<CnHeroDollResourceRow,4> parts_;
    std::array<std::filesystem::path,4> paths_;
    CnCharacterSummary source_;
    unsigned row_;
    RowStage stage_;
    std::array<std::uint8_t,36> consumer_row_;
};
// Selected table rows/path operands only. No cached ROM handle, ACT, palette,
// renderer operation, equipment ownership, observer policy or native success.
class CnAppearanceRowSelection {
public:
    using SourceRecord=std::variant<CnWorldEntry::BeginPlay,CnRemoteActor::Record>;
    const auto& parts() const noexcept {return parts_;}
    const auto& driver() const noexcept {return driver_;}
    const auto& part_resource_paths() const noexcept {return part_paths_;}
    const auto& driver_resource_path() const noexcept {return driver_path_;}
    std::uint8_t auxiliary_selector_raw() const noexcept {return auxiliary_;}
    bool auxiliary_resource_prepared() const noexcept {return false;}
    const auto& profile() const noexcept {return profile_;}
    const SourceRecord& source_record() const noexcept {return source_;}
private:
    friend class CnAppearanceResources;
    CnAppearanceRowSelection(std::shared_ptr<const CnAppearanceResources>,
        std::array<CnHeroDollResourceRow,4>,CnDriverResourceRow,
        std::array<std::filesystem::path,4>,std::optional<std::filesystem::path>,std::uint8_t,SourceRecord);
    std::shared_ptr<const CnAppearanceResources> profile_;
    std::array<CnHeroDollResourceRow,4> parts_;
    CnDriverResourceRow driver_;
    std::array<std::filesystem::path,4> part_paths_;
    std::optional<std::filesystem::path> driver_path_; // Empty native filename is retained, not a substitute resource.
    std::uint8_t auxiliary_;
    SourceRecord source_; // Exact full parsed2A/6F, not a new synthetic actor.
};
// CN582f2695:00488F70/00423960,004885B0 ->00482C90/004237F0.
// Immutable actual selected files; repeated keys use the last native row.
// Caller must still bind this profile/revision to the actual connection/world.
class CnAppearanceResources final : public std::enable_shared_from_this<CnAppearanceResources> {
public:
    static std::shared_ptr<const CnAppearanceResources> read(const std::filesystem::path& cn_root,
        std::size_t max_encoded_bytes,std::size_t max_plain_bytes);
    const auto& source_files() const noexcept {return files_;}
    const auto& hero_rows() const noexcept {return hero_;}
    const auto& driver_rows() const noexcept {return drivers_;}
    // Nonzero alternate-key inputs are excluded here (nullopt); validity and
    // native alternate/fallback branches remain open, never inferred here.
    // Missing rows/out-of-qualified-table/ActType>=3 are explicit errors;
    // they do not manufacture native missing-resource/default0 success.
    std::optional<CnAppearanceRowSelection> select_normal_initial(const CnWorldEntry::BeginPlay&) const;
    std::optional<CnAppearanceRowSelection> select_ordinary_remote(const CnRemoteActor::Record&) const;
    // Only an active row in an actual complete07. Invalid ordinal is absent;
    // missing HeroDoll row/path is an explicit qualification error. This
    // selects immutable inputs, not cache handles/ROM banks/ACT or rendering.
    std::optional<CnSelectionAppearanceRows> select_native_summary(const CnCharacterSummary&,
        unsigned row,CnSelectionAppearanceRows::RowStage) const;
private:
    explicit CnAppearanceResources(std::filesystem::path root):root_(std::move(root)){}
    CnAppearanceRowSelection select(std::uint8_t driver,std::uint8_t auxiliary,
        const std::array<std::uint8_t,8>&,CnAppearanceRowSelection::SourceRecord) const;
    const CnHeroDollResourceRow& lookup(std::uint8_t category,unsigned slot,
        std::uint8_t family,std::uint8_t variant,std::uint8_t act) const;
    std::filesystem::path root_;
    std::array<CnAppearanceTableFile,2> files_;
    std::vector<CnHeroDollResourceRow> hero_;
    std::vector<CnDriverResourceRow> drivers_;
    std::unordered_map<std::string,std::size_t> key_rows_;
};
}
