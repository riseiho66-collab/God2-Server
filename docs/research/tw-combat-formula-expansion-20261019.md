# 台服戰鬥與技能公式擴大追查（2026-10-19）

使用者要求三路並追，並追加技能傷害、治療量、持續效果、攻防減傷、五行相剋
及抗性。本輪完成新的靜態追查與 REA 函數分析，沒有恢復原服完整公式，也沒有
改寫既有 CUSTOM 規則。完整遊戲完成率仍未知；研究入口數不是玩法完成數。

## 本輪來源與執行界線

目前 `God2/God2.exe` SHA256：
`aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48`。
現用 `Data2/Fight/Spg/cbspec2.bin` SHA256：
`3adcda70a477086da50411fe5d023eec33f915efafd17ec478d55542cae42ea7`。
這份 BIN 是 **453 筆**，kind0/1/2/3 數量為 126/129/87/111；舊研究的 448 筆
`7676...` 不能當作目前全檔身分。原始每筆 110 bytes 與 file offset 已保留。

外部證據目錄：
`C:/Users/risei/.codex/artifact-archives/god2-server/20261019/formula-expansion/`。
新外部 Python 先 AST 解析再單次執行；因舊 BIN pin 拒絕的 v1 保留，另製 v2。
專案沒有新增 Python。沒有建置、測試、VM、遊戲執行、資料庫、部署或玩家資料操作。
10 月 18 日的 456 項名稱別名原生測試是前輪證據，本輪沒有重跑或計入新測試。

REA MCP 工具在本次連線不可用；改用已安裝 REA 6.5.0 的公開 launcher、
本機 Ghidra 12.1.2。只在分析子程序提供既有 Ghidra 路徑，沒有修改註冊或安裝。
透過同一公開 launcher 的 stdio 工具執行 batch，完整 Evidence 與 close 回覆外存。

v5/v6/v7/v8 分析 PE 保留原始 sections，新增 CALL 只用來建立分析函數。
這些 CALL 不是原始 caller，也不證明自然可達性；分析 PE 不得作為遊戲執行。
`formula-seeded-v*-provenance.json` 保留鏈與 source SHA。

## 乘法表與別名來源

前輪 `k-alias-neighborhood-v1.json` 擴大到 owner-relative `A9EA300..A9EA700`，
定位 row pointer `0051A004` 與相鄰狀態／queue／timer 欄位。
已實際反編譯的 `0052DD30` 會比較該 row 的字串與 actor `+DBE`，透過
`0051E6E0` 找 2 side × 14 slot；它不是填入 K 的 writer。
前輪 456 項完整函數及真實 lookup 的測試只證明這條別名路徑無非 stack 寫入，
不證明其他別名不存在。非零 count、K producer、bulk-copy／間接 caller 仍未找到。
本輪沒有把該文字投影乘法升格為傷害、減傷或暴擊倍率。

## 命中、閃避、暴擊與結果來源

`result-source-static-v1.json`、`result-classification-static-v1.json` 保留目前 EXE
的 exact bytes、上游指標與限定入口反組譯。
`00516AE0` 將 logical record 指標加一，經 `00517183` 呼叫 `0052C520`。
basic amount 是 logical WORD `+9`、basic result 是 logical BYTE `+11`；
skill 的 amount 仍在 `+9`，classification 使用不同尾端欄位，不能混用。

REA `0052C000 → 0052C0C0`：先以 `00571600` 的 13-byte 表將結果代碼轉成狀態，
再查 `00571610` 的 67-byte 表，最後寫入 actor state。
raw7→state3、raw8→state5、raw11→state82；這是收到結果後的映射。
basic 寫 `+1E8/+1EB`；skill 寫 indexed `+216/+208/+224`；
`param_5==0D` 另寫 `+27A/+27D` 的 indexed 狀態。防禦、state9／type59 等條件
影響播放狀態保護，沒有從攻守能力擲命中或暴擊的比較。
basic 表在舊研究已知，本輪價值是現用 SHA 的重核與技能 indexed stores，
不能重新計為原服概率發現。

## 技能傷害、治療及持續效果

`skill-selected-pointer-candidates-v2.json` 保存 18 處 `+EC4` 位移候選與 453 筆
BIN 原文；局部指令與直接 pointer alias 掃描不是所有技能 reader 的閉包。

REA `00526120` 對 definition WORD `+4C..64` 逐個判斷是否非零，再將**同一個
呼叫者提供的 amount**傳給格式化函數。它不將這些 WORD 乘入 amount；
因此欄位非零與標籤不能直接當作技能傷害、治療或五行係數。

REA `0052C4B0` 只讀 definition kind/id，kind1 IDs4/12/20/28/36 回1，其餘／null回0。
目前 BIN 名稱是金／木／土／水／火之術Lv4。
`0052909B`、`0052ACD9` 都傳 actor `+EC4` 給它。
它們與舊 SKB 五行壁／五回合文字的 join **未驗證**，不能由數字相近補造關係。
修正版 `skill-wall-identity-gate-static-v2.json` 明列這個界線。

REA `0052AC20` 走訪兩 side、每 side14 slots，依 `+1E9/+1E7/+233` 與 manager
`+308/+30B/+30C` 選 action，寫 active count，最後取時間寫 `+A7FBCC0`。
它是動作排程入口；本函數未證明五回合倒數、DoT tick、每回合治療或狀態成功率。
Ghidra 對 `0052AC80` 有 unreachable-block 警告，不能將偽碼當成全分支執行證明。

另一個新欄位變更線索 `00528580` 已由完整偽碼與組語核對：在 source state1，
`0052862B/32/39` 對 source WORD `+286` 做 16-bit NEG 後呼叫 `00527310`。
後者把該 WORD 交給 `0052DCC0`，處理 renderer handle 並呼叫 `0041AFE0`。
`0052DCC0` 現已由 REA 偽碼與組語核對；對輸入 w 輸出四個 byte：

```text
a = (w >> 9) & 1
b = (w >> 7) & 3
if a != 0: d = (w >> 4) & 7; c = (w & 15) + 16
else if low16(w) > 100: a = 1; d = 1; c = w & 127
else: d = 0; c = w & 127
```

這是 packed selector 拆解；本函數沒有傷害／治療運算。它在舊 monster-stat-frontier
研究已知，本輪新增的是目前 SHA 與 `528580 → 527310 → 52DCC0` 這條使用鏈。
先前把此路徑的 `+286` 稱作 HP 量不精確，已更正為未命名的 packed 欄位。
這條線沒有攻防／抗性輸入，也沒有寫 actor `+DE8` HP；不能命名為吸血、反傷或治療
公式。`8000h` 在 WORD NEG 後仍為 `8000h`，屬機器碼寬度語意，不是合法玩法量範圍。

## 攻防減傷、五行相剋與抗性

本輪 REA 重核 `004E6600`：S2C2C body 的五個 DWORD 原樣寫入 role `+A4/A8/AC/B0/B4`，
四個攻防 DWORD 原樣寫入 `+98/94/A0/9C`，再調用 `004E6710`。
`004E6710` 將五個值傳給 GUI control19..1D，四個攻防值傳給 control18/17/1F/1E。
另依既有 masks 調整四個修正 WORD 的正負顯示。`004E6DB0` 是相關面板更新。
這些已存在的接收／顯示機制，本輪是現用 EXE 的 REA 重核，不是原生減傷或相剋公式。
五行欄位與名稱、五行相剋矩陣、抵抗率、上限及減傷順序是不同證據要求；
目前沒有建立從雙方五行／抗性到權威 damage 的運算鏈。

## 其他 RNG 與時間門檻

`rng-alternatives-static-v1.json` 搜常見 LCG/MT 常數、硬體 RNG 指令、
random／clock imports 與局部三移位／兩 XOR 形狀。
所查常數只定位已知 CRT `00547D87` 的214013與 `00547D8D` 的2531011。
沒有所查 RDTSC/RDTSCP/RDRAND/RDSEED 或局部形狀候選；這不是所有自製 RNG 排除證明。

`rng-seed-and-tick-thunks-static-v1.json`：`00547D72` 是13-byte srand leaf，
經 `0054E001` 取得 TLS，再寫 seed 到 `+14`。六處原生直接 caller 為
403DA2/409FDE/41050E/439566/4D55DC/4FA8BE，五個來源是time()，一個是timeGetTime。
GetTickCount 經 `00410360` thunk 的三處呼叫都在 `00410E20` deadline／Sleep(1)循環。

`rng-time-consumers-static-v1.json` 保存戰鬥區12處 timeGetTime 消費。
`00519E3E`、`00515BBB`、`0052948D` 的門檻分別為2000／180000／10000ms，
資料流是時間差；不能把常數誤當暴擊、命中或持續回合的機率。

## 仍開放的公式來源與下一步

| 項目 | 仍缺的直接證據 |
|---|---|
| 命中／閃避／暴擊 | 攻守能力身分→門檻→亂數比較→結果 flags 的 producer |
| 傷害／治療 | 攻防／技能係數→原始量→減傷／增益→取整→收到的 amount |
| 持續效果 | 真正 status instance、回合／timer遞減、觸發／清除、每次扣補量 |
| 攻防減傷 | 原始攻防聚合及 damage 生成順序，不能由面板接收反推唯一算法 |
| 五行相剋／抗性 | 元素身分／雙方值→矩陣／係數／抗性→量的實際 consumer |
| K 投影 | 非零資料填入來源、別名 bulk writer、原始可達 caller 與權威寫回 |

下一輪優先追 `0052AC20` timer 的真正讀取者、`+286` 各 action 的不同寫入來源、
以及五行／攻防 role 欄位被傳往何種 actor／計算物件。所有負向掃描均維持範圍限制。
中毒使用當前 maxHP 的十分之一是使用者既定規則，不能重新宣稱由本輪逆向恢復。
未經來源綁定的 raw 欄位與描述不匯入正式 DB 作為權威公式。

## REA Evidence

- `004E6600`：`ev_880cbf5e234dee7d15bbff93142cbe88aa14281b5fd119d6546ecbeeafd13b1f`。
- 八函數 batch：`ev_ce05e4faf858119cc8ba16e8ff709811b7fd61b1054b2141c63013f20e4b713e`。
- `00528580/00527310`：`ev_9189e01b8313baea889312e53086fed8d39a367b5121717bb60081fee3aff41b`。
- `0052DCC0`：`ev_62da5dc24d506d80790009617ec8cb48ce82adfacf82a123f7b07229f5039570`。

完整 raw Evidence、source hash、原始指令與 analyst-seed provenance 外存；
本文件不以反編譯成功數、static candidates 或前輪黑箱成功數代替完整遊戲驗收。

## 逐輪盤點與保存

本輪唯一正式靜態報告 `round453-tw-formula-expansion` 已預先 reservation 後執行一次，
結果與 terminal receipt 存外部 `round-report/`；沒有重跑前輪452。
封包帳本的全遊戲分母、完成路徑及完成率仍為 null，本輪新增完整玩法路徑為0。
報告沿用149c...的既有封包格式索引，不能當成這次 aaf0... EXE 的全量重新盤點；
本輪函數／BIN 身分由上面的獨立 current-source evidence 證明。
goal API 與執行帳本均為 active，後續目標保持台服單一版本與來源／靜態階段。
整個 `Desktop/God2` 本輪保守 logical file length 為19,551,323,907 bytes，低於30GB。
