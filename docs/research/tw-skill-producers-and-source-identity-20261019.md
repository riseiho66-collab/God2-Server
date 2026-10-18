# 台服技能數值來源與現用資源身分續追（round455）

本輪繼續追技能傷害、治療、持續效果、攻防減傷、五行與抗性，以及命中／暴擊
的原始 producer。新增九函數 REA 證據，區分收到量的型別、技能定義指標、
UI 索引與技能書查找。所選鏈仍沒有產生原服傷害／治療公式；不能把成功反編譯
或收到量的套用計為完成玩法。

## 本輪來源與方法

| 現用檔案 | SHA256 | 範圍 |
|---|---|---|
| `God2/God2.exe` | `aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48` | 現用台服 EXE，3,237,888 bytes |
| `Data2/Fight/Spg/cbspec2.bin` | `3adcda70a477086da50411fe5d023eec33f915efafd17ec478d55542cae42ea7` | 453 筆，四 bank 為126/129/87/111，每筆110 bytes |
| `Data2/Patch/Comm/gamedata.csvZ` | `ef297a84e828537c4a18c5cf0be3d1c15bc26d5d2f25850ce9f2f030bdb58fa2` | 現用壓縮資源身分；本輪沒有解碼 |

外部完整證據目錄：
`C:/Users/risei/.codex/artifact-archives/god2-server/20261019/formula-producer-followup/`。
使用既有 REA6.5.0 公開 launcher 與 Ghidra；新 helper 先 AST／語法檢查後單次執行，
失敗版本保留。v11 分析 PE 的 SHA256 為
`6b2c8e0a4665a00033ac7aa679aa3efb65793d4bf87e2c0d3498bc49819cf128`。
13 個原始 sections 與現用 EXE 逐位元組相同；新增64個 analyst CALL 只供辨識入口，
不是原始 caller，分析映像沒有執行。

queue續追另建v12，SHA256為
`bbbae860acbbed8c343a6ff97fb2a554f303e5d65d4e043ea4c2915ff012c81c`，
保留相同13個原始sections並使用66個analyst CALL，仍未執行。

七函數 batch 為 `004A92D0/004AF4E0/004A97E0/004A97A0/004A9710/004A8E10/00528B10`，
完整偽碼與所選組語保留。Evidence：
`ev_6d6a70473fdd49c557e780c3a5ffc4f7a0212aa310bc062f63f79d42738767ac`。
第二batch為 `00401000/005140C0`，Evidence：
`ev_79ba752da54cde1e241171093e9cb7907785286db5051aced7355d8dfdf2078f`。
兩次REA session均已關閉。
沒有建置、測試、遊戲／網路、native/VM、codec、遊戲 DB SQL、遷移或部署。

## 同一 actor 欄位不是同一公式參數

`00528B10` 的原始直接 caller 為 `005291EC`，屬 scheduler 的內部播放狀態85h；
不能將85h稱為 wire opcode。source actor `+235` 經 `0051E6E0` 選出 target actor，
`source+233==4` 才進入以下套用階段。判定欄位是 **target+232**，不是 source+232。

| target BYTE+232 | source 欄位 | 原始 consumer |
|---|---|---|
| 77h | signed WORD+286 | `00528E1D → 00528A70`，HP 更新 |
| 78h | signed WORD+286 | `00528E53 → 00528AC0`，MP 更新 |
| 79h | signed WORD+286 及 signed WORD+288 | `00528E43` 更新 HP，`00528E53` 更新 MP |
| 96h | BYTE+286 | caller 第二參數非空時，`00528DE7` 寫 context+0B |
| 59h | 不以此分支讀取扣補量 | 呼叫 `005267C0(target,59h)` |
| 其他值 | 不以此分支讀取扣補量 | 呼叫 `00526430(target,type)` |

完成後將 source+1EA 清零、source+259 設1並回傳1。
本輪靜態 CFG 另以原始 jump table `00528E84` 閉合所選294條指令；
這不是執行可達性或全函數 gameplay 驗收。

量的上游仍是接收：既有 `0052B060` 的第五／第六參數 low16 分別寫+286/+288；
`0052C520` raw action04 將 logical WORD+9/+11 轉送為這兩個參數。
raw action07/09 也有 logical WORD+9 →+286 的寫入。`0052B060` 對 action5 的
模式22h/23h/24h分別格式化 HP、MP、HP與MP；文字格式化不生成治療量。

上一輪 `00528580 → 00527310 → 0052DCC0` 則將 +286 解為 packed selector。
因此不能把所有 +286 寫入都命名為 damage 或 heal，也不能由 signed WORD 的
正負推導技能係數、最大 HP 比例、攻防運算、相剋矩陣或扣補順序。
詳細來源在 `amount-source-chain-manifest-v1.json`；舊52B060證據屬交叉核對，
沒有當成本輪新恢復的函數或公式。

本輪再將 target+232 的寫入端與上述 consumer 接起來：
`0052C000` 由原始表 `00571610` 將收到的 selector 映射後交 `0052C0C0`。
所選22h/23h/24h/2Fh/1Bh分別映為77h/78h/79h/96h/59h。
basic分支使用同一source+235選出target，通常在 `0052C19F` 寫target+232；
target原為9時保留既有狀態，只有mapped59h且action05的選定分支可在
`0052C1B9` 改寫59h。mapped result82h另在 `0052C163/0052C169` 寫source+232
並清target+232，不能將全部分支概括為同一target store。
skill03/17則由source+23A[index]取target，在 `0052C29A` 寫target+232與
source+224[index]；已有9且mapped type非59h時保留9。

另外展開 `0052A8D0` 的23-entry原始表及 `0052B060` 的9-entry格式表後，
所選CFG分別有212／586個指令，沒有未展開indirect jump。
前者只見action08在 `0052AA8D` 清source+232；後者的限定CFG沒有+232存取。
這些是接收分類與播放保護，不是數值或機率公式，也不排除callee／bulk aliases。
`amount-target-type-producers-v3.json` 與table receipt保留來源及原始指令。

## 技能指標與 UI 索引分流

`004A9710` 的四個參數是 kind、id、兩個輸出指標。kind在0..3時，第三參數接收
`[005B6F80+kind*4]`；第四參數接收 `[005B6F70+kind*4]+id-1`。
第四個輸出沒有相同的 kind 範圍 guard，不能宣稱此函數對所有無效 kind 都安全。
它不是回傳110-byte技能定義的函數。

真正送往本輪名稱格式化函數的定義指標鏈為：

```text
owner+86888 → role+0D0 → 004AF5C5/004A9110 找 slot
→ 004AF5E3 讀 subordinate+258+4*slot → 004AF5F3/004AF4E0
```

`004AF4E0` 讀定義 WORD+42，並從 `004A8E10` 找到的另一種396-byte記錄取名稱+8，
組成 F鍵序號／名稱／MP 文字。這不是傷害或治療運算，也不能把顯示 MP 的讀取
直接當成服務端實際扣魔。`NativeSkillRecord::client_mp_threshold()` 已有相同
WORD+42來源界線，本輪不另造 authoritative cost 欄位。

`004A97A0` 由 subordinate BYTE+1F0 算 `ceil(count/25)`，寫+3E9，並將page+3E8清零。
`004A97E0` 設定 role，呼叫分頁初始化，再把 `00459FC0` 的四個值加41h，放入
005B6F80四個 UI bank。這些加法不是技能倍率。

`004A92D0` 先要求owner signed WORD+232DDC>=0、role+0D0非空及技能count>0，
再比對定義的 kind/id，並要求定義 BYTE+67非零及
`subordinate[1F1+slot]&1`，然後選 page=floor(slot/25)與 slot%25。
現用453筆資料中，BYTE+67非零的各bank數量為3/3/3/35。
目前只證明這個選頁／選取 predicate；不把 BYTE+67命名為命中率、暴擊率或治療率。
原始指令與欄位身分在 `skill-qualified-flags-and-ui-chain-v1.json`。

## 技能書證據的現用身分缺口

本輪 REA 再次確認 `004A8E10` 的 kind→token 為0→SpcA、1→SpcD、2→SpcC、3→SpcB。
它透過 `00459A60` 查396-byte物件，按原始 bank base+1..399升序搜尋；
比對物件+11C的 token，id<100比較6 bytes，否則7 bytes，第一個命中為準。
不能由技能名稱或 bookID減法替代；miss也不保證清掉 caller 舊輸出。
Ghidra 將此函數推為void，但 caller使用其原始EAX結果；不以推測prototype取代組語。

保留的 SKB381 matrix 來源是舊 decoded SHA
`75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815`，
對應舊 raw `gamedata.csvZ` SHA
`70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`。
現用 raw 已為ef297...，本輪未找到其完整已解碼來源，也沒有執行codec。
歷史 PET147 部分相等不能替 SKB381 作證。

舊matrix確有 SpcD04/12/20/28/36→6604/6612/6620/6628/6636的各別原始row，
但這只支持歷史資源中的五筆。不能將它接到現用453技能、現用描述或原服公式，
直到取得 current-qualified SKB rows／完整plaintext與各自雜湊。
`source-skill-book-current-identity-boundary-v1.json` 保留此更正與來源身分。
舊[技能書研究](current-skill-book-binding-20260920.md)已補日期警示，原文與舊結果保留。

## 453筆來源與權威技能仍須分別驗證

`TaiwanInstalledSkillCatalogSource` 已保留現用453筆、完整檔案與各row身分。
但 `Config.h` 預設仍為 Historical448；`Config.cpp` 支援明確的
`database.taiwan_skill_profile="installed453"`，現有 `config/server.json` 沒有此欄位。
這是所讀來源設定的事實，不是現行執行程序或 DB 內容的查證。
本輪沒有開啟DB、切換profile，不能宣稱目前 gameplay 已採用453筆。
正式掛載仍須保全既有角色與學習資料、核對完整候選來源，再在後續授權階段驗收。

現有 `SharedTaiwanNativeSkillCommandSource` 還缺真正 WorldOwner提供的學習／控制／
授權、原生費用與規則，以及完整結算。現用戰鬥 Lua 的 CUSTOM-0006／CUSTOM-0090
仍是自訂攻防與暴擊規則，不能重新標成 REA 找出的原服公式。
自訂技能126／150的正式規則保留；installed453的kind0 bank只有126筆，
不能為技能150虛構一筆原生installed row。

中毒每次扣「當前最大HP十分之一」是使用者既定要求。本輪在所讀 src/scripts 的
C++／Lua字詞與除10形式搜尋中，未找到符合的 gameplay 實作；此為有限搜尋，
不排除其他命名／別名。真正狀態建立、技能綁定、觸發／清除與原子結算仍缺，
不能把規則已寫進 AGENTS 當成中毒玩法已接通。

## K相鄰queue的複製目的地與長度

上一輪保留 `0051D3D0` 將queue資料複製到caller目的地的缺口。本輪在現用
原始.text找到七個直接caller，全部位於 `005140C0`。展開三個有明確guard的
原始switch table後，限定CFG共403個指令，沒有indirect stop或budget截斷。
七處的ECX均為owner+A9EA4B0 queue，EDI為owner+A9E9CB0目的地；首處peek，
其餘推進read index。根函數建立EDI後沒有改寫它，跨callee保留依賴原生ABI。

長度鏈為 `00415840 → 00401000 → 00401200`；401000先將opcode截為low8。
401200先unsigned檢查opcode<=FD，再查原始 `00401324` 的254項分派表。
252項為literal-return leaf（其中22項為-2），21h/25h為OR EAX,-1；
所有正數長度最大2105 bytes。目的地距Kcount（owner+A9EA4F0）為2112 bytes，
因此正數固定長度直接copy的最大exclusive結尾為owner+A9EA4E9，尚差7 bytes。
正常固定長度的這七處copy不能填入Kcount或其後K rows。

REA `005140C0` 證實此queue在 `00529020` 播放更新後，逐筆peek收到的record，
再呼叫對應handler並consume。83走 `00516AE0`，84走 `00516740`，
86有原始七子型別表，87/88/89各走 `00517540/00518A90/00518BF0`。
最後呼叫 `0052AC20` 設定播放排程；沒有在本函數生成所追的K或戰鬥數值。
此queue非default分支實際為1C/38/83/84/85/86/87/88/89，固定長度各為
45/2/15/15/2/17/3/121/57，最大121。清單由 `0051465C` 的110個mapping bytes及
`00514634` 的10個pointers推導，並與新REA一致。
這只排除已綁定的正數copy；負數variable sentinel、異常狀態、wrap、heap aliases、
其他callee與間接caller仍開放，沒有取得非零K的實際producer。
詳見 `k-queue-read-destination-conclusion-v2.json`、v2原始length table與CFG證據。
v1的手動opcode清單曾抄錯，交叉核對後以v2取代，失敗證據保留不改寫；
全254項長度與2105上界獨立於該清單。root另直接讀現用PE原始bytes，核對全表、
九個queue分支與五個selector映射，保存在 `selected-native-tables-static-receipt-v1.json`。

## 尚未恢復與本輪盤點

命中／閃避／暴擊門檻、技能傷害／治療生成、DoT實例與週期、攻防減傷順序、
五行相剋矩陣／抗性仍未得到完整原始公式。K非零參數與count的實際寫入端仍須追。
收到封包的顯示／套用函數，以及UI條件與歷史描述，不補造上述權威規則。

本輪唯一正式靜態報告為 `round455-tw-skill-producer-source`，執行前先reservation。
沿用149c...歷史封包格式索引，不能當成 aaf0...的全量重新盤點。
全遊戲分母、完成路徑與完成率維持null；本輪完整玩法新增0，goal保持active。
