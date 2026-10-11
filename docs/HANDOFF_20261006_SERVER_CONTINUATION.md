# Superseding owner directive and source state (2026-10-06)

Continued round `20261006-owned-player-vitals-source-pushes`: existing
RecoveredPlayerSnapshot/Application first-WORLD-tick restoration conditionally
sends saved S2C22 role and S2C24 HP/MP records. S2C22 already has a distinct
registered C2S21 reply branch; v12 adds the push classification without
increasing reply count. C2S candidates 151; WORLD parser 63/reviewed scoped
branches 42 (limited 66.7%), gaps 11/pending groups 10; S2C lengths
252/nondefault 206, registered replies 43, source pushes 8 (+2),
unclassified 124 (-1). Whole-game percentage unknown. No new runtime code,
tests, builds, client run or deployment. See
`docs/research/current-saved-role-journal-s2c-pushes-20261006.md`.

Continued round `20261006-owned-role-journal-source-pushes`: registered
existing conditional first-WORLD-tick S2C2C saved role auxiliary and S2CDB
subtype4 fifteen-slot saved journal pushes in frontier v11. These source
paths already existed; no C2S reply or new runtime behavior was added.
C2S candidates 151; WORLD parser 63/reviewed scoped branches 42 (limited
66.7%), gaps 11/pending groups 10. S2C supported lengths 252/nondefault
206, registered replies 43, source pushes 6 (+2), unclassified 125 (-2).
Whole-game percentage unknown. No build, tests, client execution or
deployment. See `docs/research/current-saved-role-journal-s2c-pushes-20261006.md`.

Continued round `20261006-owned-map68-custom-source`: CUSTOM-0087 now has a
source-scoped C2S68 00 -> native S2C3F 01 00 regional-map display branch,
admitted only from completed WORLD, actual saved current scene, and a matching
owned source-qualified item5569/5576 in the projected bag. It mutates no
inventory or saved state. Original 68->3F causality is still unproven;
same-number S2C68 remains independent. C2S candidates 151; WORLD parser
63/reviewed scoped branches 42 (+1, limited 66.7%), groups 18, gameplay
gaps 11 (-1)/pending groups 10. S2C lengths 252/nondefault 206,
registered replies 43 and unclassified 127 unchanged. Whole-game percentage
unknown. No build, tests, current-client acceptance or deployment. See
`docs/research/current-owned-map68-route-20261006.md` and
`round-reports/20261006-owned-map68-final-source.json`.

Continued round `20261006-existing-pet-clock-appearance-joins`: existing
Application/SQLite source handles scoped C2S28 owned-pet reserve/active
selection and returns 3B/41 plus E3 fixed53 or FB fixed73, while configured
world clock pushes 1A and configured appearance/visibility pushes DA. Ledger
and S2C frontier v10 now register these exact branches; no new runtime route,
deployment or native acceptance occurred. C2S candidates 151; WORLD parser
63/reviewed scoped branches 41 (limited 65.1%), groups 18 (+1), gaps 12 and
pending groups 10. S2C supported lengths 252/nondefault 206, registered
reply opcodes 43 (+2), source pushes 4 (+1), configured visibility pushes
4 (+1), independent formats 9, unclassified 127 (-4). Whole-game completion
unknown. No build, tests or client run. See
`docs/research/current-existing-s2c-source-joins-20261006.md`.

Continued round `20261006-s2c4d-beast-delta-classification`: classified the
existing native S2C4D logical9 beast-panel/inventory delta as an independent
known receive format. Its target inventory slot is the selected beast's physical
cell if ever used for that beast, not the C2S6B dragged food slot. The issuer
and request/reply causality remain unknown, so no 4D emission or complete route
was added. C2S candidates 151; WORLD parser 63/reviewed scoped branches 41
(limited 65.1%), gaps 12/pending groups 10; S2C supported lengths 252,
nondefault 206, independent format-only 9 (+1), unclassified 131 (-1).
Whole-game completion unknown. No build, tests, client run, activation or
deployment. Evidence `beast-panel-static-contract.json` and
`s2c-world-consumer-frontier-v9.json`.

Continued round `20261006-6b-food-pfd-readset`: source-pinned PFD catalog has
65 exact declarations, including special transformation rows, and a bounded
native prequeue trace establishes only the local lane0 UI gate. New
`OwnedBeastFoodReadset` captures full owned bag plus selected beast in one
SQLite read transaction and joins the lane0 selector, custody revision and PFD
key as a candidate. It is not wired to Application and does not authorize food,
consume items, mutate a beast or send a reply. Need exact ordinary-food rule,
effect/cap/Lua, transaction CAS and native causal S2C response. New complete
routes 0; C2S candidates 151, WORLD parser 63/reviewed scoped branches 41
(limited 65.1%), gaps 12/pending groups 10; S2C supported lengths 252,
nondefault 206, independent format-only 8, unclassified 132. All deltas 0;
whole-game completion unknown. No build, tests, client run, activation or
deployment. See `docs/research/current-companion-control6b-20261006.md`.

Continued round `20261006-6b-panel-slot-crosslink`: exact pinned native slices
tie C2S6B lane0 to the live beast-panel UI+85ABD selector, written by S2C4B/4C
and compared against S2C41's physical inventory slot only for panel close.
CUSTOM-0085 persists selector and custody slot separately; do not infer an
equality invariant or consume a beast by physical slot from this comparison.
Food owner/selection readset, eligibility, effect, persistence and native causal
reply remain open; new complete routes 0. C2S candidates 151; WORLD parser 63,
reviewed scoped branches 41 (65.1% of parser only), gaps 12/pending groups 10;
S2C supported lengths 252/nondefault 206/independent format-only 8/unclassified
132. All count deltas 0, whole-game completion percentage unknown. No build,
tests, client run, activation or deployment. Evidence:
`artifacts/integration/packet-connections-20261006/companion6b-panel-slot-link-v1.json`.

Continued round `20261006-npcboss-message-source-join`: pinned the native resource section NPCBossMessage (72 source rows, IDs 1..72) from the exact current-client message.csvZ and joined it through the native loader to the S2C 5A and NPC-mode 79 label selector. The ordinary S2C72 constructor stores a zero-extended low-WORD pool identity, which the label consumer looks up as a full DWORD. The codec now names NPCBossMessage and NPCNormalMessage selectors separately. Specific message choice, owner state and timing remain unproved; new complete routes: 0. C2S candidates 151; WORLD parser 63/scoped source branches 41 (limited 65.1%), gameplay gaps 12/pending groups 10; S2C supported lengths 252/nondefault 206/independent format-only 8/unclassified 132, all count deltas 0. Whole-game percentage unknown. No build, tests, client run, activation or deployment. See `docs/research/current-s2c-text-npc-595a5b79-20261006.md`.

Continued round `20261006-s2c-text-npc-595a5b79`: pinned four current-native fixed 9-byte WORLD S2C consumers. Opcodes 59/5B select text resource presentation; 5A updates an existing NPC pool label; 79 chooses text or NPC label by WORD logical+5 == FFFF. A read-only raw codec and bounded instruction evidence were added. No original server producer or causal C2S path is proved, so new complete routes: 0. C2S candidates 151; WORLD parser 63/scoped source branches 41 (limited 65.1%), gameplay gaps 12/pending groups 10; S2C supported lengths 252/nondefault 206/independent format-only 8 (+4)/unclassified 132 (-4). Whole-game percentage unknown. No build, tests, client run, activation or deployment. See `docs/research/current-s2c-text-npc-595a5b79-20261006.md`.

Continued round `20261006-fd12-item-key-slots`: FD12 bytes 4..21 are nine u16 item-definition keys. Native 956B0 indexes UI+26108 and calls 459A60; 957F0 selects 9/6/3 item slots under local flags. RecoveredFDE4Panel only exposes a read-only indexed key. Original server offer authority, exact length and E4 request/reply causality remain open. New complete routes: 0. C2S candidates 151; WORLD parser 63/source branches 41 (scoped 65.1%), gameplay gaps 12/pending groups 10; S2C supported lengths 252/nondefault 206/pending format-only 13/unclassified 136. Whole-game percentage unknown. No build, tests, client execution, activation or deployment. See `docs/research/current-fd12-e4-panel-20261006.md`.

續輪 `20261006-fd12-e4-ui-offer`：S2C FD subtype12 經
`69245→858B0→85BBE`更新E4 UI可用性；FB／FC也呼叫
`858B0`，但不進入FD專屬subtype switch。原生最少消費
logical26，18-byte前綴與mode／option mask／兩個button
旗標已有唯讀codec，未知尾部保留。此為上游介面資料，
尚非可授權的正式服務端offer或C2S E4因果回覆。
新增完整路徑0；C2S候選151、world parser63／限定來源41
（局部65.1%）、gap12／pending10，S2C長度252／非預設206／
待接格式13（+1）／未分類136；全遊戲百分比未知。未build、
測試、client執行、啟用或部署。見
`docs/research/current-fd12-e4-panel-20261006.md`。

續輪 `20261006-e4-producer-ui-gates`：C2S E4
operation0先經`+26128==1`及本地清旗標；1/2各需
`+26124`／`+26126==1`且`+26127==0`；3屬另一複合
UI流程，掃`+26129..+26130`八個旗標任一非零送包。
四筆都無pet slot／instance／revision，外層`+232E0E`
是UI控制ID，不能當目標。C2S0..3與S2C E4 bonus0..3
數值相同但因果未證；Application仍不啟用。完整路徑新增0；
C2S候選151、world parser63／限定來源41（局部65.1%）、
gap12／pending10，S2C長度252／非預設206／未分類136
不變；全遊戲率未知。未build、測試、client執行或部署。
見 `docs/research/current-e4-c2s-producer-gates-20261006.md`。

續輪 `20261006-e4-pet1-cache-link`：原生E3 snapshot與
S2C E4 delta對槽位42..44使用相同52-byte快取列：
`9E50+52*slot=A6D8+52*(slot-42)`。E4已釘定最大
HP／MP、雙攻雙防低12位、剩餘點數及四維加點計數
0..3的更新，另兩bytes保留opaque。`RecoveredE4Control`
已有唯讀typed view；C2S E4 operation0..3雖同範圍，
請求→回覆因果及原始加點規則未證，Application仍不啟用。
完整路徑新增0；C2S候選151、world parser63／限定
來源41（局部65.1%）、gap12／pending10，S2C長度252／
非預設206／未分類136不變；全遊戲率未知。未build、測試、
client執行、啟用或部署。見
`docs/research/current-e4-pet1-cache-link-20261006.md`。

續輪 `20261006-npc-instance-removal-link`：`S2C72`普通與
組合 constructor 均先取selector低WORD查找NPC pool，再
遮罩存入record+0；`S2C75`取相同低WORD，以`CC990`從
相同pool移除。釘定原生8段指令／bytes已保存，
`RecoveredNpcRecord::instanceIdentity()`及世界顯示儲存列
採用此語意，數值與schema不變；上一輪文檔已明列修正。
NPC動態消失權威、時機和75未讀兩bytes仍缺，runtime發送
保持關閉。完整路徑新增0；C2S候選151、world parser63／
限定來源41（局部65.1%）、gap12／pending10，S2C長度252／
非預設206／未分類136均不變；全遊戲率未知。未build、測試、
client執行、啟用或部署。見
`docs/research/current-npc-instance-removal-link-20261006.md`。

續輪 `20261006-world-pool-removal-source-push`：`S2C74／75`
原生logical5各取低WORD instance，分別以`CC990`移除
`W+153B8758`怪物／跟隨寵物池與`W+1539AED8`NPC／本地標記池。
保留未知兩bytes的純codec已加入，無可授權動態移除來源，
沒有runtime發送。既有`71／72／78`場景顯示來源推送與
配置限制的`5E／6F／73`玩家可見性推送分別登錄，並非新接
完整路徑。S2C長度252／非預設206／來源推送3／配置限制
推送3／獨立格式4（+2）／未分類136（-8）；world parser63／
限定來源41（局部65.1%）／gap12／pending10，C2S候選151
不變。全遊戲百分比未知；未build、測試、client執行、啟用或
部署。見 `docs/research/current-world-pool-removal-and-source-push-20261006.md`。

續輪 `20261006-s2c-first-hop-gm-bridge`：釘定原生WORLD S2C
未分類152個入口的第一跳；145個在有界片段有直接call，7個
沒有。`7B–81`及`F6`八個opcode共用外部`GM Tools FS2`
視窗訊息形狀的橋接，分別保留原生長度及payload長度；
伺服器producer、payload欄位和外部工具效果未證，沒有遊戲內
完整路徑。S2C長度252／非預設206／外部橋接8（+8）／
未分類144（-8）；world parser63／限定來源41（局部65.1%）／
gap12／pending10，C2S候選151不變。全遊戲完成率未知；
未build、測試、client執行、啟用或部署。見
`docs/research/current-s2c-first-hop-and-gm-bridge-20261006.md`。

續輪 `20261006-c2-mode1-five-widget-gate`：原生C2 mode1
需五個UI槽位索引均非負、bit0x10全開才送包；否則走
本地錯誤。此分支不讀F5，與F5-fed modes2..6分開。
未寫入body bytes不作零值假定。新增完整路徑0；world
parser63／限定來源41（局部65.1%）／gap12／pending10、
C2S候選151、S2C長度252／獨立格式2／未分類152不變，
全遊戲率未知。未build、測試、client執行、啟用或部署。
見 `docs/research/current-c2-mode1-five-widget-gate-20261006.md`。

續輪 `20261006-c2-controls-receiver-split`：C2S C2
logical9 modes1..6已由原生三個queue點與UI switch釘定，
mode1和F5-fed modes2..6分開記；多處未賦值bytes保留。
`RecoveredC2Control`與預設關閉WORLD parser已加入，無
Application handler。S2C同號C2固定3的consumer刷新另一
UI路徑，不建立虛構回覆。新增完整路徑0；world parser63
（+1）、限定來源41，局部比率65.1%因分母增加而下降、
gap12（+1）、pending10（+1）；C2S候選151、S2C長度252
不變，獨立S2C格式2（+1）、未分類152（-1）。全遊戲率
未知；未build、測試、client執行、啟用或部署。見
`docs/research/current-c2-control-bidirectional-20261006.md`。

續輪 `20261006-orange-shop-bf-money-quantity`：原生assert
指明EE/F3兩列族的列+2是`money`；UI選取量由顯示餘額
除以該值、最多30。BF OrangeShop候選格式已在
`RecoveredBFRequest`加入純形狀解析：key:u16、quantity:u8、
category:u8、zero-extended displayed money。每日dialog32可
與之重疊，因此不得只憑payload准入；Application沒有擴大。
正式來源未找到OrangeShop權威catalog或專用貨幣，不能沿用
一般交易wallet作為其證據。新增完整路徑0；world parser62、
限定來源41（局部66.1%）、gap11、pending9、C2S候選151、
S2C長度252／待接格式12／未分類153均不變，全遊戲完成率
未知。未build、測試、client執行、啟用或部署。見
`docs/research/current-orange-shop-bf-money-quantity-20261006.md`。

續輪 `20261006-orange-shop-f5-ef-state`：同版原生assert
原始字串命名OrangeShop商品資料，確認S2C EE的介面身分。
F5固定29變體7/8更新UI鄰近記錄並可能清空EE列；EF固定3
更新BF偶數模式的u16門檻，FFFF為隱藏分支。純codec已加入，
但BF交易、經濟權威及因果回覆未證。新增完整路徑0；
world parser62／限定來源41（局部66.1%）／gap11／pending9、
C2S候選151／S2C長度252不變；S2C非預設待接格式12（+2），
未分類153（-2）。全遊戲完成率未知；沒有build、測試、client
執行、啟用或部署。見
`docs/research/current-orange-shop-f5-ef-20261006.md`。

續輪 `20261006-bf-ee-f3-source-lists`：原生S2C EE/F3的WORLD
分派、長度、consumer與目的UI欄位已釘定。EE供C2S BF的
6-byte偶數模式列表；F3展開48-byte奇數模式列表；
`RecoveredBFSourceLists`純來源codec已加入，尚無服務端權威
資料、發送或BF結果因果。F5/EF僅改鄰近UI狀態。完整路徑
新增0；world parser62／限定來源41（局部66.1%）／gap11／
pending9、C2S候選151／S2C長度252不變；S2C非預設待接格式
10（+2）、未分類155（-2）。全遊戲百分比未知；未build、
測試、客戶端執行、啟用或部署。見
`docs/research/current-bf-ui-list-receivers-20261006.md`。

續輪 `20261006-bf-ui-row-producer-frontier`：BF兩個面板列族
分別讀取48-byte奇數模式列與6-byte偶數模式列，立即送包點
`CFC87`／`CFE77`；後段相同key時兩族可將body緩存，再走
同一確認送包點`842E4`。另有每日dialog32的共用queue分支。
原生producer分支數仍4，新增完整路徑0。world parser62、
限定來源41（66.1%僅限定分支比率）、gap11、pending9、
C2S候選151、S2C長度252均不變；全遊戲完成率未知。
沒有找到服務端列所有權／交易或S2C BE/BF因果，不擴大
Application准入。未build、測試、client執行、啟用或部署。
見 `docs/research/current-bf-ui-row-producers-20261006.md`。

續輪 `20261006-daily-bf-shared-queue-branch`：原生每日面板
dialog32確認經`8433D→8450B`共用queue送 BF，body是
item WORD、01/01、display amount DWORD；此前 BF v1
僅盤三處直接queue caller，故BF已知producer分支4（+1）。
新來源以預設關閉的 owned daily views 解析 BF，只接受已發
FD與owner/scene/保存內容完全相符的每日呈現意圖，無扣款、
發物或回覆。正式功能仍未接通；world parser62／限定來源41／
gap11／pending9、C2S候選151／S2C長度252不變，新增完整
路徑0，全遊戲百分比未知。未build、測試、client執行或部署。
見 `docs/research/current-daily-bf-purchase-20261006.md`。

續輪 `20261006-d8-retained-tail-admission`：原生 D8 mode1
`panel+20FEB` 尾位元組可保留00/A5/FF，Application舊的
`opaque_tail==0`條件誤擋原生輸入，已刪除，維持已發FD
清單與owner／NPC／位置／票券來源綁定。mode2為「每日領取」
按鈕，但原生request不帶獎品key。兩者仍只有意圖紀錄，
無傳送／領獎／Lua／原子儲存／因果S2C。新增完整路徑0，
world parser62、限定來源41、gap11，pending9（+1），
C2S候選151／S2C長度252不變，全遊戲百分比未知。
未build、測試、client執行或部署。見
`docs/research/current-d8-retained-tail-admission-20261006.md`。

續輪 `20261006-a9-context-immediate-frontier`：同版原生
`.text` 的11處 `061E..0622` 立即數引用已釘定；5處在
`F6DA0` 做 A9 判別，5處為一般資源查表，`6323A`
一處是記憶體初始化計數。這些重號不能成為 A9 的
NPC／道具／server offer 身分證據。A9 仍無正式 handler；
新增完整路徑0，world parser62／限定來源41／gap11、
pending8（+1）、C2S候選151／S2C長度252均不變。
全遊戲百分比未知；未 build、測試、client 執行或部署。
見 `docs/research/current-a9-context-frontier-20261006.md`。

續輪 `20261006-c2s68-format-parser`：四處原生有條件的
`961A0(68,1)` 呼叫及可本地分流的 wrapper 只證明送出
分支格式 `68 00`。已新增純 codec 與獨立預設關閉的世界
parser；Application 不啟用、不處理，也未假定 S2C3F／68
任一是回覆。新增完整路徑0；world parser62（+1）、
限定來源41、gap11（+1）、pending7（+1），C2S候選151、
S2C長度252不變；全遊戲完成率未知。未 build、測試、
client 執行或部署。見
`docs/research/current-c2s68-parser-frontier-20261006.md`。

續輪 `20261006-s2c83-two-stage-action-frontier`：S2C83
15-byte battle action有01..17共23個選擇值，第一分派
10不同case、actor分派14不同case。03/17兩層case相同
仍不代表語義相同；正式`RecoveredBattleAttackPresentation`
只限定01/03單體攻擊，0D delta與07診斷另列。完整表與
原始指令見 `docs/research/current-s2c83-action-frontier-20261006.md`。
新完整串接0，world parser61、限定來源41、gap10、
pending6、C2S候選151、S2C長度252差額0；全遊戲百分比
未知。未build、測試或部署。

續輪 `20261006-s2c-battle-dispatch-frontier`：原生戰鬥
`114332` switch在1C..89有110索引，九個專用opcode
`1C 38 83 84 85 86 87 88 89`、101預設；九個在WORLD
表皆為預設，故WORLD非預設206與戰鬥新增九項的入口聯集
215。86子型別0..6共七值／六個case地址；未稱完整變體。
本輪新增完整串接0，world parser61、限定來源41、gap10、
pending6、C2S候選151、S2C長度252無差額；全遊戲百分比
未知。未build、測試或部署。研究與原始表見
`docs/research/current-s2c-battle-dispatch-frontier-20261006.md`。

續輪 `20261006-s2c-world-consumer-frontier`：釘定原生S2C
長度表252可接收項（230固定／22可變）；WORLD dispatch
206非預設／46預設，非預設中41登錄來源回覆、8在pending
格式（C5重疊）、S2C68獨立格式1，帳本未分類157。
這不是157條已證漏接遊戲路徑；battle/login等另有接收狀態。
本輪新增完整連線0、world parser61／限定來源41／gap10／
pending6／C2S候選151／回覆下限41均不變，完整百分比未知。
未build、測試或部署。研究及逐opcode表見
`docs/research/current-s2c-world-consumer-frontier-20261006.md`。

續輪 `20261006-same-opcode-31-68-receiver-split`：原生S2C31
為29-byte神祇列更新，S2C68為13-byte獨立UI接收，使用
`UI+232DD8`；C2S68來源在大地圖`UI+232DA8`，S2C3F為
地圖開啟consumer，但不能依鄰接或同號填入因果。C2S31/68
均未進WORLD parser與Application業務路徑。世界parser61／
限定來源41／gap10／pending6／C2S候選151／S2C長度252／
回覆下限41／control10差額0；全遊戲百分比未知。
未build、測試或部署，詳見
`docs/research/current-same-opcode-31-68-20261006.md`。

續輪 `20261006-wrapper-ui-full-gates`：原生C2S31完整來源是
選定row bit0x10加六個row bit0x08排除檢查，舊三row說法僅
覆蓋尾段；C2S68四處wrapper caller仍受不同UI條件與本地
不送包分流限制。`31/68` 的服務端權限、狀態與S2C因果仍缺，
未增設handler。世界parser61／限定來源41／gap10／pending6／
C2S候選151／S2C長度252／回覆下限41／control10本輪均不變；
全遊戲完成率未知。未build、測試或部署。研究與原始指令見
`docs/research/current-wrapper-ui-gates-20261006.md`。

續輪 `20261006-candidate-frontier-spectator6e`：已知C2S參數候選
151與現行世界parser交集56、parser外95、parser獨有5；
95混合階段且含未證候選，不能當95個漏接世界功能。
原生C2S6E九bytes／五個直接caller追到mode1四處與
mode2/context0一處；body1..3未初始化。純codec與預設false
parser已加，Application沒有觀戰生命週期或回覆。
世界parser61（+1）、限定來源41（+0）、gap10（+1）、
pending6（+1）；S2C長度252／回覆下限41／control10不變。
全遊戲完成率未知，未build、測試或部署；見
`docs/research/current-spectator6e-20261006.md`。

續輪 `20261006-bf-s2c-panel-chain`：S2C BE先建立區域50格、
`BF`再更新既有格位；BE `5+24×count`、BF固定29-byte，
consumer `472560/472680`。已加原樣codec及bounded發送索引
檢查，沒有交易／C2S BF因果回覆／Application授權。
世界parser60／限定來源41／gap9／pending5／已知C2S候選151／
S2C長度252／回覆下限41／control10差額均0。完整百分比未知；
未build、測試或部署。見 `docs/research/current-bf-s2c-panel-20261006.md`。

續輪 `20261006-bf-bidirectional-format`：同版本原生C2SBF有
`842E4/CFC87/CFE77`三處8-byte body發送，S2CBF獨立29-byte
world consumer，沒有證明回覆關係。純codec及預設false parser
已加，Application不啟用，無交易/owner/Lua/SQLite/S2C因果路徑。
世界parser60（+1）、限定來源41（+0）、gap9（+1）、pending5
（+1）；已知C2S候選151、S2C長度252、S2C回覆下限41、
control10不變。全遊戲完成率未知；未build、測試或部署。
證據與限制見 `docs/research/current-bf-bidirectional-20261006.md`。

續輪 `20261006-e4-bidirectional-format`：同版本原生C2SE4
四個queue caller產生2-byte operation0..3；S2CE4為獨立
17-byte條件式UI consumer，不能依同號當回覆。純codec與
預設false解析flag已加，Application無handler/owner/Lua/SQLite
路徑。`68A30` 目前靜態入邊掃描仍為0，可達性未證。
本輪world parser59（+1）、限定來源41（+0）、gap8（+1）、
pending4（+1）；C2S已知候選151、S2C長度252、回覆下限41、
控制10、35 raw候選1不變。未測試、build、啟用或部署。
研究 `docs/research/current-e4-bidirectional-20261006.md`。

續輪 `20261006-c2s-wrapper-35-frontier`：新原始證據
`c2s-wrapper-frontier-v1.json` 追到第二分流 `68A30` 的
1F/22/23/35；35 raw16候選只有body8..11明確為FFFFFFFF，
無直接E8 caller，不能當已可達戰鬥action。31/68原生UI門檻
部分定位，仍無服務端權限/回覆。`RecoveredBattleCommand`來源
註記隔離此候選。不同opcode聯集151、world parser58、
限定來源41、S2C回覆41、control10、gap7、pending3不變；
新增未證可達raw變體候選1。未建置、測試或部署。研究見
`docs/research/current-c2s-wrapper-frontier-20261006.md`。

續輪 `20261006-c2s-wrapper-census`：verified原生映像 `.text` 的
31處已知`157D0/961A0`直呼及跳表新封存為
`c2s-wrapper-census-v1.json`；`1F/22/23/31/68/6D`六個
opcode均不在舊直接queue參數145內，已知聯集151（+6）。
`68`有本地訊息替代分支，`22/31/68`實際伺服器功能與回覆
仍OPEN。世界parser58／限定分支41／S2C回覆下限41／
控制10／gap7／pending3差額全0。全遊戲分母及完成率未知，
未建置、測試、啟用、部署。研究見
`docs/research/current-c2s-wrapper-census-20261006.md`。

續輪 `20261006-pet-activity9e-parser`：原生9E C2S7-byte格式與
state0/2的operation0/1、operation2的原始選取索引已整理。
`RecoveredWorldRecords`及`Session`新增獨立預設false解析flag；
Application不處理，活動、獎勵、Lua、持久化、真正S2C回覆仍缺。
世界parser58（+1）、限定分支41（+0）、gap7（+1）、pending3（+1），
S2C回覆下限41、控制10；完整遊戲百分比未知。未建置／測試／部署。
證據 `docs/research/current-pet-activity9e-20261006.md`。

# 2026-10-06 續輪：6B 雙向同號分流 V3

同一 verified mapped image 的 `.text` 直呼掃描找出C2S6B共享producer
10個E8 caller；新增 `97349`／`97370` 兩條固定selector2C、分別
lane1／3。S2C6B是獨立21-byte既有pool identity DWORD＋16-byte
NUL文字 consumer `6AABE→4CC910→509E70`。`6B4EF` 是另一條
S2CEC的owner|8000隨行名稱caller；兩者不可當C2S6B食物回覆。
新 `RecoveredWorldPoolText6B` 只有純格式，C2S6B仍預設false；
權威資料／Application發送／C++存檔／Lua效果全未接，沒有測試、
build、啟用或部署。新證據 `companion-control6b-static-v3.json`、
研究 `docs/research/current-companion-control6b-20261006.md`。
本輪世界parser57、限定分支41、S2C回覆下限41、控制10、gap6、
pending2，所有計數差額0；全遊戲串接完成率仍未知。


續輪 `20261006-companion-6b-wire-correction`：目前原生兩個C2S6B
發送函式將formal args反向寫入4-byte logical `6B,slot,selector,lane`。
舊獸類lane0 V1表格/codec順序錯誤，已在新證據V2與來源修正，
歷史artifact保留。已見原生lane0..4各caller；同號S2C6B是獨立
21-byte consumer，不冒充food回覆。新增預設false的世界解析flag與
純codec，Application、持有／消耗／效果／Lua／S2C因果路徑仍未接。
所以本輪parser57（+1）、未接功能6（+1）、pending來源群2（+1），
限定已接C2S41（+0）、S2C回覆下限41（+0），控制10。41/57約71.9%
只表示新擴大盤點分母的限定opcode來源覆蓋，非全遊戲百分比；
沒有功能退步。未建置／測試／啟用／部署。新證據見
`docs/research/current-companion-control6b-20261006.md`。

續輪 `20261006-pk-paired-settlement`：PK雙方canonical intent現在有
明確CUSTOM order／首擊致命取消第二動作的共用Battle來源；兩視角
83／86與回合最後88由同一結果構造，checkpoint、phase與兩份outbox
在同一SQLite transaction CAS提交。第二輪原始grant／counter仍未
復原，因此來源拒絕重用；Session RoomAuthority、真實profile、Lua
出手政策、全部技能／終局89／WORLD重入／重啟恢復仍缺。Application
仍未啟用，無schema安裝、建置、測試、正式更新。69／35不算接通，
WORLD56／限定C2S41／S2C下限41／control10／gap5，較上輪全差額0。
41/56=73.2%只衡量世界解析opcode至少一限定來源分支；全遊戲
完成率仍未知。詳見PK研究文最新節及本輪round report。

最新續輪 `20261006-pk-round-collection`：新增OwnedPkRound持久phase，
waiting entry保留原始86/5給雙通知後送出，typed grant epoch與checkpoint
revision分開；`submit_native`儲存雙方canonical intent和full native skill
snapshot CAS。舊立即act_native已替換；含round房間不能用舊advance
繞過收集。兩intent原子結算／fresh round counter/group/grant、真實profile、
RoomAuthority雙Session／timeout／全部技能／terminal／recovery仍缺。
獨立round schema未安裝；來源未建置、測試、啟用或部署，69／35仍未
接通。本輪56／41／S2C下限41／control10／gap5全部既有差額0。
41/56=73.2%是限定世界opcode來源覆蓋，**全遊戲完成率仍UNKNOWN**。
詳見 `docs/research/pk-source-coordination-20261006.md` 最新節；保留
下面歷史來源、未執行驗收及舊輪次，不能當最新source API。

Same-round native skill cache continuation: independent enemy agentv4 pins11
spans +both23-entry switches. Normal83/type3 first116DC1 fillsTHIS observed
id/kind atacting actorDF8, then same invocation117183 ->12C731 consumes it;
no ownside restriction, so side1 PLAYER cache prefix is now located.1C side1
still skips own50-skill copy. Full carried repertoire/four attack-defense/
primary/elements remainUNKNOWN. Native51-entry full case writes slot51 alias
EC4; not a capacity extension. Preserve earlier pk-action-view v1 OPEN note.
PK act_native now requires existing kind0/1 nonzero definition in current
NativeSkillCatalog matching mapped149...; shared transaction re-reads full
definition snapshot before checkpoint/outbox commit. Membership is not skill
ownership/native cost/balance. No new source connections, tests or deployment.

Newest PK action-view source continuation: RecoveredPkRelativeView exchanges
native2*14 positions/masks. RecoveredPkCommandSelection matches native35
owned actor/side/context, explicit basic or kind0/1 attack policies, complete
continuation, no duplicate/friendly/dead targets; kind2/3/control separate.
RecoveredBattleAttackPresentation preserves raw15-byte83/1 or83/3 scalar
templates and updates known source/masks/signed16 actualHP loss/outcome only.
RecoveredPkActionProjection produces BOTH relative83/86/88 from ONE result;
own-caster MP only, fresh raw groups/counters required, no guessed86/5/89.
OwnedPkRoomState::act_native joins trusted live identity/profile digest/server
permit -> canonical selection -> shared Battle -> two logical results ->
dual readset/shared checkpoint CAS/durable outbox. Not connected to Sessions
or Application yet. Pinned original8-span pk-action-view-static-contract.json
is static-only; opponent skill-cache dependency is tracked separately in
agent continuation. No new stats/skills/balance grants/client changes/builds/
tests/live DB/schema install/deployments.69/35 remain UNCONNECTED. Round
20261006-pk-action-views counts56/41/41/control10/gap5, all count deltas0.
Next: true profiles/entry, durable turn permits/0B/timeouts/grants, live dual
Session adapter, all skill effects/terminal/WORLD writer locks/recovery.

Newest shared-PK backend continuation: concrete OwnedPkRoomState owns ONE
Battle per room; SqliteOwnedPkRoomRepository same-connection dual owner full
resource/role/position readset + occupancy, retained AUTOINCREMENT ID, exact
opt-in feature DDL/version, shared checkpoint CAS + BOTH durable outbox entries.
Prepared entry resources/levels must match saved rows and canonical actors.
Stage on copied Battle; persist before publishing memory. Previous two-view
transport submissions must finish before next durable action. Submission is
not client ACK. Battle-local HP/MP only, no saved resource/XP/skill grants.
Finished locks retained; no fake terminal packet/reconnect recovery. Explicit
SqliteDatabase installer/factory added, NOT CALLED. Application pk_rooms still
null: real profile evidence/live CAS, dual Session adapter, skills/turns/native
replies, WORLD writer lock integration/termination/recovery remain missing.
No schema install/config change/build/test/client/live DB/deployment.69 remains
UNCONNECTED and default flag false. Round20261006-pk-shared-storage counts:
WORLD56/scopedC2S41/S2Creply41/control10/gap5; all count deltas0. Preserve older
reports below; new backend is source progress, not a connected branch.

Newest player-entry source continuation: normal82 actor pointer prerequisite
now resolved statically against original111424->11FC40;11FC8E fills all168
manager pointers from inline arena,2*14*6. Old pk-identity-static-frontier and
prior initializer evidence remain unchanged. Renderer handle is a separate
prerequisite:1C2000 rejects-1; normal86/4 before1C required. New pinned11-span
pk-player-initialization-static-contract.json records these dependencies.
RecoveredBattlePlayerAppearance parses exact17 bytes,position logical2,mode3,
appearance4..11,special WORD13 (handler input is logical+1). New
RecoveredPkEntryProjection prepares two owned raw-record views, own0/other14,
82 ->both86/4 ->1C/vitals ->88 ->86/5; no unsupported opponent MP.
No guessed DA conversion, profile seed, context value or monster fixture.
RoomAuthority reservation must carry Prepared entry matching both live IDs
before any invitation. Application pk_rooms still lacks a real implementation;
69 remains UNCONNECTED, default flag false. Shared profiles/skills/combat/CAS/
termination are next. No build/test/native execution/live DB/deployment.
Round counts unchanged: WORLD56/scopedC2S41/S2Creply41/control10/gap5.

Newest PK source continuation: RecoveredPk69 native45-byte codec, opt-in WORLD
parser/Session flag, Application owned-peer/world-generation resolution and
OwnedPkInvitationService proposal lifecycle plus Lua CUSTOM0086 eligibility
are now in source. Default flag false; no formal config changed. RoomAuthority
requires prepare/current/atomic common commit/abandon; Application pk_rooms
has NO implementation. Never publish8A until a real room reservation exists,
never set InBattle/send82 from this coordinator. This is INCOMPLETE, not a
connected PK branch. Native reply69 swaps incoming8A IDs and two text zones;
CUSTOM base36 reservation/generation context rejects old same-player offers.
60s lazy expiry/owned-position revision/WORLD and battle generations/disconnect
and potential movement revoke leases; no fabricated close/timeout ACK. No
build/test/client/runtime/live DB mutation or deployment occurred.
Current round WORLD parser56 (+1), scoped connected C2S41 (unchanged), control10,
unconnected gameplay5 (+1,69);17 groups/S2C reply41 lower bound unchanged.
Next: qualify1C PLAYER variants/relative sides and82 context, authoritative
two-owner profiles/skill source and shared35/83/86 room state/CAS/lifecycle;
do not copy EnyName0400 fixtures or bind two isolated diagnostic battles.
See docs/research/pk-source-coordination-20261006.md and pending source ledger.

Latest owner reporting requirement: end EVERY round with packet inventory,
specific connected source branches, deltas and remaining gaps. The static
round reporter is tools/reconstruction/packet_connection_report.py; ledger
and latest Markdown live in artifacts/integration/packet-connections-20261006.
First baseline: native S2C252 supported length opcodes, C2S145 direct argument
candidates (not confirmed total), WORLD55 parsed;41 have at least one reviewed
scoped source branch,17 groups/41 recorded S2C reply-opcode lower bound;
10 controls/diagnostics and4 unconnected gameplay. Full game packet count,
complete route count and percentage UNKNOWN. Do not count all opcode variants
as complete or treat these values as deployment/client acceptance.

Latest static continuation: guild war UI native76 subtype5/9 and95/96 branch
contract recovered in guild-war-static-contract.json. Exact raw1/2/3 removal
selects8, raw4/5/6/7 selects9; display masks7F separately. Row logical6/7/8
are displayed as month/day/hour via original literal "%2d/%2d %02d:00".
RelationsRawCodec names those display kinds and date bytes; existing alliance
projection uses equivalent named constants only. No calendar/year/minute/
timezone, server permission/fee/schedule or authoritative war writer inferred.
Immutable53 alliance states0/1/2 unchanged; war5/9 remains OPEN, no new route,
installer/build/test/live mutation/deployment. See research/guild-war-connections-20261006.md.

Enemy-field subagent static frontier-v3: native right-click PK action-5 sends
69/control0 (45 bytes); server8A opens dialog13; replies use69/control1 accept,
2 reject,3 busy. 6E/1 is watch.ani observation,6E/2 observation exit; neither
is enemy-stat inspection. No authoritative PK/observer room connected yet.
Enemy four primary/five element/four attack-defense values and full carried
skill list remain UNKNOWN/null. Private schema49 fixtures were prepared but
no live two-character PK or PvE occurred; custom consumer inputs are not
official/native capture evidence. Preserve frontier-v1/v2/v3 independently.

Use `docs/PACKET_CONNECTION_GOAL_20261006.md` and the active goal. Cleanup is
complete; the old waiting automation `god2` is PAUSED. The owner now explicitly
requires full bidirectional source connections first, comprehensive tests only
after all gameplay routes are connected, then comprehensive repair/release.
Do not resume the old per-feature native83 update/acceptance sequence below.

Latest source continuation: full ordinary PET bank63/64/65 is connected
through Application original-frame one-request/ticks/chat capture and exact
positioned late dispatch, OwnedMixedBankService optional same-connection
SqliteBeastBankRepository, Lua CUSTOM0085 inactive whole PET policy. Full50 bag/
300 vault/all overlays/PET/raw-selection CAS plus typed unrelated schema/history/
money/equipment guard protects atomic deposit/withdraw/whole vault neighbour
swap. Deposit retires matching valid/stale selection before FK parent removal;
withdraw creates no selection. Separate CUSTOM bag/vault BYTE selector namespaces
rebind only logical3 of4C/nullableC5 on collision; all other bytes/evidence/pins
remain. Explicit beast_bank_schema_0085 version4 adds empty vault custody/receipt
feature tables after base bank registration, preserves old1/2/3/base ledgers and
all prior DDL/rows/receipts. NOT INSTALLED. No capacity/instance grants on read.
Bank opening retains old owned NPC/placement/money lease and scalar provisioning.
All30048 on opening, changed full48 plus4B(0,0)/full30 41/3B/41 after commit;
fresh rejection synchronization; only custom exploration menu lease retired.
Other category writers retain their own paths, extended own PET proofs/new-ledger
collision checks. Both PET/mixed flags required, default false. Native static
artifact beast-bank-static-contract.json; research/beast-bank-connections-20261006.md.
No build/test/native runtime, live mutation, installer execution or deployment.
Acquisition/food/riding/exploration/rewards/appearance and original binding remain
open. User subsequently authorized a separate subagent enemy-property blackbox
research; that exception does not enable per-feature mainline tests or release.

Previous source continuation: whole ordinary PET player trade is connected
through existing native29/2A/2B/2C/2D and50 full peer instance projection.
Application selects a new same-connection beast-aware0069 repository only when
both owned_instance_trade/PET flags are enabled (default false). Lua CUSTOM0085
admits whole count1 inactive presentation PET. Both owner full50-slot/overlay/
wallet/custody/raw-selection CAS plus typed unrelated schema/history/equipment
preservation protect atomic transfer. Sender matching valid or stale selection
retires before FK parent removal; recipient is not auto-selected. CUSTOM BYTE
selector rebinding alters only logical3 of4C/nullableC5 on identity conflict.
All other bytes/origin/evidence/source/client pins survive. New tagged PET
receipt states use existing0069 DDL; old receipts/default encoding unchanged.
52 success or4F cancel closes followed by4B(0,0), full ordinary41/3B/41 and S2C27
purse; fresh cancel/disconnect/custom60s restoration. Trade deliveries retire
session exploration view lease only, not activity. Native static contract:
beast-trade-static-contract.json; research/beast-trade-connections-20261006.md.
No tests/build/runtime execution, installation, activation, deployment or live
mutation. Original binding/activity, bank/food/riding/rewards/appearance remain
open. Existing character erase FK graph covers PET custody/selection; no-FK
discard journal survives. No new delete implementation or acceptance claimed.
Goal ACTIVE; complete whole-game source routes first.

Previous source continuation: ordinary-bag PET native27 discard is now connected
through Application whole-frame preflight, OwnedBeastDiscardService, CUSTOM-0085
Lua eligibility and SqliteBeastBagRepository::discard. Exact full50-slot/PET/raw
selection/peripheral CAS protects the standalone writer. It retires a matching
valid or stale selection before deleting full custody, clears the exact owned
count1 scalar, advances its revision and journals every removed20/4C/nullableC5
byte, origin/evidence/source/client pin and retired selection. Unrelated rows,
selection, equipment and old journals must remain exact. New independent feature
beast_discard_schema_0085 version3 installs only from the explicit managed beast
installer; it does not modify custody1/selection1/equipment2 or base1..53 ledgers.
Receipt owner IDs intentionally have no deletion cascade; they are server-only
removal history, never restored inventory or new player authority. NOT INSTALLED.
CUSTOM reply pairing is4B physical-slot BYTE/0 followed by native41 clear, so
85ABD matches the physical clear and closes the current beast presentation.
No ground drop or activity cancellation is recovered. Lua admits only whole
ordinary PET with no native exploring label or alternate7/8 presentation flags;
equipped37 and original bind/drop/activity rules remain separate open work.
Preflight captures full positioned idle WORLD before prefixes; late dispatch
repeats owner/position/state and retires bank/view leases before the writer.
Rejected writes use a fresh qualified owned source projection. Successful reply
allocation occurs before mutation and post-commit logging cannot report rollback.
Native static evidence: beast-discard-static-contract.json. No tests/builds,
client/emulator execution, DDL, activation, deployment or live save writes.

Native83's 8 changed /22 added source files and relations53's 9 changed /23
added source files are now integrated into the formal source tree. Admission53
adds actual native7A/85/8D/6F create/apply routes, strict53 storage and Lua policy,
wallet replies and roster reconciliation. Ordered native91/92 bootstrap supplies
an EXPECTED cache baseline; it does not claim actual client memory observation
or new acceptance evidence. Guild world authority now retains nonzero historical
battle generations, while current WORLD and durable active-battle checks remain.

No builds/tests/client runs/restarts or live DB changes were made during this
connection phase. Running service stays schema51; source integration is not
deployment. Source changes make old filled updater baselines/receipts unusable;
the final release needs fresh source CAS, process observations, backup and
schema51→52→53 recovery preparation after full testing. Preserve all old evidence.

Static index: `artifacts/integration/packet-connections-20261006/static-packet-index.json`.
It contains 256 S2C length entries, 225 direct queue byte candidates and 53 world
parser opcodes. These are different scopes; none is a whole-game denominator.
Wrapper/indirect producers, war5/9, mixed guild mutation sequencing and remaining
gameplay routes stay open. Exact source work and old files are retained in
`artifacts/integration/packet-connections-20261006`.

Beast panel work now has a C++ codec and pinned static source artifact:
`src/protocol/RecoveredBeastPanel.h`,
`artifacts/integration/packet-connections-20261006/beast-panel-static-contract.json`
and `docs/research/beast-panel-connections-20261006.md`. C2S6C/9D and shared
food6B/lane0 belong to PET beasts, not COM/E3 pets; S2C4C/4D carry their selected
panel state. Owned snapshot storage and an opt-in Application25->4B/4C panel
presentation route are connected in source under CUSTOM-0085. Actions, Lua
operation rules and appearance remain open; no whole beast gameplay claim.
The expanded exploration codec now covers C2S9E/9F and S2CC5/C6. Correct binding:
C5 ->D8490 body308, C6 ->A0A90 body6; the old C5 annotation is retained as prior
analysis and corrected in V2. Complete native PET declaration keys147 are now in
`NativeBeastSourceCatalog.h`; current whole gamedata differs from original but
its147 ordered PET rows still match. Original pins are preserved. CUSTOM-0085
adds raw owned snapshot custody, managed accessor and explicit additive feature
ledger version1 that preserves base1..53 history. Installation code has NOT been
executed. world.owned_beast_panel.enabled defaults false.25->4B/4C pairing is custom
presentation, not original server evidence. Custom selection now persists selector/
custody revision/selection revision under a second immutable feature ledger.
WORLD restore projects full owned metadata20 and valid selected4C; the optional
shared bag projector preserves custody and raw selection in mutation proofs.
No gameplay activity lease is inferred and no feature DDL has been executed. Continue acquisition/action/food/timer/reward/appearance and
bank/trade/discard custody integration, deletion and activity reconnect. Native24
ordinary-bag whole swaps are now connected via SqliteBeastBagRepository, including
qualified neighbours, stable selected selector and full typed preservation.
Immutable original-frame capture occurs before prefixes; no feature was activated.
Two gated Session/world parser branches9D/9F and OwnedBeastExplorationService
now connect kind2/non-alternate owned C5 display and exact old-context local close.
9E activities and all alternate/non-exploration9D effects remain open. Original
9D->C5 pairing is not claimed. New static nativeA0700 evidence corrects body6
WORD from unsupported lifetime naming to percent display (FLOAT0.01, ProgramMsg362);
V2 analysis is retained and current V3 corrected without changing wire bytes.
Tests and builds remain deferred; current service and saves have not been modified.

Latest continuation expands native25 PET52/54 via the separate same-slot9AA07
producer into the existing owned panel route; SPI55xx remains excluded without
PET source membership. RecoveredBeastPanel now also projects exact4D inventory20
writes (latest correction: WORD10 low3 palette, BYTE9 full level/date BYTE,
WORD12 percent/date WORD; class5/body2 1..6 guard). Earlier6/5/8 annotation was
wrong because record+4 was subtracted twice; V1 evidence remains prior analysis.
This helper does not authorize food mutation. New bounded static evidence and
all65 original PFD rows are retained in beast-inventory-controls-static.json.
37 equipment key changes close the beast UI rather than reopening it; full28/37
custody and activity/appearance remain open. Preserve immutable custodyv1 0..29.
Continue source binding of food type/quantity fields, atomic consumption/Lua
effects and37 equipment state; no percent or original gameplay completion claim.

Latest class5 tooltip B90E7..B95EA and definition parser5970D recovery is retained
in beast-inventory-fields-static.json. Original PET zero-based column27 is read
as decimal, stored as lowBYTE at definition11C; 143 rows are zero, four nonzero
(5232=1,5350=1,5351=168,5380=72). Zero selects classic BYTE9 level/WORD12 EXP
percent; nonzero selects packed-date interpretation of WORD8/12/14. No date
duration, expiry or calendar gameplay rule is inferred from source names.
Classic WORD14 is use count except modes4000/8000, where it is elapsed minutes;
WORD16 transfer-use flag/count is displayed only in that latter branch.
WORD4 low14 is fatigue limit, WORD10 low3 palette; this does not establish the
panel meter or percentage BYTE's gameplay meaning. RecoveredBeastInventoryFields
now provides source-qualified branch views and actual custody admission uses
that view, preserving all original bytes and both branches without EXP caps.
Food6B, activity, stat and appearance rules remain open. Source only; no test,
build, client execution, installer, activation or save change has occurred.

Equipment37 storage/source admission has subsequently been connected under
CUSTOM-0085: native28 whole-frame capture -> OwnedBeastEquipmentService -> Lua
bag/37 placement -> SqliteBeastBagRepository explicit equipment domain -> full
41/3B/41 replies and WORLD restore. Original native24 remains ordinary-only.
All source/instance bytes and provenance move together; valid selection revision
advances, stale selection remains stale, and custom exploration view retires.
Additive beast_equipment_schema_0085 version2 expands custody CHECK to37 while
retaining the original schema()/custodyv1/selectionv1 ledger records. The explicit
fixed-schema migration has typed whole-save/DDL preservation and final FK guards;
it has NOT been executed. Existing default-false activation remains unchanged.
Next: food scalar-to-wire/source binding, atomic consumption and Lua rules;
equipment activity/stat/appearance, acquisition and remaining transfer domains.
Do not claim riding or whole beast gameplay merely from the28 storage route.



---

# GOD2 server continuation — 2026-10-06

The archived source chat is `01a0ca9c-41dc-7720-8dda-2a550ffced90`.
Read it only; do not restart it or send work to it. Its latest turns were
interrupted. No God2 Python/build/update worker was found in the new process
inventory; unrelated LC workers were left untouched.

## Current owner steering

The owner chose **wait for cleanup to finish before updating**. Cleanup chat
`01a10de0-4980-7e40-8cd5-32f615574f07`, titled
`整理 God2 待刪除資料夾`, is still active. Do not send it messages: the owner
chose waiting instead of authorizing coordination. Do not write, restore or
deploy into the historical directories while that chat archives/moves them.
Read-only audits and new continuation files are outside its current move plan.

Thread heartbeat automation `god2` was created successfully to check cleanup
every 10 minutes, stay quiet while unchanged, and resume this work after
completion. Disable this waiting monitor after actual continuation starts.

## Newly observed formal state

`artifacts/continuation/native83-20261006/observe_current.py` exited 0 after
fresh Win32, psutil, listener and task observations. It preserves the original
schema/config/binary/whole typed save/frozen-chat comparisons. It discovers
the current PID from the actual listener probe and compares raw FILETIME with
that same fresh probe; it does not bind a new execution to an old launch PID.

- Observed PID 10872; raw creation FILETIME 134356375411228043.
- Own listener 2592, zero connected players, schema migrations 1..51.
- Binary SHA256 `1062075f3d2063650a28adc4c9053ac5a68c646dbbb4ea0229af28bfdb8251c9`.
- Config SHA256 `cf2a708f54e4dd18bfcc8a0df164a1eae8321649db6dab727455e1914686366d`.
- Whole typed saved state equals the accepted installation; no SQL writes.
- Frozen-chat verifier passed with the original baseline unchanged.
- Formal source/binary/config/database/client have not been changed by this continuation.

These observations expire as execution authority. Re-observe before any future
deployment; do not reuse PID/HANDLE/approval receipt as a fresh binding.

## Native83 update repair

Current subject is
`artifacts/research/native-guild-founder-transfer-0083/formal83-held-root-orchestrator-draft-v03/orchestrator.py`.
SHA256 `b83aed6ef543999971d1d242ad1d3aff52a225447e2e6976bc6c49e40c9712f3`.
It closes the initial native import scope before acquiring the retained lease
and before nested guard/source/executor scopes. The original lease remains held.
The separate frozen query also closes its short import scope before execution.

On-disk V03 independent Windows scope review and full query-only replay r02
both report accepted; their current input hashes were checked unchanged.
Old V01 actual failure and source journal absence remain preserved. The old
filled bootstrap/orchestrator has stale execution literals and MUST NOT run.

Historical V09 candidate native qualification reports both locales 950/936
accepted against candidate SHA256
`0ec5208fa2d7dfd498aaad2ff1901cbadf403eecee84418bf7bf4df791bda1b0`.
This is candidate acceptance; native83 is not formally promoted or active.
No renewed qualification is claimed until all original pinned inputs resolve.

## Cleanup changes and recovery

An 8,138-file input plan is retained outside the cleanup directories at
`artifacts/continuation/native83-20261006/required-inputs-v02.json`.
It unions the formal 2,495-source baseline, native V09 contract inputs, actual
native artifacts, primitive V02/V03 closures and V03 orchestrator anchors.
It grants neither restore nor deployment permission by itself. The retained
V01 plan incorrectly treated the qualifier folder Q as a file anchor; V02
removes that directory entry while retaining the separately pinned qualify.py.
No original authority/contract/baseline was changed.

Initial read found one missing formal baseline file:
`build-native-guild-formal-tail-20261004/Release/god2-server.exe`, expected
SHA256 `76d9e815628b1736dd013915fb1d42d2cb0e5d5eb49c028d745ac657355b6fa6`.
The native contract had 497 missing inputs, mostly historical bytecode.
The candidate executable was still present. Do not remove those inputs from
the old contract, refresh baselines or call missing evidence renewed acceptance.

A source-only reconstruction check reproduced 408/496 missing bytecode files
in memory with their exact historical SHA256, without writing any cache or
restoring anything. The remaining 88 files (22 unique basenames repeated in
four historical shadows) did not match the tested filename/timestamp/compiler
settings. This is evidence recovery work, not gameplay testing or deployment.
The two old schema50 release executables checked have SHA256
`8eaac6f7e40348585500428007b74cd9656748afdedabdca5a034433805c325b`;
they do not replace the missing formal-tail binary's expected hash.

The cleanup archive is
`C:/Users/risei/Desktop/God2/artifacts/歷史精簡封存_20261006`.
Its SQLite manifest maps original project-relative paths to SHA256 zlib pack
objects. Trust extraction only after metadata `verified=true`, cleanup move
and final scan complete. Restore only required inputs and verify exact hashes;
do not restore entire historical client copies or build trees. The owner has
asked the cleanup chat to reduce the project below 50 GB.

## Next execution

1. Wait for cleanup completion; inspect its final status and move/archive proof.
2. Resolve the retained input map by exact hash and restore only required bytes.
3. Re-run fresh read-only owner/save/profile/frozen checks and native predicates.
4. Create a NEW launcher identity, execution directory, continuous lease and
   literal bindings from current V03. Preserve source CAS and release recovery.
5. Apply exact inactive registry + 8 replacements/22 additions, schema51→52
   using the reviewed managed release. Perform new postinstall native83
   acceptance before activation; never run old schema51 executable on schema52.
6. Continue common relations/native6F and town/indoor battle gaps thereafter.

## Relations84 limits and packet status

The latest inspected common-relations candidate84 report and independent
review show a compiled private Application/schema53 route, 36 synthetic TCP
requests and 34 mutator denials, **zero successful commits**. Receiver cache
baseline is NULL. Native6F accepted prompt, post-battle generation and mixed
mutation domain policy remain open. Do not describe this as playable or promote
it from its negative TCP success.

A new current-source packet census in
`artifacts/continuation/native83-20261006/current-packet-gap-ledger.json`
counts **52 distinct world-stage C2S parser opcodes** (dated 2026-09-30 report:
27). This includes parsing-only/denial/working routes, excludes login/character
stages and is not a count of complete gameplay features. Native S2C receive
length domain remains 230 fixed +22 variable +4 unsupported byte values.
No whole-game packet completion percentage has a reliable denominator.
