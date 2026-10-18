# 台服命中、閃避、暴擊續追（2026-10-18）

本輪依使用者要求繼續 REA 逆向，並以內部黑箱驗證。尚未取得原服完整的命中、
閃避、暴擊機率或倍率公式；下列是擴大來源追查與排除候選的具體進展。
未更動任何 CUSTOM 戰鬥規則，也沒有把結果顯示或亂數餘數升格為原服公式。

## 來源及分析方法

現用 `God2/God2.exe` SHA256：
`aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48`。
只用目前台服來源；無正式玩家 DB、原服連線、角色登入或客戶端視窗操作。

外部證據根目錄：
`C:/Users/risei/.codex/artifact-archives/god2-server/20261018/combat-probability-followup/`。
外部 Python helper 均先 AST 解析才單次執行，沒有新增專案 Python。

REA 使用保留原始各 section 位元組的分析 PE。新增 export 名稱與分析入口 CALL
皆為 analyst seeds，不是原始符號／原始 callers，分析映像禁止執行。
v1 只有三個入口被 Ghidra 建成 function；v2 用明列的分析入口連到既有真入口，
補齊所選函數；v3 擴展到 26 個入口，v4 到 35 個分析 CALL 目標。
原始 section SHA256 逐一保留於 provenance，v4 再逐 byte 核對原始 sections。
不能把新增分析 CALL 當作原程式可達性。

## 全 .text 亂數來源盤點

`full-text-rng-inventory-v1.json` 對 `.text` 每個 byte 的 E8 檢查 signed rel32
是否到 `00547D7F`，另查 named RNG import／FF15 與此函數絕對指標。
找到 **50 個 E8 候選**，其中 **40 個**可由推定 compiler entry 的指令控制流走到；
**47 個**位於舊研究 `00516000..0052E000` 範圍外。沒有 named RNG import 或
`00547D7F` 絕對指標命中，不等於排除所有間接 RNG、其他 RNG 或 inline 算法。
CFG 有入口候選、32KB span 與指令數限制，沒有替 indirect jump 補造分支。

REA 先對其中 39 處所屬的 17 個不同推定入口反編譯成功；對應證據：
`ev_d387ed19e90b68f30fc60cc6bfe809b8e7d1cb7501a7d85e295f8316ee3b1b3d`。
這些資料流包含：

| 原生入口 | 實際觀察 |
|---|---|
| `004061D0` | 每秒的 `%2` 結果選 action 10／11 |
| `00409590`、`0040C470` | `%7`／`%10` 寫入 `+152A0/A4/A6` 的 byte／bitfield，再更新 GUI；沒有證據把它們命名為四維 |
| `00410500` | 初始化 16 個 byte，並調用 seed 及 context 初始化 |
| `00411200` | 使用餘數與排重迴圈產生 permutation；caller 的遊戲語意仍需另外證明 |
| `0043A690`、`0043BBD0`、`0044B260/3C0/520` | 由剩餘未選索引取樣，更新選用 bit 與 remaining count；部分有原 TileType assertion |
| `00454210` | 亂數餘數選擇 char pointer 清單中的文字 |
| `00466B00` | `%2`／`%3` 修飾符號與座標偏移；沒有命中／暴擊門檻綁定 |
| `00474AB0` | 產生 `%04dtest` 名稱及 packed 測試記錄 |
| `00475400` | 隨機選資料列及 packed 欄位，交給另一 consumer；尚不賦予原服概率規則 |
| `004D7900` | `%3 + 0x1E` 送給 action consumer |
| `004DACF0`、`004DC370` | `%3` 寫 GUI 狀態並選 action／control |

以上為所選函數的資料流觀察，不是其所有 callers 或全遊戲語意閉包。
17 個入口涵蓋 39 個新舊掃描 caller；另 `00519E30` 已在下節列出，
合計對應原 CFG 支持的 40 處。

續查剩下 10 處：較寬的入口候選找到 6 個額外 CFG 路徑；`004F76D0` 是直接
以 CALL rand 開頭的短函數。`0044B670` 前面是上一函數 RET、`00522FB0` 前面
只有一個 NOP，因此先前要求至少兩個 padding byte 的入口掃描會漏掉它們。
兩者現在均由 REA 建出函數，並觀察到各自的 rand 呼叫。最後 `0052A89D`
歸屬已反編譯的 `0052A7F0`。

`rng-callsite-closure-v1.json` 現逐筆列出 **50 處直接呼叫 → 28 個入口**，
每筆附原始 call VA、entry、入口資格與 REA evidence ID。新增九入口的 REA 證據：
`ev_9003c893da05978bf69ad16be3dd5b19d7c537d73e31189c61f6677edde8e2d6`。

| 新增原生入口 | 實際觀察 |
|---|---|
| `00409FD0`、`004FA8B0` | 對 36 個文數字元做 `%36` 交換洗牌，逐字傳給 consumer |
| `00442020`、`0044ACF0` | 原 TileType_Ani／image assertion、影格索引與時間更新；rand 餘數選影格 |
| `0044B670` | 未選索引中抽樣，標記選中並遞減 remaining count |
| `0047FC60` | 輸入 `DC..E1` 才映射成 `rand()%6+DC`，其餘 byte 原值傳回 |
| `004CDBC0` | 輸入等於 `DC` 才映射成 `rand()%6+DC` |
| `004F76D0` | 回傳 `(rand()+argument)&3`，尚未建立原始 caller／遊戲語意 |
| `00522FB0` | 動作狀態機內 `%5` 寫 actor `+1E6`；所見後續路徑以既有 `+286` 量更新 HP，沒有由此亂數與攻守能力比較的門檻 |

`0047FC60` 的兩個原生 callers 另外反編譯：`0047FBB0` 讀 36 格 byte 表，
`00480890` 將重映射 byte 傳入 `00460300(...,400,300,0)`，再交給
`00497E00`；尚不把這個 byte 命名為暴擊結果。
證據 `ev_9049d50f65f07058198da2b48a31297b6f1b7f2d5f6dd00d78975a4b7f86847f`。
其餘兩個短函數的 REA incoming 只觀察到分析 CALL，不能當作原始程式不可達。

這個 50→28 是本次直接 E8 候選的定位閉合，不是所有 RNG、所有 consumers、
原始伺服器或全程式公式閉合。尤其小範圍代碼仍可能有尚未確認的下游用途。
完整 REA envelopes 存於 `rea-selected-records-v1.json`、`rea-selected-records-v2.json`。

## 完整技能及乘法候選

REA 已輸出 `00526890` 的函數反編譯及組語：所見狀態機管理目標、動作與既有量。
Ghidra 有移除 unreachable block 的警告，不把偽碼輸出視為所有分支的語意證明；
下述測試片段另由原始組語及機器碼核對。
所選 case6／type `0x77` 分支在 `00526E1E` sign-extend source actor `+28A` 的
WORD，`00526E25` 調用真實 `00528A70` 更新目標 HP；這段沒有暴擊倍率乘法。
`00528A70` 是 32-bit wrap ADD、負數歸零與 signed maximum 比較。
它不是產生傷害的攻防公式，也不能據此截斷共用 64-bit 服務端狀態。

`00519E30` 已恢復完整函數：K × descriptor 高 nibble 的運算仍存在，
但與攻防、暴擊判定及權威傷害寫回的關係仍未建立。整個函數另有 `%10`
文字格式化及 `00496990` 送出鏈。原始 caller 可達性、K 的填入來源仍缺；
分析入口新增的 xref 不能補這個缺口。

最新現用 SHA 的 `k-table-literal-leads-v1.json` 補做全 `.text` literal 掃描：
搜尋 `+A9EA4F0/F4/505/508/598`，共 7 處 literal 命中；逐位移位置對照
Capstone 指令候選與原始窗口，尚不把候選邊界升格為全程式 CFG 證明。

- count 的 4 處：`00510EFE` 是 LEA，`00519E44/00519FDB/0051A8E7` 是讀取。
  初始化原始窗口有 `MOV ECX,2B; XOR EAX,EAX; LEA EDI,[ESI+A9EA4F0]; REP STOSD`，
  只證明這段清零 43 DWORD。
- `0051A004` 的 LEA 先取 `[ECX+EBP+A9EA4F4]`，後續 descriptor／K 透過此指標
  加小偏移讀取；未直接出現 `A9EA505/508` 的 literal，並不表示欄位沒被讀寫。
- `00519E52` 讀 timestamp，`00519E68` 寫 timestamp；這不是填入 K。
- 原始 `.text` 所有 byte 的 E8/E9 rel32 與全檔 `00519E30` 絕對值搜尋都未命中。
  這只約束直接編碼，不排除計算／間接 caller、別名、offset 變形或 bulk copy。

本輪仍沒有找到非零 count／K producer。別名追蹤與自然可達性維持開放，
不能由上述負向結果宣稱它不存在或宣稱整個客戶端沒有戰鬥公式。

選定 REA 證據：
`ev_30d683f2da74c4600bbf7a6fc73ec8001031ada78293c74e64162ec7a095af3b`、
`ev_d427701242a2ca895d827b8938a9e5b13d574c2a142fc86fe03dcc8d44d5373e`、
`ev_899d06e98bd68f6c53ed34f1f6b8e39caa79c605a36bf4d96fe4150a05b1607b`。

## 本輪內部黑箱

`master-applied-amount-native-v1.json`：**160 項通過**。
直接執行目前 EXE 的 `00526E1A..00526E2A` 片段及真實 `00528A70`，沒有替換
native callee。起點明列為「已完成目標選擇、已進入 type77 分支」的合成狀態，
不是整支技能、真實封包、原服交易或原版視窗驗收。

交叉測試 signed WORD `-32768/-100/-1/0/1/2/100/32767`、五種 current/max 組合、
00/A5 surrounding bytes 與 selected-owned-target 分支。核對真實記憶體讀寫、
堆疊回復及所有執行 PC；量由 `source+28A` 讀出，直接用於 HP 更新。
此片段沒有重新擲命中／暴擊，也沒有額外乘倍。證據僅排除這段是倍率產生者，
不排除其上游由服務端或尚未確認的路徑先算好該量。

入口 fragment SHA256：
`47f41e361006027209319ed1bff5bd7576f613a3118fe0cd2d7913825464b69a`。
HP callee 80-byte SHA256：
`a3688c33bc14844c08debddbe64da043db65c361147125f7ab0cf4df0fa5fd65`。

## 仍需取得的證據

命中／暴擊能力的身分與來源、與攻守雙方／技能的綁定、亂數門檻比較、
結果 flag 語意，以及倍率／減傷／取整／上下限的完整順序仍未建立。
現有 basic／skill C2S 結構只證明請求與目標／技能識別；opaque 欄位仍保留，
不能宣稱所有請求變體都沒有任何相關資訊。
本輪沒有新增可匯入正式 DB 或取代 CUSTOM-0006 的原服公式。

本輪收據為外部 `round-verification-receipt-v1.json`（50→28、160 PASS）及
後續 K 表 literal 掃描檔。REA 已關閉；正式核心、客戶端及資料庫未因本研究修改。
整個 `Desktop/God2` 最新保守 logical file length 合計約 19.724 GB，低於 30 GB。
