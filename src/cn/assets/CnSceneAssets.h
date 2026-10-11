#pragma once
#include "cn/protocol/CnWorldEntry.h"
#include "cn/world/CnMapPassability.h"
#include "cn/assets/CnOutdoorTerrain.h"
#include "cn/assets/CnOutdoorSceneResources.h"
#include "cn/assets/CnAppearanceResources.h"
#include "cn/assets/CnAppearanceRomInputs.h"
#include <filesystem>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace god2cn {
class CnOutdoorWindow;
// Actual flag0 resource load, with explicit null slots after known open failure;
// not actor/world ownership or permission. Null cells need the actual prior grid.
// Private construction keeps unknown slots and forged resources out of consumers.
class CnPreparedStandaloneOutdoorScene {
public:
    const CnMapPassability& grid() const noexcept {return grid_;}
    CnOutdoorTerrain::ChunkCoordinate center() const noexcept {return center_;}
    const auto& resources() const noexcept {return resources_;}
    const auto& chunks() const noexcept {return chunks_;}
    const auto& source_files() const noexcept {return source_files_;}
    const auto& chunk_source_files() const noexcept {return chunk_sources_;}
    const auto& native_map_reference() const noexcept {return reference_;}
private:
    friend class CnSceneAssets;
    friend class CnOutdoorWindow;
    CnPreparedStandaloneOutdoorScene(std::string,std::vector<std::filesystem::path>,std::array<std::filesystem::path,9>,
        CnOutdoorTerrain::ChunkCoordinate,std::array<std::optional<CnStandaloneMapAsset>,9>,
        CnMapPassability,std::shared_ptr<const CnOutdoorSceneResources>);
    std::string reference_;
    // Profile paths first, then exactly nine slot-ordered chunk paths. Reused
    // chunk paths remain historical provenance; their bytes are never reread.
    std::vector<std::filesystem::path> source_files_;
    std::array<std::filesystem::path,9> chunk_sources_;
    CnOutdoorTerrain::ChunkCoordinate center_;
    std::array<std::optional<CnStandaloneMapAsset>,9> chunks_;
    CnMapPassability grid_;
    std::shared_ptr<const CnOutdoorSceneResources> resources_;
};
struct CnSceneCatalogRow {
    std::uint8_t family, declared_mode;
    std::uint16_t area_index;
    std::string_view native_mdt_path;
};
struct CnSceneState {
    std::uint8_t family;
    std::uint16_t area_index;
    std::uint8_t mode;
};
struct CnPreparedHouseScene {
    CnSceneState destination;
    std::uint8_t can_raw_kind;
    std::string native_file_reference;
    // Actual CAN and selected plain/wrapped HMD, not guessed catalog paths.
    std::vector<std::filesystem::path> source_files;
    CnMapPassability initial_grid;
};
struct CnPreparedOutdoorScene {
    CnSceneState destination;
    std::uint8_t can_raw_kind;
    std::string native_file_reference;
    // Actual selected files, including ROMs, for later profile/revision binding.
    std::vector<std::filesystem::path> source_files;
    CnOutdoorTerrain::InitialWorldPlacement placement;
    // Own decoded inputs for qualified later reloads; selected paths alone
    // cannot reconstruct the exact already loaded profile after files change.
    std::shared_ptr<const CnOutdoorSceneResources> resources;
};
class CnSceneAssets {
public:
    // A CN client root supplied by the CN application owner. No TW fallback.
    explicit CnSceneAssets(std::filesystem::path cn_client_root);
    // Real full2A/6F -> actual selected HeroDoll/Drv files -> native row keys.
    // Separate from scene geometry/admission; no resource handle or success.
    // Nonzero alternate key returns nullopt; validity/fallback and auxiliary/
    // ROM/ACT remain open. A row selection does not qualify runtime resources.
    std::optional<CnAppearanceRowSelection> prepare_normal_initial_appearance(
        const CnWorldEntry::BeginPlay&,std::size_t max_encoded_bytes,std::size_t max_plain_bytes) const;
    std::optional<CnAppearanceRowSelection> prepare_ordinary_remote_appearance(
        const CnRemoteActor::Record&,std::size_t max_encoded_bytes,std::size_t max_plain_bytes) const;
    // Actual selected ROM bytes/metadata remain tied to the exact full input
    // and immutable CSV profile. Still no native handles/ACT/issuer permission.
    std::optional<CnAppearanceRomInputs> prepare_normal_initial_appearance_roms(
        const CnWorldEntry::BeginPlay&,std::size_t max_encoded_bytes,std::size_t max_plain_bytes) const;
    std::optional<CnAppearanceRomInputs> prepare_ordinary_remote_appearance_roms(
        const CnRemoteActor::Record&,std::size_t max_encoded_bytes,std::size_t max_plain_bytes) const;
    // Pinned current CN gamedata rows, in native file order;00428430 first match.
    static const CnSceneCatalogRow* find(std::uint8_t family,std::uint16_t area_index) noexcept;
    // Recovered 0048EF40 reload branch for previous mode!=2 and target mode2.
    // previous must come from connection-owned state. nullopt means this
    // particular consumer branch does not load a house, NOT movement success.
    std::optional<CnPreparedHouseScene> prepare_enter_house(
        CnSceneState previous,const CnWorldEntry::MapChange& change,
        std::size_t max_encoded_bytes,std::size_t max_plain_bytes) const;
    // Normal initial path0044A470 ->0048CAA0 ->00537D40 passes load flag1.
    // BEGINPLAY supplies family/index/mode through00492E70's actor projection.
    // This prepares only the mode2 asset, not actor admission or BEGINPLAY reply.
    std::optional<CnPreparedHouseScene> prepare_initial_house(
        const CnWorldEntry::BeginPlay& entry,
        std::size_t max_encoded_bytes,std::size_t max_plain_bytes) const;
    // Initial mode0/flag1 path only. Does not apply live cache rotation,
    // authenticate an actor or construct a BEGINPLAY success packet.
    std::optional<CnPreparedOutdoorScene> prepare_initial_outdoor(
        const CnWorldEntry::BeginPlay& entry,
        std::size_t max_encoded_bytes,std::size_t max_plain_bytes) const;
    //00470C90 different/absent-MDT calls00462980 with flag0, NOT flag1.
    // Loads MDT/MDL/model ROMs and nine independent plain.map payloads. No MBD.
    // Input is the actual camera request; this does not commit a cache or camera.
    std::optional<CnPreparedStandaloneOutdoorScene> prepare_standalone_switch(
        std::string_view native_map_reference,CnOutdoorTerrain::ChunkCoordinate requested,
        std::size_t max_encoded_bytes,std::size_t max_plain_bytes,
        std::span<const std::uint8_t> initialized_prior_cells) const;
    // 0048E3E0 ->005396F0(nonnull actor): restore from owner-held actor state.
    // Does not represent005396F0(nullptr), whose branch resets only movement.
    std::optional<CnPreparedHouseScene> prepare_restored_house(CnSceneState actor_scene,
        std::size_t max_encoded_bytes,std::size_t max_plain_bytes) const;
private:
    friend class CnOutdoorWindow;
    struct StandaloneChunk {
        std::filesystem::path source_path;
        std::optional<CnStandaloneMapAsset> asset; // Null only for actual file-open failure.
    };
    StandaloneChunk read_standalone_chunk(const CnOutdoorSceneResources&,
        CnOutdoorTerrain::ChunkCoordinate,std::size_t max_encoded_bytes,std::size_t max_plain_bytes) const;
    std::optional<std::filesystem::path> native_profile_mdt_path(std::string_view) const;
    struct OutdoorProfile {
        std::vector<std::filesystem::path> source_files;
        std::shared_ptr<const CnOutdoorSceneResources> resources;
    };
    OutdoorProfile load_outdoor_profile(const std::filesystem::path& mdt_path,
        bool native_load_mbd,std::size_t max_encoded_bytes,std::size_t max_plain_bytes) const;
    CnPreparedHouseScene load_house(CnSceneState scene,
        std::size_t max_encoded_bytes,std::size_t max_plain_bytes) const;
    std::filesystem::path root_;
};
}
