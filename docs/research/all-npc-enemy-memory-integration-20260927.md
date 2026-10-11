# 全量 NPC／怪物記憶體目錄接入

2026-09-27。依照玩家最新要求，追查範圍改為全部已載入 NPC 與 EnyName 記錄，不以四個果力村 NPC 的成功代替全量復原。

## 實際執行與正式接入

- ReadProcessMemory 收據：`artifacts/research/live-memory-all-catalogs-20260927-01/memory-result.json`。完整資料位於 `loaded_static_catalogs`；包含 4,043 筆來源 NPC、7,815 筆 EnyName 記錄、96 組實際 descriptor。客戶端已關閉，未切換使用者桌面，未寫遊戲記憶體。
- NPC 逐筆來源欄位、28-byte prefix 與 RAM 的 94-byte 記錄比對；EnyName 逐筆 26-byte 記錄及 descriptor 指標核對。
- 正式部署：`artifacts/releases/all-npc-enemy-memory-20260927-02`。資料庫升至 schema33，新增完整 NPC 來源表，將原本空的怪物顯示表匯入全量資料。
- 正式 C++ 啟動確認：`NATIVE_NPC_DISPLAY_READY records=4043`、`NATIVE_ENEMY_DISPLAY_READY records=7815 visible=7791 groups=96`。完整來源 SHA256、每筆資料及所有原有資料表均已核對。
- 正式服務端候選 SHA256：`ca3047ee7e09c56373222fc4c60ab1404d910b45308f5642cd980b862ca4f119`；部署後 PID7056。服務仍使用原有設定，本機 2592 接聽。客戶端、設定與所有玩家資料表未變。

部署工具 `tools/operations/all_npc_enemy_source_release.py` 提供備份、隔離 stage、全表核對、apply、失敗還原及 verify。第一個 stage 因複本資料庫檔名不符合現有 town diagnostic 隔離要求而被拒絕；修改工具使用合格檔名後，第二個 stage、正式部署及核對成功。沒有放寬設定驗證。

## 測試與修復

- `database`、`network`、`config`、`recovered_movement_service`、`native_npc_display`、`native_enemy_display_integrity`：6/6 通過。
- `player_appearance_snapshot`、`player_appearance_update`、`recovered_login_failure`、`recovered_account_login`、`fruit_quest_repository`、`recovered_chat_server`：6/6 通過。聊天測試是本機 socket 回歸，不宣稱本輪有原始客戶端聊天驗收。
- 修復 NPC Python 測試的 SQLite 連線未關閉導致 Windows TemporaryDirectory 清理失敗；使用 closing 並明確 commit。
- 修復新增 inline 地圖陣列造成 movement 測試 stack overflow；地圖改由共享唯讀 heap 物件保存，movement 回歸通過。
- 沒有宣稱整個 CTest suite 全部通過；以上為本輪明確執行的 12 項。

## 全量範圍與尚未復原的欄位

7,815 是怪物／隨從等顯示來源記錄，不是 7,815 種野怪。24 筆被較新來源覆蓋的 orphan 原樣保留，只有 7,791 筆仍可由 96 個 descriptor 查找。顯示 namespace 的 area／scene 不能直接升格為實際世界出生設定。

完整來源目錄核對覆蓋率為 100%。全部原生世界擺放與原生雙攻雙防尚未完成，本輪新增合格出生實例為 0；整體服務端工程完成度仍約 11%，是估計，不是全遊戲原生內容的驗收百分比。

登入前這次 RAM 中所有來源 NPC 的 66-byte 可變尾段為零；不可把零當作原生數值。尾段已追到 F8 服務端寫入，世界位置追到獨立的 NPC／monster object pools 及 72／71／60／5F writer。完整任務 RAM 文字另抽取 665 個座標 token、327 組直接相鄰名稱關係，均保留歧義，尚未取得可核對的 instance／map／direction 組合。

後續資格條件：完整讀取已登入世界的兩個 256-entry pools，核對目前 W/R/U 與地圖身分，逐筆連到原始輸入 writer；只有源自我們自訂服務端的資料必須保留自訂來源，不能循環宣稱原服復原。座標、面向、出生條件、雙攻雙防與掉落只在取得相符原始依據後填入正式 gameplay 表。

四個 Fruit 任務的程式、儲存及 handler 已編譯進本次候選，但正式設定維持關閉、三個相關表皆為空。隔離原始客戶端尚未通過該路由，不能將 TCP／純 C++ 成功標為原生任務驗收。
