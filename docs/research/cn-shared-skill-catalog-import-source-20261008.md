# 陸服技能定義：既有共用表的明確匯入來源

本輪接續已封存的原生資源、共用表讀取器與選技來源；不重新逆向已定位的讀取器，也不把原生技能編號當成共用玩法身分。交付僅為 C++ 來源，未執行 SQLite、匯入、建置或測試。

## 已知來源與缺口

固定 CN 執行檔 SHA-256 為 `582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`，`data2/fight/spg/cbspec2.bin` 為 112,660 位元組，SHA-256 為 `857b52e36ceb4d08f61a373f2882593dada84ecbb8150da187f8c5553389a004`。既有 `CnNativeSkillCatalog` 已限定原生 `1.03`、四組計數 125／130／87／111、453 筆 110 位元組定義及實際 immutable resource owner。

既有 `CnSharedSkillCatalog` 要求同一個 `NativeSkillCatalog` 讀取器中存在完整 CN dataset 的 453 筆精確資料；先前只有匯入材料，沒有服務端 C++ 的匯入操作。因此資料來源→既有共用表這一段仍缺程式。

## 本輪來源串接

新增 `CnNativeSkillCatalogImport::import_actual_source`，透過 `SqliteDatabase::import_cn_native_skill_catalog` 明確使用該資料庫自己持有的 connection。它不由登入、客戶端封包、Application 啟動或預設 migration 呼叫。

來源程式依序：

1. 接受實際 current 的 `CnNativeSkillCatalog`；先持有所有 453 筆原生資料、逐筆雜湊、ordinal、offset、kind／ID。拒絕 JSON、測試材料或 TW 同編號記錄作為操作輸入。
2. 要求沒有外層交易，使用既有 `BEGIN IMMEDIATE`／RAII rollback，要求既有 migration 5 名稱及外鍵啟用，不建立或改動 schema。
3. 只查指定 CN dataset 的來源與定義數。來源存在但資料不完整、孤兒資料、來源衝突或原始位元組衝突時，拋出 `DatabaseError` 並保留原資料；不使用 REPLACE、UPDATE、DELETE 或忽略衝突。
4. 全新 dataset 才向既有 `native_data_sources` 與 `native_skill_catalog` 插入精確來源和 453 筆記錄。已有完整相同資料則回傳 `AlreadyPresent`。
5. 在同一 connection／交易中透過既有 `NativeSkillCatalog::lookup` 逐筆讀回，比對完整來源、ordinal、offset、hash、raw bytes 和 identity，並核對總數、重觀察 resource owner，才 COMMIT。任一步失敗由既有 RAII 交易回滾。

使用後仍以 `database.native_skill_catalog()` 與同一 native provider 呼叫既有 `CnSharedSkillCatalog::bind_actual_shared_store`。既有選技來源已使用該讀取器的 owning records；這一輪沒有修改選技規則、原生 UI gate、已學技能或角色資料。

## 邊界与剩餘工作

此為定義的來源存放，未證明 TW／CN 同編號技能的共用身分或玩法等價，未把 TW 的 `client_mp_threshold` 語義推給 CN，也未產生費用、學習資格或戰鬥公式。技能書的 386 筆綁定與 67 筆無書記錄維持既有證據。

實際匯入、reader／resource provider 配置、共用主體／技能映射、Lua 規則、角色技能存檔、持久重播、發行事件、原生回覆及 Application 尚未完成。正式 release 的備份、來源 CAS、恢復及後續驗收仍需完成；本階段不執行匯入或 release。既有 TW dataset、表名、角色存檔與凍結功能保留，沒有新表、區域前綴表或 migration。

本輪新增一個匯入 writer 與一個同資料庫入口的來源。新增封包、連線階段、网络流程 owner 與完整雙向路徑均為 0。全遊戲分母和百分比仍未知。完整 TW／CN／網頁目標、64 位元數值與合格堆疊 99、後續集中測試／修復／發布保留。
