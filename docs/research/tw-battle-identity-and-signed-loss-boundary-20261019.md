# 台服戰鬥身分來源與 signed loss 邊界（2026-10-19）

本輪為 PHASE1 原檔與原始碼靜態核對。沒有建置、測試、執行客戶端／VM／codec、遊戲 DB 操作或部署；不據此宣稱完整戰鬥、客戶端採納或完成百分比。

## 原檔與證據範圍

目前台服 God2.exe SHA256：

`aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48`

Round469 sealed identity v2 位於外部證據目錄：

`C:/Users/risei/.codex/artifact-archives/god2-server/20261019/battle-identity-owner-round469/identity/battle-identity-owner-conclusion-v2.json`

SHA256：`b137c5ee40a00c8847947e989f87347ec0931dad535a654c285d7a8f969cffc3`。共核對九個函數的 4,282 筆目前原檔指令及 13 筆 WORLD82 原檔指令。新 REA evidence：`ev_7cd5cdd00169d66ece245b696f704c077e2fa6059038e9b9129306b5b7946176`，三個父函數成功取得，分析 handle 已關閉。

Ghidra 未還原 46563D 的 jump table，provider 成功不等於完整偽碼；另以目前原檔八格表及 CFG 關閉 Main4655E0 的 298 筆指令。468160 仍有 468763 間接分支開放，位於本輪核對的 R0 寫入之後；本輪沒有把該函數或整個登入流程標為完成。分析 PE 的原始十三節區相同，額外 analyst caller 不屬於原版 caller，也未執行目標。

## B+48 的實際來源

以下 W 是實際 Main／World 的 this，R=W+1539683C，T 是 Main4655E0 的區域 context，D 是傳給 initializer 的 descriptor，B=DWORD[W+A7E05EC] 是實際 battle object。這些是 this-relative 物件；相同 W 與 entry epoch 必須由實際 owner 鏈維持。

| 原檔鏈 | 已核對的行為 |
| --- | --- |
| World setup464910 → 465176/465183 → 465194/468160 | 傳入同一 W 的 R；opaque NET+2CB8 為零時傳 NULL name，否則轉交實際 caller 的 name pointer。非零 flag 不保證 name 非空，也未證其為 authentication flag。 |
| Named468160 → 415690 | 46817B 的非空 name 路徑搜尋 opcode2A，從 logical+1 複製 36 位元組 body。這個 36 是長度，不能與 Timer36 或同號封包混同。 |
| 4685EB → 468629/468633 | body 第一個 DWORD 的 bits23..25 正規化不影響 low14；AND3FFF 後寫入 R0。因此在這筆合格寫入時，R0=LE32(實際2A body0)&3FFF。NULL name 的 4688E4 會寫 R0=0，不能當成已登入 owner 身分。 |
| Main4655E0 → 467860 → 466B00 → 468AE0 | 同一 T 傳入 WORLD；82 事件回傳 state4，沿同一父鏈回到 Main 的 state4 分支。 |
| 4657CA/4657D6 → 465836/5112C0 | Main 從目前同一 W 的 R0 讀完整 DWORD，寫入 T0；其後只有向 T30/T40 的兩段字串複製，至 initializer 前沒有外部呼叫。 |
| 5113BC → 5113F8/511401/511415/51141A | initializer 取 D4=T，將 T 的 FB 個 DWORD（1004 位元組）複製到 B+48。因此 B+48=T0=4657CA 當時的完整 R0。 |

B+48 不是82 context_a、DB character id、account id 或其 lowWORD。Named2A 證明的是指定寫入時的來源；Main 擷取的是當時 R0，不能假設任何舊2A都仍有效。

## 82 context 與 selfslot 是不同欄位

WORLD82 的 46AE19/46AE22 將 logical DWORD1 存入 T+28，46AE25/46AE2A 將 logical DWORD5 存入 T+2C；initializer 的 511409/51140F 分別讀取它們，於 51140C/511412 寫入 B+3C/B+40。它們不提供 B+48 身分。

S2C1C 是 45 位元組的 identity record，並非81。515C90 的 EBX 指向 logical record；在已核對的 type/resource 分支，side0 且 zero-extended logical WORD3 等於完整 DWORD B+48，才可於 516382 寫 B+51=logical BYTE1%14。不能把完整比較改成 DB id 的 lowWORD 比較。

B+51 另有已核對的 writer：initializer51143A 寫 FF；86/5 的 logical BYTE3 bit0 為一時，5175D9 寫 logical BYTE4&0F。86/5 primary grant 不是 turn permission，也不是客戶端採納證明。1C 後續寫入、再次 grant、初始化、重入、rebind、reconnect、exit 或未知 context replacement，都必須使舊 selfslot 候選失效或重新核對；viewer-relative 座標也必須在投影後另行核對。

## 既有伺服端 owner 邊界

原版 named2A 的 low14 範圍是 0..3FFF。既有 QualifiedSceneHandle 使用 lease.actor_handle 的 1..FFF，是另行限制的十二位元伺服端 profile，不能宣稱原版所有 identity 都只有十二位元。DB account／character、Session 與 generation 的完整64位元 owner 必須保留，不能以 native WORD 取代，也不能擴大或截斷既有 profile。

對應 native identity 的可能來源是實際 private current NormalWorldInitialization／local entry Written、原本2A body 及相符 readyLease.actor_handle 的同一 owner graph。必須同時維持同一實際 World W/R/B 與 entry epoch、無介入的 R0 重設或替換、實際 battle admission generation 以及原始 Written bytes 的 custody。相鄰函數位址不證明它們執行時持有同一 World。

既有 private Current 在進入 InBattle epoch 後依設計失效；需要從真正的進入前 graph 擷取，再明確綁定一次 transition 與完整 battle bootstrap write。不能默默 rebase 舊 Current。local Written 只證本機完成寫入，不是遠端 ACK、native adoption、selfslot 或出手權。實際 Application／Main normal-world 與 battle admission owner 的接線、所有介入的 R0 mutator、完整2A間接分支與 runtime 採納仍開放；新建未接線 receipt/model 不能解除這些邊界。

OwnedTaiwanPkInitialContextSource 的 CUSTOM-0111 保持現有契約：context_a=經檢查的 Session battle_generation+1，context_b=00001400；counter/window/display/empty slots 是既有明示初始政策。本輪只補證據註解，不改任何 context 值、player/vital Current fence 或 owner 契約。它的82 producer 不能充當 B+48 或 native selfslot 來源。

## 更正 round468 的 diagnostic88-only 推論

本輪來源 audit：`C:/Users/risei/.codex/artifact-archives/god2-server/20261019/battle-identity-owner-round469/scope/battle-identity-and-custom-groups-source-audit-v1.json`，SHA256：`187c6d6cf4c4329dbcd8ac6f7931d42f1a7e896e274a81eaec62e7c637d4c0b3`。

Application1202 只有 diagnostic_battle_participants 開啟時才建立 diagnostic_combat；NativeDeltaLab3702 在它不存在時回傳 null。因此 participants=false 的 default vitals88-only fallback7304 不會抵達 Lab／bind owner。Round468 把這個 fallback 當作實際 Lab 缺少 grant 的可達路徑，該推論撤回；成功 Lab 使用完整 participants bootstrap 與 primary86/5 slot0。

這項更正不建立一般 native self-view authority。Plain diagnostic 的 source0 S1C identity WORD 是0，不能僅靠 Battle controller 的完整 Session character 將它當作正常玩家身分。既有 PK private normal-entry／lease／appearance 鏈與 Legacy diagnostic Lab 是不同 owner；PK 已有的 initial82/88 producer 也不能被概括成88-only。所有無 grant 或失效 self-owner 的保守邊界維持原樣。

## Signed loss endpoint

標準結果原本以 hp_loss>7FFF 拒絕，漏掉 signed WORD 可表示的負端點−32768。
本輪只把標準 BASIC、既有一般技能 helper 與 PK scalar projection 的扣血上限改為
8000；這是傳輸表示範圍，不是權威傷害上限或傷害公式。核心完整64位元數值域保持，
超過此特定封包範圍仍拒絕，不截斷，也未建立較大數值的替代表示。

`skill-group/native-signed-word-boundary-v1.json` 的 SHA256：
`8826726e1a249ac8c2f9f8244c7a59f3474497378f52b53197a9ef880d73f72d`。
共重核目前原檔四函數、2,618 條指令。BASIC 接收後寫 source286，52364A 的 MOVSX
將 WORD8000 擴展成 signed DWORD−32768，523655 呼叫528A70更新目標HP。
一般524820技能由 source28A 取得量，524D72/524D79 走相同 signed DWORD HP updater；
既有 hit、目標與已死亡狀態等 gate 仍須滿足。

BASIC52B48E 將 DI 以 MOVSX 擴展後 PUSH EAX，格式字串59D968是 `HP %+d`；
一般技能亦以32位元參數交給 `HP %+d`／`%+d`，沒有16位元 ABS／NEG。
歷史原版 formatter 曾產生 `-32768`，本輪核對其整段 CRT547000..56F000
（163,840位元組，SHA256 `3f9578ab27158a9132d1b735a4fa61640c899ad1b2cdc817b49f47cd003383dc`）
及 caller／526120／literal 與現用 EXE 完全相同，僅重用該已保存證據，沒有重跑VM。
這閉合數值邊界，不代表本輪完成完整封包到畫面驗收。

C++在 loss<=32768 檢查後才轉 int32_t 並取負，再轉 uint16_t，32768精確編成
little-endian `00 80`；32767為 `01 80`。正向治療的 signed WORD 最大值仍為32767，
不能把它誤改成對稱的正負32768範圍。RecoveredPkActionProjection 既有
hp_loss<=damage、actor topology、相對視角與HP回覆政策保持。

CUSTOM126瞬影三煞斬／CUSTOM150牛轉仙界踏的 bridge 扣血上限仍為32767。
DiagnosticShunyingManual 的 skill 路徑先明確檢查7FFF，才呼叫共用 helper並改成126；
其 BASIC 路徑可用原生8000端點。兩個正式自製技能 encoder 沒有改動。

新增／修正的回歸原始碼包括雙方向、兩個PK視角、存活／死亡 outcome、一般與特殊
renderer的HP86政策、full DWORD HP fixture、32767／32768精確bytes、32769及高位截斷
拒絕，以及真正 Battle::act 在encoder失敗後保留HP／MP／revision／完整checkpoint與RNG，
重試32768等於同seed新Battle。案例依PHASE1沒有執行，不能標為測試通過。

## 技能主要結果、治療與批次的界線

`skill-group/skill-group-native-conclusion-v3.json`（SHA256
`e752f29195358a34e6cb09b806f6132e4e6054914b519d75872ceebbc213b8b6`）
重核14函數、4,486條目前原檔指令。主要target／type陣列可證14格；28A的56-byte
clear span本身只證28個WORD，不能單獨推成14格。receiver未見n<14 guard，故不能據此
放寬發送者；現有瞬影至多3目標、牛踏至多14目標維持。

03／17雖共用部分上游，03有額外kind2 self override，17另有兩個文字／render consumer；
17不能當作03 codec別名。R13 raw0映射0F，R14 raw0／27／28／34／35／36分別映射
9／59／0／77／78／79，raw0不是所有欄位通用的狀態0。

一般524820的正量可在合格hit gate更新HP；特殊526890須type77才加該量。
type78／79不是已證MP治療，59復活則仍需既有HP86。這些均為收到結果的消費行為，
未反推出原始治療量、技能傷害、攻防減傷、五行抗性、命中／閃避／暴擊或持續tick公式。
自製技能group0／88 barrier的現有source稽核也沒有證實需任意改group編號；watchdog、
replay與bridge清理仍是後續owner邊界。

唯一正式靜態盤點及獨立review、source／storage／publication收據存於同輪外部目錄。
玩法完成數不增加，全遊戲分母與百分比仍unknown/null；goal維持active。
