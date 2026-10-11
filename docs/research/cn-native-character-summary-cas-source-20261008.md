# CN 完整角色摘要原子寫入與實際 issuer 接口

本輪 `20261008-cn-native-character-summary-cas-source` 延續第150輪同一 SQLite／帳號／角色來源的完整摘要 reader。實作 `SqliteNativeCharacterSummarySnapshotRepository::replace_from_issuer`、`SqliteDatabase::native_character_summary_writer` 和 `CnNativeCharacterSummaryCommit`，將實際 issuer 提供的完整資料接至同一權威來源的原子持久化入口。這些是來源實作，尚未選用正式 issuer、安裝 schema、匯入資料或啟用登入。

Writer 接收完整 expected／next tuple，包含帳號、目標 group／server、客戶端 SHA、整份原生記錄、revision／origin、明確有序共用角色 ID、名字模式與可選 role 的完整記錄／revision／origin。Revision 與原生數值必須由實際來源供給，沒有預設初值、revision 自增、零資料或全角色可見規則。完整 expected 必須符合當前儲存，next revision 必須更大。

同一 owner thread、同一 SQLite connection、實際 accounts／characters repository、foreign keys 開啟且無外部 transaction，是寫入前置條件。Writer 自有 `BEGIN IMMEDIATE`，有重入 guard，保存整個帳號的實際共用 roots。在 Prepared、BeforeWrite、BeforeCommit 各階段前後重讀完整 tuple 與所有 roots；角色 ID、account、slot、完整 profile、created_at、name codepage 和 streamer privilege 必須一致。BeforeCommit 觀察 staged next，而非旧摘要。Issuer 是必要的可信來源 observer，必須自行比對更早的準備來源、權利、可見性及操作 revision，且不得執行 SQL writes、yield、事件泵或持有失效借用。

Header 與全部 mapping／optional role 在同一 transaction 中更新。Header CAS、刪除舊 mapping 數量、逐筆 insert 數量與完整 readback 均受檢查。沒有 role 時四個欄位明確一起 NULL，不能用猜測等級補入。Writer 在 COMMIT 前持有完整 owned 結果並執行最後 issuer／tuple／roots 檢查；COMMIT 後沒有重新查詢、callback 或結果配置。拒絕返回 nullopt、錯誤拋出並由 transaction rollback；這些不是原生回覆封包。

通用 writer 的4096記錄／row 預算只是 storage budget。CN move-only Plan 額外要求 pinned build、精確75-byte ACCOUNT07、實際 native row count（最多2）、明確唯一 common IDs、唯一原生 slot、明確名字模式，prompt 模式需原生 marker；optional CN22 必須為實際完整25-byte與獨立 revision／origin。它沿用既有 RoleLevel projection，拒絕不能投影的 FF。沒有從 common slot、CUSTOM-0013、名字或角色存在推測原生外觀、位置、權利、level 與 opaque bytes。

`commit_actual_source` 是實際 C++ caller，使用同一 `SqliteDatabase` 的 reader／writer 和共用 accounts／characters。其實際正式呼叫者、issuer、資料及權威資格尚未設定，`main` 的 CN plan 仍未選用。這輪不將 helper caller 計為正式 gameplay route。

兩個具體待接線點保持 OPEN：

- 既有 owned character removal 會刪除 mapping（FK cascade），但不會同步刷新 raw07 header／row_count。Reader 會拒絕不一致摘要；writer 不會把損壞 tuple 當不存在來修補。需要 actual owner 的完整 replacement 與同一角色 mutation transaction，或精確且可恢復的 header invalidation 流程。
- 既有 SharedWorldSelection 仍保留 issued admission 的 raw07／IDs 並檢查 common ownership。摘要 CAS 不會自動撤銷已發出的 world offer，須接實際 issuer／admission 的 revision 與 invalidation。

原生資源證據新增析構生命週期：`007E9D50 ->00449940 ->member+464 ->00427350 ->00430340/00423020`。若來源觀察原生資源 lifetime，Current 必須在此流程開始前失效；獨立 own-server catalog 無 process-memory 要求。Selector4 的 D54CE／CF、當前首個 NUL 與相關 intervening writes 仍未知。Bounded target search0 不代表 writer 不可達或 dead code。

Receiver 新增 `004AE367 ->004E0F30` tail，局部 segmented normal CFG 為51 sites；actual ESI 的負 handle suffix 有1條資格化關係，上游9個必經 helper 的 preservation 仍未知，不能認定 original entry ECX 全程保留。下一入口是 `004C4060 ->004C409C ->004C4880` 的實際 ECX／輸入及 network owner／phase。

三位子代理分工交付既有證據及本輪獨立交接審查，原始快照與歷史 seal 保留。新增 packet／phase binding／完整 owner chain／完整雙向 route 均0。全遊戲總數與完成百分比仍未知。未建置、測試、執行原生／C++／Windows API、讀取資料庫、安裝／匯入／遷移或部署。完整 TW／CN／PC／web、64-bit 數值及 stack99 目標繼續有效。
