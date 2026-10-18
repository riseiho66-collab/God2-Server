# 台服神廟、客棧與野外傳送修復：2026-10-18

本文件記錄本輪原台服資源及 REA 證據、來源資料稽核與新增規則的界線。98筆同圖版本已完成隔離Release建置、focused tests、兩區各一組實際Application TCP驗證並切換本機服務端；原版area2野外一組往返及抵達後走動通過，使用者確認房間可進入。其餘點未逐一原版驗收。新增的碧遊宮跨地圖回報另記於末節，各階段證據分開保留。

## 神廟與客棧：CUSTOM-0152

楓華集原 MDL 已帶有三棟建物的正確室內附件，對應 HMD 原檔也存在。缺口在 CAN 的 scene 資源選擇與這些附件不相符，因此舊入口匯入器將三條路線列為 `RESOURCE_MISMATCH_NO_ROUTE`。這是已證明的靜態資源配對缺口；將這些 scene 指向建物附件仍是明確的 **CUSTOM-0152 selector 修復**，不是聲稱取回原官方服務端的 scene 配置。

| scene | 原 MDL placement offset | 原附件 | CAN WORD offset | 原 file index | 修復 file index |
|---|---:|---|---:|---:|---:|
| 10 | 35492 | `indoor/TP_Nor_L.hmd` | 2340 | 1：`god01.hmd` | 34 |
| 12 | 36598 | `indoor/TP_Nor_R.hmd` | 2344 | 1：`god01.hmd` | 33 |
| 22 | 39351 | `indoor/hotel01.hmd` | 2364 | 17：`hotel02.hmd` | 29 |

候選 CAN 保留全部 36 筆原 file records 與 130 個 scene entries，只調整上述三個 WORD 欄位；六個欄位位元組中實際改變三個位元組。原 CAN SHA-256 為 `f2b9ca9dc4dcebcd1c1c40de14ea63f1b2061993f644c49b9c7baca9ce2d2f97`，候選為 `73156f4c2060f92e1be59fa9c2df30841b3df204121491a765c1ca21e68796ad`。已在客戶端關閉時套用並核對新 SHA，2580-byte原始基準保留於外部套用收據；原版遊戲已重啟，但尚未視為遊戲內驗收通過。

原楓華集 MDL 壓縮檔 SHA-256 為 `bb2b72c2cb368ad9e91046783e1c9638ef02318f589cf462f0c45bbfdce04618`，解碼 SHA-256 為 `59fd88e12c232c89ae8cb73fed4058090e708f963fc9525ededfe157fccfebef`。現用 MDL 已有 CUSTOM-0151 布告欄修補，本輪以先前保留且逐檔驗證的原台服 MDL 基準讀取原 offset，沒有把改過的 MDL 當成原始 pin。

三份原台服 HMD 的壓縮檔 SHA-256：

| 原檔 | SHA-256 |
|---|---|
| `TP_Nor_L.hmdZ` | `b5201259f272c6039069d0dbc7f4bc404ae61d59899c508b6e81e913ba24efaa` |
| `TP_Nor_R.hmdZ` | `cce0a099d4264b73a7db54df6c5ee7d159b52c8f0df4c4966d2f4c37a578ec82` |
| `hotel01.hmdZ` | `07aa9bf3df4ef93508a175b92f98f8c4cbf4ed6896b8faa6f488fc8e7ca6c184` |

新增三房各有兩組原 marker 導出的進出點，共六組。HMD 導航格由既有 C++ `recovered-indoor-grid.exe --dump` 產生；每個室內進入與離開點都在格內且非零。原楓華集導航的所有涵蓋窗口對新 town trigger 都一致為 `02`，town arrival 都一致為 `01`，沒有補造最近可走點。

`resources/world/tw/town-doors-v2.json` 在本次唯讀稽核中與外部候選逐位元組相同，SHA-256 為 `cec9ce29fffd1b09e7988d28bc22c330841e7efad2c41a26a0e0cc3a6b1e2868`。原有 23 個 route 與 23 個 navigation object 完整保留，追加後為 **26 房、26 份導航、32 組進出點、52 條方向場景連線**；原 Lua 的 26 組列保留，另加六組。這些是資料與導航資格，不等同 26 房全數取得原版客戶端收發、持久化及互動驗收。

## 野外同圖傳送：CUSTOM-0153

使用者提供的鴻濛境 `area=2, scene=0, x=407, y=256`，直接吻合原 `Island01.mdlZ` offset `122526` 的 marker0。原 MDL 壓縮 SHA-256 為 `cbdc0c946618a1bf4a9b2f221283a17fa58b1f49941b2ea336046851a2519d8d`。

該 placement 為 `[161,1080,460,411,246,0,391,266,1,0]`，marker fields 為 `[3,14,-1,-1,3,13,-1,-1]`。原生投影 `00449BB0` 使用整數除法向零截斷：

```text
project(a,b) = (a - trunc(b/2), a + trunc((b+1)/2))
absolute point = placement anchor + project(marker)
(411,246) + project(3,14) = (407,256)
```

REA 核對原生 loader `0043EE20` 把 placement fields6/7 保存至 instance+1C/+20；`00448980` 使用它們呼叫 `0043F1C0 → 00442990`，以完全相等的 anchor 座標搜尋目的模型。**fields6/7 是目標模型 anchor，不是直接抵達格。** 此例目標 anchor `(391,266)` 唯一對應反向 placement offset `137558`；其 marker0 為 `(384,275)`。

原指令 `00448EF5: 6A00` 將 slot0 傳給 `00448980`，呼叫位址為 `00448EF8`；`00448F61: 6A01` 將 slot1 傳入，呼叫位址為 `00448F64`。目的模型按相同 index 取 marker，因此此 helper 的規則是 **source0 → reverse0、source1 → reverse1**。point2/3 在另一個室內出口分類路徑使用，不能把 reverse2 宣稱為此同圖 resolver 的原生抵達點。

靜態 REA 證據使用當前台服 EXE SHA-256 `99cde6b666101c0702d712a1a15bf4d83f225a1a521a9c601bd32a6e42debe25` 的逐位元組相同程式頁。已核對的 helper、原指令與原 marker 算式，沒有證明最外層自動傳送 caller、官方服務端授權或新的專用 C2S 傳送封包。普通移動封包的存在也不能補足這個因果鏈。**自動移動觸發、目的地授權與重新觸發政策仍屬 CUSTOM-0153。**

## 28 條精確方向連線的資格

原台服 Island01 有 34 筆同 MDL 參照，能組成 17 組唯一互反 anchor。每組分別檢查 slot0、slot1，共 34 個 slot-pair 候選。本輪只接受：

- 兩端 marker 都存在，且來源與反向 anchor 唯一互反。
- 每端在完整 `2/0` 導航中，所有涵蓋窗口的位元組均相同且非零。
- 同一來源座標只有一個精確目的地；不套用 `01/02` 布林例外、不移動到鄰近格。

結果有 **14 組可用座標對、28 條精確方向 tuple**，涵蓋 11 組原 anchor；20 個 slot-pair 排除，其中 15 個缺少同 slot marker、5 個出現窗口位元組矛盾，來源多目的地衝突為零。`407,256 → 384,275` 與反向均在資格表內。判定使用 marker0/1；marker2/3 僅留作原資源證據。

本次直接比對產品 `src/game/RecoveredWildernessTransfers.h`、`scripts/gameplay/current_wilderness_transfers_data.lua` 與外部 policy，三者均為 **28 筆、28 筆唯一 tuple，逐列及順序完全一致**，且只含 `area=2, scene=0`。C++ 採完整六欄 tuple 比對，Lua 規則之外還須經核心狀態與權限檢查。

目的 marker 本身可能也是另一端 trigger。`diagnostic_door.lua` 的無位移 guard 會在 before 與 after 座標相同時直接返回；28條tuple的服務層權限、CAS、pending、落點no-op與反向測試已通過；實際Application TCP亦驗證407/256往返384/275、入口批次截斷及正確owner receipt。這仍不代替原版客戶端畫面驗收。

## 未涵蓋範圍與驗收狀態

全量來源盤點是 **142 份 MDL、1619 筆地圖參照**，含 486 筆同 MDL、769 筆跨 MDL、363 筆 HMD 與一筆缺少目標的其他參照。486 筆同 MDL 均有唯一互反 anchor，共 243 對；跨 MDL 部分仍有七筆無互反匹配，`tong/Reborn/Reborn.mdt` 目標缺失。這些數字是靜態資源圖，**不是 142 張地圖傳送全部完成**。

本輪新增 wilderness 規則只登記 `2/0` 的 28 條 tuple。其他 141 份 MDL 沒有因此取得新 wilderness 啟用資格；其原生 selector、導航與服務端行為仍需各自查證。Island01 被排除的 slot-pair 也沒有以猜測落點補進規則。

目前狀態：來源／資料稽核、Release建置、focused測試與Application TCP整合QA通過；本機服務端已切換，**原版台服客戶端遊戲內驗收PENDING**。隔離QA使用現用資料庫的一份一致快照；啟動前後全部資料表結構與typed rows完全相同、schema仍51。TCP合成人物只建立於該QA快照，正式角色存檔未被測試腳本編輯。

完整外部證據位於 `C:/Users/risei/.codex/artifact-archives/god2-server/20261018/board-object-rea/door-repair/`：

- `tw-door-static-assets.json`、`tw-door-bundle-preparation.json`：原三房資源、marker、C++ 格與 CAN 候選完整 pin。
- `wilderness-native-transfer-consumer.json`、`wilderness-rea-complete-evidence.json`：原生同 slot helper、指令、證據限制。
- `tw-wilderness-transfer-inventory-v1.json`：142 份來源 pin、1619 筆分類及 Island01 全部互反原點。
- `tw-wilderness-transfer-policy-v2.json`：28 tuple、逐端窗口 index／值及全部排除原因。

## 建置、封包 QA 與部署記錄

- `server-build-v3.log`：服務端及三個測試目標 Release 建置通過。集中建置並最小修復既有 optional 回傳型別、shared_ptr 計數、ULONG上限及generic completion空例外推導問題。MSVC map move會配置sentinel，PET保存快照改為相同排序的vector，保留COMMIT後nothrow static_assert與完整schema/row比較；未改SQL或玩法規則。
- `focused-ctest-v2.log`：diagnostic_door、wilderness_transfers、recovered_parent_route全數通過。wilderness涵蓋全部28tuple、停用旗標、owner/revision、pending、同圖reuse、防反彈、反向及三步批次的入口前綴。
- `qa-startup-preservation-v2.json`：私有快照啟動後schema51、全部schema與typed rows不變，未開啟正式DB。v1因QA檔名不符合既有diagnostic guard而拒絕，保留失敗證據；改名同一QA檔，沒有新增副本。
- 外部上一層 `qa-tcp-transfers-v2.json`：實際TCP登入／選角／ready／移動，驗證407/256→384/275及反向、批次只ACK第一入口、SC61 reuse與持久化、防反彈，以及scene10/12/22各第一組門點往返。其餘三組新門點尚未逐一TCP往返。v1硬寫舊角色1的receipt而被正確拒絕；v2使用合成人物自己的identity及初始化flag，未放寬服務端guard。
- `tw-town-door-can-applied-v1/applied.json`：三個CAN實際差異已套用；現用MDL／HMD圖資不變。
- 本機release：`artifacts/releases/map-transfer-repair-20261018/server-config.json`，二進位SHA-256 `bd60bbd08b8cc2735cc5404e8ad41385ce13b38d76cb1f83d85d7890f3245fbb`。切換前確認遊戲關閉、舊服務端沒有Established連線。沿用原正式DB路徑與功能旗標，只改26房bundle及log位置；未執行資料搬移或schema安裝。

Application現在逐步驗導航／sequence後，停在第一個合法入口，只提交並ACK該前綴，然後沿既有SC61及pending receipt流程。舊場景剩餘步驟不提交、不ACK；未指定predicate及owned-material路仍採原整批規則。這避免同一flush跨過入口卻不傳送。原生0046C4EA的receipt攜帶人物identity及同一world初始化flag，不能固定為角色1。

## 原版實機失敗與後續修正（16:28）

使用者已登入現用原版台服遊戲，session2／character2從408/255走入407/256。服務端回ACK與同圖SC61、保存384/275，原client回正確02000000 receipt，服務端接受；225ms後下一個移動被拒絕，畫面仍留407/256，使用者回報位置偏移。這次實機驗收FAILED，不把TCP helper的封包格式通過視為原版可玩。

新REA核到SC61 reuse分支在46C2B9直接跳46C414，跳過full分支的5011C0(0)。後者清motion state+30/path index+34/path count+38；502570的state8路徑可在下一frame將舊path末點寫回world+224/+228。原先短距kind0 town的reuse證據不足以支持正在走動的kind1野外。後續只對新增registered wilderness取消bit16、走原full reset，其他既有town行為保留；重新建置、private TCP及原版實機驗收結果須另記，當下不得標PASS。

REA Frida provider本機缺少frida package，沒有建立runtime hook；上述指令是REA靜態證據，畫面與時序來自原版UI及本機服務端log，不冒充Frida觀察。

## 完整重設版本（第二次部署）

`sc61-reuse-vs-full-reset-rea-evidence.json` 保留7個原生函數與9組指令probe；完整結論為 `sc61-reuse-vs-full-reset-findings-v2.json`。46C2B9的reuse分支跳46C414；full分支46C2FA呼叫5011C0，5011E6清state、5011FB清path count、5011FE清path index。502648／502652可把舊path目的地回寫gridX/Y。這證明舊路徑覆寫的機制，沒有冒稱已對第一次失敗連續觀察state8。

private begin_transfer新增預設true的reuse_same_scene參數，僅28筆registered wilderness呼叫傳false；其SC61不設bit16，讓原client執行完整reset。既有town同圖reuse、owner receipt、ring0與持久化CAS維持原規則。服務層測試另驗舊town仍設bit16；拒絕移動時可分辨sequence、step、navigation三種原因。

`server-build-v4.log`及`focused-ctest-v3.log`通過；實際Application TCP `qa-tcp-transfers-v3.json`再驗野外往返、prefix、clear bit16、防反彈及三間新房往返通過。第二次部署二進位SHA-256為 `d5c9663fcf0a471e360200e8e43b5c15562add502d897cdf2403e904b87c1f23`，正式設定與DB路徑沿用。第一次失敗部署收據另外保留，沒有抹掉失敗。

以上為第二次部署當時的狀態；後續原版驗收與98筆版本結果如下。全地圖完成度仍未知。

## 原版往返通過及98筆最終同圖版本

完整reset版本在原版台服遊戲完成 `384,275 → 407,256` 與反向，抵達後繼續走動也正常。普通OS唯讀記憶體快照觀察到落點的motion、path index、path count均為0，另有原版畫面與服務端正常移動／receipt紀錄。這不是Frida hook。證據為 `native-full-reset-wilderness-acceptance.json`、`.log` 及 `native-full-reset-south-384-275.png`。

使用者自行進出房間並確認「都可以進入」；服務端另外記錄 `2/4 ↔ 2/12`、`2/4 ↔ 2/22` 的完整來回。`native-town-room-acceptance.json` 區分使用者確認與實際捕捉範圍：scene10及全部32個門點未逐一原版走訪。

Island03原版4126個placement的anchor唯一性、完整導航窗口與互反marker另經稽核。35對合格slot0增加70條方向連線，slot1缺少marker而未啟用。產品C++／Lua現共 **98條方向、49組座標對**，其中Island01保留28條、Island03新增70條；僅限原本已啟用的 `2/0`、`4/0`。這仍不是跨MDL入口的完成數。

`server-build-v5.log`、`focused-ctest-v4.log`通過，服務測試驗證全部98 tuple。上一層 `qa-tcp-transfers-v4.json` 以私有QA合成人物實際TCP驗證兩區各一組往返、批次入口前綴、舊場景尾步捨棄、full-reset bit16清除、防反彈及落點後走動；三間新房各首組門點也保留往返QA。沒有編輯正式角色資料。

使用者停手後，原版角色正常離線且服務端無Established連線，16:52切換98筆版本。二進位SHA-256為 `8d4de459b93dcea432d4b1b033cc8761447b25acb29cfbb95751fbaf4069640c`，正式設定、DB路徑及schema保留。部署收據在 `artifacts/releases/map-transfer-repair-20261018/deployment.json`。原版遊戲只驗到area2的一組野外往返；area4與其餘點仍未逐一原版驗收。

## 碧遊宮與洞穴的新增回報

98筆切換期間，使用者另回報碧遊宮無法進入，並要求檢查洞穴。原版碧遊宮是獨立 `area2/scene43/kind3`，不是同scene0傳送。當前白名單缺少其導航、入口、receipt及重新登入恢復流程，因此不能以98條同圖傳送已通過來宣稱此缺口完成。已另行核對跨MDL互反anchor與原版地圖selector；在完整來源與驗收完成前，此項保持未完成。

### 跨MDL來源與固定規則：CUSTOM-0154

現用台版EXE逐位元組核對的REA證據確認：scene43的CAN selector25指向原始 `02maze05\maze05.mdt`，沒有室內三門的selector錯配。SC61 kind3經 `46C520 → 444B80` 正常載入MDT，X/Y直接取自封包；`444F70`讀取64-byte CAN records與WORD selectors。證據在外部 `new-cross-map/cross-map-native-findings-v1.json`、`cross-loader-current-tw-rea-v1.json` 與逐頁來源pin。

最終資源 `resources/world/tw/cross-map-v4.json` 為15,846,423B，SHA-256 `ab8364ffb02a762383f9becd4721bad85673c4b8f49b3da42e042b17ad819b57`。僅新增 `2/43`碧遊宮、`2/2`地烈黑洞、`2/32`化血黑洞、`2/108`金光黑洞四個kind3場景，1,968個導航窗口全部以既有C++與離線解析結果逐窗核對。48個精確方向包含碧遊宮北／西／南三側42條及三洞穴各雙向，原42條未改動。

跨MDL採原始互反attached-reference record、source marker0/1為trigger、reverse marker2/3為arrival。此選擇與歷史碧遊宮封包參考相符，但**是CUSTOM-0154服務端政策**；客戶端448980 helper本身仍是同slot查詢，不能冒稱官方服務端規則已恢復。完整tuple、原始MDL／record offset／hash與導航資格均保存在資源與外部receipt。

地烈有兩項明列差異：其目標anchor64/69同時有裝飾model15和attached出口model47，原生442990只按X/Y首命中，鏈順序尚未恢復。本固定服務端連線明確選擇唯一互反attached record47，不使用該模糊查詢結果；SC61直接指定已驗證落點。另兩個trigger `2/0:394,96`、`2/2:60,77` 在九個窗口均非零，但有01/02差異。現版只對這兩格啟用明確nonzero例外，且須載入整份釘選bundle；其他衝突、00、未知及未載bundle仍拒絕。現台版502BF0／502F20的選定步行consumer只拒00，但5035B0仍另有CMP2，故沒有全域等同01/02。原始bytes與SHA在 `new-cross-map/navigation-nonzero-byte-check-v1.json`。

核心補上kind3導航、C++與Lua精確tuple、入口批次前綴、full SC61 reset、pending／owner receipt、進出後peer kind、存檔位置重新登入恢復。功能須明確設定 `development.diagnostic_town.diagnostic_cross_map_navigation`，預設空且須完整Island路由與consensus條件。對registered wilderness與cross-map的完整reset另清除顯示場景cache，抵達receipt後重新投影已有實際NPC／怪物資料；不憑空生成缺少的NPC。

本次修復的範圍是上述四圖與鴻濛境的進出連線。碧遊宮內另有94筆同MDL參照（47對候選）與71筆HMD室內附件；金光黑洞另有一筆HMD附件。這些未因48條入口而取得新的啟用資格；其他區域洞穴也未一併宣稱正常。

### v4集中驗證與內部黑箱切換

`cross-build-v2.log` Release建置與 `cross-ctest-v2.log` 四項focused suites全部通過，包括全部48 routes、98舊同圖tuple、Config gating、kind3／peer／重登與窄例外回歸。外部 `qa-tcp-transfers-v7.json` 透過實際Application TCP測完 **24組往返、恰好全部48條不同方向**：每組驗prefix ACK、full-reset SC61、持久化revision、arrival no-op、抵達後走動、斷線後2A kind3／位置恢復、返回及返回後走動。合成人物僅位於既有私有QA快照，正式DB未由測試腳本開啟或寫入。

黑箱helper v5曾錯把2A的appearance offset13當kind，保留失敗收據；依RecoveredWorldEntryView修正為packed position offset29後，v6抽樣6組通過，v7完整24組通過。這是測試腳本修正，沒有放寬服務端條件。新helper皆先AST解析後單次執行，未加入專案Python。

17:10前後切換v4核心，SHA-256 `93f8a1c8d4a11716df91956c22fd992f9fe2ac0e394241be2587719483ab0ec4`，正式DB路徑／schema保留。使用者指定改用內部黑箱自測，因此此批不宣稱新的原版UI驗收。中間資源v1/v2/v3共45,944,341B移至桌面「要刪除清理/God2-cross-map-intermediate-20261018」待手動刪除；搬移實際回收0B。

同輪正式static packet report為已保留的round452單次成功紀錄，未重跑；其執行時間早於本節跨MDL整合，不能用其舊快照宣稱後續全世界封包已完成。

### 最新範圍：全遊戲地圖與NPC傳送

使用者進一步要求全遊戲所有傳送點與NPC對話傳送全部串接，並指定內部黑箱。此要求超出本節四張地圖，工作持續進行。初始全量來源索引含613個CAN SceneKeys／303個unique assets；存在別名、缺檔、kind join及HMD return binding缺口，不能把613當613已可用地圖。NPC客戶端只提供對話文字與wire contract，尚未找到完整NPC instance→menu→arrival／任務條件的原服務端定義；使用者已確認只有目前這些客戶端與服務端檔案。後續以實際可還原來源完成串接，未證明項目維持明列缺口，不把文字ID當NPC ID或把條件未知當無條件。

全世界後續結果另見 [台版全地圖與NPC傳送串接](tw-world-transfers-20261018.md)：587個有導航場景、2399條固定步行傳送、363組室內進出綁定，以及26個缺原資源selector／NPC事件條件缺口。這份舊文的98／48為歷史階段結果，最新建置、全量TCP與部署狀態以新文件及其對應收據為準。
