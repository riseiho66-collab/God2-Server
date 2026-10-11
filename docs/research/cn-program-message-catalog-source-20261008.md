# 陸服 ProgramMsg 文字來源與 WORLD31 metric 接合

本輪 `20261008-cn-program-message-catalog-source` 接續已封存的 142。
原生 EXE SHA256：
`582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`。
PHASE1：未建置／測試／執行 C++、原生、服務、Windows API、Lua、
SQL、loader、formatter，沒有匯入、遷移或部署。

## CSV ID 與 pointer index

沿用已知 00428C80 ProgramMsg 分支，本輪從真正函式入口追完整局部
normal-call-return CFG，確定 00429555 的 DEC EAX 將 CSV ID 減1，
004295A6 按 `table[index*4]` 存入字串 pointer，004295E1 保存最大 ID
至 owner+B2F64。不是 CSV ID 自身作 zero-based index。

因此 004D5440 的 pointer offset290／index164 對應 CSV ID165，
其文字為 `%6.2f％`，符合傳入單一 double 的格式。上一輪 142 把
CSV ID164「法术: %d/%d」當作 index164 的候選來源而留下的 mismatch，
在這個限定來源關聯上已釐清。142 的報告、程式、封存均原樣保留；
本輪明記更正，不能把此更正冒稱為先前證據本來就齊全。

row28 為原生 unsigned WORD，DIVSS 除以100.0f，後續以 double
交給格式化。這是面板百分比文字來源，不證明伺服器成長、攻防、
HP、MP 或其他屬性公式，也沒有執行浮點／格式化或接受實際 GUI。

## 實際供應器來源

新增 `CnProgramMessageCatalog`：實際 encoded／decoded 兩份輸入複製
後核對精確 hash，限定目前版本與实际 resource revision／Current。
完整保留 ProgramMsg 的1116列、原始行、CP936 bytes、原生 ID、
zero-based index、來源行／offset、每列 hash。

encoded message.csvZ 為59375B，SHA256
`9c027fdd114073fe9fc88776f7713c0e60575fbe1a2f15059e9bda01a9ec181e`；
decoded為112839B，SHA256
`994088ac79051df74b3569fc102ab39849594409964a674796bd67fd9d4bc054`。
ProgramMsg header在89354，1116筆資料從89371至112839，
source line從2028開始。這是釘定區塊投影，不是通用 CSV／native VM。

004231B0 明確在缺欄位／空欄位時寫入 NUL。此資料 ID9／497／886
沒有文字欄，保留原生空文字；ID291 的額外第三欄保留在 raw line，
不追加至 native column1。這些空內容不是補造的成功值或缺失屬性。

提供 `lookup_id` 與 `lookup_zero_based_index` 兩個明確入口，輸出 owned
record，查找前後均觀察同一 Current。`CnSubjectPanelOperands::Metric`
改為同時明確標記 pointer index164／CSV ID165，並直接向實際 catalog
取得這筆文字來源。不要求 process memory／HANDLE／native pointer。
CP936 是原始資產 bytes；共用遊戲文字及使用者呈現仍走既有 UTF-8、
明確編碼邊界及繁簡轉換，不把 CP936 資料當 UTF-8。

## 剩餘缺口

供應器 factory／Windows hash source 未在 PHASE1 執行，Application
尚未配置實際 resource revision／Current。真正 GUI readiness、loaded
runtime resource、百分比渲染及所有 helper／上游／玩法變體仍未驗收。
共用欄位語義、主體／收件者／名冊映射、規則、存檔、持久重播、
已提交 issuer 及完整 TW/CN/PC/網頁/WSS 功能仍未完成。

本輪供應器1、既有 metric 文字來源接合1、ID/index更正1。
1116列只是資源列數；opcode／phase／owner／完整雙向路徑增量0。
全遊戲分母／完成數／百分比未知。64位元數值、堆疊99、等級不變、
凍結功能及集中測試修復發布的完整目標保留。
