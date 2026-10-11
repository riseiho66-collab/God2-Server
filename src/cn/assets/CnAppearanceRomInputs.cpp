#include "cn/assets/CnAppearanceRomInputs.h"
#include <utility>

namespace god2cn {
namespace {
CnAppearanceRomInput read_rom(const std::filesystem::path& path,std::size_t encoded,std::size_t plain) {
    auto selected=read_cn_rom_resource(path,encoded);
    auto metadata=CnRomAsset::from_resource(selected.encoded_bytes,plain);
    return {std::move(selected),std::move(metadata)};
}
}
CnSelectionAppearanceRomInputs::CnSelectionAppearanceRomInputs(CnSelectionAppearanceRows rows,
    std::array<CnAppearanceRomInput,4> parts):rows_(std::move(rows)),parts_(std::move(parts)) {}
CnSelectionAppearanceRomInputs CnSelectionAppearanceRomInputs::read(CnSelectionAppearanceRows rows,
    std::size_t encoded,std::size_t plain) {
    const auto& paths=rows.part_resource_paths();
    // Original consumer order body/face/head/weapon. Equal filenames remain
    // separate inputs; no live cache reset, allocation or handle assignment.
    std::array<CnAppearanceRomInput,4> parts{
        read_rom(paths[0],encoded,plain),read_rom(paths[1],encoded,plain),
        read_rom(paths[2],encoded,plain),read_rom(paths[3],encoded,plain)};
    return CnSelectionAppearanceRomInputs(std::move(rows),std::move(parts));
}
CnAppearanceRomInputs::CnAppearanceRomInputs(CnAppearanceRowSelection rows,
    std::array<CnAppearanceRomInput,4> parts,std::optional<CnAppearanceRomInput> driver)
    :rows_(std::move(rows)),parts_(std::move(parts)),driver_(std::move(driver)) {}
CnAppearanceRomInputs CnAppearanceRomInputs::read(CnAppearanceRowSelection rows,std::size_t encoded,std::size_t plain) {
    const auto& paths=rows.part_resource_paths();
    std::array<CnAppearanceRomInput,4> parts{
        read_rom(paths[0],encoded,plain),read_rom(paths[1],encoded,plain),
        read_rom(paths[2],encoded,plain),read_rom(paths[3],encoded,plain)};
    std::optional<CnAppearanceRomInput> driver;
    if(rows.driver_resource_path())driver=read_rom(*rows.driver_resource_path(),encoded,plain);
    // Missing driver filename is actual table absence, not a default ROM.
    // No rollback claim: local snapshots only, no live native bank mutated.
    return CnAppearanceRomInputs(std::move(rows),std::move(parts),std::move(driver));
}
}
