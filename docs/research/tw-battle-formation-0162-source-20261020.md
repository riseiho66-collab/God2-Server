# 台服布陣、多人 PvE 投影與保留的未知規則

> 2026-10-21 pass5 更新：本文保留 pass4 歷史結論。action9、返回接續及83／88
> 時序已有後續修正，現況以 [換排與回合源碼](tw-pve-row-swap-cycle-source-20261021.md)、
> [原版佇列 REA](tw-native-row-swap-and-cycle-20261021.md) 與
> [返回接續](tw-pve-return-continuation-source-20261021.md) 為準；
> pass4 直接 consumer 推得的「83 後不能接88」不適用實際延後播放佇列。


本輪只有 PHASE1 來源／靜態分析。未建置、執行測試、遊戲、VM、codec、
SQL 或部署；回歸來源不代表驗收通過。正式封包盤點由主代理獨佔執行。

## 原生證據

原件 SHA256 為 `aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48`。
REA 使用分析專用 PE，13 個原始 section 逐位元組相同；額外 CALL seeds
不是原始 caller，分析 PE 從未執行。每個工作階段皆有 close 收據。
完整資料在外部 `20261020/sos-room-formation-capacity-pass4/formation/`。

- `515C90` 將 S1C logical BYTE1 除以14／餘14。side0、normal-player type2000、
  WORD3 等於完整自身身分時，寫 B+51 為收到的 local slot；type4000、WORD3
  有4000且低14位等於自身身分時，寫 B+52 為收到的 secondary slot。
  它接受伺服端已分配的位置，沒有由 CE 算出位置。
- `51FC40` 配置2×14×6層；`51E6E0` 實際檢查 side<2、local slot<14、layer<6。
  `51BB80` 的指定角色來源只讀 CF 選擇及 D4 數量；這個限定函數沒有 CE
  reader，不等於對整個 EXE 作「沒有任何別名」的宣告。
- `51F410` constructor 由 `571AA8..571B88` 複製28組 DWORD x/y 至
  B+A7FBCCC；內迴圈14筆。座標呈5、4、3、2斜列，**不能推出7+7**。
  `OwnedBattleFormation::native_coordinates` 保留這份原始表。
- `525B90` 延後等待動畫；actor+286 非零才交換 S83 提供的兩個 flat position
  對應之全部6層 pointer、packed side/slot、位置／presence bits；以原 actor
  pointer 更新 primary／secondary local slot。沒有產生「另一格=原格+7」
  或本服玩家／戰寵配對規則。失敗不能說已換排。
- B4→E8→角色 CE 的限定 UI 路徑沿用 CUSTOM-0142 證據。原服初場 pair/lane
  分配、CE 到伺服端 actor slot 的公式沒有原始 sender；仍然未知。

新 REA capsule 為 `formation-deployment-decompile-v1/v2/v3/v4/v5.json`。
v1 檔案的歷史檔名是 `formation-flee-decompile-v2.json`，其中只有525B90
成功；v3 的51D350尚未建立函數，以另一份明確 seed 的 v4 完整取得。
v5 取得真正座標 constructor51F410。失敗、候選 raw scan 和後續修正均保留，
沒有以失敗查詢當成原生不存在。

## CUSTOM-0162 與實際接線邊界

`OwnedBattleFormation` 是純值型 policy adapter。完整版本化 DB 設定須明列
每個 lane 的 row0／row1 local slot；空白、重疊、越界或未知 row 直接拒絕。
沒有預設 pairs、免費 pet 或由選擇 byte 建立的 actor。`Owner` 保留 session、
account、完整 character、actual native WORLD handle；沒有把 DB character
截斷成 native ID。即使 pet 不存在，也保留該 owner 的 pair reservation。

room authority 須在任何建立／加入 mutation 前取得真實保存 B4 row、完整
pair 設定與原生／儲存來源，將得到的 primary／pet positions 交給同一份
`OwnedPveRoomTypes::MemberInput`。之後 Battle、C35 actor／target／grant、
每個接收者的 S1C／86／88、保存及返回都引用實際 member slots；本 adapter
不授予 Session、技能、戰寵或 command 權限。既有 PK 的0／14 invariant不改。

`Snapshot::swapped_pair` 只準備不可變換位值。實際 action9 room mutation、
repository slot-permutation CAS、原生延遲完成 owner 與再授權**仍然 OPEN**。
不能只改 bootstrap、準備值或整包 Written 就宣稱這條玩法完成。

## 多人投影

`RecoveredPveRoomProjection::prepare` 純粹讀取實際 room after-snapshot；每個
receiver 另有完整 identity、appearance、HP／MP、counter、grant、action、
terminal profile。缺少必要來源會丟 `ProfileRequired`，不填 opaque 零值。

- 新 entrant：自己的82 context，所有86/4先於1C；每個 actor 採當前 HP／MP
  與 dead bit0；然後完整友方88與 actual primary／secondary nibble grant。
- 晚加入的舊成員：只收到新 actor delta；不重82、不重設舊 actor、counter、
  grants 或 RNG。新成員得到目前完整 roster，已死亡怪物不變回初始 HP。
- support-enabled 房間的新 entrant 另需 matching native08 profile，因原生
  5112C0 清 B+488；不能只在伺服端設 true 而讓新客戶端保持 false。
- Action 由真正 `BattleActionResult` 逐 hit 套用既有 typed83 codec；只有
  已證 pose-only consumer 才另送 absolute HP，避免正常動畫重扣血。
- 86/5 未設的 bit **不清**舊 A/B 或 slot。server grant epoch 與真正 C35
  cleanup／動畫完成分開；mask0、準備或 Written 均不冒充 native ACK。
- Support 保留 actual caller primary／secondary position；withdrawal 要完整
  83/action6／成功 flag2 來源，逐一涵蓋離開的 primary 和 actual pet。
- Retired／Returned／disconnected 不再當收件人；最後一人斷線可回空 output
  集合讓保存／退休繼續，但不排出虛構空 native 訊息。
- 每條 output 只含完整 native records，限制在現有 frame logical 上限。

## Terminal 與返回

新 current-aaf capsule `formation-terminal-decompile-v6.json` 重核518BF0、
518E50、515770。89 尾設 B+A9DF6BC=1；515770 的0B producer只在該值為0
及 expected/completed/cycle 條件滿足時呼叫518E50。0B也屬普通回合完成，
builder繞過 A/B grant gate，不能當成 terminal credential，也不能一概要求
89之後必須再有一筆0B。返回以 host 真正收到的 C1C 和 retained INIT barrier
為準，這個純投影不製造該證明。

既有 `OwnedTaiwanPkReturnSceneSource` 與 `TaiwanCustomFullActorProfile` 提供
fresh saved pose/resource/status、receiver selector、當前 actor population 的
6F／EA recipe。原生515770→465931／465BC0→state3→467860是 retained-world
resume，不是 fresh2A。不可用 CF／2A／S30 全場重播取代返回；CF可清完整
inventory，S30會 append。PvE須有自己的逐人 owner，不能挪用 paired PK ticket。

## 真正 FLEE 輸入

`RecoveredBattleFleeCommand` 為 current-aaf518E50 明列的 action6 分支：清14byte
target scratch，取5156E0當前主／副 slot，強制 count1，形成唯一 self masks。
保留17 bytes：actor<=14、action6、sideflag0／1、原始 logical4、兩個 self
masks、context=B+3C、原始 tail DWORD13..16。action6未初始化 logical4及末端
DWORD，不能將它們當零、成功結果、HP、逃跑率或費用。parser保留全部bits。

WorldRecords在任何 action2／skill fallback 前獨立解析 action6；invalid actor、
side、masks、截短或錯誤後綴皆拒整批。格式允許原生producer的actor14，不授權
room使用不存在的side0 slot14；host仍須核對真正 primary／pet、grant、context
及同一 room incarnation。CUSTOM-0161 voluntary withdrawal不是原服逃跑成功率
公式。成功的資源保存、完整83/action6 profile與逐人C1C返回仍需各自的owner。

## 回歸來源

`tests/test_owned_battle_formation.cpp` 的 explicit CUSTOM fixture 檢查未知設定
拒絕、pair reservation、不可變換位／離開、晚加入 delta、當前死亡／怪物HP、
先 renderer 後 identity、非零 primary／pet grant nibble、opaque保留、缺少
profile拒絕、secondary support，以及最後無收件人退休。它沒有執行，也沒有
假造 private Session receipt。FLEE來源另覆蓋actor0／13／14、primary／secondary、
末端高bit／FFFFFFFF、完整world typed分類及錯誤整批拒絕。真實原版客戶端／room／
保存／返回聯驗仍待後續階段。

補充靜態追查：v9 capsule formation-flee-ui-decompile-v9.json 成功5／5並
close。512760／512790／512990 從 B+46C 讀取動作，透過5156E0帶入當前
actor，再呼叫518E50；這是動態共用 caller，尚未把特定原生按鈕直接常數6
的選擇路徑當成已證。518E50的sideflag是 A==0且B!=0，與actor除14無關；
兩個權限皆在時5156E0優先primary，消耗後才輪到secondary。

原生518E50共用 cleanup對action8同樣優先清A，否則清B。CUSTOM-0161因此
消耗真實操作者的一次grant；Support83/8後補送各收件人剩餘grant，避免下一
個人物／戰寵操作權卡住。沒有用未設bit清除舊native權限。Entry enabled08
也要求該source是當前alive ownedactor，避免08將deadpet誤改為存活pose。

歷史快讀（已由20261021完整queue REA修正，見 `tw-pve-row-swap-cycle-source-20261021.md`）：現用aaf0的518A90→52D360將88當前值直接寫side0 actor+DE8／DEC，
並經516AC0清播放資料。普通83延後hit也改同一HP欄；AI→友方若緊接送
action後HP88會重扣／清播放。Action／Terminal及普通Grant均不再送88，另有reported-cycle條件Grant；新
entrant的初始roster後有88；晚入舊成員沒有重播。既有完整REA證據沿用
20261019/status-lifecycle-round459/vitals/rea-static-formulas-batch-v1.json，
ev_686bc320b04008e9046dc4397c8ca469f7363b0384a939dfa7f546efe4a66381及close。
回歸來源增加AI→友方deferred83、無eagerHP86／88與普通Grant只發86/5。

真正C35／0B只可視為未受信client cycle progress，須由host另合併server所持
所有grant已消耗及整房outbox全部Written條件；它不是native動畫ACK，也沒有
授權改傷害／RNG／owner。舊協定沒有turn nonce，原生counter更新與完整回合
時序仍須追查並實機驗收，不能以取消88或收到0B宣稱已閉合。

後續CUSTOM閉環：Change新增server-only cycle_progress_observed。普通Grant仍
只86/5；唯host實際await階段收齊required peers的原始0B、server-owned所有
grant已消耗、整房outbox全部Written後，才以true產生下一round的88＋86/5。
完整bulk/counter來源仍必需，不接受client提供counter或true布林。其他Change
若帶true直接拒。Ordinary Action／Terminal／Support／Pass絕不依此重送88。
這是明列CUSTOM進度policy；不能驗證誠實動畫完成，無turnnonce的重放／提早
通過限制仍記錄，原服counter公式／完整native時序仍非完成。
