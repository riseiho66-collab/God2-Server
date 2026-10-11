# 陸服技能來源接入現有共用 catalog 表

本輪 `20261008-cn-shared-skill-catalog-storage-source`，PHASE1 僅靜態檔案研究與來源串接。
承接第132輪已封存的實際 CN resource／loader／record 身份，不重做或更新基準。

## 本輪比較改變了接入方式

TW 原始 resource 從已保留的獨立研究 **input** 取得，不執行該研究工具或使用其模擬結果：
`artifacts/research/enemy-blackbox-20261006/consumer-experiment/inputs/client/Data2/Fight/Spg/cbspec2.bin`。
完整大小112660、SHA256 `7676acd93f164d071f7681a3fe74de94d65892759dbf2e69e3c0f748423d2f51`，
四組宣告 counts121／129／87／111，共448筆。
CN 原始 resource SHA256 `857b52e36ceb4d08f61a373f2882593dada84ecbb8150da187f8c5553389a004`，
counts125／130／87／111，共453筆。

兩版共有448個 `(kind,ID)`，**完整110-byte record 相同數為0**。
CN 另有 `(0,122..125)`、`(1,130)`，TW 原始檔沒有這5個鍵。
差異涉及字串區段，也有+42、+44、+45、+47、+48、+4A、+6B等位元組；
不憑字串解碼、翻譯、同鍵或少數欄位相等宣稱共同技能 identity／规则相同。
保存逐鍵兩側 raw／hash、差異 offset 及差異頻次；未解碼或猜測未知欄位語義。

目前已安裝 TW resource 的 SHA256 是
`3adcda70a477086da50411fe5d023eec33f915efafd17ec478d55542cae42ea7`，
counts126／129／87／111。它含既有 CUSTOM 增量，保持原狀及獨立標籤；
未拿它替換原始7676來源、未把 CUSTOM 當 CN native，也沒有把缺失的歷史路徑冒稱仍存在。

## 共同表與讀取程式

現有 `native_data_sources` 與 `native_skill_catalog` 都以 dataset 身份區分 raw來源，
`NativeSkillCatalog::lookup(dataset,kind,id)` 已有適用的 joined owning snapshot。
資料表結構可容納 CN 的453筆及 source_record_index／offset／110-byte BLOB；
不需拆 `_tw/_cn` 表、改既有 migration、改 TW current_dataset_id 或覆寫舊 rows。

新增 `CnSharedSkillCatalog`，從同一共用 `NativeSkillCatalog` reader 取得實際 CN dataset。
bind 要求實際 CN supplier 及全部453個 qualified rows；每次查找重新讀實際共享表，
比對完整來源 metadata、來源序號、offset、raw bytes及record hash，再交出自有副本。
Source Current及同一 game owner 要求保留；缺失／不同來源不回退成 TW／預設定義。
DB reader及其連線需由真正 host 保有生命週期。程式中的讀取操作尚未執行。

dataset 為 `cn-native-cbspec2-582f2695-857b52e3-v1`；
loader RVA161BB0、此次 preborn查找 RVA133300。metadata中 source_section／RVA文字
為可追溯註記，不是新的 native wire欄位。
本輪保存可供後續正式 importer使用的 row／source材料，**沒有執行 import／migration／SQL／DB讀取**。

既有 `SharedPrebornWindowSource` 改接此實際共用表讀取程式：
原生83的每個 WORD 仍保留原順序與重複項，查出實際共用表中版本合格的
`NativeSkillRecord`，交給同一共同操作及 post-commit qualifier。
沒有新增授權成功、技能資格、消耗、Lua公式、common skillID 或儲存結果。
dataset 是原生來源身份，不能當共用 gameplay skillID；raw pointer及原生 slot也不是 ID。
optional native Snapshot 繼續只是恢復證據，沒有 client-memory依賴。

## 缺口

正式 Application 尚未配置CN catalog rows／supplier／shared reader／initial issuer；
資料匯入屬後續有備份與可恢復流程的正式接入，PHASE1 不執行。
共同技能／subject identity映射、已學／可選／資格／成本、native Lua规则、
transaction／save／persistent replay及其他所有玩法仍需接通。
本輪新增共用表source adapter1、既有選擇流程來源交接補強1；完整雙向玩法0。
未測試、建置、執行API／native／C++／服務、DB存取、遷移或部署。
全遊戲分母及百分比仍未知；台陸／PC／web／64-bit數值／背包99與後續全面驗證修復發布目標完整保留。
