#include "db/ServerDataDictionary.h"
#include <algorithm>
#include <array>

namespace god2 {
namespace {
using D=ServerDataDictionary;
constexpr std::array<D::SourceLocation,1> sources_0{{
    {"src/db/SqliteNativeCharacterSummarySnapshotRepository.cpp",207},
}};
constexpr std::array<D::SourceLocation,1> sources_1{{
    {"src/db/SqliteNativeCharacterSummarySnapshotRepository.cpp",220},
}};
constexpr std::array<D::SourceLocation,1> sources_2{{
    {"src/db/SqliteNativeAccountSnapshotRepository.cpp",141},
}};
constexpr std::array<D::SourceLocation,1> sources_3{{
    {"src/db/Migration.cpp",23},
}};
constexpr std::array<D::Column,4> columns_3{{
    {"id","帳號編號","SQLite 正整數帳號主鍵，不是客戶端 actor handle。",D::ValueKind::Integer},
    {"username","登入名稱","帳號登入名稱；保留既有唯一約束。",D::ValueKind::Text},
    {"password_hash","密碼雜湊","既有密碼雜湊原值，不是明文密碼。",D::ValueKind::Text},
    {"created_at","建立時間","來源保存的建立時間文字，不改時區或格式。",D::ValueKind::Text},
}};
constexpr std::array<D::SourceLocation,1> sources_4{{
    {"src/db/Migration.cpp",140},
}};
constexpr std::array<D::SourceLocation,1> sources_5{{
    {"src/db/Migration.cpp",112},
}};
constexpr std::array<D::SourceLocation,1> sources_6{{
    {"src/db/Migration.cpp",125},
}};
constexpr std::array<D::SourceLocation,1> sources_7{{
    {"src/db/SqliteBeastBankRepository.cpp",31},
}};
constexpr std::array<D::SourceLocation,1> sources_8{{
    {"src/db/SqliteBeastSnapshotRepository.cpp",74},
}};
constexpr std::array<D::SourceLocation,1> sources_9{{
    {"src/db/SqliteBeastBagRepository.cpp",104},
}};
constexpr std::array<D::SourceLocation,1> sources_10{{
    {"src/db/SqliteBeastSnapshotRepository.cpp",67},
}};
constexpr std::array<D::SourceLocation,1> sources_11{{
    {"src/db/SqliteBeastSnapshotRepository.cpp",51},
}};
constexpr std::array<D::SourceLocation,1> sources_12{{
    {"src/db/SqliteArmorSlotRepository.cpp",42},
}};
constexpr std::array<D::SourceLocation,1> sources_13{{
    {"src/db/SqliteOwnedArmorBankRepository.cpp",65},
}};
constexpr std::array<D::SourceLocation,1> sources_14{{
    {"src/db/SqliteOwnedArmorBankRepository.cpp",83},
}};
constexpr std::array<D::SourceLocation,1> sources_15{{
    {"src/db/SqliteBankRepository.cpp",22},
}};
constexpr std::array<D::SourceLocation,1> sources_16{{
    {"src/db/SqliteBeastBankRepository.cpp",87},
}};
constexpr std::array<D::SourceLocation,1> sources_17{{
    {"src/db/SqliteBeastBankRepository.cpp",104},
}};
constexpr std::array<D::SourceLocation,1> sources_18{{
    {"src/db/SqliteOwnedForeignBankRepository.cpp",48},
}};
constexpr std::array<D::SourceLocation,1> sources_19{{
    {"src/db/SqliteOwnedForeignBankRepository.cpp",71},
}};
constexpr std::array<D::SourceLocation,2> sources_20{{
    {"src/db/Migration.cpp",563},
    {"src/db/SqliteBankItemsRepository.cpp",92},
}};
constexpr std::array<D::SourceLocation,2> sources_21{{
    {"src/db/Migration.cpp",552},
    {"src/db/SqliteBankItemsRepository.cpp",81},
}};
constexpr std::array<D::SourceLocation,1> sources_22{{
    {"src/db/SqliteOwnedMixedBankRepository.cpp",48},
}};
constexpr std::array<D::SourceLocation,1> sources_23{{
    {"src/db/SqliteBankRepository.cpp",27},
}};
constexpr std::array<D::SourceLocation,1> sources_24{{
    {"src/db/SqliteBeastBagRepository.cpp",91},
}};
constexpr std::array<D::SourceLocation,1> sources_25{{
    {"src/db/SqliteBeastSnapshotRepository.cpp",42},
}};
constexpr std::array<D::SourceLocation,1> sources_26{{
    {"src/db/SqliteBeastSnapshotRepository.cpp",23},
}};
constexpr std::array<D::SourceLocation,1> sources_27{{
    {"src/db/SqliteOwnedBlacklistRepository.cpp",12},
}};
constexpr std::array<D::SourceLocation,1> sources_28{{
    {"src/db/Migration.cpp",495},
}};
constexpr std::array<D::SourceLocation,1> sources_29{{
    {"src/db/Migration.cpp",300},
}};
constexpr std::array<D::SourceLocation,1> sources_30{{
    {"src/db/Migration.cpp",312},
}};
constexpr std::array<D::SourceLocation,1> sources_31{{
    {"src/db/Migration.cpp",120},
}};
constexpr std::array<D::SourceLocation,1> sources_32{{
    {"src/db/SqliteFruitQuestRepository.cpp",40},
}};
constexpr std::array<D::SourceLocation,1> sources_33{{
    {"src/db/SqliteFruitQuestRepository.cpp",47},
}};
constexpr std::array<D::SourceLocation,1> sources_34{{
    {"src/db/SqliteNativeEquipmentSnapshotRepository.cpp",195},
}};
constexpr std::array<D::Column,8> columns_34{{
    {"account_id","帳號編號","交付快照的完整帳號識別。",D::ValueKind::Integer},
    {"character_id","角色編號","交付快照的完整角色識別。",D::ValueKind::Integer},
    {"client_sha256","客戶端版本","快照適用的客戶端版本雜湊。",D::ValueKind::Text},
    {"record_kind","紀錄格式識別","明確版本化紀錄格式，不猜新的格式。",D::ValueKind::Text},
    {"record","原始裝備交付快照","完整 1215 位元組快照；不是第二份權威背包或裝備權限。",D::ValueKind::Binary},
    {"revision","快照版本","已保存原生交付快照版本。",D::ValueKind::Integer},
    {"source_sha256","來源雜湊","快照來源證據雜湊。",D::ValueKind::Text},
    {"source_record","來源紀錄","快照來源證據原文。",D::ValueKind::Text},
}};
constexpr std::array<D::SourceLocation,1> sources_35{{
    {"src/db/SqliteNativeWorldEntrySnapshotRepository.cpp",176},
}};
constexpr std::array<D::SourceLocation,1> sources_36{{
    {"src/db/SqliteOwnedInstanceDiscardRepository.cpp",66},
}};
constexpr std::array<D::SourceLocation,1> sources_37{{
    {"src/db/SqliteOwnedInstanceTradeRepository.cpp",113},
}};
constexpr std::array<D::SourceLocation,1> sources_38{{
    {"src/db/Migration.cpp",318},
}};
constexpr std::array<D::SourceLocation,1> sources_39{{
    {"src/db/Migration.cpp",522},
}};
constexpr std::array<D::SourceLocation,1> sources_40{{
    {"src/db/SqlitePlayerAppearanceRepository.cpp",49},
}};
constexpr std::array<D::SourceLocation,1> sources_41{{
    {"src/db/Migration.cpp",355},
}};
constexpr std::array<D::SourceLocation,1> sources_42{{
    {"src/db/Migration.cpp",102},
}};
constexpr std::array<D::Column,7> columns_42{{
    {"character_id","角色編號","生命魔力資料所屬共用角色。",D::ValueKind::Integer},
    {"hp","目前生命值","權威目前 HP。",D::ValueKind::Integer},
    {"max_hp","最大生命值","權威最大 HP；保留 HP 不超過最大值的約束。",D::ValueKind::Integer},
    {"mp","目前魔力值","權威目前 MP。",D::ValueKind::Integer},
    {"max_mp","最大魔力值","權威最大 MP；保留 MP 不超過最大值的約束。",D::ValueKind::Integer},
    {"revision","資源版本","生命魔力持久狀態版本。",D::ValueKind::Integer},
    {"design_id","設計合約識別","原有自製規則來源合約識別。",D::ValueKind::Text},
}};
constexpr std::array<D::SourceLocation,1> sources_43{{
    {"src/db/Migration.cpp",447},
}};
constexpr std::array<D::SourceLocation,1> sources_44{{
    {"src/db/Migration.cpp",133},
}};
constexpr std::array<D::SourceLocation,1> sources_45{{
    {"src/db/SqliteRoleTextRepository.cpp",38},
}};
constexpr std::array<D::SourceLocation,1> sources_46{{
    {"src/db/SqliteTeleportGemRepository.cpp",28},
}};
constexpr std::array<D::SourceLocation,1> sources_47{{
    {"src/db/SqliteTradeRepository.cpp",30},
}};
constexpr std::array<D::SourceLocation,1> sources_48{{
    {"src/db/SqliteTradeRepository.cpp",25},
}};
constexpr std::array<D::SourceLocation,1> sources_49{{
    {"src/db/Migration.cpp",457},
}};
constexpr std::array<D::SourceLocation,1> sources_50{{
    {"src/db/Migration.cpp",29},
}};
constexpr std::array<D::SourceLocation,1> sources_51{{
    {"src/db/SqliteSkillBookLearningRepository.cpp",217},
}};
constexpr std::array<D::SourceLocation,1> sources_52{{
    {"src/db/SqliteSkillBookLearningRepository.cpp",222},
}};
constexpr std::array<D::SourceLocation,1> sources_53{{
    {"src/db/Migration.cpp",147},
}};
constexpr std::array<D::SourceLocation,1> sources_54{{
    {"src/db/Migration.cpp",162},
}};
constexpr std::array<D::SourceLocation,2> sources_55{{
    {"src/db/Migration.cpp",192},
    {"src/db/Migration.cpp",202},
}};
constexpr std::array<D::SourceLocation,1> sources_56{{
    {"src/db/Migration.cpp",213},
}};
constexpr std::array<D::SourceLocation,1> sources_57{{
    {"src/db/NativeArmorCatalog.cpp",57},
}};
constexpr std::array<D::SourceLocation,1> sources_58{{
    {"src/db/NativeArmorCatalog.cpp",45},
}};
constexpr std::array<D::SourceLocation,1> sources_59{{
    {"src/db/Migration.cpp",288},
}};
constexpr std::array<D::SourceLocation,1> sources_60{{
    {"src/db/Migration.cpp",480},
}};
constexpr std::array<D::SourceLocation,1> sources_61{{
    {"src/db/Migration.cpp",342},
}};
constexpr std::array<D::SourceLocation,2> sources_62{{
    {"src/db/Migration.cpp",65},
    {"src/db/TaiwanInstalledSkillCatalogImport.cpp",35},
}};
constexpr std::array<D::Column,9> columns_62{{
    {"dataset_id","資料集識別","版本限定的原生資料集識別。",D::ValueKind::Text},
    {"source_path","來源路徑","原生來源的保存路徑註記，不代表檔案目前仍相同。",D::ValueKind::Text},
    {"source_sha256","原始來源雜湊","完整來源的 SHA-256 文字。",D::ValueKind::Text},
    {"decoded_sha256","解碼來源雜湊","完整解碼內容的 SHA-256 文字。",D::ValueKind::Text},
    {"native_image_sha256","原生映像雜湊","消費者映像證據的 SHA-256，不代表現行 EXE 觀測。",D::ValueKind::Text},
    {"source_section","來源區段","原生來源區段註記。",D::ValueKind::Text},
    {"loader_rva","載入器相對位址","已保存的原生載入器相對位址文字。",D::ValueKind::Text},
    {"lookup_rva","查找器相對位址","已保存的原生查找器相對位址文字。",D::ValueKind::Text},
    {"row_count","來源列數","此資料集完整來源列數。",D::ValueKind::Integer},
}};
constexpr std::array<D::SourceLocation,1> sources_63{{
    {"src/db/NativeDeliverySnapshotSchema.cpp",21},
}};
constexpr std::array<D::SourceLocation,1> sources_64{{
    {"src/db/Migration.cpp",252},
}};
constexpr std::array<D::SourceLocation,1> sources_65{{
    {"src/db/Migration.cpp",76},
}};
constexpr std::array<D::SourceLocation,1> sources_66{{
    {"src/db/Migration.cpp",403},
}};
constexpr std::array<D::SourceLocation,1> sources_67{{
    {"src/db/Migration.cpp",391},
}};
constexpr std::array<D::SourceLocation,1> sources_68{{
    {"src/db/Migration.cpp",271},
}};
constexpr std::array<D::SourceLocation,1> sources_69{{
    {"src/db/Migration.cpp",380},
}};
constexpr std::array<D::SourceLocation,1> sources_70{{
    {"src/db/Migration.cpp",364},
}};
constexpr std::array<D::SourceLocation,1> sources_71{{
    {"src/db/Migration.cpp",374},
}};
constexpr std::array<D::SourceLocation,1> sources_72{{
    {"src/db/NativeNpcDisplayCatalog.cpp",44},
}};
constexpr std::array<D::SourceLocation,1> sources_73{{
    {"src/db/NativeNpcDisplayCatalog.cpp",38},
}};
constexpr std::array<D::SourceLocation,1> sources_74{{
    {"src/db/Migration.cpp",511},
}};
constexpr std::array<D::SourceLocation,1> sources_75{{
    {"src/db/NativePet2CategoryCatalog.cpp",39},
}};
constexpr std::array<D::SourceLocation,1> sources_76{{
    {"src/db/NativePet2CategoryCatalog.cpp",35},
}};
constexpr std::array<D::SourceLocation,1> sources_77{{
    {"src/db/Migration.cpp",332},
}};
constexpr std::array<D::SourceLocation,1> sources_78{{
    {"src/db/Migration.cpp",170},
}};
constexpr std::array<D::SourceLocation,1> sources_79{{
    {"src/db/Migration.cpp",182},
}};
constexpr std::array<D::SourceLocation,1> sources_80{{
    {"src/db/NativePetRoomSourceCatalog.cpp",348},
}};
constexpr std::array<D::SourceLocation,1> sources_81{{
    {"src/db/NativePetRoomSourceCatalog.cpp",339},
}};
constexpr std::array<D::SourceLocation,1> sources_82{{
    {"src/db/NativeRomMapSourceCatalog.cpp",193},
}};
constexpr std::array<D::SourceLocation,1> sources_83{{
    {"src/db/NativeRomMapSourceCatalog.cpp",183},
}};
constexpr std::array<D::SourceLocation,1> sources_84{{
    {"src/db/Migration.cpp",237},
}};
constexpr std::array<D::SourceLocation,1> sources_85{{
    {"src/db/NativeSkillBookSourceCatalog.cpp",25},
}};
constexpr std::array<D::SourceLocation,1> sources_86{{
    {"src/db/Migration.cpp",224},
}};
constexpr std::array<D::SourceLocation,2> sources_87{{
    {"src/db/Migration.cpp",89},
    {"src/db/TaiwanInstalledSkillCatalogImport.cpp",46},
}};
constexpr std::array<D::Column,7> columns_87{{
    {"dataset_id","技能資料集","參照原生資料來源的版本識別。",D::ValueKind::Text},
    {"source_record_index","實體來源序號","原始來源的實體列順序，不等同技能編號。",D::ValueKind::Integer},
    {"source_offset","來源位移","技能列在固定來源中的實體位元組位移。",D::ValueKind::Integer},
    {"record_sha256","技能原列雜湊","完整技能原列的 SHA-256。",D::ValueKind::Text},
    {"raw_record","原始技能列","完整 110 位元組原生技能資料，不用描述文字替代。",D::ValueKind::Binary},
    {"kind","技能種類","原生技能種類零至三。",D::ValueKind::Integer},
    {"definition_id","技能定義編號","種類內技能定義編號，與實體列序號分開。",D::ValueKind::Integer},
}};
constexpr std::array<D::SourceLocation,1> sources_88{{
    {"src/db/Migration.cpp",432},
}};
constexpr std::array<D::SourceLocation,1> sources_89{{
    {"src/db/Migration.cpp",420},
}};
constexpr std::array<D::SourceLocation,3> sources_90{{
    {"src/db/EffectiveGuildAnnouncementRepositoryDraft.cpp",157},
    {"src/db/SqliteOwnedGuildAnnouncementRepository.cpp",157},
    {"src/relations53/GuildAnnouncement53RepositoryDraft.cpp",169},
}};
constexpr std::array<D::SourceLocation,1> sources_91{{
    {"src/db/SqliteOwnedGuildMembershipRepository.cpp",187},
}};
constexpr std::array<D::SourceLocation,1> sources_92{{
    {"src/db/SqliteOwnedGuildMembershipRepository.cpp",177},
}};
constexpr std::array<D::SourceLocation,1> sources_93{{
    {"src/db/SqliteGuildRepository.cpp",75},
}};
constexpr std::array<D::SourceLocation,1> sources_94{{
    {"src/db/SqliteOwnedGuildMembershipRepository.cpp",921},
}};
constexpr std::array<D::SourceLocation,1> sources_95{{
    {"src/relations53/schema53.inc",3},
}};
constexpr std::array<D::SourceLocation,1> sources_96{{
    {"src/relations53/schema53.inc",37},
}};
constexpr std::array<D::SourceLocation,1> sources_97{{
    {"src/relations53/schema53.inc",11},
}};
constexpr std::array<D::SourceLocation,1> sources_98{{
    {"src/relations53/schema53.inc",19},
}};
constexpr std::array<D::SourceLocation,2> sources_99{{
    {"src/db/schema52.inc",6},
    {"src/relations53/schema52.inc",6},
}};
constexpr std::array<D::SourceLocation,1> sources_100{{
    {"src/db/SqliteGuildRepository.cpp",67},
}};
constexpr std::array<D::SourceLocation,1> sources_101{{
    {"src/db/SqliteOwnedInventoryRepository.cpp",293},
}};
constexpr std::array<D::Column,7> columns_101{{
    {"account_id","帳號編號","存放格所屬帳號。",D::ValueKind::Integer},
    {"character_id","角色編號","存放格所屬角色。",D::ValueKind::Integer},
    {"location_kind","存放位置類型","明確保存的位置類型文字，不猜新的類型。",D::ValueKind::Text},
    {"location_index","位置索引","該位置類型內的完整索引。",D::ValueKind::Integer},
    {"instance_id","道具實例","可為 NULL 的實例參照；空格必須保留 NULL。",D::ValueKind::Integer},
    {"quantity","數量","此格實例數量；空格為零。",D::ValueKind::Integer},
    {"instance_revision","實例版本","此格比對交換使用的實例版本。",D::ValueKind::Integer},
}};
constexpr std::array<D::SourceLocation,1> sources_102{{
    {"src/db/SqliteOwnedInventoryRepository.cpp",272},
}};
constexpr std::array<D::Column,10> columns_102{{
    {"account_id","帳號編號","背包根身分所屬帳號。",D::ValueKind::Integer},
    {"character_id","角色編號","背包根身分所屬完整共用角色。",D::ValueKind::Integer},
    {"root_slot","根角色欄位","觀測背包時的完整角色欄位。",D::ValueKind::Integer},
    {"root_profile","根角色原始資料","觀測背包時完整 40 位元組角色根資料。",D::ValueKind::Binary},
    {"root_created_at","根角色建立時間","保留背包觀測時角色根身分。",D::ValueKind::Text},
    {"root_name_codepage","根名稱編碼頁","保留背包觀測時名稱編碼。",D::ValueKind::Integer},
    {"root_streamer_privilege","根特殊顯示資格值","背包根身分保存值，不推導新權限。",D::ValueKind::Integer},
    {"revision","背包版本","整份背包比對交換版本。",D::ValueKind::Integer},
    {"source_sha256","背包來源雜湊","背包來源資格證據雜湊。",D::ValueKind::Text},
    {"source_record","背包來源紀錄","背包來源資格證據紀錄。",D::ValueKind::Text},
}};
constexpr std::array<D::SourceLocation,1> sources_103{{
    {"src/db/SqliteOwnedInventoryRepository.cpp",285},
}};
constexpr std::array<D::Column,5> columns_103{{
    {"id","道具實例編號","完整道具實例主鍵。",D::ValueKind::Integer},
    {"definition_key","道具定義鍵","既有共用道具定義鍵，不等同原生別名；尚無新分類權限。",D::ValueKind::Integer},
    {"stackable","可堆疊標記","原有零或一堆疊宣告。",D::ValueKind::Integer},
    {"acquisition_sha256","取得來源雜湊","實例取得來源的 SHA-256。",D::ValueKind::Text},
    {"acquisition_record","取得來源紀錄","實例取得來源紀錄，與雜湊共同唯一。",D::ValueKind::Text},
}};
constexpr std::array<D::SourceLocation,1> sources_104{{
    {"src/db/SqliteOwnedInventoryRepository.cpp",304},
}};
constexpr std::array<D::Column,9> columns_104{{
    {"instance_id","共用實例編號","原生別名所屬共用道具實例。",D::ValueKind::Integer},
    {"client_sha256","客戶端版本雜湊","原生別名適用的客戶端版本。",D::ValueKind::Text},
    {"profile","別名設定識別","原生別名設定識別，不是角色 40 位元組資料。",D::ValueKind::Text},
    {"source_sha256","別名來源雜湊","原生別名的完整來源雜湊。",D::ValueKind::Text},
    {"source_record","別名來源紀錄","原生別名的來源紀錄。",D::ValueKind::Text},
    {"native_key","原生道具鍵","此版本下的原生道具鍵。",D::ValueKind::Integer},
    {"native_slot","原生欄位","此版本下的原生欄位值，不推導裝備權限。",D::ValueKind::Integer},
    {"revision","別名版本","此別名持久版本。",D::ValueKind::Integer},
    {"record","原始道具別名資料","保存完整原生別名資料，不補未知位元組。",D::ValueKind::Binary},
}};
constexpr std::array<D::SourceLocation,1> sources_105{{
    {"src/db/SqliteOwnedPkRoomRepository.cpp",252},
}};
constexpr std::array<D::Column,3> columns_105{{
    {"singleton","唯一合約列","固定值一的功能結構合約列。",D::ValueKind::Integer},
    {"version","結構版本","明確安裝的功能結構版本。",D::ValueKind::Integer},
    {"design_id","功能設計合約","功能結構宣告的原設計識別。",D::ValueKind::Text},
}};
constexpr std::array<D::SourceLocation,1> sources_106{{
    {"src/db/SqliteOwnedPkRoomRepository.cpp",255},
}};
constexpr std::array<D::Column,3> columns_106{{
    {"room","PK 房間編號","此紀錄所屬的原持久房間。",D::ValueKind::Integer},
    {"document","完整持久文件","完整版本化文件；不以部分摘要取代原文。",D::ValueKind::Text},
    {"design_id","設計合約","此歷史文件的原自製合約識別。",D::ValueKind::Text},
}};
constexpr std::array<D::SourceLocation,1> sources_107{{
    {"src/db/SqliteOwnedPkRoomRepository.cpp",220},
}};
constexpr std::array<D::Column,3> columns_107{{
    {"singleton","唯一合約列","固定值一的功能結構合約列。",D::ValueKind::Integer},
    {"version","結構版本","明確安裝的功能結構版本。",D::ValueKind::Integer},
    {"design_id","功能設計合約","功能結構宣告的原設計識別。",D::ValueKind::Text},
}};
constexpr std::array<D::SourceLocation,1> sources_108{{
    {"src/db/SqliteOwnedPkRoomRepository.cpp",229},
}};
constexpr std::array<D::Column,7> columns_108{{
    {"room","PK 房間編號","成員鎖參照的原房間。",D::ValueKind::Integer},
    {"viewer","成員視角","固定兩位成員的零或一視角。",D::ValueKind::Integer},
    {"account","帳號編號","原入場帳號完整識別。",D::ValueKind::Integer},
    {"character","角色排他鎖","完整角色識別的唯一鎖，不是線路 handle。",D::ValueKind::Integer},
    {"session","連線排他鎖","原連線識別的唯一鎖。",D::ValueKind::Integer},
    {"world_generation","世界世代","原入場世界租約世代。",D::ValueKind::Integer},
    {"battle_generation","戰鬥世代","原入場戰鬥世代。",D::ValueKind::Integer},
}};
constexpr std::array<D::SourceLocation,1> sources_109{{
    {"src/db/SqliteOwnedPkRoomRepository.cpp",236},
}};
constexpr std::array<D::Column,5> columns_109{{
    {"room","PK 房間編號","封包所屬原房間。",D::ValueKind::Integer},
    {"revision","輸出版本","此輸出的房間版本。",D::ValueKind::Integer},
    {"viewer","收件視角","零或一的成員視角。",D::ValueKind::Integer},
    {"logical","PK 原始邏輯封包","完整已保存邏輯封包；不可改寫為玩家文字攻略。",D::ValueKind::Binary},
    {"submitted","已提交標記","持久提交標記；不自行等同遠端 ACK 或渲染完成。",D::ValueKind::Integer},
}};
constexpr std::array<D::SourceLocation,1> sources_110{{
    {"src/db/SqliteOwnedPkRoomRepository.cpp",247},
}};
constexpr std::array<D::Column,3> columns_110{{
    {"room","PK 房間編號","此紀錄所屬的原持久房間。",D::ValueKind::Integer},
    {"document","完整持久文件","完整版本化文件；不以部分摘要取代原文。",D::ValueKind::Text},
    {"revision","回合版本","持久回合文件版本。",D::ValueKind::Integer},
}};
constexpr std::array<D::SourceLocation,1> sources_111{{
    {"src/db/SqliteOwnedPkRoomRepository.cpp",223},
}};
constexpr std::array<D::Column,6> columns_111{{
    {"id","PK 房間編號","不可隨意重用的房間自增識別。",D::ValueKind::Integer},
    {"state","房間狀態","reserved、active、finished 或 abandoned 的既有狀態。",D::ValueKind::Text},
    {"readset","完整入場觀測","房間保留的完整來源讀集合文件。",D::ValueKind::Text},
    {"checkpoint","戰鬥檢查點","原房間的持久戰鬥檢查點文件。",D::ValueKind::Text},
    {"revision","房間版本","房間狀態與輸出的正整數版本。",D::ValueKind::Integer},
    {"design_id","房間設計合約","原 PK 功能的設計來源識別。",D::ValueKind::Text},
}};
constexpr std::array<D::SourceLocation,1> sources_112{{
    {"src/db/SqliteOwnedPkRoomRepository.cpp",244},
}};
constexpr std::array<D::Column,3> columns_112{{
    {"singleton","唯一合約列","固定值一的功能結構合約列。",D::ValueKind::Integer},
    {"version","結構版本","明確安裝的功能結構版本。",D::ValueKind::Integer},
    {"design_id","功能設計合約","功能結構宣告的原設計識別。",D::ValueKind::Text},
}};
constexpr std::array<D::SourceLocation,1> sources_113{{
    {"src/db/SqliteOwnedPkRoomRepository.cpp",261},
}};
constexpr std::array<D::Column,3> columns_113{{
    {"singleton","唯一合約列","固定值一的功能結構合約列。",D::ValueKind::Integer},
    {"version","結構版本","明確安裝的功能結構版本。",D::ValueKind::Integer},
    {"design_id","功能設計合約","功能結構宣告的原設計識別。",D::ValueKind::Text},
}};
constexpr std::array<D::SourceLocation,1> sources_114{{
    {"src/db/SqliteOwnedPkRoomRepository.cpp",264},
}};
constexpr std::array<D::Column,3> columns_114{{
    {"room","PK 房間編號","此紀錄所屬的原持久房間。",D::ValueKind::Integer},
    {"document","完整持久文件","完整版本化文件；不以部分摘要取代原文。",D::ValueKind::Text},
    {"design_id","設計合約","此歷史文件的原自製合約識別。",D::ValueKind::Text},
}};
constexpr std::array<D::SourceLocation,1> sources_115{{
    {"src/db/NativeFruitQuestSources.cpp",37},
}};
constexpr std::array<D::SourceLocation,1> sources_116{{
    {"src/db/Migration.cpp",44},
}};
constexpr std::array<D::Column,8> columns_116{{
    {"id","角色編號","完整共用角色主鍵，不截斷成客戶端 handle。",D::ValueKind::Integer},
    {"account_id","所屬帳號","參照帳號的角色擁有者。",D::ValueKind::Integer},
    {"slot","角色欄位","帳號內角色欄位，既有約束為零或一。",D::ValueKind::Integer},
    {"profile","原始角色資料","完整 40 位元組角色資料；未知欄位不拆解或補零。",D::ValueKind::Binary},
    {"name_bytes","原始角色名稱","保留既有編碼的名稱位元組，不直接轉成 UTF-8。",D::ValueKind::Binary},
    {"created_at","角色建立時間","角色根身分保存的建立時間文字。",D::ValueKind::Text},
    {"name_codepage","名稱編碼頁","保存編碼頁識別；不以目前作業系統編碼取代。",D::ValueKind::Integer},
    {"streamer_privilege","特殊顯示資格值","原保存的零至三資格值；不推導未恢復的玩法權限。",D::ValueKind::Integer},
}};
constexpr std::array<D::SourceLocation,1> sources_117{{
    {"src/db/Migration.cpp",56},
}};
constexpr std::array<D::Column,6> columns_117{{
    {"character_id","角色編號","此權威位置所屬的共用角色。",D::ValueKind::Integer},
    {"area","區域編號","已保存位置的區域值。",D::ValueKind::Integer},
    {"scene","場景編號","已保存位置的場景值。",D::ValueKind::Integer},
    {"x","橫座標","已保存位置的完整橫座標。",D::ValueKind::Integer},
    {"y","縱座標","已保存位置的完整縱座標。",D::ValueKind::Integer},
    {"revision","位置版本","位置比對交換使用的正整數版本。",D::ValueKind::Integer},
}};
constexpr std::array<D::SourceLocation,1> sources_118{{
    {"src/db/SqliteMigrationManager.cpp",11},
}};
constexpr std::array<D::Column,4> columns_118{{
    {"version","遷移版本","已套用遷移的連續版本。",D::ValueKind::Integer},
    {"name","遷移名稱","原編譯遷移名稱。",D::ValueKind::Text},
    {"sql_text","原始 SQLite 遷移 SQL","保存不可變來源 SQL 原文，不能改寫成 MySQL DDL。",D::ValueKind::Text},
    {"applied_at","套用時間","原 SQLite 保存的遷移套用時間文字。",D::ValueKind::Text},
}};
constexpr std::array<D::SourceLocation,1> sources_119{{
    {"src/db/SqliteSkillBookLearningRepository.cpp",208},
}};
constexpr std::array<D::SourceLocation,1> sources_120{{
    {"src/db/SqliteBankAccessRepository.cpp",7},
}};
constexpr std::array<D::SourceLocation,1> sources_121{{
    {"src/db/SqliteWorldDisplayRepository.cpp",21},
}};
constexpr std::array<D::SourceLocation,1> sources_122{{
    {"src/db/SqliteWorldDisplayRepository.cpp",34},
}};
constexpr std::array<D::Table,123> dictionary{{
    {"account_native_character_summaries","帳號原生角色摘要快照","保留客戶端交付的帳號原生角色摘要快照；快照是交付證據，不是第二份角色、背包或裝備權威。",D::Storage::NativeDelivery,D::Domain::Account,D::Installation::ExplicitExtension,sources_0,std::span<const D::Column>{}},
    {"account_native_character_summary_rows","帳號原生角色摘要列","保留客戶端交付的帳號原生角色摘要列；快照是交付證據，不是第二份角色、背包或裝備權威。",D::Storage::NativeDelivery,D::Domain::Account,D::Installation::ExplicitExtension,sources_1,std::span<const D::Column>{}},
    {"account_native_snapshots","帳號原生交付封包快照","保留客戶端交付的帳號原生交付封包快照；快照是交付證據，不是第二份角色、背包或裝備權威。",D::Storage::NativeDelivery,D::Domain::Account,D::Installation::ExplicitExtension,sources_2,std::span<const D::Column>{}},
    {"accounts","帳號與密碼雜湊","保存登入名稱、密碼雜湊與帳號建立時間。",D::Storage::Authoritative,D::Domain::Account,D::Installation::VersionedMigration,sources_3,columns_3},
    {"battle_checkpoints","戰鬥復原檢查點","保留已執行操作的戰鬥復原檢查點；保留完整收據與版本，歷史本身不授予新的操作權限。",D::Storage::AuditHistory,D::Domain::Battle,D::Installation::VersionedMigration,sources_4,std::span<const D::Column>{}},
    {"battle_reservations","戰鬥資源版本預留","持久保存戰鬥資源版本預留；原有約束與寫入資格由來源 repository 定義。",D::Storage::Authoritative,D::Domain::Battle,D::Installation::VersionedMigration,sources_5,std::span<const D::Column>{}},
    {"battle_settlements","戰鬥結算歷史","保留已執行操作的戰鬥結算歷史；保留完整收據與版本，歷史本身不授予新的操作權限。",D::Storage::AuditHistory,D::Domain::Battle,D::Installation::VersionedMigration,sources_6,std::span<const D::Column>{}},
    {"beast_bank_schema_0085","神獸倉庫結構合約","宣告明確安裝的功能合約：神獸倉庫結構合約；存在宣告不表示功能已啟用。",D::Storage::SchemaMetadata,D::Domain::Companion,D::Installation::ExplicitExtension,sources_7,std::span<const D::Column>{}},
    {"beast_custody_schema_0085","神獸寫入資格結構合約","宣告明確安裝的功能合約：神獸寫入資格結構合約；存在宣告不表示功能已啟用。",D::Storage::SchemaMetadata,D::Domain::Companion,D::Installation::ExplicitExtension,sources_8,std::span<const D::Column>{}},
    {"beast_discard_schema_0085","神獸丟棄結構合約","宣告明確安裝的功能合約：神獸丟棄結構合約；存在宣告不表示功能已啟用。",D::Storage::SchemaMetadata,D::Domain::Companion,D::Installation::ExplicitExtension,sources_9,std::span<const D::Column>{}},
    {"beast_equipment_schema_0085","神獸裝備結構合約","宣告明確安裝的功能合約：神獸裝備結構合約；存在宣告不表示功能已啟用。",D::Storage::SchemaMetadata,D::Domain::Companion,D::Installation::ExplicitExtension,sources_10,std::span<const D::Column>{}},
    {"beast_selection_schema_0085","神獸選擇結構合約","宣告明確安裝的功能合約：神獸選擇結構合約；存在宣告不表示功能已啟用。",D::Storage::SchemaMetadata,D::Domain::Companion,D::Installation::ExplicitExtension,sources_11,std::span<const D::Column>{}},
    {"character_armor_slot_metadata","角色防具格中介資料","持久保存角色防具格中介資料；原有約束與寫入資格由來源 repository 定義。",D::Storage::Authoritative,D::Domain::Inventory,D::Installation::VersionedMigration,sources_12,std::span<const D::Column>{}},
    {"character_bank_armor_metadata","角色倉庫防具中介資料","持久保存角色倉庫防具中介資料；原有約束與寫入資格由來源 repository 定義。",D::Storage::Authoritative,D::Domain::Inventory,D::Installation::VersionedMigration,sources_13,std::span<const D::Column>{}},
    {"character_bank_armor_receipts","角色倉庫防具操作收據","保留已執行操作的角色倉庫防具操作收據；保留完整收據與版本，歷史本身不授予新的操作權限。",D::Storage::AuditHistory,D::Domain::Inventory,D::Installation::VersionedMigration,sources_14,std::span<const D::Column>{}},
    {"character_bank_balances","角色倉庫餘額","持久保存角色倉庫餘額；原有約束與寫入資格由來源 repository 定義。",D::Storage::Authoritative,D::Domain::Inventory,D::Installation::ExplicitExtension,sources_15,std::span<const D::Column>{}},
    {"character_bank_beast_metadata_0085","角色倉庫神獸中介資料","持久保存角色倉庫神獸中介資料；原有約束與寫入資格由來源 repository 定義。",D::Storage::Authoritative,D::Domain::Companion,D::Installation::ExplicitExtension,sources_16,std::span<const D::Column>{}},
    {"character_bank_beast_receipts_0085","角色倉庫神獸操作收據","保留已執行操作的角色倉庫神獸操作收據；保留完整收據與版本，歷史本身不授予新的操作權限。",D::Storage::AuditHistory,D::Domain::Companion,D::Installation::ExplicitExtension,sources_17,std::span<const D::Column>{}},
    {"character_bank_foreign_metadata","角色倉庫外來物件中介資料","持久保存角色倉庫外來物件中介資料；原有約束與寫入資格由來源 repository 定義。",D::Storage::Authoritative,D::Domain::Inventory,D::Installation::VersionedMigration,sources_18,std::span<const D::Column>{}},
    {"character_bank_foreign_receipts","角色倉庫外來物件操作收據","保留已執行操作的角色倉庫外來物件操作收據；保留完整收據與版本，歷史本身不授予新的操作權限。",D::Storage::AuditHistory,D::Domain::Inventory,D::Installation::VersionedMigration,sources_19,std::span<const D::Column>{}},
    {"character_bank_item_receipts","角色倉庫物品操作收據","保留已執行操作的角色倉庫物品操作收據；保留完整收據與版本，歷史本身不授予新的操作權限。",D::Storage::AuditHistory,D::Domain::Inventory,D::Installation::VersionedMigration,sources_20,std::span<const D::Column>{}},
    {"character_bank_item_slots","角色倉庫物品格","持久保存角色倉庫物品格；原有約束與寫入資格由來源 repository 定義。",D::Storage::Authoritative,D::Domain::Inventory,D::Installation::VersionedMigration,sources_21,std::span<const D::Column>{}},
    {"character_bank_mixed_receipts","角色混合倉庫操作收據","保留已執行操作的角色混合倉庫操作收據；保留完整收據與版本，歷史本身不授予新的操作權限。",D::Storage::AuditHistory,D::Domain::Inventory,D::Installation::VersionedMigration,sources_22,std::span<const D::Column>{}},
    {"character_bank_receipts","角色倉庫金錢操作收據","保留已執行操作的角色倉庫金錢操作收據；保留完整收據與版本，歷史本身不授予新的操作權限。",D::Storage::AuditHistory,D::Domain::Inventory,D::Installation::ExplicitExtension,sources_23,std::span<const D::Column>{}},
    {"character_beast_discard_receipts_0085","角色神獸丟棄收據","保留已執行操作的角色神獸丟棄收據；保留完整收據與版本，歷史本身不授予新的操作權限。",D::Storage::AuditHistory,D::Domain::Companion,D::Installation::ExplicitExtension,sources_24,std::span<const D::Column>{}},
    {"character_beast_selection_0085","角色神獸選擇版本","持久保存角色神獸選擇版本；原有約束與寫入資格由來源 repository 定義。",D::Storage::Authoritative,D::Domain::Companion,D::Installation::ExplicitExtension,sources_25,std::span<const D::Column>{}},
    {"character_beast_snapshot_custody","角色神獸快照寫入資格","持久保存角色神獸快照寫入資格；原有約束與寫入資格由來源 repository 定義。",D::Storage::Authoritative,D::Domain::Companion,D::Installation::ExplicitExtension,sources_26,std::span<const D::Column>{}},
    {"character_blacklist_entries","角色黑名單與保留列號","持久保存角色黑名單與保留列號；原有約束與寫入資格由來源 repository 定義。",D::Storage::Authoritative,D::Domain::Character,D::Installation::ExplicitExtension,sources_27,std::span<const D::Column>{}},
    {"character_daily_quest_lists","角色日常任務清單","持久保存角色日常任務清單；原有約束與寫入資格由來源 repository 定義。",D::Storage::Authoritative,D::Domain::Quest,D::Installation::VersionedMigration,sources_28,std::span<const D::Column>{}},
    {"character_deities","角色神獸持有列","持久保存角色神獸持有列；原有約束與寫入資格由來源 repository 定義。",D::Storage::Authoritative,D::Domain::Companion,D::Installation::VersionedMigration,sources_29,std::span<const D::Column>{}},
    {"character_deity_selection","角色目前神獸選擇","持久保存角色目前神獸選擇；原有約束與寫入資格由來源 repository 定義。",D::Storage::Authoritative,D::Domain::Companion,D::Installation::VersionedMigration,sources_30,std::span<const D::Column>{}},
    {"character_experience","角色累積經驗","持久保存角色累積經驗；原有約束與寫入資格由來源 repository 定義。",D::Storage::Authoritative,D::Domain::Character,D::Installation::VersionedMigration,sources_31,std::span<const D::Column>{}},
    {"character_fruit_quest_balances","角色水果任務額度","持久保存角色水果任務額度；原有約束與寫入資格由來源 repository 定義。",D::Storage::Authoritative,D::Domain::Quest,D::Installation::VersionedMigration,sources_32,std::span<const D::Column>{}},
    {"character_fruit_quest_progress","角色水果任務進度","持久保存角色水果任務進度；原有約束與寫入資格由來源 repository 定義。",D::Storage::Authoritative,D::Domain::Quest,D::Installation::VersionedMigration,sources_33,std::span<const D::Column>{}},
    {"character_native_equipment_snapshots","角色原生裝備交付快照","保留客戶端交付的角色原生裝備交付快照；快照是交付證據，不是第二份角色、背包或裝備權威。",D::Storage::NativeDelivery,D::Domain::Character,D::Installation::ExplicitExtension,sources_34,columns_34},
    {"character_native_world_entries","角色原生進場交付快照","保留客戶端交付的角色原生進場交付快照；快照是交付證據，不是第二份角色、背包或裝備權威。",D::Storage::NativeDelivery,D::Domain::Character,D::Installation::ExplicitExtension,sources_35,std::span<const D::Column>{}},
    {"character_owned_instance_discard_receipts","角色道具實例丟棄收據","保留已執行操作的角色道具實例丟棄收據；保留完整收據與版本，歷史本身不授予新的操作權限。",D::Storage::AuditHistory,D::Domain::Character,D::Installation::VersionedMigration,sources_36,std::span<const D::Column>{}},
    {"character_owned_instance_trade_receipts","角色道具實例交易收據","保留已執行操作的角色道具實例交易收據；保留完整收據與版本，歷史本身不授予新的操作權限。",D::Storage::AuditHistory,D::Domain::Inventory,D::Installation::VersionedMigration,sources_37,std::span<const D::Column>{}},
    {"character_pet2_slots","角色寵物持有格","持久保存角色寵物持有格；原有約束與寫入資格由來源 repository 定義。",D::Storage::Authoritative,D::Domain::Companion,D::Installation::VersionedMigration,sources_38,std::span<const D::Column>{}},
    {"character_pet_slots_next","寵物表重建暫存資料","migration37 重建寵物表時使用的暫存名稱，成功後改名；不是現行已安裝表數。",D::Storage::MigrationTransient,D::Domain::Companion,D::Installation::TransientMigration,sources_39,std::span<const D::Column>{}},
    {"character_player_appearance_snapshots","角色外觀邏輯封包快照","保留客戶端交付的角色外觀邏輯封包快照；快照是交付證據，不是第二份角色、背包或裝備權威。",D::Storage::NativeDelivery,D::Domain::Character,D::Installation::VersionedMigration,sources_40,std::span<const D::Column>{}},
    {"character_quest_journals","角色任務持久紀錄","持久保存角色任務持久紀錄；原有約束與寫入資格由來源 repository 定義。",D::Storage::Authoritative,D::Domain::Quest,D::Installation::VersionedMigration,sources_41,std::span<const D::Column>{}},
    {"character_resources","角色目前與最大生命魔力","持久保存角色目前與最大生命魔力；原有約束與寫入資格由來源 repository 定義。",D::Storage::Authoritative,D::Domain::Character,D::Installation::VersionedMigration,sources_42,columns_42},
    {"character_role_auxiliary_snapshots","角色輔助能力封包快照","保留客戶端交付的角色輔助能力封包快照；快照是交付證據，不是第二份角色、背包或裝備權威。",D::Storage::NativeDelivery,D::Domain::Character,D::Installation::VersionedMigration,sources_43,std::span<const D::Column>{}},
    {"character_role_snapshots","角色能力邏輯封包快照","保留客戶端交付的角色能力邏輯封包快照；快照是交付證據，不是第二份角色、背包或裝備權威。",D::Storage::NativeDelivery,D::Domain::Character,D::Installation::VersionedMigration,sources_44,std::span<const D::Column>{}},
    {"character_role_text","角色次要文字與編碼","持久保存角色次要文字與編碼；原有約束與寫入資格由來源 repository 定義。",D::Storage::Authoritative,D::Domain::Character,D::Installation::VersionedMigration,sources_45,std::span<const D::Column>{}},
    {"character_teleport_gem_metadata","角色傳送寶石中介資料","持久保存角色傳送寶石中介資料；原有約束與寫入資格由來源 repository 定義。",D::Storage::Authoritative,D::Domain::Inventory,D::Installation::VersionedMigration,sources_46,std::span<const D::Column>{}},
    {"character_trade_receipts","角色金錢交易收據","保留已執行操作的角色金錢交易收據；保留完整收據與版本，歷史本身不授予新的操作權限。",D::Storage::AuditHistory,D::Domain::Inventory,D::Installation::ExplicitExtension,sources_47,std::span<const D::Column>{}},
    {"character_trade_wallets","角色交易錢包","持久保存角色交易錢包；原有約束與寫入資格由來源 repository 定義。",D::Storage::Authoritative,D::Domain::Inventory,D::Installation::ExplicitExtension,sources_48,std::span<const D::Column>{}},
    {"character_weapon_slot_metadata","角色武器格中介資料","持久保存角色武器格中介資料；原有約束與寫入資格由來源 repository 定義。",D::Storage::Authoritative,D::Domain::Inventory,D::Installation::VersionedMigration,sources_49,std::span<const D::Column>{}},
    {"characters","舊測試角色資料","舊 fixture 角色模型；與 recovered_characters 共用權威角色身分分開。",D::Storage::Diagnostic,D::Domain::Character,D::Installation::VersionedMigration,sources_50,std::span<const D::Column>{}},
    {"deity_skill_activation_headers","神獸技能啟用版本與原列","持久保存神獸技能啟用版本與原列；原有約束與寫入資格由來源 repository 定義。",D::Storage::Authoritative,D::Domain::Companion,D::Installation::ExplicitExtension,sources_51,std::span<const D::Column>{}},
    {"deity_skill_activation_links","神獸技能啟用事件連結","持久保存神獸技能啟用事件連結；原有約束與寫入資格由來源 repository 定義。",D::Storage::Authoritative,D::Domain::Companion,D::Installation::ExplicitExtension,sources_52,std::span<const D::Column>{}},
    {"diagnostic_inventory_slots","舊診斷背包格","保存舊診斷用途的舊診斷背包格；不得混稱原生玩法規則或正式玩家權限。",D::Storage::Diagnostic,D::Domain::Inventory,D::Installation::VersionedMigration,sources_53,std::span<const D::Column>{}},
    {"diagnostic_quest_journal","舊診斷任務紀錄","保存舊診斷用途的舊診斷任務紀錄；不得混稱原生玩法規則或正式玩家權限。",D::Storage::Diagnostic,D::Domain::Quest,D::Installation::VersionedMigration,sources_54,std::span<const D::Column>{}},
    {"diagnostic_town_guide_progress","舊城鎮引導進度","保存舊診斷用途的舊城鎮引導進度；不得混稱原生玩法規則或正式玩家權限。",D::Storage::Diagnostic,D::Domain::Quest,D::Installation::VersionedMigration,sources_55,std::span<const D::Column>{}},
    {"diagnostic_town_guide_reward","舊城鎮引導獎勵收據","保存舊診斷用途的舊城鎮引導獎勵收據；不得混稱原生玩法規則或正式玩家權限。",D::Storage::Diagnostic,D::Domain::Quest,D::Installation::VersionedMigration,sources_56,std::span<const D::Column>{}},
    {"native_armor_rows","原生防具定義列","保存原生防具定義原列與來源；與武器及一般道具分表，不等同新權威平衡設定。",D::Storage::NativeSource,D::Domain::Inventory,D::Installation::VersionedMigration,sources_57,std::span<const D::Column>{}},
    {"native_armor_sources","原生防具來源","保留原生資源來源的原生防具來源；完整原始位元組及來源不得改寫，不直接授予玩家權限。",D::Storage::NativeSource,D::Domain::Inventory,D::Installation::VersionedMigration,sources_58,std::span<const D::Column>{}},
    {"native_companion_metadata","原生同伴中介資料","保留原生資源來源的原生同伴中介資料；完整原始位元組及來源不得改寫，不直接授予玩家權限。",D::Storage::NativeSource,D::Domain::Companion,D::Installation::VersionedMigration,sources_59,std::span<const D::Column>{}},
    {"native_daily_quest_parsed","原生日常任務解析列","保留原生資源來源的原生日常任務解析列；完整原始位元組及來源不得改寫，不直接授予玩家權限。",D::Storage::NativeSource,D::Domain::Quest,D::Installation::VersionedMigration,sources_60,std::span<const D::Column>{}},
    {"native_daily_quest_source","原生日常任務來源","保留原生資源來源的原生日常任務來源；完整原始位元組及來源不得改寫，不直接授予玩家權限。",D::Storage::NativeSource,D::Domain::Quest,D::Installation::VersionedMigration,sources_61,std::span<const D::Column>{}},
    {"native_data_sources","原生資料集來源與雜湊","保存資料集完整來源、解碼與映像雜湊以及原生載入查找註記。",D::Storage::NativeSource,D::Domain::NativeCatalog,D::Installation::VersionedMigration,sources_62,columns_62},
    {"native_delivery_snapshot_schema","原生交付快照結構合約","宣告明確安裝的功能合約：原生交付快照結構合約；存在宣告不表示功能已啟用。",D::Storage::SchemaMetadata,D::Domain::NativeCatalog,D::Installation::ExplicitExtension,sources_63,std::span<const D::Column>{}},
    {"native_enemy_display_catalog","原生敵人顯示目錄","保留原生資源來源的原生敵人顯示目錄；完整原始位元組及來源不得改寫，不直接授予玩家權限。",D::Storage::NativeSource,D::Domain::NativeCatalog,D::Installation::VersionedMigration,sources_64,std::span<const D::Column>{}},
    {"native_map_catalog","原生地圖目錄","保留原生資源來源的原生地圖目錄；完整原始位元組及來源不得改寫，不直接授予玩家權限。",D::Storage::NativeSource,D::Domain::NativeCatalog,D::Installation::VersionedMigration,sources_65,std::span<const D::Column>{}},
    {"native_map_item_rows","原生地圖物件列","保留原生資源來源的原生地圖物件列；完整原始位元組及來源不得改寫，不直接授予玩家權限。",D::Storage::NativeSource,D::Domain::Inventory,D::Installation::VersionedMigration,sources_66,std::span<const D::Column>{}},
    {"native_map_item_sources","原生地圖物件來源","保留原生資源來源的原生地圖物件來源；完整原始位元組及來源不得改寫，不直接授予玩家權限。",D::Storage::NativeSource,D::Domain::Inventory,D::Installation::VersionedMigration,sources_67,std::span<const D::Column>{}},
    {"native_med02_recovery_declarations","MED02 原生恢復宣告","保留原生資源來源的MED02 原生恢復宣告；完整原始位元組及來源不得改寫，不直接授予玩家權限。",D::Storage::NativeSource,D::Domain::NativeCatalog,D::Installation::VersionedMigration,sources_68,std::span<const D::Column>{}},
    {"native_multi_message_rows","原生多訊息實體列","保留原生資源來源的原生多訊息實體列；完整原始位元組及來源不得改寫，不直接授予玩家權限。",D::Storage::NativeSource,D::Domain::NativeCatalog,D::Installation::VersionedMigration,sources_69,std::span<const D::Column>{}},
    {"native_multi_message_sources","原生多訊息來源","保留原生資源來源的原生多訊息來源；完整原始位元組及來源不得改寫，不直接授予玩家權限。",D::Storage::NativeSource,D::Domain::NativeCatalog,D::Installation::VersionedMigration,sources_70,std::span<const D::Column>{}},
    {"native_multi_messages","原生多訊息內容","保留原生資源來源的原生多訊息內容；完整原始位元組及來源不得改寫，不直接授予玩家權限。",D::Storage::NativeSource,D::Domain::NativeCatalog,D::Installation::VersionedMigration,sources_71,std::span<const D::Column>{}},
    {"native_npc_display_rows","原生 NPC 顯示列","保留原生資源來源的原生 NPC 顯示列；完整原始位元組及來源不得改寫，不直接授予玩家權限。",D::Storage::NativeSource,D::Domain::NativeCatalog,D::Installation::VersionedMigration,sources_72,std::span<const D::Column>{}},
    {"native_npc_display_sources","原生 NPC 顯示來源","保留原生資源來源的原生 NPC 顯示來源；完整原始位元組及來源不得改寫，不直接授予玩家權限。",D::Storage::NativeSource,D::Domain::NativeCatalog,D::Installation::VersionedMigration,sources_73,std::span<const D::Column>{}},
    {"native_pet1_metadata","第一代原生寵物中介資料","保留原生資源來源的第一代原生寵物中介資料；完整原始位元組及來源不得改寫，不直接授予玩家權限。",D::Storage::NativeSource,D::Domain::Companion,D::Installation::VersionedMigration,sources_74,std::span<const D::Column>{}},
    {"native_pet2_category_rows","第二代寵物分類列","保留原生資源來源的第二代寵物分類列；完整原始位元組及來源不得改寫，不直接授予玩家權限。",D::Storage::NativeSource,D::Domain::Companion,D::Installation::VersionedMigration,sources_75,std::span<const D::Column>{}},
    {"native_pet2_category_source","第二代寵物分類來源","保留原生資源來源的第二代寵物分類來源；完整原始位元組及來源不得改寫，不直接授予玩家權限。",D::Storage::NativeSource,D::Domain::Companion,D::Installation::VersionedMigration,sources_76,std::span<const D::Column>{}},
    {"native_quest_definitions","原生任務定義","保留原生資源來源的原生任務定義；完整原始位元組及來源不得改寫，不直接授予玩家權限。",D::Storage::NativeSource,D::Domain::Quest,D::Installation::VersionedMigration,sources_77,std::span<const D::Column>{}},
    {"native_quest_descriptions","原生任務描述","保留原生資源來源的原生任務描述；完整原始位元組及來源不得改寫，不直接授予玩家權限。",D::Storage::NativeSource,D::Domain::Quest,D::Installation::VersionedMigration,sources_78,std::span<const D::Column>{}},
    {"native_quest_requirement_display","原生任務需求顯示","保留原生資源來源的原生任務需求顯示；完整原始位元組及來源不得改寫，不直接授予玩家權限。",D::Storage::NativeSource,D::Domain::Quest,D::Installation::VersionedMigration,sources_79,std::span<const D::Column>{}},
    {"native_raw_item_source_rows","原生道具 SPI 歷史來源列","保存歷史 SPI 中 PetRoom 6177 至 6200 的來源子集；不是完整一般道具目錄或權威平衡設定。",D::Storage::NativeSource,D::Domain::Inventory,D::Installation::ExplicitExtension,sources_80,std::span<const D::Column>{}},
    {"native_raw_item_source_sets","原生道具 SPI 歷史來源集合","保留歷史 SPI 的 PetRoom 來源子集與雜湊；不是完整一般道具目錄或權威平衡設定。",D::Storage::NativeSource,D::Domain::Inventory,D::Installation::ExplicitExtension,sources_81,std::span<const D::Column>{}},
    {"native_raw_resource_source_rows","原生資源來源實體列","保留原生資源來源的原生資源來源實體列；完整原始位元組及來源不得改寫，不直接授予玩家權限。",D::Storage::NativeSource,D::Domain::NativeCatalog,D::Installation::ExplicitExtension,sources_82,std::span<const D::Column>{}},
    {"native_raw_resource_source_sets","原生資源完整來源集合","保留原生資源來源的原生資源完整來源集合；完整原始位元組及來源不得改寫，不直接授予玩家權限。",D::Storage::NativeSource,D::Domain::NativeCatalog,D::Installation::ExplicitExtension,sources_83,std::span<const D::Column>{}},
    {"native_skill_book_bindings","技能書與技能定義綁定","保留原生資源來源的技能書與技能定義綁定；完整原始位元組及來源不得改寫，不直接授予玩家權限。",D::Storage::NativeSource,D::Domain::Inventory,D::Installation::VersionedMigration,sources_84,std::span<const D::Column>{}},
    {"native_skill_book_source_records","原生技能書完整來源紀錄","保留原生資源來源的原生技能書完整來源紀錄；完整原始位元組及來源不得改寫，不直接授予玩家權限。",D::Storage::NativeSource,D::Domain::Inventory,D::Installation::ExplicitExtension,sources_85,std::span<const D::Column>{}},
    {"native_skill_books","原生技能書目錄","保留原生資源來源的原生技能書目錄；完整原始位元組及來源不得改寫，不直接授予玩家權限。",D::Storage::NativeSource,D::Domain::Inventory,D::Installation::VersionedMigration,sources_86,std::span<const D::Column>{}},
    {"native_skill_catalog","原生技能定義列","保存版本限定的 110 位元組技能原列、定義鍵、實體序號與雜湊；不是可調平衡參數表。",D::Storage::NativeSource,D::Domain::NativeCatalog,D::Installation::VersionedMigration,sources_87,columns_87},
    {"native_weapon_rows","原生武器定義列","保存原生武器定義原列與來源；與防具及一般道具分表，不等同新權威平衡設定。",D::Storage::NativeSource,D::Domain::Inventory,D::Installation::VersionedMigration,sources_88,std::span<const D::Column>{}},
    {"native_weapon_sources","原生武器來源","保留原生資源來源的原生武器來源；完整原始位元組及來源不得改寫，不直接授予玩家權限。",D::Storage::NativeSource,D::Domain::Inventory,D::Installation::VersionedMigration,sources_89,std::span<const D::Column>{}},
    {"owned_guild_announcements_0078","公會公告","持久保存公會公告；原有約束與寫入資格由來源 repository 定義。",D::Storage::Authoritative,D::Domain::Guild,D::Installation::ConditionalMigration,sources_90,std::span<const D::Column>{}},
    {"owned_guild_applications_0078","公會加入申請","持久保存公會加入申請；原有約束與寫入資格由來源 repository 定義。",D::Storage::Authoritative,D::Domain::Guild,D::Installation::VersionedMigration,sources_91,std::span<const D::Column>{}},
    {"owned_guild_governance_0078","公會治理與建立者資格","持久保存公會治理與建立者資格；原有約束與寫入資格由來源 repository 定義。",D::Storage::Authoritative,D::Domain::Guild,D::Installation::VersionedMigration,sources_92,std::span<const D::Column>{}},
    {"owned_guild_members","公會成員","持久保存公會成員；原有約束與寫入資格由來源 repository 定義。",D::Storage::Authoritative,D::Domain::Guild,D::Installation::VersionedMigration,sources_93,std::span<const D::Column>{}},
    {"owned_guild_officers_0082","公會幹部職務","持久保存公會幹部職務；原有約束與寫入資格由來源 repository 定義。",D::Storage::Authoritative,D::Domain::Guild,D::Installation::ConditionalMigration,sources_94,std::span<const D::Column>{}},
    {"owned_guild_relation_catalog_0084","公會關係目錄與線路號分配","持久保存公會關係目錄與線路號分配；原有約束與寫入資格由來源 repository 定義。",D::Storage::Authoritative,D::Domain::Guild,D::Installation::ConditionalMigration,sources_95,std::span<const D::Column>{}},
    {"owned_guild_relation_events_0084","公會關係操作事件","保留已執行操作的公會關係操作事件；保留完整收據與版本，歷史本身不授予新的操作權限。",D::Storage::AuditHistory,D::Domain::Guild,D::Installation::ConditionalMigration,sources_96,std::span<const D::Column>{}},
    {"owned_guild_relation_wire_ids_0084","公會關係穩定線路號","持久保存公會關係穩定線路號；原有約束與寫入資格由來源 repository 定義。",D::Storage::Authoritative,D::Domain::Guild,D::Installation::ConditionalMigration,sources_97,std::span<const D::Column>{}},
    {"owned_guild_relations_0084","公會雙方關係狀態","持久保存公會雙方關係狀態；原有約束與寫入資格由來源 repository 定義。",D::Storage::Authoritative,D::Domain::Guild,D::Installation::ConditionalMigration,sources_98,std::span<const D::Column>{}},
    {"owned_guild_successions_0083","公會繼任歷史","保留已執行操作的公會繼任歷史；保留完整收據與版本，歷史本身不授予新的操作權限。",D::Storage::AuditHistory,D::Domain::Guild,D::Installation::ConditionalMigration,sources_99,std::span<const D::Column>{}},
    {"owned_guilds","公會身分與保留世代","持久保存公會身分與保留世代；原有約束與寫入資格由來源 repository 定義。",D::Storage::Authoritative,D::Domain::Guild,D::Installation::VersionedMigration,sources_100,std::span<const D::Column>{}},
    {"owned_inventory_cells","共用物品存放格","保存角色各存放格的實例參照、數量與版本；空格 NULL 與零值必須區分。",D::Storage::Authoritative,D::Domain::Inventory,D::Installation::ExplicitExtension,sources_101,columns_101},
    {"owned_inventory_headers","角色背包根身分與版本","持久保存角色背包根身分與版本；原有約束與寫入資格由來源 repository 定義。",D::Storage::Authoritative,D::Domain::Inventory,D::Installation::ExplicitExtension,sources_102,columns_102},
    {"owned_item_instances","共用道具實例","保存共用持有實例與取得來源；不是武器、防具、一般道具的萬用定義表。",D::Storage::Authoritative,D::Domain::Inventory,D::Installation::ExplicitExtension,sources_103,columns_103},
    {"owned_item_native_aliases","道具實例原生別名","保存共用實例對各客戶端版本的原生道具鍵、欄位及完整原始資料。",D::Storage::Authoritative,D::Domain::Inventory,D::Installation::ExplicitExtension,sources_104,columns_104},
    {"owned_pk_finished_return_feature","PK 結束返場結構合約","宣告明確安裝的功能合約：PK 結束返場結構合約；存在宣告不表示功能已啟用。",D::Storage::SchemaMetadata,D::Domain::Pk,D::Installation::ExplicitExtension,sources_105,columns_105},
    {"owned_pk_finished_returns","PK 結束返場鎖釋放歷史","保留已完成返場的原房間鎖釋放文件；歷史不是新的入場權限。",D::Storage::AuditHistory,D::Domain::Pk,D::Installation::ExplicitExtension,sources_106,columns_106},
    {"owned_pk_room_feature","PK 房間結構合約","宣告明確安裝的功能合約：PK 房間結構合約；存在宣告不表示功能已啟用。",D::Storage::SchemaMetadata,D::Domain::Pk,D::Installation::ExplicitExtension,sources_107,columns_107},
    {"owned_pk_room_members","PK 房間成員排他鎖","保存原 PK 成員的角色及連線唯一鎖；不可在匯出時當暫存垃圾省略。",D::Storage::Authoritative,D::Domain::Pk,D::Installation::ExplicitExtension,sources_108,columns_108},
    {"owned_pk_room_outbox","PK 房間待送與已提交封包","持久保存PK 房間待送與已提交封包；原有約束與寫入資格由來源 repository 定義。",D::Storage::Authoritative,D::Domain::Pk,D::Installation::ExplicitExtension,sources_109,columns_109},
    {"owned_pk_room_rounds","PK 回合持久紀錄","持久保存PK 回合持久紀錄；原有約束與寫入資格由來源 repository 定義。",D::Storage::Authoritative,D::Domain::Pk,D::Installation::ExplicitExtension,sources_110,columns_110},
    {"owned_pk_rooms","PK 房間狀態與檢查點","持久保存PK 房間狀態與檢查點；原有約束與寫入資格由來源 repository 定義。",D::Storage::Authoritative,D::Domain::Pk,D::Installation::ExplicitExtension,sources_111,columns_111},
    {"owned_pk_round_feature","PK 回合結構合約","宣告明確安裝的功能合約：PK 回合結構合約；存在宣告不表示功能已啟用。",D::Storage::SchemaMetadata,D::Domain::Pk,D::Installation::ExplicitExtension,sources_112,columns_112},
    {"owned_pk_terminal_resource_feature","PK 最終資源結構合約","宣告明確安裝的功能合約：PK 最終資源結構合約；存在宣告不表示功能已啟用。",D::Storage::SchemaMetadata,D::Domain::Pk,D::Installation::ExplicitExtension,sources_113,columns_113},
    {"owned_pk_terminal_resources","PK 最終生命魔力結算歷史","保留原房間最終 HP、MP 與版本結算文件；不得重新套用。",D::Storage::AuditHistory,D::Domain::Pk,D::Installation::ExplicitExtension,sources_114,columns_114},
    {"qualified_fruit_quest_sources","已資格化水果任務來源","保留原生資源來源的已資格化水果任務來源；完整原始位元組及來源不得改寫，不直接授予玩家權限。",D::Storage::NativeSource,D::Domain::Quest,D::Installation::VersionedMigration,sources_115,std::span<const D::Column>{}},
    {"recovered_characters","共用角色身分與原始角色資料","保存共用角色身分、角色欄位、名稱編碼與完整原始角色資料。",D::Storage::Authoritative,D::Domain::Character,D::Installation::VersionedMigration,sources_116,columns_116},
    {"recovered_positions","角色權威位置","保存角色權威區域、場景、座標與比對交換版本。",D::Storage::Authoritative,D::Domain::World,D::Installation::VersionedMigration,sources_117,columns_117},
    {"schema_migrations","不可變遷移歷史","保存完整不可變 SQLite 遷移 SQL 與套用歷史；目標 MySQL DDL 必須另存。",D::Storage::SchemaMetadata,D::Domain::Migration,D::Installation::VersionedMigration,sources_118,columns_118},
    {"skill_book_learning_events","技能書學習事件歷史","保留已執行操作的技能書學習事件歷史；保留完整收據與版本，歷史本身不授予新的操作權限。",D::Storage::AuditHistory,D::Domain::Character,D::Installation::ExplicitExtension,sources_119,std::span<const D::Column>{}},
    {"world_bank_service_points","世界倉庫服務地點","持久保存世界倉庫服務地點；原有約束與寫入資格由來源 repository 定義。",D::Storage::Authoritative,D::Domain::Inventory,D::Installation::ExplicitExtension,sources_120,std::span<const D::Column>{}},
    {"world_display_records","世界物件顯示宣告","保存有原生來源或隔離測試標記的 21 位元組世界物件顯示紀錄；不是怪物玩法設定。",D::Storage::NativeDelivery,D::Domain::World,D::Installation::VersionedMigration,sources_121,std::span<const D::Column>{}},
    {"world_monster_levels","世界怪物等級宣告","保存有對應來源物件的怪物顯示等級；不是怪物戰鬥屬性、掉落或經驗設定。",D::Storage::NativeDelivery,D::Domain::World,D::Installation::VersionedMigration,sources_122,std::span<const D::Column>{}},
}};
} // namespace
std::span<const ServerDataDictionary::Table> ServerDataDictionary::tables() noexcept {return dictionary;}
const ServerDataDictionary::Table* ServerDataDictionary::find_table(std::string_view name) noexcept {
    const auto found=std::lower_bound(dictionary.begin(),dictionary.end(),name,
        [](const Table& table,std::string_view value){return table.name<value;});
    return found!=dictionary.end()&&found->name==name?&*found:nullptr;
}
const ServerDataDictionary::Column* ServerDataDictionary::find_column(std::string_view table,std::string_view column) noexcept {
    const auto* entry=find_table(table);if(!entry)return nullptr;
    for(const auto& field:entry->columns)if(field.name==column)return &field;
    return nullptr;
}
} // namespace god2
