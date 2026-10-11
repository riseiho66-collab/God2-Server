# 原生任務資料接入與未完成項目：2026-09-26

## 使用者要求與目前結論

本輪要求所有任務按原生還原並實裝。**尚未達成全任務可玩還原**；不能將任務名稱、說明、封包解析或測試案例數當作已完成任務。

已將可核對的全部靜態來源接入 C++／SQLite，補上正式庫此前缺少的 418 筆任務定義、169 筆 ACTMIS 需求顯示及 85 筆每日任務原始記錄。原有 2,014 段說明保留。接取資格、完成事件、分支、消耗、獎勵與重置規則仍沒有完整原生來源；沒有以通用任務規則填補或重新啟用自訂城鎮嚮導任務。

## 實作

- migration23 `native_quest_source_catalog`：新增 `native_quest_definitions`、`native_daily_quest_source`，不重写已套用的 migration。名稱保留原始 CP950 位元組，來源路徑、檔案／解碼雜湊、行號、記錄雜湊、原始行完整保存。
- `import_native_quest_sources.py`：雜湊固定、來源結構核對、交易匯入、回讀、重複匯入不重寫、衝突拒絕、任一每日寫入失敗時兩張新表一起回滾。
- `NativeQuestCatalog`：正式 SQLite 借用的 C++ 讀取器；提供任務定義、說明、ACTMIS 顯示及每日來源欄位，並提供原生 458430 的 BYTE index／branch 查找。三個命名空間沒有自行串成同一 quest ID。
- 每日五筆 12 欄記錄保留缺欄；`field()` 的 absent 與 present-empty 分開，沒有補 0 或空獎勵冒充原始值。
- 服務端啟動檢查資料數量並記錄 `NATIVE_QUEST_SOURCE_CATALOG`，明確標註 `authority=source_display_only gameplay_rules=unrecovered`。
- `RecoveredDailyQuestRequest`／`RecoveredWorldRecords`：接入原生 D8 的 9 位元組結構，分開 selection mode1、auxiliary mode2，保留末尾不透明位元組。FD subtype2 的已核對形狀保留安全檢查，清單容量限制 40。
- `RecoveredWorldService`：每日請求只在已擁有角色的 InWorld 單筆路由送給明確設定的任務政策回呼；缺政策、錯狀態、匿名、多筆／混合記錄拒絕。**正式 Application 未啟用沒有原生規則的接任務／发獎回呼，沒有假成功或任務完成回傳。**

## 原生證據

兩份並行稽核：`native-quest-rules-audit-20260926.md`、`native-quest-exe-frontier-20260926.md`。全任務缺口逐項保存在 `artifacts/reports/native-quest-rules-audit-20260926/audit.json`，沒有把逐段說明的下一行視為完成事件。

原生測試新證據：72 個 D8 builder 情境、12 個 FD 長度邊界。每日可選狀態來自服務端清單；index／branch 不是 Mission_data ID。D8 可能是面板／導航互動，尚不能稱為接取或交付任務指令。這些證據見 frontier 報告末節，不能用早期靜態觀察取代後續原生執行證據。

## 驗證範圍

- C++20 核心、候選服務端、原生資料讀取器與每日請求測試編譯成功；新 C++ 讀取器的數值比較警告已修正。
- CTest 四項套件通過：每日請求 codec、世界政策路由、既有任務匯入、新任務來源匯入。兩個匯入套件共 8 個 Python 案例，涵蓋全部來源回讀、85 個每日 pair 查找、5 筆缺欄、衝突與交易回滾。
- 持有資料／NPC／怪物限制隔離 TCP 3/3 通過；背包 TCP 3/3 通過。這些是既有可玩鏈的回歸，不是全任務驗收。
- 原生來源接入沒有產生新玩家任務狀態、接取記錄、完成標記、任務物品或獎勵；正式庫原有 NPC／怪物原生限制保持啟用。
- `native_quest_catalog_release.py` 隔離備份、候選 migration／匯入、C++ 全量讀回、正式套用及比較既有玩家資料。更新前要求無玩家連線、既有內容與備份一致；更新失敗時連資料庫 schema 一併還原，避免舊 EXE 面對較新 migration 而無法啟動。
- 隱藏桌面實際客戶端回歸：`artifacts/playtests/private-native-quest-catalog-20260926-01` 及最终 `-02` 均 accepted=true；原生來源全部匯入隔離庫後仍可登入、还原人物／神仙／戰寵資料及完成三次戰寵轉移。輸入桌面保持 Default，來源庫与現用／隔離客戶端雜湊不變。這是原有流程相容性驗證，沒有執行全任務接取／發獎，既有合成實例的圖像診斷未宣稱已修好。
- 最終發布 `artifacts/releases/native-quest-catalog-20260926-02` 保存舊 EXE、配置、SQLite 線上備份與完整候選庫。正式服務 PID 20684，2592 監聽正常；`verification.json` 確認既有玩家表未變、quick_check=ok、正式來源數 [418,2014,169,85]、客户端與配置未變、正式 EXE 与已驗證候選一致。原有 4 個帳號、3 個角色保留。

## 仍需補齊

必須取得原始服務端任務腳本／規則表或能證明條件、事件、獎勵及命名空間的原服封包與狀態記錄。缺少這些來源時，解殼 EXE 的 UI 消費函式本身不足以重建所有原始服務端輸入。

原生完整可玩任務驗收：目前 **0 個完整任務**；418 任務的全部靜態定義與說明接入不等於 418 個可玩任務。每日 85 筆是另一來源命名空間，不能直接相加宣稱 503 個獨立任務。

整體可玩完成度維持約 **11%（規劃估計）**，不是量測封包覆蓋率，本輪資料與解析接入不增加可玩任務百分比。
