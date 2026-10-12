#pragma once
#include "protocol/RecoveredWorldEntry.h"
#include "protocol/RecoveredWorldFrame.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>

namespace god2 {
// Read the actual full TW zero-seed2A emitted by Session. No candidate builder,
// profile defaults or CN-as-TW authority. Native468626..468676 copies these
// local actor fields; all appearance/resource/opaque bytes remain untouched.
struct RecoveredWorldEntryView {
    RecoveredWorldEntry::Frame wire;
    std::array<std::uint8_t,37> logical;
    std::uint16_t actor_handle,area,scene,x,y;
    std::uint8_t kind;
    // Native149c B0bit31 -> 468204 world+A7F2F3C -> composite72 new NPC
    // slot through 4CBD70 -> 4CAFE0 argument6. Its nonzero branch requests
    // the "npcid:%d" label; existing-slot updates need not recreate it.
    // Other uses and the actual server's flag-selection rule remain open.
    // Read the complete received entry; do not derive this bit from NPC
    // membership, IDs or permission. It does not prove resource/load success.
    bool npc_id_label_requested() const noexcept {return (logical[4]&0x80u)!=0;}
    struct EntryResourceSelectors {
        std::uint8_t drv_selector;
        std::uint8_t drv_doll_selector;
        bool operator==(const EntryResourceSelectors&) const = default;
    };
    // Ordinary zero-transform2A:4684EB passes unsigned B6 and B0 bits16..22
    // to461270. The second selector reaches463AD0's distinct DrvDoll bank;
    // it does not select the four-component branch or the Drv action row.
    // These are the full entry's raw selectors, not resource membership,
    // current after-state, authoritative field construction or load success.
    // Other transform/override paths remain unqualified. Reading these values
    // does not authorize scene admission or fresh-preview component defaults.
    EntryResourceSelectors entry_resource_selectors() const noexcept {
        return {logical[7],static_cast<std::uint8_t>(logical[3]&0x7f)};
    }
    struct EntryAppearanceBaseline {
        // The identity actually bound by this2A, not a mask for arbitrary DA.
        std::uint16_t actor_handle;
        std::array<std::uint8_t,8> components;
        std::uint16_t transform_key;
        std::uint8_t raw_scalar5,raw_scalar6;
        bool operator==(const EntryAppearanceBaseline&) const = default;
    };
    // Native149c:468328/46833F save both complete component DWORDs;
    // 468558/46855D save the transform WORD;46827B/468284/46828A save
    // both raw scalars. Independently matched DA writes are documented in
    // tw-native-entry-field-flow-source-20261010.md. Keep every variant bit
    // and nonzero transform; no6bf/CUSTOM0047 storage or renderer claim.
    // This is this full entry's baseline only. Later appearance events may
    // change it; it grants neither current after-state nor DA emission rights.
    EntryAppearanceBaseline entry_appearance_baseline() const noexcept {
        EntryAppearanceBaseline value{actor_handle,{},
            static_cast<std::uint16_t>(std::uint16_t{logical[33]}|
                (std::uint16_t{logical[34]}<<8)),logical[35],logical[36]};
        std::copy_n(logical.begin()+13,value.components.size(),value.components.begin());
        return value;
    }
    static std::optional<RecoveredWorldEntryView> read(const RecoveredWorldEntry::Frame& wire) {
        const auto decoded=RecoveredWorldFrame::decode(wire);
        if(!decoded || decoded->size()!=37 || (*decoded)[0]!=0x2a)return std::nullopt;
        const auto u16=[&](std::size_t at) {return std::uint16_t((*decoded)[at])|
            (std::uint16_t((*decoded)[at+1])<<8);};
        const auto map=u16(25);
        std::uint32_t position=0;
        for(unsigned i=0;i<4;++i)position|=std::uint32_t((*decoded)[29+i])<<(8*i);
        const auto handle=static_cast<std::uint16_t>(u16(1)&0x3fff);
        const auto area=static_cast<std::uint16_t>(map&0x3f);
        // Native4681D8..4681E5 excludes area0 and >=17 in this normal entry.
        if(!handle || !area || area>=17)return std::nullopt;
        std::array<std::uint8_t,37> full;
        std::copy(decoded->begin(),decoded->end(),full.begin());
        return RecoveredWorldEntryView{wire,full,handle,area,static_cast<std::uint16_t>(map>>6),
            static_cast<std::uint16_t>((position>>2)&0x7fff),static_cast<std::uint16_t>(position>>17),
            static_cast<std::uint8_t>(position&3)};
    }
};
}
