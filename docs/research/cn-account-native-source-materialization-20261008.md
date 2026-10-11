# 原生帳號資料的實際來源寫入鏈（20261008）

本輪修改 SqliteNativeAccountSnapshotRepository.h/.cpp、SqliteDatabase.h/.cpp，新增 CnNativeAccountSnapshotCommit.h/.cpp。共四個既有來源修改、兩個新 C++ 來源。目標是把真正 issuer 提供的帳號 delivery snapshot 接進同一共用讀取物件，並保留原生登入的獨立權限來源；沒有填入原生數值或把資料存在當作可登入。

CnNativeAccountSnapshotCommit::Plan 必須收到完整 expected／next 與真正 Issuer。陸服適配器檢查固定客戶端雜湊、原生 uint32 帳號欄位、正 signed64 revision、恰好40B metadata與16B billing、來源雜湊與紀錄；expected 必須同帳號／版本且 next revision 嚴格增加。所有 bytes、origin、revision 由來源提供，不設初始1、不做 revision++、不選 billing／權限 flag，也不產生205B1D或17B0A。

commit_actual_source 透過 SqliteDatabase::native_account_snapshot_writer 取得原來 lazy reader 的同一個物件，核對實際共用 accounts backend，再把擁有的資料與 Issuer 移入 replace_from_issuer。存取器沿用原 migrated guard，沒有新開資料庫、建立另一個 reader、安裝 schema、匯入資料或改 migration vector。

通用儲存層仍採原有 opaque1..4096B 邊界，帳號／revision 需能以正 signed64 表示。Writer 檢查 game owner、重入、autocommit、foreign keys，建立自己獨立的 BEGIN IMMEDIATE。完整帳號基線僅在內部核對 id／username／password_hash／created_at，絕不傳給 issuer 或記錄。真正帳號必須存在，完整 expected snapshot 及帳號基線在 Prepared、BeforeWrite 的前後均比對，拒絕的回呼也會經過後置檢查。

UPDATE 以同 account／client／expected revision 做 CAS；INSERT 只用於 expected 不存在的情況，都需恰好影響一列。完整 staged next 在 COMMIT 前讀回並成為擁有的結果。BeforeCommit 看到的是已暫存 next，不能拿舊 snapshot Current 代替；其後再次核對完整 staged tuple 與帳號。COMMIT 後只有已擁有結果的 noexcept move，沒有回呼、reload 或新配置。拒絕與例外由原 transaction rollback，nullopt 不是原生失敗封包。

原 reader JOIN／欄位／範圍與 schema 文字保留，reader 增加同 game owner 檢查；schema 沒有註冊或執行。共用表 account_native_snapshots 按 pinned build 區分 opaque delivery bytes，帳號與 gameplay 權威仍在原共用來源，不拆兩套帳號資料庫。

寫入這條來源不等於已取得真正 metadata／billing、實作 issuer、獨立 phased entitlement、帳號目錄／deadline、角色 summary／visibility 或 world Reservation。原 SharedStoredAccountProfileSource 仍要求真正 Prepare／Authority、整份 snapshot 重讀；原 CNG／credential／directory／發布 gate 不改。storage COMMIT 不是 native ACK、客戶端驗收、登入啟用或自動 grant invalidation。

三個子代理分別處理 writer、同物件 backend、原生 input Plan／caller；before934 與前輪162完整封存保留。新的檔案正確標示為 added，沒有偽造 before。部分過長 Windows 路徑副本由交付保留為 partial inventory，最終原始來源副本另外完整保存，不能以 partial 充當來源證據。

本輪只讀寫來源與檔案帳目，未建置、測試、執行 C++／原生／Lua／API、存取 SQLite、匯入、遷移、重啟或部署。opcode／phase／完整雙向路線增量均為零，全遊戲分母與百分比未知。完整 TW／CN／web 支援、原生字體與繁簡轉換、共用表／_tw與_cn例外、仙幣單獨上限與數值64範圍、等級及凍結功能全部保留。
