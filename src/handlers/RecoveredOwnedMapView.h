#pragma once
#include "db/NativeMapCatalog.h"
#include "db/SqliteRecoveredCharacterRepository.h"
#include "protocol/RecoveredWorldRecords.h"
#include <optional>
#include <string_view>

namespace god2 {
// CUSTOM-0044: regional map presentation without consumption. This is not an
// original 25->3F server pairing or an item grant/teleport/quest reward rule.
struct RecoveredOwnedMapView {
    static constexpr std::string_view source_sha=
        "70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731";
    static bool supported(std::uint16_t item) {return item==5569 || item==5576;}
    // CUSTOM-0087: C2S68 carries no item/slot. Admit exactly one native
    // control in an otherwise idle frame; the caller must discover an owned
    // current-region map item before returning the native 3F panel opener.
    static bool map_panel68_request(std::span<const RecoveredWorldRecords::Record> records) {
        bool chosen=false;
        for(std::size_t i=0;i<records.size();++i) {
            if(std::holds_alternative<RecoveredMapPanelControl68::Request>(records[i])) {
                if(chosen)return false;
                chosen=true;
            } else if(std::holds_alternative<RecoveredWorldRecords::Tick>(records[i]))continue;
            else if(!chosen || i+1!=records.size() ||
                    !std::holds_alternative<RecoveredWorldRecords::ClientControl1F>(records[i]))return false;
        }
        return chosen;
    }
    static std::optional<std::uint16_t> map_item_for_scene(std::uint16_t area,std::uint16_t scene) {
        if(area==2 && scene==4)return std::uint16_t{5569};
        if(area==4 && scene==3)return std::uint16_t{5576};
        return {};
    }
    // Admit exactly one use, ticks and at most a trailing native1F00. Reject
    // mixed operations before loading ownership or emitting a response.
    static std::optional<RecoveredInventoryItemRequest::Request> request(
        std::span<const RecoveredWorldRecords::Record> records) {
        std::optional<RecoveredInventoryItemRequest::Request> value;
        for(std::size_t i=0;i<records.size();++i) {
            if(const auto* use=std::get_if<RecoveredInventoryItemRequest::Request>(&records[i])) {
                if(value || !supported(use->client_item_id))return std::nullopt;
                value=*use;
            } else if(std::holds_alternative<RecoveredWorldRecords::Tick>(records[i]))continue;
            else if(!value || i+1!=records.size() ||
                    !std::holds_alternative<RecoveredWorldRecords::ClientControl1F>(records[i]))return std::nullopt;
        }
        return value;
    }
    static bool qualified_map(const NativeMapRecord& row,std::uint16_t item) {
        const bool kunlun=item==5576;
        if(!supported(item) || row.area!=(kunlun?4:2) || row.scene!=(kunlun?3:4) || row.kind!=0)return false;
        const auto& s=row.source;
        if(s.dataset_id!=NativeMapCatalog::current_dataset_id ||
           s.source_path!="Data2/Patch/Comm/gamedata.csvZ" || s.source_sha256!=source_sha ||
           s.decoded_sha256!="75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815" ||
           s.native_image_sha256!="149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763" ||
           s.source_section!="Map_City_Coordniate" || s.loader_rva!="0x59a80" ||
           s.lookup_rva!="0x59d80" || s.row_count!=144 ||
           row.source_record_index!=(kunlun?77:62) || row.source_line!=(kunlun?21097:21082) ||
           row.record_sha256!=(kunlun?
               "f6d2d9389b1656741a548a85b4be608f35289cf958235331a2b36b55d3d7fd2d":
               "07eff399831668732bed8ee90e25e1c8b845fc6112efe529165c1d9f88cbf94e"))return false;
        const std::string_view hex=kunlun?
            "b0d1a4d1aa4c2c4369747949322cb158b15ba550acc92c342c302c332c3331382c3336332c64617461325c4d757369635c636974795c636974795f49322e7761762c646174615c4d757369635c46696768745c6174745f652e7761762c49736c616e6430335c4369747949325c6369747969322e6d64742c3235322c3235322c31":
            "c245c0dbb9d22c4369747949312cb7acb5d8c2ed2c322c302c342c3437372c3230392c64617461325c4d757369635c636974795c636974795f49312e7761762c646174615c4d757369635c46696768745c6174745f652e7761762c49736c616e6430315c4369747949315c6369747969312e6d64742c3138392c3138392c31";
        if(row.raw_record.size()*2!=hex.size())return false;
        const auto digit=[](char c){return c<='9'?c-'0':c-'a'+10;};
        for(std::size_t i=0;i<row.raw_record.size();++i)
            if(row.raw_record[i]!=((digit(hex[2*i])<<4)|digit(hex[2*i+1])))return false;
        return true;
    }
    static std::optional<std::vector<std::uint8_t>> logical(
        const RecoveredInventoryItemRequest::Request& use,const StoredInventorySlot& owned,
        const NativeMapRecord& map,bool item_source_qualified) {
        if(!item_source_qualified || use.raw_slot>=30 || !supported(use.client_item_id) ||
           owned.item_id!=use.client_item_id || owned.count!=1 || !owned.revision ||
           owned.source_sha256!=source_sha || !qualified_map(map,use.client_item_id))return std::nullopt;
        // Native S2C3F uses the CURRENT scene, not an item/map ID. raw_tail
        // is opaque producer residue, never quantity, privilege or consumption.
        return std::vector<std::uint8_t>{0x3f,1,0};
    }
};
}
