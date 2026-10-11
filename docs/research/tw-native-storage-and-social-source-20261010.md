# 第240輪：台服持有物品儲存入口與組隊原入口界限

本輪實際修改 `src/main.cpp`、`src/db/SqliteDatabase.h`、`src/db/SqliteDatabase.cpp`。新增明確選用的 `--owned-equipment-schema`，必須配合 `--migrate-only`，禁止所有 `--run-for`（含0），與 `--native-delivery-schema` 互斥；參數檢查先於讀取設定及初始化資料庫。普通啟動仍沿用原來的 `run_server(config,seconds)`。

新的 `install_owned_equipment_schema()` 使用真正同庫的 accounts／recovered characters，要求已遷移、autocommit、foreign_keys=1；在一筆 BEGIN IMMEDIATE 內拒絕十個相關名稱的 TEMP 大小寫影子，確認五個必要 main 基礎表，再執行既有四個 owned inventory CREATE 與一個 native equipment witness CREATE，最後一次提交。未呼叫各自另開交易的舊 installer，亦未更改它們。這是 CUSTOM-0092 儲存的實際正式 CLI 接入，不是新的物品取得規則。

這筆原子交易只涵蓋新增五表。CLI 先前的 `database.migrate()` 仍是既有獨立流程，不能說整個命令共用一筆交易。此入口只供 fresh installation；任一完整／部分既有 feature 表均使它失敗，沒有 IF NOT EXISTS、修補、升級、匯入、贈送物品或改動 schema 版本。這輪未執行此命令或任何 SQL。

原生定點追查則確認 mapped149c 與 unpacked5fcf 的 C57／C6A cursor setter、world caller、sender 及相鄰54／58分派有界 bytes 相同。原文字資源確實將3020標為「組隊」、3140標為「支援」；這與舊 CUSTOM-0062 的 Kick／Join 語義存在尚未解決的對應缺口，不能歸因版本差異，也不能直接交換。

S54 payload+0x10 的 actor WORD 被存到 UI+AFECC；原確認○／×將同一 WORD 放入 C58，加上 answer1／0。這只證明答覆所指 actor，未證明官方 C57／C6A handler 應把哪個人的 preview 送給誰。20261002 的歷史自有服務驗收曾以 menu31／cursor6／C6A 開54、menu27／cursor5／C57作 leader kick；它支持當時自訂規則與原生 consumer 相容，不能升格為原服語義。本輪沒有交換 enum、另猜 C57 邀請、覆寫歷史證據或變更聊天。

網頁端交接沿用同一服務端權威。現有 native C2F 先按1／2或9／3分出隊伍／密語／幫會，Application 各自拒絕後立即返回，沒有落入公開廣播；新 common WorldOwner／Main 尚未因此自動安裝。能力 HTTP 介面只記為待接契約，未新增或啟用 endpoint。C66 舊來源已有限定姿勢→self77／同場景 peer77，但完整 mount／moving／cooldown authority 與新 common hosting 仍缺；C56 世界神仙技能仍缺完整權威 action／消耗／回覆。

台服已觀測 C2S156、world S2C252有效值（230固定、22可變）；battle110索引含9個特別分派，均不是完整玩法分母。本輪新增完整雙向路線0，既有225個混合版本局部來源段不增加；儲存前置接入另記1項。完整 TW／全遊戲分母與百分比未知，不能報100%。真實物品取得／full1215／full25發行、完整正式 Main 供應者、各玩法與 phase/state/variant 分母仍待完成。

本輪只做原始碼修改、靜態原生 bytes 定位與檔案帳本。未建置、測試、啟動服務／客戶端、執行 native／codec、連遊戲資料庫／執行 SQL、遷移或部署。保留 CN／網頁／共用資料及凍結功能、原生字體／繁簡轉換、64位數值目標、仙幣99999999999、堆疊99與原等級。目標 API 現讀仍為 blocked，使用者授權的手動續作有效；本輪沒有呼叫 pause、complete 或另建替代目標。

完整 before／final／diff、原生有界 bytes 及小型交付封存位於 `C:/Users/risei/.codex/artifact-archives/god2-server/20261010/tw-social-command-source-240/`。既有239封存保持原樣。
