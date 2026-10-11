# 共用帳號 snapshot 到 CN 原生登入來源

本輪 `20261008-cn-stored-account-profile-source` 延續既有 CN issuer 與登入組裝，不改認證、原生 wire、權益規則或正式資料庫。上一個 goal turn 僅回覆進度，分類為 no progress；本輪接續先前已保存 before snapshot 的未結算程式增量。

## 實際程式鏈路

新增共用 `NativeAccountSnapshotRepository` 與 SQLite 唯讀實作，要求綁定同一個實際 `SqliteAccountRepository` 及其連線。查詢以既有 `accounts.id` 和固定 client SHA 為鍵，join 共用帳號表；不查密碼，不按顯示名稱配對，不另開 CN 資料庫。

新增 `SharedStoredAccountProfileSource`，在同一 serial game owner 上取得完整資料列，CN 適配器要求 metadata 恰為 40 bytes、billing 恰為 16 bytes，並保留 account、revision、兩個 SHA 與來源紀錄。prepare 前後及既有 issuer 各次 Current 觀察前後都重新讀取並比較完整 snapshot；拒絕缺列、格式錯誤、來源不同、重入或過期值。Current 仍必須呼叫實際 Authority，觀察既有 issuer 提供的完整 credential、account ID、key、catalog 與 deadline。這些敏感觀察不儲存、不記錄，只在同步 callback 範圍有效。

實際 `compose_native_login` 新增明確的 `stored_issued_account_source` 選項：同一 `Context.accounts` → stored profile prepare →既有 `SharedIssuedAccountSource` →既有 held account success。它與 full account／直接 issued source 互斥，不自動啟用。既有共用角色摘要注入、CNG key policy、credential current、目錄及 grant publication 鏈繼續沿用。

## 共用儲存與啟用邊界

`account_native_snapshots` 是單一共用資料表提案，以 `(account_id, client_sha256)` 為主鍵，存版本相關的 opaque delivery bytes；帳號、角色及遊戲權威仍在原共用表。沒有 `tw_`／`cn_` 前綴，也沒有為 wire 大小差異複製 gameplay 表。通用儲存的 1..4096-byte bounds 是操作限制，不宣稱為兩版原生格式；CN reader 另外套用已恢復的精確 40／16。

`schema()` 只回傳 DDL 提案，所有欄位明確 NOT NULL 且無 DEFAULT；沒有 migration 註冊、installer、import、upsert 或 load 時 DDL。`SqliteDatabase` accessor 僅在明確請求時延後建立 reader，使用既有連線及 accounts。未選此來源的路徑不建立 reader，也不改原 migrate／initialize 行為。正式 Application 尚未配置來源，schema 沒有安裝、沒有資料列匯入。

來源 SHA、紀錄和非零 revision 只能記錄 lineage，不能單憑其存在認定 native 正確、權益有效或官方公式。讀前後相等不保證跨程序原子性或 ABA 防護；兩個 repository 和 database 必須存活到連線 drain 完成，callback 不寫入／yield／pump event／傳送輸出。存入及修改 snapshot 的權威、實際 entitlement／deadline／目錄 metadata、角色狀態與 visibility 仍須接續；不能用全零、免費、固定 paytype 或 always-true observer 填補。

## 原生來源與排除的猜測

CN 固定 EXE SHA `582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`。本輪沿用已保存的完整 1D／0A shape；沒有新增 opcode 或欄位語義。靜態檢视 config 的 `0047CBC0` → `0047D4A0` 是 `%s` URI 字串供應鏈，不是可直接導出的 billing16／權益整數。保留函式 metadata envelope 和 literal，未訪問 URI，亦未宣稱其全部後續 consumers 已關閉。

## 本輪計數與剩餘

新增 SQLite snapshot reader 1、stored CN Profile producer 1、既有登入 composition binding 1。新增 opcode／phase binding／完整 owner chain／完整雙向 gameplay route 均為 0。全遊戲總量、完成量及百分比維持未知。

本輪只做 file/source/PE 靜態恢復與帳本整理。未建置、測試、執行 C++／原生／API／codec／服務，未讀 DB、遷移或部署。帳號存檔、認證、聊天、IME、頭像、字體、繁簡轉換、等級、客戶端資源及全部歷史封存保持。全遊戲 TW／CN／PC／web／WSS、權威玩法、數值擴充、背包 99 與完整路徑分母仍為完整目標，全部串接後才集中測試、修復及發布。
