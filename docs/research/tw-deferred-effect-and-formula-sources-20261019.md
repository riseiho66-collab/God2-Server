# 台服延後效果與公式來源續追（round454）

本輪延續命中／暴擊、傷害／治療／持續效果、攻防減傷、五行與抗性追查。
新證據將一個時間戳定位為播放完成／逾時門檻，閉合一條收到效果後的延後
消費鏈，並排除相鄰 queue 子物件及角色面板轉送鏈作為所選公式 producer。
完整原服公式仍未恢復；新增 C++ 視圖也不是權威玩法或自動發包。

## 身分與執行界線

本輪開始再次核對目前台服 EXE：
`aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48`。
453 筆 cbspec2 BIN 仍為：
`3adcda70a477086da50411fe5d023eec33f915efafd17ec478d55542cae42ea7`。

重型證據位於：
`C:/Users/risei/.codex/artifact-archives/god2-server/20261019/formula-state-followup/`。
靜態 helper 先 AST 後單次執行，REA 仍用既有公開 launcher 與本機 Ghidra。
v9/v10 分析 PE 的原始 sections 保留；新增分析 CALL 不當作原始 caller，映像不執行。
沒有建置、測試、native/VM、遊戲／網路、資料庫、部署或新專案 Python。

## 排程時間戳的實際讀取者

`timer-fields-static-v1.json` 將 `owner+A7FBCC0` 的目前 literal 使用點縮到三處：
`0051FBC5`、`0052AE3B` 寫入 timeGetTime；`00529493` 讀出舊時間戳。
這是 literal/CFG 支持的定位，不排除變形別名或整塊存取。

REA `00529020` 是兩 side × 14 slots 的播放更新。actor `+1EA` 是**內部播放狀態**：
狀態 `83h` 經 `005291BC` 呼叫 `00528660`，回傳非零才增加 `owner+A7FBC68` 完成數。
這個 `83h` 不是 wire opcode83，也不是 wire action0D。

迴圈後的完成條件為：

```text
(signed expected_count >= 0 AND signed completed_count >= signed expected_count)
OR unsigned32(now - previous_timestamp) > 10000
```

expected/complete 欄位分別為 `+A7FBC64/+A7FBC68`。成立時把完成欄位設為FFFFFFFF，
呼叫 `00529610` 並回傳完成。時間差是 DWORD subtraction，逾時比較為嚴格 `>10000`。
`00529610` 走訪 actor，核對 state9 與 renderer state，必要時調 `00526430`。
沒有由這些證據取得五回合倒數、DoT 週期或每次扣補量生成公式。

## `83/0D` 零子型別與延後消費

`0052C520` 入口的指標是 logical+1；先把 action減1，所以 switch case0C 是 wire
action0D。此分支再檢查 payload WORD+10（logical WORD+11），不能把兩個分支混用。

當 WORD+11==0：

1. manager `+30C/+30B` 決定 indexed bank 的順序／索引。
2. `0052A8D0` 設定 action0D 的播放前置狀態。
3. `0052C000 → 0052C0C0` 將 logical BYTE+13/+14 的結果與 selector 映射，
   保存 indexed actor `+27A/+27D`。
4. `0052CAAA` 將 logical WORD+9 原樣存入 actor `+280+2*manager[30B]`。

這個收到資料的 store 舊 REA 已證明；本輪新增的是它與 timer／播放 consumer 的連接。
WORD+11非零的 `+B60/+B64` 累加分支仍由既有 `RecoveredBattleDelta` 保留，沒有改動。

REA `00528660` 在 source playback substate1 讀 bank 的 `+27A/+27D/+280`。
所選 bank播放狀態0F、7A..7E或9，且既有 signed WORD 為負時，
`00528936` 將該值直接交 `00528A70` 更新 HP，再 `0052D9F0` 更新顯示。
非負量改走播放 substate4，不能由此宣稱本函數已立即補 HP。
mapped result87另選 MP 文字；相應資料仍是收到的 WORD，不是本地 MP 公式。
完成所選消費步驟後，`00528A4A` 把 bank `+27A[index]` 設為84哨兵。
這是已收到的一項效果播放／消費，不是倒數剩餘回合或自行重複傷害計算。
Ghidra 有移除 `005289CE` unreachable block 的警告；原組語另存，未宣稱全分支執行。

## C++ 原始位元組視圖

新增 `src/protocol/RecoveredBattleDeferredEffect.h`，只表達上述 zero-WORD+11 變體：

- 保留完整15-byte logical record；source為 wire位置，不能直接當成 consumer actor。
- 提供原始 WORD+9、選定 consumer 使用的 signed解讀、兩個 raw masks、logical3、opaque4。
- logical13 結果代碼以原13-byte `00571600` 表映射；未知代碼保留raw，映射回傳空值。
  這個查表不是 `0052C0C0` 經對方狀態保護後的最終 actor state。
- logical14只稱 raw effect selector，是 `00571610` index，不直接命名為 actor type。
- encode回傳原始 bytes；不借用普通攻擊的單體／對方／非空mask限制，不補造值。

沒有將 legacy WORD 轉成共用傷害／HP 上限，也不把收到量當成傷害或治療 producer。
runtime emission/mutation 均為false；尚無 formal producer、原子 bank順序、持續實例、
角色生命週期與端到端掛載。本輪只增加格式／消費來源視圖，完整玩法新增0。
獨立靜態複核確認 offsets、分支隔離與表 bytes，並補強 source綁定及raw selector註解。
未編譯或測試，不能宣稱成功回放或遊戲驗收。

## K 表相鄰子物件別名

新掃描發現 `owner+A9EA4B0` 被傳給七個 queue 函數；K count 在這個 base+40，
所以曾是整塊覆寫的候選。`k-subobject-cfg-v1.json` 以七入口248個不同指令的
有限 CFG affine 分析，只辨識到子物件 `+0/+4/+8/+C/+10` 的直接寫入。
該次沒有 budget或indirect-jump中止，但沒有替所有 callees／變形地址作證。

REA 進一步恢復 `0051D300/0051D3D0/0051D4E0`：

- D300 用 malloc配置buffer，存指標至+4、容量至+10，清+8/+C兩個索引。
- D3D0 從該buffer讀出到caller給定目的地，可選擇推進read index。
- D4E0 把來源複製到 `[this+4]+write_index`，必要時繞回buffer首端，推進write index。

所選 direct object writes 並未寫 base+40 的 K count。這縮小的是相鄰 queue alias，
不能說所有 memcpy目的地、heap aliases或K producer已排除；queue讀出caller目的地
仍須逐一綁定。非零 count/K填入與519E30自然 caller仍開放。

## 攻防、五行與角色指標轉送

`element-role-qualified-consumers-v1.json` 保存357處 `[owner+86888]` 指標載入與
限定直線別名；所見九個指定欄位使用點是既知4E6600的寫入。
`element-callee-field-leads-v1.json` 保留11個原始轉送目標及1049個raw位移候選。
後者沒有 RoleA身分，不能算1049個戰鬥consumer，也不是全域不存在證明。

本輪跟進的原始指標鏈為：

```text
4E63C5 → 4E63F0 → 4AC070 / 4AC2C0 → 4E6C90
```

REA確認4E63F0只是轉送。4AC070核對角色 current/max HP/MP、上限裁切及GUI百分比；
4AC2C0與4E6C90以 role WORD+58 更新GUI進度。這條鏈沒有讀取指定雙攻雙防及五行
欄位來生成damage／抗性／相剋量。其他別名、caller與存檔／戰寵物件仍未窮盡。

## 證據、剩餘工作與盤點

- 四函數 timer/effect REA：`ev_a152758bd1284528c0b1307da26fb61452ae363900844fd4b7bb43ff27213e8e`。
- 七函數 queue/role REA：`ev_b1225c77995088c181bad3814ff36400036f901fa7b4dd91fe56a74961376f06`。
- 完整偽碼、組語、PE provenance、helpers與欄位鏈JSON均外存；原EXE／453筆BIN未修改。

命中／暴擊門檻、傷害／治療生成、DoT實例與回合遞減、減傷及五行相剋／抗性仍缺。
下一步繼續追收到效果前的權威 producer、actor初始化／狀態欄位來源及其他實際
元素／攻防物件轉送。此次確定10秒是播放逾時，後續不再將它列為持續回合候選。
正式唯一靜態報告為 `round454-tw-deferred-effect-source`；source閉包新增本header，
全遊戲分母與完成率維持null，沒有增加已完成玩法或部署。
該報告沿用149c...既有封包格式索引，不是對aaf0...客戶端的全量重新盤點；
本輪各函數由獨立 current-SHA資料流及REA證據核對。
