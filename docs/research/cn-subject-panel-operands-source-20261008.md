# 陸服 WORLD31 後續面板整數運算元

本輪 `20261008-cn-subject-panel-operands-source` 沿用已封存的 WORLD31→
004D58B0→004D5030 關聯，新增精確、唯讀的面板投影來源。
原生 EXE SHA256 為
`582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`。
未執行原生程式、C++、服務、Windows API、Lua、SQL、建置或測試。

## 目前指令對舊反編譯文字的修正

004D5030 的 ordinary 分支在 004D5124、004D5261、004D527B、
004D5295 都是 MOVZX，讀取 row+38/3A/3C/3E 的 unsigned WORD。
special 分支同樣是 MOVZX。row+34/36 在 004D50F7/004D50FC
也以 MOVZX 讀取。舊 113 報告中「mixed signed/unsigned16 display」
不是這六個 WORD 的目前指令語義；原報告和封存保留，本輪另記修正。
row+2 在 004D507E 確實是 signed BYTE，而 row+0 在 portrait 路徑
004D532E 是 signed WORD，不能把這兩處的符號套用至其他欄位。

| 原生 control | 實際 row offset | 原生輸入 | special UI WORD |
| --- | --- | --- | --- |
| 6 / 7 / 8 / 9 | 38 / 3A / 3C / 3E | 零擴充 WORD | 42E14 / 16 / 18 / 1A |
| B / C | 44 / 48 | DWORD 原 bits | 42E1C / 1E |
| D / E / F | 4C / 50 / 54 | DWORD 原 bits | 42E22 / 24 / 20 |
| 4 | 2C / 30 | 兩個 DWORD 原 bits | 無 |
| 5 | 34 / 36 | 兩個零擴充 WORD | 無 |

special 判定是 16 位元 `(rowWORD0 - 101) <= 7` 的 unsigned branch，
即 101～108，與 portrait 的 signed 比較是不同分支。九個 scalar 的
literal 是 `%d`，DWORD bits 的十進位有號解讀保留；特殊列的 DWORD
ADD 保留原生 32 位元呈現結果，不能用作共用 64 位元玩法結算。
control F 的加值順序不同，沒有依 control 編號順序錯配 UI WORD。

## 來源接合

新增 `CnSubjectPanelOperands`，從實際保留的完整 1004B row 擷取原值。
`CnWorldConsumerSource::OwnedRowUpdate31::panel_operands` 直接使用既有
WORLD31 投影後的 row，沒有再建立第二套封包解析器。九個 UI 加值只有
明確傳入實際來源才存在；special 列缺少加值時，有效顯示運算元保持
unknown，ordinary 列不套用 special 加值。不要求原生 process memory、
HANDLE 或 pointer，亦不建立共用角色 ID、怪物屬性或權限。

004D5440 的 row+28 是 unsigned WORD，使用 DIVSS 除以 EXE
007F2C70 的 `0000c842`，即 100.0f；control 為 24，ProgramMsg pointer
index 為 164，signed count 必須至少 165。保存 literal、除法/轉換/兩個
文字 stage 的指令來源及原有 message.csvZ 解碼收據。
這份静態 CSV 的 ProgramMsg164 是「法术: %d/%d」；原生 call 傳遞的
卻是單一 double bits，不能把靜態 CSV 項目冒稱為實際 GUI 文字或直接
替代 runtime text provider。投影只保留 numerator、divisor bits 和 index，
不執行浮點/格式化、也不猜能力名稱、比例公式或實際渲染結果。

## 保留缺口

實際共用主體／收件者／名冊／全部欄位語義、UI readiness 和加值來源、
全部 helper／上游與變體、原生規則、存檔、持久重播、已提交事件 issuer、
Application 仍未接齊。本輪不新增 opcode、phase binding 或 owner；
完整雙向路徑增量 0，全遊戲分母／完成數／百分比仍未知。
TW/CN/PC/網頁、共用資料、64 位元數值、合格堆疊 99 及集中測試、
修復、可恢復發布等完整目標保留；仙幣上限 99,999,999,999、等級不改。
