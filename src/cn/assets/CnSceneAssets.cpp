#include "cn/assets/CnSceneAssets.h"
#include "cn/assets/CnAreaDirectory.h"
#include "cn/assets/CnHouseMapAsset.h"
#include "cn/assets/CnOutdoorMapAsset.h"
#include "cn/assets/CnResourceBytes.h"
#include "cn/world/CnOutdoorCamera.h"
#include <stdexcept>
#include <utility>

namespace god2cn {
CnPreparedStandaloneOutdoorScene::CnPreparedStandaloneOutdoorScene(std::string reference,
    std::vector<std::filesystem::path> paths,std::array<std::filesystem::path,9> chunk_paths,
    CnOutdoorTerrain::ChunkCoordinate center,
    std::array<std::optional<CnStandaloneMapAsset>,9> chunks,CnMapPassability grid,
    std::shared_ptr<const CnOutdoorSceneResources> resources)
    :reference_(std::move(reference)),source_files_(std::move(paths)),chunk_sources_(std::move(chunk_paths)),center_(center),
     chunks_(std::move(chunks)),grid_(std::move(grid)),resources_(std::move(resources)) {}
namespace {
constexpr CnSceneCatalogRow rows[]={
#include "cn/assets/CnSceneCatalog.inc"
};
std::filesystem::path native_relative_path(std::string_view bytes) {
    // Installed pinned catalog/CAN references are ASCII. Do not apply an OS
    // ANSI codepage or guess an encoding for an unrecovered non-ASCII variant.
    std::u8string path;
    for (const unsigned char c:bytes) {
        if (c<0x20 || c>=0x7f || c==':') throw std::invalid_argument("CN native asset path requires unrecovered encoding or form");
        path.push_back(static_cast<char8_t>(c=='\\'?'/':c));
    }
    const std::filesystem::path result(path);
    if (result.empty() || result.is_absolute() || result.has_root_path())
        throw std::invalid_argument("CN native relative asset path unavailable");
    for (const auto& part:result) if (part=="..") throw std::invalid_argument("CN native asset escapes its area directory");
    return result;
}
}
CnSceneAssets::CnSceneAssets(std::filesystem::path root):root_(std::move(root)) {
    if (!root_.is_absolute()) throw std::invalid_argument("CN client root must be explicit and absolute");
}
std::optional<CnAppearanceRowSelection> CnSceneAssets::prepare_normal_initial_appearance(
    const CnWorldEntry::BeginPlay& entry,std::size_t encoded_budget,std::size_t plain_budget) const {
    if(entry.alternate_appearance_resource_key_raw())return std::nullopt;
    return CnAppearanceResources::read(root_,encoded_budget,plain_budget)->select_normal_initial(entry);
}
std::optional<CnAppearanceRowSelection> CnSceneAssets::prepare_ordinary_remote_appearance(
    const CnRemoteActor::Record& record,std::size_t encoded_budget,std::size_t plain_budget) const {
    if(record.alternate_appearance_resource_key_raw())return std::nullopt;
    return CnAppearanceResources::read(root_,encoded_budget,plain_budget)->select_ordinary_remote(record);
}
std::optional<CnAppearanceRomInputs> CnSceneAssets::prepare_normal_initial_appearance_roms(
    const CnWorldEntry::BeginPlay& entry,std::size_t encoded,std::size_t plain) const {
    auto rows=prepare_normal_initial_appearance(entry,encoded,plain);
    if(!rows)return std::nullopt;
    return CnAppearanceRomInputs::read(std::move(*rows),encoded,plain);
}
std::optional<CnAppearanceRomInputs> CnSceneAssets::prepare_ordinary_remote_appearance_roms(
    const CnRemoteActor::Record& record,std::size_t encoded,std::size_t plain) const {
    auto rows=prepare_ordinary_remote_appearance(record,encoded,plain);
    if(!rows)return std::nullopt;
    return CnAppearanceRomInputs::read(std::move(*rows),encoded,plain);
}
const CnSceneCatalogRow* CnSceneAssets::find(std::uint8_t family,std::uint16_t area) noexcept {
    for (const auto& row:rows) if (row.family==family && row.area_index==area) return &row;
    return nullptr;
}
std::optional<CnPreparedHouseScene> CnSceneAssets::prepare_enter_house(
    CnSceneState previous,const CnWorldEntry::MapChange& change,
    std::size_t max_encoded_bytes,std::size_t max_plain_bytes) const {
    if (previous.mode>3) throw std::invalid_argument("CN previous scene state invalid");
    const auto target_mode=static_cast<std::uint8_t>(change.packed_location()&3);
    if (previous.mode==2 || target_mode!=2) return std::nullopt;
    if (previous.family==change.map_family() && previous.area_index==change.map_index() &&
        change.same_map_branch_bit()) return std::nullopt;
    return load_house({change.map_family(),change.map_index(),target_mode},max_encoded_bytes,max_plain_bytes);
}
std::optional<CnPreparedHouseScene> CnSceneAssets::prepare_initial_house(
    const CnWorldEntry::BeginPlay& entry,
    std::size_t max_encoded_bytes,std::size_t max_plain_bytes) const {
    if (!entry.initial_consumer_accepts_map_family())
        throw std::invalid_argument("CN BEGINPLAY family outside native initial consumer range");
    if (entry.scene_mode()!=2) return std::nullopt;
    return load_house({entry.map_family(),entry.map_index(),entry.scene_mode()},max_encoded_bytes,max_plain_bytes);
}
std::optional<CnPreparedHouseScene> CnSceneAssets::prepare_restored_house(
    CnSceneState scene,std::size_t max_encoded_bytes,std::size_t max_plain_bytes) const {
    if (scene.mode>3) throw std::invalid_argument("CN restored actor scene invalid");
    if (scene.mode!=2) return std::nullopt;
    return load_house(scene,max_encoded_bytes,max_plain_bytes);
}
std::optional<CnPreparedOutdoorScene> CnSceneAssets::prepare_initial_outdoor(
    const CnWorldEntry::BeginPlay& entry,std::size_t encoded_budget,std::size_t plain_budget) const {
    if (!entry.initial_consumer_accepts_map_family())
        throw std::invalid_argument("CN BEGINPLAY family outside native initial consumer range");
    if (entry.scene_mode()!=0) return std::nullopt;
    //00537D40 loads the family CAN first, uses actor area index to select its
    // filename, and joins it to0048EA40's family-base directory.
    const auto* base=find(entry.map_family(),0);
    if (!base) throw std::invalid_argument("CN family base catalog row unavailable");
    const auto base_path=root_/"Data2"/"map"/native_relative_path(base->native_mdt_path);
    auto can_path=base_path; can_path.replace_extension(".can");
    const auto directory=CnAreaDirectory::read(read_cn_asset_file(can_path,encoded_budget));
    const auto* area=directory.lookup(entry.map_index());
    if (!area) throw std::invalid_argument("CN outdoor CAN area unavailable");
    const auto name=area->filename();
    if (!name) throw std::invalid_argument("CN outdoor CAN filename unavailable");
    auto mdt_path=base_path.parent_path()/native_relative_path(*name);
    mdt_path.replace_extension(".mdt"); //00471EB0 replaces the CAN extension
    auto profile=load_outdoor_profile(mdt_path,true,encoded_budget,plain_budget);
    auto placement=profile.resources->initial_at_world(entry.x(),entry.y());
    if (!placement) return std::nullopt;
    profile.source_files.insert(profile.source_files.begin(),can_path);
    return CnPreparedOutdoorScene{{entry.map_family(),entry.map_index(),entry.scene_mode()},
        area->raw_kind(),std::string(*name),std::move(profile.source_files),std::move(*placement),
        std::move(profile.resources)};
}
CnSceneAssets::OutdoorProfile CnSceneAssets::load_outdoor_profile(const std::filesystem::path& mdt_path,
    bool load_mbd,std::size_t encoded_budget,std::size_t plain_budget) const {
    auto mdt_source=read_cn_preferred_resource(mdt_path,encoded_budget);
    auto map=CnOutdoorMapAsset::from_v12_resource(mdt_source.encoded_bytes,plain_budget);
    auto mdl_path=mdt_path; mdl_path.replace_extension(".mdl");
    auto mdl_source=read_cn_preferred_resource(mdl_path,encoded_budget);
    auto models=CnOutdoorModelAsset::from_v16_resource(mdl_source.encoded_bytes,plain_budget);
    std::vector<std::filesystem::path> sources{mdt_source.source_path,mdl_source.source_path};
    //004775E0's model registry is distinct from MDT terrain ROM slots511-i.
    // No registry sharing by matching action ID or incidental file name.
    std::vector<CnRomAsset> roms;
    if (models.rom_references().size()>128)
        throw std::invalid_argument("CN model ROM count exceeds native slots");
    roms.reserve(models.rom_references().size());
    for (const auto& reference:models.rom_references()) {
        const auto path=mdl_path.parent_path()/native_relative_path(reference);
        if (path.extension().native().size()!=4)
            throw std::invalid_argument("CN model ROM extension variant unavailable");
        auto resource=read_cn_preferred_resource(path,encoded_budget);
        roms.push_back(CnRomAsset::from_resource(resource.encoded_bytes,plain_budget));
        sources.push_back(std::move(resource.source_path));
    }
    //00462980 branches after MDL at00463440/0046344E. Camera replacement
    // calls pass0 at00470F27/00471030; initial flag1 alone loads MBD here.
    std::optional<CnOutdoorTerrain> terrain;
    if(load_mbd) {
        auto mbd_path=mdt_path; mbd_path.replace_extension(".mbd");
        auto mbd_source=read_cn_mbd_resource(mbd_path,encoded_budget);
        terrain=CnOutdoorTerrain::from_v12_resource(mbd_source.encoded_bytes,plain_budget);
        sources.push_back(std::move(mbd_source.source_path));
    }
    // Physical CN root is explicit, like the native cached working-directory
    // input. Keep plain MDT identity separate from selected MDT/MDTZ bytes.
    // Supported source paths are ASCII; no implicit CP936/UTF8 conversion.
    auto reference_path=mdt_path;reference_path.make_preferred();
    const auto reference_bytes=reference_path.u8string();
    std::string native_reference;
    for(const auto c:reference_bytes) {
        if(c<0x20 || c>=0x7f)throw std::invalid_argument("CN native resource identity encoding unavailable");
        native_reference.push_back(static_cast<char>(c));
    }
    auto resources=std::shared_ptr<const CnOutdoorSceneResources>(new CnOutdoorSceneResources(
        std::move(map),std::move(models),std::move(roms),std::move(terrain),std::move(native_reference)));
    return {std::move(sources),std::move(resources)};
}
std::optional<std::filesystem::path> CnSceneAssets::native_profile_mdt_path(std::string_view mdt) const {
    if(!mdt.ends_with(".mdt"))return std::nullopt;
    auto base=root_/"Data2"/"map";base.make_preferred();
    const auto base_bytes=base.u8string();
    // Qualify the explicit physical CN profile root, including its separator.
    // Do not open arbitrary absolute names supplied by a packet or normalize
    // path aliases into a different accepted native resource identity.
    if(mdt.size()<=base_bytes.size()+1)return std::nullopt;
    const auto fold=[](unsigned char c) {return c>='A' && c<='Z' ? c-'A'+'a' : c;};
    for(std::size_t i=0;i<base_bytes.size();++i) {
        const auto c=static_cast<unsigned char>(base_bytes[i]);
        if(c<0x20 || c>=0x7f || fold(c)!=fold(static_cast<unsigned char>(mdt[i])))return std::nullopt;
    }
    if(mdt[base_bytes.size()]!='\\')return std::nullopt;
    return base/native_relative_path(mdt.substr(base_bytes.size()+1));
}
CnSceneAssets::StandaloneChunk CnSceneAssets::read_standalone_chunk(
    const CnOutdoorSceneResources& resources,CnOutdoorTerrain::ChunkCoordinate at,
    std::size_t encoded_budget,std::size_t plain_budget) const {
    if(resources.has_retained_mbd())throw std::invalid_argument("CN standalone reader requires flag0 profile");
    const auto& identity=resources.native_mdt_reference();
    if(!native_profile_mdt_path(identity))throw std::invalid_argument("CN standalone profile root unqualified");
    const auto name=CnOutdoorCamera::map_reference(std::string_view(identity).substr(0,identity.size()-4),at);
    if(!name || !resources.owns_native_map_reference(*name,at))
        throw std::invalid_argument("CN standalone MAP axis/identity variant unrecovered");
    const auto file=std::filesystem::u8path(*name);
    //004657E0 uses plain fopen("r"), not preferred Z/decompression.
    const auto bytes=try_read_cn_plain_map_file(file,encoded_budget);
    if(!bytes)return {file,std::nullopt};
    auto asset=CnStandaloneMapAsset::from_text(*bytes,plain_budget);
    if(asset.width()!=21 || asset.height()!=21)
        throw std::invalid_argument("CN standalone cache MAP dimensions unrecovered");
    return StandaloneChunk{file,std::move(asset)};
}
std::optional<CnPreparedStandaloneOutdoorScene> CnSceneAssets::prepare_standalone_switch(
    std::string_view reference,CnOutdoorTerrain::ChunkCoordinate requested,
    std::size_t encoded_budget,std::size_t plain_budget,std::span<const std::uint8_t> prior) const {
    const auto mdt=CnOutdoorSceneResources::native_map_mdt_reference(reference,requested);
    if(!mdt)return std::nullopt;
    const auto path=native_profile_mdt_path(*mdt);
    if(!path)return std::nullopt;
    auto profile=load_outdoor_profile(*path,false,encoded_budget,plain_budget);
    if(!profile.resources->owns_native_map_reference(reference,requested))return std::nullopt;
    const auto center=profile.resources->qualified_center(requested);
    if(!center)return std::nullopt;
    std::array<std::optional<CnStandaloneMapAsset>,9> chunks;
    std::array<std::filesystem::path,9> chunk_paths;
    for(std::size_t i=0;i<chunks.size();++i) {
        const CnOutdoorTerrain::ChunkCoordinate at{center->x+static_cast<std::int32_t>(i%3)-1,
            center->y+static_cast<std::int32_t>(i/3)-1};
        auto loaded=read_standalone_chunk(*profile.resources,at,encoded_budget,plain_budget);
        chunk_paths[i]=std::move(loaded.source_path);
        chunks[i]=std::move(loaded.asset);
        profile.source_files.push_back(chunk_paths[i]);
    }
    auto grid=profile.resources->compose_standalone_frame_window(*center,chunks,prior);
    return CnPreparedStandaloneOutdoorScene(std::string(reference),std::move(profile.source_files),std::move(chunk_paths),
        *center,std::move(chunks),std::move(grid),std::move(profile.resources));
}
CnPreparedHouseScene CnSceneAssets::load_house(CnSceneState scene,
    std::size_t max_encoded_bytes,std::size_t max_plain_bytes) const {
    // 0048F27E and0048F307 explicitly push area0, not the destination index.
    // Initial/restore helpers0048E980 and0048EA40 do the same base lookup.
    const auto* base=find(scene.family,0);
    if (!base) throw std::invalid_argument("CN family base catalog row unavailable");
    auto base_path=root_/"Data2"/"map"/native_relative_path(base->native_mdt_path);
    auto can_path=base_path;
    can_path.replace_extension(".can");
    const auto directory=CnAreaDirectory::read(read_cn_asset_file(can_path,max_encoded_bytes));
    const auto* entry=directory.lookup(scene.area_index);
    if (!entry) throw std::invalid_argument("CN native area directory reference unavailable");
    const auto name=entry->filename();
    if (!name) throw std::invalid_argument("CN native area filename unavailable");
    auto house_path=base_path.parent_path()/native_relative_path(*name);
    const auto resource=read_cn_preferred_resource(house_path,max_encoded_bytes);
    const auto house=CnHouseMapAsset::from_v16_resource(resource.encoded_bytes,max_plain_bytes);
    return CnPreparedHouseScene{scene,
        entry->raw_kind(),std::string(*name),{can_path,resource.source_path},
        house.compose_initial_passability()};
}
}
