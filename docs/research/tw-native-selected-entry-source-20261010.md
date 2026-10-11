本輪把台服實際選角的完整來源接到世界入口。原先 native_select
只回傳共用角色 ID；現在同一個來源另保留私有建構、不可變的 Selected，
包含實際 Session 的選角輸入、已發清單、完整75位元組快照、全部共用角色
根資料及完整角色 ID。入口取得同一張 Selected，於取得原生入場資料前後
以及其 Current 前後重新核對。沒有新增或改寫原生封包欄位。

Selected 只保留純資料與弱來源生命週期。容量有界的 game-owner 登錄保存
弱 Session 與實際 Target/Link/資格判斷；對外 Current 只保存弱登錄來源。
同樣的三個 ID 不能替代同一張 Selected。新選角先撤下同 Session 舊記錄，
失敗不能重用舊選角；過期或關閉 Session 由真實生命週期觀察清除，沒有
自行發明原生 TTL。所有外部判斷前先複製登錄資料，不持有 map iterator。

原生 Session 的既有次序保持不變：Authenticated、character_id 為0時，
實際 native_select 之後呼叫 world_entry，成功後才設定 character_id。
入口仍要求完整共用 ID 等於2A的14位 actor handle，超出者拒絕；沒有
把 token、slot 或截斷 ID 當角色身分。完整角色 profile、編碼、建立時間、
權限與位置 revision/map 都參與目前來源判斷。原生完整40位入場 frame
與不透明欄位保持原樣，Selected 不能產生缺失的 frame 或補零。

SharedTaiwanStoredWorldEntrySource 的 Scope 比對增加 Selected 指標身分。
實際 HostPlan 同時保留並轉交選角來源與入口來源。Application vault
補上原生 Entry 中巢狀呼叫被供應者捕捉的情況：先標記，再於外層入口
回傳前拒絕；舊有未選原生角色來源的入口維持原行為。

本輪新增 C++檔0、修改7、來源接線段增加1（209→210），新增完整雙向
遊戲路徑0。沿用8段、2308位元組原生證據，沒有新增 opcode、原生覆蓋
或路徑分母。台服觀察值仍為 C2S156、世界 S2C252（230固定、22可變）、
戰鬥 S2C110；這些是不同階段的觀察值，不能直接相加當遊戲功能總數。
陸服 C2S156、分階段 S2C280 保留。本輪不宣稱整個選角/入場玩法完成。

仍需串接實際 issuer/可見性/資源與完整2A供應策略、跨G/重播/並行 admission、
回傳後 queue 與場景 publication 的來源一致性、Main 明確選用，以及其餘
世界/物品/任務/戰鬥等完整權威路徑。Selected 是入口使用前的來源核對，
不是一次性 admission CAS、網路原子性或客戶端確認。全遊戲方向/狀態/
變體分母尚未封閉，TW/全遊戲完成百分比保持未知。

本輪只有來源修改、靜態原件/差異閱讀和檔案雜湊封存；沒有建置、測試、
原生程式/codec/runtime/DB/SQL 執行或部署。保留台陸網頁共用核心、帳號
存檔、聊天/IME/認證/頭像、原生字體與繁簡轉換、等級及既定數值擴充方向。
目標保持 active，依2026-10-10指示優先完成台服全部實際來源路徑再停止。
