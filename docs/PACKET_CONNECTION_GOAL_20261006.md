# GOD2 完整雙向封包串接目標

2026-10-07數值補充：金錢、經驗值、傷害與HP須能突破約21億。使用者
確認只需數值擴充，不需整支EXE移植x64作前置條件。逐欄處理儲存、計算、
wire與顯示的完整鏈路，來源及計畫見docs/NUMERIC_EXTENSION_20261007.md；
原生格式與自有擴充分開版本，不截斷大值。第一階段禁止執行/部署仍適用。

本輪20261007-web-native-ingress：新增4份transport/plan來源，Application
接入明確web opt-in與actual native endpoint registry，完成四條路徑的條件式
轉送、Origin/限額/逾時、binary fragmentation及背壓來源。普通main未啟用，
完整native玩法新增0、部署/建置/執行/測試0；界線見research/web-native-ingress-20261007.md。

## 2026-10-07 最新補充：服務端支援既有網頁客戶端

使用者要求與 chat「打包高清角色圖與 UI」交接，該 chat 專心完成現有
網頁客戶端，本 chat 負責服務端支援與正式來源整合；交接雙方確認後回報。
以下是原 TW/CN 全遊戲目標的增補，不撤銷原生 PC 客戶端支援。

網頁採四個 WebSocket 路徑承載原生二進位 byte stream：`/tw/native`、
`/tw/native-game`、`/cn/native`、`/cn/native-game`。既有 native Session
完成認證與遊戲處理，共用帳號、角色、存檔、Lua、單一權威世界與結算。
不另做玩法服務端或網頁專用遊戲資料表；未知 CN 功能繼續原生逆向。
TW/CN wire 協定與 zh-Hant/zh-Hans 顯示偏好獨立，四種組合都納入範圍；
保留聊天原文與 sender/名字/帳密/控制欄位身分，不因顯示語言切換協定。

| 里程碑 | 新增網頁整合工作與完成条件 |
|---|---|
| M1 | 對齊現有前端 native-wire/CN wire/login 契約，分開記錄 WS byte stream、TW/CN native phase/state/variant；網頁視圖或 tunnel 不充當已接通玩法。 |
| M2 | 四路徑 gateway 與同一 Application native L/G listeners 共用生命周期；實際原生端點/版本/角色及帳號入場來源明確，Origin、binary fragments、半包/合包、關閉、背壓均接入來源。 |
| M3 | 同一權威世界服務 PC 與網頁收件者；實際已接 gameplay、session/actor 世代、文字原文/呈現與跨前端互動保留，無另一套結算/資料庫。 |
| M4 | 全來源路徑完成後集中測試 PC TW/CN、WEB TW/CN、四個協定/簡繁組合、多前端互動與 native wire framing/重連/儲存。 |
| M5 | 全面修復回歸、可恢復遷移與正式 gateway/native hosting、最終可玩驗收后發布；兩版 PC 與網頁全部要求完成才結束目標。 |

雙方來源契約、端點現讀界線與交接內容：
`docs/WEB_CLIENT_SERVER_INTEGRATION_20261007.md`。
增補後目標全文與原 active goal snapshot：
`artifacts/continuation/goal-tw-cn-web-20261007/objective-amended.txt`。
目前 goal API 僅支援狀態變更，沒有 active objective 修改入口；原模式保持
active，未冒稱完成/重設用量。此最新使用者補充與 AGENTS 規則持續適用。
第一階段仍不建置、不測試、不執行/重啟服務、不部署或讀寫正式 DB。
雙方交接已確認；網頁端沿用原生PC素材、布局、操作及動作節奏。
服務端同時承接防改包要求：身份/owner/phase/玩法權威驗證、原生語義下
的重複提交/重放處理、連線/輸入限額、背壓、Origin與正式WSS/TLS。
保留PC wire相容；安全要求目前列入來源工作及最終集中驗證範圍。


本輪 `20261006-cn-outdoor-camera-trigger`：新增2份C++來源，將原生菱形
畫面投影、viewport四角與九格可見旗標、-19／40切換條件接到同一cache
identity／generation。原生.map座標是A0..Z9的字母／數字軸碼，非十進位；
檔名由真正owner prefix與原生格式組成。只準備切換請求及「實際成功後」
畫面偏移，尚不套用camera或假定00470C90資源切換成功。真正actor／world
authority、資源替換、儲存與廣播仍缺；新增opcode／階段關聯0、完整路徑0，
全遊戲分母與百分比未知。證據cn-outdoor-camera-trigger-01；未建置、執行、
測試、部署或正式DB讀寫，原生字體與繁簡轉換保持。

本輪 `20261006-cn-outdoor-cache-lifecycle`：新增4份C++來源，保留解碼後的
MDT／MDL／ROM／MBD，供同一初始角色場景的九塊快取使用。接入0046C830
的完整九塊分支：MBD gate先於MDT clamp、X先於Y旋轉、失效塊重載、
有效塊重用及原生有序遮罩格網重算；候選以同一cache instance／generation
提交。這是內部來源增量，尚未接實際WorldOwner／位置與廣播交易。
另保存0046CE10／00470C90原生資料：普通camera觸發與.map資源切換不可
由2E座標除21代替。缺失載入、動態frame／物件、camera／.map、移動權限
速度序列及5D仍待接。新增opcode／階段關聯0、完整路徑0；全遊戲百分比null。
證據cn-outdoor-cache-lifecycle-01；未建置、測試、執行、讀寫正式DB或部署，
繁簡轉換、原生字體、聊天／IME與存檔保持。

本輪 `20261006-cn-initial-scene-provider`（M2／M3來源增量）：匯入18份陸服
原生資源來源並新增SharedInitialScene兩份來源；CAN／HMD與MDT／MDL／ROM／MBD
供應真正初始格網。一般世界選角02／2A前必須有同帳號、角色、租約世代、
位置及完整2A的場景快照，ready須同一presence；初始移動可取得這份格網，
存檔位置或場景revision改變後必須由真正live owner接手，不重用初始視窗。
保留選中資源路徑，不冒稱為資源內容雜湊；轉服／恢復／61、模式1／3、
live輪替、權限／速度／序列／5D及跨版廣播／Application仍缺。
原生證據與來源保存在cn-initial-scene-provider-01；新增opcode／階段關聯0、
完整雙向路徑0；全遊戲分母及百分比未知。本輪未執行資源載入、建置、測試、
Lua、client/server、部署或正式DB讀寫；原生字體、繁簡轉換與存檔維持。

本輪 `20261006-dual-client-endpoint-catalog`（M1）：建立雙版本可追查入口索引
`artifacts/integration/packet-connections-20261006/dual-client-route-catalog-02`。
958列為方向/階段/opcode索引位置，含預設分派和未明階段，絕非958種功能或完整路徑。
連到28組限定來源分支、146份來源檔雜湊、CN6個未掛載的階段/封包來源關聯；
14個CN條件接收上下文另外保留（12已有階段線索，47DE70/4812B0仍未明）。
CN280個分派分支原文已一併小範圍快照，輸入具原路徑與SHA256。
TW原生151候選以外，解析器另有2C/2D/6F/99/A9五值；索引收錄但不假稱新增原生封包。
下輪優先追這五個TW producer與兩個CN接收helper，逐步關閉方向/階段缺口。
本輪新完整路徑0，全遊戲分母未知；未建置、測試、執行或部署。

本輪 `20261006-cn-6d-state-ownership`（M1）：保存23份原生函式快照，
定位8個繪製狀態欄位寫入函式，連上owner+1b938與parent+a69f28的別名。
S2C36自有角色分支切換renderer狀態；S2CDA自有角色分支進5385F0刷新。
S2C4A旗標02/04/08依序提前返回；其餘路徑才可能依刷新前狀態發送6D。
記錄在 `artifacts/integration/packet-connections-20261006/cn-6d-state-ownership-01`。
這是原生客戶端狀態關係，非服務端6D回覆契約、怪物屬性或可玩功能。
新增opcode0、來源完整路徑0；完整分母未知。下一步擴充路徑總表並續追31/68
及6D權威回覆缺口；未建置、執行、測試或部署。

本輪 `20261006-cn-wrapper-state-relations`（M1）：延續既有10個CN producer
入口，補讀剩餘3個局部發送條件（共10），上游呼叫圖邊21→24。新釐清S2C3C/41
條件觸發C2S6D；另定位S2C4A即時/延後刷新至5385F0後的6D條件，不能反推
原服務端6D→4A回覆契約。4D21C0的真正owner為4D1E70 selector1/index9。
4EFD60直接相對/絕對指標掃描0個候選，間接/映射入口與落入仍未排除。
資料見 `artifacts/integration/packet-connections-20261006/cn-wrapper-route-frontier-05`。
本輪opcode新增0、完整雙向路徑新增0；全部局部條件已讀不代表全部上游路徑已恢復。
下一步追536A10 consumer、5385F0提前返回分支與+a69f4c欄位寫入/所有權。
未建置、執行、測試或部署；原生字型還原與繁簡轉換保留規則持續適用。

2026-10-06 最新外觀指示：微軟正黑體／微軟雅黑已還原原生字型呼叫。
CUSTOM-0055停用；保留繁簡文字轉換。此次僅字型還原獲授權，封包第一階段
仍不建置/執行/測試/部署服務端。詳見 artifacts/releases/native-font-restore-20261006/restoration.json。
使用者再次明確要求：轉換肯定要保留，轉換與字體分開。原生字體還原
不影響繁簡字詞呈現、UTF-8原文或CP950/CP936邊界；後續不得因字體還原停用轉換。

本輪 `20261006-cn-world-selection-owner`（M2條件式來源）：新增原生1A輸入、
02狀態視圖與世界選角控制器，以已認證世界ticket、共用offer ID及現查角色歸屬
選角；02完整23 bytes必須先於2A完整37 bytes，兩筆可同一transport aggregate。
转服及一般重連1A可保留較早的帳密字串，world00則來自更新後record/cache；
不強制兩者prefix相同，改要求此次認證來源的明確字串快照投影，不改密碼驗證。
保留兩份agent原生證據及先前帳本，沒有補造未知回覆。Native1F/alias供應器、
真正世界actor/storage/rules、1C後續dispatcher與Application掛載仍缺，新增完整路徑0。
TW C2S候選含補充156、WORLD解析63/限定来源42；S2C長度252/世界非預設206。
CN C2S156、S2C階段280（account6/world206/battle68）；未掛載來源關聯21，
按方向/階段/opcode去重15，共5條局部owner鏈；這些不是完整玩法分子。
全遊戲分母及完成百分比仍未知，未建置、執行、測試、部署或改正式資料庫。

本輪 `20261006-cn-world-entry-projections`（M2來源增量）：一般1A使用07槽位，
轉服1A使用07保留列序號對應的1F槽位；新增受限資料建構，要求相同grant來源的
完整原生07/1F與共用角色ID，拒絕模糊重複槽及尚無權威映射的clamp-to0變體。
來源保留一般／轉服路徑標記，不以07/1F槽位相等推定角色身份。

以原生TW/CN資源逐列證明144筆地圖鍵／類別／原始MDT路徑一致，來源改讀
既有共用NativeMapCatalog，逐筆核對原始SQL row bytes、source/ordinal/hash
與已準備位置，才可排入02/2A。CN沒有新增地圖玩法表或匯入獨立DB。
資料證據 `shared-scene-identity-01` 使用verified=true封存精確719032-byte原生
台服輸入，沒有恢復歷史客戶端樹；目前安裝的EF297A84資源仍保留，其144筆
地圖原始列與原生基準逐筆相同。不同完整資源雜湊分開保存，未更新舊基準。

新增2A外觀／方向／mount／renderer selector唯讀字段。CF僅套用handle與
payload24..31地圖資料；同地圖+bit16時依48EF40清除重疊x高bit，須提供舊owner
位置，不能套到一般初次2A。8..11、20..23、26..27及dword0 bits26..30仍opaque，
完整資料值／原生02/2A issuer、世界actor/出生點/scene-mode/rollback、1C與CF
1F/23後續、Application正式掛載均缺；native consumer不是這些authority的替身。
新增完整路徑0、opcode值0；未掛載來源關聯仍21／去重15／局部owner鏈5，
来源檔雜湊161。TW C2S156／WORLD parser63限定來源42；S2C252／世界非預設206。
CN C2S156／S2C階段280（6/206/68）。20項2A字段分段不是20個封包變體，
144地圖對照不是已完成地圖玩法。全遊戲分母及百分比仍未知；未建置、測試、
執行、部署或讀寫正式DB。繁簡／CP950/CP936轉換及原生字體持續保留。

## 2026-10-06 重新啟動的執行方案（最高優先）

依使用者「重新定規劃好方案再採用目標模式進行工作」重新建立執行里程碑。
承接下方整合規則、來源及歷史進度，不將目標重設計為工作完成。
新目標原文：`artifacts/continuation/goal-tw-cn-replan-20261006/objective.txt`。

| 里程碑 | 工作與交付 | 完成條件 |
|---|---|---|
| M1 原生路徑總表 | 每版/方向/連線階段/opcode/變體/狀態、producer/consumer位置、觸發條件、回覆或推播關係、缺口；追間接及延後分派 | 兩版盤點邊界封閉、變體去重、完整分母可解釋；未證配對留空，不以數量湊分母 |
| M2 雙前端與共用入口 | 明確TW/CN入口、同一遊戲executor/帳號角色權威、原生成功回覆、lease/checkkey、選服選角與世界入口 | 每版入口完整接入Application，權限/生命週期/原生回覆均有正式來源；拒絕或未掛載片段不算完成 |
| M3 全遊戲來源串接 | 世界/移動/聊天/社交→物品/裝備/交易/任務/內容→戰鬥/技能/怪物/寵物/公會同盟/城鎮室內→總表其餘路徑 | 所有範圍內路徑經權威狀態/儲存/Lua/按收件者回包；包含推播、重登、取消與斷線，無空處理或猜測成功 |
| M4 集中全面驗證 | 才開始建置、雙版客戶端、跨版交易/組隊/戰鬥/聊天、儲存重登、Windows/字碼/用字、凍結功能及錯誤恢復 | 保留原始結果和缺陷清單；不可把靜態來源完成当客戶端通過 |
| M5 修復與發布 | 依缺陷修復、全面回歸、備份/可恢復遷移、正式來源與當前狀態再讀、最終原生驗收後發布 | 兩版實際可玩、保存資料、發布可恢復；所有必要工作完成才結束目標 |

目前执行M1：先延續CN round41的31/68/6D上游條件/consumer關聯。
每輪至少留下具體原生恢復或來源串接增量與下一個可追查位置，不循環只寫計畫。
M1至M3不建置、不執行遊戲、不測試、不部署；靜態讀取/逆向/雜湊/盤點可進行。
第一輪已保存10個既有producer入口、21條上游呼叫圖邊，細讀7個入口條件、3個待追。
新辨識004EFD60為未被functions.tsv列出的指令入口；WORLD S2C3B經004C2B30
在條件成立時發送C2S6D，這是客戶端接收觸發關係，未證明服務端回覆配對。
完整路徑新增0、opcode新增0；腳本前兩次不完整擷取保留標記，由03完成輸出接替。
第一輪路徑研究保存在 `artifacts/integration/packet-connections-20261006/cn-wrapper-route-frontier-03`。
共用表優先、專屬表 `_tw`/`_cn`、CN全原生、文字政策與凍結要求繼續適用。

## 2026-10-06：陸服任務目標完整承接（目前有效）

依使用者指定，承接 chat「新增繁體 Windows 語系支援」
（`01a10f6c-933d-7d61-af57-cae96503fff1`）的目標、後續補充與 round41 待辦。
原任務於使用者要求「先停止工作」後保持 paused；本次只在此 chat 整合接續。
原目標與本 chat 舊目標原文、使用量，以及13份原CN文件/帳本的雜湊快照保留於
`artifacts/continuation/goal-tw-cn-20261006`。新目標透過官方 goal API 更新；
新 objective 的用量由API重新計算，舊目標未被宣告完成，歷史紀錄保留。

| 原陸服目標／待辦 | 整合後安排 |
|---|---|
| CN專用獨立服務端、獨立資料庫、不得混用TW | 由最新指示取代：同一服務端/權威核心，TW與CN協定分離，資料表預設共用；僅已證儲存不相容才用 `_tw`/`_cn` 後綴。原CN庫不直接匯入。 |
| 全部原生、全遊戲雙向路徑 | 承接；CN不使用自創opcode、/lang、猜測回包或替代玩法；TW CUSTOM不當CN原生證据。 |
| 先確認全遊戲總數 | 提升為目前第一項工作：追間接producer、wrapper31/68/6D、phase/state/variant、共用與延後分派，建立雙版路徑身分，避免opcode/呼叫點重複計數。 |
| transport/account/角色來源 | 復用既有固定雜湊來源；完成Application接入、1D/06/0A成功欄位、lease/checkkey、1F角色列表、建立/刪除/選角與world transfer。現有credential片段未構成完整登入。 |
| world/map/scene/movement/室內外資源 | 承接既有scene、house、terrain、chunk、座標、model/ROM/MDT等證據及未完成狀態配對，再接共同世界；資源數不算已完成地圖。 |
| chat/繁簡字詞/Windows相容 | UTF-8原文、CP936/CP950邊界、逐收件者呈現；正確詞組而非區域用詞替換，保留正確繁體與帳密/控制欄位。已有繁體Windows登入回報是客戶端相容成果，不是新服務端驗收。 |
| battle/技能/延後事件 | 承接C2S35、S2C83/86/89、F2輸入與回饋、ownership/indirect缺口；同一場戰鬥只作一次權威結算，再分版本呈現。 |
| 原生服務端資料缺失/舊三份zip參考 | 原CN使用者明示沒有原始服務端/表/封包紀錄；20260820三份未完成zip僅搜尋線索。未知規則繼續逆向，不填猜測值。 |
| 階段與保留要求 | 先來源全串接；後集中雙版/混合互動建置測試；再全面修復回歸發布。保持凍結功能及現有帳號存檔。 |
| 每輪完成度 | 分版本列C2S/S2C、分支、增量、缺口及完整路徑/總數；總數未知則百分比null，來源/部署/驗收分開。 |

CN基準承接round41：已觀察C2S opcode值156；S2C階段/opcode280
（account6/world206/battle68）；長度支援253（固定231/可變22）；完整双向遊戲路徑0。
TW保留既有151個C2S候選、63個WORLD解析opcode、42個已盤點特定來源分支opcode，
252個S2C支援長度opcode、43個來源回覆opcode。兩版全遊戲分母均未知，不能相加算總數。
本次僅目標與工作契約整合，新增完整路徑0；未建置、測試、執行客戶端或部署。

### 合併後的目標模式全文

完成同一套 GOD2 C++20／Asio／Lua 5.4/sol2／SQLite／spdlog／JSON 服務端，完整同時支援台服 TW 與目前固定雜湊的陸服 CN 原生客戶端；承接「新增繁體 Windows 語系支援」chat（01a10f6c-933d-7d61-af57-cae96503fff1）的全部適用目標、原生證據、來源成果與未完成工作，整合至 C:/Users/risei/Desktop/God2/God2-Server。原 CN 專案 C:/Users/risei/Desktop/God2-xjz/God2-Server-CN 保留作可追溯來源，原任務保持暫停；不重啟兩套競爭服務。

最高優先為整個遊戲的完整雙向封包串接。先釐清兩版全遊戲路徑總數：逐版本、C2S/S2C、連線階段、狀態、子型別與變體追完 producer/consumer、間接與延後分派；opcode、呼叫點及長度表不能充當功能分母。將每條原生請求→C++20傳輸/輸入驗證/權限/狀態/交易/儲存→Lua規則→原生S2C→對應客戶端接收完整接入正式來源，涵蓋登入、選服、角色、世界、移動、聊天、物品、任務、組隊、公會/同盟、城鎮/室內戰鬥、怪物/技能及全遊戲其餘功能，完成TW/CN玩家共用世界與跨版本互動。

採單一權威遊戲核心及版本專屬編解碼/呈現，每個Session固定協定，按收件者版本回包。兩版遊戲內容相同，帳號、角色、怪物、技能、道具、任務、地圖、經濟等資料表預設共用；線路差異優先由適配器處理。只有具體證明無法共用的儲存才拆表，表名用 _tw／_cn 後綴，禁止 tw_／cn_ 前綴；保留舊表名、ID與存檔，不直接匯入獨立CN資料庫。此整合要求取代舊CN任務的獨立服務端/僅支援CN/獨立資料庫限制。

CN全部功能依當前原生格式、狀態與規則，不自創opcode、聊天命令、UI、猜測回覆或替代玩法；證據不足持續逆向。TW既有CUSTOM保留標籤，不作CN原生證據；共用戰鬥/經濟只結算一次，不因客戶端版本產生不同權威結果。20260820舊Classic/C++/C#未完成服務端僅為線索，不能作當前原生權威。

承接繁體/簡體Windows支援及逐收件者正確繁簡呈現：內部UTF-8、明確CP936/CP950邊界，Windows語系、客戶端版本、wire編碼與玩家偏好分開；不憑chat語系bit認定版本。整套字詞庫/遊戲文字處理一對多字義及詞組，保留正確繁體，不限使用者示例，不做兩岸用詞替換；原文與呈現分開，帳密/識別/名字匹配/控制欄位不任意轉換，沿用原生文字入口，不自創/lang，不宣稱歧義文字百分百判對。

第一階段只做靜態原生恢復、盤點與全部來源串接，不建置、執行、逐項測試、驗收、測試式驗證或部署；第二階段在全部遊戲路徑串接後集中建置及全面TW/CN與混合互動測試/驗證；第三階段全面修復、回歸，再發布可遊玩結果。保留帳號、存檔、聊天、IME、認證、頭像、客戶端及凍結功能；不把空處理器、任意成功、僅解析、拒絕路徑或未接入來源當完成。

沿用兩版已釘定證據與路徑帳本，不重做既有成果、不覆寫歷史基準。每輪回報分版本方向/階段/opcode/變體數、實際接通分支、本輪增量、缺口及完整雙向路徑/全遊戲總數；原生覆蓋、來源串接、部署、原生客戶端驗收分開。分母未確認就報未知、百分比null。持續至兩版全遊戲完整串接、集中驗證修復及可遊玩發布實際完成。

Continued round `20261006-cn-shared-account-segment`: imported8 pinned CN
transport/account source files under src/cn, added a raw-UI Account04/World00
credential ingress to the existing shared AccountRepository/PasswordHash,
and retained required real admission continuation before stream release.
This is an unhosted source segment: full native account success, directory,
character admission and Application listener remain pending. No complete
gameplay route added, build/test/client execution/database mutation/deployment0.
Owner requires shared tables wherever semantics permit; incompatible new tables
use _tw/_cn suffixes (owner correction), preserving legacy saves and table names. See
`DUAL_CLIENT_PROTOCOL_GOAL_20261006.md` for source and schema boundaries.

2026-10-06 新增使用者要求：同一正式服務端須同時接台服與獨立陸服客戶端。兩版封包必須分版本、方向、狀態與變體盤點和串接；語系切換不算陸服協定驗收。實作邊界、目前缺少的陸服版本輸入和下一步見 `DUAL_CLIENT_PROTOCOL_GOAL_20261006.md`。目前陸服已證來源路徑 0、完整分母未知；此項不改寫下列台服既有計數。

Continued round `20261006-owned-player-vitals-source-pushes`: registered
existing conditional first-WORLD-tick saved S2C22 role and S2C24 vitals
pushes. S2C22 remains separately registered as a C2S21 allocation reply;
its restored-snapshot branch is another source class, not a new reply opcode.
C2S candidates 151; WORLD parser 63/reviewed scoped branches 42 (limited
66.7%), gameplay gaps 11/pending groups 10. S2C lengths 252/nondefault 206,
registered replies 43, source pushes 8 (+2), unclassified 124 (-1).
No new runtime route, build, tests, client run or deployment. Whole-game
percentage unknown. See
`docs/research/current-saved-role-journal-s2c-pushes-20261006.md`.

Continued round `20261006-owned-role-journal-source-pushes`: registered two
existing first-WORLD-tick saved-state pushes: S2C2C raw 61-byte owned role
auxiliary snapshot and S2CDB fifteen subtype4 journal records, each emitted
only when its owner-bound saved snapshot exists. Native consumers and source
conditions are scoped; neither proves monster stats, quest gameplay, or a new
C2S reply. C2S candidates 151; WORLD parser 63/reviewed scoped branches 42
(limited 66.7%), gameplay gaps 11/pending groups 10. S2C supported lengths
252/nondefault 206, registered reply opcodes 43, source push opcodes 6 (+2),
unclassified 125 (-2). Whole-game percentage unknown. No build, tests,
client execution or deployment. See
`docs/research/current-saved-role-journal-s2c-pushes-20261006.md`.

Continued round `20261006-owned-map68-custom-source`: source-connected one
bounded CUSTOM-0087 C2S68 00 owned regional-map display branch to native
S2C3F 01 00. The server checks completed WORLD, saved region, actual saved
owned bag/source and map row before returning the panel opener; no item or
saved-state mutation. Native producer/consumer are independently proven,
but the original server 68->3F causal pairing remains unproven, so other 68
contexts remain pending. C2S candidates 151; WORLD parser 63/reviewed scoped
source branches 42 (+1, limited 66.7%), reviewed groups 18, gameplay gaps
11 (-1)/pending groups 10. S2C supported lengths 252/nondefault 206,
registered reply opcodes 43 (unchanged), unclassified 127 (unchanged).
Whole-game completion unknown. No build, tests, client run or deployment.
See `docs/research/current-owned-map68-route-20261006.md`; the latest static
source accounting is `round-reports/20261006-owned-map68-final-source.json`.

Continued round `20261006-existing-pet-clock-appearance-joins`: registered
existing scoped C2S28 owned-pet selection source replies E3/FB (plus already
counted 3B/41), configured S2C1A world-clock push, and configured S2CDA
appearance push. These source branches already existed; this round corrected
their directional inventory, with no new client acceptance or deployment.
C2S candidates 151; WORLD parser 63/reviewed scoped source branches 41
(limited 65.1%), reviewed groups 18 (+1), gameplay gaps 12/pending groups 10.
S2C supported lengths 252/nondefault 206, registered reply opcodes 43 (+2),
source pushes 4 (+1), configured visibility pushes 4 (+1), independent
format-only 9, unclassified 127 (-4). New complete routes this round 0;
whole-game percentage unknown. No build, tests, client run, activation or
deployment. See `docs/research/current-existing-s2c-source-joins-20261006.md`.

Continued round `20261006-s2c4d-beast-delta-classification`: native S2C4D
fixed logical9 consumer and its source codec were already pinned; this round
registered that independent receive format in the directional ledger. Its
physical target slot is distinct from C2S6B's dragged food slot. No original
server issuer or 6B-to-4D causality is proved, so new complete routes 0. C2S
candidates 151; WORLD parser 63/reviewed scoped source branches 41 (limited
65.1%), gaps 12/pending groups 10. S2C supported lengths 252/nondefault 206,
independent format-only 9 (+1), unclassified 131 (-1). Whole-game percentage
unknown. No build, tests, client run, activation or deployment. See
`docs/research/current-companion-control6b-20261006.md`.

Continued round `20261006-6b-food-pfd-readset`: recovered all 65 exact PFD
declarations from the archived current-client source and matched their row bytes
to the present asset. Native lane0 prequeue code confirms a local dragged-slot
and UI gate, not server food authority. A source-stage readset now captures the
whole owned bag and selected beast in one SQLite read transaction, joining the
request selector, target custody and PFD source key; it is deliberately unwired
and grants no food effect. Special PFD transformation rows make declaration
membership insufficient for consumption. New complete routes 0. C2S candidates
151; WORLD parser 63/reviewed scoped branches 41 (limited 65.1%), gaps 12 and
pending groups 10; S2C supported lengths 252/nondefault 206/independent
format-only 8/unclassified 132. All count deltas 0; whole-game percentage
unknown. No build, tests, client run, activation or deployment. See
`docs/research/current-companion-control6b-20261006.md`.

Continued round `20261006-6b-panel-slot-crosslink`: pinned the native C2S6B
lane0 producer and S2C4B/4C/41 consumers around the shared UI+85ABD byte.
The lane0 byte is the live panel selector; S2C41 compares it with a physical
inventory slot for panel close, but the current CUSTOM-0085 custody keeps a
separate stable selector. No food authority, effect or causal reply was added:
new complete routes 0. C2S candidates 151; WORLD parser 63/scoped reviewed
source branches 41 (limited 65.1%), gameplay gaps 12/pending groups 10; S2C
supported lengths 252/nondefault 206/independent format-only 8/unclassified
132. All count deltas 0; whole-game completion percent unknown. No build,
tests, client run, activation or deployment. See
`docs/research/current-companion-control6b-20261006.md`.

Continued round `20261006-npcboss-message-source-join`: pinned the native resource section NPCBossMessage (72 source rows, IDs 1..72) from the exact current-client message.csvZ and joined it through the native loader to the S2C 5A and NPC-mode 79 label selector. The ordinary S2C72 constructor stores a zero-extended low-WORD pool identity, which the label consumer looks up as a full DWORD. The codec now names NPCBossMessage and NPCNormalMessage selectors separately. Specific message choice, owner state and timing remain unproved; new complete routes: 0. C2S candidates 151; WORLD parser 63/scoped source branches 41 (limited 65.1%), gameplay gaps 12/pending groups 10; S2C supported lengths 252/nondefault 206/independent format-only 8/unclassified 132, all count deltas 0. Whole-game percentage unknown. No build, tests, client run, activation or deployment. See `docs/research/current-s2c-text-npc-595a5b79-20261006.md`.

Continued round `20261006-s2c-text-npc-595a5b79`: pinned four current-native fixed 9-byte WORLD S2C consumers. Opcodes 59/5B select text resource presentation; 5A updates an existing NPC pool label; 79 chooses text or NPC label by WORD logical+5 == FFFF. A read-only raw codec and bounded instruction evidence were added. No original server producer or causal C2S path is proved, so new complete routes: 0. C2S candidates 151; WORLD parser 63/scoped source branches 41 (limited 65.1%), gameplay gaps 12/pending groups 10; S2C supported lengths 252/nondefault 206/independent format-only 8 (+4)/unclassified 132 (-4). Whole-game percentage unknown. No build, tests, client run, activation or deployment. See `docs/research/current-s2c-text-npc-595a5b79-20261006.md`.

Continued round `20261006-fd12-item-key-slots`: pinned FD12 logical bytes 4..21 as nine u16 item-definition keys. The native client looks them up through 459A60 and selects 9/6/3 slot subsets for display. A read-only indexed accessor was added; original server offer authority, rewards/costs and E4 causality are still open. New complete routes: 0. C2S candidates 151; WORLD parser 63, scoped source branches 41 (65.1% of this limited set), gameplay gaps 12, pending groups 10; S2C supported lengths 252, nondefault entries 206, pending format-only 13, unclassified 136. Whole-game percentage unknown. No build, tests, client execution, activation or deployment. See `docs/research/current-fd12-e4-panel-20261006.md`.

續輪 `20261006-fd12-e4-ui-offer`：釘定原生S2C FD subtype12
是C2S E4操作介面的上游資料之一；只有FD識別碼進入
`858B0`的subtype switch，FB／FC雖呼叫同函式但不走此分支。
FD12至少消費logical26：18-byte介面前綴、模式、八位選項
遮罩及兩個按鈕旗標。新增唯讀codec與釘定證據，未推定
未知尾部、來源權威或E4請求→回覆因果。完整路徑新增0；
C2S候選151、world parser63／限定來源41（局部65.1%）、
gap12／pending10；S2C長度252／非預設206／待接格式13
（+1）／未分類136。全遊戲完成百分比仍未知；未build、
測試、client執行、啟用或部署。見
`docs/research/current-fd12-e4-panel-20261006.md`。

續輪 `20261006-e4-producer-ui-gates`：原生C2S E4
operation0／1／2各有不同UI按鈕與本地旗標門檻；
operation3走另一段複合旗標／訊息流程，掃八個旗標任一
非零才送。四筆request都只有E4+operation，不帶戰寵
slot／instance／revision；外層控制ID也不是已證戰寵身分。
因此不能將C2S0..3直接映射S2C E4 bonus0..3。
完整路徑新增0；C2S候選151、world parser63／限定
來源41（局部65.1%）、gap12／pending10，S2C長度252／
非預設206／未分類136均不變；全遊戲百分比未知。未build、
測試、client執行、啟用或部署。見
`docs/research/current-e4-c2s-producer-gates-20261006.md`。

續輪 `20261006-e4-pet1-cache-link`：釘定S2C E4 consumer
更新與E3戰寵快照相同的槽位42..44、52-byte快取列；原生
條件檢查既有metadata與slot。17-byte E4的兩個WORD更新
最大HP／MP，兩個打包DWORD更新物理／法術雙攻雙防的低
12位，另更新剩餘點數並依bonus選擇0..3增加一項四維
加點計數。純唯讀typed view已加入，未碰存檔或發送。
C2S E4也有operation0..3，但因果、目標權威與原始加點
公式未證；完整路徑新增0。C2S候選151、world parser63／
限定來源41（局部65.1%）、gap12／pending10，S2C長度252／
非預設206／未分類136均不變；全遊戲百分比未知。未build、
測試、client執行、啟用或部署。見
`docs/research/current-e4-pet1-cache-link-20261006.md`。

續輪 `20261006-npc-instance-removal-link`：重讀釘定原生
`S2C72`普通／組合 constructor，兩者皆以selector低WORD
查找並存入NPC pool identity；`S2C75`以同一WORD對相同pool
呼叫`CC990`移除。已在NPC codec與既有儲存列明確命名此
instance語意，並修正上一輪過度保守的說法。`75`動態消失
權威／時機及未讀兩bytes仍缺，runtime發送保持關閉。
本輪完整路徑新增0；C2S候選151、world parser63／限定
來源41（局部65.1%）、gap12／pending10，S2C長度252／
非預設206／未分類136均不變；全遊戲百分比未知。
未build、測試、client執行、啟用或部署。見
`docs/research/current-npc-instance-removal-link-20261006.md`。

續輪 `20261006-world-pool-removal-source-push`：原生`74`移除
怪物／跟隨寵物池，`75`移除NPC／本地標記池；兩者皆logical5，
只讀低WORD instance，剩餘bytes保留，純codec已加入但無
動態來源／發送。既有`71／72／78`場景資料推送及配置限制的
`5E／6F／73`玩家可見性推送分別入帳，不冒稱本輪新接。
S2C長度252、非預設206、既有來源推送3（新登錄）、
配置限制推送3（新登錄）、獨立格式4（+2）、未分類136（-8）；
C2S候選151、world parser63／限定來源41（局部65.1%）、
gap12、pending10不變，完整路徑新增0，全遊戲百分比未知。
未build、測試、client執行、啟用或部署。見
`docs/research/current-world-pool-removal-and-source-push-20261006.md`。

續輪 `20261006-s2c-first-hop-gm-bridge`：對前輪152個尚未分類的
WORLD S2C 非預設入口建立有界第一跳清單；145個入口在該片段
有直接call，7個沒有。`7B–81`及`F6`八個opcode共用
`6AD6D→6B9D0`，依原生長度走`GM Tools FS2`視窗訊息形狀的
外部橋接，已單列為格式證據，不算遊戲功能串接。S2C長度252、
非預設206、外部橋接8（+8）、未分類144（-8）；C2S候選151、
world parser63／限定來源41（局部65.1%）、gap12、pending10
不變；新增完整路徑0，全遊戲百分比未知。未build、測試、client
執行、啟用或部署。見
`docs/research/current-s2c-first-hop-and-gm-bridge-20261006.md`。

續輪 `20261006-c2-mode1-five-widget-gate`：補齊C2 mode1
上游`B17A2→CEDE0`完整門檻，五個UI槽位索引均須有效且
各含bit0x10，否則客戶端本地失敗不送包。此分支不讀
F5欄位，與mode2..6分開；body只明確寫入mode1，其他
bytes保留opaque。新增完整路徑0；world parser63、
限定來源41（局部65.1%）、gap12、pending10、C2S候選151、
S2C長度252／獨立格式2／未分類152均不變。全遊戲百分比
未知；未build、測試、client執行、啟用或部署。見
`docs/research/current-c2-mode1-five-widget-gate-20261006.md`。

續輪 `20261006-c2-controls-receiver-split`：原生C2S C2
logical9有三個直接queue點、模式1..6。mode1是獨立UI旗標；
mode2..6取用F5 type7/8建立的欄位，未寫入body位元組保留
opaque。已加入預設關閉的WORLD parser，Application無功能。
S2C同號C2固定3經`6B261→C2E20`刷新另一組UI，未見
讀取兩個body位元組，不假定是C2S C2回覆。新增完整路徑0。
world parser63（+1）、限定來源41（局部65.1%，分母擴大）、
gap12（+1）、pending10（+1）；C2S候選151／S2C長度252
不變，S2C獨立格式2（+1）、未分類152（-1）。全遊戲百分比
未知；未build、測試、client執行、啟用或部署。見
`docs/research/current-c2-control-bidirectional-20261006.md`。

續輪 `20261006-orange-shop-bf-money-quantity`：原生
`PMOrangeShop.cpp`兩個assert分別命名EE/F3選取列+2的u16為
`money`；UI把顯示餘額除以此欄位得最多30的選取數量。
BF OrangeShop候選body恢復為key:u16、quantity:u8(1..30)、
category:u8(1..4)、displayed money零擴充u16。已加入純
形狀解碼，但每日dialog32 BF可有相同bytes，必須靠已發
介面列表與owner區分。正式來源無OrangeShop權威商品目錄／
貨幣來源／交易／S2C結果；新增完整路徑0。world parser62／
限定來源41／gap11／pending9，C2S候選151／S2C長度252／
待接格式12／未分類153不變；全遊戲百分比未知。未build、
測試、client執行、啟用或部署。見
`docs/research/current-orange-shop-bf-money-quantity-20261006.md`。

續輪 `20261006-orange-shop-f5-ef-state`：原生 S2C EE 的
diagnostic指向`PMOrangeShop.cpp`與`ORANGESHOP_GOODS_DATA_SC`，
其三列群數量對應原式`nKindNum+nSaleNum+u8LimitNum`。S2C F5
固定29的變體7/8更新鄰近UI記錄，且可清空EE的6-byte列表；
S2C EF固定3更新BF偶數路徑使用的u16門檻，FFFF隱藏控制。
純格式codec已加入，沒有證成BF交易回覆或權威經濟來源。
新增完整路徑0；world parser62／限定來源41／gap11／pending9、
C2S候選151／S2C長度252不變；S2C非預設待接格式12（+2），
未分類153（-2）。全遊戲百分比未知；未build、測試、client
執行、啟用或部署。見
`docs/research/current-orange-shop-f5-ef-20261006.md`。

續輪 `20261006-bf-ee-f3-source-lists`：同版原生 S2C EE 可變長
`690EE→CDF90` 把三群6-byte列填入UI+96980，正是BF偶數模式
來源；S2C F3 可變長 `69112→CE290` 將壓縮列展開至
UI+96BA4的48-byte列，正是BF奇數模式來源。兩者header均為
logical9 bytes，類別1..4映射模式；純來源codec已加入，沒有
權威列表發送、交易或BF因果回覆。F5固定29與EF固定3僅改鄰近
UI狀態。新增完整路徑0；world parser62／限定來源41／gap11／
pending9，C2S候選151／S2C長度252不變，S2C非預設待接格式
由8增至10、未分類157降至155；全遊戲百分比未知。未build、
測試、client執行、啟用或部署。見
`docs/research/current-bf-ui-list-receivers-20261006.md`。

續輪 `20261006-bf-ui-row-producer-frontier`：原生 BF 的兩個面板列族
已分開：奇數模式1/3/5/7取48-byte列、立即queue `CFC87`；偶數
模式0/2/4/6取6-byte列、立即queue `CFE77`。兩者搜尋重複列後
可把body緩存在UI child+3AE48，再由共同確認queue `842E4`送出。
這三個直接queue點不是三種獨立經濟資料源；每日dialog32透過
共用queue8450B仍是第四條來源分支。兩個列族的服務端權威資料與
S2C BE/BF因果尚未證，沒有新增完整路徑。world parser62／限定
來源41／gap11／pending9、C2S候選151／S2C長度252不變，
限定分支比率66.1%，全遊戲百分比未知。未build、測試、客戶端
執行、啟用或部署。見 `docs/research/current-bf-ui-row-producers-20261006.md`。

續輪 `20261006-daily-bf-shared-queue-branch`：補到原生 BF
先前三處直接送包之外的第四條每日面板購買分支。dialog32
`8433D` 用已顯示 item WORD、固定01/01、amount DWORD組
8-byte body，跳共用queue8450B送BF；同版原始bytes另存v2。
已把此限定變體接到預設關閉的daily FD已發清單／owner／scene
比對及未解意圖紀錄；沒有扣款、發物、Lua／SQLite事務或因果
S2C，新增完整串接0。BF原生已知producer分支4（+1），
世界parser62／限定來源41／gap11／pending9、C2S候選151／
S2C長度252不變。全遊戲百分比未知；未build、測試、
client執行、啟用或部署。見
`docs/research/current-daily-bf-purchase-20261006.md`。

續輪 `20261006-d8-retained-tail-admission`：原生 D8 mode1 尾位元組
取自面板+20FEB，既有原生producer案例保留00/A5/FF；正式來源
先前強制零而誤擋合法形狀，現已移除該限制並保留已發FD清單、
NPC、位置、票券欄位綁定。mode2原生按鈕確為「每日領取」，
但沒有物品key；仍無傳送、領獎、Lua規則及原子存檔回覆。
本輪新增完整串接0，world parser62、限定來源41、gap11、
pending9（+1明列D8）、C2S候選151、S2C長度252不變；
全遊戲完成率未知。未build、測試、client執行或部署。
見 `docs/research/current-d8-retained-tail-admission-20261006.md`。

續輪 `20261006-a9-context-immediate-frontier`：釘定原生
`061E..0622` 的11處精確立即數引用，其中5處是 `F6DA0`
的 A9 選擇判別、5處是一般資源查表、1處是記憶體初始化計數。
同數值不能把傳送 context 綁到 NPC、道具或目的地。
A9 仍只有5-byte解析／callback邊界，未有原生開選單因果、
服務端權威或正式回覆；新增完整串接0。世界 parser62、限定
來源41、未接功能11、C2S候選151／S2C長度252均不變，
pending8（+1，明列 A9 缺口）；全遊戲完成率未知。
未 client 執行、build、測試或部署。見
`docs/research/current-a9-context-frontier-20261006.md`。

續輪 `20261006-c2s68-format-parser`：原生大地圖 UI 家族有四處有條件的
`961A0(68,1)` 呼叫，送出分支格式是 `68 00`，但 wrapper 仍可本地分流。
已新增精確格式 codec 和獨立預設關閉的世界 parser；Application 沒有
授權功能或回覆。S2C3F 開地圖與獨立 S2C68 更新另一 UI 列，均未證明
是此請求的回覆；新增完整串接 0。世界 parser 62（+1）、限定來源
41（+0）、未接功能 11（+1）、C2S 候選 151／S2C 長度 252 不變。
全遊戲完成率仍未知；未 client 執行、build、測試、啟用或部署。見
`docs/research/current-c2s68-parser-frontier-20261006.md`。

續輪 `20261006-s2c83-two-stage-action-frontier`：釘定原生
S2C83的01..17（十六進位）23個action選擇值，第一層
10個不同case，actor層14個不同case；完整兩層表已封存。
03與17共享兩層case地址但不可視為同一技能語義。
目前正式單體攻擊投影只限01/03；0D另有delta codec、
07為診斷效果，其他action仍需逐分支規則及因果路徑。
本輪新增完整串接0，世界parser61／限定來源41／gap10／
C2S候選151／S2C長度252不變；全遊戲完成率未知。
未client執行、build、測試或部署。見
`docs/research/current-s2c83-action-frontier-20261006.md`。

續輪 `20261006-s2c-battle-dispatch-frontier`：釘定原生戰鬥
接收switch的`1C..89`共110個索引：9個專用opcode
`1C 38 83 84 85 86 87 88 89`，其餘101在該switch走
預設；九者在WORLD表全部是預設。兩狀態專用入口聯集
206+9=215，僅為入口盤點。戰鬥86另有0..6七個子型別
選擇值／六個不同case地址。83 action等變體未全盤；
新增完整服務端路徑0，世界parser61／限定來源41／
C2S候選151／S2C長度252不變，全遊戲完成率未知。
未client執行、build、測試或部署。見
`docs/research/current-s2c-battle-dispatch-frontier-20261006.md`。

續輪 `20261006-s2c-world-consumer-frontier`：目前版原生S2C
長度表252可接收入口（230固定／22可變），其中WORLD分派
206非預設、46預設，非預設目標RVA共198個。206中41個已在
來源回覆帳本登錄、8個屬pending格式（C5與41重疊）、
1個獨立S2C68格式，餘157個尚未在此路徑帳本分類。
WORLD預設不代表戰鬥／登入等其他狀態沒有consumer；
157也不代表舊研究從未分析。新統計是同一原生表的細分，
本輪已接來源分支仍41／61，新增完整路徑0，完整遊戲
百分比未知。未client執行、build、測試或部署。
見 `docs/research/current-s2c-world-consumer-frontier-20261006.md`。

續輪 `20261006-same-opcode-31-68-receiver-split`：同版原生
S2C31固定29-byte走`69FA9→AA200`更新既有神祇列，與C2S31
的UI送出門檻無已證因果。S2C68固定13-byte走`6ABF3→9BED0`，
讀logical+3 WORD、+5 DWORD、+9/+10 BYTE並使用`UI+232DD8`；
C2S68四處caller屬大地圖`UI+232DA8`家族，S2C3F會打開地圖，
但哪個回覆哪個仍未證。未安裝猜測handler。世界parser61、
限定來源41、gap10、pending6、C2S候選151、S2C長度252、
回覆下限41與control10相對前輪均不變；全遊戲百分比未知。
未執行client、build、測試或部署。見
`docs/research/current-same-opcode-31-68-20261006.md`。

續輪 `20261006-wrapper-ui-full-gates`：補齊原生C2S31完整
`BF300..BF505` 生產者；須一個選定row的bit0x10且六個其他
row不得有bit0x08，修正前輪只看尾端三row的計數。C2S68
四個wrapper直呼各有不同UI/輸入門檻，且wrapper可能本地分流
不送包。兩者仍無正式服務端功能與因果S2C回覆，未加空handler。
本輪世界parser61、限定來源41、gap10、pending6、已知
C2S參數候選151、S2C長度252、回覆下限41、控制10差額均0；
完整遊戲百分比未知。沒有client執行、build、測試或部署。
見 `docs/research/current-wrapper-ui-gates-20261006.md`。

續輪 `20261006-candidate-frontier-spectator6e`：原生直接／已知
wrapper參數候選151中，現在56項與世界解析opcode交集，95項
在世界解析器外（混合階段／未證候選），另5項世界parser未列於
此種靜態參數掃描；這些是集合差額，非全遊戲封包完成分母。
原生C2S6E五個直接caller及9-byte body已定位：mode1四處、
mode2/context0一處，三個body位元組於producer未初始化。
S2C6E是獨立5-byte預設dispatch，回覆未證。新增原樣codec及
預設false解析；觀戰生命週期、房間授權、戰鬥投影與退出仍缺。
世界parser61（+1）、限定來源41（+0）、gap10（+1）、
pending6（+1）；C2S候選151／S2C長度252／回覆下限41／
control10不變，全遊戲完成率未知。未建置、測試或部署。
見 `docs/research/current-spectator6e-20261006.md`。

續輪 `20261006-bf-s2c-panel-chain`：同版原生S2C BE是
`5+24×count`可變長分區列表，BF是29-byte既有分區／格位更新；
`472560/472680`共用50×24格位狀態。新增BE/BF純codec和安全
發送索引界線，並封存bounded native slices。C2S BF與這兩條S2C
的交易因果、商品／貨幣／Lua／SQLite仍未證，Application不發送。
世界parser60、限定來源41、gap9、pending5、C2S候選151、
S2C長度252、回覆下限41、控制10皆無本輪數量差額；完整
遊戲百分比未知。未建置、測試或部署。見
`docs/research/current-bf-s2c-panel-20261006.md`。

續輪 `20261006-bf-bidirectional-format`：原生C2SBF有3處直接
queue caller，都是8-byte body／9-byte logical；`842E4`是暫存
對話框body確認，另外兩處依不同UI記錄構造。S2CBF的29-byte
世界consumer獨立，同號因果回覆未證。純codec及預設false世界
parser已加，Application交易／owner／Lua／SQLite／S2C授權仍缺。
世界parser60（+1）、限定來源41（+0）、gap9（+1）、pending5
（+1）；S2C長度252、C2S已知候選151、S2C回覆下限41、
控制10均不變。全遊戲完成率未知，未建置、測試或部署。
詳見 `docs/research/current-bf-bidirectional-20261006.md`。

續輪 `20261006-e4-bidirectional-format`：C2SE4四個原生
queue caller送出2-byte `E4,operation`（0..3）；S2CE4則是
獨立17-byte既有UI記錄consumer，同號因果回覆未證。
已加純雙向codec與獨立預設false世界parser，Application、
owner state、Lua規則、SQLite與S2C授權仍缺。`68A30`
入邊掃描仍無可見直接／相對／絕對參照，不宣稱35 raw候選
可達。世界parser59（+1）、限定來源41（+0）、gap8（+1）、
pending4（+1）；S2C長度252、C2S已知候選151、
S2C回覆下限41、控制10、靜態35變體候選1均不變。
全遊戲完成率未知，未建置、測試或部署。
詳見 `docs/research/current-e4-bidirectional-20261006.md`。

續輪 `20261006-c2s-wrapper-35-frontier`：`68A30` 第二分流表
把輸入1F/22/23/35映到不同C2S producer；35候選為17-byte
logical，但本地只寫body8..11=`FFFFFFFF`，其餘12 bytes
未由此函式初始化，且 `.text` 無直接E8 caller；可達性未知。
既有35戰鬥action parser不得接受它。31和68的局部UI發送門檻
已定位，真正服務端狀態、回覆仍OPEN。新增的是1個**靜態
未證可達 raw 變體候選**，不同C2S opcode聯集151不變；
世界parser58／限定來源41／S2C回覆41／控制10／gap7／
pending3亦全無變化。全遊戲完成率未知，沒有測試或部署。
詳見 `docs/research/current-c2s-wrapper-frontier-20261006.md`。

續輪 `20261006-c2s-wrapper-census`：已封存同build `.text` 中31處
`157D0/961A0`直呼、包裝器原始指令與跳表，確定原生單零位元組
候選`1F/22/23/31/68/6D`。這六個與舊145個直接queue參數
opcode不重疊，因此已知直接＋包裝器參數候選聯集151（+6），
不是全遊戲封包總數。`68`可能改走本地訊息；`22/31/68`
服務端狀態/回覆仍未恢復。本輪世界parser58、限定已接分支41、
S2C回覆下限41、控制10、gap7、pending3均未變；全遊戲
完成率仍未知。沒有測試、build、啟用或部署。參見
`docs/research/current-c2s-wrapper-census-20261006.md`。

續輪 `20261006-pet-activity9e-parser`：目前原生C2S9E的
`contextDWORD,operationBYTE,selectionBYTE`固定7-byte格式，
operation0/1與state0/2的one-based選取及operation2的zero-based
選取已定位。世界解析和Session獨立flag已加入，預設false；
Application／owner state／活動與獎勵規則／Lua／持久化／S2C因果
回覆均未接。S2CC5/C6只有顯示/狀態格式，不冒充9E業務完成。
本輪世界parser58（+1）、限定來源41（+0）、gap7（+1）、
pending3（+1）、S2C回覆下限41、控制10；41/58=70.7%僅
衡量限定世界opcode來源覆蓋，全遊戲完成率仍未知。
沒有測試、build、啟用或部署。詳見
`docs/research/current-pet-activity9e-20261006.md`。

續輪 `20261006-companion-6b-consumer-census`：同一原生 build 的
兩個C2S6B函式在PE `.text` 內有10個E8直呼caller；新定位
`97349`／`97370` 是固定selector2C的lane1／3。獨立S2C6B
為21-byte「原樣LE32既有世界pool identity＋16-byte NUL文字」，
`6AABE→4CC910→509E70`更新次級顯示文字；S2CEC另有
owner|8000隨行同伴名稱caller，不可混同。已加純S2C codec與V3
證據，但缺權威文字來源、pool建立與發包時序，C2S6B亦缺真正
持有／效果／Lua／回覆。世界解析57、限定已接分支41、S2C回覆
下限41、控制10、gap6、pending2，本輪計數差額全0；
41/57=71.9%僅為限定世界opcode來源比率，全遊戲完成率未知。
未build、測試、啟用或部署。

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

最新使用者指示：2026-10-06。此順序優先於舊文件要求的逐項測試與驗收。
目標模式已啟動；完整遊戲串接、全方位測試驗證、全面修復全部仍未完成。

## 每輪結束的封包數據回報

使用者追加要求：每輪結束回報全遊戲封包盤點、已串連的具體分支、
本輪差額及未完成項。維護 `artifacts/integration/packet-connections-20261006/
packet-route-ledger.json`，以 `tools.reconstruction.packet_connection_report`
產生唯一輪次的 JSON／Markdown，保留先前輪次。最新摘要為
`artifacts/integration/packet-connections-20261006/packet-progress-latest.md`。

首輪靜態盤點：S2C 長度表252個可接收 opcode（230固定／22可變）；
C2S引數候選145個，尚不是已確認全包種。世界C2S解析55個，其中41個
至少有一條限定功能來源分支，登錄17功能群、41種S2C回覆下限；
10個控制／診斷、4個缺正式業務。登入／角色及其他模式另列，不把
重用opcode直接相加。41包含唯讀、呈現和CUSTOM分支，不代表整個
opcode所有用途完成，不能除以55、145或252宣稱全遊戲完成率。

全遊戲總封包數、全遊戲完整路徑數和百分比仍未知。每輪報告必须
注明來源已接、啟用、部署和客戶端驗收的不同狀態。首次報告只建立
基準，不捏造前輪差額。新增功能分支才更新人工 ledger；不能只靠
新增 parser case 或回覆 opcode 把一個遊戲系統記為完成。

## 三階段執行順序

最新續輪 `20261006-pk-action-views`：原生35 owned選擇／完整序列
經雙side映射送入ONE共同Battle，83/86/88双視角logical回覆與雙方
durable CAS/outbox呼叫鏈已有來源；尚無真實profile、Session完整
admission、回合授權／receipt／terminal恢復。69／35維持未接通；
WORLD56、來源41、S2C下限41、control10、gap5均差額0。仍無測試或部署。

最新續輪 `20261006-pk-shared-storage`：共用 PK state／SQLite backend
已加入來源，同房 ONE Battle、雙人完整 saved readset／checkpoint CAS
與雙方 durable outbox。尚無完整 Session RoomAuthority／真實profile
取得／回合技能／結束重登，69仍未接通，Application保持null、旗標false。
本輪WORLD56、限定來源41、S2C下限41、control10、gap5均差額0。
未建置、測試、安裝schema、修改正式設定、啟用或部署。

目前續輪 `20261006-pk-coordinator`：世界解析56（+1，新增69），限定
來源分支41（+0），S2C回覆下限41（+0），控制／診斷10，缺正式功能5
（+1，69）。PK格式、Session/Application入口、雙方context與生命週期
協調及Lua已加入來源；共用RoomAuthority仍缺實作，功能預設關閉，
不得列為完整串接／實戰。下一步追出1C玩家variant需要的actor前置
建立，接雙方共用戰鬥與存檔。未建置、測試、啟用或部署。

1. **完整串接**：盤點原生雙向格式，接入正式來源的網路、Session、
   Application、C++ 狀態與 SQLite、Lua 規則及 S2C 回覆。此階段停止
   逐項單元/TCP/原生客戶端測試、測試式驗證及個別驗收發布。
2. **全方位測試與驗證**：所有封包功能路徑接通後，集中測試簡繁兩套
   原生客戶端、狀態轉換、角色/帳號隔離、交易與存檔、斷線/重登，
   正常與錯誤序列，以及凍結功能的回歸。
3. **全面修復**：依問題清單修復功能、資料、狀態、回覆及客戶端表現，
   集中回歸後發布可遊玩結果。發布前仍執行凍結聊天 gate。

正式來源整合與正式服務部署分開記錄。現用服務及玩家存檔保留，
不以未測試的階段性重啟打斷本輪完整串接工作。

## 串接完成的定義

每條功能必須有實際的雙向鏈：

`原生操作/producer → C2S格式 → Session狀態 → Application處理 →
C++狀態/SQLite及Lua規則 → S2C格式 → 原生consumer/遊戲功能`

清單至少記錄：客戶端 build/hash、方向、opcode、變體/子命令、
長度/欄位/編碼、producer/consumer 位置、狀態條件、請求與回覆關係、
正式程式入口、狀態變更、持久化、資料/公式來源、未解項目。

僅有收包長度、解析器 case、空 handler、拒絕操作或通用成功回覆，
都不能記為功能完成。未知原生規則繼續逆向；合法 CUSTOM 規則保持
明確標記，不能改稱原生恢復。

## 第一階段的工作批次

- 建立完整 C2S producer 與 S2C consumer 清單，包括包裝/間接呼叫，
  以及登入、角色選擇、世界、戰鬥等不同階段與子命令。
- 對照現有 `src/protocol`、Session 和 Application，區分缺少格式、
  缺少入口、缺少功能/狀態/儲存、缺少回覆，以及已接通來源。
- 先整合已有原生來源及完整候選實作的路徑；接續資料驅動系統、
  角色/同伴、背包/交易/銀行、公會/同盟、NPC/任務、地圖/移動、
  戰鬥/技能/成長及其餘 producer/consumer。相依系統一併接入。
- 每完成一條，更新實际程式入口與雙向對應；不進行逐項測試。
- 全部功能鏈完成才切換階段；有未解的 authoritative handler/
  reply/state/storage 不可提前宣稱全遊戲已串接。

## 現況起點與清理後限制

此前來源盤點為52個世界階段 C2S parser opcode。原生 S2C 長度域為
230 fixed、22 variable、4 unsupported。兩者方向、變體及統計層級
不同，不能相除；沒有全功能可信分母，整體百分比維持未知。

目前運行版本為 schema51。native83 已有候選實作及歷史簡繁原生
接受紀錄，尚未部署。原定逐項更新驗收流程依最新指示停止；
保留全部已有證據與回復流程，不重用舊 launcher/PID/HANDLE/receipt。

清理已完成，歷史研究存入 SHA256/zlib 精簡封存。以必要程式與格式
來源的選擇性讀取/恢復支援工作；不整批還原8.9GB歷史測試輸出及
編譯庫，不把恢復舊測試環境當作本階段主要工作。

## 不變的保護範圍

M1 補充盤點（2026-10-06）：台服通用發送候選151的歷史基準保留，
另存2C／2D包裝參數、6F建立／加入共用發送點、99／A9條件分支的
6筆原生來源證據；合併opcode集合156，不代表156條完整玩法。
目前63個世界解析opcode均有通用候選或此次补充原生證據，但所有
階段、變體、權威與回覆關係仍未窮盡。證據位於
`../artifacts/integration/packet-connections-20261006/tw-supplemental-producers-01/`。
陸服47DE70／4812B0已追查內部落點、owner與游標差異；階段仍未知，
無直接caller不構成不可達證明。最新總表為dual-client-route-catalog-05。
下一步接續CN登入成功／admission的原生欄位與共用帳號世界入口，
這兩個未定階段helper保留為獨立追查項，不能用相同opcode硬配對。

M2 目錄來源增量：CnAccountReplies已加入原生06四byte記錄及
04→05→06有序組裝，限制每group累計最多10個node、每node最多
10個location，按0xA00上限在完整record之間分段。05內server index
改變不會重設原生node ordinal；06後三byte保留opaque，不捏造地圖
或座標。尚需真實拓撲／原生資料供應，未掛入Application或登入成功。
1D會覆寫共用204-byte登入記錄，後續04／00可攜帶舊9C/A0值；
它們僅是claim，不能直接授權，也不能加上「必須為零」的假限制。
server lease/checkkey發行、0A帳務資料、1F角色及世界入場仍是缺口。

M2 授權owner來源增量（20261006-shared-world-admission-owner）：
共用SharedWorldAdmission已接CN帳號／世界兩個Verified continuation，
由核發generation、已驗證帳號、已選端點與保留／提交ticket管理接續入口。
帳號斷線僅解除原帳號socket的控制，世界斷線以原ticket釋放world owner；
cleanup由transport持有，wrapper先銷毀仍可清理。此處容量、明確輸入deadline、
同registry內tuple不重用等是服務端整合／安全政策，不冒稱官方key算法或有效期。
沒有預設issuer、TTL、1D尾欄或billing值，沒有新成功封包。Application掛載、
真正成功／選服controller與1F尚未完成，完整路徑新增0。TW既有入口未更改。
證據與四份來源快照：
`../artifacts/integration/packet-connections-20261006/shared-world-admission-owner-01/`。
另外cn-billing-byte5-agent-01追查123個UI函式及billing別名；兩處memset
均不清payload byte5，原生mutex完成條件也未讀它，仍保留opaque及範圍外追查。

保留帳號、存檔、IME、認證、頭像、原生客戶端二進位及凍結功能。
C++20 負責傳輸、驗證、狀態及儲存；Lua 按既有架構負責規則。
只使用自有服務端。此處的「驗證」指正式程式處理輸入的必要檢查，
不是在第一階段執行測試式驗證。

## 本輪已接入的來源（尚未測試／部署）

- native83：8個正式來源替換、22個新模組，包含世界／Session／儲存與
  公會轉讓的實際入口；正式設定和運行服務不變。
- relations53：共用公會／同盟的固定76請求、95名冊、96刪除、
  schema53 selector、儲存 factory、複合名冊／公告／操作入口接入。
- admission53：7A選單→85選擇→8D名稱提示→6F建會／申請加入，
  既有明確標記的CUSTOM0078 Lua政策、交易儲存、關係wire ID分配、
  錢包回覆與成員／申請者名冊同步串連。所有權以伺服器帳號／角色
  與事前提示lease判定，客戶端名稱和本地slot不提供帳號權限。
- cache bootstrap：依保留的原生91/92流程，50輪byte-slot清除後
  發送目前self91＋self92，11段依序串接；記錄為已入佇列的預期
  原生空快取，**不是已觀測到客戶端執行，也不是新驗收證據**。
  同盟操作仍需獨立的fresh Help授權及完整雙方儲存／WORLD lease。
- 戰鬥世代累積值與「正在戰鬥」分開：共用模組保存原世代供CAS，
  當前WORLD入口和durable active-battle判定仍阻止戰鬥中的操作。

上述仍有戰爭5/9、混合公會操作批次、整體遊戲各系統路徑等未解項。
不把「接入來源」說成「全遊戲完成」，不以53個parser opcode估算百分比。
靜態producer/consumer索引含256個長度入口與225個直接queue呼叫候選；
包裝／間接呼叫及子命令仍需追蹤。相關編译、全方位測試和原生客戶端
驗收留到第二階段；最終更新需重新準備來源CAS與515253復原流程。

## 神獸雙人交易來源續接（未測試、未啟用）

既有29開啟、2A物品、2B金額、2C確認、2D取消已加入完整持有神獸變體。
50回覆使用完整原始metadata20；雙方確認後，同一交易移交持有資料、
4C／可空C5與來源證據，同步背包與27錢包。取消、斷線與自訂逾時
回覆目前保存狀態。移出神獸的選擇退役，收件人不會自動選擇；識別值
衝突依明確標記CUSTOM0085規則重綁，其餘欄位保留。角色刪除既有
外鍵清理涵蓋神獸持有／選擇，獨立刪除歷史保留。詳見
`research/beast-trade-connections-20261006.md`。銀行、餵食、騎乘、探索
活動及外觀等仍未完整串接，沒有全遊戲完成百分比。

## CN 選服授權來源續接（20261006-cn-account-selection-owner）

新增 SharedAccountSelection 的 A6 aggregate→共用帳號 grant→實際目錄
slot／enable／endpoint→共用 CharacterRepository 角色歸屬→grant.select
→同連線原生07來源鏈。07必須由資料擁有者提供完整75bytes及共用角色ID
對應；不使用CUSTOM-0003初始值、不從名字猜角色、不補零未知欄位。
角色摘要的非零routing key需存在於所選group/server的06資料。
目前 NativeSummary 資料供應器、1D／0A登入成功及Application掛載仍未完成，
所以這一條為條件式、未掛載來源增量，完整雙向路徑新增0。

cn-account-tail-agent-01另釐清CF前204bytes會覆寫同一登入紀錄，
重新account04／1D可再覆寫；CF payloadCC額外selector在紀錄之外，
0044D5F0將其與07角色slot低3bits比對後才採用row索引。
CnCharacterSummary新增此查找，未匹配回傳缺值，不默認角色0。
159函式直接位移掃描確認兩個A9 group寫入；其他A8屬不同owner。
AA..CB、CF額外CD..CF及官方成功欄位供應仍未知，掃描不代表全圖alias封閉。

來源／原生定位及雜湊封存：
`../artifacts/integration/packet-connections-20261006/cn-account-selection-owner-01/`。
本輪不建置、測試、執行客戶端、部署或改資料庫；繁簡轉換保留、字體維持原生。

## 共用角色 offer 與 CN 原生入口分支（20261006-cn-character-offer-owner）

核對Application後，已修正上一輪選服控制器的角色庫：使用實際TW玩法
的RecoveredCharacterRepository／recovered_characters，移除早期骨架
CharacterRepository／characters識別值的假共用。兩庫數字ID不互相等同，
不做名字或slot連接；舊來源快照與報告保留為歷史。

選服時已確認歸屬的共用角色ID清單寫入grant當前世代，世界連線只能用
已提交的自身ticket查詢offered角色；空清單不授權任何角色，關閉世界
連線後ticket失效。此為供後續世界選角handler使用的來源範圍檢查，
尚未實作1A選角、角色啟用或1F成功資料。入口仍須重讀目前角色歸屬／revision。

新增CnCatalogRoute的0047FAA0→0047D1C0→0047C830原生分支：
相同group/server先找07非零routingkey，找不到時取第一個有非零
06 locationkey的node，保留05全group ordinal；沒有節點就回傳缺值。
移除先前只接受精確routingkey匹配的過窄條件，不補寫07位置欄位。

cn-summary-opaque-agent-01查明07 flags位0存network+4200及登入UI
分支，新增中性native_mode_bit0讀取，未把它當權限、付費或核發规则。
row18原值投影到124list+24h+28h*i；世界1F會覆寫整份list，
因此後續list值不能自動沿用07來源。row18語義、flags核發及完整
07／1D／0A資料供應仍未知。完整路徑新增0，Application仍未掛載。
來源、角色庫差異、原生三函式bytes／ASM及雜湊封存：
`../artifacts/integration/packet-connections-20261006/cn-character-offer-owner-01/`。

## CN 共用位置移動來源（20261006-cn-shared-movement-owner）

原生2E解析／相鄰方向Lua／非零通行格→必需的真正world authority
→目前共用位置revision CAS→真正actor/window及TW/CN廣播→完整5D
已接条件式來源。mode0/2快照保留原生格值；不沿用TW自訂navigation。
5D byte未猜作ringindex，不補未知移動權限／速度／初始化queue或回覆。
實際WorldOwner／資料／Application仍缺，完整路徑新增0。
詳見`research/cn-shared-movement-owner-20261006.md`。

## CN 登入成功與帳號斷線來源（20261006-cn-account-success-owner）

新增完整原生1D/0A資料→這條連線已驗證Login物件／共用account ID
→issuer deadline與有效目錄目的地→共用grant→AccountSelection→
1D／04-05-06目錄／0A輸出的條件式來源。欄位未知仍要求真實供應器，
不echo04尾欄或補零。新增終止C2S0A的本連線name比較／斷線，保留
已選服world handoff；不由claim查其他帳號。實際native issuer／資料、
Application與剩餘玩法未掛載，完整路徑新增0。
詳見`research/cn-account-success-owner-20261006.md`。

## CN 初始世界就緒來源（20261006-cn-world-ready-owner）

本輪CN初始就緒來源（20261006-cn-world-ready-owner）已加入實際共用
角色／已存位置revision lease、1F→23→1C相對順序、30/36穿插、同連線
2A handle綁定及transport持有的世代清理。普通與CF登入適用；後續
場景恢復／61換圖1C交實際world dispatcher，不套初始三步。
TW尚未加入同一presence registry，完整原生資料供應器、world publication、
bootstrap/control及Application掛載仍缺，完整雙向路徑新增0。
原生新增證據釐清17／1B不同後續流程，以及2A metadata→1B四選UI遮罩，
未推定permission或從preview生成07。詳見
`research/cn-world-ready-owner-20261006.md`；全遊戲分母／百分比仍未知。

## 神獸銀行來源續接（未測試、未啟用）

原生63存入、64取出、65整格交換已加入完整神獸變體；48保留全部
metadata20，持久化4C／可空C5與來源證據。背包／銀行識別值依
CUSTOM0085分開管理，衝突僅重綁已知識別欄位。存入退役对应選擇，
取出不自動選擇。獨立bankv4空表註冊保留舊DDL／存檔／遷移紀錄；
尚未執行安裝。完整交易與回覆接進既有銀行lease，詳見
`research/beast-bank-connections-20261006.md`。原生綁定／活動、取得、
餵食、騎乘、探索及外觀仍待接續。使用者另授權子代理黑箱敵方
屬性／技能研究，該獨立研究不表示啟動主線逐項測試或發布。


## CN 已發布選角改名身分來源（20261007-cn-selection-name-identity）

已接入實際 AccountSelection 發布的完整07、原始 queue 修訂號、原生列序號與共用角色 ID／完整帳號角色快照的查詢鏈。原生 state13 的百分號首尾標記只描述提示分支；不當成伺服器改名權限。原始快照 current 檢查限修改前，SQL BeforeCommit 必須由真正 operation owner 核對已暫存的新快照與規則 lease。正式 D3 處理器、名稱規則、完整07／錯誤回覆供應器與改名後新 offer／恢復仍待接入，完整雙向路徑新增0；等級保持不變，未建置、測試、執行或部署。詳見 research/cn-selection-name-identity-20261007.md。


## CN 帳號改名交易與新列表發布來源（20261007-cn-selection-name-operation）

D3 帳號 ingress 已連到已發布07身分／原生規則 lease供應器、真正共用SQL全帳號快照CAS、TW/CN舊offer失效、來源完整新07／1E與exact queue IO發布。BeforeCommit核對暫存的新共用角色列，不沿用舊名稱根快照。Login composition於成功發布／讀取恢復前安裝可選的真正同一 preparation／presence／SQL供應器；缺失來源不給任意成功。新增条件式owner鏈1／phase關聯3，正式native規則與data/configuredhost／durable recovery仍待完成，完整路徑新增0。另保存並ACK網頁世界迴圈41原生來源範圍（CN21現讀、TW20歷史），本機時鐘／FP不新增server動畫節奏欄位，renderReady=false。等級未改，未建置、測試、原生執行、SQL存取或部署。详見 research/cn-selection-name-operation-20261007.md。


## CN 改名原文與共用編碼串接（20261007-cn-selection-name-encoding）

CN D3 原始25 bytes與共用16-byte名稱／明確codepage已由typed projection綁定；CP936提交與共用CP936／CP950必須是相同UTF8原文且無損往返，未知0僅容許原樣ASCII。成功NameDecision與真正SQL全快照CAS採同一候選；完整07仍須來源發行並echo原CN bytes。名稱識別不套繁簡呈現、正規化或截斷，也不修改舊未綁定存檔。新增共用名稱識別邊界1／CN typed projection1、強化既有D3 operation1；新owner／phase／完整路徑皆0，native權限／唯一規則／issuer／hosting／durable recovery仍缺。原生53F880 display映射保持獨立；已保留3個primary metadata envelope與明確import declaration來源。等級未改，未建置、測試、執行或SQL存取／部署。詳見 research/cn-selection-name-encoding-20261007.md。


## CN 創角名稱與共用快照串接（20261007-cn-create-name-encoding）

完整45-byte原生17與來源明確供應的共用40-byte profile／slot／codepage／style已由typed projection綁定；原CN CP936名稱與共用名稱須是相同UTF8原文且無損往返。NativeCreatePlan在真正共用SQL建立前要求這份projection；實際返回角色逐欄匹配，direct/CAS兩模式成功結果也核對原文名稱。其餘欄位原樣保存，未推定44→40映射／default／slot／level／權限規則。新projection1／既有17 CAS強化1／成功結果資格1，新增owner／phase／opcode／完整路徑0。下一步追實際02／18輸出發布前資格與真正資料／規則／issuer／hosting／durable recovery。另保存並SHA ACK網頁controller53範圍（CN27現讀、TW26歷史；指定TW原本路徑缺失），controller status維持本機UI／操作意義。前一loop ACK與更正對方已讀，新ACK讀取待確認；renderReady=false／peer14前端檢查不算server原生驗收。等級未改，未建置、測試、原生／API／DB執行或部署。詳見 research/cn-create-name-encoding-20261007.md。


## CN 創角02／18發布屏障（20261007-cn-create-reply-publication）

新增verified WORLD connection publication入口，實際帳號／world session／registry ticket在觀察回呼前後核對，沿用未改動的native framing／capacity／IO hold barrier。ordinary create02／choice18於bytes放行前核對current結果／規則與共用角色或已提交位置，publish AwaitingChoice／原status49 retry／failure／Completed；後續queue callback僅確認本次published result與同連線，不套已過時root／lease。direct/CAS來源均需明確QueueAccepted規則階段；存檔已COMMIT則輸出失敗不冒稱回滾。新增WORLD publication來源1／既有02與18關聯強化2／stage-qualified rule handoff1，new owner／phase／opcode／完整路徑0。下一步接selected-world02／2A／initial scene實際發布資格及native資料／規則／issuer／hosting／durable recovery。網頁controlled-raster三原檔及兩引用來源已保存與SHA ACK，118範圍中CN59現讀、TW59歷史；原initial camera／ground、current private publication範圍不擴成整個runtime camera／playable體感，renderReady=false／peer15前端與20GPU檢查非server native驗收。上一controller ACK对方已讀，新ACK待讀；等級不變，PHASE1未建置／測試／API或native／server／DB執行或部署。詳見 research/cn-create-reply-publication-20261007.md。


## CN 世界列表與選角入場發布（20261007-cn-selected-world-publication）

1F與selected02→2A改走實際verified WORLD IO barrier。1F在offer資格通過後先publish offer_queued；selected入口在pending排他下要求真實Reservation分階段觀察，before/QueueAccepted核對同一character/account/session、準備位置／handle／ready First1F、當前MapCatalog完整row與normal exact scene或CF真正previous lifecycle，然後move預配置ready dispatcher及scene再放行IO。Queue callback不再套過時prepared lease／First1F／position／offer root；Preparation completion跨同步／posted失敗只回覆一次，cleanup保持本incarnation與native ReleaseOnce。新增既有1F發布強化1／selected02與2A強化2／stage rule handoff1／single completion1，new owner／phase／opcode／完整路徑0。bootstrap／entered／完整native資料、規則、issuer、reservation／Application hosting／durable recovery仍缺。等級不變，PHASE1未建置、測試、native／API／server／SQL執行或部署。詳見 research/cn-selected-world-publication-20261007.md。


## CN bootstrap actual-source publication (20261007-cn-bootstrap-source-publication)

Existing pre-ready1F/23/30/36 now requires a full actual issuer result and observing BeforePublish/QueueAccepted predicate. Full outputs reuse verified WORLD held IO; next ready stage is published before release. No-output is an explicit source choice requiring the same authority, never a default acknowledgement. Ongoing ready-world controls remain independent. Existing four publication bindings strengthened, one typed result boundary; new owner/phase/opcode/full route0. Actual native suppliers/response causality, initial1C entered/visibility/gameplay publication, Application hosting/recovery and whole-game routes remain open. Levels unchanged; PHASE1 no build/tests/runtime/SQL/deployment. See research/cn-bootstrap-source-publication-20261007.md.


## CN initial1C actual presence/gameplay publication (20261007-cn-entered-world-publication)

Exact full1C now reaches actual scene issuer with inactive same common Lease; required source result/BeforePublish/QueueAccepted precedes activation. Existing held world IO publishes exact presence, existing gameplay/normal movement scene installation and InWorld before release; failures clear original active presence on the same game turn. Later gameplay requires installed controllers. Existing1C publication strengthened1/gameplay entry installation1, lifetime guard1/failed activation cleanup1; source-result/transport contracts reused, new owner/phase/opcode/full route0. Full initial visibility/rules/native data/issuers/providers/hosting/durable recovery and all gameplay/denominator remain open. Peer driver originals SHA ACK with CN59 current/TW59 historical ranges; controlled-raster ACK read confirmed, new driver ACK read pending. Peer16 frontend/56 GPU fixtures not server/native acceptance; renderReady=false. Levels unchanged, PHASE1 no execution/tests/deploy. See research/cn-entered-world-publication-20261007.md.


## CN actual initial incoming visibility (20261007-cn-initial-visibility-publication)

Actual scene issuer must prepare an explicit ordered common actor set/full native6F/5E/73 for the inactive CN recipient. Private same-owner/generation/connection/position token preallocates nodes; each complete81-byte6F matches its actual aggregate slice. Held1C IO qualifies all current sources around issuer, activates recipient/installs gameplay, merges model nodes then publishes InWorld/releases bytes. Existing6F model binding strengthened1/1C result handoff strengthened1, initial publication source1; new owner/phase/opcode/full route0. Full native visibility policy/appearance/data/resources/providers/hosting, outward TW/CN fanout/later lifecycle/durable recovery and full gameplay/denominator remain open. Four CN primary consumer/reset/removal ranges retained, no new fields/rules or native execution. Previous peer driver unchanged; levels unchanged; PHASE1 no build/tests/runtime/SQL/deploy. See research/cn-initial-visibility-publication-20261007.md.


## TW actual common-world held publication (20261007-tw-common-world-publication)

Separate common identity binds/revokes actual TW presence account/character/generation after real ready and before cleanup, never borrowing PRIVATE0083 generation. Complete native source bytes use unchanged framing/budgets; held IO entry ->same game identity/publisher ->requalified IO release ->single game local completion. Original send/PRIVATE0083 method bytes retained; old queue held defaults false, writer stops held head only. TW publication source1/common identity source1/existing lifecycle strengthened1; new owner/phase/opcode/full route0. Actual outward6F model/fanout/caller/full native providers/hosting/initial and later lifecycle/recovery and full gameplay/denominator remain open. Levels unchanged; PHASE1 no builds/tests/runtime/SQL/deploy. See research/tw-common-world-publication-20261007.md.


## Initial CN source ->TW/CN observer publication (20261007-dual-outward-visibility-publication)

Actual1C incoming publication release now dispatches the mandatory actual ordered outward observer set. Full version-native6F/5E/73 and real scene/source predicates feed preallocated common model nodes inside each TW/CN held publication. Exact pending source guards prevent movement/partial model use until all local queues release; generation-qualified disconnect/reset/failure cancels once and requires real recovery, not atomic fanout/rollback. Outward source1/initial1C handoff strengthened1/pending lifecycle guard1; new opcode/phase/owner/full route0. Actual visibility/appearance/resource/data/issuer providers and production hosting, TW own initial/handle/later lifecycle, replay/recovery and all gameplay/denominator remain open. Levels unchanged; no builds/tests/runtime/DB/deploy. See research/dual-outward-visibility-publication-20261007.md.


## CN actual normal scene ->ordinary remote appearance (20261007-cn-normal-remote-appearance-source)

Pinned CN normal2A and6F use00482C90 with differently packed/narrow driver inputs. Actual same normal scene/connection/common lease/full2A supplies the retained source; checked ordinary projection copies only two selectors/eight packed component bytes into a supplied complete6F. Private witness requalifies initial/inward/outward publication; no truncation, alternate fallback, layer/state/name/opaque defaults or TW CUSTOM authority. Projection1/concrete normal source1/existing6F binding strengthened1; new opcode/phase/owner/full route0. Complete actual equipment/appearance/resources/issuer/observer policy/hosting and all gameplay/denominator remain open. Levels unchanged; no builds/tests/runtime/DB/deploy. See research/cn-normal-remote-appearance-source-20261007.md.


## CN original appearance table row/path sources (20261007-cn-native-appearance-resource-source)

Actual selected HeroDoll/Drv file bytes -> immutable native-key/ordinal row profile -> full normal2A/ordinary6F getters -> original ActType/body/face/head/weapon and head-dependent face variant -> selected RoleDoll/Drv paths. Profile1/scene preparation edges2; new opcode/phase/owner/full route0. HeroDoll918 rows, Drv92 slots/rows (machine bound0x5B, not assertion text91). Current DrvDoll exceeds declared length in file-only decoding; exact encoded source/error retained, no bounds relaxation or fabricated auxiliary. ROM/ACT/cache/current profile/issuer/world, equipment/full6F/rules/observer/host and all gameplay remain open. Levels unchanged; no builds/tests/runtime/DB/deploy. See research/cn-native-appearance-resource-source-20261007.md.


## CN full appearance input ->actual selected ROM file source (20261007-cn-appearance-rom-input-source)

Exact full parsed2A/ordinary6F and immutable CSV profile retained ->native004197E0 filename/probe/fallback selection ->four original part inputs/optional actual driver input ->owned source bytes/existing ROM metadata. New ROM-specific selector1/exact SourceRecord lineage1/immutable ROM input source1/scene preparation edges2; no native slot/cache/ACT/rendering/authority success. Six actual CSV-referenced format samples saved, not authenticated actors. Native004197E0 TSV593-byte envelope retains an additive62-byte return tail to00419A6C ret8; old sealed sources unchanged. Auxiliary bounds gap and all bank/context/revision/equipment/full6F/observer/host/gameplay/denominator remain open. New opcode/phase/owner/full route0, levels unchanged; no builds/tests/runtime/DB/deploy. See research/cn-appearance-rom-input-source-20261007.md.


## CN ACTINDEX/reference and same-scene appearance source (20261007-cn-appearance-bank-source-binding)

Actual native ACTINDEX/action operand metadata1/read-only command10 projection1/same-scene full2A+ROM source witness1/existing supplied6F source qualification strengthened1. Two native caches are reused; checkpoint restores allocator cursors, not proof512 slots reset. Actual Drv5451.ROMZ identity5455 and108 raw self references retained. No invented bank, zero slot or CSV-ordinal allocation. Actual source owner/auxiliary/ACT/equipment/full6F issuer/observer/Application hosting and all gameplay/denominator remain open. Web peer confirmed prior127-file ROM source read; current three originals received file-only, renderReady=false, new full route0. Levels unchanged; no builds/tests/runtime/DB/deploy. See research/cn-appearance-bank-source-binding-20261007.md.


## CN actual cache-owner initialization/current-bank source (20261007-cn-appearance-cache-owner-source)

Recovered004826C0 constructor: actual two records cleared, active=-1;004173C0/004187C0 initialize only specified512-ROM fields, not allbytes. Fixed00483820 preload independently advances both banks before004838A0 saved bases. Cache hit/switch/checkpoint and area row-cache invalidation retain differing semantics. New actual owner-layout source reader1/read-only switch operands1/existing command10 selected-bank binding strengthened1; no process memory acquisition or source reader execution. Real owner/current/provider/equipment/full6F/observer/auxiliary/ACT/hosting and full gameplay/denominator open. New opcode/phase/owner/full0, levels unchanged; no builds/tests/runtime/DB/deploy. See research/cn-appearance-cache-owner-source-20261007.md.


## CN account native issuer scope/held success publication (20261007-cn-account-success-publication-source)

Existing verified account→compose_native_login→SharedAccountSuccess now requires actual native issuer scope/current at prepared/beforeissue/beforepublish. Complete1D/ordered original catalog/0A stays behind existing IO encode/capacity publication barrier until exact connection/login/grant confirmation; after local release only current published grant checked, not obsolete issuer predicates. Bounded original request retains wiping deleter, no credential logging/saving. Scope1/existing success publication strengthened1/read-only grant observation1; real seed/1D/0A/entitlement/key/catalog/deadline/provider/host and full gameplay/denominator remain missing. TW auth/codec/selection/admission/core source bodies retained; levels unchanged; opcode/phase/owner/full0, no build/test/runtime/DB/deploy. See research/cn-account-success-publication-source-20261007.md.


## CN verified credential source through login publication (20261007-cn-credential-source-continuity)

Real shared verifier now privately issues a bounded original-row current token; same CN connection/original Login binds it weakly, and compose_native_login plus held account1D/catalog/0A and independently verified World001F publication observe same repository row before bytes leave. No obsolete source veto after release; no raw password in token/receipts; owned new encoded hash copies explicitly cleared. Current-value equality is not monotonic revision/ABA/external-write/cross-process authority. Existing TW auth/Application/repository/admission/native codecs retained; levels unchanged. New opcode/phase/owner/full0; no build/test/runtime/DB/deploy. Full-appearance peer three originals saved, renderReady/releaseEligiblefalse and full0; report checks not rerun. See research/cn-credential-source-continuity-20261007.md.


## CN complete native login record source observation (20261007-cn-login-record-source-observation)

Transferred original CnAccountBilling header byte-identically; readonly1D A8 view and scoped window040A/network40EC/UI17AABE lineage retained. Actual NativeData issuer Current now sees full literal1D/0A plus typed original billing/flags at Prepared/BeforeIssue/BeforePublish; bounded original native data retained/wiped through existing held IO publication, no guessed native issuer/defaults or post-release veto. Current Data2 Client.csvZ ASCII ClientVersion2 observed file-only, complete strictCP936 comment decode failure retained without substitution; no live profile proof. Opcode/phase/owner/full0; all formal providers/hosting/gameplay/denominator remain open; levels unchanged; no build/test/runtime/DB/deploy. See research/cn-login-record-source-observation-20261007.md.


## CN07 native selection resource input source (20261007-cn-selection-appearance-source)

Saved11 primary native envelopes/3865B;00443080 preview literalActType0/four HeroDoll rows, head face-base BYTE derivation, selected palette operands and separate00443640 local mutations recovered. Full raw75-byte07 plus explicit pre/post-panel stage retained; resource rows connect to original ROM-input readers without fabricated2A/6F/driver0/selection or in-world cache. Native levels and shared saves unchanged. New opcode/phase/owner/full routes0; formal07 issuer/cache-bank-ACT/rendering and all auth/world/gameplay/denominator remain open. No build/test/C++resource reader/runtime/DB/deploy. See research/cn-selection-appearance-source-20261007.md.


## CN selection filename cache source (20261007-cn-selection-filename-cache-source)

Saved15 metadata ranges6815B plus retained loader62B additive window. Actual445040 initial22 filename allocations/256 pointer table/separate UI16174 ROM bank, real flow preload/checkpoint0, selected prefix/full-name first match, negative load/no countincrement and success-only filename insertion recovered. Added readonly actual UI/pool/buffers/revision/Current source, slot operand query and preload-count operand; no constructor/default/loaded bank/native success. Standalone tail ASM starts midinstruction and is retained unqualified; corrected identical contiguous655B ends419A6C ret8. New opcode/phase/owner/full0; levels/commonstate/frozen sources unchanged; no build/test/runtime/C++reader/DB/deploy. See research/cn-selection-filename-cache-source-20261007.md.


CN selection filename addendum: final source requires actual CRT009FA544 snapshot0/owner identity and Current;76DD42 folds only A..Z bytes, all other bytes unchanged. Initial malloc/uninitialized navigation inference corrected:76C3BF jumps790027, HeapAlloc flag8 at7EB4FC is verified by full1009-descriptor reader and SDK HEAP_ZERO_MEMORY definition. Successful initial calloc100h,1 is zeroed, never a generated current cache. Initial source/findings remain saved; final source-correction is separate. Total20 native envelopes7266 unique bytes; no test/runtime/DB/deploy.


## CN deferred role refresh source (20261007-cn-deferred-role-refresh-source)

Primary4A single cached DWORD/last-write behavior, pending drain after actual completed step, outer clear after refresh early returns and31/68/6D exact wrapper table/payload00 scopes recovered. Added actual owner/revision/Current readonly deferred source and strengthened existing completed-frame/path handoff with fresh same-owner pending-clear receipt. No provider, renderer/resource success,6D authority or full path configured. Nine envelopes15707B/16001 uniqueB; six scoped variants are not packets/routes. New opcode/phase/owner/full0; no build/test/native/C++reader/DB/deploy; levels/frozen/shared values unchanged. See research/cn-deferred-role-refresh-source-20261007.md.

Static accounting correction for this round: captured004B1B40 metadata is35B, not initial29B. The actual unique range union is15995B, not initial16001B; original draft snapshots/table claims remain preserved beside explicit correction. Final source/native relation records are under cn-deferred-role-refresh-source-01/source-correction.


## CN original WORLD31/68/6D consumers (20261008-cn-same-opcode-consumer-source)

Three exact29/13/29-byte records and actual UI=main+89B26C ownership recovered.31 uses first signedBYTE/WORD identity match and preserved1004B actual row;68 signed resource-count/one-based140B row lookup and native handle gates;6D original28B/page header, retained tail/text/UI dependencies still required. Added actualCurrent/revision/list/resource readonly source operands; attached native evidence to existing three WORLD endpoints without source binding/owner/full-route inflation. Ten envelopes15959B; no native/provider authority, invented stats/skills or request/reply pairing. All formal account/world/gameplay/numeric/hosting/denominator pending; no build/test/runtime/DB/deploy, levels/frozen state unchanged. See research/cn-same-opcode-consumer-source-20261007.md; date7 source filename retained for cross-midnight continuity.


## CN literal directory/deadline source observation (20261008-cn-account-catalog-source-observation)

Strengthened actual existing account-success handoff: BeforeIssue/BeforePublish Current sees exact ordered04/05/06 records and actual issued grant deadline, retained once before moving output records into the held aggregate. Prepared explicitly has directory/deadline absent. No obsolete source check after output release; credential wipe/grant cleanup preserved. Native codecs/wire/TW/Application/admission/transport/DB/frozen contexts unchanged; actual provider/hosting/full routes0. Prior damaged shell-written中文 Markdown and original79-file seal retained; separately named apply_patch UTF8 correction restores presentation only. New opcode/phase/owner/full0; no build/test/runtime/DB/deploy; all gameplay/numeric/denominator remain open. See research/cn-account-catalog-source-observation-20261008.md.


## CN explicit operational transport seed (20261008-cn-transport-seed-source)

Retained pinned CN five function envelopes1703B plus actual key table256B; native intake copies16 literal bytes then derives key/challenge. Official server RNG distribution remains unknown. Added explicitly selected own-server WindowsSystemCngV1 source using BCryptGenRandom success only, same actual endpoint/game owner/one-shot connection identity, no cached/fixed/default/random fallback. Existing login composition chooses exactly one supplied callback or explicit policy; account/world suppliers remain required. Existing listener/codec/PasswordHash/Application/main/CMake/frozen contexts unchanged. Source selected/hosted/full routes0; no build/test/RNG/runtime/DB/deploy; all native login/world/gameplay/numeric/denominator work retained. See research/cn-transport-seed-source-20261008.md.


## CN issued native account source (20261008-cn-issued-account-source)

Implemented explicit SharedIssuedAccountSource: native1D exact credential fields156 + independently verified shared ID4 + separately generated operational check_key4 + actual native profile metadata40;0A exact supplied billing16. Composition selects one full account callback or explicit source config, preserving the existing held grant/selection/publication owner. Profile requires source revision/current observation and all opaque bytes; no profile/default rights/padding invented, no raw request tail reflection. Actual profile owner/hosting remains absent. Retained three primary metadata spans2859B, not new native field semantics or whole CFG. Source assembler1/key issuer1/binding1; new opcode/phase/owner/full0; no build/test/RNG/runtime/DB/schema/deploy; all full-world/gameplay/numeric/denominator scope intact. See research/cn-issued-account-source-20261008.md.


## CN bound native account directory (20261008-cn-bound-account-directory-source)

Implemented actual game-owned bound listener registry: successful bind/listen/local_endpoint precedes controller factory, async accept starts only after complete controllers, managed stop invalidates snapshots before socket close. SharedAccountDirectorySource takes native group/node metadata and derives IPv4/port only from actual targets, preserving04/05/06/order/slot/raw fields. Existing whole-native catalog is qualified without rewrite. Composition always binds the same host/current/exact directory gate before issue/held publication; explicit issued-account producer can use a typed Plan. New registry1/producer1/gates2, new opcode/phase/complete owner/full0; original native catalog evidence reused with no new field claims. No source metadata guessed, formal hosting or build/test/network/native/DB/deploy; frozen transport/native codec/verifier/admission/Application/storage/fonts/conversion/levels unchanged. See research/cn-bound-account-directory-source-20261008.md; full goal remains active.


## CN actual selected group configuration (20261008-cn-client-group-configuration-source)

Recovered four selected config.iniZ resources and pinned native file selection/EOF/group ordinal/slot lineage. Implemented immutable actual resource supplier and required it in existing directory/login composition: slot counts derive from the selected client file, full catalog must match, duplicate group labels stay separate ordinals. Native helper returns0; no GB branch/language conflation. Valid native compressed files differ from plain siblings; no official topology or runtime selection claim. Source supplier1, native selection forms4, existing directory binding1, new opcode/phase/complete owner/full0. Native static file recovery only, no C++ reader/build/test/runtime/network/DB/deploy; frozen source contexts retained. See research/cn-client-group-configuration-source-20261008.md. Full goal active.


## CN normal startup configuration lineage (20261008-cn-native-launch-config-lineage-source)

Recovered00405A60 parsed/narrow argv0 ->complete vsnprintf_s %%s copy ->008AEEC0 and same main+240/0047FA20/0047C990 initial-host lineage. Added bounded normal-startup read factory and explicit StartupClientGroups alternative in actual login composition; mutually exclusive with existing immutable config input. No Windows quoting/ACP emulation/default argument/root or reinit/cache generalization. Ordinary first startup forms3, prior lower-level forms4 retained. Projection1/existing composition binding1, new opcode/phase/complete owner/full0, denominator unknown. No native/API/C++/build/test/runtime/DB/deploy; frozen contexts preserved. See research/cn-native-launch-config-lineage-source-20261008.md; full goal active.


## CN actual config version handshake source (20261008-cn-config-version-handshake-source)

Added selected native config integer/low BYTE source and retained SAME immutable configuration through real login composition, host, connection and transport. Actual preferred$296 ->40 qualifies unchanged native account01/28/00; plain$268 ->12 is not substituted. Missing/mismatched actual source rejects without rebaselining; world240/login200/codec/verification/grants unchanged. Version producer1/existing handshake binding1, new opcode/phase/complete owner/full0; no new tail or billingbyte5 semantics/guessed values. Native/code/resource file recovery only, no C++/native/API/build/test/runtime/DB/deploy. See research/cn-config-version-handshake-source-20261008.md; full goal active.


## CN common character name summary source (20261008-cn-common-character-summary-source)

Added actual common repository name/codepage ->unchanged Unicode identity ->CN936 name producer, retaining complete actual native07 metadata and explicit ordered common ID/visibility mapping. Native prompt markers require explicit source mode; no all-visible/slot/default/opaque/name-lookup rules. Composition binds SAME Context.characters for full account or issued Profile Prepare; conflicting summary suppliers reject. Producer1/existing source composition binding1; opcode/phase/full owner/full routes0. Actual metadata/visibility/revision/profile/billing/host remain unconfigured; whole totals/percent null. No builds/tests/native/API/text-codec/C++/DB/deployment. See research/cn-common-character-summary-source-20261008.md; full goal active.


## CN native role22 summary level source (20261008-cn-native-role-summary-level-source)

Primary-qualified WORLD22 direct cell/branch and BATTLE22 selector/cell/branch reach00519590 with distinct actual UI owners. Added full original25-byte CN22 reader and explicitly revised same-common-ID07 level source; role255 cannot silently become selection-panel1. No level field/progression/cap change, no CUSTOM-0013 stored diagnostic promotion, no other raw metadata defaults. Reader1/existing level projection1/consumer contexts2; opcode/phase/full owner/full routes0. Actual role/metadata/rights/host remain unconfigured; whole totals/percent null. No build/test/C++/native/API/DB/deploy. See research/cn-native-role-summary-level-source-20261008.md; full goal active.


## CN stored common account profile source (20261008-cn-stored-account-profile-source)

Added same-account/backend read-only SQLite snapshot repository and explicit CN stored40/16 Profile producer. Actual login composition binds SAME Context.accounts to existing issuer/common summaries/held output. Complete stored values are reread before/after real Plan/Authority observations; source lineage is not native rights proof or cross-process atomicity. Common table proposal only, no defaults/migration/installation/import/write API; actual rows/rights/Plan/Application remain absent. Reader1/producer1/existing composition1, opcode/phase/full owner/full routes0, whole totals/percent null. No build/test/C++/native/API/DB/deploy, frozen contexts unchanged. See research/cn-stored-account-profile-source-20261008.md; full goal active.


## CN billing presentation variants (20261008-cn-billing-presentation-variants-source)

Qualified actual eight-cell44445C table, group6/7 display override, default8 no billing-row writes and assertion>=9 boundary. ProgramMsg owner+B2F60/4-byte pointer rows and actual11 WORD label IDs are distinct from SystemMessage; wrong same-ID rows retained as rejected source. Added readonly presentation operands to SAME CnAccountBilling already supplied by issuer Observation; no rights/date normalization/serializer defaults. Projection1/resource relation1/eight display cells, new opcode/phase/full owner/full routes0; whole totals/percent null. Actual native values/rights/Plan/Application and whole scope remain open; no build/test/native/C++/API/DB/deploy. See research/cn-billing-presentation-variants-source-20261008.md; full goal active.


## CN post-world exit source (20261008-cn-post-world-exit-source)

Primary six-cell0044A960 table and upstream pushes qualify controls0/1/2 at existing0044A8C8; preserve historical nearest-push counts and add explicit correction. Native main+458 game transport is distinct from main+454 account owner; this post-game transition does not close all return/state semantics. Added same ready lease/current saved position/once terminal designation/actual full03 supplier, integrated as last gameplay aggregate record. Existing write/drain/OnClosed cleanup; terminal callback does not reread obsolete ready source or pump more gameplay. Partial owner1/phase bindings2/new control observations2/direct sites0/opcodes0/full routes0; whole totals/percent null. Actual rule/save/replay/native03 issuer/Application and entire TW/CN/PC/web/gameplay/numeric/stack scope remain open. No build/test/C++/native/API/DB/deploy. See research/cn-post-world-exit-source-20261008.md; full goal active.


## CN world return state frontier (20261008-cn-world-return-state-frontier)

Primary8-cell0048E080 world loop table qualifies6 terminal EAX values; preserved actual main0044A727 use despite void decompiler signatures. Frame25-selector/5-target tables qualify4 negative command selectors; their semantic producers remain open. Cookie normal path preserves EAX; independent world03 cell/24-byte return8/ret4 ->frame1 ->world1 ->main2 ->0201 relation, not default reply policy. Readonly projection1, expanded local entry/table CFG; opcode/phase/owner/full routes0, whole totals/percent null. Actual native03/server rules/saves/replay/Application and full TW/CN/PC/web/gameplay/numeric/stack scope remain open. No build/test/native/C++/API/DB/deploy. See research/cn-world-return-state-frontier-20261008.md; full goal active.


## CN world command return lineage (20261008-cn-world-command-return-lineage)

Qualified actual004AE370 gates/00527840 post-callback mode AL1/2 and final8AC override after four tail callbacks. 005280B0 normal returns have mandatory AL clears: exclude two literal caller candidates at004AE62B, not two global packets. Same0201 carries native main1 and main2 paths; cannot invent server exit reason from control alone. Readonly command projection1/tail projection1/gate relations3; opcode/phase/owner/full routes0, whole totals/percent null. Actual UI labels/early returns/state6/native03/rule/save/replay/Application and full TW/CN/PC/web/gameplay/numeric/stack remain open. No build/test/native/C++/API/DB/deploy. See research/cn-world-command-return-lineage-20261008.md; full goal active.


## CN world exit UI binding and A0/A3 source (20261008-cn-world-exit-ui-binding-source)

Qualified same world+89B26C ECX for initialization0, S2C A3 write1 and condition-gated A0 clear0 after00534640. BOTH A0/A3 full logical records are3 bytes; new readonly reader preserves all payload bytes. UI handles are actual returned AX; same main+464 ProgramMsg resource binds IDs62/63 only to confirmation item2/3, other image-only labels remain unknown. Reporter counts now derive current ledger tuples with optional current-catalog source snapshot binding; historical catalog114 pointer/reports retained. Readonly formats2, flag writer cases3/UI bindings2/ProgramMsg relation1; new opcode/phase/owner/full routes0. Sender/payload/rule/save/replay/Application and full TW/CN/PC/web/gameplay/numeric64/stack99 scope remain open; whole totals/percent null. No build/test/native/C++/API/DB/deploy. See research/cn-world-exit-ui-binding-source-20261008.md; full goal active.


## CN native preborn choice source (20261008-cn-preborn-choice-source)

A0 F74/F75 qualify ProgramMsg281/282 mimic/special-skill choice display counts. Complete primary00534810 code1252B/table28B proves mode1/item6/8A8-zero ordered C2S81(2B)/83(3+2N); metadata162B alone is insufficient. Added four directional readers/A0 projection1 and one conditional common-operation owner composition in SharedWorldGameplay after actual1C. Actual already-issued window, common rule/skills/save/replay and post-commit output revision are mandatory and unconfigured; no fabricated ACK/values/entitlement/reply pairing. Source phase bindings6/partial owner1/new opcode0/full routes0; whole totals/percent null. Full TW/CN/PC/web/WSS/gameplay/numeric64/stack99 scope and real Application/initial issuers remain open. No build/test/native/C++/API/DB/deploy; see research/cn-preborn-choice-source-20261008.md; full goal active.


## CN actual preborn window lifecycle (20261008-cn-preborn-window-source)

Pinned primary initialization qualifies same saved UI owner/mode0 constructor/actual AX handle; A0 gate D4 is native list count, not server permission. Added concrete SharedPrebornWindowSource and held initial window publication: actual supplied records/revision/scope publish before bytes release, then existing81/83 retires local scope before real common transaction and uses actual post-commit output. Gameplay binds same lease/controller/source only, never emits at1C or invents native activation timing. Native84 producer saved but caller/phase unresolved, no84->A0 pairing. Local complete normal CFGs3, primary metadata4968B. Same existing chain lifecycle increment, new opcode/phase/partial-owner/full routes0, whole totals/percent null. Actual subject/resources/initial issuer/rules/skills/save/persistent replay/Application and full TW/CN/PC/web/WSS/gameplay/numeric64/stack99 scope remain open. No build/test/native/C++/API/DB/deploy; see research/cn-preborn-window-source-20261008.md; full goal active.


## CN actual selected preborn subject (20261008-cn-preborn-selected-subject-source)

Pinned mode0 actual array index10/object+90/004D2D30 qualifies UI430AC object and430A8 inline role, thus same selected160/D0 and bank4504/4474. Added supplied-byte CnPrebornSubjectState reader and required same-source revision/selected snapshot in existing window lifecycle; actual common apply receives retained native subject/skill references, not pointer-as-DB-ID or guessed eligibility. Post-commit checks actual new revision and retained identity, never obsolete native Current. Primary metadata11821B/local normal CFGs3; misaligned initial instruction/table views retained as unqualified, actual4936A4 table recovered from root instruction. Actual CN skill loader/catalog/common mapping/rules/save/persistent replay/initial issuer/Application and all TW/CN/PC/web/WSS/gameplay/numeric64/stack99 remain open. New opcode/phase/partial-owner/full routes0, whole totals/percent null. No build/test/native/C++/API/DB/deploy; see research/cn-preborn-selected-subject-source-20261008.md; full goal active.


Selected-subject operational correction: native memory-shaped Snapshot is optional recovery evidence only. Own-server windows require actual common-data subject/skill/rule/save/replay authority and native issuance, without player process-memory/address dependency or invented pointer words. Provided native evidence keeps current/same-revision checks; post-commit uses retained identity and actual new revision. Initial source/findings/catalog131/raw CLI remain preserved; current corrected source and policy are under source-correction, final report binds endpoint-catalog131-final. No new opcode/phase/owner/full routes or build/test/runtime/DB/deploy.


## CN actual skill resource (20261008-cn-native-skill-catalog-source)

Primary scene+149DF8 component loader writes+888444, proving same scene+9D223C bank. Actual CN plain cbspec2.bin112660B/1.03/hash857b52e3 contains453 declared110-byte records in125/130/87/111 groups. Added owned/hash/current qualified CN supplier and existing preborn raw83 WORD ->owned record ->actual common apply/post-commit handoff; no pointer requirement or TW promotion. Resource definitions are not common identity/learned eligibility/cost; real rule/save/replay/issuer/Application and all whole-game scope remain open. No new opcode/phase/partial owner/full route. PHASE1 no build/test/API/native/DB/deploy; later comprehensive validation and recovery release unchanged.


## CN same-table skill source (20261008-cn-shared-skill-catalog-storage-source)

Retained original TW resource7676 and CN857b comparison:448 intersecting native keys, zero identical complete records, CN-only0/122..125 and1/130. Installed TW3adc CUSTOM resource remains distinct; no source baseline replacement or same-ID/name semantic alias. Added CnSharedSkillCatalog binding actual CN rows in existing native_data_sources/native_skill_catalog through the same NativeSkillCatalog reader, full source/ordinal/offset/raw/hash/current/thread checks; existing preborn apply receives owned shared-store native records. Prepared CN source/row material only: no DB access/import/migration/activation. Common skill identity/learning/rules/save/replay/issuer/Application and full-game goal remain open. No new opcode/phase/partial owner/complete route; PHASE1 and later comprehensive tests/repair/recovery release unchanged.


## CN selected skill references (20261008-cn-preborn-skill-reference-source)

Primary4D5E60/4D5CC0 local normal CFGs890B/241sites qualify actual bank record pointer and opaque flag0/3 writers. Added optional actual snapshot ->same shared catalog owning definitions resolver; existing window preparation qualifies supplied evidence only. No client memory requirement or skill entitlement/common identity inference. Full game goal and PHASE1/later comprehensive validation unchanged.


## CN WORLD subject skill update (20261008-cn-world-subject-skill-format-source)

Pinned WORLD34/35 full4B format and actual shared definition reader binding; two phase-format source associations, no new opcode/owner/full route. Three native operands preserved, not common identity or server grant. Actual rules/save/replay/sender/recipient/Application remain open; full goal and phase1 unchanged.


## CN committed subject-skill output (20261008-cn-world-subject-skill-publication-source)

Added actual SharedSubjectSkillPublication owner bound in same1C gameplay/Lease; actual committed event/recipient/revision/native records/owning definitions ->existing held world publication, readonly common mapping/rule/save/persistent replay observations before queue and held release. Bind emits nothing; no old preborn Current, fabricated grant, new wire or local replay claim. Two overlapping phase associations/one partial owner, no complete route. Actual common issuer/rows/rules/save/replay/Application unconfigured; full goal and phase1/later comprehensive validation preserved.


## CN native skill-book bindings (20261008-cn-native-skill-book-bindings-source)

Recovered primary category base/order/prefix-first lookup and SKB type6 alias writer; retained386 bindings/67 no-book definitions and112 zero-alias PFD/GEH candidates. Added pinned actual pair supplier with same shared CN catalog and optional owning common preborn apply/post-commit handoff. No common identity/learned ownership/rule/save/replay/provider/Application completion, no DB/native execution. Whole goal and PHASE1 preserved.


## CN preborn skill-choice facts (20261008-cn-preborn-skill-choice-source)

Recovered2272B/712sites five primary consumers: duplicate identity,19 book12C/literal exclusions and actual optional subject filter using object+90 WORD rather than object+0. Added actual shared selection resolver and retained owning facts into common apply/post-commit delivery, no native memory requirement or authority inferred from UI. No new packet/phase/network owner/complete route; actual common authority/providers/rows/rules/save/replay/Application open. Full goal and PHASE1 preserved.


## CN local GUI close / unphased84 boundary (20261008-cn-preborn-ui-close-caller-lineage)

Qualified nine direct close contexts and actual5342E0 GUI-root/tail lineage;4A89A0 branches to4A8470,not neighboring4A89B0.84 emitter reads actual object WORD+0,not fixedzero. Added exact standalone3-byte reader without WORLD registration or guessed cancel/A0 pairing; indirect/root/phase and full common providers/authority/gameplay remain open. No new packet/phase/owner/complete route; full goal/PHASE1 retained.


## CN shared-table skill import source (20261008-cn-shared-skill-catalog-import-source)

Added explicit SqliteDatabase entry using its own connection and pinned native453-record C++ import source. Existing shared tables/migration/foreign keys/own transaction; no overwrite of partial/conflicting/orphan rows, exact source and every record read back before commit, RAII rollback and actual Current gates. No import/default migration/login/Application execution or grants; actual provider/shared reader/common subject/skill mapping/rules/save/replay/issuer remain open. Retained original native source and prior seal; PHASE1/full TW/CN/PC/web/WSS/gameplay/numeric64/stack99/denominator and later comprehensive tests/repair/recovery release unchanged.


## CN WORLD31 committed source publication (20261008-cn-subject-status31-source)

Reused existing WORLD31 native consumer/table/first signed-BYTE-to-WORD roster match; new shared view used by prior OwnedRows31 projection and new held post-commit publisher bound in actual1C on same lease. Actual common subject/native roster/recipient/fields/rules/save/durable replay/new revision/event/order issuer remains unconfigured; no native process memory prerequisite or same-opcode C2S pairing. One conditional owner and one S2C WORLD31 association, no new opcode/complete route; PHASE1/full goal/numeric64/stack99 and later comprehensive tests/repair/recovery release retained.


## CN WORLD31 panel operand source refinement (20261008-cn-subject-panel-operands-source)

New exact readonly panel operands reuse existing WORLD31 projected row. Primary MOVZX proves all six row34/36/38/3A/3C/3E WORD inputs unsigned; retain old113 seal/report and separately correct its decompiler signedness statement. Special101..108 bonus WORDs kept separate, absent remains unknown, D/E/F use UI42E22/24/20; native32 presentation ADD is not common64 calculation. Metric unsigned row28 / pinned100.0f and ProgramMsg164 pointer source retained, static two-integer text versus native double remains unresolved; no guessed stat labels/formulas. New projection1/existing row handoff1/signedness refinement1/literal relation1; new opcode/phase/owner/full route0; actual common/UI/rules/save/replay/issuer/Application and full goal remain open. PHASE1 no builds/tests/native/API/server/SQL/deploy.


## CN ProgramMsg actual catalog / metric source (20261008-cn-program-message-catalog-source)

New pinned encoded/decoded/current owned1116-row ProgramMsg supplier and existing metric source lookup. Primary loader CSV ID minus1 proves pointer index164 is CSV165 percent format, correcting142 wrong CSV164 candidate while retaining142 seal/source/report. Native column1 getter explicitly clears absent/empty text; raw tails retained without joining column2. Native text mode preserves the pinned CRLF boundary projection. Supplier1/existing metric handoff1/ID-index correction1; resource rows are not packets, new opcode/phase/owner/full routes0. Actual source/Application/GUI readiness/rendering/common semantics/rules/save/replay/issuer and full goal remain open; PHASE1 no build/test/native/API/server/SQL/deploy.


## CN WORLD30 roster and ordered publication (20261008-cn-subject-roster-publication-source)

Recovered WORLD30 length19/actual owner/primary compressed switch extended114-site entry CFG; preserved incomplete99B metadata. Exact signed-BYTE absolute ID/capacity16/staged inactive row/first high-ID control1 skill-count reset/negative append selection and name source operands retained. New typed declaration and ordered30/31/34/35 actual committed event held publisher; same1C ready lease, separate status/skill publishers mutually exclusive, real post-commit identity/roster/name/fields/rules/save/durable replay/issuer required. One partial CN owner/one S2C WORLD30 association; new opcode/full route0. Common providers/Application/all variants/full goal remain open; no native-memory prerequisite. PHASE1 no build/test/native/API/server/SQL/deploy.


## CN ordered subject event frame packing (20261008-cn-subject-roster-frame-packing-source)

Existing ordered30/31/34/35 publisher now packs whole actual records into frames<=2560, bounded256-frame batch instead of old event-total2560 cap/one record per frame. No padding/split/reorder, records/definitions stay aligned. Immutable frame ranges/byte totals retained and supplied to same BeforeQueue/QueueAccepted actual post-commit authority. Existing socket codec/pending/output/wire capacity and held publication unchanged; native byte-cursor/record-reader source retained, not runtime acceptance. Frame binding1/layout observation1/capacity boundary strengthening1, new opcode/phase/owner/full0; actual common rules/save/replay/issuer/Application/all variants/full goal remain open. PHASE1 no build/test/native/API/server/SQL/deploy.


## CN WORLD30 actual GOD names (20261008-cn-subject-template-name-source)

Recovered WORDkey direct pointer table/generic column4 name writer and actual34 GOD rows; separated NPC appearance names and conditional missing-key SPACE literal. Added pinned copied-input CnSubjectTemplateNames/current revision supplier and aligned owning name evidence handoff in existing ordered roster publisher. Independent0042D540 pointer replacement must invalidate source revision;004D4B80 is tab-label refresh, not attribute initialization. New opcode/phase/owner/complete route0; actual common authority/Current/rules/save/replay/issuer/Application remain open. Full goal/PHASE1 retained; no build/test/native/API/SQL/deploy.


## CN WORLD33/39 actual selected-row updates (20261008-cn-selected-subject-update-source)

Recovered actual world owner/case/length2/17 and current role+D0 selected-row null gates. Preserved BYTE40/tail icon bits and DWORD2C/30, MOVZX WORD34/36, four unread payload bytes and signed DWORD %d presentation. Added exact typed forms/full-row readonly projection, optional current native snapshot full row handoff and existing held publisher ordered33/39 forms. Added two S2C WORLD bindings; new opcode/owner/complete route0. Actual common selection/fields/rules/save/replay/issuer/Application and WORLD32 resource source remain open. Full goal/PHASE1 retained; no build/test/native/API/SQL/deploy, no numeric64 completion claim.


## CN WORLD32 and reviewed shared account context (20261008-cn-selected-subject-title32-source)

Three explicitly requested agents completed disjoint title-boundary/receiver-frontier/M2 composition deliveries. Added exact2B WORLD32, four current GodLevel CP936 names, actual-row projection and same held ordered publisher. Selectors0..3 copy actual source;5..255 retain actual text; accepted4 remains UNKNOWN and is not emitted as a guessed empty string. Current invalidates before reset/load/write;42CA20 return1/early EOF is not table completeness. Applied reviewed three-file mechanical same-SQLite account snapshot reader context/owns_accounts bridge; main nullCNplan/actual providers unchanged. Receiver14/12 unchanged; qualified local231-site graph excludes one candidate only. Added one S2C WORLD binding; new opcode/owner/complete route0, whole-game denominator/percentage unknown. Full goal/PHASE1 retained; no build/test/native/API/SQL/deploy.


## CN native login controller Context adapter (20261008-cn-shared-login-composition-context-source)

Reviewed/applied typed real Context source factory ->existing plan.controllers ->compose_native_login caller. Stored profile explicitly binds exact Context snapshot reader; all real Prepare/Authority/native profile/world/client groups/seed source requirements preserved. Main still null CN plan and actual suppliers absent: no activation/full-route claim. Three agents retained startup table-rooted402D40 ctor lineage and initial PE bytes (actualresource/writes/string4 still open), receiver475D40 entry metadata-truncated RET4 closed with exactly one PE byte, and reviewed composition source patch. New packet/phase/owner/complete route0; full goal/PHASE1 retained; no build/test/native/API/SQL/deploy.


## CN actual stored character summary source (20261008-cn-stored-character-summary-source)

Implemented same SQLite/accounts/characters complete version-keyed summary reader, explicit ordinal/commonID/nameMode/optional native22 revision-origin, single SELECT ownership/coherence, actual full75/native25 adapter and whole tuple reload around mandatory real Authority. Connected same Context reader into existing common summary/native login; schema/data/provider/Main activation not performed. Corrected149 outer-login probe: member+464 resource8AF63C, actual UI65364 binding/load lineage qualified; Current/writes/string4 still open and old seal preserved. Three agents plus readonly source review retained; root fixed missing CnCharacterSummary include. Receiver two primary tails/local149-site graph/path-specific ECX qualified, no receiver caller/phase. New packet/phase/owner/complete route0; full goal/PHASE1 retained; no build/test/native/API/SQL/deploy.


## CN actual issuer summary atomic CAS source (20261008-cn-native-character-summary-cas-source)

Added same SQLite/account/mutable-character writer with full expected/next tuple CAS, own transaction, owner/reentry/FK checks, complete common roots and tuple reload around mandatory actual issuer Prepared/BeforeWrite/BeforeCommit; all header/mapping/optional-role writes atomic, four NULL roles, exact cardinalities and owned pre-COMMIT readback. Added strict pinned CN75/optional25 move-only Plan and actual same-database commit entry; actual issuer/caller/schema/data/Main remain absent. Character deletion stale header and issued worldoffer revision invalidation explicitly remain open. Native destruction member+464 lineage/Current invalidation and receiver one tail/negative-handle ECX suffix retained; upstream9 helper preservation unknown. Three owner-requested agents plus readonly review/handoffs retained; new packet/phase/owner/fullroute0, whole-game percent null. No build/test/native/C++/API/DB/deploy; full TW/CN/web/numeric64/stack99 goal stays active. See research/cn-native-character-summary-cas-source-20261008.md.


## Complete native-summary invalidation with owned removal (20261008-cn-native-summary-removal-invalidation-source)

Added complete all-account raw summary inventory in an actual owner transaction; exact canonical scope/tuple/role/ownership and always child-count checks. Explicit actual issuer authorizes whole account header invalidation in same root removal transaction; same backend/owner/FK/fullinterval reentry lease; expected inventory and full roots around BeforeErase, header+child absence before cleanup, roots-minus-ID and absence around BeforeCommit; foreign-account removed-ID references reject. Actual SharedCharacterRemoval with-summary caller preallocates existing character offer plan and applies immediately after COMMIT; general account/worldoffer revocation remains open. Old handler selection preserved; actual native issuer/handler/schema/data/Main not selected. GodLevel rowreader overwrites parser result with1; no column-completeness/bank bound inference. Misaligned42C9B0 excluded. Existing WORLD68 caller/lookup/callback refined; no new phase/stack99 claim. Three agents plus static source review retained. New packet/phase/owner/fullroute0; whole-game percent null; full TW/CN/web/numeric64/stack99 goal active, no build/test/native/API/C++/DB/deploy.


## Conditional native delete summary source binding (20261008-cn-native-delete-summary-source-binding)

Existing native delete success source now explicitly selects complete summary invalidation when host supplies native_summary_removal. Actual same-backend owned observation of all summaries+roots in own read transaction feeds mandatory issuer; exact Attempt/fullrow/fulltuple Decision and both phased native+summary Current precede152atomic removal. Selected source failures do not fall back, nonzero native replies skip observation/preparation/invalidation, Context identity independently guards optional presence. Queue summary Current requires actual committed removal and receipt rather than old raw Current. All summary decisions/expected inventory owned before removal SQL; existing transport completion/send_batch work remains postCOMMIT with durable recovery OPEN. WORLD68 resource/key/outputWORD and negative-GUI-path owner refined; GodLevel scratch/copy destination qualifications separated. Actual issuer/config/schema/data/Main still absent; three agents+source review saved; new packet/phase/owner/fullroute0, percent null, no build/test/native/API/C++/DB/deploy. Full goal active.


## Native deletion held reply before removal SQL (20261008-cn-native-delete-held-reply-source)

Dedicated world mutation entry preserves observing publication semantics. Actual native deletion owns decisions and reply, then existing native transport prepares PendingSend/callbacks/frame+byte capacity/encrypted frames behind barrier BEFORE synchronous game removal. ReplyHeld async resume requalifies exact designated operation/full common root/old identity; actual writer retains full inventory+root CAS and native/summary Current. Local reference callbacks remain confined to synchronous transaction. Nonzero replies skip summary/removal; selected failures never fall back; BeforeQueue gains double phase guard; AfterQueue retained. PostCOMMIT posts/writes/Current/close can still fail; durable receipts/replay/recovery/1E remain OPEN, not DB+network atomicity. Three agents and separate actualsource review delivered WORLD68 nestedowner/conditional preservation and GodLevel selectedrow layout; stride3EC and field distance21 do not prove title capacity. Actual issuer/config/schema/data/Main absent; new packet/phase/owner/fullroute0, percent null; no build/test/native/API/C++/SQLDB/deploy. Full goal active.


## Actual common removal commit observation (20261008-cn-native-delete-commit-observation-source)

Single-attempt noncopy/nonmove process-local observation marks Started before observing calls, actual Committed immediately after SQL writer true, Invalidated only after prepared offer apply true. False/throw consumes attempt; apply failure preserves actual committed fact. Two observed shared entries preserve bool-only semantics through null observer. CN both success branches retain same member fact, exact account/character/Invalidated before queue, distinct nonquiescent CommittedFailure and owner-checked outcome; nonzero skips observation. No new native permission/reply/durable receipt, SQL or frozen TW handler changes. WORLD68 actual stack-base/NULL outputs/normal-return preservation refined. Two research/design workers completed plus source review; title worker interrupted by safety and inventory-only sealed partial, not retried or counted qualified. Actual issuer/config/schema/data/Main/recovery still absent; new packet/phase/owner/fullroute0, percent null; no build/test/native/API/C++/SQLDB/deploy. Full goal active.


## Shared experience award64 settlement source (20261008-shared-experience-award64-source)

ExtendedExperienceAmount validates saved/earned signed64 representability before arithmetic, not EXP gameplay cap or coin cap. Actual virtual/SQLite battle and checkpoint award entries now64, actual canonical numeric request versions/replay/CAS retained, accumulated amount bound explicitly signed64 to existing integer columns. Application progression uses same checked helper; Config type64 but legacy signed32 limit/zero/terminal authorization unchanged; diagnostic opcode89 logical57 accepts64 input then exact bound before explicit DWORD projection. Only existing test fake signature mechanically matched, no tests added/run. CUSTOM award not CNnative; extended TW/CN/web wire/object/display/native award rules stillOPEN. Three workers+source review delivered WORLD68 child owner write/register and server-only HP/damage storage+calculation frontier; no retry of interrupted native title research. New packet/phase/owner/fullroute0, percent null; no schema/build/test/native/API/C++/SQLDB/deploy. Full goal active.


## Three-worker HP/damage connection dependencies (20261008-shared-hp-damage-connection-frontier)

Owner requested delegation: three disjoint workers delivered actual resource load/CAS/writer/schema/role maxima, Battle/Lua/checkpoint calculations and per-recipient native projections/web source evidence. Root additionally captured PK legacy entry/readset/checkpoint/outbox and guild whole-resource lease dependencies. Source hashes, copies and reading ranges retained; bounded inventories are not all writers/consumers. This round is new research, not implemented HP/damage widening or native packet/phase/route completion. Preserve exact original DWORD math and version1 replay; separately version wide storage/checkpoint/role/entry/recipient profiles and additive migration, exact Lua integer arithmetic. No coin cap applied to HP/damage; gameplay maxima remain undecided; native levels/frozen functionality unchanged. Prior EXP64 source and all history preserved; interrupted title native work not retried. New complete routes0, percent null; no game-source mutation/build/test/native/API/C++/SQLDB/deploy. Full goal active.


## Actual shared HP64 storage and legacy boundaries (20261008-shared-hp-storage64-source)

CharacterResources HP/maxHP64, checked absolute signed64 storage representation, actual repository uint64 load/explicit signed64 CAS bind and complete HP/MP guards before settlement canonical replay connected. Whole owner/revision/role maxima/readback/receipt/version123 preserved. Supply/manual/PK/diagnostic initialHP and role/progress/party native inputs check full values before narrowing; party snapshot retains full values before original HUD guard and independent chat readiness. Three agents plus fresh storage review retained separate before/current receipts; recipient worker authored onlytwo party files. Old migration/Application snapshot retained and currentrouting reviewed separately. Schema DWORD/mandatory role equality and Battle/rules/checkpoint/native profiles remainOPEN; do not bypass guarded53 for54 or guess dependency-dropping migration. No cap selected or level/CUSTOM/nativewire changes. New packet/phase/fullroute0, percentnull; no build/test/native/C++/Lua/API/DB/SQL/deploy. Full objective remains active.


## Shared Battle HP64 core source (20261008-shared-battle-health64-core-source)

Battle actor HP/maxHP, damage/loss and revival input/output carry64-bit exact values. Explicit ExtendedHealth64 profile connects signed loss/healing arithmetic and staged act/revive; LegacyCustom default preserves prior limits/native DWORD behavior. Checkpoint v1 unchanged shape and v2 explicit profile tag, strict restore/canonical/runtime identity; diagnostic and PK reader/writer admission stays v1Legacy with profile invariance. Original bounded Lua formulas, MP/stats/levels/wire preserve; full native/WSS/web numeric profile, exact wide rules, role authority and additive recoverable schema remainOPEN. Three bounded agent deliveries retained real before/current sources and late observation copies. Actual18 gameplay files modified; no opcode/phase/fullroute added, percentage null. No build/tests/native/API/Lua/DB/migration/deploy. Full goal remains active.


## Actual explicit Battle profile and exact Lua64 source (20261008-shared-battle-lua64-source)

Shared profile header and actual act/revive callback propagation connected; ExtendedHealth64 uses exact Lua integer inputs/returns and inherited custom formula integer floors in separately labeled CUSTOM0090. LegacyCustom modules/caps retained; new trusted Policy profile must match Battle before binding. No inferred official formulas, skills/stats, native CN custom permission or client numeric profile. Registry0090 appended without changing prior87 records. Application/PK/diagnostic/schema/native wire unchanged and full admission/authority/persistence/native/web display remainOPEN. Actual9 gameplay source files plus provenance registry changed, three actual bounded agent deliveries. New packet/phase/fullroute0, percentage null, no builds/tests/native/API/Lua/DB/migration/deploy. Full objective remains active.


## Actual Supply HP64 and projected atomic source (20261008-shared-supply-health64-source)

Supply HP/maxHP/restoreHP widened, explicit ExtendedHealth64 uses exact Lua integers through unchanged CUSTOM0016 supply.lua. MP retains old signed32 bounds; actual known profile propagated from trusted Policy. Legacy bytes/order retained; Extended needs pure full-value bounded logical projection before existing atomic inventory/resources CAS. Current factories remain LegacyCustom; role maxHP DWORD/schema constraints retained. CUSTOM0091 appended preserving88 designs and metadata. No new recovery amounts, items, native formulas, CN framing or activated native wide profile. M2 actual factory-before-listener-start dependency requires deferred directory construction during account preparation; real rights/world providers and Main selection remainOPEN. Actual4 gameplay source files plus registry changed, three bounded agent deliveries. New packet/phase/fullroute0, percentage null, no builds/tests/native/API/Lua/DB/migration/deploy. Full objective remains active.


## Actual deferred stored-account directory source (20261008-cn-deferred-stored-directory-source)

with_active_directory retains real Prepare, exact managed listener/configuration owners and same game thread; observes only on account preparation after host start, with busy/current guards. Actual compose_native_login stored-profile branch wraps Prepare before existing create. Raw complete catalog becomes an owned qualified directory; valid supplied directory-only source and its authority are preserved. Supplied directory previously lost its Current after catalog copy; issuer now retains that original Plan before key/credential copies, checks current all phases/exact catalog before issue/publish, rechecks after actual Authority. Actual Context gate also remains. No invented fields/rights/defaults/opcodes/native formulas. Existing create fulltuple and credential/key/native output/summary unchanged. No late post-release source veto or remote rollback claim. Main production selection, actual native data/phased entitlement/summary/world Reservation and schema inputs remain OPEN. Actual4 source files changed, three bounded agent deliveries. New packet/phase/fullroute0, percentage null, no builds/tests/native/API/Lua/DB/migration/deploy. Full TW-CN-web objective remains active.


## Actual native account source materialization (20261008-cn-account-native-source-materialization)

Explicit CN native account40/16/pinned-build input Plan and actual phased Issuer connect through same-object Application account reader/writer. Game-owner/reentry/owntransaction/FK guards, complete account and expected snapshot, supplied increasing revision CAS and staged readback before real BeforeCommit; result owned preCOMMIT with no postcommit callback/reload/allocation. No password/account record passed to issuer, generated native values/revision, default rights or native ACK. Existing schema text/registration, login Authority/native serializers/key/directory and all saves/frozen features unchanged. Actual source bytes/issuer implementation/caller, phased login entitlement/summary/world/schema/Main selection and publication/invalidation remain OPEN. Actual6 source files changed/added, three bounded agent deliveries. New packet/phase/fullroute0, percentage null, no builds/tests/native/API/Lua/DB/migration/deploy. Full TW-CN-web objective remains active.


## Parallel actual native delivery storage (20261008-parallel-game-connection-frontier)

Three resumed agents connected original native account/summary schema -> independent explicit schema qualifier/installer -> same migrated SQLite backend -> actual --migrate-only --native-delivery-schema CLI caller. Original DDL/base migrations/readers/writers/common identities unchanged; no native data/default permissions/Main CN factory/activation. Five C++ source files changed/added.30 saved TW83/86 subdispatch inventory records explicitly separate native cases, existing scoped projections and unresolved original authority/state/caller; no new native discovery or complete route. Separate numeric matrix and actual TW-world caller evidence identify next source work. Packet/phase/fullroute additions0; whole-game denominator/percentage null. No build/test/C++/native/SQLite/runtime/migration/deployment. Full TW-CN-web goal active.


## TW battle fields and actual Session lifecycle (20261008-tw-battle-state-source)

Three agents delivered six C++ source increments: two owned raw consumer field views for known83/02,0C and86/2; four existing source files connect the actual once-per-Session factory caller and fresh Binding assembly. Native emission/state mutation and actual Application hosting remain absent. Original30 battle inventory entries retained with separate new annotations; existing86/3/4/5 metadata and6 disjoint sides do not count as new discovery. Actual persisted world position/revision/scene/full native movement and recipient appearance sources, shared TW/CN presence and CN issuer/rights/Main remain open. Packet/phase/fullroute additions0; whole-game denominator/percentage null. No build/test/native/C++/Lua/DB/SQL/runtime/deploy. Full TW-CN-web goal remains active.


## Actual common Application world context (20261008-shared-world-host-context-source)

Three agents delivered ten C++ source increments. One game-owner SharedWorldHost creates the actual same repository/presence/visibility pair; explicit Application world plan and four public entrypoints pass it to TW per-Session lifecycle factory and the CN controller Context. A game-owned vault retains actual TW factory/hooks/installed cleanup behind revocable network facades, with cleanup-owner source projection and normal/startup-failure scope revocation before database destruction. The actual game disconnect also abandons the correct still-owned slot when close arrives after factory but before prepared/cleanup installation; identity/reentry guard failures cannot consume another slot. Mandatory actual Entered and world data remain caller-owned; default Main and frozen handler bodies are preserved, no candidate frame/state promotion/native gameplay success. Native83/08 unsigned WORD9 control field and side-specific bounded consumer view added without damage semantics, runtime emitter, authority or native pairing. Prior30 battle entries and full prior165 sealed inventory retained. Packet/phase/fullroute additions0; whole-game denominator/percentage null. No build/test/native/C++/Lua/DB/SQL/runtime/deployment; full TW-CN-web goal remains active.


## Actual common preparation and TW saved native entry (20261008-common-world-preparation-source)

Three agents delivered ten C++ source increments. CN explicit assets/Reserve/budgets select one actual preparation from the exact Context host repository/presence/visibility; legacy world and naming sources check both registry identities. Optional naming bind requires explicit intent and an absent competing preparation. TW actual saved character tuple/position revision/map record and mandatory full native frame/Current source connect through an explicit Application factory and a game-owned revocable entry vault. A newly discovered actual dependency requires adopting the native frame geometry into existing movement state before the preserved ready bind. The dedicated opt-in preparation uses actual saved geometry and existing qualified navigation; no candidate frame, placement defaults, SQL write or invented appearance. Conflicting candidate appearance/visibility diagnostic modes reject explicitly. Existing default entry/ready/prepare/bind bodies remain; all original native frame bytes retained. Actual native producers, scene owner, queue-stage Current, CN rights/assets/Reservation, Main selection and full-game routes remain open. Full prior166 inventory and30 battle entries preserved. New packet/phase/fullroute0; denominator/percentage null. No build/test/native/C++/Lua/DB/SQL/runtime/deployment. Full TW-CN-web goal active.


## Actual asynchronous TW scene publication (20261008-tw-scene-publication-source)

Three agents delivered ten C++ source increments. Separate initial TW visibility tokens retain exact prepared recipients, source generations, saved positions and complete supplied native6F/5E/73 models. Explicit asynchronous lifecycle and mandatory scene issuer connect the actual native tail to held entry publication, phased Current, real scene Install/InWorld, exact common presence activation/ready identity and incoming model publication. After the actual incoming queue release, the full supplied TW/CN outward observer set publishes through the existing native visibility owner before gameplay input resumes. Cancellation and game-owned revocable callback storage cover pending operation failure and release. Legacy sync/default handlers and CN initial publication remain separate. Local queue release is not native receipt; no guessed native values, visibility policy, scene resource rules or distributed atomic fanout. Original scene issuer/reservation/assets/WorldOwner, CN native rights/data/Reservation, Main selection and full gameplay still open. Entire prior1671990 sealed members and30 battle entries preserved. Packet/phase/fullroute0; denominator/percentage null. No build/test/native/C++/Lua/API/DB/SQL/runtime/deployment; full TW-CN-web goal remains active.


## Actual native TW record boundary grammar (20261008-tw-native-record-grammar-source)

Three agents delivered pinned TW native grammar/source integration and bounded CN owner research. Four C++source increments add a read-only grammar and connect scene/transport. Native230fixed/22variable/4unsupported counts unchanged. VariableWORD is total includingheader3, native single record<0xA00; malformedtotal0..2 nativeearlyfinish is honestly rejected. Every native6F aggregate boundary matches exactly one full81-byte ordered staged model/offset; hidden/omitted/duplicate/non-boundary designations reject. Non6F bytes/order unchanged. Explicit entry transport grammar runs before callback ownership/budget/encoding; old readyrecords byteidentical. Explicit noinitialreply is local-only. CN five native spans/four mechanical constructor+104/two4710-allocation relations remain phase-null;14contexts/12qualified unchanged. Native source issuers/resources/fullpeer/Current/WorldOwner/Main and all gameplay still open. Entire prior1681824sealedmembers and30battleentries preserved. Packet/phase/fullroute0; denominator/percentage null. No build/test/native/C++/Lua/API/DB/SQL/runtime/deployment; full TW-CN-web goal active.


## Actual TW common movement host source (20261008-tw-common-movement-host-source)

Three agents delivered eight C++source increments (sixexisting/twonew) plus five bounded CN slot/callback relations. The actual game-owned published lease supplies a strongly owned controller/native WorldOwner/rules; malformed wholebatch rejects beforefactory. Explicit Application Context selects the actual movement/release/invalidate_active trio, weakVault facade requires completedscene; disconnect releases controller before lifecycle/DBteardown. Caught source or Vault reentry invalidates actual provider before next positionCAS; complete native5D is supplied and peerprojections prepared before singleCAS. Committedprefix remains durable. No actual native WorldOwner/resources/rights/full5D/Main was invented or selected; mixedworldrecords remain separate and frozenCUSTOM remains unchanged. CN slotcopies and knowncaller ECX/threadcallback relations add no unknownphase;14contexts/12qualified unchanged. Entire prior1692003sealedmembers and30battleentries retained. Packet/phase/fullroute0; source162; denominator/percentage null. No build/test/native/C++/Lua/API/DB/SQL/runtime/deployment; full TW-CN-web goal active.


## Actual TW native map getter and retained movement scene (20261008-tw-native-movement-scene-source)

Three agents delivered three new C++sources: actual46FF0 mode0/mode2 rawcell reader and a concrete strongly owned TW native WorldOwner/factory. Mode0 reads real63x63 embeddedwindow/centers; mode2 follows actual32bitpointerlinks and signedwidth/height into rowmajorcells. Rawtags preserved, missinginputs never default0. ActualSession/lease/savedposition/nativegeneration/Current qualify immutable realownedmaterial; actualAuthority/full5D/one-use publication remain mandatory beforeCAS. Concrete publish retains the actual committed actorposition/direction for latersteps; sceneincarnation is source state, not an invented originalnativecounter. CN bounded newcaller/callee/lockcontext evidence does not qualify unknownreceivephase;14contexts/12qualified unchanged. No existingC++/Lua/nativeEXE/DB changes. Entire prior1702071sealedmembers and30battleentries retained. Packet/phase/fullroute0; source163; denominator/percentage null. Snapshotissuer/actualserverrights/full5D/runtimecache/resources/Main/fullgame remain OPEN. No build/test/native/C++/Lua/API/DB/SQL/runtime/deployment; full TW-CN-web goal active.


## Original-derived TW mode2 grid composition and retained scene (20261008-tw-native-grid-composition-source)

Three agents delivered two new grid C++sources and extended two retained scene sources. Original TW coordinate/mask/ordered object evidence qualifies address-free composition without fake native structures or addresses. Rawtags and actual material provenance/generation/Current remain mandatory; the unchanged captured snapshot path is retained separately. The retained WorldOwner connects composed cells to the existing real movement factory/controller and one common position CAS; actualAuthority/full5D/one-use publication remain required. CN bounded mechanical evidence does not fabricate unknown receivephase;14contexts/12qualified unchanged. OtherC++/allLua/nativeEXE/DB unchanged. Entire prior1712067sealedmembers and30battleentries retained. Packet/phase/fullroute0; source164; denominator/percentage null. Materialissuer/actualserverrights/full5D/runtimecache/resources/Main/fullgame remain OPEN. No build/test/native/C++/Lua/API/DB/SQL/runtime/deployment; full TW-CN-web goal active.


## TW native tile-mask and actual map asset material (20261008-tw-native-mask-material-source)

Three agents delivered four new native mask/asset C++sources. Qualified actual native source bytes and placement/selection semantics feed the existing grid and retained movement scene directly. TW proof remains distinct from CN references; rawtags and actual material provenance/generation/Current remain mandatory. No native x86 addresses or unknown permissions are fabricated. The existing WorldOwner/movement factory/controller/one common position CAS remain unchanged; actualAuthority/full5D/one-use publication still required. CN bounded mechanical evidence does not fabricate unknown receivephase;14contexts/12qualified unchanged. ExistingC++/allLua/nativeEXE/DB unchanged. Entire prior1722047sealedmembers and30battleentries retained. Packet/phase/fullroute0; source165; denominator/percentage null. Nativeassetselection/lifecycle/actualserverrights/full5D/runtimecache/Main/fullgame remain OPEN. No build/test/native/C++/Lua/API/DB/SQL/runtime/deployment; full TW-CN-web goal active.


## TW native ROM geometry and exact map binding (20261008-tw-native-rom-geometry-source)

Three agents delivered two new ROM C++sources and two modified map asset C++sources. Qualified actual TW ROM/action/image geometry feeds exact ordinal/reference-bound map material, the existing grid and retained movement scene directly. TW proof remains distinct from CN references; rawtags and actual material provenance/generation/Current remain mandatory. No native x86 addresses or unknown permissions are fabricated. The existing WorldOwner/movement factory/controller/one common position CAS remain unchanged; actualAuthority/full5D/one-use publication still required. CN bounded mechanical evidence does not fabricate unknown receivephase;14contexts/12qualified unchanged. OtherexistingC++/allLua/nativeEXE/DB unchanged. Entire prior1732134sealedmembers and30battleentries retained. Packet/phase/fullroute0; source166; denominator/percentage null. Nativeassetselection/lifecycle/actualserverrights/full5D/runtimecache/Main/fullgame remain OPEN. No build/test/native/C++/Lua/API/DB/SQL/runtime/deployment; full TW-CN-web goal active.


## TW native resource selection and game-owned scene source (20261008-tw-native-resource-selection-source)

Three agents delivered four new selection/resource owner C++sources. Qualified actual native TW selected resources feed exact ordinal/reference-bound map material and a concrete game-owned source supplier for the existing scene factory. TW proof remains distinct from CN references; rawtags and actual material provenance/generation/Current remain mandatory. No native x86 addresses or unknown permissions are fabricated. The existing WorldOwner/movement factory/controller/one common position CAS remain unchanged; actualAuthority/full5D/one-use publication still required. CN actual account location consumer evidence does not invent map/coordinate semantics or unknown receivephase;14contexts/12qualified unchanged. ExistingC++/allLua/nativeEXE/DB unchanged. Entire prior1742124sealedmembers and30battleentries retained. Packet/phase/fullroute0; source167; denominator/percentage null. Unqualifiednativepaths/dynamiclifecycle/actualserverrights/full5D/runtimecache/Main/fullgame remain OPEN. No build/test/native/C++/Lua/API/DB/SQL/runtime/deployment. Owner explicitly requested stopping after this175 round; preserve full objective and pause goal after completed accounting/seal, no next round.

## 第176輪恢復：正式來源呼叫端組裝

使用者明確回覆「現在恢復串接，全部打通後才驗證」，撤銷第175輪後的停止要求。沿用全部 TW／CN／網頁遊戲目標，先實作完整雙向來源，全部接通後才集中建置、測試、驗證與修復。本輪新增同一 Application Context 的 entry／initial scene／movement plan、實際 native movement resource/controller host 與精確 retirement，以及 CN 實際 account callback 的選角 Location 資格鏈。原始07與原生基準不改；完整 native suppliers、Authority／完整5D／權限與 Main 仍需實際接入。完整路徑新增0，來源紀錄168，全遊戲分母與百分比未知。細節：[第176輪](research/tw-native-host-composition-source-20261008.md)。
## 第177輪：原生世界混合封包來源串接

持續啟用目標模式，依使用者要求先全部串接、再集中驗證。本輪新增同源 Movement／Others 分派與 Application opt-in 呼叫、精確來源資格及斷線清理；台陸子代理追查原生導航／raw cell 消費規則。兩個新與四個既有 C++ 檔變更，來源紀錄169；新 opcode／phase／完整雙向路徑仍為0，全遊戲分母與百分比未知。實際 native Others／Current／權限／5D／場景供應及 Main 仍待接入，不把可接入介面算成完成玩法。TW／CN／網頁全遊戲、數值64位元、stack99、原生字體與繁簡轉換要求持續保留，沒有建置、測試或部署。見[第177輪](research/tw-native-mixed-dispatch-source-20261008.md)。

## 第178輪：原生聊天到混合分派的來源呼叫

目標模式保持 active，先全部串接、後集中驗證。新增 TW 原生 chat source 與有序 sender reply／remaining handler 分派，透過實際 Context 接入 MixedRecords plan；OtherBinding 的失效與清理傳到真正處理端。實際權限、native header／cipher／loaded destination／完整場景供應及 Main 仍未完成，不用預設成功替代。新原生證據區分4968E0特殊命令 producer與496990普通／頻道路徑，限定新TW普通sink252 bytes，凍結聊天原件保持。四個新、四個既有 C++ 檔變更，來源紀錄170，新增 opcode／phase／完整雙向路徑0；全遊戲分母／百分比未知。保留 TW／CN／網頁全遊戲、64位元、stack99、原生字體／繁簡轉換與凍結功能。見[第178輪](research/tw-native-chat-record-source-20261008.md)。


## TW typed native chat-family and consumer source (20261008-tw-native-chat-family-source)

Three agents delivered a read-only complete actual TW5C contract and original native TW/CN family-source evidence. Actual Private2/9, Party1 and Guild3 parser variants now preserve all4 raw header bytes and original text into the existing native chat source in order; entire exact chat-copy preparation precedes actual game callbacks. Eight proven TW plain channels use the actual252 whole-text domain; wire8/9 alias0/2 before the initialized ESC-prefix sink. Source consumes the actual complete supplied record, not a guessed header/prefix. Channel-specific permissions/membership/whisper lookup/audience/native header/profile/loaded destinations remain mandatory real suppliers. One new and three modified C++ sources; source segments170->171. New opcodes/phase/fullroutes0, full denominator/percentage null. Main remains unselected. TW/CN/web all-game,64bit,stack99,shared tables,native fonts/conversion/frozen features remain full scope. Entire prior1782258sealed members preserved, before1285 pinned, complete originals/intermediates/agent/raw/final reports separately kept. No build/test/native/C++/Lua/codec/API/DB/SQL/runtime/deployment or security-stopped155 formatter/capacity-chain retry. See docs/research/tw-native-chat-family-source-20261008.md.

## CN native chat consumer and actual owner source (20261008-cn-native-chat-consumer-source)

Actual CN ingress uses complete supplied TW5C reader/header and eight proven plain252 whole-text budgets, with explicit recipient CP936/CP950 independent of native consumer tag. Actual SharedWorldGameplay caller passes its strong chat WorldOwner; ongoing outer active-batch rejection invokes the same actual chat invalidator, and source/full recipient lease-position-phase checks bracket owner/visibility callbacks. Transport close_requested is immediately visible; socket and OnClosed cleanup are deferred, so no false async-closing-flag claim is used. Four existing C++ sources change; source segments171->172. Actual legacy TW CUSTOM0073/74/75/62 rights/narrow IDs/audience/formatters cannot become native CN authority. Native-neutral64 ownership/namecodepage/full common lease source is retained and mapped. Original CN recipient fields reconciliation is retained-only, not new spans/opcode/phase/fullroutes. Actual fullheader/native issuer/rights/membership/whisper identity/loaded sinks, entry/Main and all-game routes remain OPEN. TW-CN-web64bit/stack99/common tables/native fonts/conversion/frozen features remain full scope. Before1290 pin and entire1792226 sealed members preserve originals/intermediates/agent/raw/final reports. No build/test/native/C++/Lua/codec/API/DB/SQL/runtime/deployment or retry of security-stopped155 formatter/capacity chain. See docs/research/cn-native-chat-consumer-source-20261008.md.

## 第181輪：原生私聊的共用在線身分來源

兩個新、六個既有 C++ 檔將同一 presence 的完整64位元 active population、實際 common root／saved position／strict name codepage 與不可變 current proof，接入實際 CN／TW native named-chat callers。新 source 先複製 target 原始位元組與 registry，再讀取並重新核對完整人口；缺失／重複／重入使整次觀察失效，不授權任何假收件者或預設回覆。TW 原生 typed15-byte、history72-byte、issued peer名字與 common14-byte範圍保持分開；真正Owner仍須提供native namespace／fullID mapping／權限／body grammar／完整header與實際loaded destination。台服新原生12spans1439B、陸服retained6spans404B均不增加opcode或完整玩法數。來源172→173，新opcode／phase／完整雙向路徑0；全遊戲分母／完成率未知。Main與其餘全遊戲路徑保持OPEN，先全部來源串接再集中測試。完整before1294、前輪2249sealed members、actual originals／intermediates／三代理與報告分別保存；全TW-CN-web／64位元／stack99／共用表／字體轉換與凍結功能目標不縮減。見[第181輪](research/shared-native-chat-identity-source-20261008.md)。


## ?182????????????64????

??CN?TW Publication?????target?sender private visibility Binding???PublishedChatName source???identity/presence/visibility???raw-name encoding/revision/Current???root?lease???strong sender transport?????Witness?????Current?delivery?queue????????12?DWORD?common64?TW?????6F bit25??loaded WORD selector??????adapt????raw???????????RawNameState?????adapted?manual?history?offscreen??????OPEN?CN tag0????CP936?tag1 receiver projection????????alias???????C++?????173?174??opcode?phase???????0???????????????issuer????membership?fullheader?cipher?loaded sink?entry?Main????????????active???TW-CN-web?64???stack99??????????????????before1300???1812318sealed members??????build?tests?runtime?native?codec?API?DB?SQL??????155?????[?182?](research/native-published-chat-identity-source-20261009.md)?


## ?183????????6F????

??SharedNativeActorNameSource?onlyfirst29..44?????TW/CN6F??show/??initial/outward?publisher?????aggregate?fullmatch?supplied81B?same-size??????records?PublishedChatName??C2S inputpage?actual6F nativepage?????UTF??rawbyte???2new6mod?8CPP?source174?175?newopcode/phase/fullroute0?????null???TWsystemLANGID initializer?cachedtwoWORD????????loadedCurrent?wirepage???adapted names/actualsuppliers/rights/Main/???routes OPEN??research/native-common-actor-name-source-20261009.md??build/test/runtime/DB/deploy?????active?


## Round184 common native world transport source

Actual same-presence full ready Lease now binds actual TW Session or CN connection after true entry completion (TW sync/async; CN after held incoming and all outward queue releases). Private weak-transport Token cleanup precedes common presence cleanup and cannot erase another incarnation. TW/CN Chat explicitly selected deliveries look up actual registered transports, retain strong operation snapshots, and qualify registry and sender endpoints after actual observers. New C++2 + modified10 =12 files; source175 to176; opcode/phase/fullroute increment0. Native spectator source evidence keeps actor namespaces distinct, mode2 input event latch not battle authority, unknown UI/external target publication OPEN. Actual WorldOwner rights/audience/profile/full native reply/cipher, entry/appearance suppliers/Main/all game routes remain OPEN; denominator/percentage null. Whole source first, no build/test/native/C++/Lua/API/codec/DB/SQL/runtime/deploy. Original account/saves/native fonts/text conversion/IME/auth/avatar/client/frozen features preserved. See research/shared-native-world-transport-source-20261009.md.


## Round185 actual native transport host composition

One actual Application SharedWorldHost now constructs/retains the same-presence native transport source. Two real sync/async TW lifecycle callers, the real Context chat factory, CN common login preparation, two alternative preparation identity checks, and actual Reservation.gameplay->Sources->Gameplay composition receive that exact source. No parallel CN registry or default native data/rights. Existing C++7 changed; no new CPP; source176 to177; newopcode/phase/fullroute0, denominator/percentage null. Bounded TW D0 two WORD operands feed the target arrays later used by C2S6E; CD flags/metadata and reset are independent qualification requirements. Actual target namespace/current battle authority and full native reply/rights/entry/profile suppliers/Main/all game routes remain OPEN. All sources before builds/tests/acceptance; no native/C++/Lua/codec/API/DB/SQL/runtime/deploy. Prior sealed2336 members and before1320 preserved. See research/native-world-transport-host-composition-20261009.md.

## 第186輪：原生觀戰請求来源串接

台服 typed C2S6E 實際 source 以相同主機已登記 Session／完整 Lease／私有 Token，接入必要 WorldOwner 單次 execute、actual post phase／battle generation／root／saved position 核對及有序 encrypted replies。新 chat＋spectator＋remaining overload 預先拷貝整批 requests，保留原分派順序；同 Context factory 與實際 WorldRecordSource／plan／Application install_records 傳遞 typed framing flag，舊來源預設 false。D0 僅精確只讀 view，不是已完成S2C發行者；CN獨立原圖補上 D0／CD→UI→C2S6E限定證據，方向／phase不混。真正權限、target namespace／current battle identity、完整回覆與Main供應者仍OPEN。3new＋9modified C++，來源177→178，新增opcode／phase／完整玩法路徑0；分母與百分比null。fresh before1325及前輪2286封存成員保留，未測試／建置／執行／DB存取／部署，未重試155停止链路。全TW-CN-web、共用64位數值、stack99、共用表、字體轉換與凍結功能目標不縮減。見[第186輪](research/tw-native-spectator-record-source-20261009.md)。

## 第187輪：同一世界主機的原生觀戰發送紀錄

完整供應的 CD／D0 經同一 presence／transports 的真正台陸 held queue，true local release 後保留不可變歷史；同 Context factory 將 exact recipient／private Token 的實際觀察接入台服 typed6E Scope。弱永久 receiver／WorldOwner 與強 pending callbacks 保留正確生命週期；失敗使用預備 view，精確 retire／remove 不清理共用或後繼連線，私有 absence lineage 不 wrap。Missing／Retired／Unavailable 是負事實，Published 不等於客戶端收到或遊戲權限。TW F7重設模式2不證明模式1觀戰視窗世代，A3／CB body1 是保存 this 指標高位，不是nonce。3new＋8modified C++，來源178→179，opcode／phase／完整玩法新增0，全遊戲分母與百分比null。真正視窗與目標發行者／身分映射／battle membership／完整回覆／Main及其餘路徑仍OPEN；既有CUSTOM Battle不冒稱CN原生權限。先全部来源串接再集中驗證；TW-CN-web、64位元、stack99、共用表、原生字體與繁簡轉換／凍結功能目標保留。fresh before1333／前輪2377封存成員／三代理原件及報告保留，沒有建置／測試／native／codec／DB／SQL／部署或155停止鏈路重試。見[第187輪](research/native-spectator-ui-publication-source-20261009.md)。

## 第188輪：共用觀戰目標身分與陸服typed6E入口

真正已釋放D0操作數連到明確供應的核心Target／Issuer及其世代，以同一host的presence／transports／publication保留exact私有Token與UI lineage。相同context須同Target物件、weak ownership及世代，衝突Ambiguous，負狀態是觀察不是權限；沒有官方命名空間或WORD→common64 ID猜測。台服typed Scope與同Context factory使用可選exact目標來源；陸服新只讀logical9 C2S6E經既有Gameplay整批split／dispatch接入單次真正execute與actual held logical replies。CN首次ready請求才保存私有Token；post-release／取消不重試已發前綴，child只清理自身。只有D0 UI來源證明WORD，其他mode1 context保留完整DWORD，mode2/context0及12018 input latch不是battle權限。5new＋8modified C++＝13檔，來源179→180；newopcode／phase／完整雙向玩法新增0，全遊戲分母與百分比null。18native spans801B中14new bounded547B／4retained254B，並非18完整封包；真正native issuer／battle membership／rules／replies／Main／WebC56／其餘全遊戲仍OPEN。before1341及前輪2428封存成員／三代理原件／四原始與四最終報告保留；不建置／測試／執行／DB／部署，不重試155停止鏈路。完整TW-CN-web、64位、stack99、共用表、原生字體與轉換／凍結功能目標保持active。見[第188輪](research/native-spectator-target-identity-source-20261009.md)。

## 第189輪：台陸原生觀戰關閉與精確UI退休

本輪另完成網頁端 CN C35 陣形／primary skills／F1..F5 item shortcuts 來源交接 ACK，四份原件完整保存。既有服務端僅有 S86/5 gate 與 scalar projections，尚缺真正 C2S35 request／handler／戰鬥與grant權威及回覆；接續優先從獨立原生 producer 與實際輸入鏈推進。C56、S2C world35及TW CUSTOM保持分開；原件與ACK不計入完整玩法增量。UI退休 capture 仍要求原發行view current，後續revision的真正issuer reissue亦保持OPEN。

A3／CB各logical2、body保留saved incoming this最高BYTE；TW128B完整helper只保留187，CN獨立完整4A1DA0..4A1E16 118B加4限定caller區173B，6spans419B不等於6封包。兩版typedClose接到獨立必要CloseOwner／單次execute及原順序native回覆；Close Scope使用actualUI，target=nullopt，不假造context0，不自動離開戰鬥或發ACK。TW close旗標獨立於6E，經sameContext factory→OtherBinding→Source→Plan→Application→Session parser；CN真正Gameplay split／dispatch取得實際close_ingress。目標源以先capture exact private Entry UiRetirement、再retire(ticket)處理原UI，common/pub釋放後仍不能誤退後繼entry；不加tombstone或改budget。2new＋17modified CPP＝19檔，來源180→181；TW parser63→65，reviewed42不增加，新A3／CB列未完成，局部64.6%不是全遊戲。已知TW/CNC2S各156、TWS2C length252、CNS2Cphase280，newopcode／phase／完整雙向玩法0，分母／百分比null。真正UI發行者／核心操作／battle權限／完整回覆／Main／WebC56／全遊戲路徑仍OPEN。freshbefore1351、前輪2437封存成員與原件／報告保留；不build／test／native／C++／Lua／API／codec／DB／SQL／部署，不重試155停止鏈路。完整TW-CN-web、64位、仙幣99999999999／stack99／共用表／原生字體與轉換／凍結功能及全源串接後集中驗證目標保持active。見[第189輪](research/native-spectator-close-record-source-20261009.md)。

## 第190輪：陸服原生戰鬥35到實際遊戲輸入

獨立CN582f producer logical17／body16，完整1268B producer與253B item caller及兩個限定caller共4spans1596B；type switch9DWORD36B另屬data。新的readonly Request完整保留raw／unknownkind／padding／operand，raw_target_field在特殊skill-kind2分支是2WORD而非通用mask，80續送不當通用duplicate。SharedWorldGameplay實際Sources／initialize／split-copy／ordered dispatch接入新BattleCommandSource；strong操作receiver、lazy原私有Token、完整root／position前後current、once execute及原CN held logical replies／late prefix／exact own cleanup均接上。真正battle／actor／context issuer／grant／rules／MP／item／formation／once settlement／完整reply與Main仍OPEN，沒有guess success或借TW CUSTOM。3new＋2modified CPP共5檔，來源181→182；newopcode／phase／完整雙向玩法0，分母百分比null。freshbefore1358、整prior1892537members、actual originals／intermediates／兩代理與報告保留，不build／test／native／C++／Lua／API／codec／DB／SQL／部署或155停止鏈重試。完整TW-CN-web、64位元、仙幣99999999999／stack99／共用表／原生字體轉換／凍結功能與先全源串接再集中驗證目標不縮減。見[第190輪](research/cn-native-battle-command-source-20261009.md)。

## 第191輪：陸服戰鬥整組輸入與原生context來源

有界完整有序C35 group接到真正必要Authority.prepare／current／execute_group：Append只保存並使用explicit intermediate Reply，Single／Final才真正整組callback一次；不單靠kind80分組或猜成本／ACK。Scope攜原私有Token與完整共同root／position，opaque Receipt保持實際結果，Stage外once release hook與callback退出清理只退休自身pending。Gameplay明確選用grouped或direct owner，再交既有ordered Source，Main／真正native權威規則／成本／replies仍OPEN。獨立CN S82 logical9的實際同一T pointer追到battle owner3C／40、再連190 C35 reader；新readonly82不是BattleID或grant，S86 absentbits不清歷史。3new＋4modified CPP共7檔，來源182→183；newopcode／phase／完整雙向玩法0，全遊戲分母／百分比null，958端點行不是分母。freshbefore1365／prior1902295members及三代理原件／四原始四最終報告另封存；網頁v12／更新契約另存新epoch，不改189／190。先全源串接再集中驗證，完整TW-CN-web／64位元／仙幣99999999999／stack99／共用表／原生字體轉換／凍結功能保持active，不build／test／native／API／codec／DB／SQL／部署或155停止鏈重試。見[第191輪](research/cn-native-battle-command-group-source-20261009.md)。

## 第192輪：陸服戰鬥技能與道具資料來源

Actual C35完整有序請求接入SharedWorldGameplay明確data configuration→SharedNativeBattleCommandData→既有Groups→Source。真正共用CN catalog lookup／完整110B definition view與必要InventorySource完整36B dictionary snapshot串接，catalog/store lifetime必須在borrowed read前由真正權威qualify；beforeimage／actual Result Current保留，不偷偷rebase。技能0x03／0x17（decimal23）及特定continuations0x83／0x97依原bytes核清，歷史簡寫不改；道具05／0C high signedslot／lowWORDitem保留，getter38／updater50／bag30／stack99分開，slot30..37選中29的原生edge不作ownership修正。4new＋2modified CPP共6檔51879B，來源183→184，newopcode／phase／完整雙向玩法0，958endpoint rows／28source groups非分母，百分比null。Skill新增3complete445B／retained1318B，Inventory新增2complete121B／retained1793B，不當封包完成數。真正學習權／custody／battle issuer／actor／target／formation／rules／cost／once settlement／replies／Main及全遊戲仍OPEN。已向授權webpeer回傳本輪服務端ACK，完整保存v3.1與runtime v6／契約新epoch；manualequip0C無C28，generic C28仍OPEN。freshbefore1373、prior1912448封存成員、三代理與六CPP原件／diffs及四原始四最終報告保留。沒有build／tests／native／C++／Lua／API／codec／DB／SQL／runtime／部署或155停止鏈重試；完整TW-CN-web／64位／仙幣99999999999／stack99／共用表／原生字體與轉換／凍結功能／先全源串接再集中驗證目標active。見[第192輪](research/cn-native-battle-command-data-source-20261009.md)。


## 第193輪：陸服選中技能列表接入戰鬥命令資料

真正原始primary/secondary清單與signed選中index／actual指標／完整110B技能定義，经readonly SkillSelection→concrete SelectionSource→explicit optional DataBinding→既有必要DataAuthority／Groups／Source串接。完整快照保留原WORD bit14/15与bank112656（資源4B header分開），Same bank不證明same actor或learned rights；可選native recovery不是存取玩家client memory的正式runtime要求。factory不讀DB，actual store lifetime先由DataAuthority限定；原選擇保留，失敗不equal-key fallback／重讀rebase。Native refined expected地址由owned scope計算，初版与diff保留。3new＋3modified C++6檔58465B，來源184→185；newopcode／phase／完整雙向玩法新增0，958endpoint rows不是分母，百分比null。清單17spans2110B含new complete922/new bounded317/retained871；subject另new382B／retained1075B，只確認552870／553220 call前沿与16group100WORD清bit15，未恢復learned materializer。真正battle／actor／learned／context／grant／cost／once settlement／reply／Main與其餘全遊戲仍OPEN。新的授權web v4.1/runtime v8交接保存與source ACK：特殊kind2/effect非FF5的C35 offset5是兩WORD位置與255sentinel，普通mask分開；私有client token／送出後回位不是權限，secondary仍OPEN。三代理current/context完整copy及seal保留；source原總數77漏readcontext4另附81更正，不覆寫旧seal。before1382／prior1922472 members／六CPP全文diff与四原始四最終報告保留；不build／test／native／C++／Lua／codec／API／DB／SQL／runtime／部署或155停止鏈重試。完整TW-CN-web／共同64位數值／仙幣99999999999／stack99／共用表／原生字體及繁簡轉換／凍結功能／先全源串接再集中驗證修復發布目標active。見[第193輪](research/cn-native-battle-skill-selection-source-20261009.md)。


## Round194 CN native battle skill publication source

Actual deferred S87 directly calls554750, not54DEF0. GUI552870/553220/552CB0 and5540B0/5545C0 do not materialize learned rows; prior193 historical frontiers remain immutable and this current correction is additive. Standalone readonly logical3 typed87 preserves fullWORD bit14/15/kind/ID; original deferred table and externalstaticassert/getter stay distinct from grants. Actual postcommit Plan/fullshared110B definitions connect samepresence/transports/catalog/lifetime/originalLease/privateToken/fullroot/position to optional Gameplay-bound publisher and existing real held queue. Before/after pure necessary WorldOwner qualifies actual learned/save/replay/battle/list/nativeprofile; genuine issuer/rules/grants/cost/fullreplies/Main still OPEN. PreparationStage ends before real send, approval owns Stage, and actual true local release history survives throw/cancel/current failure without replay or fabricated ACK. Six CPP3new+3modified; source185->186, opcode/phase/fullroute increment0, whole-game denominator/percentage null. Native12spans1164B all retained; history new complete54CFF0 wrapper49B incomingphase OPEN, six retained438B. RootcompleteC6 plus newwrapper/all19instructions, complete6source definitions/diffs, before1390/prior1932605members and threeagent original epochs/seals retained. No build/test/native/C++/Lua/codec/API/runtime/DB/SQL/deploy or155/52F330/52F170 retry. All TW-CN-web gameplay, common tables,64bit explicit wire/object/display, coin99999999999 only/stack99/nativelevel/fonts/conversion/frozenfeatures and source-first then comprehensive tests/repair/release goal remain active. See research/cn-native-battle-skill-publication-source-20261009.md.


## Round195 native learned-skill owner and storage frontier

Research only: CPP0 and source186 unchanged; opcode/phase/full bidirectional route increment0, whole-game denominator and percent unknown. Actual same P/call/epoch qualifies R=P+1478084, H14=R and H20=U=P+89B26C; bundle base EBP-A18 makes EBP-A10 slot2 and loaded EBP-A0C slot3/H24. Initial misindex and full corrected epochs are retained. Mode0 attaches U430A8=R90; mode1 does not reattach. Native addresses are not common actor IDs, learned ownership or casting grants. Three exact non-GUI getters5537E0/553810/553B40 add117B within explicitly compared193/194 manifests;16 other subject spans1405B and three list spans636B are retained coverage. Existing selection snapshots already preserve the fields; no equivalent interface added.

Actual TW character_deities raw S34 persistence has fixed TW provenance and CUSTOM0039 policy; owned revision/CAS/transaction infrastructure and shared native catalogs can be reused, but raw membership/custom/test labels are not CN learned authority. Next trace genuine common actor/subject identity, learned commit/event/replay, independent86/87 full ordered history, actor/context/target/range/cost/formation/once settlement/native replies and real Main suppliers. WORLD34 does not automatically populate battle87. New web commands v5.1/runtime v9 hashed source epochs and authorized ACK are saved; resource/input lifecycle facts do not become server grants or joint gameplay acceptance.

Fresh before1398/full prior1942562 members and three completed sealed agent deliveries preserved. All TW-CN-web gameplay, shared-table defaults and concrete _tw/_cn exceptions, common64 plus explicit wire/object/floating text, coin99999999999 only/qualified stack99/native level/fonts/conversion/frozen features remain active. All connections precede comprehensive tests/repair/recovery/release. No build/test/native/C++/Lua/codec/API/runtime/DB/SQL/migration/deploy or155/52F330/52F170 retry. See research/cn-native-learned-skill-owner-frontier-20261009.md.


## Round196 same Application shared skill reader and actual event frontier

Five existing source definitions modified, CPP0new/5modified; same SqliteDatabase NativeSkillCatalog reader now flows to TW Context/source factory/exact Owner::same and CN explicit ref constructor/private pointer implementation/Controllers Context/source factory. Old constructors and aggregate absence remain null; no query/import/CN provider/default plan/learned grants. Source186->187, opcode/phase/fullroute increment0, whole-game denominator/percentage unknown. Actual CN453 source/store/provider/current qualification and genuine learned/core/cost/rules/Main remain required.

WORLD30 retained existing-row reset clears only skill count after capacity check and staging inactive slot.34append/35pointerflag3, independent87 active list/row5C/60, WORLDrow1F0/258 and mode1 nonreattachment stay separate. History6spans1621B and Native9spans1369B all retained; literal123B new bounded extraction is already contained in full195PE, not newcode/opcode. DebugGodUpdateSkillLevelUp belongs34/4D5E60; wrong35 descriptive epoch/correction preserved.32name/33row40/initclear and boundedGUIsender candidates are not acquired/removed skill transactions. Existing native effect/view definitions reused, no duplicate reader.

Concrete preborn81 staging/83 single apply still lacks real mutation supplier. Actual store_deity and inventory-resource debit commit separate transactions; sequential calls cannot be claimed atomic learning/book-consume/event/replay. Next actual native acquisition/custody/subject mapping/rules must feed ONE concrete committed store outcome, independent WORLD/battle ordered output, grant/context/target/range/cost/formation/once settlement/full reply/Main. Freshbefore1403 and entireprior1952611 members preserved; five full C++ originals625027B/diffs and three agent source/initial/corrected epochs sealed. Newpeer ack195/v17/runtimev10/commandsv6 exacthashes/currentcontract preserved;196 sourceACKsent with no jointplayability.54F360 primaryrefresh versus5510300 formationclose andFightEnyWORD4 metadata versusserverstats/grants remain separate. Current regular-file census and peer recursive-stat without resolved dedup are distinct saved scopes; large new outputs remain outside project.

AllTW-CN-web gameplay/complete phase-state-variant denominator/shared tables/_tw/_cn exceptions/common64 explicit wire-object-floating text/coin99999999999 only/qualifiedstack99/nativelevel/fonts/conversion/frozenfeatures remain active. No build/test/native/C++/Lua/codec/API/runtime/DB/SQL/migration/deploy or155/52F330/52F170 retry; all sources before comprehensive tests/repair/recovery/release. See research/cn-native-learned-skill-event-frontier-20261009.md.


## Round197 explicit pinned CN skill definitions on the actual shared reader

Two existing C++/header definitions changed. Explicit SharedServerPlan native_skill_definitions binds all453 declared CN definitions on the exact Application shared SQLite reader before constructor-time controllers factory; qualified catalog is strongly held in State through controller/connection destruction and passed by Context shared_ptr. Factory completion/listener start/credential entry observe native-resource Current; legacy null remains absent. Read-only binding is not an atomic whole-DB snapshot or extra-row count, and Current is not a shared DB epoch. Future lookups still qualify exact rows; Application owns reader/connection through real game drain. No implicit import, TW fallback, learned grant or Main activation.

Source187->188, newopcode/phase/complete bidirectional routes0, whole-game denominator/percent unknown. Three agents retain bounded complete source copies for provider/store/host owner and credential exception boundary, with independent immutable follow-up context for the already sealed store delivery. Native inputs/code increment0; no redundant PE/history restore. Genuine native learned identity/rules, ONE same-store skill/book/durable-event transaction, independent world/battle histories, complete replies and real Main suppliers remain OPEN. All TW-CN-web/gameplay/shared tables/common64 explicit wire-object-display/coin99999999999 only/stack99/native levels/fonts/conversion/frozenfeatures remain the objective. No builds/tests/native/C++/Lua/codec/API/runtime/DB/SQL/deploy; all sources before comprehensive tests/repair/recovery/release. See research/cn-native-shared-skill-supply-20261009.md.


### Round198：原生技能書分支研究完成，依使用者指示暫停

386本CN SKB：367本背包直送C25，19本modal3B確認；快捷欄走C26。
C25尾端是原DWORDarg高BYTE別名，第三arg未使用；C26最後BYTE未寫入。
真實學習、扣書、共用subject/current issuer及單一持久交易/完整回覆仍OPEN。
已保存限定原生來源及共用儲存研究；C++変更0、source段仍188、新完整路徑0。
全遊戲分母/百分比仍未知；TW42/65=64.6%僅解析opcode來源分支審閱。
本輪結束後停止，不啟動下一輪。下次需使用者明確恢復後接modal3B真正確認送包。
報告：docs/research/cn-native-skill-acquisition-frontier-20261009.md。


### Round199：使用者恢復，真正modal3B→C25與獨立ready1F來源接入

原始event/flags/index/table/operand已限定；3B→saveditem/slot→C25 raw5，
再條件式C1F raw2{1F,00}，不能當學習ACK或初始bootstrap1F。
新增3份、修改4份C++來源：lossless request、exactowned SKB item lookup、
realOwner/current/store lifetime/fullnative queue來源、Gameplay完整split/dispatch/cleanup。
source段188→189，真學習/扣書/durable event交易與Main選擇仍OPEN，新完整路徑0。
全遊戲百分比仍unknown；TW42/65=64.6%僅審閱分支，沒有本輪測試/建置/部署。
使用者恢復取代198輪stop指示，目標保持active。下一項：實際共同subject、
learned/book custody/single durable mutation owner與ready1F原生全回覆。
唯一報告：docs/research/cn-native-skill-confirmation-frontier-20261009.md。


### Round200 concrete source increment (2026-10-09)

Pinned CN386 SKB raw source now has explicit same-connection shared source schema/import and item/index reader source; TW381/mandatory396 parsed projection remains frozen. Source segments189 ->190, new complete routes0, full-game denominator/percent unknown. Ready1F is a multi-caller window-gated control, not a proved learning/bootstrap ACK. Definition67/42 condition and6B prompt/arm condition remain separate client facts; next trace actual inline430A8+64 supplier and current learned/custody owner for authoritative mutation and native replies. No SQL/build/tests/runtime/native/codec/deployment in PHASE1. Evidence: docs/research/cn-native-item-control-source-frontier-20261009.md and cn-native-item-control-source-frontier-01; endpoint-catalog200. Root goal active, bounded agents stopped200.


### Round201 concrete source increment (2026-10-09)

Actual same-store CN386 SKB source binder is now connected to selected C25 request composition, with owned native+stored rows and real store/lifetime/current fences. Source segments190 ->191, new complete routes0, no new opcode/phase binding. WORLD24 original17-byte raw DWORD view and selected actual auxiliary prefix/source fields preserve stale data; neither grants learning/battle rights. No builds/tests/native/SQL/DB/runtime/codec/deploy. See docs/research/cn-native-shared-book-request-source-20261009.md and endpoint-catalog201. User requested stop after NEXT round: finish201, then202, pause goal and stop agents, never start203 until explicit resume.


## 第202輪來源與使用者指定停止點

# 第202輪：陸服原生 WORLD24 數值發布來源

本輪新增 `SharedInlineRoleCountersPublication.h/.cpp`，並修改 `SharedWorldGameplay.h/.cpp`。來源串接由191增至192段；新增完整雙向玩法路徑0，全遊戲分母及完成百分比仍未知。依使用者「下一輪結束後停止工作」，第202輪封存完成後暫停目標模式，不開始203輪。

實際增量是：已持有的原生17位元組 WORLD24 → 實際共用世界收件者及原始登記 token → 真正提交後事件的唯讀權威判定 → 原有 held publication queue → 保留實際本機釋放事實。這是來源接線，尚未有正式 Main 選定的具體事件 issuer，不是已完成數值玩法、部署或客戶端驗收。

原生依據沿用第201輪固定雜湊的陸服 EXE：WORLD cell 00492A68 → 004912E8，以 packet+1、mode0 呼叫 00518F70；length cell 00567D34 → 00567B9A 返回17。四個 DWORD 順序為 inline-role +5C/+64/+60/+68。原生封包沒有 actor/subject ID。四值維持未知語義，不標成 HP/MP，不當成 C1F 或 C25 的回覆，不把原生 DWORD 宣稱為已完成64位元數值擴充。

新發布來源只接收完整且已持有的 `CnInlineRoleCounters24` 記錄，不以截斷64位元值、猜測編碼、零資料或成功回覆製造輸出。發布持有真實原連線；第一次實際 ready 發布才取得既有 registry 的私有 token，後续操作固定同一登記世代。實際 WorldOwner 必須確認共用事件、保存、持久重播、提交版本、角色與 inline-role 關係、全部原始數值及順序。單純 record 的值、client pointer 或相同 lease 不提供權限。

BeforeQueue、BeforeRelease、AfterRelease 都保留相同角色、存檔位置及登記 token，且在真正權威觀察前後重新確認。原始 bytes 在觀察前完整複製；事件與提交版本不得為0；記錄數及總 logical bytes 有明確來源預算。局部 last-attempt 僅避免本機立即重複，不代替共用持久事件重播。

準備觀察與實際佇列批准使用獨立 nonreentrant stage。同步完成、取消、晚到完成及 throwing send 保留實際傳回true的本機釋放事實；發布前預先配置兩種 receipt，釋放後不為 receipt 配置記憶體。AfterRelease 不再有效時，保留已釋放 receipt 並標示 post-release current=false。這不表示網路送達或原生客戶端接受。

靜態審阅發現既有 CnTransportSession::complete_send 在 game callback 前套用 accepted && !closing。因此 strand 已釋放、但 callback 前 close/drain 的情況可能回傳false。新來源保留此既有契約，不擅改登入、運輸或其他發布者：只有傳回true是確定的局部釋放；false或沒有receipt代表釋放狀態未知，不能當作「沒有送出」或重送依據。完整 released-then-closed 事實仍缺單獨的來源介面；共用持久事件恢復由真正issuer負責。

SharedWorldGameplay 只在實際1C初始發布內綁定可選來源。compose 要求相同 presence/transport registry，不發啟動資料、不替代 bootstrap、不安裝不存在的權威。來源隨拒絕、terminal、destructor 取消自己的 pending；不釋放共用 token 或寫入 common state。既有 C2S 格式/分派及 roster31/34/35、C1F、C25 維持原樣。

尚缺：具體共用角色數值事件與提交/持久重播 issuer、四個 DWORD 的完整來源語義與跨版 mapping；技能書扣除/學習的權威 mutation、原生初始技能主清單及世界到戰鬥清單來源；完整 TW/CN/web 路徑盤點與64位元/堆疊99擴充。所有路徑打通後才全面建置、測試、修復及發布。

現有盤點：TW/CN C2S 觀察聯集各156；TW 世界 S2C 長度支持252/256、戰鬥分派110；CN S2C 階段條目280（帳號6／世界206／戰鬥68）。TW world parser 審閱42/65，64.6%只代表該範圍審閱。958端點索引、38條未正式host的部分owner鏈、CN93個/TW10個來源phase binding都不能加總成完整遊戲路徑分母。

本輪只做靜態原始碼及來源封存。沒有建置、測試、執行codec/native/server/DB/SQL、遷移、部署或原生驗收；帳號存檔、客戶端、原生字體、繁簡轉換與凍結功能保留。

封存此輪後呼叫目標暫停；停止子代理，不開始第203輪，等待使用者續行。


## 第203輪來源及五輪停止指示

# 第203輪：陸服世界主技能清單與同庫來源

第203輪是使用者這次續工五輪中的第1輪。依「從本輪開始算起，5輪之後結束並停止工作」，第203至207輪完成後暫停，不開始208輪。第202輪停止點已完成並保留歷史；本輪因使用者「繼續工作」恢复active。

新增 `CnWorldPrimarySkillSource.h/.cpp`，修改11份C++來源，新增1段來源串接，累計193段。新增完整雙向遊戲路徑0，完整遊戲分母與百分比未知。本輪不建置、測試、執行native/codec/server/DB/SQL、不遷移部署。

原世界主技能解析器只有 bank pointer+4、group6E04、record110 的指標幾何，再查共用目錄；沒有比對原指標位置的實際bank。新可選來源持有完整 actual selected snapshot、完整112656B bank payload及強原生目錄，在任何外部 observer 前複製原始输入。bank address必須等於實際subject保存的bank，且整段payload與釘定resource去除4B檔头後逐byte相等。按原主清單順序匹配每個實際pointer、完整110B record、source、offset、hash，保留flags、重複與順序；不拿row+5C/+60 auxiliary當primary，不生成pointer，不读取客户端process memory。

共用 `CnSharedSkillCatalog` 現在保留實際store的強生命週期owner及必需StoreCurrent。每次原生來源callback、借用SQLite讀取之前及之後都需先由真正store owner确认同一reader、native provider、store lifetime、population及epoch；resource SHA/Current不代替DB Current。既有453筆驗定義流程及所有lookup經過nonreentrant guard，捕捉到nested reentry也不可復活；已匹配定義的共享列缺失/腐壞會使該來源失效。這是必要來源接線，不是自動取得資料庫所有權或新實際schema/data。

SharedServerPlan對顯式native_skill_definitions新增必需native_skill_store_lifetime/native_skill_store_current，唯一原生host bindcall同步傳入；只有store資格而沒有native definitions被拒絕。未選定該opt-in的舊來源不添加讀取，也沒有任何默認非擁有marker。真正Application store owner必須仍由實際配置提供；Main沒有因此變成完整可用的正式遊戲owner。

WORLD primary來源接入 `CnPrebornSkillReferences` 與 `CnPrebornSkillChoiceSource`，強來源路徑逐整筆比對shared/native definition。窗口Source可選read_primary_skills；選定後缺少subject、supplier返回null或不一致都拒絕，不回退舊幾何路徑。沒有選此額外證據時，原幾何推算保留未知bank身份，不能宣稱已驗明actualbank。own-server共同operation本身不要求native記憶體。

prepare/issued/current/selection各階段持有同一完整Window及強Primary，回呼之前複製Scope/Selection/Window並拒絕nested reentry；true callback即使吞掉重入錯誤也不能復活已terminal窗口。發布轉交Choices前結束本source觀察stage，允許合法來源prepare。apply把原生bank scope與完整entries/flags定義保存為owned Facts，再退休原窗口執行真正一次共用operation；postcommit delivery只交retained provenance，不問過期precommit Current。沒有新增default學習、扣書、common技能identity、資格或原生成功回覆。

子代理新增127B/34個原生指令位置：493FC0完整70B為真正whole-row reset；4927FC呼叫端57B明確傳R=P+1478084，ECX另為P。R+164=0、R+15F=FF、R+160=0，memset(R+168,0,3EC0)清16個完整3EC列，同時清主技能count/flags/pointers及aux。之後獨立inventory reset不是技能grant；WORLD CF success分支後的C1F/C23沒有證明技能學習或回覆因果。旧116B初始化context保留不重算。這與WORLD30只清primary count、可能保留aux stale state的生命週期不同。

正向初始主清單供應、WORLD→battle primary填入、真實common actor/learned/custody、技能書扣除與持久事件/交易及原生回覆仍待接。下一個具體原生data leaf為4D2B50的primary pointer ordinal lookup，僅會員查找不當writer/grant；將接著沿實際非GUI寫入端追源。帳號存檔、client EXE、原生字體、繁簡轉換、等級與凍結功能維持。

現有盤點未變：TW/CN觀察C2S聯集各156；TW世界S2C長度支持252/256，戰鬥110條分派；CN S2C階段条目280（帳號6／世界206／戰鬥68）。958個端點索引與193段來源不是全遊戲完成路徑。TW解析分支審閱42/65＝64.6%，僅限這個範圍。完整遊戲完成百分比仍null。

本次由203算第1輪，完成203至207共5輪後暫停；本203仍active，不開始208。


## 第204輪來源及五輪停止指示

# 第204輪：CN 原生主技能第一筆序號來源

本輪是使用者指定203至207共五輪中的第2輪。目標繼續active，207完成後暫停並停止子代理，不開始208。只做靜態原生恢復與來源串接，未建置、執行原生、測試、操作DB／SQL或部署。

原生004D2B50的93-byte純資料leaf從UI+430A8取得role，再取role+D0選中row。一次讀取row+1F0的BYTE count；按row+258的DWORD指標原始順序比較definition BYTE1／BYTE0零擴展值與兩個完整DWORD參數，回傳第一筆0-based ordinal，沒有符合則-1。沒有flags過濾、去重或上位bit截斷。缺少role或selected pointer也回-1；現有完整bank來源必須已取得真實選中row，沒有把缺失row製造成empty成功。

004DA630的type2實際資料caller保留兩段179B。mode0與mode1使用不同表，kind／id是signed WORD符號擴展為DWORD；mode1還使用selected signed BYTE作表索引。負數或含高位值不能以截BYTE替代成合法技能。首筆匹配之後另送004D3B60 gate；首筆gate失敗不能改找後面的重複項目。沒有進入formatter、GUI、render或該gate內部，本輪不將member lookup當learned／cast權限。

CnWorldPrimarySkillSource新增find_actual_primary_ordinal，對已完整擁有、與釘定資源逐byte相符的選中row／bank來源執行相同first-match資料投影。入口及返回都要求實際Current，重入／Current失效終止；外層null表示資格失敗，合格結果的內層無ordinal表示原生-1。使用完整uint32 kind／id，保持original order／duplicates／flags；ordinal轉uint8由既有完整row指標幾何界線保證，沒有新增遊戲等級或技能數上限。

既有CnPrebornSkillChoiceSource只有在選用actual primary supplier時，才保存每個retained word高／低byte對應的owned ordinal facts，並由既有prepared／issued選擇來源交給共用操作輸入。這是明示的word投影，不聲稱該word來自004DA630的mode table，也不取代native filtered offer、書籍來源、server entitlement或downstream gate。缺supplier仍未知；選用supplier後Current失敗拒絕，不退回geometry／同key目錄來冒充成功。owned facts跨commit保留，沒有事後重用舊Current作權限。

本輪修改4個C++來源檔、新增來源區段1；累計來源區段194，新增完整雙向玩法路徑0。既有帳本歷史、完整203封存與代理原始來源保留，root／catalog204另存全檔SHA與有界原生bytes。未更動帳號存檔、原生EXE、字體、繁簡轉換、native等級或凍結功能，沒有啟用Main實際來源。

| 範圍 | 本輪結束數量 | 說明 |
|---|---:|---|
| TW C2S 已觀察opcode聯集 |156|151 generic＋5 supplemental，不是完整玩法分母|
| CN C2S 已觀察opcode聯集 |156|本輪沒有新增opcode|
| TW WORLD S2C 長度表 |252／256|230固定、22變長、4 unsupported；不是完成路徑|
| TW BATTLE S2C 索引 |110|9 special、101 default；83 action23、86 selector7|
| CN S2C phase entries |280|account6、world206、battle68；phase entry不是全遊戲去重總數|
| CN receiver contexts |14／12已具體限定|47DE70、4812B0仍unknown|
| TW WORLD parser review |42／65＝64.6%|僅這個固定parser範圍的review比例|
| partial owner chains |38|CN35＋TW3，仍非完整route|
| endpoint rows／source groups |958／28|不作可玩百分比分母|
| partial source segments |194|193→194|
| 本輪新增完整雙向route |0|沒有把readonly projection算完整gameplay|
| 全遊戲完整路徑總數／完成百分比 |unknown／null|方向、狀態、變體、deferred總表尚未完整|

下一個精確來源是004D3B60的非GUI ordinal gate，以及原生主清單的正向寫入端。真正common learned actor、owned book custody、扣書、儲存／durable event與原生回覆、WORLD→battle materializer、實際store lifecycle與Main issuer仍待串接；64位數值／99重疊與TW／CN／web整體雙向玩法也仍待接。全部來源打通後才集中全面測試與修復。停止點維持207。

本次由203算第1輪，本204為第2輪，完成203至207共5輪後暫停；本204仍active，不開始208。


## 第205輪來源及五輪停止指示

# 第205輪：CN 主技能第一筆序號的原生資料條件

本輪是203至207共五輪中的第3輪。目標仍active，207完成後暫停並停止子代理，不開始208。本輪是靜態原生來源與C++串接，沒有建置、測試、原生／codec／runtime、DB／SQL操作或部署。

004D3B60的完整67B純資料leaf已由第200輪保存，今輪保留原件与精確原始SHA，不重算新恢復bytes；004DA630的第204輪type2 caller68B也保留。今輪new bounded native bytes為0，retained為135B；新增的是此前未接入共用操作輸入的Current-qualified firstlookup→gate來源。

原生gate先讀UI+430A8的role再讀role+D0，沒有role-null guard。只檢查selected row不為null、ordinal為signed nonnegative、row+258+4*ordinal的pointer不為null；不檢查count、flags、bank或Current。之後要求definition BYTE67非零，definition unsigned WORD42小於等於role+64的完整unsigned DWORD；unsigned比較包含等號。原生沒有對這些欄位提供server learned/cast權限，欄位玩法語義仍不冒稱MP、耗費或戰鬥能力。

CnWorldPrimarySkillSource新增project_actual_first_primary_gate，把既有完整DWORD kind／id的first physical ordinal投影與這個原生gate連起來。它只接004D2B50→004D3B60的first-match組合，沒有對任意ordinal提供未限定的原生gate。完整owned選中row／bank及Current是獨立来源資格；原生leaf本身沒有這些檢查。第一筆為ordinal0仍正常處理；qualified -1結果變成false，不另尋後面的重複項目。沒有截斷參數、讀auxiliary list或將flags當優先權。

PrimaryGate owns原始lookup、第一筆definition pointer、BYTE67、WORD42、inline DWORD64及predicate。DWORD64由完整角色來源的counter order index1取得，不是selected-row2C／30。這些是已擁有的raw值，native gate在BYTE67為0時不會求值WORD42／counter64，不能把retained數值記錄冒稱原生當次分支已讀。Current在投影前後確認，同source reentry／stale皆終止，外層null資格失敗與合格false分開。

CnPrebornSkillChoiceSource只有選用actual primary supplier才一次投影並保存gate和same lookup ordinal；absence仍未知。保留每個request word的高／低byte投影、原始順序與重複，沒有冒稱它們來自004DA630的signed-WORD mode table。predicatefalse只是owned來源事實，不拒絕UI選擇、不賦予或撤銷common技能權限。只有failed Current才拒絕來源，沒有退回同key目錄或geometry假裝成功。既有Window把owned facts送到實際共用操作／post-commit delivery，不在commit後重用obsolete Current。

本輪修改4個C++來源檔、新增來源區段1，累計195。新完整雙向gameplay route仍為0；實際Main、learned actor、書籍custody／扣除、持久交易／durable event／原生回覆及WORLD→battle primary materializer仍有缺口。未修改原生EXE、字體、繁簡轉換、等級、帳號存檔或凍結功能。

| 範圍 | 本輪結束數量 | 計數範圍 |
|---|---:|---|
| TW C2S opcode observed union |156|151 generic＋5 supplemental／6 branches|
| CN C2S opcode observed union |156|本輪無新增opcode|
| TW WORLD S2C length entries |252／256|230 fixed＋22 variable、4 unsupported|
| TW BATTLE S2C indexed entries |110|9 special＋101 default；83 actions23／86 selectors7|
| CN S2C phase entries |280|account6／world206／battle68|
| CN receiver contexts |14、12有具體限定|47DE70／4812B0仍unknown|
| TW WORLD parser review |42／65＝64.6%|只有這個parser範圍的review比例|
| partial owner chains |38|CN35／TW3；不是fullroutes|
| endpoint rows／source groups |958／28|不是全遊戲總數|
| partial source segments |195|194→195|
| 本輪新增完整雙向玩法route |0|來源predicate不算可玩完成|
| 全遊戲完整路徑總數／百分比 |unknown／null|全方向、狀態、變體、deferred分母未完整|

下一步追實際主技能正向寫入端及4DA630 mode-table來源，不再把既有raw leaf當新發現。共用學習、custody、扣書、save／durable、精確回覆、實際store lifecycle／Main issuer、TW／CN／web數值64與stack99及其餘雙向玩法仍待接。全部来源完成後才全面測試、修復及發布；本次停止點仍207。

本次由203算第1輪，本205為第3輪，完成203至207共5輪後暫停；本205仍active，不開始208。


## 第206輪來源及五輪停止指示

# 第206輪：原生技能更新與完整角色列來源

本輪是使用者指定203至207共五輪中的第4輪。目標仍active，207結束後暫停並停止子代理，不開始208。只做靜態來源串接，沒有建置、測試、原生／codec／runtime、DB／SQL操作、遷移或部署。

004D5E60／004D5CC0對WORLD34／35的角色列遍歷，都會繼續處理所有符合incoming subject BYTE零擴展WORD的列。不是first-roster-only，也不是只改currently selected row。每次續行重新取得role／count；source arithmetic及角色原生識別碼不等共用actor identity。本輪保留196／201的7段資料原始區間814B／233 instructions，新原生覆蓋0，原seal不改。

WORLD34每matching row先要求count BYTE小於100，依原始指標順序比較definition BYTE kind／ID。第一duplicate走diagnostic callsite，之後原生重新讀count；不能猜該回呼沒有副作用。新append寫flag0、bank-relative原指標、count++，page bytes3E8為0、3E9為ceil(count／25)，呼叫pure auxiliary helper。WORLD35用精確bank DWORD pointer找該列第一筆匹配，寫flag3，不移除、去重或調整count；原生沒有35的count100上界guard。兩者subject match會繼續所有同識別碼列。

純004D5830先只清auxiliary count5C，依primary flag bit2把指標抄到60的prefix；保留null、重複、順序及未覆寫的舊尾端。不是把所有auxiliary bytes清零，也不能把任何flag當成common learned／cast grant。assert、diagnostic、selected-row refresh、mode menu refresh及selected35 pending table分支的未知callee／實際資料仍明列缺口，沒有進入UI、formatter或render內部。

新增CnWorldSubjectSkillUpdateSource擁有actual object4508、所有16個完整3EC row（包含inactive／stale內容）、完整112656B bank、原生catalog強生命週期與實際Current。先複製所有borrowed input，再確認actual UI+430A8／object+90、bank身份與釘定payload逐byte一致。來源Scope與server post-commit revision分開；Current失敗永久terminal、caught reentry不能復活，Operation還擁有strong self跨observer，避免外部最後持有者在回呼中釋放this。

project_updates按原始record順序，對每一筆的所有matching rows保存完整before與primary／aux data stage、原生definition及選中／menu／pending表的待補條件。Source只獨立限定captured16-row／100-pointer安全幾何，不宣稱原生有這些guard，也不clip count、造default row或拿同key fallback。34 capacity row直接保存無primary變動；35不安全prefix拒絕qualification。完整bank/source/raw/hash/file offset維持精確來源。

staged continuation是條件式資料來源。當走duplicate diagnostic、append menu refresh或selected35時，requires_unchanged_unmodeled_call_roster明確為true；實際權威owner必須獨立限定未知回呼前後仍是同row／count／role域。Source Current本身不能证明未知callback effects。沒有將這個階段投影冒稱完整原生封包副作用或正向common學習流程。

既有SharedSubjectSkillPublication新增明示的optional actual BEFORE-event source與QualifyNative成對輸入；任一邊缺失便拒絕，不fallback。原mandatory common post-commit Qualify仍保留。輸出前將每筆projected definition和same-store CnSharedSkillCatalog的actual source、kind／ID、raw、hash及offset完整比較。immutable projection及strong source穿過BeforeQueue／QueueAccepted，並要求實際native-stage qualifier涵蓋所有匹配列與未知診斷／UI／pending表／rebindings。沒有default issuer、沒有Main啟用、沒有由檔案來源冒出技能權利。

本輪新增2個C++檔、修改2個，來源區段195→196；新完整雙向玩法route0。CMake既有recursive source配置涵蓋新cpp，未執行建置。初版new2及修訂前publisher header確有全文read但沒有實體全檔snapshot，審查明列缺失；existing pub2的before原件與final4來源均完整保留，不重建初版或冒稱所有epoch齊全。所有歷史client／native／source seals原樣保留。

| 範圍 | 本輪結束數量 | 計數範圍 |
|---|---:|---|
| TW C2S observed opcode union |156|151 generic＋5 supplemental／6 branches|
| CN C2S observed opcode union |156|本輪無新增opcode|
| TW WORLD S2C length entries |252／256|230 fixed＋22 variable、4 unsupported|
| TW BATTLE S2C indexed entries |110|9 special＋101 default；83 actions23／86 selectors7|
| CN S2C phase entries |280|account6／world206／battle68|
| CN receiver contexts |14、12具體限定|47DE70／4812B0仍unknown|
| TW WORLD parser review |42／65＝64.6%|僅這個parser範圍的review比例|
| partial owner chains |38|CN35／TW3，非完整routes|
| endpoint rows／source groups |958／28|非全遊戲分母|
| partial source segments |196|195→196|
| 本輪新增完整雙向玩法route |0|native data stage不算完整玩法|
| 全遊戲完整路徑總數／百分比 |unknown／null|全方向、狀態、變體、deferred inventory未齊|

下一輪把這份原生stage接到combined ordered roster publication，遇30／31／32／33／39等介入時要求實際state checkpoint，不能從目前selected row或未知callback推斷；原生UI／diagnostic完整effects及真實common learned／custody／扣書／save／durable／精確native reply／Main issuer／WORLD→battle materializer仍待接。TW／CN／web完整雙向玩法、64位數值與stack99亦未完成；全部來源打通後才全面測試及修復。下一輪207為本次最後一輪，結束暫停目標並停止。

本次由203算第1輪，本206為第4輪，完成203至207共5輪後暫停；本206仍active，不開始208。


## 第207輪來源及五輪停止指示

# 第207輪：原順序角色／技能 checkpoint 來源接入

這是使用者「從本輪開始算起，5輪之後結束並停止工作」的第5輪：203、204、205、206、207。本輪完整帳本、報告、封存及交接完成後暫停目標模式，不開始208；之後需要使用者明確恢復。本輪只做靜態原生研究及來源串接，沒有建置、測試、原生執行、封包模擬、DB、SQL、服務重啟或部署。

新增 CnRosterSkillCheckpointSource.h/.cpp，修改 SharedSubjectRosterPublication.h/.cpp。來源保留 WORLD30/31/32/33/39/34/35 混合原順序，在各連續技能區段提供實際 before-image checkpoint；不能把34/35抽出後跨角色更新套用同一舊快照。每筆技能記錄必須由 checkpoint 唯一覆蓋，索引及順序精確，不能重疊、漏接、倒序或跨非技能記錄；實際供應者可以因既有640筆來源投影預算拆分連續技能區段，不能自造新狀態或版本。640是操作預算，不是原生遊戲上限。

所有借用 records、aligned definitions、checkpoints 在呼叫外部 Current 前複製持有；投影包含原始索引及206的完整16列資料階段。同共用技能資源庫逐筆比對 kind/id/offset/hash/fullraw；來源指標保留強生命週期，immutable projection、原始分幀與實際事件在 BeforeQueue 和 QueueAccepted 都保留。選擇此契約必須顯式提供額外原生 checkpoint owner；既有共用 post-commit Qualify 仍必要。缺失技能來源不能降級用舊快照，不選擇此契約時不能夾帶 checkpoint。

原生保留968 bytes／283條指令，全數沿用既有證據，本輪新增原生位元組0。30先寫 inactive row；duplicate inline 分支只清 active matchingrow primarycount 後返回，負值30在正常追加後才更新選取。31使用 signextended ID、第一個 matching row；34/35使用 zeroextended ID、所有 matching rows。32/33/39沒有 subject ID，依當時 selected row（或原生 null-selection no-op）執行。這些差异決定實際供應者必須資格化中間的 reset/selection/row/revision，不能把來源 Current 當整段原生效果证明。

206投影內未知 log/UI callback、selected35 pending-table 及可能角色重綁的條件保留；本輪沒有展開 GUI、formatter、glyph 或容量流程。真正共用學習交易、保存、持久重播、WORLD-to-battle 技能 materializer、Main issuer及實際 per-run checkpoint供應者仍未接入。checkpoint 是真實事件持有的不可變 before-image 契約，沒有宣稱客戶端同時處於多個未來狀態，也不要求運作時讀取客戶端記憶體。Socket queue accepted 只是本機排隊接受，不能算客戶端已處理或原生 ACK。新增完整雙向路線0。

來源增量：新增C++2份、修改C++2份；部分來源段196→197。完整遊戲分母與完成百分比仍未知（null）；來源段、opcode與 endpoint 都不能算完整遊戲路線。

| 範圍 | 本輪最新數量 | 計數含義 |
|---|---:|---|
| TW C2S | 156 | 已觀測opcode聯集：151 generic＋5 supplemental，6分支 |
| CN C2S | 156 | 已觀測opcode，階段／變體仍未全定 |
| TW WORLD S2C | 252有效／256表項 | 230固定、22變長、4不支援 |
| TW BATTLE S2C | 110 | 9 special、101 default；83 action23、86 selector7 |
| CN S2C | 280階段項 | account6、world206、battle68 |
| 雙版 endpoint 索引 | 958 | 端點索引，非完整路線 |
| TW WORLD parser | 65／已審閱42 | 64.6%只適用此有限parser審閱範圍 |
| TW reply/control/unconnected | 43／10／13 | reply為下界，不是完整回覆總數 |
| CN receiver context | 14／已資格化12 | 47DE70、4812B0仍未知 |
| CN未hosting phase binding | 93／71不同值 | 原生階段來源，非完整路線 |
| TW未hosting phase binding | 10／10不同值 | 原生階段來源，非完整路線 |
| partial owner chain | 38 | CN35＋TW3，未hosting |
| 部分來源段 | 197 | 本輪＋1，不等同遊戲功能完成 |
| 本輪完整雙向路線增量 | 0 | 共用權威與正式issuer仍有缺口 |
| 全遊戲總數／完成度 | 未知／未知 | 不以局部解析或拒絕測試冒充 |

保留前206與更早帳本、帳號存檔、聊天、IME、認證、頭像、原生EXE／字體與繁簡轉換。共用表預設，只有已證明儲存不相容才 `_tw`／`_cn`；仙幣99,999,999,999、共用64位數域、合格堆疊99、等級不改的未完需求不變。整個 God2 目錄容量上限50,000,000,000 bytes，原生PE只原地雜湊，不恢復大型歷史樹。

實際 before 既有publisher2、第一候選4、最終4及實際依賴均完整保存；不更改206缺失候選原件的歷史紀錄。兩個子代理都在207停止。根封存及catalog207完整封存後，另存實際目標API paused回條與容量交接；不建立自動恢復工作。

下次需使用者恢復後才可接續：實際共用已提交混合角色事件與 per-run immutable checkpoint供應者，資格化中間資料／選取及未知 callbacks，再接真實學習／技能書權威交易、保存、重播與正式issuer。全部TW/CN/web路線完成後才集中全面測試、修復、發布。

本次由203算第1輪，本207為第5輪；本207完整封存交接完成後依使用者指示暫停目標並停止，不開始208。
# 最新優先序：2026-10-09 台服先達完整串接100%

使用者明確要求：「現在繼續工作 先把台服完全串接起來 達到100% 在停止工作」。先前203至207共五輪後停止已完成並撤銷；第208輪恢復，停止條件改為台服全部權威雙向來源路線接通。保留原目標的台陸／網頁共用核心、資料表、數值擴充與凍結功能，先完成TW再推進CN，不移除既有CN或另造服務端。

TW100%以完整版本／方向／階段／狀態／變體／間接與延後路徑的分母為準：原生請求→實際權威handler／Lua規則／交易與儲存→原生回覆、推播、斷線路徑→客戶端consumer。目前156個TW C2S觀測值、65個WORLD parser、42個已審閱局部分支都不是完整分母。不要把default拒絕、codec、條件式owner或單獨來源段稱為已接通。分母尚未封閉就維持未知百分比。

繼續遵守先全部串接、之後集中全面測試，再全面修復；本階段不建置、測試、執行原生／codec／服務、存取DB／SQL或部署。207 paused回條保留歷史；最新人類恢復指示及實際goal API active回條另存208，不偷偷改舊基準。


## 第208輪：TW-first正式scalar數量來源

# 第208輪：台服優先與實際scalar物品數量來源

使用者最新要求：「現在繼續工作 先把台服完全串接起來 達到100% 在停止工作」。先前203至207五輪停止已撤銷，實際goal API現讀active；本輪後繼續TW。TW100%必須是完整方向／階段／狀態／變體／間接與延後的權威雙向來源分母；parser、endpoint及局部來源段不能代替。保留CN/web共用核心既有成果，優先完成TW。

本輪修改4份C++：InventoryMoveService.h/.cpp、SqliteInventoryMove.cpp、SqliteRecoveredCharacterRepository.h。CUSTOM-0089數量99域現在接入既有Application的CUSTOM-0037合格scalar bag swap；這不是僅增加一個未呼叫codec。Application先以既有source/catalog／slot資格化並讀取owned snapshots，InventoryMoveService逐slot驗99及occupancy／revision，再準備原生完整回覆，最後到既有SQLite whole-slot CAS；writer在原本交易內再次檢查99、empty destination及非零bounded revisions，保存兩槽完整內容及各physical slot新revision並readback。

原生C2S24是3 bytes、來源slot與目的slot，沒有client-supplied quantity。回覆沿用完整兩槽41(clear)／3B／41(absolute)投影；空格只有41(clear)，不是3C。编码與allocation在commit前。此數量上限來自使用者自訂需求，不冒稱原生stack規則。實際production commit_inventory_move在src中只有InventoryMoveService一個呼叫；Application已有inventory_moves.move呼叫，但本輪未讀當前正式配置／進程，也未部署或宣稱正在執行新程式。

只接已資格化scalar whole-stack swap，不新增stackability、merge、split、equipment／PET／weapon／gem instance規則或item grant。普通背包30格、native50位置、獨立shop購買30及完整instance分路保留。原生signedBYTE127讀取／projection仍保留，以免剪截既有100..127存檔；這些既有rows不遷移，新此類swap被拒絕。所有完整metadata、來源SHA與owner仍由既有資格化來源提供，不以quantity域代替權威。

本輪沒有build、tests、native、codec、runtime、服務重啟、DB／SQL執行或部署；只靜態來源編輯、全文來源保存與帳本雜湊。保留帳號存檔、聊天、IME、認證、頭像、EXE、原生字體、繁簡轉換、等級與原凍結功能。本輪沒有新opcode／phase／原生bytes，也沒有新增完整雙向遊戲路線。

TW上游缺口已重新對齊當前來源：Main目前仍使用不含world-plan的run_server overload，完整TW NativeWorldHostPlan／Application安裝接點已存在，但實際NativeSourceFactory、完整2A材料、初始peer／scene材料、movement timing／permission／complete5D Authority仍未供應。舊historical2A候選不能冒稱完整當前角色材料。現有部分6E／A3／CB typed來源亦不能說全無程式；正確缺口是實際owner／issuer／Main及完整native效果還未接入。

下輪先接實際TW完整entry／scene材料與正式source factory，推進正向2E權威位置CAS及完整native回覆；其餘已知缺口包括PK35／69、A9傳送、D6 PET2 revert、D8每日任務、6B companion control、9E活動、E4控制、BF商店、C2對話、6E觀戰與A3／CB close，還有已審閱42個分支中未完的變體、玩法與儲存／推播。它們不能因本轮99寫入域已接入而刪除。

| 最新有限範圍 | 數量 | 說明 |
|---|---:|---|
| TW C2S觀測聯集 | 156 | 151generic＋5補充opcode／6分支，未窮盡phase／variant |
| TW WORLD S2C | 252有效／256表項 | 230固定、22變長、4不支援 |
| TW BATTLE S2C | 110 | 9special、101default；83 action23／86 selector7 |
| TW WORLD parser／已審閱 | 65／42 | 64.6%僅此parser審閱比例，非台服完成度 |
| TW已審閱reply下界／control／unconnected | 43／10／13 | 現有partial來源仍保留完整權威與變體缺口 |
| TW未hosting phase binding | 10／10不同值 | 非完整遊戲路線 |
| CN C2S／S2C階段項 | 156／280 | account6、world206、battle68；既有成果保留 |
| 全域endpoint／source groups | 958／28 | 索引不是遊戲功能分母 |
| partial owner chains | 38 | CN35＋TW3，不因本輪局部writer而增加 |
| 部分來源段 | 198 | 197→198，本輪＋1 |
| 新C++／改C++ | 0／4 | 已有Application呼叫的實際service/writer接入 |
| 新完整雙向路線／台服100% | 0／未達成 | 全TW分母及完成百分比仍未知 |

before4、第一候選4、final4與實際Application／projection／quantity／SQL source依賴分別完整保留，不重写207及更早封存。兩個bounded子代理交付208後停止自己的小任務，主目標仍active。全God2容量維持50,000,000,000 bytes以下。每輪仍提供唯一報告與路徑帳本；達TW全部來源串接100%才按使用者指示停止，集中測試／全面修復保持後續階段。

台服全部串接100%前持續工作；207 paused回條僅為歷史，不在208停下。


## 第209輪：TW完整入場material來源

# 第209輪：台服完整2A入場資料來源

本輪新增5個C++來源檔、修改5個既有C++來源檔，接入完整入場原始資料的共用儲存介面、SQLite同連線讀寫來源，以及台服儲存資料至既有世界入口Source的橋接。這是部分來源串接，新增完整雙向遊戲通路0條；台服完整通路分母及完成百分比仍未知。

`NativeWorldEntrySnapshot`保留完整共同角色root（ID/帳號/slot/profile/created_at/name_codepage/streamer_privilege）、存檔位置與位置revision、原始封包、客戶端build SHA、source SHA/source_record及實際revision。`character_native_world_entries`按帳號、角色、build及record_kind共用儲存，屬版本化delivery witness；沒有另建兩套遊戲角色表。舊witness允許讀取以供精確CAS替換，讀取本身不宣稱角色與位置仍current。

SQLite writer在同一帳號/角色connection自有交易內比較完整expected tuple，實際角色及位置需與next一致；Prepared、BeforeWrite、BeforeCommit要求真實issuer。每次observer前後均追查共同root/位置及material tuple，BeforeCommit對照staged next。重入即使被observer攔截也使外層不能commit。revision及原始資料由實際issuer提供，不自行產生初始1、遞增值或預設native資料。此輪只寫SQL/C++來源，沒有開啟資料庫或執行SQL。

`SharedTaiwanWorldEntrySource::Scope`現在包含完整selected root。`SharedTaiwanStoredWorldEntrySource`從同源storage取出精確40-byte零seed原始frame，要求build、完整角色、位置revision及map一致，再交給必要的真實Qualify；返回的Current重讀相同完整tuple，並保留原生未知位元。repositories/catalog為明確借用，所有Source/Native/Current必須在實際database被銷毀前排空；shared closure只擁有snapshot及guard，沒有假稱其擁有資料庫。

新schema有獨立明確fresh installer來源，不變更既有NativeDeliverySnapshotSchema v1，不進入default migrate/login/Main，缺schema不被視為空成功。新的來源檔依既有src glob納入來源集合，本輪没有建置。真實issuer、全部欄位的共同狀態來源、場景初始資料、queue/publication生命週期、5D移動Authority及Main正式SourceFactory仍OPEN；此輪沒有啟用正式服務。

原生子代理依保留的149c1b45… native master追完2A正常initializer的1904 bytes與575條靜態指令，包含32-byte switch資料；這些是既有原生證據的重新定點分析，新增opcode與新增native coverage均0。2A為37-byte logical、36-byte body、40-byte standalone wire。B8..11未在限定initializer獨立讀取，不能稱全遊戲unused；B26..27是DWORD load的高WORD，可能進入scene helper參數，不能清零。appearance/status/resource及transform資格仍需實際issuer，不能以歷史body換ID代填。

原生master目前由既有consumer-experiment/inputs/native-image.bin原地全檔雜湊；歷史capture_work的原始master路徑缺失，保持原紀錄及此缺失，沒有恢復歷史樹或偷換原基準。149c master、6bf75e歷史audit、99cde6字體恢復installed EXE各自保留身分。原生子代理在root修改前讀取的Entry Source兩檔精確對照before209，與最終root版本分開記錄。

盤點沿用：TW C2S觀察opcode156；WORLD S2C長度表有效252（fixed230/variable22），BATTLE S2C110（special9/default101），83 action23、86 selector7。WORLD parser65、已審來源42；42/65只代表該parser審阅範圍。CN C2S156、S2C phase280。這些opcode數不能加總充當完整遊戲通路分母。部分source segment198→199；全遊戲與TW完成率均null。

下一段優先追查完整2A真實產生器、外部name/role/resource/status輸入及實際Scene初始material，接入SourceFactory與Main時必須有真實scene/movement/lifecycle，不能以always-true callback補洞。繼續台服全部来源串接至實際100%再停止，保留CN/web共用成果。全面測試、驗證與大修依使用者順序留待全部串接後。



## 第210輪：TW儲存入場Application組裝

# 第210輪：台服儲存入場來源接入Application組裝

本輪修改4個C++來源檔，接通第209輪完整2A儲存來源的實際組裝呼叫端：Application的共同Database → 明確選用的Context reader → StoredSourceFactory → StoredNativeSource → 既有guarded Factory/Owner → Entry、initial scene與movement facade → game vault → Session原生entry handler。部分來源段199→200，新增完整雙向玩法通路0；Main與正式服務沒有啟用此plan，完整台服與全遊戲分母、完成百分比仍未知。

`SharedWorldHostPlan::Context`新增借用的`native_world_entries`reader；只有明確`requires_native_world_entry_snapshots=true`才由Application取同一Database的optional accessor，並對實際accounts/characters做`owns_sources`。legacy/generic plan維持false/nullptr，不額外開資料庫、安裝schema或製造資料。這輪只修改來源，沒有執行Application或SQL。

`SharedTaiwanNativeWorldHostPlan::create_from_stored_entry`要求實際build SHA及完整StoredSourceFactory。該factory在既有game-owner guarded建構內執行，取回必要的real Qualify、entered、movement rules/resources/capacity與選用mixed records，然後由Context的精確reader、角色及地圖建立209的NativeSource，交回既有Sources/Owner。沒有先造一個空entry來佔位；既有泛用SourceFactory API保留。Owner.same也比較reader指標，不能換一個Application的storage來延續原owner。

實際Database/catalog仍借用，Source與Current持有其owned snapshot與game-affine guard；既有Application的handler/vault、listener/controller清理必須在Database解構前排空。本輪没有宣稱將borrowed Database改為shared ownership。full raw40、root/profile/name metadata、位置版本、map、actual issuer/Qualify及其後續scene/queue/current資格仍是必要實際來源；factory組裝不代替這些語義，也不證明完整native acceptance。

原生定點追查辨明2A初始化器的外部參數：connected路徑65186從64910第二arg取名字指標，65194呼叫68160；role參數指向world inline角色物件W+1539683C，third out-flag來自Application+A4。名字指標在正常40E0D6 caller指向DE80的local+30；既有selected-copy5BD2..5BDB從rawList+2+36*selected複製40B至這個buffer，wire stride36與copy40保留為各自原生觀察。名字後續進入role+B7，不是2A37 logical內的名字欄位。disconnected分支使用NULL與內部fallback，不能拿此離線fallback當服務端真實名字來源。

這些caller邊界與已知selected-copy data site合計7段保留原生raw404B、106條指令；新增native coverage/opcode/完整通路皆0。4DA0等GUI/text/render內部不展開；caller的原始buffer輸出與已知copy來源分開記錄，不能把client指標當伺服器權限或假造指標回包。需要將實際selected record/name/codepage/current、同一共同角色root與完整2A frame分開資格化後串在同一選角/入場epoch。

盤點沿用：TW C2S已觀察156個opcode；WORLD S2C252（fixed230/variable22）；BATTLE S2C110；83 action23、86 selector7。WORLD parser65、已審來源42；此比例不是完成率。CN C2S156，S2C分phase280。endpoint958、群組28及部分來源段200均不是完整玩法通路分母。

下一步優先接實際selected record/name/codepage與完整2A issuer，再接初始scene material、WorldOwner/delivery與全5D Authority，最後才選用Main正式SourceFactory。其餘TW gameplay/state/variant/deferred路徑、numeric64與stack99完整變動鏈、CN/web共用支援仍在同一目標內。台服全部來源串接實際達100%才停止；全面建置、測試、驗證與修復依使用者順序留待全部串接後。



## 第211輪：TW原生選角列表共同角色來源

# 第211輪：台服原生選角列表與共同角色來源

本輪新增2個C++來源檔並修改8個既有檔，將實際儲存的TW07原生列表、原生選角token與完整共同角色ID接入同一個Application／Session流程。來源串接段由200增加到201；本輪新增完整雙向玩法路徑為0。TW全遊戲方向、階段、狀態、變體與延後分派分母仍未知，完成百分比為null。使用者的最新順序是台服優先，實際全部串接完成才停止；先前五輪停止条件不再適用。

## 已寫入的實際接線

`SharedTaiwanNativeCharacterListSource`借用實際共同帳號、角色與`NativeCharacterSummarySnapshotRepository`。同一reader必須`owns_sources`配對；固定原生build雜湊、目的地來源TargetSource、目的地Current與完整Qualify均由實際供應者提供。沒有預設group0/server0、猜測6B欄位、成功fallback或自造原生列表。資料缺失、角色歸属變更、名字編碼或來源不一致時，不能輸出假成功。

列表來源保留完整75個logical bytes（opcode07＋74本文），保留旗標、資源、外觀、routeBYTE32及名字NUL後的原始位元組。只核對真正共同角色名字的原始codepage與CP950嚴格轉換是否等同原生列內名字；不改字體、不改名、不進行名字繁簡呈現替換。舊codepage0僅能處理確定ASCII，非ASCII資料需其實際原始codepage。輸出使用既有frame envelope的C++來源路徑；本輪未執行codec。

列表行依真實issuer ordinal與原生token綁定共同角色；原生token的低3bit不當成共同slot。選角來源在實際Authenticated且尚未選角色的Session內，重新觀察完整帳號角色集合、同一列表完整tuple與實際目的地Current／Qualify，再傳回完整共同角色ID。創角後若帶有實際pending_created_character，token必須指向該完整ID；沒有共同slot或14bit actor ID替代。

`SharedWorldHostPlan::Context`新增可選實際帳號／summary reader；Application只在明確`requires_native_character_summaries`時取得同一Database的reader，檢查其共同來源後交給Context。`create_from_stored_entry(...,native_characters=true)`從實際StoredSources的ListSources建立上述Binding，與既有stored-entry、scene、movement及mixed-record來源共用同一guarded Owner。一般`create(...,true)`同樣選取此capability，Owner要求實際account／summary非空且`owns_sources`一致，避免兩個工廠走不同資料庫資格。

Application將native list/select/invalidate來源保留在game owner的WorldLifecycleVault。帳號與角色兩個真實listener中的Session handler僅持有弱facade；revocation在Database還存在時清除實際來源。兩listener使用exclusive native_list/native_select，舊list/select_created/select_existing分支不能混用。Session的選服後列表與角色選取分派實際呼叫這些facade；新操作鎖與來源invalidate_active使供應者捕捉巢狀reentry也不能授權外層繼續。

同時將summary reader/writer的既有SELECT/DML鎖定`main.accounts`、`main.recovered_characters`與兩個共用summary表，避免TEMP同名遮蔽。新增writer reentry poison，實際issuer callback捕捉巢狀writer拒絕後，外層fulltuple核對仍會失敗。canonical v1 schema原始suffix保持逐位元組相同；未修改資料表布局、default migration、舊快照基準或持久化資料。另有獨立removal來源檔的歷史處理未在此有限範圍修改，不能宣稱其全部租約邊界也已完成。

## 原生資料邊界

兩個既有子代理分工：一個定點釐清已保留原生receiver／data-copy證據，一個審本輪10個C++全檔雜湊、實際diff、依賴與owner接線。原生覆蓋本輪新增0，保留11段共528 bytes／174 instructions。TW07 receiver只複製74個本文bytes；本文第一BYTE是count，下一BYTE是opaque flags，不是WORD count。共同兩角色／fixed75幾何預算不是原生permission，receiver沒有自行clamp count。

原生行stride36而選中後複製40 bytes。第一行多出的4 bytes來自下一行前綴；第二行最後4 bytes超出本次receiver寫入範圍，其中包含Application相鄰另一domain。不能補零、當checksum、當創角profile40或宣稱完整selected40已由07提供。保留原始列表與外部selected-name來源；原生名字傳入世界角色的既有caller鏈也不能取代服務端權威資料。

## 本輪明確未完成的接續

- native list/select Current是game owner pre-use觀察；network strand queue-current原子性、實際發出列表的跨socket版本／生命周期尚未接上，不得在strand呼叫SQLite Current，也不能以copied frame＋closing核對冒稱原生完成。
- 真正raw07 issuer、post-create後列表重發、create response/header來源、未明目的地與實際route/resource／visibility權限仍由真實供應者提供，尚未有完整Main工廠。非ASCII的未知原始codepage不能自動填950。
- 從已發出的列表／已選角色到完整2A原生材料的同epoch來源資格、第二行外部selected40 suffix來源、完整initial scene/peer material、publication queue及5D Authority仍開放。storedblob與共用ID綁定本身不等於上述權威。
- 台服13組其餘玩法與全方向／狀態／變體／延後分派、64位元數值全路徑與stack99仍待實際串接。共同資料表預設共用；CN與web成果保留，只有已證明儲存不能共用才考慮`_tw`／`_cn`尾綴。

TW已觀察C2S opcode156；世界S2C有效252（fixed230／variable22），戰鬥S2C110；83 actions23、86 selectors7。TW world parser65，其中42組已做來源盤點，這不是遊戲完成百分比。CN C2S156；S2C phase rows280（帳號6／世界206／戰鬥68），亦非去重後完整雙向玩法分母。來源段201、endpoint958／group28與上述opcode只用來描述盤點範圍。

第一階段未build、test、執行原生、codec、runtime、DB/SQL、migration或deploy；沒有新增正式原生驗收或宣稱已部署。全面測試、修復與可恢復發布保持在全部來源串接之後。



## 第212輪：TW原生A6選取輸入來源

# 第212輪：台服帳號階段A6選取資料來源

本輪修改5個既有C++來源檔，新增來源串接段1（201→202），新增完整雙向玩法路徑0。TW方向／階段／狀態／變體／延後分派分母仍未知，TW與全遊戲百分比均為null。台服先完整串接100%再停止的優先要求保持；此輪結束不暫停目標。

## 實際原生格式與來源

已保留的原生producer `147D0`將兩個實際參數的低BYTE寫入2-byte本文，`147EA`使用opcodeA6。實際caller `B490`從Main+8F4與Main+B40的WORD取值；這兩個線路BYTE不能擅自當成group ID、server ID、IP或port。`12506`是通用framer／send回傳位置，多個opcode共用，不能單憑該PC判定封包種類。舊「6B」標籤與歷史receipt保留作歷史，不改掉基準或冒稱舊raw trace已找回。

在現有明確recovered zero-seed／feedback0、未壓縮、原logical queue為空且只含一筆A6 logical3的profile下，standalone envelope為6 bytes。原生`10670`校驗是clear header長度bytes及每個logical BYTE加0x3C之和mod256；`10690`使用key與先前clear feedback。key、feedback與加密旗標仍是profile條件，不將此source extension泛化成任意dynamic seed或混合queue。此次已保留11段726 bytes／264 instructions，新原生coverage為0；未執行codec或原生。

`ParseNativePostServerSelectRequest`針對上述現有profile處理完整wire6、length、A6 opcode與校驗，保留完整raw、logical、checksum與consumed；兩個selector bytes原樣可供真正來源使用。原`ParsePostServerSelectRequest`仍保留舊exact-fixture gate。Session僅在實際native_list opt-in時選擇一般A6 parser，其他default／legacy模式仍走舊gate；避免把任意selector接到candidate成功列表。

## 已接入的來源鏈

實際Session strand parser取得owned request value後，在真正`character_operation` game工作內傳遞，並只在native-list分支、Authenticated、帳號非0、未選角色、未closing且尚未安裝時，發布`RecoveredServerSelection{session,account,request}`。該不可變observation由私有atomic shared_ptr保存，沒有public setter。網路端不讀取game-owned帳號欄位，不以已清除的strand輸入buffer或strand狀態作game來源。

`SharedTaiwanNativeCharacterListSource::Scope`持有同一不可變observation。實際TargetSource／Target.Current／Qualify能取得真正收到的A6輸入；Current核對同一observation identity以及session／account、原有phase／closing與完整角色／snapshot來源。List缺少這個真實輸入便拒絕，沒有猜測目的地或成功fallback。Scope仍保留原生selected-token與完整common ID資格，既有reentry poison路徑保留。

獨立God2CharacterConnection世界socket直接登入後不經帳號A6階段，其Select.Scope中的observation誠實為null。不能填造另一socket的A6、不能將相同raw bytes當成跨socket已發行列表receipt。observation是每Session一次發布的輸入來源；pointer identity防止equal-byte ABA，本身不是權限ticket、目的地grant或列表送達證明。

兩個既有子代理分工：原生代理釘producer／framer原始證據；來源代理審本輪5個C++全檔、實際caller與diff、所有實際依賴。原生代理的`RecoveredPostServerSelect.h`副本是真實before212 epoch，因root後續修改而與final不同，會在source epoch reconciliation如實對到完整before；該代理未審final C++，final來源由另一代理fresh審閱。兩份封存各自保留，不能偷偷refresh原始檔。

## 仍未完整的部分

- 真正已廣告table／目的地／phase／visibility／resource Current與native07 issuer仍須接上；native兩BYTE不是通用server索引資格。A6解析與輸入保留不等於選服玩法完成。
- 實際發出的列表epoch與跨account／world socket選角來源、queue-current原子性、post-create native header／issuer與完整2A材料鏈仍開放。不能在strand跑SQLite Current。
- 原生dynamic seed、其他feedback／加密flags、混合logical queue與其他選服variant需其實際證據與來源；不藉此修改凍結認證／hello／seed profile。
- 完整initial scene／peer publication、5D Authority、真正Main工廠與台服13組其餘玩法仍待串接；64位元數值全路徑、stack99、CN與web共用成果保持原範圍。

TW盤點C2S156、世界S2C有效252（fixed230／variable22）、戰鬥S2C110、83 actions23／86 selectors7；TW world parsers65與已盤點來源組42不變。CN C2S156、S2C階段列280（帳號6／世界206／戰鬥68）。endpoint958／group28，來源段202；opcode與來源段都不是全遊戲完成百分比。

本輪沒有build、test、原生執行、codec execution、runtime、DB／SQL、migration、deploy或新的原生驗收。帳號存檔、聊天、IME、認證、頭像、客戶端、原生字體與繁簡轉換等凍結功能保留。先完成全部来源串接，再集中全面測試與修復。



## 第213輪：TW实际送出清单与选服输入来源

# 第213輪：TW實際送出的選服清單與選服輸入來源

本輪新增1個C++來源檔、修改4個既有C++來源檔。累計來源串接段202→203；新增完整雙向玩法路徑0。台服完整方向／階段／狀態／變體分母尚未釐清，完成百分比仍為未知。台服完整來源串接仍是優先目標；使用者最新要求「這輪結束停止工作」，因此本輪收尾後暫停，等待明確恢復。本輪沒有建置、測試、原生執行、編解碼執行、資料庫操作或部署。

Session現在只在原生角色清單來源明確啟用時，將實際加入socket寫入佇列的伺服器清單bytes、session及候選來源種類保存在不可變物件中。實際async_write成功回呼核對同一個佇列元素、完整bytes與session後才記錄。這個記錄表示伺服器已完成該次socket寫入，不表示客戶端已處理，也不等同可登入權限。舊有封包與預設路由行為保留。

實際A6選服請求於strand解析後，將同一筆已完成寫入的清單記錄連同擁有的解析值捕捉到game回呼。既有認證、帳號、狀態及一次性發布條件仍成立；game不直接讀取strand的可變欄位。不可變選服記錄再交給原生角色來源Scope與實際Target／Current／Qualify，讓資格供應者可以核對選服輸入和同一次送出的原始清單。

新增RecoveredTaiwanServerAdvertisement保留04完整body DWORD、實際ordinal與mask WORD；依來源順序覆蓋重複ordinal。已釘定原生長度為04／06 logical5、05 logical9。解析僅沿用既有zero-seed／feedback0／uncompressed封包profile；05／06完整原始bytes仍在不可變清單中，沒有捏造目的地或資源ID。64個04儲存ordinal與1MiB傳輸記憶體預算分開；後者不是原生容量。

原生Main+8C是04接收目的地，Main+8E+14*g WORD是接收mask；第一個選擇器記錄實際物理ordinal，和顯示壓縮ordinal不同。第二個選擇器還受獨立配置count、mask與指標來源約束。這些事實不能直接變成帳號權限或任意group／server映射，不能將普通顯示迴圈0..7當成所有A6輸入的完整界限。UI helper內部保持未追查。

角色List要求同一筆選服記錄及可解析清單。Select對「存在選服記錄但清單損壞」明確拒絕，與獨立world socket沒有account選服記錄的情況區分。Current保留既有完整root／snapshot／session／account核對，並檢查不可變清單的來源session。原生目標資格、候選清單的正式來源、配置／指標供應者、權利與時間點仍由實際Target.Current／Qualify提供；沒有預設成功或假的跨socket授權。

靜態原生子代理保留23個既有code span、939 bytes、267 instruction sites，另外55 bytes分派資料與12 bytes長度指標；新增全域原生覆蓋0。另一子代理檢查before、candidate及最終5個來源檔；其指出的損壞清單與來源缺席混淆已在實際Select來源修正。封存只證明本輪靜態來源及檔案版本，並非遊戲驗收。

台服封包盤點沿用C2S156、world S2C252、battle S2C110；陸服C2S156、分階段S2C280。不能相加成完整玩法分母。仍須接入正式已發布清單／選服epoch、跨socket與queue-current原子性、完整native07角色清單issuer、full2A世界入口與Main實際選用來源，接續其餘台服權威玩法及擴充數值／物品堆疊。清單候選Origin不提升成原生正式權限。



## 第214輪：TW原生角色清單來源與實際寫入完成

# 第214輪：台服原生角色清單來源與實際寫入完成

使用者2026-10-10恢復工作，要求台服完整來源串接100%才停止；撤銷上一輪收尾暫停，目標保持active。本輪修改6個既有C++來源檔，新增0個C++檔，來源串接段203→204，新增完整雙向玩法路徑0。台服完整方向／階段／狀態／變體分母仍未知，百分比null。未建置、測試、執行原生、codec、runtime、DB／SQL或部署。

## 本輪實際接線

原生native_list不再只交出裸frame78。SharedTaiwanNativeCharacterListSource建立不可變純資料delivery：實際session／account、只增不重用的source sequence、完整frame78與該Session實際A6觀察。sequence是服務端準備識別，不放進原生wire，沒有自造跨socket nonce或grant。完整snapshot、roots、Target及Scope留在game owner的pending map，使用實際host session capacity限制數量；每Session只允許一筆pending，sequence overflow明確拒絕。

新增current及complete來源callback，和list／select一起穿過實際SharedTaiwanNativeWorldHostPlan Owner及Application WorldLifecycleVault。Session只持可撤銷的弱facade；real callback與借用資料庫來源留在game owner。所有constructor／factory配對條件都要求完整來源，沒有缺callback時默認成功。既有legacy list／select與未啟用native來源的行為保持原分支。

Session將同一個完整response buffer以held Write加入佇列；Write只含不可變純資料識別，不持real game callback。接著post到game執行同一pending的完整Current／Qualify，再回strand核對同一delivery pointer、held項目、buffer pointer與完整frame bytes才解除held。來源拒絕、關閉或幾何不符會走同一次取消。

實際async_write成功回呼再次核對同一Write／buffer／delivery。只有這條成功路徑才以written=true排回game；失敗、timeout、關閉或清除佇列則以false完成。active_native_list在排程前清除，避免同筆完成重送。game_busy及讀取暫停保留到game完成處理，讓Session正常關閉能等待實際來源清理。complete先移除pending再呼叫外部Current／Qualify，即使來源拋例外也不積累已消耗項目；duplicate不能發布或移除另一筆。

只有實際socket成功加上game完整來源重新核對成功，才在原Session發布private atomic不可變寫入記錄。沒有public setter，保留完整原生frame與A6來源觀察。這是伺服器本地寫入與來源核對記錄，並不是客戶端已處理的ACK、角色權限或獨立world連線的授權。

## 時間與原生資料界限

Current在解除held前及寫入完成後執行；game回strand至async_write期間其他game工作仍可能改變來源。後置Current可以拒絕發布失效記錄，不能撤回已寫出的bytes，因此本輪沒有宣稱「wire寫出瞬間與SQLite來源完全原子」。實際queue/source發行原子性與取消所有在途bytes仍是後續工作。

靜態原生子代理重新核對10段保留code span，935 bytes／250 instruction sites，新增原生覆蓋及opcode均0。14C50的C2S1A為logical38／body37／outer41，兩段16-byte輸入來自憑證緩衝區而非07角色名字；各末BYTE強制NUL。實際低3bit token0..7經此producer投影為0..3保留、4..7變0，與connect路由lookup不同；body尾端3 bytes沒有完整producer明確寫入，不能填造語意。

原生客戶端state18／1A會修改本地清單backing的token及路由／資源欄位，不能把後來記憶體值冒稱原始S07 issuer。原始logical75／body74、row stride36及另外selected40的外部suffix繼續分開。L登入連線與G世界連線需要獨立認證；複製A6或帳號ID不形成其來源鏈路。以上都是資格邊界，沒有增加完整玩法路徑。

## 尚未接通

獨立world Select仍需實際issued-list LinkSource：同帳號／build／目的地／source epoch及新socket認證來源，不能選取該帳號最新或第一筆清單當作權限。本輪immutable記錄提供可引用的原來源，沒有自動跨socket傳送、重用登入授權或推定所有token變體。完整raw07權威issuer、post-create來源與列表重發、配置／resource／visibility、full2A／initial scene／5D／Main正式選用仍開放。

TW盤點C2S156；world S2C252（fixed230／variable22）；battle S2C110，83 actions23及86 selectors7。CN C2S156，S2C phase rows280（account6／world206／battle68）。上述不是完整雙向玩法總數。台服其餘13組玩法、數值64位全路徑、stack99及全狀態／變體／延後分派仍待接通；保留共用資料表、CN／web、存檔、認證、聊天、IME、字體與轉換。全部來源串接後再集中全面測試與修復。



## 第215輪：TW完整選角輸入與已發清單來源對應

# 第215輪：台服完整選角輸入與已發角色清單來源對應

本輪修改8個既有C++來源檔，新增0個C++檔。來源串接段204→205，新增完整雙向玩法路徑0。目標保持active、台服完整來源串接100%才停止；完整分母與百分比仍未知。前一輪有實際6個C++來源修改，屬progress，並非等待或僅改計畫。本輪依要求未build／test／原生／codec／runtime／DB／SQL／deployment執行。

## 已寫入實際呼叫路徑

RecoveredPostCreateSelect新增Selection，保留完整raw41、logical38及實際存在時的raw5 prefix。既有selection_token_from_frame保留原接受條件與token介面；legacy分支仍走原token路徑。native Session將實際解析值擁有地捕捉到game工作，再沿Application弱vault facade及同一Host Owner交給native_select，沒有從外部名字或角色資料重造請求。兩段憑證資料與opaque tail保留在私有請求，不記錄其值。

Session在真正原生選角分派前，一次發布session／account／完整輸入／pending_created_character的不可變觀察；僅實際解析呼叫路徑能設定，沒有public setter。Source重新解析raw41並核對logical38與prefix，再核對同一Session私有觀察、獨立已認證帳號、未選角狀態、created完整ID、closing與來源reader。在呼叫外部LinkSource之前即要求上述條件，不接受僅自行填寫的Selection.logical。

上輪的實際async_write成功路徑現在另發布一筆純socket-written觀察，與後置來源合格的觀察分開。只有同一個已成功寫出的Write／buffer／delivery能設定它；後置Current失敗時仍能如實表示本地寫入曾完成。Source complete(true)必須核對這個私有exact pointer才能繼續，不能單靠公開callback的written=true建立發行來源。

Source在真實寫入與完整Current通過後建立private constructor、禁止copy的Issued票證。票證保留完整原snapshot、完整共同roots、delivery及issuer Scope；只弱引用該Source identity，沒有DB／Session強引用或Target.current callback，外部保存不延長資料庫生命。票證起初dormant，交給必需的Publish來源；只有Publish接受、重新完整Current／Qualify仍通過且沒有供應者捕捉reentry時，最後才activate。拒絕、拋例外或失效留下的票證永遠未啟用。

選角必須由實際LinkSource取得已發票證及必需的Link.current。Source拒絕未啟用、來自另一個Source owner、不同帳號或不存在的票證；用新連線自己的Scope與Target讀取真正目前快照，再核對整個snapshot tuple與全部roots是否和已發原件完全相同。issuer Scope另保留在票證，沒有把登入連線的A6偽裝成世界連線的A6，也沒有用新連線重跑舊L Target.current冒稱同一來源。

真正token→完整共同角色ID仍受Qualify、created ID、Link.current及前後完整Current限制。StoredSources::ListSources新增必需的Publish／LinkSource，透過現有create_from_stored_entry交給同一個game Source。沒有帳號最新／第一筆清單fallback、缺來源時成功或重新定義token為共同slot。

## 原生分支與明確邊界

靜態原生子代理保留8段既有code span，531 bytes／173 instruction sites，新增全域原生覆蓋與opcode0。既有角色state14可直接BA00→14C50送1A，該有界caller沒有C18。創角成功D26E分支才先BE80送18再BA00送1A；18值是low8(原WORD+1)，不是07 token或角色ordinal。這兩個原生輸入域保持分開，不把postcreate prefix套到所有選角。

1A的body37包含兩段各16 bytes憑證投影、body32 token、body33 literal4與末尾3個未明確寫入的原生stack bytes。logical38／outer41不能混稱；opaque tail不填零、不當作權限key。原始row W19低3bit、後來客戶端本地backing修改與1A clamp並不等價；實際producer對0..3保留、4..7投影0。目前來源只保留既有不alias且≤3的subset，其餘變體仍須真實供應者接入。

Issued是來源證明，不是一次性角色admission／parallel-G鎖或防重播CAS。本輪沒有新增這些結算／租約語義。Publish與Link的完整bounded handoff owner、實際認證／目的地／native projection供應者仍待建立；介面與真實caller接線不等於已有Main正式選用或全部跨連線選角完成。postcreate不能靠舊07重造新角色issuer或隨意補列表重發。held-release Current與寫入後Current依然不等同wire emission瞬間原子，後置拒絕不能撤回已發bytes。

## 盤點與接續

台服C2S156；world S2C252（230 fixed／22 variable）；battle S2C110，83 actions23／86 selectors7。陸服C2S156；S2C phase rows280（account6／world206／battle68）。這些盤點數不代表完整雙向玩法分母，不能轉成遊戲完成百分比。

下一步把實際已發票證交接owner與新G選角來源接入，再接原生raw07 issuer、創角後完整來源、full2A／初始scene／5D／Main及其餘台服玩法；保留共用資料表、CN／web、帳號存檔、聊天、IME、認證、原生字體及文字轉換。全方向／狀態／變體與deferred分母、數值64位全路徑及stack99仍開放。全部來源串接完成後再全面測試、驗證與修復。



## 第216輪：TW角色清單交接owner與獨立世界認證來源

# 第216輪：台服角色清單交接 owner 與獨立世界認證來源

新增2個、修改5個C++來源檔。來源串接段205→206；新增完整雙向玩法路徑0。依使用者最新指示持續台服優先，完整來源串接100%才停止。完整方向／階段／狀態／變體／延後分派分母仍未知，百分比null。未建置、測試、執行原生／codec／runtime、存取DB／SQL或部署。

## 實際接線

Session僅在明確選用native_select的連線，於真正帳號認證完成且account非0、無error、未closing時，一次發布private不可變認證輸入觀察：實際session、account、ProtocolMode與完整raw176／logical173。沒有public setter，不記錄憑證值；不更改既有認證成功／失敗判定、password worker、回覆或legacy模式。觀察配置失敗不改寫登入結果，後續原生交接因缺來源明確拒絕。

SharedTaiwanCharacterListHandoff實作真正game owner bounded map，使用實際host session capacity與獨立單調不重用epoch。紀錄只保存不可變Issued及原L認證輸入，沒有Session／DB／Target.current強引用。Issued新增source_alive弱來源生命觀察；實際源失效、來源快照／roots／帳號／Live失效、失敗未啟用票證會在後續操作清理，亦提供exact ticket retire。正常L連線關閉本身不被當作G交接失效，沒有自創TTL或account-latest替換。

Publish只接受dormant、同一Session真正async_write成功的exact delivery pointer、原L04成功認證觀察、原A6及未選角Authenticated生命週期。重新讀取同一借用reader的完整snapshot tuple／完整共同roots／帳號，並由必需的Live資格化實際issuer epoch、catalog、visibility及生命週期，才登錄票證。Source仍於Publish返回後完成自身Current，最後啟用；Owner不能把dormant提前當權限。

Link必須來自獨立G00成功認證和真正Session private選角輸入。核對session／account／mode／opcode／raw重新解析結果、created完整ID、未選角Authenticated及closing，再比對原生憑證投影。逐一檢查同帳號、符合投影、仍active且來源完整的已發票證，由必需Authority資格化實際目的地、原生variant及選角權限。候選超過一筆明確拒絕，沒有第一筆／最新一筆fallback。

返回Link.current保留exact owner epoch／ticket、G認證及選角private pointer；每次重查所有候選與Authority，涵蓋Link之後票證啟用或新增造成歧義。所有repository／provider呼叫前先複製紀錄，不持map iterator或reference跨回呼；巢狀owner操作會使當次工作失效，即使外部供應者捕捉例外。公開binding在每次呼叫保留本地strong owner，避免供應者釋放facade導致執行中生命消失。Current只弱引用owner，外部不能靠Current延長DB借用來源生命。

StoredSources::ListSources::with_handoff將此實作交給真正create_from_stored_entry，同時要求exact accounts／characters／summary readers、client SHA及host capacity一致。與直接Publish／Link供應者互斥；未選用原生方案的legacy呼叫不變。新CPP由既有CMake src/*.cpp遞迴來源集合收錄。

## 原生依據與未完成界限

子代理保留13段code、1022 bytes／344 instruction sites，新增全域覆蓋與opcode0。547B80完整254 bytes為此子代理首次本地保留，不冒稱全域新覆蓋。實際bounded stringcopy在firstNUL後補零；14C50各複製16並強制末byte NUL。因此從auth logical[1:25]與[25:157]各取最多15個firstNUL前bytes、補零、末byte NUL，才對應1A兩段16 bytes。不能直接memcpy auth前16，不能把角色名字、文字轉換、casefold或opaque tail當憑證權限。

L04／G00原生來源共有saved credential部分，但1D可能改寫172-byte tail；不要求兩者full172相等，也不把parse成功當真實認證。投影只是必要predicate，真正獨立帳號認證、同源epoch與Authority仍不可省略。

實際Live／Authority政策供應者、raw07權威issuer、創角後列表來源與全部token／localbacking變體、full2A／initial scene／5D／Main正式選用仍開放。本輪有界owner實作不等於完整跨連線admission；沒有一次性admission CAS、防重播或parallel-G消耗租約。前後Current不能使wire emission與來源原子，也不能撤回已發bytes。借用reader及real callback仍必須由既有game owner／Application vault drain保證生命。

TW盤點C2S156；world S2C252（fixed230／variable22）；battle S2C110，83 actions23／86 selectors7。CN C2S156；S2C phase rows280（account6／world206／battle68）。這些不是全遊戲完成分母。台服其他13組玩法、全方向／狀態／變體／deferred、numeric64與stack99仍須接通，保留共用資料表、CN／web、存檔、認證、聊天、IME、原生字體與文字轉換。全部來源串接後再全面測試、驗證與修復。



## 第217輪：TW原生廣告路由與實際世界連線目的地

# 第217輪：台服原生廣告路由與實際世界連線目的地

修改5個既有C++檔，新增0個C++檔；來源串接段206→207，新增完整雙向玩法路徑0。上一輪有實際2新增／5修改，屬progress。台服完整來源串接100%才停止，完整分母與百分比仍未知。本輪只靜態恢復與來源修改，沒有build／test／native／codec／runtime／DB／SQL／deployment執行。

## 已接入的具體來源

RecoveredTaiwanServerAdvertisement原先只留下04 mask row，現在另保留完整已解碼04／05／06連續資料與原始接收順序；真正成功寫出的外層wire仍在Session private advertisement。新增primary_destination(Table,token,raw75)明確區分native table group／subgroup／實際configured count與儲存snapshot group／server，不把A6低BYTE或mask當目的地權限。

投影先取raw07第一個token低3bit相等的完整row，再取該row BYTE32非0路由key。按原生順序重放廣告：04重設endpoint counter但不清既有endpoint tail；05即使subgroup改變仍增加endpoint counter，每筆05重設route counter；06保存完整DWORD，查找只比最低BYTE，重複key取j0..9／r0..9第一個實體匹配。

使用原生0x260 subgroup／0x30 endpoint／4-byte route實體byte offset，而非彼此獨立的(k,j,r)容器；相鄰subgroup endpoint範圍可能重疊，最後實際byte寫入決定讀取值。初始配置endpoint區域按13FE3..1403B清零，後來重複04不再清零。沒有把重複記錄錯當account-latest或清除高tail。

這是明確的server-owned bounded primary subset：actual configured count1..10、subgroup<count、endpoint／route index<10、完整raw75且row count1..2、確實matched row／非0key。原生寫入端沒有同等index界限，不能把這些安全邊界冒稱原生總容量或已支援全部變體。原生12250 fallback與不完整來源保留OPEN，沒有改成默認目的地。

Session只在native_select明確選用的God2CharacterConnection，於constructor body讀取真正accepted socket.local_endpoint，保存不可變private session／mode／IPv4／實際port；全部Session atomic已初始化，沒有在Impl constructor提前存取未建構欄位。沒有public setter，不用remote_ip、config.port或factory前尚未listen的port候選。觀察失敗不改既有socket／認證結果，只讓後續明確來源缺失時拒絕。

Handoff Authority現在必須返回DestinationAuthority，包含實際native Table／configured count與Current。每個候選都核對原L實際A6低BYTE必要相等條件、原始完整廣告、已發raw07及真正G local endpoint；只有原生primary查找產生的IPv4／port與實際接受連線一致才繼續。caller仍須資格化實際table／source epoch／local backing變體與權限；低BYTE相等不是原始UI WORD高位或配置來源證明。

Link.current攜帶完整native Table與Destination（完整05 body8／06 body4及row／j／r），重查全部候選時要求來源與實體查找結果完全相同。保留獨立G00帳號認證、Session private選角輸入、完整snapshot／roots、Live／Authority Current及候選歧義拒絕；沒有把L A6填進G Scope，亦沒有憑IP／port匹配創造帳號或角色授權。

## 原生依據與界限

原生子代理保留14段code，1048 bytes／342 instruction sites，另保留format literal12 bytes；新增全域原生覆蓋與opcode0。S05 logical9／body8：body0 subgroup k、body1 opaque、body2..5 IPv4、body6..7 unsignedLEport。S06 logical5／body4：低BYTE為lookup key，剩餘3 bytes仍opaque。從12310／130E3／13165／12440／11D30追到真正獨立G connect參數；formatter、assert、logger／status內部保持opaque，沒有API執行。

目前仍需真正配置／issuer生命週期與權限政策、完整raw07 issuer與創角後來源、localbacking／clamp／fallback及較大配置變體、全2A／initial scene／5D／Main正式選用。新的端點對應不能取代admission CAS、防重播或parallel-G結算租約，前後Current也不是wire寫出瞬間原子。未正式掛載或驗收。

TW盤點C2S156；world S2C252（fixed230／variable22）；battle S2C110，83 actions23／86 selectors7。CN C2S156；S2C phase rows280（account6／world206／battle68）。盤點與來源段數不代表完整玩法分母。全方向／狀態／變體／deferred、其餘台服13組玩法、numeric64及stack99仍待接通；保留CN／web、共用資料表、存檔、聊天、認證、IME、原生字體與轉換。全部來源串接後才全面測試與修復。



## 第218輪：TW實際配置表來源與世界連線槽位

# 第218輪：台服實際配置表來源與世界連線槽位

新增2個、修改4個C++檔；來源串接段207→208，新增完整雙向玩法路徑0。這輪實作配置來源、Handoff消費與實際Context組裝，屬progress；全遊戲與台服完整路線分母、完成百分比仍未知。依使用者最新指示持續台服優先至實際完整來源串接100%，不在輪末暫停；全部串接後才集中測試。本輪沒有build/test/native/codec/runtime/DB/SQL/deployment執行。

## 接入的來源

新增TaiwanNativeClientGroupConfiguration，限定原生149c1b45…固定來源。TW11BB0以initial_host前8 bytes是否192.168.、TW531C10的實際WORD59DFD8==4且WORD59DFDA==2，選config.ini/config_gb.ini/config2.ini/config2_gb.ini。兩個WORD是實際呼叫端輸入，不推論Windows語系，也不採用CN的constant-false helper或config_2命名。明確供應已解析的絕對client root；沒有模擬未知native path formatter或從process cwd猜路徑。

復用既有TW TaiwanNativeResourceSelection，完整保留Request、candidate/original路徑、probe、branch、encoded原件與已打開的candidate原件。只在Candidate0516分支使用本輪由TW00401D20獨立恢復的有界ring解碼來源；OriginalAfterOpenFailed/Non0516按純文字原件處理，即使原檔前兩bytes恰為05/16，也不能重新探測並解碼。firstcandidate原先漏掉這個branch條件，子代理指出後已在真正final補正；兩個實體epoch分開保存，沒有冒稱候選就是final。

新來源保存完整decoded bytes及不可變ordered groups/slots。TW12740每個group配置0x1804 bytes、count在+40、row stride0x260，最多10 slots、64 groups。無等號的非註解內層列仍消耗一格並保存空name/value；duplicate labels各自保留ordinal；空group/count0保留觀察，使用時拒絕無可用槽位。槽位數不取決於位址有效、廣告05筆數、mask或儲存server ID。

原生rt FILE的CRLF翻譯與parser分開；前置只trim TAB/SPACE，內層blank line結束group，註解;/#跳過，下一個[直接轉外層解析，10列後回外層。$只在外層解析；TW failed %d保留network+650舊值，不能照CN歸零。owned subset拒絕failed/partial/overflow整數、NUL、0x1a、lone CR、超127byte line、無終止LF/未閉合label及過長欄位，保留原始bytes。這些是安全實作限制，並非原生已有防護或完整錯誤分支仿真。CRT非ASCII locale whitespace、64組以後尾端、外層@/^/-含義仍未資格化。

Handoff現在強持shared_ptr<const配置>，create必須提供實際配置與相同固定client來源。Authority只供native group/subgroup及Current，不再能任填configured_subgroups；resolve從不可變配置導出count，目的地前後核對也再次比對同一count。既有完整04/05/06實體偏移重播、raw07 primary key、獨立G private accepted-local endpoint、帳號/roots/snapshot、Live、歧義拒絕與全候選Current保持。configuration值只限定查找域，不創造角色、帳號、native UI WORD高位或權限。

新增ListSources::with_configured_handoff，在真正SharedWorldHostPlan::Context工廠內取相同accounts/characters/native_character_summaries建立owner，保留build/capacity/config/Live/Authority/Target/Qualify強依賴。沒有保留借用Context，沒有替Main選用不完整plan，沒有預設成功或臨時造list。

## 證據及未完成部分

原生子代理保留12段有界code、2061 bytes/668 instruction sites，另7段data/162 bytes；封存62 members+seal，獨立TW wrapper/decoder/parser/selector來源，新增全域coverage/opcode0。另一子代理保留initial27完整依賴、firstcandidate6與真正final6進行靜態來源審閱；全部只是原始檔與雜湊盤點，沒有執行解析器、codec或任何測試。

原生2530確實會解碼到真正暫存wb，再reopen rt，忽略decoder bool；reopen失敗可fallback原檔。owned source對選中壓縮檔錯誤直接拒絕，不重現暫存副作用。原生cache在已載入global count>0時不重讀，現有物件是不可變first-load來源模型；真正startup operands/cache epoch與issuer Live/Authority仍須正式供應。空原檔繼承既有ResourceSelection的拒絕限制，不能宣稱完整支援原生empty-file成功。未解碼或啟用現有Data3檔案，未更新歷史原生基準。

完整raw07/創角後issuer、localbacking/clampedtoken4..7/fallback/較大配置變體、one-time admission CAS/replay/parallel-G、完整2A/initial scene/5D/Main正式選用及其餘玩法仍OPEN。前後Current不等於wire寫出瞬間原子，不可因新增配置來源就稱登入/世界路線100%。

TW盤點C2S156；world S2C252（fixed230/variable22）；battle S2C110，83 actions23/86 selectors7。CN C2S156；S2C phase rows280（account6/world206/battle68）。這些是分階段opcode盤點，不能直接相加當玩法分母或拿來源208段換算完成度。其餘台服13組玩法、numeric64、stack99與完整方向/狀態/變體/deferred分母仍待接通。保留CN/web、共用資料表、帳號存檔、聊天、認證、IME、原生字體、文字轉換及既有凍結功能。



## 第219輪：TW角色清單實際issuer與共用寫入接線

# 第219輪：台服角色清單實際issuer與共用寫入接線

新增2個、修改6個C++檔，來源串接段208→209，新增完整雙向玩法路徑0。上一輪有實際2新增/4修改，屬progress；本輪持續台服優先至真正完整來源串接100%才停止。台服與全遊戲完整分母、百分比仍未知。只做靜態恢復、來源實作及檔案雜湊盤點，沒有build/test/native/codec/runtime/DB/SQL/deployment執行。

## 實際呼叫鏈

新增SharedTaiwanNativeCharacterOfferSource，讓真正TW完整75-byte logical07、實際visible ordinal對應的common64ID、revision/source origin與mandatory issuer，經既有SqliteNativeCharacterSummarySnapshotRepository::replace_from_issuer落入共用原始交付儲存，再由既有TW native List讀取及傳送。Offer不是實驗candidate，也不從create/profile40推測raw36、補零或把common slot當選角token。

SharedWorldHostPlan::Context新增typed writer能力。Application在已有requires_native_character_summaries明確選用時從同一SqliteDatabase取現有lazy writer，確認它與reader確實同一物件。accessor本身不做SQL/DDL；沒有新資料庫、schema install或migration。HostOwner保持exact writer identity，StoredSources::ListSources可明確提供實際Offer supplier，create_from_stored_entry直接組成OfferSource→List Prepare，並非無caller的孤立wrapper。Main仍未選用未完成plan。

List只在list呼叫的read(...,true)執行Prepare：先保存完整common roots、取得並核對真正Target，再調actual issuer，成功後讀fresh committed tuple。Select、Current、write-completion都不呼叫Prepare，不會暗中寫入。prepare false/throw/來源變動時直接停止這次列表，不退回舊snapshot發包。舊明確read-only供應路徑在未選Offer supplier時保留。

Offer先按原始75/07/count/ordered bindings及common ownership檢查，TW只接受CommonIdentity、不採CN role22/NativePromptMarker。名字只從實際root.name_codepage原名嚴格轉至CP950，再比對原生前NUL字串；不做繁簡顯示轉換、不變更名字、不推論page0是950（page0只允許ASCII無歧義）。所有postNUL、header flags、unused/inactive rows、route、token高位、appearance及resource bytes原樣保存。可見順序由issuer提供，不照common ORDER BY slot重排。row count<=2與token<=3仍是現有transport有界子集，不是原生全容量證明。

Prepare強持實際來源與owned Scope/Target/complete roots/expected/next/issuer。writer使用原有expected-fulltuple CAS、complete roots以及Prepared/BeforeWrite/BeforeCommit observer。每個observer前後檢查parent的Session/Scope/Target/roots與reentry poison，防止供應者捕獲重入例外後仍commit。這個guard不比較old stored snapshot：BeforeCommit處於staged-next，實際writer自行核對該完整next，避免錯拿old Current讓合法staging必敗。

writer commit返回後不再呼叫provider、reload或自動重試；後續List Current仍可能拒絕發布，但不能假稱已回滾durable commit。此接線也不是客戶端收到/處理ACK、選角一次性admission、wire瞬間原子或正式啟用。

## 原生欄位與缺口

原生子代理保留21份完整實際來源及211..215的既有有界證據，4段298 bytes/106 instruction sites；新全域coverage/opcode0。per-row-field-qualification逐欄說明：只對common ownership/實際64ID及原名可做強資格化；W17↔C29等appearance既有關係仍是matching-consumer inference，沒有官方serializer或copy來源證明。W19 token不等於common slot，W32要真實廣告route/resource Current，inactive row及opaque flags不能自動清零。不能把RecoveredCharacterListCandidate升格為原生issuer。

第二子代理保留initial37加later-read unchanged7完整依賴、實體candidate8與真正final8；核對Application→Context→Host→OfferSource→List的實際可達來源。原生peer封存較早的ListSource原件在root修改後成為歷史epoch，保留原seal與全份原件，另以root/account的fresh current來源及epoch-reconciliation明確對照，不偷偷刷新peer或歷史基準。

實際issuer/visibility/ordered metadata/resource/revision policy實例仍待供應；native_select現在回commonID，至world_entry還沒有typed admission ticket。SharedWorldAdmission的32-bit Key/永不重用模型不能把TW低3bit token、常數0或推測TTL塞入冒充原生授權。one-time CAS/replay/parallel-G、postcreate/localbacking/clamp/fallback、完整2A/scene/5D/Main與其餘玩法仍OPEN。此輪不改凍結Session選角/聊天/認證結果，未執行任何來源。

TW C2S盤點156；world S2C252（fixed230/variable22）；battle S2C110，83 actions23/86 selectors7。CN C2S156；S2C phase rows280（account6/world206/battle68）。這是方向/階段opcode盤點；來源段209、parser branch64.6%都不能當全遊戲完成度。保留CN/web、共用資料表、存檔、聊天、IME、認證、原生字體與文字轉換；完整TW方向/狀態/變體/deferred分母、剩餘13組玩法、numeric64/stack99仍待接通。全部來源串接後再全面測試和修復。



## 第220輪：TW實際選角來源與世界入口接線

本輪把台服實際選角的完整來源接到世界入口。原先 native_select
只回傳共用角色 ID；現在同一個來源另保留私有建構、不可變的 Selected，
包含實際 Session 的選角輸入、已發清單、完整75位元組快照、全部共用角色
根資料及完整角色 ID。入口取得同一張 Selected，於取得原生入場資料前後
以及其 Current 前後重新核對。沒有新增或改寫原生封包欄位。

Selected 只保留純資料與弱來源生命週期。容量有界的 game-owner 登錄保存
弱 Session 與實際 Target/Link/資格判斷；對外 Current 只保存弱登錄來源。
同樣的三個 ID 不能替代同一張 Selected。新選角先撤下同 Session 舊記錄，
失敗不能重用舊選角；過期或關閉 Session 由真實生命週期觀察清除，沒有
自行發明原生 TTL。所有外部判斷前先複製登錄資料，不持有 map iterator。

原生 Session 的既有次序保持不變：Authenticated、character_id 為0時，
實際 native_select 之後呼叫 world_entry，成功後才設定 character_id。
入口仍要求完整共用 ID 等於2A的14位 actor handle，超出者拒絕；沒有
把 token、slot 或截斷 ID 當角色身分。完整角色 profile、編碼、建立時間、
權限與位置 revision/map 都參與目前來源判斷。原生完整40位入場 frame
與不透明欄位保持原樣，Selected 不能產生缺失的 frame 或補零。

SharedTaiwanStoredWorldEntrySource 的 Scope 比對增加 Selected 指標身分。
實際 HostPlan 同時保留並轉交選角來源與入口來源。Application vault
補上原生 Entry 中巢狀呼叫被供應者捕捉的情況：先標記，再於外層入口
回傳前拒絕；舊有未選原生角色來源的入口維持原行為。

本輪新增 C++檔0、修改7、來源接線段增加1（209→210），新增完整雙向
遊戲路徑0。沿用8段、2308位元組原生證據，沒有新增 opcode、原生覆蓋
或路徑分母。台服觀察值仍為 C2S156、世界 S2C252（230固定、22可變）、
戰鬥 S2C110；這些是不同階段的觀察值，不能直接相加當遊戲功能總數。
陸服 C2S156、分階段 S2C280 保留。本輪不宣稱整個選角/入場玩法完成。

仍需串接實際 issuer/可見性/資源與完整2A供應策略、跨G/重播/並行 admission、
回傳後 queue 與場景 publication 的來源一致性、Main 明確選用，以及其餘
世界/物品/任務/戰鬥等完整權威路徑。Selected 是入口使用前的來源核對，
不是一次性 admission CAS、網路原子性或客戶端確認。全遊戲方向/狀態/
變體分母尚未封閉，TW/全遊戲完成百分比保持未知。

本輪只有來源修改、靜態原件/差異閱讀和檔案雜湊封存；沒有建置、測試、
原生程式/codec/runtime/DB/SQL 執行或部署。保留台陸網頁共用核心、帳號
存檔、聊天/IME/認證/頭像、原生字體與繁簡轉換、等級及既定數值擴充方向。
目標保持 active，依2026-10-10指示優先完成台服全部實際來源路徑再停止。



## 第221輪：TW完整入場issuer與共用寫入接線

本輪把實際完整台服2A資料供應者接到既有共用資料庫寫入器，再由世界入口
讀取剛取得的完整資料。新增 SharedTaiwanNativeWorldEntryOfferSource：
供應者必須提供完整原生40位元組 frame、共用角色根資料、實際儲存位置、
正遞增 revision、來源雜湊/記錄與真正 issuer。沒有候選 frame、補零、
不透明欄位推測或僅憑座標放行。

實際 Application Context 現在提供與 native_world_entries reader 同一
物件的 writer；沿用現有 accessor 與連線，不安裝 schema、另開資料庫
或更動一般登入。明確選用 entry_offer 的 StoredSources 必須同時具有
原生選角來源。HostPlan 將 Prepare 接到入口取得 NativeSource 之前；
未選用的舊入口保留原行為，Current 純讀不呼叫 Prepare。

Offer 擁有完整 Scope/Selected/資料與回呼，重查同一選角、完整共用根資料、
位置 revision 與 map。寫入沿用 existing expected-fulltuple CAS 與
Prepared/BeforeWrite/BeforeCommit；parent Current 在 issuer 前後核對
選角/根資料/位置/map，不比較舊2A tuple。BeforeCommit 此時資料庫裡是
staged-next，舊 snapshot 可以保留舊 profile/位置作 CAS 見證，next 才必須
等於本次 Scope。交易提交後不再呼叫 provider、重新載入或重試；稍後來源
失效可抑制發送，不能冒稱已回滾持久寫入。

來源閱讀另發現：舊 vault Entry caught-reentry flag 只在入口回傳後檢查，
issuer 位於 Selected Current 兩次呼叫之間時，單靠 active guard 可能
無法在提交前知道巢狀呼叫已被捕捉。本輪增加精確 invalidate_selection
(sessionID)，由 Application 在 Entry 巢狀拒絕時先撤銷該張登錄，再經
HostPlan 傳遞。下一個 parent Current 因登錄已撤而拒絕，能在 COMMIT
前中止；不影響其他 Session 的選角記錄，不把撤銷說成一次性 admission。

新增 C++檔2、修改8；接線段210→211，新增完整雙向遊戲路徑0。沿用8段、
2308位元組原生證據，新增 opcode/覆蓋0。台服 C2S156、世界 S2C252
（230固定、22可變）、戰鬥 S2C110；83動作23、86選擇值7。陸服 C2S156、
分階段 S2C280（登入6、世界206、戰鬥68）維持。不同階段觀察值不當功能
分母，TW與全遊戲百分比仍未知。

完整不透明2A資源/狀態 producer 與真實 issuer policy 仍須供應；此接線
不等於已取得全部原生資料。一次性/跨G/重播/並行入場權限、回傳後 queue/
場景 publication、Main 明確選用、其餘世界/物品/任務/戰鬥與完整方向/
狀態/變體分母仍 OPEN。保持台服優先、共用核心與既定台陸網頁支援。

只做來源修改、靜態來源閱讀與檔案雜湊記帳，未建置、測試、執行原生程式/
codec/runtime/DB/SQL、遷移或部署。保留帳號存檔、聊天/IME/認證/頭像、
原生字體、繁簡轉換、等級與數值擴充方向。目標 active，台服全部實際來源
路徑達100%後才停止。為維持 Desktop/God2 低於50GB，新完整帳本與計畫
原件另存 task-owned 外部封存位置，逐一以絕對路徑/大小/雜湊記錄；沒有
移動、刪除或改寫任何已封存歷史原件，外部原件也不是只存 receipt。



## 第222輪：TW入場前共用角色占用來源

# 第222輪：台服入場寫入前接上共用角色占用來源

本輪實際修改3份既有C++來源，新增0份C++來源；來源串接段由211增至212，新增完整雙向玩法路線0。台服與全遊戲完整路線分母、完成百分比仍未知，不能將212段或opcode盤點當成完成率。

`SharedTaiwanWorldEntrySource` 的原生選角路徑現在要求傳入與實際角色儲存來源相同的 `SharedWorldPresence`。`SharedTaiwanNativeWorldHostPlan` 傳入實際共用Host的同一Presence，並由Entry持有；未選用原生角色來源的既有路徑維持原本配置。

Entry在讀取共同角色根、存檔位置與地圖前後檢查完整角色ID的既有占用紀錄。這個Current同時包住第一次外部原生供應、完整2A Prepare，以及既有issuer的Prepared、BeforeWrite與BeforeCommit邊界，因此已占用的角色不會先執行入場資料供應與寫入，再等較晚的生命週期準備才拒絕。

檢查沿用現有服務端規則：尚未ready的Prepared、活躍與尚未由原世代Lease釋放的紀錄都算占用，同session也沒有例外。不會因儲存根變更而刪掉紀錄，不會取得、接管或釋放Lease。實際Session仍在同一game callback中依序選角、取得Entry、設定character_id、呼叫原生命週期prepared；其供應來源契約要求同步且不泵事件。此處是使用前的純讀取檢查，沒有新增入場CAS、Issued一次性消耗、跨G重播權限或網路回覆原子性。

同Presence下的CN/TW Lease可以共同排除相同角色；不同角色的actor_handle碰撞仍由既有較後方presence.prepare拒絕。本輪沒有宣稱擋完全部admission衝突，也沒有完成所有CN入口。完整原生opaque/resource/status issuer、實際Main選用、場景回覆與其他玩法仍OPEN。原生40位元組2A、共用ID與原生actor欄位規則不變。

兩個靜態帳本工具新增可選的外部完整封存方式：新catalog的完整輸入、原生來源與大型輸出仍保留全部原始位元組，local manifest逐檔記錄絕對位置、大小與SHA256；不是用收據取代原件。Report只接受所屬封存區內、唯一完整pin且與當前ledger逐位元組相同的來源。舊catalog與歷史封存不改動。

盤點維持TW觀察156個C2S值；世界S2C表252個有效項（230固定、22變長）；戰鬥表110項（9特別分派、101預設），83動作23項、86 selector7項。這些是不同階段與分派層級，不能相加成全遊戲封包總數。CN保留156個C2S值與280個階段S2C項。尚有13個TW來源缺口類別；新增完整路線0，部署及原生驗收0。

僅做來源串接、靜態來源閱讀與檔案封存盤點；未建置、未執行測試、原生客戶端、codec、遊戲、API、資料庫、SQL、遷移或部署。維持台服完整串接100%之前持續工作的使用者指示，CN/web與存檔、認證、聊天、IME、頭像、字體及文字轉換保持既有範圍。



## 第223輪：TW2A場景bank資料來源研究

# 第223輪：TW2A原生資料來源與場景bank分離

本輪是有界靜態來源研究：C++新增0、修改0、來源串接段維持212、新增完整雙向玩法路線0。未建置、執行測試、客戶端、原生程式、codec、遊戲、API、資料庫、SQL、遷移或部署。台服與全遊戲分母、完成百分比仍未知；目標保持active，台服實際來源100%之前繼續。

本輪新的可操作結論是入場body B[24..27]的高WORD，不能由共同地圖資料或角色HP臆造。對149c原生映像的兩個純資料查表leaf做精確靜態閱讀：45AA70..45AAE6取area低BYTE、scene低WORD，在17個area、9941位元組stride、142位元組scene record中找第一個匹配；45A000..45A04D取area低BYTE、scene低WORD，在17個(count,pointer)根及12位元組scene descriptor中找第一個匹配。兩leaf不使用高WORD，但後續scene呼叫仍可能接收它，因此只證明這兩個查表入口的窄化，不能宣稱整個B26..27無用或清零。195位元組是既有原生範圍的本輪保留，不當作新的全域原生覆蓋。未進入scene/UI/render/font/formatter callee。

兩個入口實際指向不同的資料表：

| 原生入口 | 真正來源 | 既有來源結果 | 正式來源缺口 |
|---|---|---|---|
| 45AA70 | gamedata 的 NPCList，row loader 45A91D..45AA3F | 451來源列、251場景群、1509資源碼；依列序追加(category,ordinal)資源對 | 沒有正式的NPCList場景群catalog。現有NPCAppearData是另一張表。 |
| 45A000／45A0A0 | gamedata 的 EnyName，loader45A1A0 | 7815原始列；重複area替換後7791可見列、96場景群；scene descriptor12B、顯示record26B | NativeEnemyDisplayCatalog已有完整來源與逐列lookup，仍缺場景有序descriptor／26B bank供應API。 |

`tools/strike_lab/import_native_enemy_display.py` 的SOURCE_ROW明確釘定149c映像與原始／decoded gamedata雜湊；`NativeEnemyDisplayCatalog::counts()`資格化全7815列指紋及可見性。這是可重用的原始描述資料來源契約，不能把每列lookup當成完整bank，也不證明現有正式資料庫已載入。本輪沒有讀取資料庫。

`NativeNpcDisplayCatalog`與其importer則釘定6bf映像、NPCAppearData4043列、prefix28／570F0。它不是149c的NPCList251群，不因同一gamedata檔名就能代替。EnyName的名字、資源byte、component及flags也不是怪物HP、雙攻雙防、技能、遭遇率、掉落或座標；那些權威數據仍另追。

另實讀目前安裝路徑 `C:/Users/risei/Desktop/God2/God2/Data2/Patch/Comm/gamedata.csvZ` 為3,131,095位元組，SHA256 `ef297a84e828537c4a18c5cf0be3d1c15bc26d5d2f25850ce9f2f030bdb58fa2`，與歷史同149c來源raw `70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`不符。未解碼或匯入它，未刷新舊基準；此差異阻止直接把目前路徑當作舊來源重建，沒有否定可獨立資格化的既有完整catalog。舊decoded pin為 `75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815`，本輪沒有宣稱其完整輸入已恢復。

角色數值亦保持分離：logical22為25B角色／四維／maxima資料，logical24為17B的HP、MP、maxHP、maxMP四DWORD；共同load_role與load_resources是獨立狀態來源。沒有證據能把它們寫入2A opaque B8..11。原生07的raw36、選取時複製40與create40也不相同，外觀consumer相似不足以授權完整serializer。historical_body、CUSTOM-0047及只覆寫少數profile/geometry的candidate不能變成真full2A供應器。

下一個實作切點已收斂為：同來源／section／occurrence identity的不可變NPCList有序群來源，以及EnyName的完整場景descriptor投影；保留重複area替換、空群、順序、原始列與build pin。再接實際preload/完整2A issuer與場景回覆，不拿NativeMapCatalog、顯示catalog或資源計數代替權限與玩法。

目前盤點維持TW C2S觀察156值；世界S2C有效252項（230固定、22變長）、戰鬥分派110項、83動作23項、86 selector7項。CN維持C2S156值、S2C階段280項。這些層級不能相加成全遊戲分母。純帳本工具本輪讓新的完整round report可存於專用外部封存區，local latest仍可讀，歷史報告與原件不改動。



## 第224輪：TW原生場景內容來源

# 第224輪：台服原生場景資源來源

TW先完成全部雙向來源串接，再集中建置／測試／修復；本輪只改來源，目標保持active。

新增 TaiwanNativeNpcSceneGroups.h/.cpp：實際供應的完整decoded原件先自有複製再核對75c3雜湊（4MiB界限），保留全文及NPCList原始451列、CR/CR/LF、行號／offset／列身分。17個area按首次場景出現順序建立251群，重複場景追加資源，空群保留，共1509個原碼。每資源保留原int32 code及原列／欄位置，另依149c的45A91D..45AA3F產生商／餘數低BYTE；低BYTE投影可能有損，不能充當共用實體ID。查詢scene使用WORD完整比較，不將256以上別名成BYTE場景。不合成142B原生記憶體padding。

原生45A8F0對area只有signed>=17檢查，新群寫scene低BYTE及count0；並未證明negativearea／新群70上限／unused尾部clear。原生對非正code停止該列，滿70資源跳過後續寫入，sscanf('%d')允許尾部未消耗。新來源明列較窄的owned安全子集：area0..16、scene0..255、2..7完整ASCII整數欄、正int32 code及70群／70資源界限，reject而不重現越界或靜默丟棄。這些守衛不是聲稱原生本來有完整輸入驗證。五段579B純資料loader/token邊界保守列作已覆蓋證據，不增加全域native覆蓋；兩段195B既有query leaf直接引用223封存。

NativeEnemyDisplayCatalog新增Scene/read_scene(area,scene)：同一CatalogReadScope先完整核對7815列（含24 superseded）、7791可見／96群的既有指紋，再從main表一次取得該場景所有可見列，依ordinal排序，保留完整raw/provenance／generation／source occurrence。拒絕temp影子與main缺schema，既有counts()/lookup行為保持原樣。未載完整catalog回nullopt；完整資格後查不到該場景回帶來源的空Scene。精確source tuple為149c／70a4／75c3／EnyName／0x5a1a0／0x5a0a0。這是場景名稱／資源資料，未生造26B bank、位置、怪物HP、雙攻雙防、技能或掉落。

現有encoded gamedata是ef297／3131095B，與歷史70a4不同。本輪沒有解碼、匯入、恢復歷史原件、查真資料庫或偷偷換基準。NPC factory要求真實供應的完整75c3 decoded內容，其絕對路徑只是該供應原件的來源；historical_encoded_sha256是歷史metadata，不表示encoded檔目前存在。EnyName可使用既有完整資格catalog契約，但本輪沒有聲稱正式DB已載入或新API已啟用。

本輪2新增＋2修改C++檔、1個實際來源增量，累計來源段212→213；新完成全雙向玩法路徑0。TW已觀察156個C2S；world252有效分派（230定長／22變長，另4不支援）、battle110（9專門／101預設），是不同方向／階段的盤點，不能相加當全遊戲總數。65個解析分支中42個已review（64.6%僅解析分支review率）。TW／全遊戲完整路徑分母與完成率仍未知（null）；958端點／28群是當前跨版靜態帳本，也不是遊戲完成分母。

下一步把這些實際完整場景內容接進入場的完整2A資源／狀態issuer，保留尚未解出的B26..27與其後scene呼叫邊界；不得用NPCList或EnyName推猜完整40B封包。一次性admission／lifecycle／scene／reply與Main實際選用，以及PK、邀請、傳送、寵物、每日、同伴、活動、商店、對話與觀戰等全部剩餘TW路徑仍OPEN。保留共用核心、CN／web、數值64位、仙幣99999999999、合資格堆疊99、native字體／文字轉換及凍結功能。

本輪無build／tests／native或VM執行／codec／server／DB／SQL執行／migration／deployment。大型新增完整原件與報告存於本任務外部archive，歷史封存保持原位；來源與證據計量只讀，不充當遊戲驗收。



## 第225輪：同一Application場景內容接入入場來源

# 第225輪：同一Application場景內容接入入場供應來源

新增實際資料流：Application同一SqliteDatabase既有EnyName reader → Context.native_enemy_displays → StoredSources::scene_entry_offer → with_scene_content → 完整SceneSupply → 既有Offer／writer CAS／stored-entry讀回流程。NPCList由224的完整75c3 decoded不可變原件供應，EnyName由224的完整資格場景讀取器供應。本輪修改6個既有C++檔，新增0；來源段213→214，新增完整雙向玩法路徑0。目標保持active，台服全部串通才停止。

SceneContent私有建構並只公開readonly資料，強持完整NPC原件及擁有完整EnyName Scene（完整source tuple、raw列、ordinal、generation、source occurrence）。真正封包producer收到這些實際完整內容後仍必須提供完整40B2A及真實Issuer。NPC群缺席／空群、完整EnyName下的缺場景是資源觀察，不能自動授予入場；EnyName全目錄未載回nullopt，無fallback空bank。area保持入場1..16，scene保持原2A可表達的0..1023；NPC對256..1023仍WORD完整比較而缺席，不窄化到BYTE別名。

供應前後及原writer的Prepared／BeforeWrite／BeforeCommit三個Issuer邊界前後重新比較完整EnyName場景觀察，同時保留強NPC原件及exactissued完整snapshot。三階段仍呼叫原始真正Issuer；資源Current不能代替原生權限／規則／完整狀態。新SceneState同步owner／caught-reentry拒絕，callback入口先強持owner／content／issuer，不以catch後的true資格復活。原Offer::create的common-root／position／Selected／Presence與完整tuple CAS流程保留，不在BeforeCommit比較已過時的old entry，不在COMMIT後重讀／provider／重試。

Context追加const catalog指標，預設null維持其他來源可建構；Application只在既有Context aggregate加入已migrated同一Database的既有無SQL／DDL accessor。Host Owner保留同ptr並在same(Context)比對；helper要求同writer／reader物件及實際account／character／common根。generic with_scene_content只是borrowedcatalog adapter，不能證任意reader／writer同連線；同DB與lifetime保證來自實際Application Context與既有game-owner vault drain。沒有新增Schema、資料庫表、migration、import或Main啟用。

本輪未替未知2A B26..27、高位資源／狀態、native142B／26B padding、場景權限、怪物HP／雙攻雙防／技能或spawn造值。現encoded gamedata ef297仍不是歷史70a4；未解碼／恢復／換基準，完整75c3 NPC輸入未聲稱現已載入。尚待真正完整SceneSupply producer、一次性admission、lifecycle／scene／reply、Main明確選用與全部剩餘TW路徑；這是來源鏈進展，尚非部署或遊戲完成。

盤點維持TW C2S156；世界S2C252（230定長／22變長，另4不支援）、battle110（9專門／101預設）、83動作23／86 selector7；65解析分支中42已review＝64.6%僅解析review率。CN C2S156／S2C280階段項（account6／world206／battle68）。跨版958端點／28群、38部分未hosting owner chains維持；不同層級不能相加當全遊戲分母。TW及全遊戲完整路徑分母／完成率仍null。

兩個子代理僅做靜態來源閱讀／原件封存；全新覆蓋bytes／opcode／完整路徑均0。本輪沒有build／tests／runtime／native或VM／codec／server／DB／SQL執行／migration／deploy。保留CN／web、共用資料與核心、64位共用數值、仙幣99999999999、合資格重疊99、原字體／文字轉換、accounts／saves／chat／IME／auth／portraits及全部凍結功能。新增完整root／agent原件與報告在本任務外部archive，Desktop只保留小型指標及catalog metadata，舊封存不移動不刪除。



## 第226輪：TW2A逐位來源與同版DA狀態寫入

# 第226輪：TW2A逐位來源與同版DA狀態寫入

本輪完成有界靜態資料流研究，C++新增0、修改0，來源串接段維持214，新增完整雙向玩法路線0。兩個子代理分別追原生資料流與36B來源對照；完整研究、來源原件和報告保存在本輪外部封存區。沒有建置、測試、原生／codec／遊戲／資料庫／SQL執行或部署。台服和全遊戲分母及百分比仍未知，目標保持active。

本輪訂正第223輪對B26..27的推論，保留舊報告原件。4682DB的IMUL先覆寫EDX，之後計數運算及未進入的4607D0呼叫使高位來源未資格化；4682F9只把AX搬到DX，468304也只右移DX。46830C傳給461AD0的完整EDX高位不是已證明來自B26..27。不能把未知高位改稱零，也不能推論B26..27全域無用或讓serializer任填。

完整1904B既有initializer內另見46865C的第四次B24 DWORD load；468660先將完整ECX複製到EDI，ECX經AND3F取area，EDI另經ANDFFFF再右移6取scene，兩條分支皆丟掉高WORD。未識別到B26..27直接持久scalar store；但46819C傳遞完整body目的指標，4684D6傳body+12給未知callee，alias可讀範圍未恢復。因此所有callee都不觀察高位的說法仍不成立。本輪保持461AD0、4607D0、461270及其他場景／GUI／render函式為閱讀邊界。

同一149c映像已找到2A與DA共同寫入的實際狀態：

| 2A body欄位 | initializer目的 | 同版DA payload來源 | DA寫入位置 |
|---|---|---|---|
| B32..33 WORD | R+4696 = W+1539AED2 | payload+2 WORD（logical3..4） | 503D4F／503D56 |
| B34 BYTE | R+4695 = W+1539AED1 | payload+4 BYTE（logical5） | 503D3D／503D40 |
| B35 BYTE | R+4698 = W+1539AED4 | payload+5 BYTE（logical6） | 503D46／503D49 |

DA實際dispatch表目標469369，長度表401252對應logical15。consumer先比較當前已綁定local actor，再以真正payload呼叫503D30；這是客戶端狀態選擇，不能代替服務端權威。只閱讀503D30..503D88純資料前綴。468315..468326清除R+90起的0x1141 DWORD，結束於R+4594，不覆蓋以上scalar；未據此宣稱整個後續生命週期不改寫。

36B完整對照表拆成54個mask部分，逐一區分consumer、共同來源、條件式對應及未知producer。已具共同來源的actor14bit、area6／scene10、x／y15bit仍須維持精確account／selection／position lineage，禁止截斷。B0／B4的資源與status、B8..11、B26..27、kind的權威產生規則，以及transform與兩個scalar的實際語義／合法狀態來源仍有缺口。名字、logical22角色資料及logical24資源數值各自接原有來源，不填入2A opaque欄位。

現有appearance view確實有2A→DA對應，但儲存契約釘定6bf／CUSTOM-0047及transform0，不能直接升格為149c正式producer。本輪獨立恢復149c DA寫入，沒有更換舊schema來源或修改凍結功能。下一步先追actual149c完整8個appearance components、transform WORD、兩個scalar的owned after-state issuer，再處理B0／B4資源status和其餘opaque；完整40B保存／CAS只能保留現有資料，不能產生缺失資料。

盤點維持TW C2S觀察156值；世界S2C有效252項（230固定、22變長）、戰鬥分派110項（9特殊、101預設）、83動作23項、86 selector7項。CN C2S156值、S2C階段280項。958個endpoint索引、214個來源串接段都不是完整玩法分母；完整雙向串接百分比目前不能可靠計算。背包stack99、仙幣99999999999、共用64位元數值、CN／web、原生字體及繁簡轉換保持既定範圍。

帳本工具新增完整metadata外部封存與本地精確雜湊索引，以保留原件並維持God2容量方向；所有歷史原件不變。這只改靜態來源記帳位置，不啟用服務、連線或測試。



## 第227輪：實際入場資料直接供應場景外觀基準

# 第227輪：實際入場資料直接供應場景外觀基準

本輪新增兩個唯讀C++存取器，修改2個header，新增C++檔0，來源串接段維持214，新增完整雙向玩法路線0。子代理分別獨立恢復149c原生資料流及審閱實際來源／caller。沒有建置、執行測試、原生程式、codec、資料庫／SQL或部署。台服及全遊戲分母、百分比仍未知；目標保持active，優先完成台服來源100%。

`RecoveredWorldEntryView::entry_appearance_baseline()` 直接從既有完整37B logical資料按值取得bound actor、B12..19全8個component、B32..33完整transform WORD及B34／B35兩個raw scalar。保留所有variant bit和非零transform，不經6bf／CUSTOM-0047型別、不補值、不encode或授權。`SharedTaiwanWorldEntered::Scope::entry_appearance_baseline()` 將同一view的投影直接提供給既有實際場景source；沒有新增資料表、callback、cache或獨立Current wrapper。

實際來源鏈是完整NativeWorldEntrySnapshot／entry Qualify→SharedTaiwanWorldEntrySource→Session生命週期→Binding或AsyncBinding保存完整view→SharedTaiwanWorldEntered持有的Scope→真正scene source讀取此基準。新增nested型別與member function不新增View／Scope資料成員，不改既有聚合初始化、送包、生命週期或凍結功能。來源的full root、position/revision、source／client／kind、完整40B、record revision及原writer CAS繼續各自資格化；存取器不取代它們。

本輪同149c靜態資料流確認：normal2A 468328／46833F將兩個DWORD保存至R+4584／R+4588；local DA的普通transform0分支在503FF4..504018將兩個完整DWORD寫到相同W+1539ADC0／C4。前面的502210及之後501810維持CALL閱讀邊界，其副作用與完整rendered after-state未恢復。B32..35同版DA寫入延用226的獨立原生證據，不借舊6bf測試結果。

remote DA不可稱為完整8B保存：4FC130只將incoming odd BYTE高3位寫到actor+251+2*i並保留原low5；override actor+61 bit10時只強制live variant7，該路徑不更新saved odd BYTE。4FD830先寫兩個raw scalar到actor+264／265，再呼叫component更新；所讀前綴未證明remote transform WORD的持久store。實際lookup必須先找到已有actor，128筆、stride0x268，缺席不spawn。純handle／variant setter與呼叫邊界各自保留，不進入GUI／render／場景函式內部。原生consumer行為不自動成為服務端權威規則。

這些值明確只叫「入場外觀基準」。後續DA及36／37事件會改變外觀，舊2A無法單獨證明當前after-state；原樣load相同witness也不能消除這個缺口。仍須真正同源觀察證明沒有中間mutation，或讓實際appearance mutation commit同步更新完整witness。新存取器不授DA發送、observer已出現、transform合法性或裝備到component映射；完整2A issuer、B0／B4、opaque欄位和全遊戲其餘路線仍待完成。

目前TW C2S觀察156值；世界S2C有效252項（230固定、22變長）；戰鬥分派110項（9特殊、101預設），83動作23、86 selector7。CN維持C2S156值、S2C階段280項。65個TW parser中42個具範圍限定來源分支，64.6%只代表該parser分支覆蓋，不是台服完整度。帳本仍不把958個endpoint、214個串接段或唯讀投影當完整玩法分母。

下一步追真正149c appearance mutation issuer及裝備／transform來源，維持同root／revision的完整after-state後再接DA與已出現observer；不以基準投影代替它。CN／web、共用表、64位數值、stack99、仙幣上限、原生字體、繁簡轉換與既有存檔保留。完整來源、原生切片、實際before／candidate／final和報告保存在外部封存區，本地保留精確雜湊索引。



## 第228輪：台服裝備外觀權威與原子提交接點

# 第228輪：台服裝備外觀權威與原子提交接點

本輪完成有界靜態原生／實際來源研究；C++新增0、修改0，來源串接段維持214，新增完整雙向玩法路線0。未建置、測試、執行原生／codec／遊戲／資料庫／SQL或部署。前輪的實際入場外觀基準存取保持不變；台服及全遊戲完整分母、百分比仍未知，目標active。

現有裝備→外觀→回包路徑有真正可參考的交易結構，但來源資格不能沿用：`SqliteWeaponSlotRepository::move`擁有同一BEGIN IMMEDIATE，先比對兩個完整slot及revision，更新並讀回，再呼叫PrepareExtra。舊Application在此callback內用`SqlitePlayerAppearanceRepository::save`借用SAVEPOINT保存外觀，預先編碼pair＋DA；兩slot再次讀回後才COMMIT。提交後才commit visibility與發送。這是現有實際caller，沒有執行它。

該路徑仍是6bf／CUSTOM-0046、CUSTOM-0047與兩個synthetic WPN實例；`fixture_after`不提供一般item→component映射，外觀repository限定transform0。armor路徑是另一c5d8 pin／CUSTOM-0066，只有instance及完整slot CAS，沒有外觀權威。不同EXE pin與來源不能因交易結構相似而升格成149c正式資料。一般`InventoryRepository`仍是reserved interface，`Inventory`仍placeholder；既有bag proof只限定背包格並排除部分instance類別，不是equipment after-proof。

本輪獨立核對同149c的4個既有原生範圍，共1436B／420指令位置，另保留3個宣告資料表共215B；全部是既有範圍的再資格化，不增加全域原生覆蓋。459420..459960 parser的CALL均維持邊界，不追UI／formatter／render。family1／2／25／26走同一已識別分支，numeric source26／27／28／29分別保存到metadata+11C BYTE／11D BYTE／11E WORD／120 BYTE；459933取+114 WORD，經459FC0有界RomMaps ordinal查找寫+116 WORD，+118設FFFF。459A60的低WORD key界限／pointer lookup沒有生成完整appearance component。

來源tag與metadata用途保持分開：本輪完整parser範圍的直接token callsite沒有找到WPN／TWP分支讀source1／2／30／31，未建立WPN tag到DA component的資料流；未知CALL及全client alias仍未全資格化，不能把這個有界結果當全域不存在的證明。歷史6bf differential結果保持歷史。icon／RomMaps ordinal、tooltip欄位、等級顯示與reach各有消費端，不能據名字、數字巧合或ItemType code直接推導HeroDoll外觀。原始tag表含重複WPN／EQU到default的表項，也不能任挑alias當family。NativeWeaponCatalog保存1259筆完整definition來源與396B metadata及指紋，並不持有玩家完整20B instance、裝備權限或item→外觀規則。本輪沒有查DB或聲稱catalog已載入。

完整入場witness的writer不能直接塞進舊PrepareExtra：`replace_from_issuer`要求autocommit並擁有自己的BEGIN；Issuer明確禁止SQL寫入。它資格化full root、position、完整record與revision，沒有inventory expected／revision。`SharedTaiwanWorldEntrySource`及entryOffer針對尚未入場的selection／presence，會拒已reserved角色，不是InWorld裝備提交入口。放寬該writer或套另一Current callback會丟失其現有契約。

共用`SharedActorVisibility`亦尚無149c裝備→DA更新API；舊`RecoveredVisibility::prepare_appearance`是production_disabled的CUSTOM-0027路徑，不能代替actual Binding的已出現狀態與incarnation。後續正式實作須使用真正共同inventory／equipment expected及來源revision、完整12B prior／after appearance、同庫交易owner；在Prepared／BeforeWrite／BeforeCommit核對來源及staged next，外層COMMIT後才由game owner發布。每個recipient仍須符合真正已出現Binding、generation／incarnation、Current與queue生命週期，不藉DA產生不存在的actor。

下一個實作切點因此是共同owned instance／equipment mutation owner與真正149c完整after-state來源，然後接完整witness、DA與actual visibility。不能直接重用測試武器、從icon／reach拼外觀、以舊2A基準當current，或再增加可插拔Current wrapper。缺失producer值保持OPEN；交易與資料表預設共用，僅證明不可共用的原生raw儲存才用_tw／_cn後綴。

盤點維持TW C2S觀察156值；世界S2C有效252項（230固定、22變長）；戰鬥分派110項（9特殊、101預設）、83動作23、86子型別7。CN C2S156值、S2C階段280項。214個來源段與958個endpoint不是完整玩法分母；本輪新增opcode／完整路線均0。CN／web、64位數值、stack99、仙幣99999999999、原生字體、繁簡轉換、帳號存檔及凍結功能保留。完整before、研究原件與報告外部封存，本地只有精確索引。



## 第229輪：台服DA實際角色綁定與送包入口

# 第229輪：台服遠端 DA 實際綁定與送包入口

本輪新增 `RecoveredTaiwanPlayerAppearanceUpdate`，獨立以同一149c原生映像的 DA15 格式持有完整實際來源 bytes；既有6bf fixture 介面保持原用途。`SharedActorVisibility::publish_taiwan_appearance` 接入真正的 private Binding、完整 Entry 觀察值、Session common-world identity 與 held queue。這是一個來源串接增量，尚未具備正式裝備交易呼叫端，新增完整雙向遊戲路線為0。

## 原生依據與限制

原生映像3174400B、SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`，沿用完整保留來源，沒有重訂舊基準。第229輪保留8段363B／114個指令位置及2個指標8B，新增原生覆蓋0。

6F consumer 的 payload+14h（logical21..28）先完整存入 actor250/254；payload+4Ch（logical77/78）存 actor262；logical79/80 對應 actor264/265。DA 的實際遠端4FC130只改每個奇位元組的高3 bits，保留其低5 bits與偶位元組；actor61 bit10 的特例還會跳過該保存動作。DA scalar5/6 對應264/265，但 DA transform3/4 是否寫入遠端262尚未證明。不能從同名欄位或舊預覽測試宣稱全部遠端快取已還原。6F 的低12位 actor identity 與 DA 完整WORD查找也必須透過實際綁定，不截斷共用資料庫ID。

因此本輪保留完整入場6F，新增不可變的「最近DA發布紀錄」。紀錄包含完整15 bytes、實際權威來源 revision 與 provenance，只代表發布歷史，不是假造 after6F／完整原生快取。舊完整 Entry token 比較該紀錄 identity，更新後即失效；移動仍只投影已確認的位置。重新出現／重新入場的完整6F必須重新由真正來源供應，不以舊入場6F或DA紀錄重播最新完整外觀。

## 實際來源接點

單一已出現的台服收件角色使用不可自行構造的 Binding，完整保存 before Entry、強收件 Session、座標、common-world generation 與 battle generation。必要的 `TaiwanAppearanceSource` 必須每次返回完整已提交 afterstate（DA record、正值且逐次增加的實際來源 revision、1..2048B且無NUL的 provenance），不能只返回 bool Current。Prepare、held publish 前、發布紀錄安裝後與 queue release 回呼均重新讀取並要求完全相等；所有外部讀取前後都重查同一個完整 Entry／transport／presence。

pending owner map 擁有真正 provider、completion、強 Session 及 registry keepalive；跨 IO 的 facade 僅持 weak registry、固定 key 與不重用 nonce。紀錄與 full after-token 在 IO 前配置，held publish 只安裝預配置紀錄，然後才讓 Session 放行 DA。實際 provider 的呼叫副本在 game owner 執行與析構。巢狀 publication 會令原操作失效；相同 pair 的 show、移動準備、完整移動集合與 advance 在 pending 期間拒絕。

hide、reset、release 會取消精確綁定的 pending；顯式 drain 用於 executor 停止前。取消入口及完成函式保留 owner 直到整個方法結束，避免完成回呼解除最後外部 owner 後使用已析構的 registry。drain 期間拒絕新的發布。未送入 IO 的準備失敗保留既有角色；已 issued 的失敗只移除原 incarnation 並關閉原 receiving generation，不能移除新 incarnation、重送裝備變更或回滾已 durable 的交易。

成功只代表本地 held queue 放行，不代表 socket 寫完、客戶端收到或畫面驗收。原生自角色 DA、完整TW/CN觀察者 fanout、CN格式與跨版本外觀映射不從這個單一TW入口推定；CN變體明確不適用，既有CN功能保留。

## 尚缺的完整路線

真正同資料庫的共用裝備 instance／slot mutation、完整 before/after row與來源revision、實際 item→12B外觀 afterstate、outer durable COMMIT 與此入口的正式呼叫仍未供應。原生規則／資源資格由該真正來源負責；字串provenance、DA解析或任意callback均不自動成為權威。入場baseline、舊6bf/c5d8測試資料與 SAVEPOINT release 都不能代替它。pending 必須在 executor 停止前 drain；正式 Application retain/drain／綁定及Main啟用仍為OPEN。

另有完整2A來源、once-Issued admission/lifecycle、13個世界玩法分支與全遊戲狀態／變體分母未完成。來源段214→215只是部分來源段累計；台服與全遊戲完成率仍為未知。本輪1個新增C++來源檔、2個修改檔、0條新增完整雙向路線；沒有建置、測試、原生／codec／遊戲執行、資料庫／SQL、遷移或部署。目標保持active，優先台服完整串接，再集中測試驗證。



## 第230輪：台服完整裝備呈現快照、提交憑證與DA來源

# 第230輪：台服完整裝備呈現快照、提交憑證與 DA 來源

本輪新增完整原生裝備呈現快照的實際 SQLite 儲存、完整 tuple CAS、outer snapshot COMMIT 後私有憑證、同 Application Context 接點及第229輪真實 DA held-queue 呼叫端。這是版本化 delivery witness，不是共用道具權威、裝備規則或完整裝備交易。正式裝備 handler、物品取得／入庫與 item→完整外觀來源仍未供應。

## 原生範圍

仍使用3174400B、SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763` 的原件。本輪保留7段1021B／285個指令位置，新增覆蓋0；舊6bf動態病例不重跑，也不當目前149c證明。

C28 是 logical5：opcode、item低WORD、source低BYTE、flag低BYTE，沒有目的格、持有者或完整實例；已觀察 caller flag1也含卸裝，不能當 equip boolean。C24只帶兩個低BYTE格號，client panel gate不代表服務端權限。3B logical25帶count、slot、opaqueWORD與完整20B實例；consumer依metadata決定count1或8-bit加法後signed比較30，因此不能當安全絕對數量快照。41的signed count<=0只清count與實例低WORD，保留其餘18B。

兩個consumer直接限定格號0..49，以24B步幅存放完整20B實例到row+4，count在row+0。row+1..3仍未知；3B opaqueWORD沒有證據等於此prefix。新快照保存**全部50×24=1200B原始快取**，再附完整實際DA15，共1215B，不填零、不截尾、不把3B/41封包當完整快照。普通武器slot34的已確認metadata+120是reach，仍不構成item→DA對應。

## 實際儲存與提交

`NativeEquipmentSnapshot` 持有完整common root、當前saved position／revision、獨立native actor handle、client/source SHA、來源紀錄、嚴格正值revision及全部1215B。共用64位character ID與native handle分開，DA完整WORD必須吻合handle，不能截斷ID。資料只屬版本化呈現證據，沿用單一 `character_native_equipment_snapshots` 表按client/profile key保存；沒有複製角色、道具或裝備玩法資料表。

`SqliteNativeEquipmentSnapshotRepository` 必須使用同一個實際SQLite account／character來源。writer拒絕借用交易與caught reentry，自己持有BEGIN IMMEDIATE，對完整expected tuple比對，確認實際common root／saved position及pending battle。必要issuer在Prepared、BeforeWrite、BeforeCommit各返回完整next，必須完全相等；呼叫前後查完整原件、common root、position、交易狀態與SQL total_changes。issuer不得寫SQL、提交交易、yield、pump或發包。BeforeCommit讀staged next，不錯比舊before。

私有 `Committed` 憑證與完整owned snapshot在COMMIT前配置，成功outer snapshot COMMIT後才返回；COMMIT後沒有provider呼叫、重讀、配置或重試。token綁定不可複製writer的private identity，token本身move保持兩份有效。`committed_current`要求autocommit，使用獨立讀取交易重新確認完整快照、實際root／position與pending battle；SAVEPOINT release、另一個writer、staged tuple或來源過期均不能代替。

這個COMMIT只提交呈現快照，**沒有提交canonical item／slot mutation**。完整快照必須由真正取得全部50格與完整外觀afterstate的issuer供應；任意blob或通過格式檢查不會取得物品、規則或權威資格。

## 真正呼叫鏈路

`SqliteDatabase`新增lazy reader／writer accessor，兩者是同一物件，在實際Application game Context建立；普通initialize／migration／login不建schema。顯式fresh schema方法拒絕TEMP影子、要求foreign keys與自有交易，沒有IF NOT EXISTS、匯入、預設資料或自動遷移。本輪沒有呼叫任何SQL。

新的host opt-in預設false。Context附上同一reader／writer，Application驗證實際common sources；host Owner保留並比對新增兩個Context identity。`StoredSources::equipment_publication_factory`在啟動game owner建立後續提交用closure，擷取實際reader／writer、account／character借用來源及strong common host，不保留Context、不在啟動階段寫入。真正後續handler提交後，才將該writer的私有憑證交給closure，建立 `SharedTaiwanNativeEquipmentPublicationSource`；closure拒絕不同thread。

writer的每次load也拒絕TEMP中的accounts、recovered_characters、recovered_positions及battle相關同名物件，因為既有common reader仍使用未限定名稱。完整tuple／issuer邊界與committed_current都重新經過這個檢查，不能讓main witness搭配被TEMP遮蔽的common save。

Source的publish真正呼叫第229輪 `SharedActorVisibility::publish_taiwan_appearance`。每個Prepare／BeforePublish／AfterPublish／queue completion邊界重新讀完整已提交快照，前後確認同一ready lease、實際saved position及獨立actor handle；不能用lease固定入場位置冒充當前位置。快照因移動過期即拒絕，必須由真正issuer重新提供，不偷偷改位置。借用DB的生命週期必須覆蓋game owner drain；既有pending取消、私有Binding與weak IO facade仍沿用229實作。

完整1200B庫存只是來源觀察，不在此發送，也不假裝供出完整最新6F。新snapshot／DA歷史紀錄不代表全快取重建、socket寫完或客戶端驗收。native self-local DA、混合版本完整fanout及真Application全生命週期仍獨立OPEN。

## 進度與下一步

本輪新增5個C++來源檔、修改7個來源檔，新增1段部分來源串接，累計216；新增完整雙向遊戲路線0。台服C2S156、世界S2C252、戰鬥S2C110；完整狀態／變體分母與完成率仍未知。

接下來必須把真正共用owned instance／equipment mutation、完整before/after source revision、實際item→12B appearance、完整庫存回覆及native handler接上，canonical交易成功後才能取得相應呈現資料並發布。本輪快照憑證不能代替該canonical交易。完整2A producer、once-Issued admission、Main與13個世界玩法分支仍OPEN，保留CN／web／共用資料／64位數值／stack99／原生字體與凍結功能。

沒有建置、測試、native／VM／codec／遊戲執行、資料庫讀寫／SQL、遷移或部署。目標active，台服完整串接100%之前持續工作，再集中測試驗證。



## 第231輪：共用物品持有儲存與台服C28原生選取來源

# 第231輪：共用物品持有儲存與台服C28原生選取來源

本輪加入實際共用整件物品持有儲存、完整owner population CAS、永久實例／取得憑證去重，以及台服C28(flag1)對真正ready玩家與已持有原生alias的唯讀選取來源。這是CUSTOM-0092內部儲存政策及限定原生來源接點，沒有把舊CUSTOM／6bf／c5d8物品升格，也沒有完成裝備玩法、原生取得規則或item→DA。

## 原生定點與限制

同149c原件保留兩段432B／137個指令位置、12個opaque CALL，新增原生覆蓋0。3B尾段498EA4..498FC2、41尾段499268..4992FA可將完整24B快取row與sign-extended slot送到49B850；它仍是未進入的UI/helper邊界，不能宣稱內部沒有物品→外觀對應。3B依UI866A4的mode0／1跳過不同slot，slot34在mode1不走這個直接CALL；41有效slot尾仍可到4992F0。49FBD0／48E7A0也可存取receiver／global狀態。沒有進入STOP、GUI、render或formatter內部。

既有metadata114／116／118是icon、120是reach；既有DA12B來自完整incoming raw15／2A。這些事實都不能組成完整物品→12B after-appearance來源。C28的完整低WORD key、source低BYTE與flag1也不提供目的格、equip boolean、持有者或全域實例ID。

## 實際共用持有儲存

`OwnedInventorySnapshot`持有完整common character root、嚴格正值revision、來源SHA／record、完整排序的明示位置與全部原生aliases。空格是明示的`nullopt`，未列位置不是空位。位置kind／index是服務端內部名稱，沒有推定原生equipment slot、容量或目的格。

每個物品有獨立server-only正signed64 instance ID與共用definition key、quantity／stackability／revision及不可變取得來源。ID與definition不可由raw20、keyWORD、slot或selector生成。各client／profile alias保存全部原始bytes、native key／slot、來源及同一實例revision；raw20不作共同數量或唯一ID解碼。合格可堆疊量1..99沿用CUSTOM-0089，其餘整件量1；實際definition、stackability、slot資格仍由完整issuer供應，不冒稱原生規則。4096 cells／16 aliases／4096B record是內部資源界線，不是遊戲容量。

`SqliteOwnedInventoryRepository`用同一實際account／character connection與四張共用表。`owned_item_instances`是永久全域registry，instance ID和取得SHA／record各唯一；退役只移除位置，ID／receipt永不自動刪除。新ID只能INSERT，因此不能偷取別人實例、重放同一取得憑證或復活退役實例。跨owner交易與自動merge／split需另外實際多owner交易，目前沒有提供。原生aliases外鍵掛到唯一實際位置，移除位置／角色會連帶移除current aliases，永久registry仍保留。

writer自己持有BEGIN IMMEDIATE，拒借用交易與issuer reader／writer reentry；對完整before population及所有aliases作CAS，不只比revision。原本實例的definition、stackability、取得來源不可變，換位／數量／alias異動須提高instance revision。每個issuer邊界回傳完整next，必須完全相等；不得SQL寫入、交易操作、yield、pump或send。Prepared／BeforeWrite／BeforeCommit前後檢查完整實際root、pending battle、來源、autocommit與total_changes；BeforeCommit比staged next。所有儲存SQL限定main，且拒絕common及新table的TEMP遮蔽。

完整immutable private token在COMMIT前配置，只有成功outer COMMIT才返回，之後沒有issuer、重讀、重試或配置。`observe_committed`是對已存在持有資料的新獨立讀取交易觀察，不是新交易／取得憑證；它與`committed_current`均要求autocommit、完整資料與當前common root。loader自身也用一致讀scope，沒有將數個獨立SELECT當同一觀察。

## 台服C28選取與Application來源

`SharedTaiwanOwnedItemSelectionSource`使用真正Session／ready lease、InWorld、native world ready、common delivery generation、非entry delivery、當前saved position與battle generation。讀取已提交持有資料前後與最後再次檢查；回傳private完整owned Selection，包含原始request、完整持有snapshot、精確cell／instance／alias及連線weak identity。caught重入會poison外層觀察，不接受替身Session。

只有same149c、`tw149c-item20`、exact20B、同raw slot與完整item WORD、alias revision等於實例revision才可被選取。firstWORD只驗client key，沒有推導common ID、definition、quantity或目的格。Request由外部typed caller傳入；這個reader不證明實際封包收取、請求freshness或動作授權，真正C28 dispatcher仍需接入。`current`僅適用mutation前的完整before；真正staged after不能拿舊before比較。C28不會新增物品、猜裝備動作、送成功回覆或代替規則owner。

Database新增optional共用reader／writer；SqliteDatabase lazy accessor在真正game Context建立同一物件，ordinary initialize／migration不裝schema、不匯入或填資料。顯式fresh schema只有原始SOURCE，沒有執行SQL。Context附上同一reader／writer，Application及host Owner驗證／保留實際來源identity；`StoredSources::owned_item_selection`用同一common presence建立選取來源。host opt-in預設false，選取能力限定149c，Main仍未選取。

## 進度與缺口

新增5個C++來源、修改7個C++來源，新增1段部分串接，累計217段。台服C2S156、世界S2C252、戰鬥S2C110維持原方向／階段定義；新增完整雙向遊戲路線0，台服／全遊戲總分母與完成率仍未知。

真正取得／掉落／任務／definition mapping issuer、native C28玩法handler與Lua規則、共用物品變更和完整native presentation快照的**同一outer COMMIT**、完整庫存回覆與item→DA producer仍OPEN。第230輪快照COMMIT仍與這個canonical custody COMMIT分開，不能先後呼叫兩個writer就宣稱原子裝備交易。也未供應self-local DA、完整mixed fanout、完整2A、once-Issued admission或Main／全生命週期drain。

CUSTOM-0092只新增內部儲存政策，不授權CN自訂玩法；共用帳號／角色／道具與各版本alias分開保存。保留CN／web、帳號存檔／聊天／IME／認證／頭像／EXE／原生字體／繁簡轉換／等級、64位數值與stack99要求。本輪沒有建置、測試、native／VM／codec／遊戲執行、SQL／DB操作、遷移或部署。目標active，先續台服完整來源串接再集中測試。



## 第232輪：共用物品與台服原生外觀同筆交易及推播來源

# Round232: joint owned inventory/native equipment source transaction

This is PHASE1 source integration only. No build, test, native execution,
codec, game, database access, SQL execution, migration, restart or deployment
was performed. TW-first work continues; common CN/web support is preserved.

## Concrete source change

`SqliteOwnedEquipmentTransaction` uses the actual shared Application custody
and native equipment writers, on their identical SQLite connection and game
thread. It rejects unrelated account/character readers, borrowed transactions
and reentry. It owns one BEGIN IMMEDIATE and one outer COMMIT for both whole
populations. This is the atomic storage coordinator missing after230/231;
calling the two standalone public commit methods in sequence is not used.

The existing writers now share private validate/stage implementations with
the coordinator. Their public replace methods still own their transactions,
reject borrowed transactions and return only durable receipts. Private stages
never call an issuer, start/commit a transaction or return public staged tokens.
They retain the original whole owner CAS, permanent globally unique identity
and acquisition receipt registry, immutable item definition/stackability/origin,
strict revision transitions, complete versioned aliases and complete native
1215-byte witness. No canonical ID is derived from native raw20/key/slot.

The coordinator accepts optional complete expected snapshots for each store
and a complete next pair. Both next snapshots must have the identical full
common character root. Existing individual validity/transition checks remain
mandatory. Inside its transaction it compares both stored expected tuples,
the actual common root population, saved position and absence of a pending
battle. Its genuine issuer returns the entire exact next pair at Prepared,
BeforeWrite and BeforeCommit. The final phase occurs after BOTH populations
have been staged and compared. Detected issuer reentry, autocommit changes or
total-change differences poison the operation; no bool-only Current callback
supplies the state. The issuer is a trusted synchronous source with an explicit
no-SQL/no-transaction-operations contract. These observations do not prove an
arbitrary callback never rolled back and opened another transaction internally;
this API is not isolation for arbitrary same-connection SQL callbacks.

Both immutable individual snapshots and a private coordinator-identity receipt
are allocated before the only COMMIT. Failure or exception before that COMMIT
rolls back the whole pair. No provider, reload, retry or allocation occurs after
the durable COMMIT. Copies/moves preserve both valid owned receipts; callers
cannot manufacture a joint receipt from independent single-store receipts.

Joint committed_current owns one consistent read transaction for both full
tuples and current common root/position/battle state. It does not call two
separate public committed_current methods and combine potentially unrelated
observations. Coordinator and both underlying writer identities must match.

## Actual publication/source composition

The existing SharedTaiwanNativeEquipmentPublicationSource has a joint-receipt
construction path. Every source reread in the existing held DA publication
endpoint now checks the joint current pair when that path is selected, plus
its existing actual ready presence lease, actor handle, saved position and
common/visibility ownership checks. It retains the coordinator and complete
receipt strongly. The older delivery-witness-only path remains explicitly
delivery-witness-only, with its original behavior.

StoredSources::owned_equipment_transaction builds this coordinator from the
actual same Application Context's two readers/writers, after identity checks.
StoredSources::owned_equipment_publication_factory retains that exact
coordinator, actual common world and borrowed account/character readers, never
the Context. It accepts a future joint post-COMMIT receipt on the game owner.
Construction performs no reads/writes or schema operations; both existing
explicit storage flags must be supplied. Ordinary Main remains opted out.

## Native provenance and remaining gaps

Native baseline remains149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763.
The complete equipment witness is50 actual24-byte cache rows (including the
unknown prefix1..3 of every row) followed by an actual full DA15. It is not a
packet and is not inferred from additive3B/41 or a raw20 item instance.

Retained231 native work:432 bytes/137 instruction sites, two bounded spans,
12 opaque CALL boundaries. A full24-byte row may reach49B850 under actual
mode gates. Mode0 skips38..41; mode1 skips30..37/42..45/46..49, so slot34 in
mode1 skips that direct CALL. Receiver helpers remain opaque. This is no proof
that an item-to-DA mapping is globally absent. No new native bytes/opcode or
complete route are claimed by this transaction work.

Still OPEN: genuine acquisition/drop/quest entitlement and common definition
source; actual authenticated C28 dispatcher/input freshness/action and equip/
unequip/slot/Lua rules; exact native item-to-fullcache/DA producer; complete
ordered inventory replies; source/self-local DA and mixed-version fanout;
full2A/once-issued admission/lifecycle/Main suppliers and full TW route
denominator. The readonly231 typed Request is not proof of a fresh network
action. The issuer contract remains a mandatory genuine supplier; its API is
not a fabricated implementation of those gameplay rules.

Atomic storage makes this particular source chain more complete. It does not
make the full equipment route, whole opcode or game complete. Joint snapshot
revision and provenance do not invent an extended wire profile. Stack99 applies
only to qualified stackable common instances; native additive signed30 gates,
bag30 slots, unstackable/PET semantics and numeric expansion remain separately
tracked. Preserve saves/chat/IME/auth/portraits/EXEs/native fonts/conversion/
levels and all STOP/render/refresh helper boundaries.

CUSTOM-0092 remains the label for shared server identity/custody storage policy.
This coordinator adds transaction mechanics to that policy; it introduces no
gameplay rule, item definition, mint entitlement, native mapping or CN custom
game permission. Historical custom registry entries are unchanged.

## Accounting

New C++ files2; modified existing C++ files8. Added one partial source segment;
cumulative218. New complete bidirectional routes0. TW/global completion and
full directional/state/variant denominators remain null. Existing packet index
counts are unchanged. Static source review/accounting is not runtime acceptance.
Full exact before/current sources, diffs, agent deliveries and metadata are
retained outside DesktopGod2 under the232 task archive; old231 seals stay intact.



## 第233輪：台服實際 C28 請求接入共用物品選取來源

# 第233輪：台服實際 C28 請求接入共用物品選取來源

本輪新增實際 Session 原始批次→私有 C28 occurrence→混合分派→完整共用物品選取→必要實際 Action 的來源接點。新增一段部分來源鏈；完整雙向玩法新增0，台服全遊戲分母及完成百分比仍未知。沒有建置、測試、執行客戶端、封包 codec、資料庫、SQL、遷移或部署。

Session 僅在實際已認證、已接受世界尾段、持有共用 ready 身分的 game callback 中，於任何玩法 callback 前保存完整批次內每個 C28 的原始 Request 位址與 owned logical5。一次 take 只接受該原始位址；複製 Request 不能取用。私有 receipt 的所有複本共享同一次 take／dispatch 狀態，必要 Action 前先 claim；重複 claim 將當前 window 失效。RAII 在同步 handler 返回或異常退出時退休整個 window。綁定實際 Session、帳號、角色、ready 身分物件、批次序號、原始 record index、phase 與 battle generation；序號不溢位重用。

這是服務端內部一次 occurrence 的來源連結。它不是原生 wire nonce、二進位來源證明、客戶端 ACK、玩法權限或語意重送防護。相同5 bytes在另一批次仍是新 occurrence；真正裝備／使用重送必須依完整物品狀態、規則與整筆 CAS 處理。receipt API 與 game-owned 欄位相同，只能在序列 game callback 使用，不宣稱能隔離任意跨執行緒或惡意 C++ provider。

WorldRecordSource 僅在安裝完整 SelectionBinding 時，把原始 C28 分成逐筆 singleton run；移動及其餘最大連續段仍依原順序處理。C28 在聊天 composer 複製 Others records 前直接從原 span 取 receipt，失敗不能 fallback 到另一套 Others。Application 由實際 Binding 傳遞明確 opt-in；預設 false 保留既有分派及凍結功能。累積原生加密回包保持 run 順序及原有 frame／byte budget；必要 Current 仍觀察完整原始批次和實際前進 prefix。

OwnedItemRequestSource 強持有實際同一 presence 的 OwnedItemSelectionSource；後者用231共用 custody 儲存與完整版本化 alias，以 key／source slot 找完整 instance，不從 raw20 推 common ID。必須 supplied 完整 handle／release／invalidate，沒有猜測裝卸動作、空成功或預設回覆。Action 前核對完整舊 Selection.current；Action 後只核對 receipt、實際 ready lease、位置及 battle generation，不把已合法提交的新 inventory 和舊 Selection 比較而誤拒。Action 自己必須採232整筆 custody＋native snapshot 交易與真實規則／next issuer／durable receipt，並供應完整有序原生回覆或有依據的明確 no_reply。

重入／拒絕／異常傳遞實際 Action invalidation；真實 release 即使另一子清理異常仍執行。借用 Context 不被保留。HostPlan 的 with_owned_item_requests 只在實際同一 Application Context 建來源，拒絕重複安裝；不選 Main、不讀寫啟動資料庫、不授予任何物品。現有 chat、spectator、CN、web、數值及存檔來源保留。

presence 的 ready lease／saved position 讀取經實際 repository observers，故其前後均核對完整本地 receipt／Session phase／身分／battle generation 與 reentry fence；observer 捕捉已拒絕的重入後回傳有效資料，也不能讓 Action 繼續。混合來源 invalidation 有遞迴防護，每個子 callback 的複製也在各自異常處理內，避免一次配置失敗略過其餘清理。

相同 fence 也接入外層 WorldRecordSource 的 ready／stored／snapshot：repository observer 後重讀本地 phase／battle／ready 身分、精確 slot 物件與 live 狀態，防止 BeforeRun 的 observer 已 terminalize 外層後仍進入下一個 C28 Action。既有 Current 的純觀察與 game-only 合同不變，不宣稱隔離任意 provider 自行改寫同一資料庫。

原生依據維持149c SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`。共享 producer VA496550 的第三參數低 BYTE 經4965D0／4965E9進 wire，並非 producer hardcode1。現有 logical5 decoder 僅支援已觀察 caller 的 flag1 subset，行為不改；flag1也有卸裝，不能當 equip boolean、數量或目的格。舊6bf EGG／SPP／WPN／EQU／TWP／TEQ執行探針保留為歷史，不能當149c驗收；本輪只修正 header 的來源說明。

仍未接通：真實 definition／取得物品權威、C28 action／目的裝備格／Lua裝卸條件與結算、full item→native1200/cache／DA15 producer、完整背包／裝備回覆、來源自己本地更新／混版 fanout、實際正式 Main suppliers。完整2A、once-issued admission、其餘台服 gameplay 與全路徑分母仍須持續追查。Conditional Action 插槽、私有 receipt、解析器、拒絕分支及資料庫技術交易均不計完整遊戲路徑。



## 第234輪：台服完整物品欄位及交易回覆元件來源

# 第234輪：台服物品原生欄位與交易回覆來源

本輪將同一149c台服的完整3B物品資料編碼、既有41數量更新，接到實際共用物品／原生裝備聯合交易的回覆元件來源。新增3個C++檔、修改6個C++檔；增加1項局部來源串接，新增完整玩法路線0。台服／全遊戲完成百分比與完整路線分母仍未知。

同版原生呼叫證實 C28 傳來源格、物品鍵與旗標，目的格只參與本地條件；反向卸裝也走旗標1。來源不能由旗標猜裝備目的地或玩法權限。這輪保存6段有界指令切片776 bytes／222處指令，沒有宣稱它們是全歷史未曾涵蓋的新位元組；另保留3B／41兩段780 bytes／236處指令的完整既有同版證據。

`RecoveredTaiwanInventoryItemRecord` 必須明確供應 incoming raw count、0..49格、opaque WORD 與完整20 bytes，25-byte邏輯記錄逐欄保留，無預設opaque0。3B替換完整20 bytes，但數量依metadata分支相加或設1，不能當絕對數量；41的 signed BYTE 才決定絕對數量或清除count/key，其餘18 bytes與未知prefix不因此清空。原生伺服器順序、opaque helper副作用與完整1200-byte afterstate尚未恢復。

`SharedTaiwanOwnedInventoryReplySource` 由同一 Application Context 的實際owned reader與joint transaction組裝，準備時以同一讀取範圍核對完整共用／原生before，並核對私有實際C28 occurrence及選中full20 alias。供應者必須明確傳入已排序操作及限額；每筆3B都是該格真實before／next instance，拒絕重複3B；每筆正值41都須符合真實before／next count/key，所有修改格均須涵蓋並以絕對41收尾，未知prefix不得虛構。這是有界來源投影政策，不是恢復原服回覆順序。

封包在未來實際COMMIT之前配置／編碼。取出時只接受同一joint writer的私有提交憑據，重讀完整已提交雙資料群與當前Session、私有input、ready lease／位置；取出一次後不能重送或重建。提交後仍有實際current讀取，可能配置或拋例外，並非聲稱整個取出流程零配置。故意將Component與完整World Reply區分，不能冒稱能力重算、pending完成或DA外觀發布已接通。

凍結既有背包projection與其他功能。尚待真正的definition/acquisition、裝卸合法性與目的格選擇、Lua規則、完整next issuer、能力變化、物品到DA映射、完整有序回覆與Main供應者。保留CN／網頁／共用資料、64位元數值目標、99堆疊目標、原生字體與繁簡轉換。

本輪只做靜態原生來源追查、C++來源串接和檔案帳本；未建置、未執行遊戲／native／codec、未測試、未連資料庫／執行SQL、未遷移或部署。目標維持active，遵照台服完整串接100%後才停止的最新指示。



## 第235輪：台服選中物品接入完整原生定義觀察

# 第235輪：台服選中物品接入完整原生定義觀察

本輪新增1個C++來源檔、修改9個C++來源檔，將實際owned物品的原生別名鍵，接到同一共用SQLite連線的完整武器／防具定義，再交給既有必要Action。新增1段局部資料串接，完整雙向玩法路線新增0；完整台服分母與完成百分比仍未知。沒有建置、測試、native／codec／遊戲／DB／SQL執行、遷移或部署。

同149c parser已證：source14..21的最低bit分別生成metadata11A各bit，source22..25生成11B低四bit，高四bit保留原值。2不是true，3最低bit才是1；不能用「非0」代替。11A bit04是本地C28發送條件，11B bit01是3B數量相加條件，均不是服務端裝備權利或共用99堆疊規則。實際鍵由token0建立lookup，metadataDWORD0取自token5，不是物品ID；重複鍵的原生後寫覆蓋與family第一匹配分開記錄。本輪5個有界切片383 bytes／126處指令，另保留parser1344 bytes／393處指令；不宣稱全歷史新增覆蓋。

`NativeItemDefinitionObservation` 保存完整396 bytes、原CP950定義行、family、獨立native key、來源位置與完整catalog指紋。其資格明確是mapped149c parser對歷史70a4 encoded／75c3 decoded來源的定義觀察，外層6bf／c5d8客戶端驗收保持歷史。當前encoded素材ef297不同，這輪保存原件但未解碼，也未冒稱重新取得當前decoded75c3或遺失的兩份records cache。preROM group/action不能當最後外觀、戰鬥屬性或裝卸權限。

新的`observe_native_definition`直接使用共用custody repository的私有實際連線，擁有單一讀取交易；拒絕借用交易、寫入／issuer期間重入、TEMP同名影子，以及正式main缺表時借ATTACH來源。兩個完整catalog分別通過既有全指紋後才選唯一key；任一缺席、沒有匹配或雙匹配均不猜family、不補定義。既有catalog公開讀法與存檔保持不變，僅讓同一repository讀完整已資格資料。

顯式`create_with_definitions`將這個owned完整值附到私有Selection；變更之前Current重讀定義和完整custody，前後核對實際ready lease／Session。`instance.definition_key`仍是獨立共用ID，沒有宣稱它等於native key，也沒有把acquisition receipt或alias source誤作定義來源。Host的`with_owned_item_definition_requests`接到真正同Context C28→Selection→必要Action；回覆factory也須顯式選相同definitions模式。原有無定義模式保持可用，Main未自行啟用。

本輪另修正晚發現的第234輪來源物件複製缺口：`SharedTaiwanOwnedInventoryReplySource`現在禁止copy／move，避免複製一次性consumed狀態；共享同一Source仍維持一次取用。完整Component bytes仍是可複製的資料，不冒稱不能複製封包。第234輪原件與封存未重寫，其當輪有界審閱結論不當成永久無缺陷的保證。Selection reader亦禁止copy／move並在實際presence observer之後重核Session本地狀態。

真正common definition對應、目前資源全bank資格、物品取得、裝卸條件／目的格、Lua規則、完整next issuer、能力結算、pending完成、item→DA與完整有序回覆仍待串接。維持TW優先100%停止條件，保留CN／網頁、共用表、64位數值、仙幣99999999999、99堆疊、原生字體／繁簡轉換及凍結功能。



## 第236輪：物品操作接入神仙裝備完整狀態來源

# 第236輪：物品操作接入神仙裝備完整狀態來源

新增2個C++來源檔、修改6個C++來源檔，直接將同庫持有者的完整D1/D2觀察附到實際C28選中物品。這是1段部分來源串接，完整雙向玩法新增0；台服全遊戲分母與百分比未知。沒有建置、測試、native/codec/runtime/DB/SQL執行或部署。

同149c的40127C長度leaf回21；兩個實際dispatcher的D1 caller先跨過opcode，再將20 bytes交49F510寫到UI866A8。D2的49F540寫到866BC，沒有覆蓋866BA。49B5E0的guard讀D1 body18（logical19）低兩個bits，不讀普通角色sex或目的格。狀態2拒7101..7200/7401..7500，狀態1拒7201..7300/7501..7600；7000以下、8000以上及其餘情形由此client predicate返回允許。這只是客戶端發送條件，不能當服務端裝備權利。

`RecoveredTaiwanDeityEquipmentState`保留D1/D2各完整21 bytes；42-byte Pair是明確儲存容器，不是恢復的封包或回覆排序。原生切片新增擷取7段199 bytes/60指令，另保留715 bytes/208指令及3段18-byte資料表；不宣稱全歷史新覆蓋。既有30/31/34神仙列、選取列、角色性別及1200+DA15裝備cache均不能生成缺失D1/D2。

復用既有version-keyed `main.character_native_world_entries`通用raw witness儲存，不另建表、不修改schema、不把它的名稱解釋成世界入場權限。新kind為`tw149c-deity-d1d2-ownerlocal-v1`，必須由真正來源供應全部42 bytes及獨立provenance/revision。原有CAS寫法仍須真issuer；它不自動證明中途裝卸、battle條件或原服公式。本輪沒有生成或匯入任何D1/D2資料。

`observe_native_deity_equipment`直接使用共用custody repository的私有實際連線，自有READ scope核對完整raw、來源、版本、owner/common root/position與未結battle；拒絕借用交易、寫入期間重入、六個相關common/witness表的TEMP大小寫影子或缺main表借ATTACH。缺資料或舊root/position返回缺失，壞形狀報錯，不猜補未知bytes。私有建構`NativeDeityEquipmentObservation`保存完整觀察。

新的顯式definitions+deity模式把資料交給既有實際C28 Action；Current重讀完整觀察與custody，回覆factory須選同模式。各來源觀察使用各自讀取範圍，沒有聲稱custody/definition/D1跨讀取構成同一原子交易。真正Action的next issuer仍須在實際寫入交易核對所有必要來源。舊普通／definition模式維持原樣，沒有自行選Main或將client guard當授權。

尚未完成：當前D1/D2原件的真正產生／持久化issuer、選中神仙列lineage與狀態變更、裝卸合法性／目的格／Lua規則、完整next issuer、能力結算、item→DA、pending與有序完整回覆、Main及其餘台服路線。保留CN/網頁、共用表、64位數值、仙幣99999999999、堆疊99、原生字體／繁簡轉換、帳號存檔與凍結功能。



## 第237輪：台服背包請求接完整持有物品交易與回覆

台服第237輪集中接 C24 背包移位／交換。新增具體處理器，原始 mixed records 中的 C24 分成 singleton，先於聊天 Others 複製段派送。實際服務自行讀取完整持有物品與 native1215 狀態、決定完整下一態、預製兩筆41、同庫全量 CAS 交易，再於 durable receipt 與目前 Session／lease／位置一致時回傳。沒有要求外部再提供 Action／next-state issuer 的空處理器。

原生依據為既存149c C24 producer 與41 consumer。41 只改數量和 key；兩格原有尾18 bytes 必須相同，其他 prefix1..3、所有剩餘格、DA15 完整保留。這個限定讓原生41能完整表達本次 cache 欄位結果；不猜3B未知 WORD、不用C28 receipt冒充C24、不宣稱UI helper或原生驗收已完成。

CUSTOM-0093 明示服務端全物件移位／交換政策：只用兩個已明確存在的共同 bag 位置0..29，來源非空、兩格不同；整個 instance 連同 ID、definition、acquisition、raw20 與數量搬移，不合併、不拆堆、不新增物品。更動的 instance 只允許單一149c item20 alias，避免猜改其他版本位置；其 revision 與 alias slot 同步更新，完整 inventory/equipment revision 同交易遞增。全50格目前 alias 與 native witness 逐格一致才處理。保留其他版本資料與既有 CUSTOM-0037 限定，不把此政策說成原版服務端規則。

透過實際 Application Context 的 with_owned_bag_moves 安裝新處理器，要求真正共同帳號／角色／presence 及兩個既有 writer。Main、資料表安裝、初始真正 acquisition／完整 native witness supplier 尚未啟用，缺資料直接拒絕，不把舊 diagnostic 格轉成新持有權。

來源 provenance 保留完整原文並只首次附加固定 CUSTOM-0093 尾標記；後續移位不繼續增長紀錄字串。每次狀態改變仍透過完整 CAS 及 header／instance／native revision 前進，不截斷 provenance、不把來源SHA誤稱下一態雜湊。初版逐次追加操作的候選完整保留為歷史，最終候選修正此限制。

本輪新增2個、修改7個C++來源檔，增加1段條件式來源串接。聊天適配組裝保留新C24 binding，安裝順序不會使它遺失，既有聊天行為不變。TW觀測C2S156、世界S2C252（230固定／22可變）不變；新增整個opcode全變體完成數0。完整遊戲分母仍未建立，台服整體百分比未知，不能把此子集或來源段數換算成100%。待補一般 metadata 不同格移位的完整3B來源、其他C24目的區／同格與空格行為、裝卸完整規則與回覆，以及正式 caller 與其他台服玩法。

按使用者先串接要求，本輪未建置、測試、啟動原生或服務端、執行codec、DB／SQL、遷移或部署。目標API現讀仍為blocked，保留真實狀態與原目標，使用者已授權的本輪手動工作持續。



## 第238輪：台服背包接完整3B持有物品材料

第238輪繼續台服背包 C24 實際處理：新增明確 opt-in 的完整3B物品材料模式，直接從既有同庫完整 owned aliases 讀取，不增加外部 Action／issuer callback 占位。新增 TaiwanOwnedBagItemMaterial 比對同一物件兩個精確 profile、完整20／25 bytes、key、slot、revision 與相同來源宣告；缺少真25-byte材料就拒絕，不從1215 cache或舊helper的0,0猜未知WORD。

CUSTOM-0094 明示保留每件真full25內原有incoming count與opaque WORD，只投影已知slot欄位。這是自訂的材料保留政策，並非已恢復原版服務端搬移規則或原生helper相容性。內建 whole-instance plan 同步兩個alias及物件revision、完整共同庫／native witness的CAS；預編碼先清兩格數量、逐件發其完整3B、最後以兩筆41設定真正數量／key。所有20-byte物品資料保留，prefix1..3、其他格與DA15不變。incoming count不當作canonical quantity；原生3B中途clamp與helper副作用仍待全串接後驗收。

既有 CUSTOM-0093 create／with_owned_bag_moves 預設仍只用單alias及兩格tail18相同的41子集。新增 create_with_item_material／with_owned_bag_move_material 才選0094；沒有缺料回落舊模式。新增profile為tw149c-item3b25-material，仍用同一通用持有物品alias表，不拆台陸玩法表，不匯入或執行資料庫。變更slot後材料須稱derived來源；sourceSHA是原始宣告，不是改後raw的雜湊。來源標記只首次附加，不累積操作字串。

同版3B完整receiver保留498 bytes／151個指令位置；另純lookup30 bytes／8位置，合計528 bytes／159位置，新增全域原生覆蓋0。logical3..4未被本函式直接讀取，但完整payload指標EBX跨opaque CALL，因此不能宣稱全域unused／padding或任意補零。沒有找到真正原服務端producer；新模式仍要求真正full25來源與未來完整原生相容性資格。

本輪新增1個、修改4個C++來源檔，增加1段條件式來源能力，整個C24完成數仍0。真正acquisition／full25材料發行者、Main、移動到1215 witness同步、一般完整裝卸與所有台服路線仍待接齊。TW觀測C2S156／世界S2C252（230固定、22可變）不變；完整路線分母與台服整體百分比未知。

本輪未建置、測試、原生或服務端執行、codec、DB／SQL、遷移或部署；未變更陸服、網頁、凍結功能、原生字體與文字轉換。既有0093註冊與第237輪封存完整保留，0094另行註冊；不得把這個有明示缺口的模式計成100%。



## 第239輪：台服移動同步完整持有物品見證

第239輪只推進台服一般移動2E→同庫位置與背包見證→原5D／周邊5E來源。新增 CUSTOM-0095 保存政策：從目前精確共同持有物品與完整1215-byte原始見證出發，在一次實際 SQLite outer transaction 內一起更新共同位置及見證位置／revision；所有物品ID、數量、取得來源、aliases、inventory revision與1215／DA15 bytes原樣保存。這是明示的自訂保存規則，不是重新取得原生afterstate，不能用來修補已過期／缺失的材料。

具體程式已接 actual Sources／StoredSources Context factory→NativeMovementHost→MovementSource→強持有 controller→SqliteOwnedEquipmentTransaction。強制相同 Application readers／writers／character repository、Session／lease／actor／root／完整old position，缺一拒絕且不回退。原本 native scene／Lua幾何／權威／完整5D與peer材料仍全部必要；沒有新增任意成功／空Action或猜回包。

交易在 Prepared／BeforeWrite 調用現有實際場景與peer Current；寫入位置後只用封閉的完整來源讀取核對，避免用仍處於舊位置的scene Current誤判。actual main位置CAS→完整inventory/native-old核對→native witness stage→完整next核對；一次COMMIT前配置同庫durable receipts。提交後核對當前receipt／Session／lease／位置，再沿用真scene publish和peer deliver。完整物品存檔不重寫，既有default-null／borrowed路徑不選此政策。

本輪修改10個C++來源檔，新增1個條件式來源串接增量；新增完整雙向路徑0，TW／全遊戲百分比仍未知。可見候選仍為TW C2S156、world S2C252有效值（230固定＋22變長）、battle110索引（9特別分派）；這些不能當完整玩法分母。仍缺真正持有物品／完整材料發行、正式Main來源接入、其餘玩法及phase/state/variant完整分母。沒有建置、測試、執行原生／codec／SQL、存取資料庫、遷移或部署。



## 第240輪：台服共用持有物品儲存正式入口

本輪修改3個C++來源檔：Main新增明確 --owned-equipment-schema --migrate-only 選項，直接接同庫單一交易的四個owned物品表與一個native裝備見證表。參數先於Config／DB初始化檢查，禁止任意--run-for含0，與舊delivery schema選項互斥。新五表DDL共用一筆交易；先前既有migrate仍獨立。只fresh-install，既有完整／部分feature表拒絕，不repair、升級、匯入、填充或建立物品權利；普通Main遊戲啟動不變。

同版原bytes證明C57／C6A新菜單入口衝突不是版本不同。54保存actorWORD並由58答覆的字段已定點追到，卻沒有官方handler證明應向誰發preview；不交換舊CUSTOM0062語義或擴猜邀請，歷史自有服務驗收保留。

儲存前置來源增量1項，新增完整雙向玩法0；既有混合版本局部來源段225不增加。台服觀測C2S156／world S2C252有效值與battle110索引不變，完整分母與整體百分比未知。真acquisition／full1215／full25 issuer、正式完整Main及其餘TW玩法仍OPEN。本輪未建置、測試、native／codec／runtime／遊戲DBSQL、遷移或部署。目標API仍blocked，保留授權的手動續作，不pause／complete／另建替代目標。

詳見 docs/research/tw-native-storage-and-social-source-20261010.md 與外部 tw-social-command-source-240 封存。


## 第241輪：台服C35原始技能指令到共用權威處理入口

新增完整17-byte獨立WireRecord與same149c定義資格grammar；ordinary／群體、scope13/14/16保留重複與順序、scope17單包self+friendly及normal formation整數WORD分開。scope5原生3FFF包含空位置，不能裁成livingmask。實際catalog使用同Application Context，client MP threshold不當server cost。

完整可選binding→mixed dispatcher→host plan→Application→Session已接，跨frame83/3用既有有界筆數／timeout且新入口釘住battle_generation，避免舊前綴跨離開再進入戰鬥；遊戲端逐完整command攔截，保留原始順序與release/invalidation。原CUSTOM PK／診斷／凍結預設不改。來源元件必須由真WorldOwner執行一次結算與完整非空native wire，缺權威不成功。

本輪修改9個、新增3個C++檔，新增1段條件式來源能力。真正WorldOwner實作者、learned/grant/cost/完整settlement與S2C supplier、正式Main及其餘台服仍OPEN；新增完整雙向玩法0。既有混合TW/CN來源段225→226不是台服完成條數。TW候選C2S156／world S2C252（230固定、22變長）／battle110索引不變；完整分母與整體百分比未知，不能聲稱100%。

未build/test/runtime/native/codec/遊戲DBSQL/migrate/deploy。目標API現讀blocked，保持已授權手動續作，不宣稱已恢復自動目標或另建替代目標。詳見docs/research/tw-native-skill-command-source-20261010.md與外部tw-native-skill-command-component-source-241封存。


## 第242輪：台服完整已選仙靈持有技能資料來源

新增SqliteCompanionRepository完整selected readset/current，保留仙靈19/29/all34、選擇與仙靈revision及provenance；實際Application同Database reader進Context，具體OwnedDeitySkillSource連完整same149c技能定義與Session/common ready lease/position/phase/battle generation。舊bool與其他load/write、既有CUSTOM與凍結路徑不改。此為觀察資格；獨立S87、86/5 actor、grant、真正MP扣費、once settlement/fullreply及Main仍缺，不把已學技能冒充戰鬥授權。

修改6個、新增2個C++檔，混合部分來源段226→227；新增完整雙向玩法0/opcode0。TW C2S156/world S2C252/battle索引110不變，完整分母與百分比未知。未build/test/runtime/native/codec/遊戲DBSQL/migrate/deploy。目標本輪root實際現讀active，舊241blocked保持歷史，不停止台服優先目標。詳見docs/research/tw-native-owned-deity-skill-source-20261010.md及外部tw-native-skill-authority-source-242。


## 第243輪：台服真主技能列表資格接C35

新增具體PrimarySkillList與game IssuedSkillSource，完整100 raw/aux、獨立nullable aux定義、DWORD control、S87只bit15更新/append及尾段ownordinal mirror、S38全tailclear/firstothersamekey已接；源於same149c原件而非將learned list全enabled。bounded真Session/common lease/position/battle generation/private ticket current進Source241 action前；strictprimary只side0，action後不驗舊consumed state。Host同Context factory及release/invalidation已接。實際一般nativepublisher/actor綁定/grant/MPcost/once settlement/fullreply/WorldOwner/Main仍缺，不宣稱發送或完成路線。

4改3新C++，混合部分來源227→228，新完整雙向玩法0/opcode0。TW C2S156/world S2C252/battle索引110不變，完整分母/%未知。未build/test/runtime/native/codec/遊戲DBSQL/migrate/deploy。goal API現讀active；current execution plan舊blocked依真receipt更新，舊ledger/241blocked完整歷史保持。詳見docs/research/tw-native-issued-skill-source-20261010.md及外部tw-native-skill-selection-source-243。


## 第244輪：台服86/5控制actor接C35來源對照

只推進TW：完整保留direct86/5的17-byte原件，按flagsbit0/1各自置A/B=1與低/高actor nibble，未置位維持完整舊DWORD/actor。Snapshot保留真primary/secondaryactor，PRIMARY Lookup帶同snapshot BYTE+51/side0。registry exact-ticket/fullcatalog/Session replacement已接，C35 raw及WorldOwner qualification皆比同issued actor/side。actor不是selecteddeity key或world localactor；last raw不是完整歷史/grant，沒有把本地cleanup當ACK。native完整UI/rearm/time/其他selectors仍由actual owner供應。

5改0新C++，混合部分來源228→229，完整雙向玩法新增0/opcode0。實際一般nativepublisher/held battle queue與write/pending/cancel生命週期、actor→deity所有權、grant/MP/rules/once/fullreply/WorldOwner/Main仍OPEN。現有common world sender不能直接發布InBattle清單；具體next已封存。TW C2S156/world S2C252/battle索引110不變，完整台服分母與百分比未知。未build/test/compiler/runtime/native/codec/遊戲DBSQL/migrate/deploy；goal保持active，繼續台服優先。詳見docs/research/tw-native-control-actor-source-20261010.md及外部tw-native-skill-publication-source-244。


## 第245輪：台服技能registry接真戰鬥held/write生命週期

4改0新C++：具體registry已呼叫獨立Session common InBattle sender，exact common identity/phase/battle generation、保留Write buffer、game-before/fullcatalog資格化、actualsocket success witness、game-post before/next Current及精確pending CAS串接。source/net雙pending屏障與onceclose/fail取消、弱來源只ongame lock/destroy、reservedlocalrevision不回退、失敗只retire舊exactslot不rollback presumedclientstate。純Publication觀察取代任意Completion，transportmarker退役且ticket真Current才交nextticket。新發布前已buffer的外框/83會failclosed；發布中inflight/unreceivedbytes屬哪個grant仍未知，不能以此冒稱完整replay權威。direct86/5非完整consumer/grant。

混合部分來源229→230，完整雙向玩法新增0/opcode0。實際一般nativeissuer/actor→deity/turngrant/MP/rules/once/fullreply/WorldOwner/ordinaryMain仍OPEN；只發布能力，不是完整技能玩法。TW C2S156/world S2C252/battle索引110不變，完整台服分母與百分比未知。未build/test/compiler/runtime/native/codec/遊戲DBSQL/migrate/deploy；goal保持active，繼續台服優先。詳見docs/research/tw-native-skill-write-lifecycle-source-20261010.md及外部tw-native-skill-write-lifecycle-source-245。


## 第246輪：台服獨立secondary技能清單接S87寫出及C35資格

6改0新C++：新增actual optional3×10 secondary完整nullable定義/rawWORD/aux/rawtails/selector模型；S87bit14按原first nonnull match僅改bit15及同ordinalaux，無match boundedappend完整WORD，S38只改primary。registry重讀全present secondary catalog（含inactive），直接沿245 held/write與before/next pending CAS。C35真controlA0/B非0選secondary BYTE52/side1，仍與actual WorldOwner qualification吻合；不能由C2S flag選list。原51B900 signed pointer gate→51B760 rawWORD bit15 compound已恢復，secondary key→ordinal仍是明示bounded owned firstkey投影，非原生keysearch/UIordinal/回合權限。resetprefix不當完整init，沒有由saved34造初始清單。

混合部分來源230→231，新增完整雙向玩法0/opcode0。TW C2S156/world S2C252/battle索引110不變，完整台服分母／百分比未知。普通native initialissuer／battle actor→saveddeity／grant／MP／rules／once／fullreply／WorldOwner／Main仍OPEN；沿真正battle-entry roster和selector/reset pure-data來源接續。未build/test/compiler/runtime/native/codec/遊戲DBSQL/migrate/deploy；goal active，台服優先，保留common/CN/web及凍結數值功能。詳見docs/research/tw-native-secondary-skill-source-20261010.md及外部tw-native-skill-issuer-source-246。


## 第247輪：台服主技能初始化資料前綴與兩類enable-clear

3改0新C++：將same149c51BB80..51BC2A的16主銀行REP清0、page_count1/raw_page_index0及真linked row材料接入既有private Ticket installation；row+5C/+60獨立aux必須由真same-roster owner提供，不借S34已學清單。51C4B0主clear清所有16×100 enableWORD/aux/state，51C4F0次clear僅清3×10 WORD且保留aux，沿真previous Ticket/pending/catalog/ready replacement CAS。沒有從C35推測local clear、創造ACK或grant。先前246將11C4F0建議作初始化的歷史檔保留，本輪明確訂正為secondary enable-clear。

混合部分來源231→232，新增完整雙向玩法0/opcode0。TW C2S156/world S2C252/battle索引110不變，完整台服分母／百分比未知。S88僅vitals、S1C才有construction identity，但變體不提供通用saved deity身分。普通admission／完整initial issuer／真row aux producer／actor→saveddeity／grant／MP／once／fullreply／WorldOwner／Main仍OPEN。未build/test/compiler/runtime/native/codec/遊戲DBSQL/migrate/deploy；goal active，持續台服優先。詳見docs/research/tw-native-skill-initial-source-20261010.md及外部tw-native-skill-initial-source-247。


## 第248輪：台服真正roster輔助技能producer串入初始化

3改0新C++：恢復same149c4A9750完整純資料helper，按真learned flags&2原順序重建獨立aux count/pointers，NULL/duplicates/全部inactive tail保留。實際S34 append flag0及S35 first physical pointer match flag3均same-row呼叫，沒有把S34當battle main或把S35當grant。新full100 owned roster材料經helper→16 linked aux→247primary初始化→同private Ticket install；全roster snapshot/equality保留完整尾資料，registry重讀全部present learned/aux定義含inactive，沿既有ready/pending/exact Ticket資格。100是owned安全幾何，非nativehelperguard；穩定owned input不冒native count單次讀。

混合部分來源232→233，新增完整玩法0/opcode0。TW C2S156/world S2C252/battle索引110不變，完整台服分母/百分比未知。找到真世界companions restore→Application send producer，但saved roster revisions/provenance/write lineage與ordinary battle admission/actor→deity/initial issuer/grant/MP/once/fullreply/WorldOwner/Main仍OPEN。未build/test/compiler/runtime/native/codec/遊戲DBSQL/migrate/deploy；goal active，繼續TW優先。詳見docs/research/tw-native-roster-aux-source-20261010.md及外部tw-native-roster-aux-source-248。


## 第249輪：完整已存神祇資料接實際世界登入發送

5改0新C++：同repository私有完整readset保存全部raw30/31/34、順序、revision/provenance、optional selection與同次模板keys，own READ/main資格/重入觀察，全部Statement先析構再COMMIT；full current不作future write CAS。私有Restoration綁exact batches，共用原builder與次序，不冒pet原子修訂。實際Application fresh-world呼叫已接新來源，game map保留exact weak Session/owner/phase/battle generation/material，發送前local→full current→local、逐批原void sender返回計數，disconnect最先精確清除；不是queue/write/ACK/actor/grant。same149c6段550B/174位置區分S30 body17有限learned_count reset與inactive staging／normal append tails、真正42B全roster reset與獨立S31 scalar prefix；caller/root/reset event尚未接入。

混合部分來源233→234，新增完整玩法0/opcode0。TW C2S156/world S2C252/battle索引110不變，台服完整分母/百分比未知。下一個實際缺口world reset/roster event與saved source、真正write資格、ordinary battle admission/actor/initial issuer；grant/MP/once/fullreply/WorldOwner/Main與其餘TW流程仍OPEN。未build/test/compiler/runtime/native/codec/遊戲DBSQL/migrate/deploy；goal active，繼續TW優先。詳見docs/research/tw-native-saved-roster-source-20261010.md及外部tw-native-saved-roster-source-249。


## 第250輪：台服完整神祇回包接真正socket寫入觀察

3改0新C++：Session私有被動handle由真正world-records game callback TLS RAII資格化，ready CharacterSelected或InWorld保持實際phase；原void與observed sender共用原enqueue/encode/FIFO/budget。獨立Attempt最後owner CAS Pending→Failed，App保活Data不阻止失敗；exact front/buffer/frame/full transferred唯一CAS Written。Application真companion loop收各batch handles，後續真callback核local/exact bytes/all Written→fullDeityCurrent→local，empty明列NoRecords、read例外明記Failed保留原handler。歷史觀察不是ACK/永久current/actor/grant，沒有callback/held/input屏障，沿原drain。same149c13段698B/182位置及24B tablecell，確定normal init與CF成功分支同Main+1539683C reset，CF有opaque條件、world2A是default，不推定初始化或重排30/31/34/35。

混合部分來源234→235，新增完整玩法0/opcode0。TW C2S156/world S2C252/battle索引110、CN156/280不變，台服完整分母/百分比未知。下一實接同root/reset occurrence/U+86888 epoch與ordinary admission/actor/initial issuer；grant/MP/once/fullreply/WorldOwner/Main與其餘TW流程仍OPEN。未build/test/compiler/runtime/native/codec/遊戲DBSQL/migrate/deploy；goal active，繼續TW優先。詳見docs/research/tw-native-roster-publication-source-20261010.md及外部tw-native-roster-publication-source-250。


## 第251輪：台服真實正常入場來源接神祇存檔及回包

3改0新C++：Session私有NormalWorldInitialization接真select供應者的Frame40/logical37、exact async_write、23B內原尾段及成功world_ready hook。supplier之前捕獲fullowner/battle，prepared之後等值才建metadata；初candidate重標tuple缺口已修並保留舊epoch。TLS current與entry_written分開，允許尾段先到或write先完成，close/fail/替代retire；觀察缺失不阻既有路徑。Application真freshworld存同handle與saved readset/batches，後續真callback join current+entrywritten+全部exactbatchwritten+完整DeityCurrent；Unavailable/Pending/NoRecords不充完成。22原生span1080B/309位置及103B tables，normal S2A成功→同R reset→R90/G綁U86888/86874→C1F/C23/C1C尾段已追；catalog factory仍opaque。本輪未建expected16row reset/replay模型，不是遠端reset/ACK/grant/Main。

混合部分來源235→236，新增完整玩法0/opcode0。TW C2S156/world S2C252/battle索引110、CN156/280不變；台服完整分母/百分比未知。下一接expected receiving-state模型與actualepoch/owned catalog，再ordinary admission/actor/initial issuer；MP/once/fullreply/WorldOwner/Main與其餘TW仍OPEN。未build/test/compiler/runtime/native/codec/遊戲DBSQL/migrate/deploy；goal active，持續TW優先。詳見docs/research/tw-native-world-roster-initial-source-20261010.md與外部tw-native-world-roster-initial-source-251。


## 第252輪：台服實際入場來源接expected神祇技能資料前綴

5改1新C++：新TaiwanNativeDeityRosterPrefix在真251/250 Application normalcurrent+entrywritten+allbatchwritten+savedCurrent之後實際建置及重讀；qualified reset16rows/all100 flags及nullabledefs/aux tails，按真30/31/34 batches順序投影。Opaque status/name/pet原bytes及frameboundary全留，_current比較完整batches，修firstcandidate只比相同投影缺口。handler SQL前own完整inputs，creationthread/reentrypoison，main限定新lookup_main與舊lookup共用原parser；只對referenced448 full110 rows重算SHA及full等值重讀，既有lookup行為不改。不宣稱全448檔/loaded/原子跨來源/wholeGUIafterstate/actor/grant/Main。Native252十span434B/121位置、36B literals，B→manager144938→catalog A924D7C→R4504來源別名已釘，loader/factory成功仍不能證完整材料。歷史448/7676與current453/3adc分版，不刷新基準，peer453/mail僅sourceACK。

混合部分來源236→237；新增完整玩法0/opcode0/globalcoverage0。TW C2S156/world S2C252/battle索引110，CN156/280不變；台服完整分母/百分比未知。下一接ordinary admission/actor/event/initial issuer/control/grant；native MP/once/fullreply/WorldOwner/Main/453profile與其他TW仍OPEN。未build/test/compiler/runtime/native/codec/遊戲DBSQL/migrate/deploy；goal active。詳見docs/research/tw-native-roster-receiving-state-source-20261010.md及外部tw-native-roster-receiving-state-source-252。


## 第253輪：台服戰鬥入口所有者來源與技能資料查讀接通

7改0新C++：實際normal prefix reader、既有conditional issued registry三讀/C35兩讀/saved skill兩讀共用main限定完整110-row SHA API，normal prefix兩讀同路；舊lookup與lookup_main語義保留。Issued完整model含空模型先後比對main完整source metadata；所有primary/aux/secondary/roster inactive tails及私有Session/ready/pending/CAS保留，after_action不重讀已消耗舊grant。新的公開API在SQL前own dataset selector，候選/修正原件分開留。Native253十二span494B/133位置及16B表，S82 logical9→T28/T2C→真descriptor D10=R→B14/R90已追出；非完整1004B事件、actor/deity對應或grant。沒有另造未調用admission殼。

混合部分來源237→238；新增完整玩法0/opcode0/globalcoverage0。TW C2S156/world S2C252/battle索引110，CN156/280不變；台服完整分母/百分比未知。下一接實際S82發行者與同normal receiving/readset/position/Session epoch的participant/86 issuer；WorldOwner/Main/learned actor/grant/MP/once/fullreply及其他TW仍OPEN。Generic issued來源仍generic，normal448/current453分版保留，不稱全檔/loaded/atomic證明。未build/test/compiler/runtime/native/codec/遊戲DBSQL/migrate/deploy；goal active。詳見docs/research/tw-native-battle-admission-catalog-source-20261010.md及外部tw-native-battle-admission-owner-source-253。


## 第254輪：台服實際PK就緒接正常入場來源

3改0新C++：原Session TLS Current保留，另以actual posted select/world-sender私有原件mint的immutable owner thread與exact弱Session incarnation，提供明確on_game純資料Current；先核thread再讀gameIDs，強保活當次Session，不從公有firstcaller認owner。Application實際pk_peer.ready改接完整normal入場/const Restoration/expectedprefix/所有exact Written batches，SQL前own來源、前後local/transport/full saved+catalog Current及重入poison，移除只對PK就緒的diagnostic visibility依賴。既有聊天/visibility填表不動，不把歷史last_observed當當前授權。pk_rooms仍null，未發82或改InBattle，未造stats/contexts/grant/room。Native254釐清1004B是client-local非serverpayload；0/14僅CUSTOM0086視角，fullbattle input producer與雙Session publication/terminal adapter仍缺；既有paired settlement後端不誤稱缺失。

混合部分來源238→239；新增完整玩法0/opcode0/globalcoverage0。TW C2S156/world S2C252/battle索引110，CN156/280不變；台服完整分母/百分比未知。下一接真正owned完整battle profile/readset→prepare_waiting/repo privateTicket與durable pair publication/once recovery，缺原件不造資料。未build/test/compiler/runtime/native/codec/遊戲DBSQL/migrate/deploy；goal active。詳見docs/research/tw-native-owned-battle-readiness-source-20261010.md及外部tw-native-owned-battle-admission-source-254。


## 第255輪：台服黑名單實際請求、儲存與回包

9改5新C++：same149c C89 logical17/name16、C8A logical5/fullDWORD，接actual owned captured-name持久化與A5 logical21/A4 logical5回覆；正常ready後真Tick還原持久項。CUSTOM0096明列immutable name/唯一row namespace/0與FFFFFFFF保留/max10政策，owner刪角cascade、target僅初始provenance；不改聊天filter/IME/字型/轉換。schema及config皆明確opt-in，未安裝或啟用。

新增限定request→storage→reply支線2，完整全遊戲路徑0；mixed239→240。TW C2S候選156/world S2C252/battle索引110保持，世界parser及限定來源支線另見當輪靜態表，不能當全台服完成率。完整台服分母/百分比仍未知。PK完整資料與雙Session房間發布/回合/結束恢復、其餘contact/mail及全遊戲仍待接。未build/test/compiler/runtime/native/codec/遊戲DBSQL/migrate/deploy；goal active。詳見docs/research/tw-native-blacklist-authority-source-20261010.md。

第255輪最終來源：unfinished replay在同Session/owner合法返World後以真Tick重啟，避免舊battle epoch永久pending。來源候選5保留於封存final/；最終6完整14檔另存final-current/，未冒稱測試。新255segment方向鍵使用tw_native_*，不把台服分支加入陸服統計。


## 第256輪：台服組隊目錄刊登、查詢、翻頁與退出

6改3新C++：實際 C8E查詢／C8F刊登更新／C92翻頁→owned transient directory→原生A7回包；C8D1退query、C8D2退query兼撤己刊，單向lifecycle不造ACK。actual private written/current2A的native actor WORD與full64 common owner分開對映，不截斷commonID，不套舊partyHP上限。完整query24含opaque selector/tail保留，A7來源真名字／等級／職業；flags/header0與same-scene discovery/page規則明列CUSTOM0097。projection和回包先準備、來源再重讀後COW發布；接在final handlers後保既有chat/blacklist回覆及順序，default-off未啟用。

新增限定權威request/core支線4（3回包＋1單向lifecycle），完整全遊戲路徑0；mixed240→241。TW C2S156/world S2C252/battle索引110保持；完整台服分母／完成率未知。C90/91、AB真appearance/status、menu join consent、watcher即時廣播、原filter及missing後battle identity renewal仍OPEN，原NativeParty consent不動。未build/test/compiler/runtime/native/codec/遊戲DBSQL/migrate/deploy；goal active。詳見docs/research/tw-native-party-directory-source-20261010.md。


## 第257輪：台服組隊詳情與既有同意串接

6個既有C++來源：C90由當前owned query實際發出的可見列解析到完整Session/common角色與現有party，再產生AB；Photo4完整取private written/current2A logical21..24，明示entry baseline而非DA後current。CUSTOM0098採target先、其他真成員穩定順序至多4slots，原官方選取/status/header仍未知。C91重觀測私有已發詳情/target與相關membership，再接existing NativeParty Join pending→S54 Preview→原C58 Answer才真正加入；不即時join、不造ACK。highWORD原raw保存，不當0/nonce；legacy commonWORD與actualnativehandle精確相同才橋接，不截斷full64。NativeParty只增readonly完整state比較，rules不改；預分配投影/重讀來源後再commit。

新增限定權威支線2（1詳情回包＋1pending consent），完整全遊戲路徑0；mixed241→242。TW C2S候選156／world S2C252／battle索引110保持；完整台服分母／完成率未知。廣義ID適配、窄資源呈現、DA currentappearance、watcher及原filter/window、postbattle identity renewal仍OPEN。未build/test/compiler/runtime/native/codec/遊戲DBSQL/migrate/activate/deploy；goal active。詳見docs/research/tw-native-party-detail-consent-source-20261010.md。


## 第258輪：台服組隊名單跨玩家推播；本輪後依使用者要求停止

4個既有C++來源接入CUSTOM0099：實際owned query查看者的A7完整清單／A8撤列／A9精確描述推播。C8F刊登更新、C8D2撤刊、world_ready、disconnect及原handler成功後均接入reconcile；C8D自己的query/detail（mode2連同listing）先獨立撤銷，再best-effort推播。A9保留原生postNUL尾端；AB/last_join仍存在時用A7清除。修正caller預建A7來源需二次完整一致。單一query識別tombstone／容量衝突可能整個plan failclosed、延後刷新；consent後僅membership變化的AB刷新仍OPEN。普通IO送出不是原子fanout／Written／ACK。

新增限定推播投影3；來源push opcode8→11（A7/A8/A9），request reply47維持，mixed242→243。C2S候選156／world S2C252（固定230、可變22）／battle索引110／world parser73／限定C2S50維持；完整遊戲新增路徑0，台服分母與完成率未知。全部來源仍未build/test/執行/部署。使用者要求本輪結束停止；此來源保存時goal API active，全部收尾後才呼叫paused，不宣稱已完成100%。


## 第259輪：台服完整設定WORD與局部開關來源

CUSTOM0100預設關閉：實際C1D fullWORD seed/update，已知baseline後B1(7/8)只改0200並保留其他位元，S1B完整WORD feedback與延後入口恢復。原生wire/consumer已定點追查；server echo/persistence policy並非官方已知，不造初始0、不拿RoleAuxiliary替代。精確Session/fullcommonowner/private written-current entry，ready時僅標記、後續合格callback才恢復，斷線精確清理。設定不授予chat/filter/gameplay/權限變更。

新增限定設定請求變體3、同Session入口恢復支線1；設定控制與玩法分開，玩法C2S50保持。world parser73→74、控制10→11、回覆47→48（S1B）、mixed243→244；候選156／world S2C252／battle索引110保持；完整全遊戲新增路徑0，分母與完成率未知。沒有build/test/runtime/native/codec/DBSQL/migration/activation/deploy。使用者已要求恢復目標工作，但本輪起始goalAPI仍paused；不能把文字授權假寫成API active。


## 第260輪：入隊同意後的組隊詳情生命週期

3個既有C++來源新增CUSTOM0101：C90提交AB後保留獨立Presentation完整owner/target/group/participants順序及party_size；C91只消耗privateDetail，Presentation不能授予入隊權限。實際C58同意／C57踢人／C5A退隊解散及成員斷線後，完整readset可觸發A7清除，即使名單列不變。失敗新C90只撤權，保留舊實際AB來源紀錄到替代AB/A7或query退休。補上舊capturedprivateentry current/written檢查，避免同Session重新入口且wire相同誤把舊憑證當有效；C91真正權限及watcher最後發布均檢查，NativeParty規則不改。

新增限定呈現生命週期支線1及private來源資格修補1；完整全遊戲新路徑0／新opcode0。mixed244→245；C2S候選156、world S2C252、battle索引110、world parser74、玩法來源C2S50、限定回覆48、推播11維持。全遊戲分母與完成率未知。未build/test/compiler/runtime/native/codec/DBSQL/migrate/activate/deploy；goal現讀active。單query整plan conflict、非原子送出、官方eventpolicy及postbattle entry renewal仍OPEN。


## 第261輪：組隊名單單一查詢衝突隔離

CUSTOM0102在每個watcher的Query副本完成投影；issued WORD衝突、重複身分、容量或列格式不合格時丟棄該次嘗試，僅為該當前收件者準備零筆完整A7，保留原issued歸屬，清掉visible/description/Detail/Presentation/lastjoin。其他已合格查詢繼續。已有完整空白來源基準時不逐包重送；這不是Written/ACK。直接prepare失敗則只reconcile實際舊狀態，不提交失敗listing；補上該新路徑的reentered回傳檢查。

2個既有C++、0新增，實際691216 bytes。限定watcher隔離支線1＋既有失敗reconcile邊1；新opcode0／完整全遊戲新路徑0。mixed245→246；C2S候選156／世界parser74／部分玩法50／限定回覆48／推播11／世界S2C252／battle索引110維持。全遊戲分母與完成率未知；goal現讀active。未build/test/compiler/runtime/native/codec/DBSQL/migrate/activate/deploy。global readset/CAS/alloc/IO/原生opaque呈現與其他玩法仍OPEN。


## 第262輪：戰鬥表情C66→S77來源串接

CUSTOM0103保留實際完整bootstrap及全部S1C，依原生variant2000完整WORD身分、初始S86/5主選擇寫入與實際Battle/controller綁定，接上standalone posture0 C66→普通framed S77。綁定Session弱參照、帳號/角色及battle generation；表情與獨立server時鐘只在回包準備後更新，不改戰鬥數值/回合。App在battle分支提前返回，保留原世界姿態。原生S77是secondary queue，不新增primary110索引。

6修改＋1新增C++；mixed246→247，既有opcode的限定來源變體1，完整全遊戲新增路徑0。功能預設關閉，現有入口僅explicit diagnostic player bootstrap；普通共用戰鬥producer/對手fanout與原生呈現仍OPEN。準備好的bootstrap與歷史grant不代表Written/ACK或當前native model/selector。全遊戲分母與百分比未知。未build/test/compiler/runtime/native/codec/DBSQL/migrate/activate/deploy，goal維持active。


## 第263輪：一般PK入場與本地S1C選擇器的原生來源

本輪完成限定靜態資料流：真2A低14位本地身分→Main角色欄位→實際T+0→Battle+48→自有S1C variant2000、side0、完整WORD與DWORD相等→primary selector+51。原先僅由初始化FF推論必須補初始grant的假說被新原始指令推翻；未修改等待時序、補發grant或虛構RoomAuthority。條件仍含原生handle!=FFFF與opaque呼叫，不代表角色已成功建構。

0個C++修改／0新增；新增原生限定資料流資格1，無新增opcode、來源回包分支或完整玩法。mixed247、reviewedgroups26、世界parser74／部分玩法50／回覆48／推播11維持，TW來源關聯37／去重33、CN93／去重71維持。初始0B targetlist/count未有完整來源，不能猜成零遮罩；真正雙攻雙防／技能profile、2A/DA→86/4、雙Session入場與恢復仍缺。全遊戲分母及百分比未知；goal維持active。未build/test/compiler/runtime/native/codec/DBSQL/migrate/activate/deploy。


## 第264輪：首次控制通知與動態目標來源

追到實際battle loop→513CE0在0B前有條件改寫44C目標清單與45C數量；入口旗標初始0、事件重啟與首次ordinary值仍未知，不能推定零遮罩或固定值。實際大型HeapAlloc flags0也不提供清零保證。CUSTOM0104新增明確opt-in Prepared通知模式，現有repository綁定完整entry所導出的可用slot範圍，version2 round只在InitialControl收集一次實收mask並持久保留，無攻擊/技能/傷害權威。既有owner/header/current/自身entry提交與雙通知→獨立grant barrier保留；legacy exact API/readset/version1與後續ResultsControl exact resolver masks不變。

5個既有C++來源修改；mixed247→248，限定unhosted core來源分支1、request/reply及完整玩法新增0。實際C69房間、權威profiles/完整入場/雙Session持有發布仍OPEN。全遊戲分母、完成路徑與百分比未知。未build/test/compiler/runtime/native/codec/DBSQL/migrate/activate/deploy；goal active。


## 第265輪：一般PK外觀的完整原生讀取與Fight資源來源

追完當前149c ordinary mode1／specialWORD0的S86/4讀取範圍與實際資源callee：最後packed pair透過454F60固定family1/component3選列，row+2A供其他component family；454E50使用side字元15、component字元bfhw及r%d%c%d%c%d%02d，資源來自Data2/Fight。這與世界HeroDoll key/catalog不同，不能僅憑8bytes相同就宣稱2A/DA→完整86/4原生轉換。選定完整ordinary分支未讀logical12/15/16且未傳原record別名給child，只是限定讀取事實，不是原服務端tail內容或新canonical政策。

0個C++修改／0新增／0 CUSTOM，新增限定原生資料流資格1；source segments248、reviewedgroups26、TW來源關聯38／去重34、CN93／去重71維持。C2S候選156／世界parser74／部分玩法50／限定回覆48／推播11／世界S2C252／battle索引110維持；新增完整玩法0。真實owned跨catalog selector來源、完整戰鬥profile與雙Session RoomAuthority仍OPEN，分母與完成率未知。goal active，未build/test/compiler/runtime/native/codec/DBSQL/migrate/activate/deploy；peer v61只收到通知未讀receipt或ACK，先前v60有限ACK不擴張。


## 第266輪：Fight實際欄位來源接入四個入場視角

從verified=true清理封存精確取回run02/native.json（2,853,351B，SHA55009500...142d），只保留外部本輪證據；現有HeroDoll及Fight編碼原檔均與歷史資料pin吻合。歷史JSON完整保存3578個Fight、918個world解析欄位列；這不是完整原始decodedCSV或rawoffset，decodedSHA仍是歷史紀錄。Chinese欄位有效Unicode，先前終端顯示異常不作資料有損證明。

新增TaiwanNativeFightCatalog，對完整既有ordinary86/4按當前149c的component3→family、component2→derivedordinal及其餘key讀取實際列；新的明確Prepared入口在每個viewer的own0／other14重綁後各選列，四組選取及完整17bytes保留至既有房間readset。舊工廠／readset與CUSTOM0086／0104策略保持；2份C++修改、1份新增，限定資源來源串接1，mixedsegments248→249；沒有新增opcode／方向階段關聯或完整玩法。

TW來源關聯38／去重34、CN93／去重71；C2S候選156、世界parser74、部分玩法來源50、限定回覆48、推播11、gated推播4、世界S2C252（230fixed／22variable）、battle primary110／specialized9、86 subtype7／處理6、83 actions23／投影2維持。world與Fight有569barekey交集、349worldkey無Fight對應，匹配鍵與雙side仍有衍生欄位差異；fresh限定域只證明列選取閉合，非完整角色producer。真實owned戰鬥profile、完整入場／grant及雙Session的RoomAuthority仍缺，Application未啟用；整體分母／完成率未知。

goal active；依使用者順序未build/test/compiler/runtime/native/assetcodec/gameDBSQL/migrate/activate/deploy。只執行靜態來源記帳與精確封存容器解壓。peer v62僅保留收件metadata，receipt未讀／未ACK，不擴張舊v60有限ACK。


## 第267輪：當前owned外觀來源接入戰鬥準備

新增OwnedTaiwanPkAppearanceSource，從實際Session私有normal-entry receipt（已完成本機write）、ready lease、同writer完整inventory及1215B裝備聯合Committed保留不可任意鑄造的Observation。先檢查game-thread/Session receipt才讀Session欄位；完整角色、帳號、handle、root、原入場pose、目前saved position、revision及同connection來源逐項保留。SharedWorldPresence generation與Application PK world_generation分屬不同命名空間，沒有猜測相等。

CUSTOM-0105明確選取transform0限定域、普通mode1／special0，原樣投影DA packed8及高3bit，12／15／16採限定分支padding0；這是自訂呈現producer，非官方服務端恢復或world/battle等畫面證明。兩角色資料在新的Prepared工廠進入四個收件者相對Fight選取，完整來源寫入條件readset；reserved prepare/current/initial/activate才於SQL交易外檢查Current，後續active動作不要求過期world lease。舊工廠／readset／schema不改，Application仍未啟用。

修正舊265／266文字：實際Frame40／logical37，原封存receipt保持不改。原生追查另確認DA完整WORD與localRole完整DWORD比對；transform0只為充分條件，selector0不可推論action0；world/Fight衍生欄位差異也不否定明確自訂packed8投影。

本輪2份C++修改、1份新增、CUSTOM0105新增；限定material source1，mixedsegments249→250。新增完整玩法0，opcode／階段關聯與全域來源group26不變。TW C2S候選156、世界parser74、部分玩法來源50、限定回覆48、推播11、gated4；世界S2C252（230fixed／22variable），battle primary110／specialized9、86 subtype7／處理6、83 actions23／投影2不變。TW owner來源關聯38／去重34，CN93／去重71。全遊戲路徑分母與完成率未知；parser50／74的67.6%不作完成率。

下一步接完整owned戰鬥profile、S1C／82／88／grants/context與兩個確切held Sessions到共用RoomAuthority；保持preflight／SQL／queue原子性、world return及reconnect缺口明確。goal active；未build/test/compiler/runtime/native/codec/gameDBSQL/migrate/activate/deploy。peer v64只保留收件metadata，未讀完整receipt／未ACK，不計整合。


## 第268輪：完整owned雙攻雙防資料接入PK準備

目前149c自角色S2C2C完整61B接收／顯示來源已定點確認：logical45物防、49物攻、53法防、57法攻均為完整DWORD絕對拷貝；%d是有號顯示，沒有原生100萬上限或截斷規則。修正值是獨立WORD／mask處理；五行只確認接收operands，不推論標籤順序／相剋公式。2C不帶敵人ID，未恢復怪物真正數值或原服計算公式。

CUSTOM0106明確採用實際owner-bound資料庫所存舊6bf／CUSTOM0045的2C絕對總值，僅選origin欄為NATIVE_CAPTURE_VERIFIED的記錄；此字串不是獨立原生證明，拒絕CUSTOM_TEST_NOT_NATIVE，原始build／raw61／origin／provenance／revision全部保留，不變更存檔或重新標成149c。新私有combat source與267實際外觀receipt同源，完整角色root／pose／role／resources／auxiliary一致讀取；prepare_owned直接消費兩份receipt產生actors／roles／resources及內部算出的完整profile digest，條件readset保留全部來源。reserved SQL使用封閉具體reader比較捕獲資料，liveSession／joint Current留在交易外；active保持入場選定數據，不要求過期worldlease。

本輪4份既有C++修改、1份新增、CUSTOM0106新增（103筆既有完整保留→104筆）；限定combat material來源1，mixedsegments250→251。完整玩法0、新opcode0、全域來源group26維持。TW C2S候選156、世界parser74、局部來源50；S2C世界格式252（230fixed／22variable）、限定回覆48、推播11／gated4；battle primary110／specialized9，86 subtype7／處理6、83 actions23／投影2不變。TW owner來源關聯38／去重34，CN93／去重71不變。全遊戲分母／完成率仍未知，67.6% parser覆蓋不作完成率。

仍需真實技能／actor／規則、完整S1C／82／88／grants/context、共用RoomAuthority及兩個held Sessions入場／回復。既有LegacyCustom不支援的數值明確拒絕，不clamp／截斷；64位元擴充與其他原生版本目標保留。goal active；沒有build/test/compiler/runtime/native/codec/gameDBSQL/migrate/activate/deploy。peer v65僅保留收件metadata，完整receipt未讀／未ACK，不計互通驗收。


## 第269輪：實際保存名稱／第二文字接入完整玩家S1C來源

目前149c完整玩家S1C45的兩段16B是實際名稱／第二文字輸入，分別經5097D0與509E70進原生顯示欄位；WORD7及DWORD41旗標確實影響狀態，不能當padding。CUSTOM0107明示採正常玩家variant2000、ordinal0、status0；此為新自訂呈現規則，不冒稱原服預設或原生未使用欄位。全45不等於完整56B既存actor metadata／renderer建構。

新增私有player entry source消費268實際combat／角色／資源、267外觀與完整common root，加上同連線實際保存CUSTOM0056第二文字16B／UTF8／codepage／revision；缺資料列拒絕，真正保存空文字另論。依每收件者實際private正常世界初始化config0／1做CP950／936嚴格無損投影，產生四份完整45B，不共用錯誤編碼字串，不代換／截短名稱，不改存檔。新entry factory消費完整來源與保存level／identity／appearance，HPMP完整templates須比對268實際資源；不猜vital opaque、82 contexts、88 counter、grant。完整來源與四份records進room conditional readset／live preflight及reserved封閉SQL比對；active保留入場凍結material。

本輪3份既有C++修改、1份新增，CUSTOM0107新增（104筆既有完整保留→105筆）。限定完整玩家identity來源1，mixedsegments251→252；完整玩法新增0、新opcode0。TW C2S候選156／世界parser74／局部玩法來源50，控制11／未串玩法13；世界S2C252（230fixed／22variable）、限定回覆48／推播11／gated4；battle primary110／specialized9、86 selector7／case6、83 action23／限定projection2維持。TW來源關聯38／去重34，CN93／去重71維持。全遊戲路徑分母／完成率未知，67.6% parser覆蓋不是完成率。

仍需原始variant／ordinal／status規則、完整82／88／grant／技能與renderer條件；真正共同RoomAuthority、69接受後雙Session heldqueue／input barrier與非同步啟用、部分I/O回復、終局世界返回及重連待接。保留台陸／網頁、共用64位數值等完整目標。goal active；沒有build／compiler／tests／runtime／native／codec／gameDBSQL／migrate／activate／deploy。


## 第270輪：接受PK邀請接入雙Session held entry與共同房間啟用

新增CUSTOM0108明示非同步入場：精確69Accept私有token→optional AsyncRoomAuthority／AdmissionPending→雙方實際Session私有PREPARING／Held收據、完整encodedqueue與輸入barrier→重查269／268／267來源及獨立PK／commonlease分代→單一RoomState持久啟用→雙方不再配置記憶體或呼叫callback的預配置battleidentity提交→釋放雙entry→精確fullsocketwrite／revision1／viewer出站submitted。不是只post兩個queue就Accepted；既有同步authority及普通sender未選新API時保留。

既收／暫存／partial或barrier競爭輸入拒絕，舊read僅取消自身operation且收到ack後才Held；不取消socket所有write，不在Invite階段阻擋69Accept。原生無epochnonce，尚不能證明TCPqueued／延遲舊bytes完全不存在。取消前提交只abandonReserved；active後失敗關雙方且保留room／outbox／memberlocks，無假rollback。自訂Session5秒、invitation15秒及256retainedroom配額明示；取消Reserved回收strongSession，active／complete／failedActive等terminalrecovery，容量可能耗盡。

本輪3份既有C++修改、1份新增；105筆舊CUSTOM完整保留→106筆。非同步entryadmission來源1、mixedsegments252→253；新opcode0、完整玩法路徑0。TW C2S候選156／世界parser74／局部玩法來源50，控制11／功能未接13；世界S2C252（230fixed／22variable）、限定回覆48／推播11／gated4；battleprimary110／specialized9、86selector7／case6、83action23／projection2不變。TW關聯38／去重34、CN93／去重71不變。全遊戲總路徑／完成率未知；67.6%是parser限定覆蓋。

Application pk_rooms仍未安裝；實際82／88／vitalopaque／grant完整來源、commonworldvisibility、35／技能／Lua規則、結果與世界返回／重連／恢復待接。保留台陸／網頁與共用64位數值目標。goal active，未build／compiler／test／runtime／native／codec／gameDBSQL／migrate／activate／deploy。


## 第271輪：實際已存資源接入完整HP／MP入場封包來源

新增CUSTOM0109：private268完整已存資源→私有VitalSource→與269玩家來源精確Combat收據一致→內部產生四份完整17-byte HP0／MP0→雙viewer六個ownHP／ownMP／opponentHP14入場記錄→共同房間完整readset／digest與實際wirebytes比對。新增來源不再需要caller提供普通vitaltemplates；既有路徑保持完整原WORD／tail。Repository現行Session／來源Current在SQL外，RESERVED完整storedtuple在交易內；ACTIVE使用已入場不可變來源。

完整149c 517230／5173A0所有topbranches及callee scalarargs證明ordinary0／1僅讀position／subtype／DWORD5maximum／DWORD9current，六個3..4／13..16bytes不讀且不傳packetpointer。明示自訂零序列化，不當原生padding／官方producer／全域unused；side1MP原生忽略，不送。忠實MP0／maxMP0不造max1，opaqueGUI顯示未證。S88 counter1／raw118實際使用，完整82／88／futuregrant仍原樣caller供應，本輪不猜值。

本輪2份既有C++修改、1份新增；106筆舊CUSTOM完整保留→107筆。ownedvital來源1、mixedsegments253→254；新opcode0、完整玩法路徑0。TW C2S候選156／世界parser74／局部玩法來源50，控制11／功能未接13；世界S2C252（230fixed／22variable）、限定回覆48／推播11／gated4；battleprimary110／specialized9、86selector7／case6、83action23／projection2不變。TW關聯38／去重34、CN93／去重71不變。全遊戲總路徑／完成率未知；67.6%僅parser限定覆蓋。

Application pk_rooms仍未安裝；original完整入場context／counter／grant、commonworldvisibility、35／技能／Lua規則、結果及世界返回／重連／恢復待接。private268的舊6bf資料採用仍CUSTOM0106，不能說恢復149c原公式或怪物真值；保留台陸／網頁與共用64位數值目標。goal active，未build／compiler／test／runtime／native／codec／gameDBSQL／migrate／activate／deploy。


## 第272輪：實際角色來源接入初次操作授權完整封包

新增CUSTOM0110：private269玩家／268Combat來源→私有InitialGrantSource→完整17-byte86/5→與271Vital精確Combat收據一致→Prepared與共同房間readset／digest完整來源比對。初次雙方0B通知後才發grant，9records／305-byte入場流不變。實際Current在SQL外，RESERVED完整storedtuple在交易內；ACTIVE保留已入場來源。

明示自訂flags1／ownslot0／rawWORD5=0與raw2、7..16 canonicalzero；只產生三個resource數字001，不當原生時限／回合／官方授權或GUI顯示成功。完整86/5對WORD5是零擴展DWORD加1再取末三位；secondarylabel可在無mask02時更新，缺bit不清secondarycontrol。S82／S88仍完整外供，raw118操作位08／04／02／01不能當padding。歷史contextA本地時間說法追加更正：ordinaryC35actions1／2／0B packedtargets0..27條件式echo，實際timeGetTime獨立；S82contextBbyte1原樣unsigned0..255。S88 RET4起518BE8、exclusiveend518BEB；舊封存不改。

本輪2份既有C++修改、1份新增；107筆舊CUSTOM保留→108筆。新增initialgrant來源1、mixedsegments254→255；新opcode0、完整玩法路徑0。TW C2S候選156／世界parser74／局部玩法來源50，控制11／功能未接13；世界S2C252（230fixed／22variable）、限定回覆48／推播11／gated4；battleprimary110／specialized9、86selector7／case6、83action23／projection2不變。TW關聯38／去重34、CN93／去重71不變。全遊戲總路徑／完成率未知；67.6%僅parser限定覆蓋。

Application pk_rooms仍未安裝；完整context／counter／commonworldvisibility、35／技能／Lua規則、latergrants、結果／世界返回／重連／恢復待接。保留台陸／網頁與共用64位數值目標。goal active，未build／compiler／test／runtime／native／codec／gameDBSQL／migrate／activate／deploy。


## 第273輪：私有來源產生完整初次 S82／S88 入場封包

新增CUSTOM0111：exact private269Player／271Vital（相同268Combat／267Session來源）→完整9-byte82與121-byte88→無callerView的factory→實際Prepared九records／305bytes→房間fullprefix／tail／readset／digest。contextA採checked actual Session prebattle generation+1，不截低位、不wrap、不是globalnonce／timestamp／musicseed／roomID；contextB0x1400的BYTE1為自訂20秒，HIGHWORD0不當globalunused。初始counter0／own0保存HPMP／13emptyplaceholder0／raw1180與1171191200均明示CUSTOM，不冒稱官方producer或padding。

原生成功normalreset提供168inlinepointers／14friendlytype0；空槽1D8FFFF由52D9F0略過opaque顯示，不需14個虛構身份。仍保留constructor／allocation／resource／cleanup成功條件與GUI未驗收；不造emptymaxima／opponentMP。actual Current在SQL外，RESERVED完整storedtuple在交易內，ACTIVE沿用已入場immutable來源。初次雙方0B後才發既有272grant，不改後續回合來源規則。

本輪2份既有C++修改、1份新增，3source84,671bytes；108舊CUSTOM exact保留→109筆，mixedsegments255→256。新增initialcontext source1、新opcode0、完整玩法路徑0、reviewgroups26不變。TW世界parser74／局部來源50／控制11／未接13；S2C252（230fixed／22variable）／限定回覆48／推播11／gated4，battle110／specialized9、86selector7／case6、83action23／projection2；TW來源關聯38／去重34、CN93／去重71均不變。全遊戲總路徑與完成率未知，67.6%僅parser限定覆蓋。

Application pk_rooms未安裝；commonvisibility、35／skills／Lua turn/results、latergrants／counter、terminal／worldreturn／reconnect／recovery待接。全TW／CN／web與共用64位數值目標保留；未build／compiler／test／runtime／native／codec／gameDBSQL／migrate／activate／deploy。根代理本輪另處理使用者GitHub私有專案與Discord通知；.git／.gitignore／工作流與通知檔案完全不計273source證據。273帳務由source子代理依授權完成，root未聲稱全文閱讀native/findings/doc；各代理實際閱讀範圍分開封存。


## 第274輪：同資料庫的 PK 入場準備來源

CUSTOM0112新增joint.observe_committed唯讀完整durable tuple→真正private joint／雙writer憑證；不執行無意義write，不把普通Before或兩次獨立讀取拼成提交證據。callback-compatible準備來源以實際Session／private正常入場Written／InWorld／共同readyLease／savedPose／exactPair ready與blocked及世代重觀察，依序連到267外觀→268角色能力→269玩家文字→271體力→273完整82／88與初次grant→prepare_owned。伺服器seed由明示可信來源供應，不能用context、時鐘或任意預設冒充原生規則。reservation後失敗會abandon RESERVED；未啟用或發包。

SqliteDatabase factory只組裝同一connection的實際reader／writer及joint，保留rawdb私有、Fight immutable資料owned lifetime與借用Database／room drain要求。CharacterSelected不得順手改InWorld。單向common lifecycle release不是PK暫停／返回；完整世界可見性退場與回場、35／skills／Lua turn／results、terminal／reconnect／recovery仍待接，Application pk_rooms維持未安裝。

本輪5份既有C++修改、1份新增，CUSTOM109→110、mixedsegments256→257、groups26不變；new preparation source1、新opcode0、完整雙向玩法路徑0。TW C2S parser74／具局部來源50／控制11／未接13；S2C252（230fixed／22variable），回覆48／推播11／gated4；battle110／specialized9、86selector7／case6、83action23／projection2。TW未host關聯38／去重34、CN93／去重71不變。全遊戲分母與完成率未知；未build／compiler／test／runtime／native／codec／gameDBSQL／migrate／activate／deploy，保留TW／CN／web與共用64位數值及凍結功能。


## 第275輪：雙人 PK 世界可見性退場來源

CUSTOM0113把可見性專用的雙端退場接到明示 opt-in admission：同一 rooms.activate 後，兩個真正 private Held 與 common lease 產生 paired departure；先封鎖兩端、撤下雙方完整 incidence，取消待發來源與以既有 native73 撤下存活觀察者，再重驗兩個 Held；兩個 Session commit 後以新增 private Committed-current 及 departure fence 重驗，最後釋出 held82。保留共用 presence／common transport identity；不呼叫單向 lifecycle.release，不以 raw InBattle 或舊 normal Current 冒充私有承諾。

新 departure 不產生猜測回場；post-activate 失敗關閉雙端並保留 active/outboxes，marker 由 exact cleanup 回收。private current 僅為 Held／Committed 的 pre-release 範圍，不是 Written/nativeACK 或 terminal authority。原有未選取此 common visibility 的 admission/default 與凍結功能維持。Application pk_rooms 未安裝；Finished 鎖、完整 saved settlement／89／fresh generation initialization／worldreturn 與 restart recovery 仍待接，舊 diagnostic 回場不能代用。

本輪既有 C++ 修改6份／新增0份；CUSTOM110→111、mixed257→258、groups26不變；新增 departure source1、新opcode0、新完整雙向路徑0。TW C2S74（具局部分支50／控制11／未接13），S2C252（230fixed／22variable），回覆48／推播11／gated4；battle110／specialized9，86selector7／case6，83action23／projection2。TW unhosted38關聯／去重34、CN93／71不變。全遊戲總量與完成率未知。未build／compiler／test／runtime／native／VM／codec／gameDBSQL／migrate／activate／deploy；GitHub/Discord通知分開記錄，不當遊戲驗收。


## 第276輪：保留私有 Ticket 的持久 PK 房間復綁

CUSTOM0114由原 repository 的真正私有 Ticket 讀取 active／finished room、雙方 owner locks、完整 checkpoint／RNG、round 與全 outbox，產生不可外造的 recovery snapshot。RoomState 先取得唯一 runtime claim、恢復該 checkpoint 並預配置 map node，最後重驗完整 durable snapshot 才發布房間。activate 也持有相同 claim，拒絕另一個 RoomState 同時擁有第二份可修改 Battle；失敗由 RAII 釋放未發布 claim，舊持有者析構後才可復綁。

復綁不從 seed 重開、不重置 round／grant／intent／submitted，不自動重送或解除 Finished 鎖、不改 saved resources 或 Session。此來源只恢復仍保留真正 Ticket 的執行器房間；跨程序 restart 的 private Prepared／Observation／Session／initialization 重建、terminal saved settlement／native89／fresh generation worldreturn 與 Application hosting 仍待接，不能以 scalar／JSON 偽造憑證。

本輪既有 C++ 修改3份／新增0份，CUSTOM111→112、mixed258→259、groups26不變；新增 retained recovery source1，新opcode0、新完整雙向路徑0。TW C2S74（具局部分支50／控制11／未接13），S2C252（230fixed／22variable），回覆48／推播11／gated4；battle110／specialized9，86selector7／case6，83action23／projection2。TW unhosted38關聯／去重34、CN93／71不變。全遊戲總量與完成率未知；未 build／compiler／test／runtime／native／VM／codec／game DB SQL／migration／activation／deployment。GitHub／Discord 通知另外記錄。


## 第277輪：私有 PK 入場接到真正授權／結果封包寫出

CUSTOM0115新增 opt-in outbox owner：同一 live Room 的原 Ticket incarnation，加上雙 Session 私有 Committed hold，在任一 entry release 前綁定；真正 full entry write 經其來源接受並清除 pending 後，以保留的私有 Written proof 接初次0B／35來源入口及後續封包。fast first0B 不要求另一端 Written，但兩端都不能 closing。新 Session PK sender 僅接受已有限定 standalone86/5 或一／兩組 scalar83／HP86（own MP可選）及 final88，不放寬原87／38／86-5技能 sender。

明示 pump 讀取型別區分的 grant epoch／result revision，before write 與 full write completion 都重查完整 pending row、實際 checkpoint／round 和私有 Session incarnation，完整本機寫出才標記 submitted；不是 enqueue 或 native ACK。普通 callback response 先排入，之後才插 held frame；既收 prefix 在 release 前拒絕，快速回覆 bounded暫存直到交接完成。每viewer最多一個Flight，completion不auto-pump；5秒 deadline 及256 retained binding quota明示自訂。失敗關閉並保留room／locks／outboxes，不重送或偽造rollback；executor allocation失敗可能延後通知另一端，不能聲稱所有callback必達。

本輪既有C++修改5份／新增1份，CUSTOM112→113、mixed259→260、groups26不變；新增限定publication來源1、新opcode0、新完整雙向路徑0。TW C2S候選156／世界parser74（局部來源50／控制11／未接13），S2C252（230fixed／22variable），回覆48／推播11／gated4；battle110／specialized9，86selector7／case6，83action23／projection2；TW來源關聯38／去重34、CN93／71不變。全遊戲總量與完成率未知。

Application仍未安裝；完整Lua turn／skills／fresh projection、later grants／counter、terminal saved settlement／89／fresh generation worldreturn／reconnect／restart私有憑證仍待接。原生無epoch nonce，不能證明未接收TCP舊bytes不存在。保留TW／CN／web、共用64位數值與凍結功能；未build／compiler／test／runtime／native／VM／codec／gameDBSQL／migrate／activate／deploy。GitHub／Discord通知分開記錄。


## 第278輪：正常 CharacterSelected 入場接到 PK 私有準備狀態

CUSTOM0116修正已存在的來源阻塞：正常原生bootstrap有意保留CharacterSelected，既有private normal初始化Current允許CharacterSelected或InWorld，但PK外觀／準備／Session hold硬性要求InWorld。現於真正game-owner初始化proof通過後捕捉每位玩家實際合法phase，Appearance私有State及Preparation局部binding各次Current／callback fence都比對原phase；Session私有Data的Preparing／Held／cleanabort沿用同一exactphase，只有既有commit轉InBattle並battle generation+1。取消不製造InWorld，也不實作terminal世界回復。

C++既有5檔修改，其中3檔行為、2檔註解；新增C++0。Material／Request／歷史durable readset／schema／原生封包不變；無callerphase或publicphasegetter。mixed260→261、CUSTOM113→114、groups26不變；新增限定phase來源1，新opcode0，新完整雙向路徑0。這是條件式PK來源可達性修補，Application仍未安裝，不能稱正常玩家已可實際PK。

TW C2S候選156／世界parser74（局部來源50／控制11／未接13），S2C252（fixed230／variable22），回覆48／推播11／gated4；battle110／specialized9、86selector7／case6、83action23／projection2；TW來源關聯38／去重34、CN93／71不變。CN歷史觀察C2S156／S2C階段opcode280／length253屬不同範圍。全遊戲路徑總數及完成率未知，不把50／74當遊戲百分比。

尚缺完整Application派送、同一權威Lua回合／技能、fresh83 opaque／group及88counter／raw118、latergrant／controlmask、terminal存檔／89／世界回復／重連。原生來源審查另更正：PK撤出移除visibility incidence，仍保留ready lease；這不自動授權技能，也不能拿失去presence當拒用理由。phase equality不是事件歷史／ABA證明。保留TW／CN／web／共用64位及凍結功能，未build／compiler／tests／runtime／native／VM／codec／gameDBSQL／migration／activation／deploy。


## 第279輪：真正房間持有的 fresh 基本攻擊結果來源

新增CUSTOM0117 OwnedTaiwanPkBasicResultSource，由實際RoomState私有Ticket／目前單一Battle／repository Ready雙指令產生fresh83/1及88，接既有雙方相對視角與原子settle。嚴格要求兩位owned player/vital/combat/initial-context完整圖與initial88 seed0；legacy Ticket不升格，commit後不拿prebattle world Current作battle權限。basic只限物理零MP單對手；actual Rule必須pure/nonreentrant，server order及next masks仍必須明確提供。完整round document fence防止供應後重讀變動。

本輪新static native追查分開R4、basic13/14、scalar3尾端及88 current/首次seed/readiness/latch。full15 queue copy／global context／renderer仍未全閉合。root另讀caller保留group與manager52AC20，發現255 BYTE加一wrap跳actor scan；首版mod128保留，修為mod127、兩組0..253。opaque零、group及positive checked counter=round≤INT32_MAX均為明示CUSTOM，不宣稱原服公式、native接受或全客戶端忽略。

C++既有1檔修改、新增1檔，限定freshbasic source1；mixed261→262、CUSTOM114→115、groups26不變。新opcode0、新完整雙向路徑0；TW C2S156／世界parser74（限定來源50／控制11／未接13），S2C252（fixed230／variable22）、回覆48／推播11／gated4；battle110／specialized9、86selector7／case6、83action23／projection2不變。TW未掛載關聯38／去重34、CN93／71不變；CN歷史C2S156／S2C階段opcode280／length253屬不同範圍。全遊戲分母及完成率未知。

尚缺Application／Lua完整owner派送、技能fresh83、later grants及實際control masks、terminal存檔／89／世界返回／重連。現有legacy signed16 loss仍failclosed，不能代替TW/CN/web64位擴充；完整目標與凍結功能保留。webv74僅metadata pending，沒有ACK或來源credit。PHASE1無build/compiler/tests/runtime/native/VM/codec/gameDBSQL/migration/activation/deployment。


## 第280輪：私有PK整批輸入派送與明確雙方結算橋接

CUSTOM0118在既有OwnedPkOutboxPublication加入complete-frame preflight：Tick-only、單一0B加Ticks、單一basic1加Ticks；空批、混合、重複、skills/action2或其他操作整批在durable寫入前拒絕。實際private Session／Written hold／Ticket推導room、viewer、context及目前phase，未綁定才回空；已indexed但錯誤／pending／failed不得落入diagnostic。分開現行server profile仍是必填且須等於Ticket retained digest，不能把retained equality冒稱current issuer。BasicParameters只含明確有界數值，不接受caller header／source／MP／skill map。既有own outbox／own grant submitted guard保持。

顯式resolve bridge接279freshbasic83/88及原子雙方settle，必須兩Written／pending清空／無Flights或pump，copy order／next masks／pure Rule，Rule前後檢查actual Battle snapshot與完整round document；同binding reentry poison及失敗close雙方保留durable狀態。無inline pump，不拿Tick作ACK或grant。native worker只重讀3段681B舊263證據，0新PE範圍，不聲稱原服mixed frame排程或full35完成。

Application pk_rooms仍null，本輪未掛載。現有真正initialization registry保留；下一步需實際current profile／Fight archive／seed／coefficients／order／next masks／Lua owner及合法idle output scheduling，later grant／terminal89／saved settlement／world return／reconnect仍缺。不加dummy factory/default來灌正式進度。

既有C++1檔修改、新增0；限定adapter1，mixed262→263、CUSTOM115→116、groups26不變；新opcode0、新完整雙向路徑0。TW C2S156、世界parser74（限定來源50／控制11／未接13）；S2C252（fixed230／variable22）、回覆48／推播11／gated4不變；battle110／specialized9、86selector7／case6、83action23／projection2不變。TW未掛載chains3、bindings38／去重34；CN chains35、bindings93／71不變。CN歷史C2S156／S2C階段opcode280／length253屬不同範圍。分母及百分比未知。webv75 metadata pending，無ACK／integration credit。完整TW/CN/web／shared64及凍結功能保留；PHASE1無build/compiler/tests/runtime/native/VM/codec/gameDBSQL/migration/activation/deployment。


## 第281輪：實際active房間的凍結入場profile綁定來源

CUSTOM0119新增repository require_active_owned_profile，原issuer／完整private來源圖／同connection／全readset／內部digest，ownBEGIN snapshot核13main表與TEMP shadow、既有PKDDL版本、active room／2locks／saved roleresourcespose／無獨立battle；persisted完整checkpoint含RNG須等於RoomState真正Battle，驗immutable topology／initialrev1／fullround。由private Room內部取得expectedcheckpoint；新no-profile-argument派送直接消費此來源，resolver每pure Rule前後再查。舊explicitprofile seam保持外部owner責任，不冒稱已內部查核。

Active採admitted immutable stats/text/appearance，絕不把RESERVED recursive stored_current或戰前worldCurrent搬進來；current combatHPMP/RNG只由一個Battle提供，savedresources不等於戰鬥中HPMP。Read snapshot不是lease或Session+SQL原子，既有write CAS／grant／outbox fences保持。

另找出已verified exact FightJSON2853351B／550095...abd142d及現讀installedCSVZ36974B／1195af...338b8。既有from_archive已fullhash／rowgate，下一步仍須明示singleopen bounded JSON provider；本輪未decode／restorewhole tree／實作provider／掛Application。seed／coefficients／order／nextmasks／Lua／idleoutput／latergrants／skills／terminal89／savedsettle／worldreturn／reconnect仍缺。

C++4既有檔修改、新增0，限定profile source1；mixed263→264、CUSTOM116→117、groups26不變，新opcode0、新完整雙向路徑0。TW C2S156／worldparser74（限定來源50／控制11／未接13），S2C252（fixed230／variable22）／reply48／push11／gated4不變；battle110／specialized9、86selector7／case6、83action23／projection2不變。TW chains3／bindings38去重34，CN chains35／bindings93去重71不變；CN歷史C2S156／S2C階段opcode280／length253範圍獨立。全遊戲分母／百分比null。完整TW/CN/web／shared64與凍結功能保留；webv70..75 pending無新ACK或credit；PHASE1無build/compiler/tests/runtime/native/VM/codec/gameDBSQL/migration/activation/deployment。


## 第282輪：限定FightJSON檔案來源接實際準備工廠

CUSTOM0120新增TaiwanNativeFightCatalog::from_archive_file，copy明示filesystempath，singlebinaryopen／固定2853352B read，只收exact2853351+EOF+noBad，再交原owncopy→SHA→JSON→3578row gate；empty／openfailed／short／extra／bad／nonEOF拒絕。不stat／reopen／窄字串／Zsuffix／fallback／CSVZdecode。新的Database *_from_archive在IO前查actualsameDB／presence／room／4resolver身份，catalog完整合格後才delegate原factory；沒有callback／prepare／reservation／schema／Sessiontransition。

檔案provider補上既有準備工廠實際輸入，仍無Configpath/default/Appinstall。具體JSON來源已在281留verified550095...abd142d；c5d8 parseddata與current149c code／1195af compressedasset保持分開。後續grant再讀retained272 fullconsumer：WORD5 unsigned+1僅最低3decimalglyphs，非88counter／timer／mask／serverepoch。CUSTOM0110初次scope及round!=1 guard保持，不冒稱原服laterproducer已恢復。

C++3既有檔修改／新增0，限定fileprovider source1；mixed264→265、CUSTOM117→118、groups26不變；新opcode0／完整雙向路徑0。TW C2S156／worldparser74（限定來源50／控制11／未接13），S2C252（230fixed／22variable）／reply48／push11／gated4不變；battle110／specialized9、86selector7／case6、83action23／projection2不變。TW chains3／bindings38去重34，CN chains35／bindings93去重71不變；CN歷史C2S156／S2C階段opcode280／length253獨立範圍。分母／百分比null。

仍缺actualseed／coefficients／order／nextmasks／Lua／idleoutput／latergrants／skills／terminal89／savedsettle／worldreturn／reconnect的完整Appowner。完整TW/CN/web／shared64與凍結功能保留；webv70..75 pending無新ACK／credit；PHASE1無build/compiler/tests/runtime/native/VM/codec/gameDBSQL/migrate/activate/deploy。


## 第283輪：實際房間快照產生後續主要授權

CUSTOM0121由RoomState實際Ticket／Battle checkpoint接Repository明示overload，同transaction沿用完整activeprofile issuer／privategraph／sameDB／readset／main+TEMP／schema／memberlocks／savedowner／fullRNGcheckpoint／frozenactor／round資格，再由private freshsource產生17B86/5。舊Ticket-only後續拒絕、round1原來源、非Grants空結果皆保留；不重用初次raw、不讀prebattle Current/stored_current、不刷新戰鬥屬性。

限定active LegacyCustom／round2..INT32MAX／兩個活著canonicalcontroller／currentGrants+epoch。BYTE3=1／BYTE4=0，WORD5=(round-1)%999僅CUSTOM三位數顯示，非timer／88counter／epoch／mask或原服公式；raw2/7..16 canonical0範圍保留。既有exactbytes+typedepoch before/fullwrite及ownGrant輸入閘門不變。無inlinepump／resend／Apphost。

Retained5159BC..515A59再讀釐清513080收到Battle+490，非已證44C列表；helperbody不在合格span，51398D僅raw disp32候選非instructionstart，不算maskwriter／新nativecoverage。動態next0B masks／actualseed／coefficients／order／Lua／idleoutput／skills／terminal89／savedsettle／worldreturn／recovery仍缺。

C++既有3改／新增1，限定latergrant source1；mixed265→266、CUSTOM118→119、groups26不變；新opcode0／完整雙向路徑0。TW C2S156／worldparser74（限定來源50／控制11／未接13），S2C252（230fixed／22variable）／reply48／push11／gated4，battle110／specialized9／86selector7／case6／83action23／projection2均不變。TW chains3／bindings38去重34、CN chains35／bindings93去重71不變；CN歷史C2S156／S2Cphaseopcode280／length253獨立範圍。全路徑分母／百分比null。TW/CN/web/shared64、凍結功能保留，webv70..76 pending無新ACK；PHASE1無build/compiler/tests/runtime/native/VM/codec/gameDBSQL/migrate/activate/deploy。


第283輪靜態審查補強：新actualcheckpoint overload在任何phase的第一個round／owner lookup之前拒絕TEMP替代與檢查13個main tables，並全phase比對完整durablecheckpoint/RNG/id/revision，避免偽造round1降級跳過later資格。舊Ticket-only初次介面保持原行為；terminal空結果及legacyinitial不要求完整ownedgraph，後續grant仍必須完整private資格。候選1／初次帳本與報告保留，候選2為最終來源；REVIEW283-01以來源修補，無執行測試。


## 第284輪：實際戰後roster與本輪結果通知

CUSTOM0122新增明示Outbox／RoomState basic通知resolver，保留privateWritten／profile／order／pureRule／reentry邊界，actual staged postBattle交Round產生relativebounds1/1，非caller exactmask／initialmask／hit targets猜測。只有明示v2→canonical17field v3，v1/v2舊exact格式及行為保留；exactresultsAPI拒絕v3降級。percyclebounds／observations／battlerevision獨立permanentfirstreceipts，null與observed0/0分開。ownresultsubmission後每端一次subset通知，兩端後advance once/newgrant epoch；receipts保留Grants/Collect/Ready，freshresults重置；Terminal無0B／grant。

Repo由actualnextsnapshot重推wholefollowingdoc，transaction在firstupgradewrites前完整originalprivateprofile資格，checkpoint／phase／tworesults原子寫入。v3readbindissuer／sameDB／readset／frozenactor／RNG／cycle／兩個resultrow，每個recordedreceipt必須ownsubmitted。無DDL／save migration／inlinepump。

Native新bounded靜態恢復513080／514B70及mode tables：51398B才是aligned45Ccountwriter，51398D在disp32內；分支46C==47及record條件，unsignedinput4 cap5並清14targets，非basic/fresh0B固定值。Basic464==1只見first44Cwrite，無direct45Cwrite，opaquechildren／readiness仍缺。CUSTOM通知不冒稱原服公式；舊同header/mask跨cycle延遲replay無nonce不可唯一辨識，仍開放。

C++5既有改／新增0，限定resultnotification source1；mixed266→267、CUSTOM119→120、groups26不變；新opcode0／完整雙向路徑0。TW C2S156／worldparser74（限定來源50／控制11／未接13），S2C252（230fixed／22variable）／reply48／push11／gated4、battle110／specialized9／86selector7／case6／83action23／projection2均不變。TW chains3／bindings38去重34、CN chains35／bindings93去重71；CN歷史C2S156／S2Cphaseopcode280／length253獨立範圍。全路徑分母／百分比null。Apphost／seed／coefficients／order／Lua／idleoutput／skills／terminal89／savedsettle／worldreturn／recovery／shared64仍缺；完整TW/CN/web及凍結功能保留。Webv70..77 metadata pending無新ACK／credit／容量測量。PHASE1無build/compiler/tests/game/runtime/native/VM/emulator/codec/gameDBSQL/migrate/activate/deploy。


第284輪原生證據補充：51F2A0先收到input+4，之後清14targets，再讀unsignedinput4 cap5；mode47是second-dispatch當下46C，非已證函式進入值。worker完整2helpercode4614B／1426ins+table128B、retainedcaller745B已比對ownpinnedimage；4547codeB相對具名TW283 scope為新增，67B重疊countdown，不作globalcoverage百分比。candidate1 source不變，candidate2只精確修正文件順序與覆蓋範圍。


## 第285輪：實際 Lua basic owner 與原生數量來源

CUSTOM0123新增OwnedTaiwanPkLuaBasicOwner，由同一RoomState建構並獨佔OutboxPublication，借用實際LuaEngine。明示coefficients／兩端order複製、界限檢查且immutable，無caller Rule／stats／nextmask／templates／default seed。Admission private committed holds bind，完整nativeframe dispatch沿現有privateprofile／identity／epoch；input與Tick不resolve／pump。明示advance_at_idle只於真正後續gameidle使用，實際pair／incarnation／failure檢查，privateWritten／flights／pending不就緒回AwaitingTransport；兩端新Session private binding predicate先核對Committed／Released／Written的原pending／common／normal／world／battle identity，revoked拒絕並failpair、不當無限retry；phase／pre-resolver／output例外也failpair，非fullwrite授權。此狀態不證明ordinaryoutput／strand清空，一次post不足。Ready才同步呼叫內部Lua combat_damage，LegacyCustom／zeroMP／exactcoefficients及既有pureRule前後profile／checkpoint／phase／reentry fence；同一sharedBattle原子settle後透過原outbox送兩視角。Grants／ResultsControl／Terminal僅訪問pending；Initialrevision1仍Admission獨有，Collect不resolve。OutputVisited／Resolved不是fullwrite／remoteACK／nativeacceptance；無async Lua捕捉／新scheduler／App啟用。scriptbytes/reload並非本次immutablepolicy，既有CUSTOM0006及legacy限制保留。

Native限定靜態51F2A0完整74B／27ins，實際manager2F4／2F8逐bit計數；flag0計0..13、nonzero計5..13，perbitreload非atomicmask snapshot。mode47 input4／5即flag1輸出，aligned51398B的min(count,5)只限該條件分支。5154E0完整398B／131ins，selectedrecord BYTE1==2且WORD3E!=0FF5先轉opaque5108C0(47)繞過普通countsetup；普通515619數量來自51EAD0(manager,selectedBYTE45,&Battle468)，仍下輪追查，末端flag0計全部14bit。5151A0完整785B／264ins及36Bshortcut table確認轉交input。總新scope1257codeB／422ins+36dataB，不作全client覆蓋率／固定0Bmask／原服公式。

C++既有3改／新增1，限定Lua-basic owner source1；mixed267→268、CUSTOM120→121、groups26不變，新opcode0／完整雙向路徑0。TW C2S156／worldparser74（限定50／控制11／未接13），S2C252（230fixed／22variable）／reply48／push11／gated4、battle110／specialized9／86selectors7／cases6／83actions23／projection2均不變；TW chains3／bindings38去重34、CN chains35／bindings93去重71，CN歷史C2S156／S2Cphaseopcode280／length253各自範圍。全遊戲分母／TW與全遊戲百分比null。App pk_rooms仍null；真正seed／Fightpath／coeff/order政策選擇／idle重試排程與drain／技能／terminal89／savedsettle／WORLDreturn／recovery／shared64仍缺。Webv70..77 metadata pending，無新ACK／acceptance／容量測量。完整TW/CN/web及凍結功能保留。PHASE1無build/compiler/tests/runtime/native/VM/emulator/codec/gameDBSQL/migrate/activate/deploy。


## 第286輪：實際 PK scheduled driver 與原生選擇數量表

CUSTOM0124新增OwnedTaiwanPkBasicDriver，擁有285LuaBasicOwner／同一Publication／RoomState，保存原Ticket／兩Session／privateholds。bind前配置mapnode並用新Session identity-only API核對實際gameexecutor。明示1..1000ms CUSTOM重試政策、單一coalescedsteady_timer、weaklifetime／terminalstop取消／dirty Idle休眠；input／writecallback不inline resolve／pump，真正後續gamevisit才Ready/bothprivateWritten/clearedpending之內部Lua結算。scheduled不是idle證明，仍用既有Session staging：game_busy等待、普通ACK先enqueue再resume-stage、partial／staged／skillprefix及beforewrite二次檢查保留。無offstrandbuffer getter／一次post假就緒。已durablesettle之後仍可能strand拒絕，保留checkpoint/outboxes恢復、不冒稱網路原子。timer／allocation／reentry／revokedbinding failclosed保留room/locks，reentry立即close使pureRule fence可見；exactdisconnect停止後仍idempotent。無App啟用／WORLDreturn／savedsettle／reconnect/restart。

Native完整51EAD0 94B／27ins及571BB0 table72B（正常讀68B），signedindex1..17固定count [1,2,3,4,1,1,1,1,1,1,1,1,2,7,1,3,2]，13／14／16 flag0其餘1；ECXmanager不讀。actual515614選selectedrecordBYTE45，515619寫Battle45C／outBattle468，與51F2A0 maskpopulations分開。invalid402C70 opaque，不把index0當合法；此普通actionkind3路徑可被mode47繞過，不作basic／0B普遍公式。下一追查selectedrecordBYTE45 producer／resource／skillmapping與metadata／mask lifecycle。

C++既有4改／新增1，限定scheduleddriver source1；mixed268→269、CUSTOM121→122、groups26不變，新opcode0／完整雙向玩法路徑0。TW C2S156／worldparser74（限定50／控制11／未接13），S2C252（230fixed／22variable）／reply48／push11／gated4、battle110／specialized9／86selectors7／cases6／83actions23／projection2不變；TW chains3／bindings38去重34、CN chains35／bindings93去重71，CN歷史C2S156／S2Cphaseopcode280／length253範圍獨立。全分母／TW與全遊戲百分比null。App pk_rooms仍null，真正Fight／seed／coeff／order政策與Admission／driver／Application生命周期、技能／terminal89／savedsettle／lockrelease／WORLDreturn／recovery／shared64仍缺。完整TW/CN/web與凍結功能保留；Webv70..79 metadata pending，無新ACK／acceptance／容量測量。PHASE1無build/compiler/tests/runtime/native/VM/emulator/codec/gameDBSQL/migrate/activate/deploy。


## 第287輪：同資料庫 PK 後端擁有者與選取記錄來源

CUSTOM0125新增OwnedTaiwanPkRoomBackend及SqliteDatabase私有組合工廠，擁有同一repository issuer／RoomState／Preparation／scheduledDriver／Admission。明示實際Lua／gameexecutor／presence／visibility／Fight archive／四供應者／basic係數／順序／重試政策；非空及同角色來源／samepresence與policy bounds在檔案IO前檢查。單一shared resolver bundle保留每個callable一次，前後terminal fence涵蓋resolver內同步stop；不複製mutable std::function目標。Admission pre-release Bind消費同一Driver的原Ticket／兩Session／privateholds，完整native frame仍走既有私有輸入／ACKprefix／Written障壁，不inline結算／送包。stop保留Admission物件／map、撤銷weakcallbacks、不通知已清退invitation completion，再停Driver；清退後reserved abandon／active close保留durable checkpoint／outbox／lock。destruction Admission→Driver→Preparation→RoomState→repository，bundle存活至forwarder後；外部Invitation raw authority offers／completion必須先drain，DB／初始化Lua／executor／捕獲物件必須存活。無App賦值／預設政策／schema安裝／WORLDreturn／savedsettle／recovery。

Native worker完整5156A0／51B8C0／51B900三小函數187B／55ins：actualBattle+A9DF73C索引，不讀caller stackarg。A9E9C38為0且A9E9C3C非0才secondary；manager Battle+A9DC198。primary signed groupBYTE+4 0..15，count+10+g*2D0／pointer+DC+g*2D0+i*4；secondary unsigned groupBYTE+2D10<3，count+2D64+g*54／pointer+2D28+g*54+i*4；signed index>=0且<count，invalid null。三body皆不供應record+45內容；pointer-table／record writer及技能ID／內容／生命週期仍OPEN，不冒稱原生技能authority。

既有C++3改／新增1，限定backend composition source1；mixed269→270／CUSTOM122→123／groups26不變。新opcode0／完整雙向玩法路徑0。TW C2S156／worldparser74（限定50／控制11／未接13），S2C252（230fixed／22variable）／reply48／push11／gated4／unclassified117；battle110／specialized9／86selectors7／cases6／83actions23／projection2不變。TW unhostedchains3／binding38去重34、CNchains35／binding93去重71；CN歷史C2S156／S2Cphaseopcode280／length253為不同範圍。分母／TW與全遊戲百分比null。Application pk_rooms仍null，hosting／可信policy suppliers／Invitation drain／skills／terminal89／savedsettle／lockrelease／freshWORLDreturn／reconnect/restart／shared64仍缺。完整TW/CN/web與凍結功能保留；Webv70..80 metadata pending，無新ACK／server acceptance／容量測量。PHASE1無build/compiler/tests/runtime/native/VM/emulator/codec/gameDBSQL/migrate/activate/deploy。


## 第288輪：私有 PK 終局來源與原生89接收條件

CUSTOM0126由原Ticket／實際Finished Battle／Terminal v4 phase及完整owned entry graph私有導出57B無訊息89，明示selector4與其他52payload bytes零是TW CUSTOM，非原服padding／PK獎勵／零收益。RoomState把它附於兩view最後88後，同checkpoint／roundCAS／pairedoutbox transaction，無假Battle revision／新outboxnamespace／獨立89receipt。v4只在Terminal保留結果通知政策，既存v1／v2／v3文件codec與legacy exact-mask API保留；notification resolver的Finished結果現在選v4並附新tail。Repository settle／read_round核對83／可選ownMP86／targetHP86／final88／canonical89 grammar及privateterminaltail；Publication在beforewrite／fullwrite重導actualFinished，Session只開此受限後綴並沿用privateWritten／ACKprefix／stagedhold／currentidentity／queuebudget障壁。無App賦值／savedresourceXP／lockrelease／WORLDreturn／recovery。

Native worker完整518BF0..518E3A 586B／188ins，selector49 unsigned>3直達共同cleanup；0分支四slot正DWORD／WORDFFFF及5／9／13／53顯示，1／3固定ProgramMsg300／299原TW文字與語義仍OPEN，2分支DWORD1 mod32abs／397398。所選>3完整topbody無其他directpayloadread／explicitpacketpointerforward，但opaque children／callee-savedEBP／globalalias OPEN，非全clientpadding證據。5140C0..51460E1358B／403ins證實83group與callerlocal延後88／89，88consume後停止本visit；529020..5295211281B／411ins readiness也可10s timeout，非全animation／ACK保證；52AED0..D7 7B／2ins僅manager2E0getter，writer／515C40完整exit與WORLD lifecycle OPEN。含messagebinding完整70B／20ins共5code spans3302B／1024ins與5data487B，保留745B歷史loop且承認overlap。未跑messagecodec。

Source audit指出先存HPMP會破壞原owner/readset，須PK專用atomic雙人beforeafterledger與窄settledterminalguard；不能兩次套diagnosticsettlement／預設HP1／推斷零獎勵。原案separateterminaloutbox早於完整FIFO新證據，本增量改samefinalpair並明示無獨立89receipt。Bothlocks／terminalrows保留，freshnormalinit／presence／visibility／returnowner／reconnectrestart仍缺。

既有C++6改／新增2；限定terminalsourcebranch1，mixed270→271／CUSTOM123→124／groups26不變。新opcode0／完整雙向玩法路徑0。TW C2S156／worldparser74（限定50／控制11／未接13），S2C252（230fixed／22variable）／reply48／push11／gated4／unclassified117；battle110／specialized9／86selectors7／cases6／83actions23／projection2不變。TW unhostedchains3／binding38去重34，CNchains35／binding93去重71；CN歷史C2S156／S2Cphaseopcode280／length253不同範圍。完整分母／TW與全遊戲百分比null。Application pk_rooms仍null，hosting／可信policy suppliers／Invitation drain／skills／savedsettle／lockrelease／freshWORLDreturn／recovery／shared64仍缺。完整TW/CN/web與凍結功能保留；Webv70..81 metadata pending，無新ACK／server acceptance／容量測量。PHASE1無build/compiler/tests/runtime/native/VM/emulator/codec/gameDBSQL/migrate/activate/deploy。


## 第289輪：雙方實際fullwrite到原子終局HPMP存檔

CUSTOM0127只由同一私有Publication Binding實際兩端fullwrite完整交付／同terminalrevision／原Session privatehold／writtenpointer重核後，經privatefriend RoomState自持runtimeclaimedcheckpoint及兩完整writtenbuffers進privateRepo。submitted flags只是追加DB guard，不可鑄造／重啟恢復fullwrite能力。單TX重導完整privateissuer／sameDB／原readsetprofile／mainnamespace／exactschema／canonicalFinishedRNG／actors0/14／Terminalv4／兩memberlocks／兩final88+canonical89rows及實際兩writtenbytes，無olderpending。clone原resources只用actualHPMP，maxima／designCUSTOM0012保留、revisionchecked+1一次、HP0不改1。雙人fulltuple CAS／readback／新CUSTOM0127 fullledger／stagedguard同commit，無nestedcharacterwriter／diagnosticID reuse／XProleeconomy修改／零獎勵推論。

新feature／ledger explicit extension，oldPK/resourceDDL及finishedstate不改；backendfactory在archiveIO前require既有extension，無安裝執行。ACTIVE／RESERVED owners_current原樣，僅Finished精確ledger重導after；缺extension／ledger仍核原resources。material不遞迴read_round／require_ticket；RetainedRecovery加optionalledger finalcut，防相同checkpoint／rows掩蓋存檔epoch變化。兩locks與finishedcheckpoint／outbox保留；丟失私有fullwrite能力／第二writeflag後resourcecommit前故障不能從DBflags自動結算／重啟。savedDB與network／WORLD非原子，freshinit／presence／visibility／lockrelease／原獎勵／revival／recovery仍缺。

Native worker16選取spans3831B／1078ins（非全域新增，含273initializer等歷史overlap）。52AEA0 setter把arg寫manager2E0/2E4；normal51FC40初始化1，第一次83兩prefix重置0，FIFO條件ready後setter1，非死亡判據。完整515C40 exit66B／5118E0 cleanup514B／465BC0 WORLDtop576B及481C20 aggregateinit845B，追到Main1539683C保存大aggregate／位置／資源；不是logical37 2A或HP1可取代。Main arg1是textbuffer、arg2 globalBOOL，465BC0拿returncode+text；中途錯辨明確保留修正。502210／465638 deferredcontinuation／opaquechildren／完整aggregate來源仍OPEN；無原服award／resource／revivalauthority宣稱。

既有C++6改／新增0，限定terminalresourcesave branch1；mixed271→272／CUSTOM124→125／groups26不變。新opcode0／完整雙向玩法路徑0。TW C2S156／worldparser74（限定50／控制11／未接13），S2C252（230fixed／22variable）／reply48／push11／gated4／unclassified117；battle110／specialized9／86selectors7／cases6／83actions23／projection2不變。TW unhostedchains3／binding38去重34，CNchains35／binding93去重71；CN歷史C2S156／S2Cphaseopcode280／length253不同範圍。分母／TW與全遊戲百分比null。Application pk_rooms仍null；完整TW/CN/web、凍結saves／auth／chat／IME／fonts／conversion／nativeEXE保留。Webv70..82 metadata待實際source／commit／server配對審閱，無新ACK／共同驗收／容量測量。PHASE1無build/compiler/tests/runtime/native/VM/emulator/codec/gameDBSQL/migrate/activate/deploy。


## 第290輪：原生保留世界返場來源與伺服端owner邊界

本輪具體靜態恢復11選取code spans／8247B／2394instruction sites及4DATA／85B，含歷史overlap，非全域新增覆蓋。完整502210680B為資源呈現，非完整角色constructor／HPMP來源；完整500C601370B／5011C01101B恢復aggregate讀寫與opaque子呼叫邊界，WORD0／48經46C6A0零arg2分支為UI/context key，不作共用角色ID。主狀態表465A14 index3→465644→4678601123B持續worldloop，完整466B002964B→468AE0實際parentT；state3 arm不要求fresh2A，opaquechildren／各worldroute仍OPEN，無新0B／1C／ACK。4FAC70完整169B是字串catalog，466910是RET4、467D70是mask removal；早期timer／185B／actorinit標籤明確修正保留，不提升成事實。

更正前輪frontier的「fresh normalinit」：它是尚未證實的方案，不是原生返場前置。實際PK保留commonpresence／transport identity，visibility departure只Held／Committed PRE-release current；Written後marker仍阻擋，不能直接delete當ready。Session normalinit綁原battle generation且只CharacterSelected／InWorld，set_state進出InBattle皆+generation；舊frame／tail無法鑄造fresh receipt。Fresh lifecycle／release為一次登入與清理，會撤原lease；不可當返場捷徑。現有native24 HP-loss還會扣同伴HP，Application freshentry在companionbinding前送、後續避免重送，非通用返場更新。

下一實作目標是genuine retained-world resume owner：先追468AE0 resumed queue／4FB290 inputcatalog context／真outbound clockcontrol與原aggregate／角色同伴resources來源，再把同一私有terminalfullwrite／savedledger／Sessions／leases／departure接到新generation world capability、撤battleinput、重建incoming／outwardvisibility及durablelockrelease／recovery；無猜包、HP1、fresh2A重播或unusedwrapper湊進度。C++0改／0新，CUSTOM125／mixed272／groups26不變，sourcebranch0／新opcode0／完整雙向路徑0。TW C2S156／worldparser74（限定50／control11／未接13），S2C252（230fixed／22variable）／reply48／push11／gated4／unclassified117；battle110／specialized9／86selectors7／cases6／83actions23／projection2不變。TW unhostedchains3／binding38unique34、CNchains35／binding93unique71；CN歷史C2S156／S2Cphaseopcode280／length253不同範圍。全遊戲分母／TW與全遊戲百分比null。原凍結功能及289存檔來源不改，App hosting／rewards／EXP／return／unlock／restart仍缺；無build／compiler／tests／runtime／nativeexecution／VM／emulator／codec／gameDBSQL／migrate／activate／deploy。


## 第291輪：原生1C終局context實際私有輸入接點

Native465DF2→4157F0實際送1C+4B：lowWORD為保存normalentry aggregate0的nativehandle，highWORD是cached GetSystemDefaultLangID Chinese/Simplified predicate0/1，非勝敗／CP／displayconfig。原PEimport及四選取code spans與mapped149c相等，無全image等價宣稱；14code spans1452B453sites／3importdata48B，含歷史overlap。獨立supplement重用263來源三span292B比對sameMain1539683C→468160第二arg→468629AND3FFF→468633[EBP]，0newcoverage；sameentry/noopaque rebind條件保留。Shared4132E0 queue與467B43 flush4133F0→413370→4124D0已限定，無firstpacket／standalone／ACK推論。

CUSTOM0128由actualBackend→Driver→LuaOwner→Publication existingfullframe入口接ContextNotification，整span pureclassification只exactlyone1C+Ticks；mixed/repeat/unsupported先拒。只有context避開activeonlyprofile讀取，改由privateRoomState自持runtimeclaimedcheckpoint與originalBinding ownterminalfullwrite/revision進privateRepo single readsnapshot：sameDB/issuer/privategraph/readset/mainTEMP/exactschema/canonicalFinishedv4/兩memberlocks/兩finalrows，ownfullbytes/submitted1/原nativeentryhandle，0/1locale不比較winner/config。Firstviewer可在peeroutput/save未完成前到達；不requirebothsubmitted/savedledger。原before resources或精確0127after均重導。所有fallibleguard後重核ownhold/writtenpointer/revision/noownflight/noownpending，最後fixedsize processlocalmarker；exactretryidempotent/differentrawfailclosed。無DBwrite/schema/recoveryepoch/phaseflip/lockrelease/WORLD/ACK/App；futureconsumer須freshguard不可從DBflag重建。

Sourceworker另恢復10completebodies+4partial1733B555sites，現有own86與final88已經4E71E0同步retainedroleHPMP；final88先用packetownHPMP+actormaxima再bulksetter。相同consumer減selectedcompanionHP，沒有mode/contextbypass；0127playeronlyledger未存該companionRAMdelta，不能補猜24或誤稱完整resourcesettlement。Opaque returnchildren/resourcepreservation、nativeworldgrouping、samelease/newgenerationresume、visibility/locks/recovery/restart/rewards/revival/fullskills/App仍缺。

既有C++4改／新增0，限定terminalcontext sourcebranch1；mixed272→273／CUSTOM125→126／groups26不變。新opcode0／完整雙向玩法路徑0。TW C2S156／worldparser74（限定50／控制11／未接13），S2C252（230fixed／22variable）／reply48／push11／gated4／unclassified117；battle110／specialized9／86selectors7／cases6／83actions23／projection2不變。TW unhostedchains3／binding38unique34；CNchains35／binding93unique71，CN歷史C2S156／S2Cphaseopcode280／length253不同範圍。分母／TW與全遊戲百分比null。Webv70..84metadata待actualsource/server配對，無新ACK／聯合驗收／容量測量。凍結saves/auth/chat/IME/fonts/conversion/nativeEXE及CN/web保留；PHASE1無build/compiler/tests/runtime/native/VM/emulator/codec/gameDBSQL/migrate/activate/deploy。


## 第292輪：原始同伴發布來源接入PK準備與房間讀集

CUSTOM0129保留actualsameDB companionrepository/helper/catalog、genuineprivateNormalInitialization、exactlocallyWritten restoration批次，完整30/31/all34／orderedrows／revision／provenance／nullableselection／templatekeys／expectedresetdataprefix／full110skilldefinitions及原Session/phase/battlegeneration。PrivateObservation sharedincarnation，material不能自造權限。新optionaltrustedresolver實際接Preparation/completeBackendfactory→Input完整readset/profiledigest→Reserved/Active/Finished closedSQLroster/catalogguard。Configured兩owner都必須成功；缺resolver保留舊行為，非emptyroster。OutsideTX liveCurrent多次核privateinit/fullwrite/owner/reentry/storagechange；insideTX只closedSQL、無Session/worldcallback/nestedBEGIN/oldwriterbehaviorchange。無HP/MP CAS／skillgrant／send／newDDL／WORLD／App啟用。

Receipt無queueordinal/originalnormalinitpointer；只證exactlogicalbytes於同ownerstate locallyWritten，無physicalresetorder／後續companiontraffic排除／nativeRAM／消費確認。ActualApplication registry resolver尚未裝配；prefix只expecteddata。既有writer鎖battle_reservations非ownedPKmemberlocks，新storedguarddetectdrift但不interlock/repair。DBselection缺且roster非空時31仍可選最後row，不能當無同伴。Nativecompanion2C/30為currentHP/maxHP，非MP；saved31→這些offsetproducer未解，0127playerledger非同伴持久化。

Native15selecteddisjointspans7944B2497sites／22fullinputs，current149c與original5fc選取bytes相等，無wholeimage等價。4E7CAB發布sameaggregate+90到UI86888，4B1295→4E72D0→4AC070只條件unsignedcurrent>max裁切；current<=max跳過stores，maxMP0跳過wholeleaf，opaqueUI/role/renderchildren仍OPEN。Actualreturn4658F8先寫manager13418=1，再465902→4FAC60→4FAFC0→4FC900→4FC560清occupied128slot身份；此修正先前modeunknown，不覆寫歷史seal。Qualifiedworld6F→4FB460 existingcleanup→complete4FC1C0constructor／4FCC60ringreset，ordinary461270缺任一四resourceWORD則skip；未造profile／ACK／renderacceptance。

既有C++10改／新增header1，限定companionlineage sourcebranch1；mixed273→274／CUSTOM126→127／groups26不變，新opcode0／完整雙向route0。TW C2S156／worldparser74（限定50／控制11／未接13）；S2C252（230fixed／22variable）／reply48／push11／gated4／unclassified117；battle110／specialized9／86selectors7／cases6／83actions23／projection2不變。TWunhostedchains3／binding38unique34；CNchains35／binding93unique71；CN歷史C2S156／S2Cphaseopcode280／length253不同範圍。FullTW/全遊戲分母與百分比null。Samelease/newgenerationresume/input／同伴resourcepersistence／visibility雙向重建／memberlockrelease/recovery/restart／fullskills/App仍缺。Webv70..84metadata待actualpairing，無新ACK/聯合驗收/容量測量。保留frozenaccounts/saves/auth/chat/IME/fonts/conversion/nativeEXEs/CN/web，PHASE1無build/compiler/tests/runtime/native/VM/emulator/codec/gameDBSQL/migrate/activate/deploy。


## 第293輪：真實離開世界憑證保留至終局輸入

CUSTOM0130 actualAdmission Attempt privateTaiwanPkDeparture，經exclusiveadditiveDepartureBind／sameDBfactory先captureowners後move／Driver／LuaOwner到Publication私有Binding，beforeentryrelease。ActualVisibility/presence/2originalleases/recordedposes/Sessioninstances/privateholdpointerexact。Bind BOTHCommitted，新retainedguard BOTHbinding_current+OWNacceptedWritten；actualterminalcontext前後消費，peerfinal/savepending不要求bothoutput。OldHeld/Committedpre-releaseguard不變。新增Presence activeexactregistry-onlypredicate，沒有repository/SQL/observercallback；recordedpose非freshsavedpose，原RepoFinished/readset/兩locks/ownrow/fullbytes等獨立重核。舊3argbind保留，actualfactoryrequiredprivateDeparture不fallback。無DDL/DBwrite/unlock/Worldstate/generation/normalinit/6F/73/markerretire/App。

Native18selectedcoderanges4295B1355sites+12data91B／17fullinputs，149c/current與5fc/original選取bytes相等，非wholeimage/globalnewcoverage。ActualS39 length17→46A00B→4AA9E0，logical1DWORD寫selectedcompanion2C currentHP、logical9DWORD寫30 maxHP；logical5/13 WORD寫34/36僅raw。S2B currentHP-only；S30/31complete tops無direct2C/30stores，31refresh讀existingresources，saved30/31/34不可當resourceproducer／HP CAS。Complete4E63F0/4E6710/4AC2C0/4E6C90 no topstaleHPMPcopy，4E6710 specificbranches反號88/8A/8C/8E，opaquechildren仍OPEN。Nativeworker保留firstPEoffsetpackagingfailure及sectiontranslation修正，歷史seal不變。

既有C++9改／新增0，限定retaineddeparture sourcebranch1；mixed274→275／CUSTOM127→128／groups26不變，新opcode0／完整雙向route0。TW C2S156／worldparser74（限定50／控制11／未接13）；S2C252（230fixed／22variable）／reply48／push11／gated4／unclassified117；battle110／specialized9／86selectors7／cases6／83actions23／projection2不變。TWunhostedchains3／binding38unique34；CNchains35／binding93unique71，CN歷史C2S156／S2Cphaseopcode280／length253不同範圍。FullTW/全遊戲分母與百分比null。下一步 genuineeffectiveNormalInitgeneration保留originalphysicalEntry/Written、asyncstrandACK/inputbarrier、sameleasevisibility重建、privatedurableFinishedunlock/recovery、actualselectedownerresource。不可freshEntered/normal2A/loginreplay/HP1/defaultawards替代。Webv70..85metadata待actualpairing無newACK/聯合驗收/peerexecution/current容量測量。保留frozenaccounts/saves/auth/chat/IME/fonts/conversion/nativeEXEs/CN/web/NativeParty；PHASE1無build/compiler/tests/runtime/native/VM/emulator/codec/gameDBSQL/migrate/activate/deploy。


## 第294輪：終局輸入到實際傳輸排空屏障

CUSTOM0131 actualretaineddeparture Binding acceptedterminal1C，實際world_records TLS+原privateWrittenentryhold+ownexactfinaldelivery，接distinctSession terminalbarrier。Strand等當前gameACK確認acceptance並排入response、emptyworldinput/pendingrecords/skillprefix、actualreadcancel operation_aborted+0ACK、writes/bytecount完整排空，再gameowner privateReady callback前後重核Finished/ownfullbytes/readset/ownerpose/bothlocks/departure。Ready≠accepted，所有Ready後queueappend（包括held）invalidate/failclose；獨立5sdeadline持續Ready/accepted。弱gamefacade、once ready/failure、bindinggame強持有，失敗closepair保留recovery；無cleanresumeoldBattle。歷史無departurebinding保留context-only；peerfinal/savepending仍可接受owncontext。無resume/consumeAPI，非WORLDreturn/remoteTCPepoch/nativeACK。

同伴source inventory確認saved30/31/34與restoration/prefix/privatelineage無39currentHP/maxHP，WorldDisplay只71/72；2Bonlyproducer為isolateddiagnostic，39literal為retiredfixture，playerresources不能替代。重用293原生39/2Bconsumer證據，0newdisassembly/opcode；須actualselectedrow/revision/roster/build/origin/normalepoch+full39/equivalentsupplier和issuanceorder，39沒有subjectkey。boundedinventory非全域不存在證明。

既有C++3改／新增0，限定terminalinputbarrier sourcebranch1；mixed275→276／CUSTOM128→129／groups26不變，新opcode0／完整雙向route0。TW C2S156／worldparser74（限定50／控制11／未接13）；S2C252（230fixed／22variable）／reply48／push11／gated4／unclassified117；battle110／specialized9／86selectors7／cases6／83actions23／projection2不變。TWunhostedchains3／binding38unique34；CNchains35／binding93unique71，CN歷史C2S156／S2Cphaseopcode280／length253不同範圍。FullTW/全遊戲分母與百分比null。下步finalpairedstrandconsume、genuineeffectiveNormalInitgeneration保留originalphysicalEntry/Written、sameleasevisibility、selectedcompanionresources、durableFinishedrelease/recovery/App。Webv86peer報告source/CI/容量僅metadata，無newACK/聯合驗收/rootpeerexecution/current容量測量；保留frozenaccounts/saves/auth/chat/IME/fonts/conversion/nativeEXEs/CN/web/NativeParty。PHASE1無build/compiler/tests/runtime/native/VM/emulator/codec/gameDBSQL/migrate/activate/deploy。


## 第295輪：雙方實際終局接受到返場世代預配置

CUSTOM0132 接實際 Session ready 回調接受／current 重核／accepted stamp 後的 private 通知，由同一 Publication TerminalFlight 等兩方真正 accepted receipts，接 existing saved player ledger 只讀 guard（runtime checkpoint、完整 after resources/readset／兩方 final fullbytes/submitted/memberlocks）再預配置並私有保留兩方 return generation。補上 driver Terminal rows 空時可能 Idle 停表、不能假設還有下一次輸入的實際觸發缺口。Normal Data 新 effective_battle 與原 physical Entry/Written 分開，保留原2A而不偽造新Written；prebattle+2 overflow guard。原 prebattle worlddelivery pointer 私有捕獲並核對，未來 identity 使用原 namespace，不借PK peer worldgen/common leasegen。缺原identity歷史binding不獲返場權限。無liveData/state/gen/identity發布、inputresume、visibilitymarker刪除、unlock或App，原5sdeadline仍在。

Native primary9完整functions3504B1062sites，S30/S31指定UIchildren無直接同伴2C/30來源，4A9070完整leaf讀的是玩家MP與skillWORD42。另獨立resource-owner supplement閉合468120 fullreset+497FE0 fullchild，freshnormalreset返回時16×3EC rows包含2C/30確定0；10selectedspans668B172sites與原PE比對。這是freshnormal epoch，不能冒稱PK當前HP/maxHP0；重用251caller/alias不算全新全球覆蓋。其後issuedrecords/selection/opaquechildren仍開。原native seal及後續supplement分開保存。

既有C++6改／新增0，限定pairedreturngenerationpreparation sourcebranch1；mixed276→277／CUSTOM129→130／groups26不變，新opcode0／完整雙向route0。TW C2S156／worldparser74（限定50／控制11／未接13）；S2C252（230fixed／22variable）／reply48／push11／gated4／unclassified117；battle110／specialized9／86selectors7／cases6／83actions23／projection2不變。TWunhostedchains3／bindings38unique34；CNchains35／bindings93unique71；CN歷史C2S156／S2Cphaseopcode280／length253不同範圍。本輪CN來源增量0。FullTW/全遊戲分母與百分比null。下步paired finalstrandconsume、sameleasevisibility、selectedcompanioncurrentresources、durableFinishedrelease/recovery/App；來源預配置不等於完整返場。Webv70..87仍peer metadata未新ACK／聯合驗收；保留frozenaccounts/saves/auth/chat/IME/fonts/conversion/nativeEXEs/CN/web/NativeParty。PHASE1無build/compiler/tests/runtime/native/VM/emulator/codec/gameDBSQL/migrate/activate/deploy。


## 第296輪：雙方返場完整可見資料的條件式私有預配置

CUSTOM0133 從同一DB factory→Backend→Driver→LuaOwner→Publication接可選ReturnSceneSource，在實際第二方accepted callback及295 private preparations後取得雙方完整current incoming/outgoing名單。全6F81B／5E13B／735B、12bit handle／pose／state、資源與三段native文字／receiver profile／完整selection readset均由真正source提供；mutual directed edge按兩份相應名單一致去重，衝突拒絕，預配置mapnodes與records，含既有models總計每receiver128上限。callback重入poison、完整registry/current/savedpose／savedledger／contexts／兩方preparations核對。普通departed guards不改，common_name_source不支援則明確拒絕。未配置source保持295；配置後缺資料失敗，不能空集合／舊edges／DA8／全ready人口補洞。真正production full6F issuer仍缺，故只計條件式source preparation一支；無modelmerge／send／liveData／WORLD／identity／marker刪除／readresume／unlock／App。

定點native確認原生world6F/73與entry／return使用同一Main+15383410 manager；mode0入戰清理資源，mode1返場清理128×268 rows並釋放identity。舊world6F pool不能當返場保留物件；這不是全原生outcome、nativeACK、資源載入成功或原始visibility policy證明。17selectedspans3881B1189sites+44dataB，重用292證據不冒稱全新coverage。另同伴UIchild15完整functions2732B796sites+68dataB：4AF110傳6B UIbinding/slot、4A9110讀selectedrow技能定義、4AF4E0處理skillWORD42文字、4ABFC0視窗選擇；沒有新的HP/maxHP source，genericUI/CRT/globalalias開放。outermode1 tupletype=-1跳過4AF110，wholebody cleararm不冒稱此caller可達。

既有C++8改／新增0，條件式private visibility preparation1；mixed277→278／CUSTOM130→131／groups26不變，新opcode0／完整雙向route0。TW C2S156／worldparser74（限定50／控制11／未接13）；S2C252（230fixed／22variable）／reply48／push11／gated4／unclassified117；battle110／specialized9／86selectors7／cases6／83actions23／projection2不變。TWunhostedchains3／bindings38unique34；CNchains35／bindings93unique71；CN歷史C2S156／S2Cphaseopcode280／length253不同單位。本輪CN增量0。TW／全遊戲分母與百分比null。989capturedsrc為rawbytes完整性；只claim本輪實際delta及限定owner/reviewer reads，未claim989全人工審閱。Webv70..88仍peer metadata未新增ACK／聯合驗收／root執行。下步actualfull6Fissuer／pairedfinalstrandconsume／visibilitypublicationcompletion／selectedcompanioncurrentresources／durableFinishedrelease/recovery／App。PHASE1無build/compiler/tests/runtime/native/VM/emulator/codec/gameDBSQL/migrate/activate/deploy。


## 第297輪：返場使用真正共用存檔姓名來源

CUSTOM0134 接實際secondaccepted→296私有pairedreturnplan→現有同Presence SharedNativeActorNameSource.project/current，讀真正common profile/name_codepage與canonical qualification.receiver_text，保留D8/DA selector及CP950/936嚴格邊界、原Unicode不截斷不補名。只更改完整6F29..44第一姓名欄，其他65bytes／5E／73保留，stagedmodel及所有對應ordered incoming/outgoing複本一致更新，mutualedge同owner/qualification/profile一致去重。精確privatepair／endpoint守門、持續重入poison、retainedexactname不默默刷新，所有name/resource/text/pose callback之後fullsceneCurrent與finalpurefence。普通departed/name wrapper及原NameSource行為不改。

稽核39members／31fullrawinputs明確限讀範圍：Application診斷模板fullspawn不能提升正式來源，21B71/72DB不是6F，2A/DA不構成81B，entered lists已move、main沒opt-in。故本輪接真正first-name來源，不冒稱完整6F/resource/text2/3/selection issuer已完成。無新的native解碼覆蓋或原生封包；無modelmerge/send/liveData/WORLD/identity/markerremove/readresume/unlock/App。

既有C++2改／新增0；限定commonstoredreturnnamebranch1，mixed278→279／CUSTOM131→132／groups26不變，新opcode0／完整雙向route0。TW C2S156／worldparser74（限定50／控制11／未接13）；S2C252（230fixed／22variable）／reply48／push11／gated4／unclassified117；battle110／specialized9／86selectors7／cases6／83actions23／projection2不變。TWunhostedchains3／bindings38unique34；CNchains35／bindings93unique71；CN歷史C2S156／S2Cphaseopcode280／length253不同單位，本輪CN增量0。TW與全遊戲分母／百分比null。989capturedsrc是byteintegrity，不是989人工審閱。Webv70..90仍peer metadata未新ACK／聯合驗收／root執行。下步完整current定向actor/resource/alltext/selectionissuer、pairedfinalconsume/outputcompletion、同伴currentHP/maxHP authority、durableFinishedrelease/recovery、App。PHASE1無build/compiler/tests/runtime/native/VM/emulator/codec/gameDBSQL/migrate/activate/deploy。


## 第298輪：完整6F欄位與當前來源生命週期

本輪限定靜態原生恢復：9選取code spans3857B／1286sites，其中完整6F與insert重用292／296；新選取7下游函式1822B／628sites。原始PE與所選mapped bytes相等，不宣稱全image等價。恢復packedfirstDWORD全部位元切片／secondDWORD旗標及status、actor+220 exactcopy；bit15反相經actualID lookup到姓名顏色分支，status12／13影響外觀palette／顯示。這是呈現依賴，非PK／權限規則。DWORD9、secondDWORD低5bits、DWORD17的真正來源／同actor下游及第三文字語義仍OPEN，不補零、不拿配點WORD／guildname代替。wholetext+220搜尋只作lead定位，Main/local同偏移排除，無globalabsence宣稱。

具體來源稽核找到entry writer與move/equipment不同mutationlineage：position commit及DA收據不更新原2A，Session immutableoriginalEntry＋effectivebattle只證owner/generation。OwnedTaiwanPkAppearanceSource167..195仍要求originalentry與lease座標一致，現有來源有stationaryentry限制；不放寬guard冒充完整currentmodel。下步完整issuer須聯結currentposition、jointcurrentequipment、全部opaque/text/resource與directedaudience實際來源，不再加unfedcallback。

既有C++0改／新增0；新sourcebranch0／opcode0／完整雙向route0；mixed279／CUSTOM132／groups26不變。TW C2S156／worldparser74（limited50／control11／unconnected13），S2C252（fixed230／variable22）／reply48／push11／gated4／unclassified117；battle110／specialized9，86selectors7／cases6，83actions23／projection2不變。TWunhostedchains3／bindings38unique34；CNchains35／bindings93unique71，CN歷史C2S156／S2Cphaseopcode280／length253不同scope；本輪CN增量0。完整遊戲分母／TW與全遊戲百分比null。989sourcebytecapture不等於989人工審閱。新native/source evidence各自seal與boundedreadscope，凍結功能及CN/web保留。無build/compiler/tests/runtime/nativeexecution/VM/emulator/codec/gameDBSQL/migrate/activate/deploy。


## 第299輪：返場真正共用第二文字來源與第三文字上游

CUSTOM0135由既有sameDB PK backend factory自建privateowner，注入configuredreturnscene，actualsecondaccepted→Driver/Lua/Publication→privatepairedplan讀SqliteRoleTextRepository真完整row／revision；缺row拒絕、savedempty不同，opaqueidentity防owner位址ABA、caughtreentry永久poison、sameconnectionDML計數守門。依原packetbit25sourcepage嚴格投影，actualreceiverD8DA與wirepage一致，沿用nativepeerconversion容量檢查。只改6F45..60，其他65bytes不改；canonical／staged及全部orderedcopies一致。所有scene/name/profile/pose callback後再onefinalallrowreadonlysnapshot，再purefence；普通roletext/chat/name及CUSTOM0056不改。沒有genericrowcallback／假空字串／新schema／send／modelmerge／WORLD／unlock／App。

Native7選取spans930B／286sites＋8tableB，原PE與selectedmapped相等；實際world2D→469E49把logical+1寫Main153968D2＝savedaggregate1539683C＋0x96，經4E7180及conditional509F80；465427→500180的actualsavedaggregatearg與boundedthirdsetter對應remote6F61。500180只限定prefix、exploratory失準截斷保留排除，不宣稱wholeclient或原服guildstorage。既有CUSTOM0075 membership/name成為具體下一來源，第三欄尚未接、不默填空。

既有C++3改／新增header1；限定storedsecondaryreturnbranch1，mixed279→280／CUSTOM132→133／groups26不變；opcode0／完整雙向route0。TW C2S156／worldparser74（limited50／control11／unconnected13），S2C252（fixed230／variable22）／reply48／push11／gated4／unclassified117；battle110／specialized9，86selectors7／cases6，83actions23／projection2不變。TWunhostedchains3／bindings38unique34；CNchains35／bindings93unique71，CN歷史C2S156／S2Cphaseopcode280／length253不同scope；CN增量0。完整分母／TW與全遊戲百分比null。989beforecapture只byteintegrity，986舊src未改；bounded source/native/implementation/review分別seal。Webv91僅peerreportedmetadata，無新ACK／共同驗收／rootclient執行。完整currentactor/opaque/resources/thirdtext/selection／pairedfinalconsume/output／同伴HP／durableFinishedrelease/recovery／skills/rewards／shared64／App仍缺。無build/compiler/tests/runtime/nativeexecution/VM/emulator/codec/gameDBSQL/migrate/activate/deploy。


## 第300輪：返場真正共用公會第三文字與聯合最終讀取

CUSTOM0136由sameDB PK backend factory注入actualSqliteGuildRepository，沿原secondaccepted→Driver/Lua/Publication→privatepairedplan消費。wholeStoredRoleText＋optionalwholeGuild{id,nameUTF8,guildrevision,memberrevision}＋actualmain globalMAXguildclock在同一snapshot保留；invalidowner/schema/provenance/readerror拒絕，只有confirmednonmembership可空。clock保留可信guildwriters的join/leaveABA，不宣稱arbitrarymanualSQL；dynamiccharacterdelete另由owner/lease拒絕。opaqueidentity/thread/reentry/operationDML與main/TEMP守門保留。依原bit25sourcepage嚴格roundtrip及actualD8DA receiver/nativeconversion容量，只改第三61..76，與secondary合計45..76，其他49B不改；canonical/staged及allorderedcopies一致。普通guild/chat/name/roletext不變。

獨立review R300-01找到actualPublication在Visibilityfinalsnapshot後仍讀terminalresources／兩份context SQL；已修為那些reads後再stored-onlyjointcut，同persistentVisibilityguard且不重播scene/name/profile/presencecallbacks，之後只有purepair/Session/registryfences。舊299及reviewcandidate1歷史保留，不冒稱原本已閉合。新native四選取spans1398B／428sites＋134tableB釘定三字串sharedsourcepage、thirdcopy及mode3structuralgate；2D/localsetter重用299。舊0075raw缺失明記，新currentpinnedbytes自行支持結構，沒有原服storage/economics/nativefullroute宣稱。

既有C++6改／新增0；限定guildthirdreturnbranch1，mixed280→281／CUSTOM133→134／groups26不變；opcode0／完整雙向route0。TW C2S156／worldparser74（limited50／control11／unconnected13），S2C252（fixed230／variable22）／reply48／push11／gated4／unclassified117；battle110／specialized9，86selectors7／cases6，83actions23／projection2不變。TWunhostedchains3／bindings38unique34；CNchains35／bindings93unique71，CN歷史C2S156／S2Cphaseopcode280／length253不同scope；CN增量0。完整分母／TW與全遊戲百分比null。990beforecapture只byteintegrity、984src未改；native/implementation/review各seal與boundedreadscope。Webv92僅peerreportedmetadata，無新ACK／共同驗收／rootclient執行。完整currentactor/opaque/resources/selection／pairedfinalconsume/output／同伴HP／durableFinishedrelease/recovery／skills/rewards／shared64／App仍缺。無build/compiler/tests/runtime/nativeexecution/VM/emulator/codec/gameDBSQL/migrate/activate/deploy。


## 第301輪：當前角色來源更正與原生替換生命週期

更正298／300的stationary-only判讀：Lease.position與storedfull2A保留原acceptedentry lineage，actualsaved_position另與currentjointequipment／Pair.peer.position核對。既有CUSTOM0095 configuredcustodymovement已在單TX更新位置與equipmentwitness位置／revision／provenance、保留completeinventory及1215nativebytes，PKprep重新observe_committed；不是角色不能移動。非custody造成staleequipment仍拒絕，original2A／sameDB／currenttuple／identity／CUSTOM0105guards不放寬。歷史sealed紀錄保留，此輪明確supersede錯誤判讀，沒有虛增新sourcebranch。

原生full6F實際4699F1→4FB460查128slot／stride268；既有slot進4FC560後仍傳newfullbody進4FC1C0，ID=-1只在poolflag13418==1，selectedremove無directactor220但opaquechildren未閉合。poolzero不構成logical17權威；newbody+10→actor220仍opaque；selfMain220是449330輸出的座標，排除同offset誤配。6Fbits12..13／actor260與self2Abits14..15走同type3顯示，但actual36會改selfrole4694、selectedremote36／37保留marker。6Fbits21..24／actor7A由36／37延後type0消費，self2Abits3..7是5bit而remote4bit，signedWORD>9clamp9，畫面相同不能推原值相同或截位。worldtable1024Bcapture尾端含padding／code，僅36／37entry具本輪consumer證明，非256validtargets／完整extent。

三worker分別完整closure及boundedreadscope；native22011spans2234B／707sites（8newselections1245B／389sites），prefix9spans6238B／2017sites（vs298新7／4711B／1500sites，舊2；另1084dataB）。包含歷史2A／跨包overlap，不合計全域新增coverage。logicalDWORD9／17原始語義與producer、secondDWORDlow5、currentpackedstate／resources／directedaudience／actualApp仍OPEN。C++0改／0新增，sourcebranch0／opcode0／fullroute0，mixed281／CUSTOM134／groups26不變。TW C2S156／worldparser74=limited50/control11/unconnected13，S2C252=fixed230/variable22，reply48/push11/gated4/unclassified117，battle110/specialized9，86selectors7/cases6，83actions23/projections2；TWunhostedchains3/bindings38unique34，CNchains35/bindings93unique71、歷史C2S156/S2Cphaseopcode280/length253不同scope，CN增量0。完整分母／TW與全遊戲百分比null。990src byteunchanged，不冒稱全手讀；無build/compiler/tests/runtime/native/VM/emulator/codec/gameDBSQL/migrate/activate/deploy。Webv93僅peerreported來源交接，無新ACK／共同驗收／rootclient執行。


## 第302輪：返場真正共用current endpoint根資料／位置最終來源

CUSTOM0137在actualsameDB PKbackendfactory注入真正recoveredcharacters與exactPresence，沿既有configuredreturn→privatepairedplan消費；先seed雙participants即使emptyactors，再canonicaldedup所有actor source／recipient端點，lease／完整pose／Session／battle一致才可重用。私有EndpointObservation保留owneridentity／lease／七欄root／完整currentpositionrevision；actuallist_for_account證明account及root，load_position證明owner及pose，currentpose不與oldLease.position混淆。Presence觀察者在SQL外，之後再wholeendpointread；retained不refresh舊receipt。text／guild／epoch／allroots／poses在ONE finalsnapshot核對，actualPublication terminalresources＋兩contextSQL之後既有storedonlycut也一起核對；其後僅pureRegistry／Session／pair。six actualmain tables／TEMPshadow／thread／reentry／operationDML guards保留，缺root／pose拒絕。root無native獨立revision，不宣稱arbitraryexternalSQLABA；無credentialsnapshot／nativefull6F投影／第二HPMP結算／wire改動。

新nativealias追到actor1EC／224 constructor、actual4FCFD0→50DCC0／4FFAD0／4FF9C0兩組位置資源、4FC618→4FFCF0四handle retirement；4FC130只收logical21appearance，不是DWORD9／17。原nativecandidate1 XORmask文字方向錯誤已保留sealed歷史，correctedcandidate2：非override分支保留oldlow5、寫rawhigh3，status0x10 override跳assignment。corrected15spans1707B／581sites（vsreferenced301/298新13選1599B／552sites，舊108B／29sites），不是全歷史新增coverage。DWORD9／17原始權威仍OPEN，不零填／舊slot／座標代換。

既有C++5改／新增0；限定commoncurrentendpointsourcebranch1，mixed281→282／CUSTOM134→135／groups26不變，opcode0／fullroute0。TW C2S156／worldparser74=limited50/control11/unconnected13，S2C252=fixed230/variable22，reply48/push11/gated4/unclassified117，battle110/specialized9，86selectors7/cases6，83actions23/projections2；TWunhostedchains3/bindings38unique34，CNchains35/bindings93unique71、歷史C2S156/S2Cphaseopcode280/length253不同scope，CN增量0。完整分母／TW與全遊戲百分比null。990src beforebytecapture／985不變，boundedmanualreview分開。fullactor／currentmarker／resources／directedscene／pairedfinalconsume/output／normalpublication/markerretire／durableFinishedrecovery／skills/rewards／companionHP／shared64／actualApp仍缺，TW/CN/web與凍結功能保留。無build/compiler/tests/runtime/native/VM/emulator/codec/gameDBSQL/migrate/activate/deploy。


## 第303輪：返場輸出實際收件者與原生世界接收生命週期

實際第二個terminal accepted callback只retain未publish的prebattle+2 normal generation與private visibility；return incoming[i]按返場recipient、outgoing[i]按返場source，不能把outgoing當同一Session的第二批。mutual directed edge在輸入兩處出現但canonical model一次；共同surviving observer可能跨兩份outgoing，仍缺按actualrecipient分組的joint order／strand queue reservation。普通acceptance僅入列，common held publication僅local release，observed fullwrite需exactrecipient callbackTLS；皆不能直接當return完成。terminal5s自strand prepare起算、accepted不rearm，Ready拒絕新output；需要distinct private ReturnHold與one-use pairedconsume，早切normal state會使舊PK proof失效。durableFinished／memberlocks／已存資源仍保留，retained restore不等於跨程序Session重建。

原生468AE0使用networkowner+2CC4固定buffer，413670只清+2CC0 count、commonjoin隨即413420重填；殘留DWORD9不是角色權威。外層stack scratch非packet pointer；415AF0／415B20→412CF0原PE為xor eax,eax;ret，排除該observer候選但不推全域無alias。82消費後可先poll下一筆再return而未dispatch；413420非零count fastpath與upstream framing／decrypt仍未資格確認，519370下一phase reachability也未證。實際466E47→4FB290在467154→468AE0之前，新增4FB0D0更新local WORD pose+74/+76再接302資源定位；cached context讀取arg2=0，465FA0的20entry／80B是local context dispatch不是opcode／ACK。opaquecontroller／resources／original DWORD9／17 producer仍open，無zero／stalecache代替。

三worker獨立有界scope／完整byteclosure。nativebuffer20spans2061B／632sites，vs302選18／2005B／616sites、舊6F overlap2／56B／16sites，另8dataB；明示20260919/20歷史overlap非全域新增。nativereturn11spans2758B／891sites，vsreferenced289/290/295選9／2405B／790sites、290overlap2／353B／101sites，另80dataB。currentoutput16完整input／524002B不冒稱全手讀。990src byteunchanged；C++0改／0新增，sourcebranch0／opcode0／完整路徑0，mixed282／CUSTOM135／groups26不變。TW C2S156／worldparser74=limited50/control11/unconnected13，S2C252=fixed230/variable22，reply48/push11/gated4/unclassified117，battle110/specialized9，86selectors7/cases6，83actions23/projections2；TWunhostedchains3/bindings38unique34，CNchains35/bindings93unique71，CN歷史C2S156/S2Cphaseopcode280/length253不同scope，CN增量0。完整分母／TW與全遊戲百分比null。無build/compiler/tests/runtime/native/VM/emulator/codec/gameDBSQL/migrate/activate/deploy。下一來源為full6F當前issuer／scene與Apphost，加actualrecipient ReturnHold／pairednormalpublication／outputcompletion／markerretirement／inputresume／durableFinished recovery，原雙版／web／shared64範圍持續。


## 第304輪：實際82後續phase／6F消費與當前完整角色來源缺口

原生82→result4→outer index4/46565B→515770；先條件呼叫519370，返回後才465BC0及outer3。phase+10來自input root+438，outer+624是output scratch非packet；與world+A7E05E0 alias、phase+A9DF6BC gate producer及opaque children custody仍open。secondary6F actual selector62→5198A1只consume(2)/poll(2)，不是6F body parser。此82鏈與forward entry/staging相容，不是terminal returnACK／victory／resumed WORLD readiness；舊normal WORLD return3仍依原資格。新graphic children actor61→508980/5087B0/50ADC0及59BAA8/59BAAC資源表、actor48→4FC6A0/509DF0/509CC0 mode/name刷新，未解actor220／DWORD17原義，不當server技能或結算規則。

actual DA15 source/commit authority存在，但Visibility存last_taiwan_appearance不改native.spawn，advance僅coords；current DA opaque15B/oddhigh3與olderFields copy8不能當最新full6F merge規則。host entered／PK ReturnSceneSource仍外部fullscene source；singlejoining supplied order非兩個returner共同observer joint order。world_display DB僅21B NPC/monster不是81B player6F；App diagnostic caches/entry2A/lastDA不能補未知DWORD9/17/currentpacked/resource authority。不加沒有actual issuer的外部orderedlist／batch容器，不改frozen來源。

nativephase17限定spans2075B/586sites，vsqualified303新選15/2022B/570sites，明示overlap53B/16sites，data13B；closure131/7140243B。nativeactor14spans2275B/762sites，新child6/793B/268sites，歴史overlap8/1482B/494sites，data44B；closure129/7048736B。recipient source36完整captured inputs/1214516B，closure43/1259670B；bounded searches及failedlookups/truncation均保留，不冒稱全域absence/novelty或完整手讀990src。

990src byteunchanged，C++0改/0新增，sourcebranch0/opcode0/fullroute0；mixed282/CUSTOM135/groups26/pending10不變。TW C2S156/worldparser74=limited50/control11/unconnected13，S2C252=fixed230/variable22，reply48/push11/gated4/unclassified117/nondefault206/default46，battle110/specialized9，86selectors7/cases6，83actions23/projections2/outside21；TW unhostedchains3/bindings38unique34，CN chains35/bindings93unique71，CN歷史C2S156/S2Cphaseopcode280/length253各自scope，CN增量0。完整遊戲封包數/已完整串接路徑/分母/TW與全遊戲百分比null。無build/compiler/tests/runtime/native/VM/emulator/codec/gameDBSQL/migrate/activate/deploy。下一來源為精確owner alias/gate/child custody及current full6F issuer，再接actual Apphost/ReturnHold/fullwrite/normal publication/terminal marker retirement/inputresume/durableFinished recovery；shared64/CN/web保留。


## 第305輪：初始化owner來源、89佇列與C2S36實際輸入缺口

Actual world464910 saves firstarg root and root+438; outer4655E0 passes the same root to5112C0 which rereads root+438 into phase+10. Shared initialization provenance is closed; later owner replacement/opaque-child equality remains conditional.

Actual gate0 producer5117F8 and secondary89 queue51D4E0 are qualified. Caller ignores capacity/append failure.5140C0 consumes89 only with active gate, pending head, phase+A9DF6C4 zero and second output pointee zero;518BF0/parent set gate1. Separate helper/mode5 conditions exit; not native ACK/immediate result1.

Exact4116F0 worker+14 sendowner,411690 timestamp/count under+6C lock, conditional+3C send lock; formatter uses embeddedobject+10 output distinct from receive+C10 and parsedowner+2CC4. Compression stub0 and optional transform qualified; original/mapped IAT separately pinned. No global concurrency/custody stability claim.

Actual actor+224 resource subobject has owner at+24C from pool+4; adjacent opaque+220 is separate. Four stride6 resource slots/Actionrecord owner+10+handle*290 have bounded readsets, not whole-actor/skill/server authority.

Concrete actual C2S36 TimerNotification private route rejects before durable operation and Driver closes exact paired Sessions retaining durable state. Default-off diagnostic fixture path is not formal PK authority. Original timer purpose/timing must be recovered before genuine consumer, not ignored/noop acceptance.

原生記憶體offset均依原證據hex；resource actor+0x224/0x24C不同於opaque+0x220，完整81B及logical byte9/17保持未知權威。原候選19/2282B/694sites owner（2錯位slice已撤回資格，改採corrected successor）、16/730B/274sites custody、9/1477B/507sites resource均為限定區段；明示歷史overlap，非全域新增或已接通遊戲。source-obligation16完整captured inputs/979768B。完整worker封存與metric pins見本輪research doc及外部archive。

990src byteunchanged；C++0/sourcebranch0/opcode0/fullroute0；mixed282/CUSTOM135/groups26/pending10。TW C2S candidate156/worldparser74=limited50/control11/unconnected13，S2C252=fixed230/variable22，reply48/push11/gated4/unclassified117/nondefault206/default46；battle110/specialized9，86selectors7/cases6，83actions23/projections2/outside21。TW unhostedchains3/bindings38unique34，CN chains35/bindings93unique71；CN歷史C2S156/S2C phaseopcode280/length253各自scope，CN增量0。全遊戲封包數/完整路徑/分母/TW與全遊戲百分比null。未build/compiler/tests/runtime/native/VM/emulator/codec/gameDBSQL/migrate/activate/deploy。shared64/帳號存檔/native fonts/CN/web與其他凍結功能保留。

下一來源：Trace root+438 binding/replacement and reached postreset/prereceive children; native C2S36 producer caller/lifecycle/control purpose, then actual private PK input; full current6F issuer before actual App backend/paired ReturnHold/fullwrite/normal publication.

Independent static review rejected two original owner slices starting midinstruction (511797 and515858). Original seal/candidate1 retained immutable; corrected successor requalifies boundaries and replaces effective owner metrics, without new source/opcode/fullroute credit.
有效owner metrics: {"qualified_spans": 19, "bytes": 2284, "sites": 692, "new_selected_spans_vs_qualified304": 15, "new_bytes": 2063, "new_sites": 627, "explicit_overlap_bytes": 221, "overlap_sites": 65, "data_slices": 5, "data_bytes": 26, "global_new_coverage_claim": false, "raw_seal_sha256": "72ca8138af90af6a551f74a2238fd753f343331b63bea96a56228ce289cb3437", "canonical_closure_sha256": "0e5f43aa9ae76d4d2da40369b542b4710ec7806a52ea00a4224be960c2a4d53a", "closure_members": 92, "closure_bytes": 619272}


## 第306輪：原生36 producer生命週期與具體globalroot來源

Exact4119B0 owner→worker14/CreateThread callback4117E0 is concrete, not successful live thread (return1 ignores creation result).411780(nonzero) sends36 immediately and updates last28 before gate1C; zero only disables36. Processing18/gate1C/unsigned elapsed≥raw10000 govern repeats; independent30 path uses primaryperiod5000. Selectedstop Sleep/deletelocks is not thread join.

Actual36 payload84 comes from82 logicalbyte1 context_a through outer scratch28; payload88 comes from outerESP18, distinct from82 context_b atESP264. Constructor does not initialize84/88. Timestamp28/opaque payload kept distinct; no server clock/ACK/room/nonce semantics inferred.

Actual globalroot5E00F8 constructor/init caller chain writesroot438 via40DD43 allocation4204→412D10→40DD87. Networkowner+40D4 worker is supplied owner through412E70→4119B0. Actualworldcallers passsame root; destructor clears438. Phase fresh read precedescalls, firsttwochildren directreadsets qualified, otherlifecycle/alias/children/concurrency remainopen.

Actual Session1758..2003 frame→gamecallback→acceptedresponse→strand resume path has no automatic Timer acceptance; nohandler allows onlymovement/Tick; PKpending rejects beforecallback; Timer interrupts continuedskill. App installs orderedworldcallback, privatePK remainsunhosted; diagnostic fixture is not controlauthority.

Current CUSTOM0111 first82 context uses checkedfutureSessiongeneration, context_b explicit1400. Native copy lineage is not originalnonce/timestamp authority. Source scope and bindingargument-list clerical corrections preserve originalsealed packages and qualifiedmetrics.

timer23spans1117B/394sites，限定4sets比較new938B/336sites/overlap179B/58sites/imports119B；binding19spans4048B/1109sites，新local3707B/overlap341B，603B boundaryproof不給newcredit。Source-routing10完整captured inputs1041999B；scope successor/arg-order successor保留original封存並更正誤植，非新sourcebranch。完整metric/pins見本輪research doc與externalarchive。

990src unchanged；C++0/sourcebranch0/opcode0/fullroute0；mixed282/CUSTOM135/groups26/pending10。TW C2S candidate156/worldparser74=limited50/control11/unconnected13；S2C252=fixed230/variable22/nondefault206/default46/reply48/push11/gated4/unclassified117；battle110/specialized9，86selectors7/cases6，83actions23/projections2/outside21。TW unhostedchains3/bindings38unique34；CN chains35/bindings93unique71，CN歷史C2S156/S2C phaseopcode280/length253各自scope，CN增量0。全遊戲封包數/完整雙向路徑/分母/TW與全遊戲百分比null。無build/compiler/tests/runtime/native/VM/emulator/codec/gameDBSQL/migrate/activate/deploy。shared64/CN/web/nativefonts/帳號存檔/其他凍結功能保留。

下一來源：Qualify actual outerESP18 writer and reached36 enable/disable caller lifecycle; originalserver36 controlpurpose/phase before privateconsumer; continue root/phase opaquechildcustody and originalcurrent6F issuer before actualApphost/pairedReturnHold/fullwrites/normalpublication.


## 第307輪：36 physical-local來源與82 packedcontext實際consumer

Actual4655E0 U=entryESP-A24 makesworker88 sourceU18=entryESP-A0C local. EarlyliteralESP18 isU20, output18 isU250, ctx_bU264. Exactselector3/result4 tables and receiveractual547B50 stackprobe establishoutputU238 provenance. Producerstillopen, no nativegarbage/uninitialised/ctx_b/clock/ACK semantics.

ActualouterinitialwriterU20=scratchU238 andstructU1C establishinput+4slot; conditionalonpointercurrentacrossopaquechildren,82ctx_a/ctx_b scratch28/2C reachesphase3C/40/currentblock; ctx_a also feedsconditionalnative resource selection and initialC2S35body8 storage. Full518E50 target quotient14 maskloop can overwritecontext lowWORD for targets>=28. Initialcopy is notguaranteed eventualecho ororiginalserverauthority.

Ctx_b lowbyteFF selectsphaseflag/selected180000tick timeoutskip; bits8..15 zeroextendinitialcountdown, selectedtickelapsed/1000 subtraction anddecimaldigits. Literal1400 yields20 inthatbyte, but originalserverdefault/turnauthority/spectatorwholebehaviourremainunproven.

Actualworld/guildnotification predicates do notgrantTimerpayload/room/writeauthority. FullWorldService rejectsTimer beforebattlecallback ormovelesssuccess; privateOutbox unsupportedTimer isclassifiedbeforedurablemutation. ExistingdiagnosticTimeracceptance isnotauthoritative originalgameplay. ActualAppworldcallback/privatepolicy remainseparate.

PrivateCUSTOM0111 checkedSessiongenerationand1400 source pluscommandcontext policy exactentry/revision/grant/profilechecks stayexplicitlyprivate. No sourcepromotion guessedfromnativecopies; preciseaddress/fielduseschangesnexttrace while allcompletegameplaymetricsremainunknown.

Native限定metrics與四worker完整closure pins見本輪research capsule及externalarchive，不合計全域coverage。Source-routing9完整inputs838744B；source-command3完整inputs73352B，manualscope分開。990src unchanged；C++0/sourcebranch0/opcode0/fullroute0；mixed282/CUSTOM135/groups26/pending10。TW C2S candidate156/worldparser74=limited50/control11/unconnected13；S2C252=fixed230/variable22/nondefault206/default46/reply48/push11/gated4/unclassified117；battle110/specialized9，86selectors7/cases6，83actions23/projections2/outside21。TW unhostedchains3/bindings38unique34；CN chains35/bindings93unique71，CN歷史C2S156/S2C phaseopcode280/length253各自scope，CN增量0。全遊戲封包數/完整雙向路徑/分母/TW與全遊戲百分比null。無build/compiler/tests/runtime/native/VM/emulator/codec/gameDBSQL/migrate/activate/deploy。shared64/CN/web/nativefonts/帳號存檔/其他凍結功能保留。

下一來源：Trace actualreceiver467860/466B00/468AE0 message/callback outputaliases thatcanreachphysicalU18 (negative220 fromoutputU238), andlater5112C0 structnegative4 users; continue current81Bissuer andqualified82contextpolicy beforeactualApp/Timerowner promotion.


## 第308輪：actual message與full81B opaque來源邊界

ActualPeekMessage pointerV20 proven by stackrebasing; rawV28/V2C pushorder reaches465F30 formalarg2 descriptor. Descriptor opcode/length/payload goes toactual4132E0 owner36C8 append, notexplicitU18/outU238. No typedmessage swap/guessed semantics.

Newcomplete465F30/55AD35/55AC24 exposesconditionalatomicheaderP-C writer withlocalM-10 pointercell; P-C=U18 requiresP=U24, actualsetterstillopen. HistoricalP/guard equalityskip doesnotprove currentglobals orno writer. ActualregisteredDispatchcallback/rawdescriptor/globalP setter remainconcrete nextcuts.

12 actualreachedcomplete remote/actor1EC/actor224 callees qualifybase and graphics/coordinate/flaghandle fields. Nested34=actor220 adjacency notread/wholecopyproof; resourceowner28=actor24C. Originalbody8/logical9 andbody10/logical17 issuerstillopen; shifted4FC800 explorationexcluded.

Full81B rawpass-through andactualshared name29..44/secondaryguild45..76 projection guards preserveopaque9/17; commonroot/pose/currenttext andfullrecordcomparison do notsupply originalfullscene/materialissuer. Sharedfactory still invokesexternalcomplete resolver; actualprivatepairedretention isnotworldpublication orApphosting.

Original123member nativeopaque seal omitted3nestedhistoricalseals; immutable128member successor includesexactclones/originalseal/succession andwithdrawsfullclosureclaim. Rooteffective correction actualheader153/namecpp140lines preservessealedsourcepackage; failures notabsence. Native/source increments0, goalactive.

Native限定metrics與完整修正版closure見本輪research capsule；source-custody9完整inputs280577B。990src unchanged；C++0/sourcebranch0/opcode0/fullroute0；mixed282/CUSTOM135/groups26/pending10。TW C2S candidate156/worldparser74=limited50/control11/unconnected13；S2C252=fixed230/variable22/nondefault206/default46/reply48/push11/gated4/unclassified117；battle110/specialized9，86selectors7/cases6，83actions23/projections2/outside21。TW unhostedchains3/bindings38unique34；CN chains35/bindings93unique71；CN歷史C2S156/S2C phaseopcode280/length253各自scope，CN增量0。全遊戲封包數/完整双向路徑/分母/TW與全遊戲百分比null。無build/compiler/tests/runtime/native/VM/emulator/codec/gameDBSQL/migrate/activate/deploy。shared64/CN/web/nativefonts/帳號存檔/其他凍結功能保留。

下一來源：Trace actualregistered nativeDispatch windowprocedure and rawV28 descriptor/global5A0B60 setter forphysicalU18; obtain truecaller of4FC6E0 or otheractor/bodypointer indirectchild seekingoriginalopaque9/17 supplier, notzero/cache/unfedcallbacks.


## 第309輪：registered callback／remote pool owner與world source缺口

Actualstartup531ECA→532070 registersliteral532360 atclassarg+4; sameclass59E024 CreateWindowreturn6F4CA0. Complete532360→root5E00F8/40E3B0 qualifies4A selector→40E557→40E2E0. CurrentMSGwindowmatch/lateroverride/OSsuccessnotproven; originalregisteredcallbackrecoveredstatically.

Newrootbridge descriptorformalarg2 israwV2C, not308preDispatchV28. Complete547B80 count1 provesoneBYTE percopyiteration; stableL localbase..base+L-1, D4reread andnouper400boundselected. CurrentL/descriptorlifetime/OSstackdepth unknown; no actualoverflow/U18supplier. NewlocalcleanupstillusesopaqueglobalP.

Actualmsg403predicate throughnon-nullroot440 Main→467DF0→Main15383410→4FC6E0 qualifieschangedDWORDflag128slotsstride268 toknown4FC720 andpool1341Cstore, equalflagreturns. Former308exploratoryloopnowhasactualcaller/base, notgloballyfreshbytes. Adjunct256recordsstride1D8/lowBYTEflag separate; no remoteopaque9/17issuer.

Concrete403producer nextcut4828D2→4F4B50 WORDselector table4F4FE4/bit2case4F4E12/403sender4F4E52, plus475D60 raw4CFsenders. Unqualifiedcaller/import/currentobject/purpose stayopen; no UI-only/skill/checkbox or networkopcode semantics inferred.

ActualD8 sharedApplication bound172B list/account/character/area/scene/nativeNPCpair/firstbag18CA logsunresolvedonly. Issuedcontext hasno coordinates/revision/placement; separatebagreads notatomicconsumption. NPCprefix4043/NPCList451rows251groups1509codes/72two retainedspawns/customfruithints do notsupply generalDaily destination/cost/reward. No unfedreader/no-op acceptance orcurrentdatagrants added.

Native限定metrics與三完整closure pins見本輪research capsule；source-world12完整inputs719981B，manualscope分列。990src unchanged；C++0/sourcebranch0/opcode0/fullroute0；mixed282/CUSTOM135/groups26/pending10。TW C2S candidate156/worldparser74=limited50/control11/unconnected13；S2C252=fixed230/variable22/nondefault206/default46/reply48/push11/gated4/unclassified117；battle110/specialized9，86selectors7/cases6，83actions23/projections2/outside21。TW unhostedchains3/bindings38unique34；CN chains35/bindings93unique71；CN歷史C2S156/S2C phaseopcode280/length253各自scope，CN增量0。全遊戲封包數/完整双向路徑/分母/TW與全遊戲百分比null。無build/compiler/tests/runtime/native/VM/emulator/codec/gameDBSQL/migrate/activate/deploy。shared64/CN/web/nativefonts/帳號存檔/其他凍結功能保留。

下一來源：Trace actualraw4A descriptor sender forregisteredclass59E024/currentwindow6F4CA0 andglobalPsetter; qualify4828D2→4F4B50 jumpcase4F4E12/403send and475D60, keepingpoolflag distinctfromfull81B opaque9/17. Recover actualdaily NPC placement/eligibility beforetransactionaloperation.


## 第310輪：IPC方向、角色旗標producer與正式世界來源

原生 S2C 接收分派的八個 GM Tools FS2 轉送早已有歷史紀錄；本輪不計新 opcode，补原始 PE 匯入身分、實際 entry／呼叫、12B stack descriptor 及同步呼叫資料生命期。GM 工具標題與 XianJieWndClass／6F4CA0 分開，這條 outgoing IPC 不替代 incoming 遊戲視窗來源；wrapper virtual 回呼的 mutation 邊界依原生包保留。

實際466B00 caller 的子物件 I=W+A7F2F6C →4820A0→4828D2→4F4B50。504620只追到output WORD=-1／BYTE=0入口，caller後續讀這些locals與返回值選擇分派，後段event來源未資格。selector10 的指定 flag 條件切換 I-relative pointer object449E bit2，產生完整 DWORD0/1並於4F4E58 SendMessageA 到global6F4CA0的403；4F4E52只是PUSH403。不同 objectbase 不混用；local403不是networkopcode。

532360 callback 傳送原始 wParam stack slot 的位址，40E854讀 slot 的scalar旗標，並非 dereference address0/1；對上309 root440 Main→467DF0→128×268池旗標呼叫。另一256×1D8 pool／AL flag分開，未提供完整6F opaque DWORD9／DWORD17或原生 Timer36 U18 供應者。

另資格既有S2C1B table46B5D4[1B]→46AE4D→4F5030，bodyWORD只直接寫subobject pointee449C..449D，不寫449E。跨opaque4F55F0/4F5670等children才重讀449E bit2，4F50D5傳local403，另4F50FA傳405；不證旗標由body供給或跨call保持。它不是鄰近82 case (82→46AE12)。網路consumer→本地通知來源已追到，仍无1B服務端issuer／玩法權威或完整雙向路徑，opcode計數不增加。

實際 main88行的run_server(config,seconds)進入無 CN/web/world plan 的overload；explicit Application 同一Context host/factory/entry/lifecycle/movement/mixed接點存在，但完整原生供應者仍external。SceneSupply資料／完整2A issuer／Current／install缺口有精確來源位置，不啟用不完整 Main 路徑。

完整WorldEntered210行及Session2422..2544追清 held frame→install／visibility→release queue→outward／ready順序；QueueReleased不是socketwrite或nativeACK。ExplicitNoInitialReply需真實source decision/current/install，不作空成功。HMD model placements與NPCList resources無已資格的NPC／Daily join，不能靠相同座標名授權目的地、費用或獎勵。

三份證據完整closure與限定metrics見本輪research capsule；source-world15完整inputs1039959B，人工閱讀scope分列。990src unchanged；C++0/sourcebranch0/opcode0/fullroute0；mixed282/CUSTOM135/groups26/pending10。TW C2S candidate156/worldparser74=limited50/control11/unconnected13；S2C252=fixed230/variable22/nondefault206/default46/reply48/push11/gated4/unclassified117；battle110/specialized9，86selectors7/cases6，83actions23/projections2/outside21。TW unhostedchains3/bindings38unique34；CN chains35/bindings93unique71；CN歷史C2S156/S2C phaseopcode280/length253各自scope，CN增量0。全遊戲封包數/完整雙向路徑/分母/TW與全遊戲百分比null。無build/compiler/tests/runtime/native/VM/emulator/codec/gameDBSQL/migrate/activate/deploy。shared64/CN/web/nativefonts/帳號存檔/其他凍結功能保留。網頁v102僅收到peerreported交接，無ACK／adoption／wireacceptance或目前容量現讀宣稱。

下一來源：沿既有S2C1B→4F5030→4F55F0/4F5670及I+86888真實constructor/lifetime追449E寫入者，保持bodyWORD與flag分開；追cleanup55B42F/5463B5及原始5A0B60/64初始化與currentwriters，不能將refcount形狀冒稱gametimer supplier。GM outgoing IPC同步descriptor/wrapper不是incoming遊戲producer；完整2A/6F issuer與Current/install具備後才選定Main factory。保持NPC model geometry／NPCList／Daily association分開。


## 第311輪：本地選項來源、2A初始化與配置生命期

實際local current pointer setter已定位：465BC0 trueentry以I=W+A7F2F6C、R=W1539683C呼叫481C20 mode0；481C81把R+90傳向4E7C80及4A7D60/4A97E0，寫I86888。因此這條current O=R+90 local aggregate alias，不是remote6F，亦不把其他mode/後續pointer lifetime視為已完成。289既有方法沿用並列重疊，無global新coverage宣稱。

在資格化的468160 nonnull-name/成功2A路徑，4681A3呼叫415690複製body36B；packet2A與原map等guard成立後，468315..326以EAX0/ECX1141清[R+90,R+4594)（末端不含），即[O,O+4504)，涵蓋449C及449E。這是local memory initializer，不是2A多一個449E wirefield，不以全0替代服務端profile或不明opaque欄位。

既有1B→4F5030直接bodyWORD寫O449C..449D。actual4F55F0/4F5670完整方法直接修改另兩個WORD44A0/44A2，以16-bit wrapping lowWORD加法後signed16 clamp0..10；selected directwrites不改449E，但opaquechildren仍可能改。完整4F5150重讀當前I86888而無直接讀formalpointer arg，子呼叫副作用未展開；local403與405的scalar來源及不同field/base保持分開，未提供server1B issuer或完整玩法規則。

配置／回收鏈追清55ABA2 live header (1,length,capacity)、55AC24→5463B5 release把首DWORD重用為free-listlink、55ABC4→546326 allocation彈回同pool後重設；55B42F→5479FF fallback有declaredHeapFree及opaqueheapbranch。5A0B60/64→74/68与header(-1,0,0)只historicalPE initializer，沒有currentglobalwriter／P=U24／physicalTimer36U18供應者。

實際source-options追到C1D全WORD種子、B1 selectors7/8→bit0200、CUSTOM0100 exact owner/current Written-entry receipt/replay及S1B普通回傳。disabled C1D仍是ready-world transport-only無state/reply；default-off與CUSTOM causal policy保留，既有ordinaryreturnedwire不當Written/ACK/原子delivery。正常entry receipt只local transcript，非remoteconstructor/commonlease/遊戲權威。

三份完整closure及限定metrics見本輪research capsule；source-options10完整inputs1029187B，人工閱讀scope另列。990src unchanged；C++0/sourcebranch0/opcode0/fullroute0；mixed282/CUSTOM135/groups26/pending10。TW C2S candidate156/worldparser74=limited50/control11/unconnected13；S2C252=fixed230/variable22/nondefault206/default46/reply48/push11/gated4/unclassified117；battle110/specialized9，86selectors7/cases6，83actions23/projections2/outside21。TW unhostedchains3/bindings38unique34；CN chains35/bindings93unique71；CN歷史C2S156/S2C phaseopcode280/length253各自scope，CN增量0。全遊戲封包數/完整雙向路徑/分母/TW與全遊戲百分比null。無build/compiler/tests/runtime/native/VM/emulator/codec/gameDBSQL/migrate/activate/deploy。shared64/CN/web/nativefonts/帳號存檔/其他凍結功能保留。網頁v103僅peerreported，無ACK/adoption/wireacceptance/rootcapacityclaim。

下一來源：沿實際468160 successful2A→R current local alias與其他初始化/後續write集合，把完整2A body欄位和local derived/defaultmemory區分；再追完整6F81B opaque9/17的實際producer/consumer。I86888其他setter與角色pool binding lifecycle分開；僅在有真正currentP=U24或相關currentglobalwriter證據時才將genericallocator延伸為Timer36供應者。保持CUSTOM0100/原生1B/C1D/B1各自來源，不啟用未完成Main sourcefactory。


## 第312輪：2A卡片resource條件與遠端actual consumer

2A變身resource的新實際caller cut把45C100資格與45C000 rowmatch及45A0A0結果分開。45C100只是lowWORD key與signextended catalog WORD bound的inclusive比較；45C000只有rowWORD0==key分支先寫selected8B local，common join仍複製local到output，BYTE3未資格。Eligibility成功不是完整record來源或任意有效resource。

實際2A caller從card-derived outputBYTE2/WORD4/WORD6供給45A0A0；leaf可返回0，而selected caller立刻解參考結果BYTE。完整issuer必須資格exact card row與target EnyName selector/非空lookup，不把ChangeDollCard增益或resource label當wild怪物能力。World場景與card target場景必須分開。

實際S2C36/37 table46B5D4→469C6B/469C09，packet+1是各自body。36 low14identity等於W1539683C時走local5038A0並bypass；只有nonself36及37所選支路CALL4FBC30。它lookup bodyWORD6&3FFF→A=P18+slot268，N=A1EC→完整50DF20/50E150。body9 conditional寫A265，body8非零conditional寫A264；直接children寫N E/10/12/14 WORD或N22 scalar，不碰N34/A220。它不是C2STimer36或full6F body8/opaque9/17。ESI完整DWORD只資格selected低BYTE來源，opaque4614A0/其他children未展；body0/1 masking非完整Afterstate。原REPORT eachcalls phrase以外部immutable effectivecorrection限定，原seal/metrics不改。

實際stored entry來源已對到Application同Database reader/writer→HostPlan→Prepare/Offer→CAS→Native/Current。完整raw frame40保持，不臆補opaque；Prepared/BeforeWrite及staged-next BeforeCommit與來源不變檢查既有。COMMIT後不重跑provider/reload/retry，後來Current可壓掉發送但不能撤銷已存快照，不宣稱Written/ACK或完整worldpublication。

SceneContent wrapper只提供actual current-world area/scene的NPCList及EnyName觀察，不能替代card-derived另一target場景資格；完整SceneSupply與entry_qualify仍mandatory。current Main86只呼叫無explicitworldplan的run_server(config,seconds)。缺口是實際資料/規則/scene owner，不新增重複泛用factory或啟用空owner。

本輪三份固定封存closure/metrics見research doc；source-entry19完整inputs824429B，manual scopes另列。990src unchanged；C++0/sourcebranch0/opcode0/fullroute0；mixed282/CUSTOM135/groups26/pending10。TW C2S156/worldparser74=limited50/control11/unconnected13；S2C252=fixed230/variable22/nondefault206/default46/reply48/push11/gated4/unclassified117；battle110/specialized9，86selectors7/cases6，83actions23/projections2/outside21；TW chains3/bindings38unique34；CN chains35/bindings93unique71，historical C2S156/S2C phaseopcode280/length253 distinctscope。全遊戲封包數/完整雙向路徑/分母/TW與全遊戲百分比null；所有execution false。保留shared64/CN/web/nativefonts/帳號存檔/其他凍結功能。前goal status-only turn no progress已revalidate並採取本輪newbounded trace，goal active。

下一來源：用實際2A非零transform path的精確card lookup owner/row/target EnyName resource資格，補完整issuer所需原始資料；沿native-remote312已資格的actual other-opcode escaped pointer consumer追其直接writers及未展開子呼叫，保持full6F body8/10 opaque來源獨立，不再重跑已知local option或generic allocator。


## 第313輪：原變身卡catalog與入口target來源串接

新增TaiwanNativeTransformCards，持有呼叫者提供的完整原decoded0f04 bytes，先own再SHA／解析。保留101筆原始key0..100、raw行／offset／39欄及selected原始整數；field0/1/3/4/5與8..22按實際45BB10的BYTE／WORD stores投影，不生成pointer／padding或怪物combat值。

明確card-aware scene_entry_offer接入原Application同Context的EnyName reader與原entry supply／CAS。供給完整2A後只在nonzero transformkey找exactcard row，再讀其可能不同於world的target area／scene／one-based ordinal；完整Scene witness保留到actual Issuer各CASboundary的前後來源檢查。原producer仍mandatory，不改下一快照bytes或啟用Main。

完整45BB10 loader／numerichelper／tokenizer資格與來源reader設定分開。Native col0作48B索引及WORD0，col3/4/5→BYTEC/WORDE/WORD10；cols8..22→WORD12..2E。Loadedbound舊值未在loader清零，maxacceptedkey+1是有條件結論。Native token count由owner指定，actual source reader配置52再clamp5..52；39欄只是歷史decodedsource的strictsubset，不是固定native grammar。

Remote actual S2CDA nonself46938F→4FC990是128×268 identity pointer lookup，不是setter，並有self503D30分流。實際appearance→wholeactor4FD160直接寫A79，在其條件分支才呼叫4FF8E0；C=A224直接寫WORD C26=A24A，opaqueAction children仍open，不能由此填full6F DWORD9/17或A220。

新增C++2／修改4，source材料元件1；完整玩法branch/opcode/fullroute0。decoded plaintext未恢復，encoded現讀pin吻合；factory要求未来actual owner提供原bytes，不聲稱已載入資料。Strict39fields是原pin的歷史subset。TW156/world74=50部分/11control/13未接；S2C252=230fixed/22variable；CN156/phase280/length253各scope不合併，本輪CN增量0。mixed282/CUSTOM135/groups26/pending10未改。全遊戲總數／完整路徑分母／TW及全遊戲百分比null；無build/tests/runtime/native/VM/codec/SQL/migrate/activate/deploy。保留凍結功能／shared64／TW/CN/web。下一步：恢復不執行codec的既有original card plaintext或獨立完整來源證據，將實際2A供應者及後續Current/Entered接到新catalog；沿actual4FD160→4FF8E0已知Action children及full6F original sources追opaque9/17，避免重跑identity lookup/localoptions/genericallocator。


## 第314輪：入口Supply/Current資源資格與原明文恢復

恢复verified=true历史封存内两份精确原明文：ChangeDollCard15455B/0f04与GameData2783008B/75c3，完整bytes保持。只恢复这两份外部输入，不恢复整个历史客户端或建置树。

with_scene_entry_content在实际Application Context一次安装paired offer与stored entry_qualify，两者同一SceneState强持NPC/card，借用同一catalog到所有issuer/Native/Current drain。实际完整SceneSupply和原qualifier仍必需，拒绝覆盖已有entry_offer。

Stored Supply/Current先拥有Snapshot/Scope/Frame，检查exact frame/root/position，读取完整worldScene与非零transform的exact card targetScene/ordinal；真正原qualifier(Check不变)前后比较完整观察。零key保留原45C000 bypass，不生成opaque2A bytes；原writer/CAS语义保留。

Actual6F旧actor replacement进入C=A224的4FFCF0 cleanup四handle，全部73B旧资格重叠，新增native bytes0。Actionowner/record不是A220/bodypointer；不继续无指向的Action树，不把未知DWORD9/17填成零或已恢复。

修改C++4、新增0、資源資格延伸1，精確恢復原檔2；完整branch/opcode/fullroute增量0，TW156/world74=50部分/11control/13未接，S2C252=230fixed/22variable；CN156/phase280/length253各scope分列。mixed282/CUSTOM135不變。全遊戲總數/完整路徑分母/百分比null。未build/tests/runtime/resourcecodec/gameDBSQL/deploy；只允許一般archive恢復及唯讀tool index。下一步：将两份现已精确恢复的输入供给后续真实游戏资源owner；追完整2A frame issuer的剩余字段及post-entry publication，远端仅追实际full6F bodypointer/A220 read custody，避免重跑known cleanup/allocator/lookups。


## 第315輪：2A body方向與暫存器、遠端參數別名更正

更正226所留46819C fullbody escape方向：傳到415690的是scratch目的，實際2A branch從packet複製至scratch，不能由此formalarg推定wholebody input reader；其後global/opaque callback界線仍open。保留原226紀錄，新增有效更正。

資格actual4607D0低WORD setter與呼叫端EDX來源，關閉未知callee clobber邊界；其selected direct行為不提供2A B26..27或完整native producer。不將count高位／opaque猜成0。已知461270 body+12來源8B及其他已資格方法只作caller-context對照，按實際namedoverlap記錄不算全域新發現。

Remote4FC1C0的body base、directloads與各actual formalarg逐點追蹤；&原body slot在449330前已被改成另一scalar cell，不能當wholebody傳入。沒有恢復新body8 reader或A220權威來源；disp220候選不具actualremotebase資格，維持boundednegative而不說全域unused。

C++新增/修改0、新完整branch/opcode/route0。TW156/world74=50部分/11control/13未接，S2C252=230fixed/22variable；CN156/phase280/length253各scope獨立，CN增量0。mixed282/CUSTOM135保持。全遊戲總數/route分母/百分比null；不build/tests/runtime/VM/codec/gameDBSQL/deploy，不用歷史fixture/defaultkind或0補來源。下一步：依有效方向更正排除knownpacketcopy與knowncomponentreader；追actual2A B0/B4/B8 source及真正scene/publication供應者，遠端只追完整body或A220真實owner的讀取／生成來源，避免generic Action/allocator/lookup及同一negative掃描重跑。


## 第316輪：實際場景WORD消費與owned profile writer來源

接續315 actual461B05→4619D0完整leaf：formalarea／scene在入口讀低WORD，兩個cache bank使用WORD比較／儲存。Q高16不参与此直接consumer；不由此宣稱全461AD0 children/global或原wire B26..27無用／應為0。

45AA70 actual2A caller以area低BYTE、scene低WORD查NPCList；scene WORD與row首BYTE零擴展比較，scene>255是無匹配，不是截成BYTE別名。返回ptr+1 count是無符號BYTE零擴展，僅resource membership／loading來源，非NPC instance／座標／戰鬥權威。既有20260927／223方法保留歷史credit，只計named-reference限定差額。

追實際native create前40B→共同角色profile BLOB來源與current owned appearance writer；SqlitePlayerAppearanceRepository釘6bf/CUSTOM0047、transform0，Application diagnostic fixture writer及單純DA尾快照不能升格actual149c完整2A issuer。Profile局部已知投影保持；缺少真實持久外觀mutation/resource與完整欄位來源，不新增fixture/defaultkind完整成功。

C++新增/修改0；完整branch/opcode/route增量0。TW156/world74=50部分/11control/13未接，S2C252=230fixed/22variable；CN156/phase280/length253各scope独立，本輪CN增量0。mixed282/CUSTOM135保持，全遊戲總數/完整分母/百分比null；無build/tests/runtime/native/VM/codec/gameDBSQL/deploy。下一步：依已排除scene-cache高位直接使用與舊6bf fixture來源，定點追真正actual149c owned appearance mutation／完整2A issuer，NPC／EnyName只保留來源membership，不把resourcecount或名字當worldinstance；需要時追實際B0/B4狀態與下一個確實使用的欄位，而非已知cache/lookup/allocator重查。


## 第317輪：實際入口readonly selectors與原明文資源

actual普通2A CALL4684EB：formal1 unsigned B6控制461270四component zero/positive branch；formal2 B0bits16..22只流向463AD0的DrvDoll tail。兩selector與Drv32B／DrvDoll136B namespace分開，未推原server issuer。

在實際RecoveredWorldEntryView加入by-value EntryResourceSelectors，直接讀logical[7]與logical[3]&0x7f；SharedTaiwanWorldEntered::Scope從同一entry轉發給既有Source。兩既有headers修改、無新增檔案／aggregate欄位／wire／DB／cache／權限。只計readonly source projection1，完整branch/opcode/route0。

fresh verified=true archive receipt精確恢復HeroDoll37189B與Drv3899B、共41088B，外置God2；釘8HeroDoll rows與Drv原row0。普通archive zlib與readonly archive-tool SQL，不執行遊戲resourcecodec或gameDBSQL。DrvDoll第三原明文尚未恢復，98fresh conditional domain不當owned2A default。

TW world50/74=67.6%限定部分分支，完整route新增0，全遊戲分母/百分比null。CN無增量，mixed282/CUSTOM135保持；無build/tests/native/gameDBSQL/deploy。下一步：精確恢復獨立DrvDoll原明文並釘ordinal grammar到463AD0的136B bank；接著追actual149c owned2A creation/mutation完整來源，不重查既有cache/allocator或以fresh preview/fixture推權威。


## 第318輪：DrvDoll exact來源與paired入口接入

精確恢復DrvDoll decoded7620B/de9510e0...，145CRLF lines、first26/count120、每row7rawfields。Ordinals0..119來自native count，不以col0 label索引；field1真正空的0沿451B50/451BA0/451B60實證，原第0行filename空，非有效ROM或owned default。

新增immutable TaiwanNativeDrvDoll h/cpp：exactSHA＋全原bytes/header/120rawrows/7fields/offset/line，原col1低WORD、col3 signed32原int、filename原bytes；float multiplier bits只是metadata，不算FPU值／cachehandles／ROM結果。源表不變成怪物屬性或角色所有權。

在既有SceneContent/SceneSupply及paired offer/Issuer/CAS與stored Qualify共享同一strong immutable來源；新增sameContext HostPlan overload保留完整producer和qualifier mandatory。4existing modified/2newsource，resource source extension1；原overloads/current null契約保持，不推Main或完整route。

TW world50/74=67.6%限定部分分支，完整branch/opcode/route新增0；全遊戲分母/百分比null。CN無增量，mixed282/CUSTOM135保持；无build/tests/native/gameDBSQL/deploy。下一步：已排除DrvDoll availability與ordinal混淆，沿current角色profile/owned equipment真實write chain與2A B0/B4 consumer差額追完整owned entry issuer；先匹配真source字段與state lifecycle，不重跑已知rowloader/allocator/ROM，不能用col0/emptyrow/fresh preview推所有權。


## 第319輪：入場current-selector與ownedDA交易來源

將current R44的實際Petdrv signed-WORD getter、local scalar派生與原2A欄位／prior-state來源分开，具體跨度／新舊scope見native-entry固定證據，不把currentselector無條件改稱原B6或server issuer。

對齊C28 occurrence→唯一full20 alias／可選full396 definition→mandatory Action及fullState issuer→jointCommitted→完整DA15的既有source custody；後態有components/transform/scalars/actorID，並沒有fresh2A B0/B4/B8及完整原owned來源。

定位兩writer的實際交易邊界：joint只stage inventory/equipment，entry自有transaction，joint Current也要求autocommit。禁止把publicwriter/current嵌入另一transaction的Issuer；純observe或順序兩次commit不能代替atomic source。

C++/完整branch/opcode/route新增0；TW world50/74=67.6%只是部分解析。全遊戲分母/百分比null，CN/mixed282/CUSTOM135不變；無build/tests/runtime/native/gameDBSQL/deploy。下一步：依actual current-selector與producer差額，從原角色／裝備所有者的真正mutation來源及完整phase-bound入場供應者追字段；對已證明兩store seam不再新增重複adapter。若處理existing-entry＋DA持久同步，必須是same-connection完整tuple的實際source機制，並保留完整原opaque、身份與currentness，不靠public Current嵌入transaction。


## 第320輪：existing-entry與裝備三tuple共同保存

新增existing-entry appearance三population實際同步：同一connection inventory/equipment/full2A在one outer IMMEDIATE、全expected CAS與三phase完整issuer下stage及COMMIT，完整immutable receipt於COMMIT前配置。

Mandatory source提供完整nextframe，不DA生成body；只准logical13..20及33..36改變且nextbaseline等nextDA，其餘selectors/opaque全部exactexpected不變。actor只比較scene handle/DA，common64 root身份保持獨立。

新增同Context三writer binding與publicationfactory；原heldDA source持有EntryCommitted，Prepare/Before/After/queue的每次Current同consistent read核完整三tuple，不降成二tuple。Old兩store/publicentrywriter/Main/packetgrammar保持。

7existing C++ modified/1added，新atomic storage sourceedge1，完整branch/opcode/route新增0。TW world50/74=67.6%只是部分解析；wholegame分母/百分比null。Mixed282/CUSTOM135/CN不變，0092只追加當輪來源provenance。無build/tests/runtime/native/gameDBSQL/deploy。下一步：將真正phase-bound原equip規則與完整nextState供給現有C28 Action及新三tuple source；依原角色owned selector來源追firstentry，不再重做已解兩次publictransaction seam或genericgetter。再處理實際storedEntry/common64-to-scene-handle mapping與正常入場收據生命周期，不猜識別或重新發fakebootstrap。


## Round321: entry-preserving inventory component

Existing pre-COMMIT inventory projection now has explicit take(Session&,EntryCommitted), producing an EntryComponent which retains the complete three-store receipt and the original allocated source.

EntryComponent.current observes the same actual Session/private C28 occurrence/lease/phase and all three durable tuples. Material is compared to the prepared projection; durable Current always selects EntryCommitted and rechecks after the last ready observer.

Retain source/receipt/actual Session before virtual observers, terminalize nested observation or stale data, consume once without encoding/rebuilding a reply. Expose the same complete token for the existing entry-aware DA factory.

Two existing C++ files changed; conditional consumer extension1, atomic writer/native opcode/complete gameplay routes0. Prepare remains two-material-before only; full entry CAS belongs to320 issuer. Same-action use is a caller contract; private occurrence retirement is at whole records batch boundary. Actual independent scene-ID remedy must span Application movement, lifecycle lease and Session tail; not implemented here. World50/74 parser coverage only; whole-game completion null. Phase1: no builds/tests/runtime/native/DBSQL/deploy. Next: Supply original full equip after-state/rules to actual C28 Action, preserve the same EntryCommitted through inventory and DA composition, and wire ordered native replies. For independent scene identity, implement a consumed qualified prepared-lease handle path spanning real HostPlan/Application movement and Session tail, rather than loosening only stored-source equality.


## Round322: qualified scene identity through actual entry callers

Explicit QualifiedSceneHandle source mode keeps common character/storage identity64-bit and obtains the separate scene handle only from a fully qualified complete native2A and the actual prepared private lease.

Same immutable mode spans HostPlan actual selection/entry/stored/Offer/Current, Application movement bookkeeping, lifecycle preparation and the game-owner vault callback; Session strand receives the qualified handle value for its existing1C tail parser.

New-mode activation copies the qualified lease and refinds its exact prepared registry after virtual repository observations. New-mode lifecycle/Entered retain ownership and registry/Session/phase qualifications after observers; old default activation, movement and tail behavior remain selected-character based.

20 existing C++ modified/1 header added; identity source handoff1, complete gameplay branches/routes/native opcodes0. Vault forwards the actual prepared lease handle to the game-side Session before strand tail creation. Original full producers/suppliers remain mandatory; frozen unrelated bounded-ID adapters remain open. TW50/74=67.6% only partial parser coverage; full-game denominator/percentagesnull. CN/mixed282/CUSTOM135 unchanged; Phase1 no build/tests/runtime/native/DBSQL/deploy. Next: Recover the actual owned first-entry producer and complete source rules; supply real C28 full next material and compose existing three-store receipt with native ordered replies. Trace per-feature scene-handle consumers separately before extending frozen gameplay adapters.


## 第323輪：入場原始 NPC ID 標籤旗標來源

# Round323: preserve the native entry NPC ID label request

Two existing C++ headers gain ten lines: an exact read-only flag projection in
RecoveredWorldEntryView and its forwarding accessor in the actual Entered Scope.
One native field-use crosslink is recovered; no new full source-owner chain,
native opcode, gameplay branch or complete bidirectional route is credited.

## Recovered native source relation

Pinned149c mapped image and original5fc PE agree at all selected cuts. Body DWORD0
bit31 is logical4 bit7:4681EB loads the body DWORD,4681FF shifts31 and468204 stores
the resulting0/1 to world+A7F2F3C. WORLD72 composite variants46A84C/46A990 load that
same world field and push it as4CBD70 argument8. This is structural def-use;
intervening mutations, lifetime and all other uses are not globally closed.

For a new NPC slot,4CBD70's4CC253 reads argument8 at entry-SP+20h and passes it
as4CAFE0 argument6.4CB05D reads that argument,4CB061/063 test/branch on zero.
The nonzero branch formats ASCII `npcid:%d` using the actual NPC row DWORD0,
then4CB087 calls509E70. The guarded text writer copies the NUL-inclusive text
to its display row+81h with optional leading padding for a14-character width.
That width is formatting, not a proved buffer capacity or permitted NPC ID range.

Composite catalog/resource guards and new-slot applicability remain essential.
Existing-slot updates need not recreate the label. No rendered success, valid
resource creation, all-NPC behavior, gameplay privilege or original server
flag-selection rule is inferred. This is not a monster ability/stat field.

Six selected spans total648 code bytes/233 instruction sites and two data cuts
total13 bytes. Relative to the explicitly named315/known reference only,282B/
107sites are outside that union and366B/126sites overlap. These are not global
novelty or full-function/game coverage claims. Complete caller maps are boundary
evidence; only the selected trace and necessary joins have semantic qualification.

## Source projection

`npc_id_label_requested()` returns exactly `(logical[4]&0x80u)!=0` from the
complete received entry. Entered Scope forwards it without reading another
snapshot, constructing native bytes, setting a default, changing layout or
granting authority. It makes this recovered request available to the existing
mandatory scene supplier. No concrete supplier invocation, NPC label publication,
new original frame producer or active Main binding is claimed by this accessor.
The complete raw entry remains unchanged, including every other packed bit.

## Equipment source cut and next work

The actual C28 Action still has no literal three-store mutation caller in the
bounded src/scripts h/cpp/lua search. This does not prove global absence.
320/321 already preserve inventory/equipment/existing-entry and its private
EntryCommitted through the inventory component and held DA factory; another
equivalent wrapper would not supply the missing Action.

The real Action must supply complete next inventory/1215B equipment/full40B
entry, genuine ordered3B/41 count/opaque data and the original rules/phase.
Returned sender Reply bytes accumulate in original mixed-batch order, while
held DA uses a separate qualified observer send. Receipt sharing alone does
not establish complete stat/self/observer reply order or mixed fanout, nor is
this a claim that different recipients require a single global order.
Post-COMMIT output failure cannot undo durable mutation; actual recovery and
fresh response authority remain required. The sealed worker report's text
`414991E0` is a typo; the source address is4991E0. Its original report is retained.

Next native entry work must recover genuine full2A setting authority/B8/B26 and
complete6F DWORD9/17/full81B issuer, rather than infer producers from consumers.
For C28, obtain the actual full-next/rules and response owner before connecting
the existing transaction directly. Full-game direction/phase/state/variant and
deferred-path denominator remains open; these source cuts are not gameplay.

## Counts and phase

TW C2S156 candidates; world74=partial50/control11/unconnected13.67.6% is only
partial world parser coverage. S2C252=fixed230/variable22, nondefault206/default46,
reply48/push11/gated4/unclassified117. Battle indexed110/specialized9;86selectors7/
cases6;83actions23/projections2/outside21. TW unhostedchains3/bindings38 unique34.
CN C2S156; S2C phase280 and length253 are separate scopes; chains35/bindings93
unique71. Mixed282/groups26/pending10/CUSTOM135. All count deltas are0.
Whole-game packets/routes/denominator and TW/overall completion percentages null.

No builds/compiler/tests/runtime/native/VM/emulator/resource codec/game DB SQL,
migration/activation/deployment. Static byte custody and source review only.
Custom registry, shared tables/TW/CN/web, shared64 plan, coin99999999999/stack99,
native levels, accounts/saves/auth/chat/IME/portraits/fonts/text conversion and
client binaries remain unchanged. No new custom rule or balance value is added.
Heavy evidence stays outside Desktop/God2. The native worker stopped with a
capacity error after its candidate was fixed; root read the selected trace,
completed its archive seal and retained the independent bounded review.

External root: `C:/Users/risei/.codex/artifact-archives/god2-server/20261012/tw-native-entry-npc-label-source-323`.
Native: `../tw-native-entry-packed-mode-source-323/native-entry`.
C28 source: `../tw-native-owned-equipment-action-source-323/c28-source`.


## 第324輪：C28送包返回與本地panel來源

known49A330→496550後無success測試即呼叫4D5910；直接panel body只資格UI+50/52與panelWORD/bit20，opaque5073E0/507BB0保持open，不能當full next裝備來源或pending85608 reset。known4999C0首個equipment30..37條件key非零/instanceDWORD+0C bits8..14<=2，僅該key尋首個bag0..29 field>=3，無count讀取；呼叫496550後直接return1，不證送出或原服成功。

新增靜態來源capture工具1、report欄位1，runtime C++0、new native method/opcode/完整route0；6selected cuts428B/148sites，2known mechanical maps4956B不計fullmanual或globalnovel。獨立count來源審閱確認234舊3B byte-add/signed30與41 absolute，CUSTOM0094 full25 supplier不能升格C28原權威。分母/百分比null；TW156/world74=50partial/11control/13open、S2C252=230fixed+22variable，CN156/phase280/length253 scope獨立，mixed282/groups26/pending10/CUSTOM135不變。

封存native29members/125120B、review10members/42514B均桌面God2外，歷史323與blocked goal觀測保留。新chat full TW/CN/web goal active，不因舊goal/tool狀態停止授權工作。未build/tests/runtime/native/VM/codec/gameDBSQL/migrate/activate/deploy。下一步取得真正C28 fullnext/rules與sender/stat/self/observer有序owner；不重查本輪localpanel/packedloop當新進度，不再新增空supplier wrapper。詳見docs/research/tw-native-equipment-request-context-20261012.md。


## 第325輪：共用quantity64校驗與裝備完整後態界線

修改2既有C++：OwnedStackQuantity from/increase/decrease收完整uint64並先檢邊界後BYTE投影；actual SqliteOwnedInventoryRepository::valid直接消費common quantity64，occupied1..99、unstackable1保持。load/validate_change/stage_replace及現有joint writer校驗共用域；舊literaluint64原已拒大存檔量，並非宣稱原存檔截斷bug。CUSTOM0089舊值保留、追加325來源；沒有新increase/decrease caller/grant/stackability或native99資格。

獨立有界來源收斂新缺口：320三tuple不含self2C/role/resource after-state；可讀aux硬pin6bf/CUSTOM0045，PK讀saved值CUSTOM0106，不能升格149c ordinary equip stat authority。需要genuine same-rule2C/22/24 producer、owned20到DA15、完整affected-state persistence及sender/stat/self/observer order/recovery，不再加外部unknown材料wrapper。authority review24members129027B（含seal25files134008B），sha3401440af868639515c2f2a093dd4d74d1e7a14bcdb1bb4eddae8ba2018a6686。

共用quantity sourcecall新增1；完整branch/opcode/native method/route新增0，TW156/world74=50partial/11control/13open、S2C252=230fixed+22variable；CN156/phase280/length253 scope分列。mixed282/groups26/pending10/CUSTOM135不變，全遊戲分母/百分比null，goal active。未build/compiler/tests/runtime/native/VM/codec/gameDBSQL/migrate/activate/deploy，frozen/TW/CN/web/sharedtables/coin99999999999/stack99/level不變。詳見docs/research/tw-owned-quantity64-and-equipment-state-source-20261012.md。

## 第326輪：E5 PET2 真正輸入來源與原生連續寫入

資格化原生S2C E5 logical9/body8 WORLD4691D9→4A3320 family3→4A5A40；full9與opaque2B保留。完整method／slot42..44／existing72B／非零key／storedslot／inclusive6D61..7F58＋actualmetadata guard、35selector表與directwrite masks已釘定。selector19實際先WORD14再fall-throughWORD16；初始worker簡化錯誤保留並追加correction，root來源用pluralwrites。selector2另外改inventory bits8..14，active44/HUD／GUIchild仍OPEN；無D6因果／歷史／消耗資格。新增1 readonly C++ codec／field operands，不變更pet狀態或Application，沒有權威issuer／完整Action。

append-only frontierv18只加獨立format E5：independent9→10、ledger-unclassified117→116；TW C2S156/world74=partial50/control11/unconnected13、S2C252與reply48/push11/gated4、CN／mixed282/groups26/pending10/CUSTOM135保持。新完整opcode玩法／bidirectional route0，分母和TW／全遊戲百分比null。native14cuts2350codeB/136dataB，67members213199B及初次partial／seal／修正均保留；fullimages只hashrefs。source independent review通過，14members30775B。未build/test/runtime/native/VM/resourcecodec/gameDBSQL/migrate/activate/deploy或clientchange。全TW/CN/web、共用表64／coin99999999999／stack99／原生level及凍結功能目標active。見[第326輪](research/tw-native-pet2-e5-update-source-20261012.md)。

## 第327輪：E5 family0/1/2 與前輪地址修正

補上原生E5其餘direct family：0的signedslot無範圍guard／inventory property WORD；1的slot45→world44/48/4C精確mask、marker／flag／clock／control與其後current context BYTE8/scalar重新讀取；2的existing E3 52B及metadata guards／34selector masks。新增唯讀operands到既有C++ codec；family1 final inventory不得由V推測，root未封存草稿已修正為currentread descriptor。沒有真正issuer、joint mutation／規則／儲存／C2S因果或Application接通。

修正326文件及worker countDWORD文句：58EC*24=85620，family3 S2實際inventory24B row14h DWORD bits8..14（20Bmetadata10h），不是row0/count；原326seal/原始source/report與全部舊parsedledgerfields保留，另加獨立勘誤封存。family3 selector19依序雙寫仍保留。three native/correction packages與finalheader獨立靜態review通過；nativeopcode／phase／完整bidirectional新增0，TW C2S156/world74=partial50/control11/unconnected13、S2C252／independent10/unclassified116/reply48/push11/gated4及CN/mixed282/groups26/pending10/CUSTOM135保持。分母／TW與全遊戲百分比null，goal active。未build/test/native/runtime/VM/resourcecodec/gameDBSQL/migrate/activate/deploy或clientchange。全TW/CN/web、sharedtables/common64/coin99999999999/stack99/nativelevels及所有凍結要求不縮減。見[第327輪](research/tw-native-e5-family-source-20261012.md)。


## Round328 — actual E6 scalar input, 2026-10-12

Previous327 was source progress; goal remains active, not paused/complete/blocked.
See research/tw-native-e6-petegg-input-source-20261012.md. Actual E6 length13
table and WORLD4691EB qualify body0/4/8 direct copies into primary UI U44/48/4C
at U=WORLD+A7F2F6C, shared with E5. New RecoveredPetEggStatus is lossless and
read-only. Existing4D5970 can clear U44 low28 after opaque children, so incoming
values are not final current state or E5 input. PetEgg_Open's full20 item reads
do not establish scalar generation; incoming3B slot45 does not initialize U8.
Native source20cuts3474codeB/286dataB; historical methods receive no new novelty.
Frontier v19 independent10->11/unclassified116->115; new opcode/phase/handler/
complete bidirectional routes0, all other scoped counts unchanged. Denominator,
TW completion and whole-game completion null. Full TW/CN/web/shared-table/common64/
coin99999999999/stack99/native levels/frozen requirements remain active.
PHASE1 source/hash/PE/Capstone/static report only; no build/test/native/runtime/VM/
codec/game DB or SQL/migration/activation/deployment. Next recover actual U8
lifecycle and true E6 current-state issuer/rules/persistence/ordered replies,
retaining postcopy child effects rather than assuming final values.


## Round329 — PetEgg actual index and B1 action source, 2026-10-12

Previous328 was progress; goal active, not complete/paused/blocked. See
research/tw-native-petegg-selection-and-b1-source-20261012.md. Actual Main setup
forms U=Main+A7F2F6C ->4817C0 ->4D4B80, which directly setsU8=45,
U44/48/4C=0 andU52=FFFF; later opaquechildren do not establish finalstate.
Actual primary actiondispatch ->complete4D6940/table/guardleaves ->4D6BA0
qualifies B1logical2/body1 selectors0..6/9. It carries no slot/key/full20 and
no E5/E6 causal reply is recovered. New readonly RecoveredPetEggControl is
standalone; existing Options7/8/CUSTOM0100 and worldparser stay unchanged.
4/5/6 needWORD52predicate RETURN0 and currentU44bit29; common opaqueprefix
precedes live reads. Source final17cuts7028codeB/66dataB; historicalmethods
gain no globalnovelty. Ledger appends eightunresolved gameplayvariants under
unique329field while old B1control7/8 scope remains historical.
All scopedcounts unchanged, completebidirectional/handler/opcode/phase increments0;
whole denominator/TWcompletion/wholecompletion null. FullTW/CN/web/sharedtables/
common64/coin99999999999/stack99/nativelevels/frozenrequirements remain active.
PHASE1 source/hash/PE/Capstone/staticreport only, no build/test/native/runtime/VM/
codec/gameDB/SQL/migrate/activate/deploy. Next exactmissingedges: currentU8/owned45
instance acrosschildren, realUI504620input, genuineB1 operation/rules/storage/
orderedreply/recovery and any E5/E6 pairing; no empty supplier closes these.


## Round330 — genuine deferred PetEgg B1 variants, 2026-10-12

Previous329 was progress; goal active, not complete/paused/blocked. See
research/tw-native-petegg-deferred-b1-source-20261012.md. Alternative localopens
4DA680/4DC710 lead to distinct later actualUIevents: primary482748->4DA730
queuesB1selectors10/11;4827A5->4DC880 queues14..37 fromcurrent24WORDarray or43
fromcontrol25. Opensdo notdirectqueue; opaquechildren/currentstate remainopen.
Existing RecoveredPetEggControl now preserves35selectednumericvalues and three
knownUIorigin tags, notauthorityphase/ownership. Guardeduint16 1821..1838 lowBYTE
projection exact; native MOVSX targetisCX, notfullECX; highbitsnotpredicted.
Compactlabels are not automaticallyoriginalrow/control; actualU0A writersopen.
No parser/handler/owneditemprovider orreplypairing added. Native15cuts904codeB/
11dataB; historical329caller/producer and324close retainnovelty0. Independent
review exactheaderpassed; aggregate-null metadata retained withimmutableappendix.
All scopedcounts unchanged, opcode/phase/handler/completebidirectional increments0;
27 sourcevariants are not27completedroutes. Denominator/TW/wholecompletion null.
FullTW/CN/web/sharedtables/common64/coin99999999999/stack99/nativelevels/frozen
requirements persist. PHASE1source/hash/PE/Capstone/staticreport only, no build/
tests/native/runtime/VM/codec/gameDB/SQL/migrate/activate/deploy. Next actualU0A
writer/eventlineage and trueoperation/rules/currentowner/persistence/replies/
recovery, withpostchildcurrentstate andB1/E5/E6causality independentlyproved.


## Round331 — E7 raw status and genuine list zero source, 2026-10-12

Previous330 published141c1eb with successful notification; goal stays active.
See research/tw-native-petegg-e7-list-source-20261012.md. Actual4691FD->4D6340
S2CE7 length2/body1 has two localtype/row predicates, low7status branches and
necessary4D9990 child preserving rawhighbit37/38/39. New readonly raw2codec
RecoveredPetEggNotice is formatonly: no guessed B1 response/eligibility/handler.
ActualsameU setup4817C0->481C20->4DC610 directlyzeros48B U0A..U39; later
children and nonzero arraypopulation remainopen.15cuts3220codeB/55dataB all
pinnedPEequal; initialseal precisionerror preserved withimmutableappendix.
Frontierv20 changes onlyE7 classification, retainsallnative/historicalfields:
independentformat11->12, unclassified115->114. No newopcode/parser/phase/
authority/completebidirectional/gameplay credit. TW C2S156/S2C252/world74
partial50/control11/gap13; CN C2S156/phaseS2C280/lengthS2C253. Allotherscoped
counts unchanged; denominator/TW/wholecompletion null. FullTW/CN/web/common64/
sharedtable/coin99999999999/stack99/nativelevels/frozen requirements persist.
PHASE1source/hash/PE/Capstone/staticreport only, no build/tests/runtime/native/
VM/codec/gameDB/SQL/migrate/activate/deploy. Nextnonzeroarraywriter/actualinput
lineage and originalissuer/rules/currentownedstate/persistence/orderedreplies;
B1/E5/E6/E7 pairing must be independentlyproven, notsameUI/similarstatus.


## Round332 — actual E8/E9 byte sources and UI event lineage, 2026-10-12

Previous331 wasprogress;0f01cd9 publishedandnotification succeeded. Goalactive.
See research/tw-native-e8-e9-ui-byte-sources-20261012.md. ActualWORLDcells
46B974/78 identifyE8/E9 at46B46E/46B480, notPetEggadjacentcase. Bothlogical2
body1, fullrawBYTE writes: E8indirectP15E thenrereadP8688C+90 child;E9U8B747
thenWORD8B744/BYTE8B746zero before2opaquechildren. Newreadonlyraw2codec keeps
eachopcode and allBYTEbits withoutBooleanclamp/currentowner/resultguesses.
Actualfull504620 source qualifies primaryU+E2170 polloutput localWORDcontrol,
localBYTEevents and AXwidget feeding realdeferredcontrolbranches; these are
localUI, notreceivedpacket/ownership/phase/gameauthority. Arraynonzero fill
and originalissuers/causalB1 pairing remainopen. No newstatewrapper/handler.
Frontierv21 onlyaddsE8/E9independentformats12->14/unclassified114->112 while
retainingallnative/historyrows. Allothercountsunchanged: TW C2S156/S2C252/
world74 partial50/control11/gap13; CN C2S156/phaseS2C280/lengthS2C253. No new
opcode/parser/phase/authority/completebidirectional/gameplaycredit; denominator/
TW/wholecompletionnull. FullTW/CN/web/sharedtables/common64/coin99999999999/
stack99/nativelevels/frozenrequirements persist. PHASE1static source/hash/PE/
Capstone/reportonly, no build/tests/runtime/native/VM/codec/gameDB/SQL/migrate/
activate/deploy. Next actualnonzeroarraywriter, originalP/issuers and genuine
currentownedstate/rules/storage/orderedreplies/recovery, noUIasauthority.


## Round333 — real9C raw format and PetEgg list boundary, 2026-10-12

Previous332 wasprogress;d08fde8 publishednotification succeeded. Goalactive.
See research/tw-native-9c-and-petegg-list-boundaries-20261012.md. Actual9C
logical49/body48 length401594->401276/WORLD46B844->468C8C->full4F34C0 reads
UIformat operands undercurrent signedU232E22 gate, notdirect24WORDU0A copy.
Newreadonlyraw49 RecoveredWorldPanel9C keepsall48bytes/rawDWORD20/24, no
fixed16strings/result/ownedstate/issuer guesses. SelectedE7 full4D9BE0/4D94D0
andnecessary4D98B0/RET4D97F0 showdirectscalar/UIeffects, noqualifiedlistwriter
orqueuedchain. WORDUIcounter native16wrap/partialAXthenDEC32 keptassource,
notnewmath/currentstate API/common64gamedomain. Allregisterfinite0A scan19
rawcandidates hasnoalignedaliasproof/globalabsenceclaim. Nonzerolistpopulation
stillopen; actualunprovenchildren/computedalias/upstreamissuer next.
Frontierv22 adds9Conly, independent15/unclassified111; allpriornative/history
fields preserved. Othercountsunchanged: TW C2S156/S2C252/world74 partial50/
control11/gap13; CN C2S156/phaseS2C280/lengthS2C253. Opcode/parser/phase/
authority/completebidirectional/gameplayincrements0, denominator/TW/whole
completionnull. FullTW/CN/web/sharedtables/common64/coin99999999999/stack99/
nativelevels/frozenrequirements persist. PHASE1source/hash/PE/Capstone/report
only; no build/tests/runtime/native/VM/codec/gameDB/SQL/migrate/activate/deploy.


## Round334 — actualF4 list-word writer and current web source handoff, 2026-10-12

Previous333 wasprogress;87fa5f3 publishednotification succeeded. Goalactive.
See research/tw-native-f4-list-writer-and-source-handoff-20261012.md and the
updated WEB_CLIENT_SERVER_INTEGRATION_20261007.md source/gate matrix.
ActualF4 logical5/body4, length4016F4->4012AC/WORLD46B9A4->469233->same
primaryU Main+A7F2F6C->full4A3380 supplies rawWORD2 toU0A+2index forinitial
unsignedindex<24. This demonstratesa nonzero-capable input to24WORD array
readby4DC710/4DC880. Initial>=24 hasopaqueassert thenreread; diagnostics
readWORD2 butno directstore inthatbranch. RawBYTE1/fullWORD/allindexes kept;
noWORDvaluegate orfinalpopulation/ownership/issuer/F4-B1causality invented.
No parser/handler/authority activation ornew currentstate provider. Expanded
named.text833rawcandidates/physical-mappedsection and2knownCALL scopes retain
noexecflags0 pitfall, unmappedtail andcomputedalias/indirect/otherwritersOPEN.
Webhandoff listsactualnativephase source contracts plusordinarymain plansnull
versusqualified common/Web source owners; no currentendpoint/liveacceptance.
Frontierv23 addsF4only, independent16/unclassified110; allpriornative/history
fields preserved. TW C2S156/S2C252/world74 partial50/control11/gap13; CN
C2S156/phaseS2C280/lengthS2C253 unchanged. Opcode/parser/phase/authority/
completebidirectional/gameplayincrements0, denominator/TW/wholecompletionnull.
FullTW/CN/web/sharedtables/common64/coin99999999999/stack99/nativelevels/frozen
requirements persist. PHASE1 source/hash/PE/Capstone/report only; no build/
compiler/tests/runtime/native/VM/codec/gameDBSQL/migrate/activate/deploy.

## Round335 — actual PetRoom catalog namespace and source boundary, 2026-10-12

Previous334 was progress;12bba54 publication/notification succeeded. Goalactive.
See research/tw-native-petroom-catalog-source-boundary-20261012.md. Actual
459A60 reads lowWORD-indexed shared pointer table; full4599B0 registers token0
keys to396-byte rows, complete459420 puts token5 inmetadataDWORD0/token4 at+8.
Actual459150/459380/456130 distinguish category selection duringload fromlookup;
4591C0/459A20 are interior instructions. F4 list andfull20PetEgg reader share
catalog pointer, butactual6177..6200 bank/rows/loadorder remainOPEN. Historical
four-family observation cannot stand for currentbank/eligibleownedpopulation.
ExistingF3/F5 codecs agree; establishedF3 TOTALframing remainsqualified. New
receiver continuity retains F5storedgate/bodyWORD0reread andF3partialAX caveats;
no duplicatecodec/class/consumer credit. ActualC28/companion sources cannot
supplyF4population/B1operationowner. No newprovider/handler/activation.
Newpublic staticcapture sources2; existingC++ provenancecomment3lines only.
Frontierv23 byte-identical; TW C2S156/S2C252/world74 partial50/control11/gap13;
independent16/unclassified110; CN C2S156/phaseS2C280/lengthS2C253 unchanged.
All packetcount/phase/authority/completegameplay increments0; fullTW/game
denominator andcompletionnull. Next exact source: actualbank-qualified rows,
eligibleownedpopulation/issuer/actionselection/rules/fullorderedreply/storage
andApplicationhosting. FullTW/CN/fourWS/sharedtables/common64/coin99999999999/
qualifiedstack99/nativelevels/fonts/textconversion/frozenrequirements persist.
PHASE1 static source/hash/PE/Capstone/report only; no build/compiler/tests/
runtime/native/VM/codec/gameDBSQL/migrate/activate/deploy.

## Round336 — exact SPI raw-source catalog, 2026-10-12

Previous335 was progress;68cd74a publication/notification succeeded. Goalactive.
See research/tw-native-petroom-spi-raw-source-20261012.md. Actualretained SPI
records6177..6180/6183..6200 total22, ordinals517..538/lines8695..8716,
normalizedCP9503512bytes with all rawfields/hash provenance. Sourceinventory
16127/SPI737 and ItemType9/line20/categoryoffset1213 independentlyqualified.
6181/6182 absence is bounded to that historicalinventory, not currentbank.
Decodedrowoffsets remainNULL; full396 unavailable. Categoryselector0 requires
historicalzeroallocation. EGG/SPP labels cannot substitute for actual SPI.
NewC++ files2 implement exact22-row catalog/checkedconsistentread and explicit
atomic/idempotent importer into common rawsource tables. No gameDB was opened
or queried/imported/migrated; no Main/Migration/requestactivation. Existing
MapItem twoSPIrows/C28/custody/companion behavior unchanged; source data is not
eligibleownedpopulation, actionpermission or an authoritative gameplay value.
Actualoperationcontrollers13cuts2433code/46paddingbytes retain sourceoperands
row11h/full20+0Dh androw15h/full20+11h; opaqueUIcalls yield no neweligibility.
Signedremainder+30 permits28..32 withoutproducer qualification. Report18h
correctedseparately to PUSH12h/decimal18; sealedoriginal retained intact.
Publiccapture copies2 exact, not rerun. Frontierv23 byte-identical; TW
C2S156/S2C252/world74 partial50/control11/gap13 independent16/unclassified110;
CN C2S156/phaseS2C280/lengthS2C253 unchanged. Packet/format/parser/phase/handler/
completebidirectional/gameplayincrements0; fullTW/game denominator/completionnull.
Next currentbank/full396, eligibleownedpopulation/F4issuer/B1rules/fullordered
reply/storage/recovery/Applicationhosting. FullTW/CN/fourWS/sharedtables/
common64/coin99999999999/qualifiedstack99/nativelevels/fonts/textconversion/
frozenrequirements persist. PHASE1 static source/hash/PE/Capstone/report only;
no build/compiler/tests/runtime/native/VM/codec/gameDBSQL/migrate/activate/deploy.

## Round337 — actual common-parser SPI text projection, 2026-10-12

Previous336 was progress;79f69b9 publication/notification succeeded. Goalactive.
See research/tw-native-spi-definition-text-20261012.md. Native451AE0 andcommon
459420 copies token4->record+8/token7->2E thenforces2D/53NUL; common description
joins nonemptytokens8..12 with LFbetween, noleading/trailingLF, forceBDhafter
unbounded appends. Actualbyte tokenizer/search/copy hasnoquote/CP950conversion.
Finite22pins fitnativebuffers: name6..24/caption20..32/allfieldsmax34/join26..89;
noNUL/CR/LF/comma insidefields. These are meaningfultext, notzero-padded396.
ExistingC++catalog nowlookup_definition_text validateswhole22dataset before
projectingexactrawname/caption/description andretainingfullsource_record.
No numeric/resourcebank/commonID/playerinstance/ownership/eligiblepopulation
oractionpermission supplied; noAPI/DB/importer execution orMainactivation.
Native451BA0 initializeslocal0 andrequires scannerreturn1. ActualboundedCRT
decimalpath qualifiesconditionalaccumulate/write/return only; input/ctype/
EOF/multibyte dependenciesOPEN. No historicalVMadapter promoted to native.
Token13 storesWORD112h/459574; separateWORD118h isFFFF/45994A. Rootunsealed
draft mistaken118h destination corrected andretainedwithreconstructionlabel.
SPIselector0 doesnotdirectlywrite11C; currentallocation/bank/RomMaps/full396
remainOPEN. Publicstaticcapture exactcopy1, no rerun/native methodrecredit.
Frontierv23 byte-identical; TW C2S156/S2C252/world74 partial50/control11/gap13
independent16/unclassified110; CN C2S156/phaseS2C280/lengthS2C253 unchanged.
Packet/format/parser/phase/handler/completebidirectional/gameplayincrements0;
fullTW/game denominator/completionnull. Next numeric/resource/current396,
eligibleownedpopulation/F4issuer/B1rules/fullorderedreply/storage/recovery/
Applicationhosting. FullTW/CN/fourWS/sharedtables/common64/coin99999999999/
qualifiedstack99/nativelevels/fonts/textconversion/frozenrequirements persist.
PHASE1 static source/hash/PE/Capstone/report only; no build/compiler/tests/
runtime/native/VM/codec/gameDBSQL/migrate/activate/deploy.

## Round338 — historical offsets and conditional physical scalars, 2026-10-12

Previous337 was progress;78a2459 publication/notification succeeded. Goalactive.
See research/tw-native-spi-offsets-and-scalars-20261012.md. Retainednonretired
round314 decoded75c3 independentlyqualifies SPI22 historicaloffsets/allrawbodies
and57RomMaps raw5-fieldrows/order/offsets. SPI3556B CRLF cut673207..676763;
RomMaps3513B cut4374..7887. Currentef297 encodedbank remainsdistinct/unobserved.
Existingcatalog lookup enriches returnedcopy offset+supplementale9c54fingerprint;
rawSQLv1NULLpins/843555fingerprint/importer unchanged. No migration/DBexecution.
NewphysicalscalarAPI validatescomplete22 before restrictedASCIIdecimal32bit
sourcearithmetic/WORD114/112/11A8bits/11BLOW4. Returnedqualification explicitly
requires stablevalidctype -1..255 and masks0004/0008; no observed/satisfiedbool,
currentnativevalue/default11C/resourceordinal/full396/gameplayattribute claimed.
Actual49h stringdescriptor/byteinput/EOF branch nowqualified; finiteEOFsuccess
returns count1 via550C31/37/89/8E/9D. Previousconditional550C9A keptseparate.
ASCII/EOF classification fastpaths avoidopaque multibytechild, butactual553BB3
canpublish dynamicallygeneratedctype. InitialPE values notcurrentlocaleproof.
Classification738code/522dataB; report518 typo correctedimmutableappendix,
originalseal retained. Input5completecuts428B; allnative methodcredits0.
RomMaps459F47 interiorrowfragment notfullmethod; actualloader/count/allocation/
order/convertedranges remain nextsource, notinventedWORD116. PriorNULLmetadata
andfailedcapture drafts remainpreserved; publicstaticcapture exactcopies2 plus
classification finalCRLF-to-LF derivative1; originalsealedscript notrewritten.
Frontierv23 byte-identical; TW C2S156/S2C252/world74 partial50/control11/gap13
independent16/unclassified110; CN C2S156/phaseS2C280/lengthS2C253 unchanged.
Packet/format/parser/phase/handler/completebidirectional/gameplayincrements0;
fullTW/game denominator/completionnull. Next classifierlifetime/RomMapsloader/
currentbank396/eligibleownedpopulation/F4issuer/B1rules/fullorderedreply/storage/
recovery/Applicationhosting. FullTW/CN/fourWS/sharedtables/common64/
coin99999999999/qualifiedstack99/nativelevels/fonts/textconversion/frozen
requirements persist. PHASE1 static source/hash/PE/Capstone/report only;
no build/compiler/tests/runtime/native/VM/codec/gameDBSQL/migrate/activate/deploy.

Round338 independentreview clarification: scalarqualification also requires exact
normalized1..5 ASCIIdigit bytes in ordinarynative flags49h stringdescriptor.
OriginalCRLF finaltoken25 line-reader behavior is OPEN; retainedCR would require
opaque nonEOF pushback553158. Stablectype alone does not establish actualnative
original-file output. API observes neither inputpreparation norclassification.

## Round339 — common RomMaps source and conditional SPI resource field, 2026-10-12

Previous338 was progress;7f111e4 pushed and notification38249832572 succeeded.
Goalactive. See research/tw-native-rommaps-spi-resource-source-20261012.md.
ActualCALL456268 reaches full459EF0loader, signedWORDcount/84hstride/token0slot;
459FC0 firstunsignedinclusiveWORDrange match and459943 AX->WORD116 nowqualified.
Loaderreturn1 notfullpopulation; positivecount nullguard absent. Fullallocation
helper547E23 includesreachablecoldtail; allocationchildren/success unobserved.
Actualrt->4000h->fd80h->54EF0C CRLFtoLF source proves conditionalnormalizedinput,
with successfulread/lookahead/seek/stablefd/exactsource/transform conditions.
Prior338 CRLFgap/seal preserved; no native/current input or ctype observation.
Two new commonC++sourcefiles pin raw57 RomMaps/5fields/bothpaths/header/offsets,
dataset tw149c-historical-rommaps-source-v1; canonical14189B/708atoms SHA99f0fe.
Strictmain joinedwhole57 read/counts/envelope/rawbytes exposesorphans, borrows
callertransaction elseownsreadscope. Explicitimporter BEGINIMMEDIATE/idempotent/
emptyinsertonly/reverify/rollback plus main/TEMP case-insensitivetriggerguards;
sourceSQLnotexecuted, noMain/Migration/requestcaller. OriginalitemSQLv1NULLpins/
read/importer/MapItemtwoSPI/saves unchanged. Newresourcecomposition oneouter
sameconnection ReadScope validatesbothinstalledSPI22/RomMaps57 beforekeylookup;
missing/empty/corruptsource iserror, absentkey onlyafterbothvalidations returnsnone.
Convertall57finiteindices/ranges beforefirstslotmatch, unsignedWORDinclusive/
uint16FFFFsentinel, returnowningsource/scalars/matchedrawrecord+catalogfingerprint.
194rawnumerictokens1+171+22 ASCII1..5/max65500/count57/alloc7524beforealignment;
57nonoverlappingranges/all22iconsmatch:slot25x4,27x2,35x1,43x4,44x7,46x4.
Independentconditionalnumericproof23012B SHA388012; bothnativeinput/ctype and
loaderdispatch/allocation/fullpopulation/stablebank/SPIcommontail conditions
remainexplicitunobserved. token4/default11C/118/full396/ownedrights notinferred.
Historical70a4/75c3 remainsdistinctcurrentef297. SevenoriginalLFstaticcaptures
publishedexactly/notrerun; generationstage+TEMP/maincasecorrections preserved.
Frontierv23 byte-identical; TW C2S156/S2C252/world74 partial50/control11/gap13/
independent16/unclassified110; CN C2S156/phaseS2C280/lengthS2C253 unchanged.
Packet/format/parser/phase/handler/completebidirectional/gameplayincrements0;
wholeTW/game denominator/completionnull. Next full396/currentbank/eligibleowned
population/F4issuer/B1rules/fullorderedreply/storage/recovery/Applicationhosting.
FullTW/CN/fourWS/sharedtables/common64/coin99999999999/qualifiedstack99/native
levels/fonts/textconversion/frozen requirements persist. PHASE1 staticsource/
hash/PE/Capstone/uniquereport only; no build/compiler/tests/runtime/native/VM/
codec/gameDBSQL/migrate/activate/deploy.


## Round340 - conditional historical SPI396 source composition (2026-10-12)

Previous round339 is progress, not goal completion: private mainfe468e6 and
Discord notification38251918456 succeeded. The full goal remains active.

Actual54A550..54A5A8 is retained complete88 bytes with both RETs and no callees.
On the known allocator's valid small-block success, actual547E9E passes pointer,
literal0 and original count*stride product, qualifying exactly that product's
zero stores under DF-clear/fault-free/valid-storage conditions. The successful
HeapAlloc flag8 alternative has official Microsoft HEAP_ZERO_MEMORY evidence.
No API was invoked, and failure/callback outcomes remain opaque.

The original category bank declares46 rows with1602 stride; SPI ordinal9's
selector63D preserves allocated zero only when all36 comparisons return nonzero.
The original SPI bank declares737 rows with396 stride. Retained22 rows occupy
physical source ordinals517..538, not token0-key slots or a native22-row bank.
Actual preceding reads, correct sameallocated physical slot, valid key-pointer
table, bounded children and no prior/intervening/OOB writes remain prerequisites.

Full generic selector0 write coverage separates20 common direct stores from
28 excluded category stores, and separately inventories copy helpers and scratch.
Finite text fits actual native regions. Variable NULs, forced2D/53 NULs and the
description scratch189-after-append boundary are retained; no fixedrecord111
write is invented. BYTE11B highF0/texttail gaps/11C..18B112 bytes preserve the
conditional original allocation zero, rather than becoming observed bank state.

Independent static source arithmetic composes22x396=8712 conditional bytes,
SHA256df6d876a3c5cb3b0d59b9cd2f653696b8401ecbbf41fc50c7e72647a55f89afa.
Canonical12994-byte proof SHA256242ec2de0b202a5f772b48285474fd45aadb03928bec1b1224735253281a3618
retains source/physical position/write origins and all native premises. Exact
historical decoded input, successful rt/CRLF/read/seek, compatible stable ctype,
stable literals and complete unchanged RomMaps57 population remain required.
Current encodedef297 equivalence/native bank/current396 is not observed.

NativePetRoomDefinitionRecordSource and lookup_definition_record_source are
additive source implementation in existing PetRoomHCPP. One outer sameconnection
read scope validates full57+22 resource sources before an absent-key return,
then obtains text and requires identical owning SPI source records. The owning
conditional array uses explicit little-endian stores and bounded exact copies.
No Main/Migration/handler/Application call activates it. BYTE11C conditional0
does not grant eligibility. Old pins/SQLv1/read/importer/text/scalar/resource,
frozen fourfamily observation and oldtwoSPI MapItem catalog remain unchanged.

Unique report20261012-tw-native-spi-conditional-record-340 preserves all prior
ledger fields and frontierv23. New opcode/format/parser/phase/authority/fullroute
credits0; TW C2S156, S2C252=230fixed+22variable,206nondefault+46default,
world74=50partial+11control+13unconnected. Parser-scoped67.6 is not TW completion.
CN C2S156/S2Cphase280/length253 are separate scopes; TW3/CN35 unhosted chains
and TW38/CN93 sourcebindings remain partial. Whole-game denominator/TW/whole
percentages stay null. No build/compiler/test/runtime/native/VM/codec/gameDBSQL,
migration/activation/deploy. Continue actual selected inventory/U8/F4issuer/B1
rules/replies/storage/recovery/hosting and the fullTW/CN/fourWS/sharedtables/
common64/coin99999999999/qualifiedstack99/nativelevels/frozen-feature goal.


## Round341 - exact staged PetEgg client local write source (2026-10-12)

Previous round340 is progress, not completion: private mainfdec5e8 and Discord
notification38253288527 succeeded. Full goal remains active; no narrower success.

Full primary pre-action4D7230..4D78C7 supplies actual response-fed local state
continuity before outgoing UI dispatch. Its selected4D76E0 gate requires whole
WORD U+A6D4==0; field meaning is unknown. Actual first selected clock result
minus liveU8C wraps32 bits, then CDQ/XOR/SUB forms unsigned native magnitude.
Unsigned CMP/JB admits>=60000, including80000000's exact nativebit result.
Full DWORD accepted difference domain isEA60..FFFF15A0 inclusive; no real
elapsed-time, monotonicity, server schedule or gameplay unit is inferred.

First liveU4C+60 changes low18 only, preserving high14 at4D7718. Actual second
clock call precedes freshU4C read771D; secondclock result writesU8C at7720,
then freshsignedU8 read7726 selects rowDWORD+8 at85618+24*I for7733's
secondU4C&3FFFF write. TwoU4C reads and entry/freshU8 are never combined.
Earliernonzero key gate723D is not a lease for the later row. Source offset
is mathematicallysigned64 while original DWORD/WORD/packed masks are retained;
this is not completed shared64 wire/object/display extension.

New standalone RecoveredPetEggLocalCounterSource.h implements exact staged
unsigned arithmetic and returns three ordered direct write descriptions only.
Header5170 bytes SHA256f1138228f0c2e8f73d5da962785147446c8fbfb0461286b3318e4956bc544029.
NativeStageOperands retains each actual read/call operand independently; no
pointer/API/native/inventory/DB write occurs. Nativeprefix/validstorage/faultfree
sameU/read-stage conditions remain unobserved. Emission/mutation flagsfalse;
no Main/Session/gameplay caller, timer rule, Lua policy or authoritative issuer.
Existing E6/PetRoom/RomMaps/MapItem/Sqlite/frozen source is byteunchanged.

Actual complete49A330 control45 drag-release key/type/metadata/panel path leads
toOpen, but directlysetsnoU8. Actualselected validators alsoarenotsetters.
Open same-rowaffinity requires liveU8==45 at every relevant row-read plusstable
row/key acrosschildren. Known329initialwrite45 isnot lifetimeinvariance, and
incoming3Bslot45 isnot U8assignment. False4671A8 primaryalias ispreservedand
excluded: EDI hasbeenreplacedbyformaloutputptr. No wholeimageabsenceclaim.

Pre-action/close actualsources join E5/E6/E7-fed fields andlocal statusflags,
butdo not identify pending request context joining B1/F4/E5/E6/E7. ListB1
selector-onlyproducer queues/closes withoutdirectselectedkey/index/full20save;
validF4 directarraywritehasno directpendinggate. Opaquechild effects andactual
serverissuer/ownedbinding/operationrules/storage/orderedreply/recovery/hosting
remainOPEN. Clientcopy/localwrites nevergrant serverauthority.

Unique report20261012-tw-native-petegg-local-state-source-341 preservesprior
ledgerfields/frontierv23; newopcode/format/parser/phase/authority/fullroute0.
TW C2S156/S2C252=230fixed+22variable,206nondefault+46default; world74=
50partial+11control+13unconnected. CN C2S156/S2Cphase280/length253 separate
scopes; TW3/CN35 unhostedchains andTW38/CN93 bindings remainpartial. Wholegame
denominator/TW/wholepercentnull. No build/compiler/test/runtime/native/CRT/VM/
codec/parser/gameDBSQL/migration/activation/deploy. ContinuefullTW/CN/fourWS/
sharedtables/common64/coin99999999999/qualifiedstack99/nativelevels/fonts/
conversion/saves/frozenfeatures objective, not a local-projection substitute.


## Round342 actual selected presend absolute storage source (2026-10-12)

Round341 was progress, pushed44140eb925f71db5aed45b84e20276ef1c4a0bdf with
notification38255307049 success; full-game goal stays active. Round342 adds
RecoveredPetRoomPresendStorageSource, an actual conditional client source
description of ten ordered global WORD/DWORD writes before optional505230 UI
delegation, and a separate WORD overwrite only after normal return. No native
pointer or storage mutation is performed and no Application gameplay is hosted.

Authentic complete49B82035B maps six-zero incoming to(0,0,12h,0,0,0); large
4B5BE0 has85B authentic entry +294B selected null-input tail, not full-method
qualification. Opaque547B50 frame1184/argument/direction/ordinary-storage
premises are explicit. Complete4BC2E017B and necessary4BC2A055B preserve actual
same-U path. Nine selected absolute writes precede wrapper WORD5926B0=FFFF.
The child gate reduces to signed livehandle>=0 only under the stableFFFF read
premise. Actual composed OR EAX,FFFFFFFF then MOV AX handle/PUSH EAX yields
FFFF0000|handlelowWORD; generic child upperEAX alone stays unknown.505230 uses
U+E2170 with opaque side effects, so no U8 preservation or final-state claim.

Absolute field semantics/pending request/requestID/serverissuer/owned B1F4
causality are unknown. Later caller operations may modify these globals. Old
C++/catalog/SQLv1 NULL pins/importers and immutable v23 are unchanged; decoded
historical data is not relabeled as current client state. No guessed success,
packet variant, parser/control/reject or unhosted source counts as completion.

Unique report round20261012-tw-native-petroom-presend-storage-source-342; all
opcode/format/method/parser/phase/handler/full-route credits0. TW156C2S/252S2C,
world74=50partial/11control/13unconnected;67.6% remains parser source coverage.
CN156C2S/280phase entries/253length entries are separate scopes. Whole TW/game
denominator and percentage remain null. Full TW-first/CN/shared core/fourWS/
common64/coins99999999999/qualifiedstack99/nativelevels/frozen/fonts/conversion
objective continues. PHASE1: no compiler/build/tests/runtime/native/API/CRT/
VM/codec/parser/gameDBSQL/migrate/activate/deploy. Seal/member/source accounting
and static symbolic source reasoning only. Heavy artifacts remain external.


## Round343 actual C24 full native bank alias integrity repair (2026-10-12)

Prior342 was progress, pushed43f4d294b8f017d2b00d697aa68a9c2e3726d8d5 with
notification38256817514 success; full objective remains active. This round
repairs the actual C24 planner's missing exact-TW alias bank bound. Generic
alias BYTE/schema permits0..255; old/next50-row checks only visited0..49 and
could ignore an extra149c/tw149c-item20 alias at50..255 in another owned cell.
The new whole-population scan rejects only that exact pair outside50 before
either0093/0094 mode prepares native output or invokes joint CAS/issuer replay.
All in-bank matching aliases and otherclient/profile retain downstream behavior.
Single562B source insertion preserves every old C++ byte; one existing C++
file changed, no new C++ file/binding/schema/provider/default grant added.

Concrete C24 planner/ready-owner/full joint CAS/two41 result already exist;
its move policy stays CUSTOM-0093, full25 mode stays CUSTOM-0094. Bank-source
audit finds conditional same-connection existing full-pair read closure, not
initial population/acquisition. Legacy/diagnostic/raw definitions cannot create
ownership/native1215 or pad missing witnesses. Host-source audit requires actual
2A/initialscene/direction/ROMprefix/generations/full5D pending Authority/records
Current/real Others, plus existing CUSTOM-0095 movement custody for walk→C24.
Main still selects no world plan. No new placeholder Main factory is installed.

Native preview4D68D0 is control22's alternative prefix, not after49B820/common
deferred send; local20 gets type-only masks and control22 exits without direct
B1. External source evidence/13 gameplay gap inventory/50 reviewed-opcode
crosswalk and precise-line correction remain scoped, immutable and credits0.

Unique report20261012-tw-native-c24-fullbank-alias-source-343. New full routes,
opcode/format/method/parser/phase credits0; TW156C2S/252S2C, world74=50partial/
11control/13unconnected. CN156C2S/280phase/253length scopes unchanged. Parser
source coverage67.6% is not game completion; whole TW/game denominator/percent
stay null. Full TW-first/CN/fourWS/sharedtables/common64/coin99999999999/
qualifiedstack99/nativelevels/frozen/fonts/conversion objective continues.
Five exact LF helpers copied once, no capture reruns; previous ledger fields,
goal binary prefix and immutablev23 preserved. Heavy artifacts remain external.
PHASE1 forbids build/compiler/tests/runtime/native/API/CRT/VM/codec/parser/
gameDBSQL/migrate/activate/deploy; none occurred. Static source/custody only.


## Round344 concrete normal-entry C24 owner and Main source host (2026-10-12)

Prior343 was progress: dd7524e842479f4ca534f1f0a5291d93c3412c34 pushed;
notification38259615521 success; full goal remains active. New concrete normal
owner uses private actual Session initialization/current_on_game/entry_written,
captured CharacterSelected/InWorld phase/root/battle, actual full2A actor and
existing RecoveredMovementService positive live saved pose. It reuses the exact
full-instance planner, out-of-bank alias guard, prepared native result and full
joint CAS. Pure issuer checks no reader reentry; postcommit stale delivery throws.

Only full25 CUSTOM-0094 is exposed on this legacy owner, never count-only0093
from scalar projected flags. Main's default-off world.owned_whole_bag_moves
creates real same-Database writers/transaction and the actual movement binding.
Final outer world_records wrapper precedes typed consumers/observers; dedicated
existing service admits exactly oneC24+idleTicks before any mutation. Competing
inventory/battle request batches and scalar/typed projection/population options
are excluded. Config-load and programmatic Config share the validation; explicit
shared plan/native-records lab conflict. Original default routing and normal
movement/chat remain. Weak facade stops/invalidate before drain, disconnect
releases before observers, game-owner guard revokes before borrowed DB/movement.

Genuine existing full common/native50 bank, full25 aliases/current actor/pose
remain mandatory, not populated/granted/padded/imported. Two affected rows alone
receive clear/full3B/final41; other48 initial cache and remote execution unknown.
Legacy movement does not advance equipment witness pose; stale bank refuses,
no automatic rebase. Existing common CUSTOM0095 is separate unselected frontier.
Opaque helper/original swap rules/full mixed provider remain OPEN. This closes
one actual Main source-connection gap, not full gameplay, freshclient initial
population or all C24 variants. Shared normal/common factory policies retain
CUSTOM0093/0094 provenance; no compiler/runtime acceptance claimed.

Unique report20261012-tw-native-c24-normal-entry-source-344. New source Main
branch1; opcode/format/parser/phase/full-route credits0. TW156C2S/252S2C;
world74=50partial/11control/13unconnected; CN156C2S/280phase/253length scopes
unchanged.67.6% remains parser-source coverage; whole TW/game denominator and
percentnull. Full TW-first/CN/fourWS/commoncore/sharedtables/common64/coin
99999999999/qualifiedstack99/nativelevels/saves/frozen/fonts/conversion goal
continues. Heavy evidence external, every package member checked individually.
Goal binary prefix/prior ledger fields/v23 preserved. Static source only;
PHASE1 no build/compiler/tests/runtime/native/API/CRT/VM/parser/codec/gameDBSQL/
migrate/activate/deploy. Baseline capture correction candidates stay preserved.


## Round345 actual normal-entry joint movement custody source (2026-10-12)

Prior344 was progress: pushed1b9bccaf29915afb37d7ee3379f5261b141eba2c,
notification38261399611 success; full objective remains active. Normal-entry
C24 now has a real Main owner, but legacy movement made its native witness
stale by committing only saved position. New concrete MovementService typed
Session+samejointtransaction API shares the exact existing batch sequence/
step/navigation/ACK preparation. It commits finalxy once perbatch, including
stationary revision advance, and retains all inventory/native material bytes.

Actual private initialization/entrywritten/currentgame/actor/root/phase/battle
andpositive existing saved pose/full bank are checked, no common fakelease or
supplied Current/commit callback. Owned old active snapshot and poison guard
close opted reentry/remove/rebind; no mapiterator spans observer calls. Joint
Current runs pure OLDactive+Session only beforestaging, noSQLreader reentry.
AfterCOMMIT validate receipt/oldactive then publishnew saved/queue/geometry,
then freshcurrent_location/jointcurrent before returningprebuiltACK. Missing
or stale material refuses opt path, never legacy fallback/default/rebase/grant.

Mainexistingdefaultoff wholebagprofile retains SAME tx for C24 andmovement.
Final outerwrapper sends wholebatch anyC24/move to real service beforeother
mutators/observers: movements+ticks ORoneC24+ticks only; mixedreject prewrite.
Postcommitfacade stale throwsforbothsources. Weakcaptures/revocation before
borrowedmovement/DB remain; Configadditionaltransfer/probe/visibility conflicts
are explicit for same-mapprofile. Defaultfalse/frozen native movement/chat/
auth/CN/fourWS/sourcefonts/conversion remain unchanged. Sourcepolicy0095 is
materialretention, not nativeafterstatecapture/originalwitness lifecycle.

Genuine initialfullbank/full25 acquisition/clientfresh50, generalmixedrun,
transfer/battle-return continuity, fullnative5D pending/helper/authority and
native3B opaque/originalmove rules remain OPEN. No freshsourcebytes or native
variant/method inferred from custody.
Unique report20261012-tw-native-normal-entry-movement-custody-source-345;
newMainjointmovementbranch1, nativeopcode/
format/parser/phase/fullroutecredits0. TW156C2S/252S2C,world74=50partial/
11control/13unconnected;CN156C2S/280phase/253length scopesunchanged;67.6%
remains parser-sourcecoverage, wholegame/TWdenominatorandpercentnull.
Full TW-first/CN/fourWS/sharedcore/common tables/common64/coin99999999999/
qualifiedstack99/nativelevels/saves/frozen/fonts/conversion goalcontinues.
Heavyartifacts outsideGod2, individualsealmembers exact. Oldgoalbinaryprefix,
priorledgerfields/v23 preserved. PHASE1: no compiler/build/tests/runtime/
native/API/CRT/VM/parser/codec/gameDBSQL/migrate/activate/deploy.


## Round346 actual mutation aftertuple and original response write custody (2026-10-12)

Previous345 was progress: publishedf5ab47fa8e55ff8c7438284caa23f61c26ca0efe,
notification38264232569 success; all source/ledger/seal/receipt exact. New
concrete source step retains the ACTUAL private joint Committed from each
normal-entry C24 and owned movement plus its original prebuilt response.
Private typed carriers/newopt-in APIs leave old/common APIs as exact adapters;
no laterobserve_committed or suppliedissuer manufactures mutation proof.

Session private WorldResponseWrite is minted onlyactualworld_records callback
for its exact original complete RAW response. Attempt coverscapture/gameunwind/
post/queue/drop; finalacceptedvalidresponse identity mustmatch. Newoptional
Write marker islast, oldresponsebytes/FIFO unchanged. Written onlyexactunheld
front/pointer/fulltransfer/PendingCAS; strandreadsimmutablewire/weakSession/
atomicstatus only. Reject/throw/mismatch/budget/terminaldeny/close/drop→Failed;
duplicate/reentry poisonsoriginal evencaught. Gracefulclose olddrain retained.
No logicalreframe/directsend/native timing barrier or initialreplay.

Actual defaultoffMain uses newtypedC24/move APIs, owns preallocateddraft and
latestactualaftertuple/privateentry/response token per Session incarnation.
Beforefuturemutation requalify closedtuple/currentactualepoch outsidejoint
Current. Pending preservesexistingadmission; Failed/stale refuses writes.
Nextactualmutation replacesoldreceipt; oldWritten cannotqualify stale bank.
No mapiterator acrossobservers; caughtreentry invalidatesdraft/binding.
Weakcaptures/disconnect beforepreviousobservers/stoprevoke beforeborrowed
owners remain. Postcommitallocation/publication failure preservesdurableprefix
andthrows, neverrollbackclaim/retry/native success. Writtenlocal only, no ACK/
cache/catalog/helper/acquisition grant inferred.

Initialmaterial plans locate genuinedefinition/instance/acquisition authority
beforemint143 and full1215row+1/emptytails/DA missing. FirstTick/ready/Written
are notinitialissuers. Genuineinitialfullbank/full25/freshclientfull50,
fullnative5D/queue/helper/valueauthority/transfer/postbattle/allvariants and
nativeacceptance remainOPEN. CUSTOM0094/95 rules/135IDs unchanged; new passive
responseobservation field documentsdata/wireboundary, not newgamepolicy.

Unique report20261012-tw-native-owned-mutation-response-custody-source-346;
existingC++files7modified/new0, newactualMain sourceconnection1; newopcode/
format/native methods/parser/phase/fullbidirectionalroutes0. TW156C2S/252S2C,
world74=50partial/11control/13unconnected;CN156C2S/280phase/253length distinct
scopesunchanged. Parser67.6% notwholecompletion; denominator/TW/gamepercentnull.
Full TW-first/CN/fourWS/sharedC++20AsioLua5.4SQLite/common tables/common64/
coin99999999999/qualifiedstack99/nativelevels/saves/frozen/fonts/conversion
objectiveactive. Heavy evidenceexternal/permemberexact, oldgoalbinaryprefix/
priorledgerfields/frontierv23 preserved. PHASE1 no compiler/build/tests/runtime/
native/API/CRT/VM/emulator/parser/codec/gameDBSQL/migrate/activate/deploy.


## Round347 actual normal-entry readiness and initial authority (2026-10-12)

Previous346 progress published8431708cd2654e419e8a1409f74bc512bc992016,
notification38267614964 success, exactsource/ledger/seal/receipt. Seven actual
C++ changes connected same-operation aftertuple/originalresponse/localwrite;
Pending retainedadmission; Writtenlocalonly. Fullgoal remainsactive.

347 readonly native/body/source increment narrows actual2A readiness:
parentG+2CB8selectsstorednameorNULL; flag!=0 doesnotprovenamepointer!=NULL.
468160independentformal1NULLbranchreturn1skip415690/Ureset but separately
initializesactor. Qualifiednonnull/415690return0/map1..16/normalchildren path
468827→468120(Main,actor)→canonicalU=Main+A7F2F6C→497FE0 forwardREP300DWORDs
underDFclear/writablepreconditions. No blankettail/ready/Written⇒clientreset.
Known468160complete1988B/596sites/4RET12/eightentrytable; old311selectedlabels
remaincorrect. Mechanicalunion1778→1988(+210B), newmethodcredit0. Sixexisting
wholemethods4178B+fourparent/tail486B, total4664code/162data, allcurrentPEequal.
Distinct465323→4817C0→498030 sameU reset/catalog setup; actualcontext+20h
feedsU+CFF70. CorrectedstableESP: S465274/P=S+24 captured4652FB; EDX4652DA
readsMainAA36480; twoPUSH465303/465310 makeESP=S-8;465317[ESP+4C]=S+44=P+20.
ActualsupplierMainAA36480 nowclosed, distinctMainAA36478context18. Initial
native347sealedclaimOPEN missedPUSHheight; originalpreserved+exclusivecatalog
correction supersedesclaim beforepublication. Tableallocation/lifetime/current
bounds/eligibility/remoteacceptance remainOPEN; no newmethod/route/authority.

ExistingTW37/85 privateconversation→LuaCUSTOM0021→atomicCUSTOM0022quest/
scalarrewardreceipt atSqliteRecoveredCharacterRepo225 isconcretelead, not
commondefinition/instance/full20/full25/native1215issuer. Mapcatalogdisplay
importerinventory_grants0; charcreation/entry/CAS/PKserialization cannotgrant
firstbank. Needactualoriginalsave/importproducer orseparatelydocumentedpolicy
mappingevent tocommonidentities+authentic sameeventmaterialbeforemint143.
No conditionalreplay/gate/newcustompolicy/sourcefactory/grant/schema/rebase.

C++changes0/newnativeopcode/format/method/parser/phase/sourceconnection/full
routes0. Unique report20261012-tw-native-normal-entry-readiness-authority-source-347.
TW156C2S/252S2C/world74=50partial11control13unconnected;CN156C2S/280phase/
253lengthseparate scopes unchanged; parser67.6% notcompletion. Allwhole/TW
percent+denominatornull. Threeexternalpackages124members371541B plusindependent
review; sixpublicsuccessfulLFhelpers exactnotrerun. Alloldgoalbinaryprefix,
priorledgerfields/frontierv23/custom135IDs/sourcebytes preserved. Initial
bank/full25/freshclientfull50/DA/catalog/helpers/native5D/allvariants/transfer/
postbattle/nativeacceptance OPEN. FullTWfirst/CN/fourWS/common64/coin99999999999/
qualifiedstack99/nativelevels/saves/frozen/fonts/conversiongoalactive. PHASE1
no compiler/build/tests/runtime/native/API/CRT/VM/emulator/parser/codec/SQL/
importer/migrate/activate/deploy.


## Round348 actual catalog loader and item helper source (2026-10-12)

Previous347 progress published6f1dc2da05006fe9c6142ae9fba748fb02c63efc,
notification38269315142success; actualsource/ledger/seal/receipt exact. Corrected
known2A/reset/context20 source doesnotattestremoteclient/currentbank/authority.
348followsactualpointer/loader andclosesonepreviouslyopaqueknown49B850 method.

Exact4649DB rereadsMain+A7E05C4 afteropaqueCALL412EE0;4649EC/F1 adds444/stores
MainAA36480. OriginalApplication affinity requiresnointerveningfieldreplacement
andvalidlifetime, notinferredopaqueinvariance. Qualifiedconstructor/startup
Application+444 source separates ProgramMsgdynamicB2C68/signedWORDB2C6C label
bank fromgeneric396-byte records/inline32600DWORD B2D40 keytable(130400B).
396recordwidth notcapacity. Actual22filenamepairs/44names+%scomm pathoperands
qualified; noresourceopened/decoded. ProgramMsg literal/categoryprecedence
selectsknown458C90 count*4/stringallocation/line-token1/NULcopy/boundupdate.
No priorboundresetwhenarrayreplaced; return1 includesEOF/nonpositivecount;
missing/duplicate/currentallocation/bound/entries/helperreadiness remainOPEN.
Sameobject/nativecatalogsource cannotgrantitems ormakebankreceipt.

Known49B850..49BAE0 complete656B/224sites/9RET8/alllocaljumps closesinspected
238/346opaquefrontier only, no globalhistoricalfirst/newopcode/format/route.
LowWORDsignedDI0..49 gate leavesfullEDIupper16unknown; parentMOVSX CX,AL
preservesECXupper16. Rowfull20=existing3Bbody+4copy→row+4. LiveDWORDrow+4
stagedreads cannotcollapseacross49B720/5068C0/49B770; selected42/43rereadagain.
Directcount/mask003F0000/byte+0C andProgramMsgkey1A2/36A UIbranches noeligibility
orissuer. Directnonstackstores0 notglobalchildstateabsence. Outputmeaning/
U-rowstability/allocation/opaqueUI/queue/currentness OPEN. NextactualsameU
stackoutputsource49B720/49B770 separatefromcommonacquisitionauthority.

Twoexternalpackages115members182026B individuallyverified; loader13cuts2846B
(eightknownwhole2424+fiveselected422),data50cuts1238B. Helpermisaligned38B
caller draftpreserved/excluded; newaligned498E0A..498E30 sourceequal. FiveLF
publichelpers exactsuccessfulstages, none rerun. Prior347all54members,335six
referencedmembersONLY; helperprior346/238106members375100B verified. Heavy
custodyoutsideGod2; oldgoalbinaryprefix/priorledgerfields/frontierv23/C++/
custom135IDs/rules/defaultsallunchanged.

Unique report20261012-tw-native-catalog-material-helper-source-348; C++changes0,
newcoveredknownmethod1 ininspectedfrontier, nativeopcode/format/parser/phase/
source-route/fullbidirectionalroutecredits0. TW156C2S/252S2C/world74=50partial/
11control/13unconnected;CN156C2S/280phase/253lengthseparateunchanged. Parser67.6%
notcompletion, whole/TWpercent+denominatornull. Initialgenuinecommonbank/full25/
full1215/freshclientfull50/native5D/allvariants/transfer/postbattle/acceptance
OPEN. FullTWfirst/CN/fourWS/common64/coin99999999999/qualifiedstack99/nativelevels/
saves/frozen/fonts/conversiongoalactive. PHASE1 no compiler/build/tests/runtime/
native/API/CRT/VM/emulator/parser/codec/SQL/importer/migrate/activate/deploy.


## Round349 actual item helper outputs and primary UI boundary (2026-10-12)

Previous348 source progress publisheda5e3a01603e77f9707efaaadcd37722dd7729eca,
exactHEADnotification38270660071success; immutable receipt/custody remain.
Actual49B850 outputs now qualify two known helpers within audited opaque frontier:
49B72072B/18sites/2RET0C;49B77059B/18sites/2RET8. First readsWORD116/storesout1,
then reloadsout2pointer/readsWORD118/storesout2; genericalias mustpreserveorder.
Missinglookup WORD0041/FFFF. Actualcaller usesdistinctstackWORDs/signextension.
EAXmixedpointer/field oroutputpointer, notstatus. Second BYTE11Bbit0→NEGCF/SBB/
AND29/INC→WORD1or30; null→1. Nativeformatterthreshold notserverstackability,
acquisitionorqualifiedcommon99. Known459A60 acceptsunsignedlowWORD0..32599,
key0inclusive; highbitsmasked; currentpopulatedrecord/allocation/loadconditions
notproved. Generic396records/key/rowcount/token5 distinctfromProgramMsglabels.

Primaryknown5068C0112B/36sites/4closedbranches/soleRET16 hasno directobject/
queuewrites; only41EA00delegate remainsopaque. ActualthisU+E2170. Widgetformal1
onlysignedlowWORD used:nonnegativeg→offset10760*g;groupWORD818nonzero required.
No maximumgroup/allocationextentguard. FullslotDWORD loadedESI, signedSI<106
indexes100*signExtend16(SI); calleeownnegativeguard absent, actualparentDI0..49
qualifiesselectedpaths. Byte8B8nonzero needed. SlotfullESI stillforwardedchild.
MOVAXhandleWORD81C retainscomputedgroupoffsethigh16; childECX=this8, actualargs
(offsetHigh16|handleWORD,originalfullslot,fullformal2,fullformal4). Formal2/4
positiveparentMOVSXoutputs orclear31/-1; nofullchainhighbitirrelevanceclaim.
KnownhistoricalUIcontinuation gets0methodcredit; no nativeauthority/policyadded.

Twoexternalpackages48members101585B individuallychecked; overlappingpriorcustody
isnotuniquenativecoverage. FourpublicLF exactsuccessful capture/custody stages,
none rerun; discoveryfailuresretained. Oldgoalbinaryprefix/priorledgerfields/
frontierv23/custom135/C++/config/rulesunchanged. Newcoveredknownhelpers2/131B
boundedfrontieronly; opcode/format/parser/phase/handler/source/fullroutecredits0.
Unique report20261012-tw-native-item-helper-output-ui-source-349. TW156C2S/
252S2C/world74=50partial11control13unconnected;CN156C2S/280phase/253length
separateunchanged; parser67.6%notcompletion; whole/TWdenominatorpercentnull.
41EA00/5077C0effects/currentwidget/catalog andgenuinecommonacquisition/full25/
full1215/freshfull50/native5D/transfer/postbattle/nativeacceptance OPEN. Full
TWfirst/CN/fourWS/common64/coin99999999999/qualifiedstack99/nativelevels/saves/
frozen/fonts/conversiongoalactive. PHASE1 no compiler/build/tests/runtime/native/
API/CRT/VM/emulator/parser/codec/SQL/importer/migrate/activate/deploy.


## Round350 actual UI direct writes and acquisition transaction seam (2026-10-12)

Previous349 source progress publishedcd81bbeffa13b014dc1b39481351828bc78face4,
exactHEADnotification38271579466success and immutable receipt. Authenticknown
41EA00 whole487B/132sites/17closedjumps/3RET16,9NOPpadding. HistoricUIchain
alreadylisted, newmethod/opcode/format/routecredits0. ActualQ=UIthis8 distinctU.
Formal1 lowAX<4096/maskFFFF own656stride; formal2 signedlowWORD<106 ownslot,
nonegativeguard, actualparent0..49 premise. Wholeformal1/2 celladdresses passed
41E710 sohigh16notgloballydiscarded. Formal3 lowCX<512 yetFULL5396stride;
actualparentMOVSXmetadataWORD/clear31 passinggate implies0..511/high16zero,
notgeneralDWORDcallers. Formal4fullsigned sign; directWORDactionstoreBEFORE
sign/childsuccess. TwofurtherconditionalDWORDstoreschildresultandpostchildfull
formal1cell toliveP/J projectionaddresses. Rereadsdistinct acrossopaquechildren,
no validpointer/currentUI/queue/rights/nativeacceptance inferred. Remaining
41E710/402C70/427160/4271E0/425C80 andpartialregisterforwardingeffectsOPEN.

Hosted37/85 CUSTOM0021/0022townreward scalar5569/count1 andpublicprogress/slot
receipt notgenuinecommondefinition/instance/acquisition/full20/25/native1215.
TownownBEGINIMMEDIATE/COMMIT vscommonautocommit/guardedissuer/privateouterstage
meansnestedorcallbacktwo-call adaptersrejectconstraints; sequentialcommitscan
splitdurablestate. Futureatomicownerseam needstruequalifiedtuplesupplier first.
Noobservationalcatalog/publicreceiptcanmintprivateauthority; noC++wrapperadded.
Source143=line notCUSTOM0143; actualstorageCUSTOM0092, custom135IDsunchanged.

Externalindividualcustody/seals andexactLFsuccesshelpersnotrerun. Oldgoalprefix/
priorledgerfields/frontierv23/C++/config/rules/savesunchanged. Unique report
20261012-tw-native-item-ui-acquisition-seam-source-350; C++changes0; allnewmethod/
opcode/format/parser/phase/handler/source/fullroutecredits0. TW156C2S/252S2C/
world74=50partial11control13unconnected;CN156C2S/280phase/253lengthseparate,
allcountdeltas0. Whole/TWdenominatorpercentnull; parser67.6%notcompletion.
Truecommonacquisition/full25/full1215/freshfull50/native5D/allvariants/transfer/
postbattle/fullrouteinventory/nativeacceptance OPEN. FullTWfirst/CN/fourWS/
common64/coin99999999999/qualifiedstack99/nativelevels/saves/frozen/fonts/
conversiongoalactive. PHASE1 no compiler/build/tests/runtime/native/API/CRT/VM/
emulator/parser/codec/gameDBSQL/importer/migrate/activate/deploy.


## Round351 actual UI output cells and blacklist same-owner source (2026-10-13)

Previous350 published7486b393c5e87a95f57c779d517e2b4727dcc663 with exactHEAD
notification38272510428success. Authentic known41E710162B/57sites/4branches/
2RET20/noCALL;14padding. ActualoutC completeDWORD overwrites handle cell,
outD BYTE overwrites slotlow8 retainingupper24 withoutoldread. OptionaloutE
skippedactualformal5zero. Subsequentframe/descriptor/global585BD8rereads and
genericalias effects retained; selecteddistinctvalidstackpremises only. Signed
actioncount uppergate lacksnegativecheck outsideactualpositiveparent. Return
resource/descriptoraddress notBool/right; actualallocations/currentglobal and
otherdescendantsOPEN. Historicalmethodalreadyknown/newmethodcredit0.

ActualCUSTOM0096 TW C89/C8A add/remove retainnativeA5logical21/A4logical5,
capturedCP950/identity/rowallocator/max10active4096lifetime/135customIDs. Private
move-onlytransaction ownsactualbefore/after/row/wire/changed beforeCOMMIT;
sharedimmutablealiases noaftercommitcopy/reobserve. Fixedtotalchanges/autocommit
guard acrossafter/roots/material/finalroots protectsactualcompleteafter.
Nooporiginalreply/nofanout; validrejectemptyreplycontinues; noSQLretryrollback
afterdurablecommit. Arbitrarycommit/finalize observers contract stillbounded.

NewprivateownTickNormalInit/Writtenrecipienthandle hasactualgameowner guards,
immutable/atomicstrandchecks(no bareIDs), synchronizedrevoke/FIFOinsert/Queued,
RAIIfailures andsaturatingepoch. Generic sender/FIFO/async/originalresponse exact.
Mainpreownsstrongpeers/copiedsource/pendingnodes21B beforeSQL; actualchange to
idle-readysameowner exactbefore/handle only. PendingQueuedprogressrefindsall
identities/current. SenderafterSUBMITTEDreply; noWritten/nativeACK. Mismatch
permanentlydisablesincarnation. Actualpending senderhazard closesBEFOREnextSQL;
pendingpeerchains unsupportedretireclose. Plainineligible peersdisabledwithout
indiscriminateclose. Oldcontrol/re-ready/disconnect/stop/unwindrevoke before
borrowedowners. OnlysuccessfulownTickrecaptures. Allvariants/pendinglossless/
transfers/postbattle/nativeadoptionOPEN.

SevenexistingC++filesmodified, newfiles0; twoactualboundedconnectedsourcebranches
(A5add/A4removepeerpush), no newopcode/format/parser/phase/handler/fullroute.
Fiveupstreamseals/exactinverse/independentstaticreview andsuccessfulLFhelpers
preservedwithoutreexecution. InitialApphelperfailuresno trackedmutation and
reviewcorrectioncandidatehistory retainedadditive. Oldgoalprefix/priorledger/
frontierv23/config/customIDs/saves exact. Unique report
20261013-tw-native-item-ui-blacklist-owner-source-351. TW156C2S/252S2C/world74=
50partial11control13unconnected; CN156C2S/280phase/253length separate; existing
frontier/countdeltas0. Whole/TWdenominatorpercentnull/parser67.6%notcompletion.
Genuinecommonacquisition/full25/full1215/freshfull50/native5D/allvariants/
fullTW-CN-fourWS/nativeacceptanceOPEN. FullTWfirst/common64/coin99999999999/
qualifiedstack99/nativelevels/saves/frozen/fonts/conversiongoalactive. PHASE1 no
compiler/build/tests/runtime/native/API/CRT/VM/emulator/parser/codec/gameDBSQL/
importer/migrate/activate/deploy.


## Round352 row alias/material custody and ordered blacklist source (2026-10-13)

Previous35131d79bad16484d0a2021a938cb1a99b58231ba14 published with exactHEAD
notification38275802935success. Actual498D30 getter/514AC0 alias reader/514890
hotkey parent retain776whole+214explicitpartial=990codeB348sites/data0.
Getter signedWORD0..37/keynonzero/no count; control+20 canonicalU affinity
unproved. Alias loop dynamic bank/key/count; finaluncheckedESI; general30..37
counter29 mismatch. Writes other-control fields only. Actual518E50 FOUR stack
args5,second5156E0EAX,1,&control44C; numeric5 notwire. Candidatebulk4CA158 OUT
to866E8+24slot not8560C.318literal/102materialization candidates/0directprefix
stores are scoped mappedphysicalintersection discoveries; omittedoriginalPE
.imprec11776B separate rawliteral0 cannot prove absence. PrefixwriterOPEN.

ActualCUSTOM0069 trade conserves preexisting privatelegacy20/origin through
PreparePlan/pairedCAS/transfer/receipt/readback/COMMIT, no firstcommonissuer.
Pre-overlay instance sources explicit syntheticfixtures; importer396definitions
instances_created0 not acquisition. Genuine sameeventfull25/opaqueWORD+20/
commondefinition/globalstableinstance/acquisition/full50/DA/full1215 OPEN.
Independent fullnative5DACKbyte/timing/index/pending issuer stillOPEN.

One existingApp changes; relatedsixcore/Session exact. Four newconditional
sourcevariants PeerPriorPendingA5/A4 and SenderPriorIncomingPendingA5/A4.
PureprivatechainCurrent, preSQLstrongpeers/21Bnodes and actualtypedbefore/after;
successfulsamegame/sameconcreteStrand post precedes tail/endpointpublication.
Map endpoint newestOrderedSubmitted notQueued/Written/nativeACK. AllQueued
clearsattemptlist withoutendpointadvance. Cap256 actualpeerattempts reflects
localmax_writes; no pernodesnapshots/fictitiousownreplynodes/unboundedsender
retention. OwnNormalInit/TLSqualifies senderpending and fanout; copiedfacade
no livechainprogress. Noop/rejectoriginalsemantics exact; actualmissedchanged
edge closes onlyoldpendinghazard. No postCOMMITSQLretry/rollback. Ownreply
appended beforeendpointadvance, SubmittednotACK. Outerfailure/finalvalidation/
terminalpost/contextabort/allvariants/transfer/postbattle/adoption remainOPEN.

Four upstreamseals, exactinverse and separatefinalcanonicalreview; fourteen
successfulLFhelpers copiedexactwithoutreexecution. Failednative/material
helpers/partialcuts/corrections additive. PriorGoalprefix/ledger/frontierv23/
config/135customIDs exact. Newmethod/opcode/format/parser/handler/phase/fullroute
credits0/globalcountdeltas0. TW156C2S252S2Cworld74=50partial11control13open;
CN156C2S280phase253length distinct. Whole/TWdenominatorpercentnull; parser67.6%
notcompletion. Unique report20261013-tw-native-item-row-alias-blacklist-chain-source-352.
FullTWfirst/CN/fourWS/common64/coin99999999999/stack99/nativelevels/saves/frozen/
fonts/conversiongoalactive. PHASE1 no compiler/build/tests/runtime/native/API/
CRT/VM/emulator/parser/codec/gameDBSQL/importer/migrate/activate/deploy.


## Round353 native computed banks and original response custody (2026-10-13)

Previous352618eb9cbce52632f984b45f7409407a4e465c234 published; exactHEAD
notification38278789301success. Genuine sixwholebodies1418B+twoleaves12B+
fourpartials114B=1544codeB454sites/24dataB, mapped/PEequal.177rawhits/201
unalignedcandidates are scopeddiscovery notglobalabsence.497290 actual2A
6payload bytes allinitialized/no newcredit.49E440 full24OUT toaux866E8 then
prefix1=live855F0slot; postqueue reread lacksrepeatguard.49DF10 incoming50
full24topeeraux867A8 signedbody1index0..7. Neither bank iscanonical8560C.
Rollback/close directauxcount/key/purse/UI effects do notrecovercanonicalprefix.
Opaquechildren/affinity/computedindirectbulk writersOPEN. Existing5DAuthority
fullBYTE required; goldenonlyseed/loginfalse, OriginalServer2E/full5DissuerOPEN.

ThreeexistingCppchange; repository/service/config/135customIDs frozen/defaultoff.
Fourconditional custodybranches committedA5/A4 andnonemptytombstone/active
replay. ActualSessionINIT/thread/epoch/phase/battle/TLS receipt independent of
WorldResponseWrite; ownEntryWritten notrequired, peerWrittenstillrequired.
SamecallbackDatareuse/exactrefind identity; pureCurrent checksevenwithnopeer
nodes. Actualframedcomponentregistration precedesreceipt/snapshot/cursor.
Finalvalidwire orderedframeboundary match+privateguard+FIFO+Queued underSync;
write/log/resume/fail outside. ObservedpushbeforebyteDebit, legacyELSEexact.
RAII/drop/reject/unwind/postthrow failure retiresepoch andatomiccloserequest.
PostCOMMITcomponentallocation canfail/noSQLretryrollback. Empty/unarmed and
noINIT replay historical/notnewcustody. QueuedlocalFIFO notWritten/nativeACK.
Generalundestroyedcontextabort/control/transfer/postbattle/allvariants OPEN.

Fiveupstreamseals individuallyverified; exactthreeCppinverses; Sessionfailed
prewritehelpers/506candidate/emptyindexdraft+correction retainedadditive.
SuccessfulLFhelpers copiedexactwithoutreexecution; finalcanonicalreview.
PriorGoalbinaryprefix/ledgerfields/frontierv23 exact. Newnative method/opcode/
format/parser/handler/phase/fullroutecredits0/globaldeltas0. TW156/252/world74
=50partial11control13unconnected; CN156/280phase/253length separate.
Whole/TWdenominatorpercentnull/parser67.6% notcompletion. Unique report
20261013-tw-native-item-writer-original-response-source-353. FullTWfirst/CN/
fourWS/common64/coin99999999999/stack99/nativelevels/saves/frozen/fonts/conversion
active. PHASE1 nocompiler/build/tests/runtime/native/API/CRT/VM/emulator/parser/
codec/gameDBSQL/importer/migration/activation/deploy.


## Round354 native save/restore, authority frontier and options (2026-10-13)

Previous353b6c0ec2d88c7c3f23dc2050ed21abe3c17e09650 published with exactHEAD
notification38281892043success. Actual3whole1076B+outerpartial40B=1116codeB/
285sites/data0, mapped149c/PE5fcfequal.23rawREPnear-literal candidates scoped;
3/11actualalignedcallers.49C638 full20 OUT toUI85AD4;49C770 signedDWORDkeygate,
unsignedsavedslot0..255/no50guard, lowkey/countonly restore thensignedclamp and
opaquechildren. No full20copyback/directprefixstore/globalpurity. Outermatching
canonicalUaffinityconditional.1215 serverwitness1200cache+DA15 notincomingpacket.
Canonicalprefix/computedindirect/issuer OPEN, knownmethodsnotrecredited.

Finite27immutableHEADsources/12cuts rankactualPK69/35 backend lackingtruepair/
fullmaterial/seed/basiccoeff-order/returnowner; A3/CB lacksactualwindowCloseOwner;
6Blane0 readset/PFD candidate notfoodauthority/effect/consume/reply. Fiveopcode
subset of13unconnected/10pending, notwholeinventory. No fakefactory/rules.

TwoCppApp/OwnedClientOptions change; Session/protocol/config/core/custom135
frozen. DefaultoffCUSTOM0100 transientuntrustedWORD, notpermission/chat/game
rules. Fourqualifiedresponsecustodyvariants C1Dword/B1sel7/B1sel8/knownwordreplay.
ActualwrittenINIT+own353callback beforeprogress, pureCurrent/refinds; oldFailed
blocks, PendingonlysameData, QueuedknownWORDmaycrossgenuinewrittennewINIT without
callingoldINITcurrent/ACK. Nextstate/framedS1B/merged staged, expectbeforeCAS/
swap; componentcopyitselfmayallocate. ready/disconnectmarkerase neverrevoke
sharedData. Actuallaterreject/phasechange/finalinvalid/drop/postfailure failclosed
asauthorized, no mixedtransferacceptance/rebase/nativeadoption claim. Queuedlocal
FIFO notWritten/nativeACK; generalundestroyedcontextabort OPEN. Unobserved
generic/frozenchat bytebehavior exact, noSQL inoptions path.

Fiveupstreamseals+twoexactCppinverse+independentreview, separatefinalcanonical.
NineexactsuccessfulLFcopieswithoutreexecution. Failedprewriteoptionshelper,
authorityApp-race/cut206→202 partials/corrections additive. Goalold603907binary
prefix/priorledgerfields/frontierv23 exact. Newnative method/opcode/format/parser/
handler/phase/fullroute0/globaldeltas0. TW156/252/world74=50partial11control13open;
CN156/280phase/253length separate. Whole/TWdenominatorpercentnull/parser67.6%
notcompletion. Unique report20261013-tw-native-world-control-authority-frontier-source-354.
FullTWfirst/CN/fourWS/common64/coin99999999999/stack99/nativelevels/saves/frozen/
fonts/conversion active. PHASE1 nocompiler/build/tests/runtime/native/API/CRT/VM/
emulator/parser/codec/resource/gameDBSQL/importer/migrate/activate/deploy.


## Round355 native child lineage and actual party permission custody (2026-10-13)

Previous354b934e539e9d0cb279e2d6b58678afdb7b555dcf9 published with exactHEAD
notification38283720696success. Actualwhole49D2E0..49D365133B/42sites/data0
resets savedUI85AC0..85AE7, notcanonical8560D..F. Sameobject child lineage,
mapped149c/PE5fcfequal; DF0/span/faultfree premises. Prior142members476077B
individuallyunchanged. Existing49B850 no demonstrated rowdestination forwarded;
23rawREPwindows+refinements discoveryonly, notwholewritercensus/globalabsence.
Canonicalprefix/full25/full1215/acquisition/issuer OPEN, no methodcredit.

Actualmaterial C24/jointmovement alreadyhosted; earliestmissing genuine
definition-instance-acquisition/full25/cache50x24+DA owner BEFOREmint; syntactic
validity/historical396 is notauthority. Full5D externalAuthority mandatory.
PKpairedterminal/preparedfutureINIT/completeReturnScene remains preparationonly;
no coupled visibilitymerge/socketwrite/liveINIT/markerunlock/inputrelease yet.
No fakefactory/rebase/emptycache or nativeformula added.

ThreeCpp App/Directory/Service change; Session/protocol/config/core/custom135
frozen/defaultoffCUSTOM0097/98/101. ActualC90->AB privateowncallback receipt
captured beforeprogress, exactframedAB expect BEFOREstateCAS; state/frame/merged
alreadyallocated, componentregistrationitselfmayallocate. Detail/Presentation
share actual353Data withoptions/blacklist; owningData cannot preventRAIIfailure.
C91 ONLY currentQueued oldDetail grants privateconsentpermission, bothpreaction
and afterallobservers; Pending (includingnewC90+C91samecallback), Failed/absent/
staleepoch denied. Queued localfinalvalidFIFO notWritten/delivery/nativeACK.
NewC90oldpermissionretirement unchanged; Pendingpresentation can remaincurrent
provisional, missing/Failed/currentfalse invalidates watcherreadset. Finalretained
AB fence qualifies privatecurrent receipt. ready/disconnect/windowrelease never
revokes sharedData. ArmedactualABlaterreject/phase/drop/postfailure failsclosed;
unobservedgeneric/frozenchat bytesexact. C91peerpreview transport/nativeadoption,
allparty variants/mixedtransfer/postbattle/universalcontextabort stillOPEN.

Fiveupstreamseals+threeexactCppinverses+independentsemanticreview+finalcanonical
review. FailedprewriteLF/CRLF literal draft/correction retained additive, no tracked
mutation onfailure. TenexactsuccessfulLFhelpers copiedwithoutreexecution.
Oldgoalbinaryprefix/priorledgerfields/frontierv23 exact. Twoconditionalsource
custody/admissionbranches, native method/opcode/format/parser/handler/phase/
fullroute0/globaldeltas0. TW156/252/world74=50partial11control13unconnected;
CN156/280phase/253length separate. Whole/TWdenominatorpercentnull; parser67.6%
notcompletion. Unique report20261013-tw-native-route-authority-source-355.
FullTWfirst/CN/fourWS/common64/coin99999999999/stack99/nativelevels/saves/frozen/
fonts/conversion active. PHASE1 nocompiler/build/tests/runtime/native/API/CRT/VM/
emulator/parser/codec/resource/gameDBSQL/importer/migrate/activate/deploy.


## Round356 actual C91 peer preview transport custody (2026-10-13)

Previous3556c2d3412e22316d1537323bc13e449f87ddfd03a exactHEAD notification
38285659697 success. Native432BB0..432C3A138B/49sites/RET12/two branches
forwards unsignedfullBYTE231 from known467BBA debug path to opaque formatter/
renderer with known3B `%d` literal. Known5D46930A fullBYTE store/unconditional
ring pop and4678D8 entry reset referenced only. Prior137members4737817B and
27 mapped/physical spans unchanged. Twelve raw literal matches/thirteen windows
discovery only; no server ACK value/timing/permission issuer or global absence.

Actual hosted trade2A/both2C repo.commit251..308 is a two-owner legacy seam;
common stage_replace139..145 permanently registers incoming global identities.
Two one-owner replaces cannot transfer an existing ID without forbidden remint
and split settlement. Genuine donor common instance/definition/original
acquisition/full25/cache50x24+DA must qualify before one atomic two-owner common/
witness/legacy settlement. No donor supplier/fake factory/SQL implementation.

ThreeexistingCpp App/SessionH/CPP plusnew headeronly OwnedPartyPreviewTransport.
Old capture retains owncallback TLS check; explicit game capture uses actual
private Written INIT/thread/exact Session/epoch and existing transport guards.
Actual C91 courier owns full sources/exact strong peers/fresh handles/complete
projections/registry node beforeCAS, bounded config.max_sessions. Final pure
freshhandle/source fence after all observers plus355oldABQueued admission.
Immediately afterDirectoryCAS markcommitted noexcept beforeNativeParty/wire move.
Uncommitted cancel onlyfreshrevoke/release nopeerclose; after both commits actual
send_normal_world_records attempts retained. Send/post mayallocate/throw then
freshrevoke+closeall exact heldflight sources; no rollback/retry/consentduplicate.
Existing50msScheduler settles Pending/current/Failed; no new timer/timeout.
AllcurrentQueued retires withoutrevoke, queuedWrite ownsData; notWritten/ACK.
Close/stale detected via privatecurrent and nextsettle/stop, no new direct
disconnect registryhook. stop/destructor ownsunfinished beforeScheduler/network.
CallerfinaloriginalC91callback rejection remainsOPEN; emptyownreply no fakeFIFO
ticket. Nativeadoption/allpartyvariants/mixedtransfer/postbattle OPEN.

Defaultoff owned_party_directory_enabled unchanged; NativeParty/C90permission/
Directory/Service/protocol/config/storage/custom135/frozenchat/Scheduler exact.
Fourfinalpins/threeexistingexactinverses/newheaderadditive containmentinverse,
fiveupstreamseals plus independentsemantic and canonical current reviews.
SuccessfulLFhelpers copiedwithoutreexecution; failedproposalcaptures immutable.
Goalbinaryprefix/priorledgerfields/frontierv23 exact; R exactlytwoLF keylines.
Oneconditional C91peer-projection custody branch; nativeopcode/format/method/
parser/handler/phase/fullroute0 and globalcountdeltas0. TW156/252/world74=
50partial11control13unconnected; CN156/280phase/253length separate. Whole/TW
denominatorpercentnull; parser67.6% notcompletion. Unique report
20261013-tw-native-party-preview-transport-source-356. FullTWfirst/CN/fourWS/
common64/coin99999999999/stack99/nativelevels/saves/frozen/fonts/conversion active.
PHASE1 nocompiler/build/tests/runtime/native/API/CRT/VM/emulator/parser/codec/
resource/gameDBSQL/import/migrate/activate/deploy.


## Round357 actual whole-callback admission before party preview (2026-10-13)

Previous356b5a2afd1364c50613525f07757ba31350dad9882 exactHEAD notification
38288004028 success. Owner requests stop at this round end: finish357 publication/
receipt then pause fullgoal; no358. Fullobjective unchanged, no completionclaim.

New distinct NormalWorldCallbackAdmission Pending/Admitted/Failed uses actualown
world_records TLS/private Written INIT/exact Session/Sync epoch. Sameactualcallback
Data shared by allC91prefixflights; retainedData cannotprevent separateprivate
Pending Attempt failure on scope/unhanded/postthrow/drop. Real wholecallback result
has_value includesempty; empty no frame/dummyWrite/FIFOmarker. Existing normal
response components/raw response exactwire/finalvalidwholeprefix retained. Final
gameexceptions/poison rejectcapture; strandsource guarded originalnonemptyFIFO
insertion, then allthrowinglogger/resume work before finalprivateSync Admitted.
Admitted onlyactualwholecallback admission, not Queued(empty)/Written/nativeACK.

FourexistingCpp files with exactwholeinverses, no newCpp. Actualdirectory twoReading
reentries rejectstoredsameadmission even otherSession/caughtobserver; featurecatch
aftercommittedC91 rejectswhole admission. Existing355oldABQueued/privatepermission
and356freshrecipient/fullprivate fences remain. Owningregistry preCAS, mark immediately
afteractualDirectoryCAS, noalloc/noexcept handoff Deferred aftertwoModelcommits.
Nopeerwrite beforeAdmitted/current. Existing50msScheduler waitsPending no timeout,
Failed/stale revokesfresh andclosesexactstrongsources, Admitted submitsonce then
existingPending/Failed/allQueued settling. SuccessfulQueued retirewithoutrevoke.
All samecallbackprefixes fail together onlaternull/throw/outerreject/poison/epoch/
phase/close/postdrop; no rollback/retry/rebase/SQL. Retainedrole/position/HUD only
preparation snapshots; pureSessionchecks notliveDB/modelrefresh. Generalexecutor
convergence/Schedulerrearm/contextabort/nativeadoption/fullvariants remainOPEN.

Actualupstream20-byte private-clone seed writers explicit synthetic/CUSTOM_TEST_NOT_NATIVE;
NATIVE_CAPTURE_VERIFIED contractlabels/catalog396/hexwidth not acquisition evidence.
Common/witness constructors don't populate genuine tuple; normalC24 consumes existing
sameDB beforetuple. Genuine donor instance/definition/originalacquisition/full25/
full50cache+DA missing BEFOREseed/mint, then oneatomic twoownercommon/witness/legacy
settlement; no fakefactory/grant/import/newSQL. Nativebounded32historicalrowLEA
candidates/sevenraw windows discoveryonly; selectedrowptrforwards known49B850 or
outwardfull20 savedUI85AD4. Newwhole/code/data/qualifiedsites0, no globalabsence.
Prior355N70/77600+356N54/92377 individuallyunchanged; canonicalprefix/full25/1215OPEN.

Fiveupstreamseals/independentfourcurrentsemanticreview/finalcanonicalreview;
successfulLFhelpers copiedwithoutreexecution, failures/partials additive.
Defaultoffconfig/protocol/custom135/NativeParty/Directory/Service/Scheduler/frozenchat
exact. Oldgoalbinaryprefix/priorledgerfields/frontierv23 exact; R twoLFkeylines/K3.
Oneconditional actualC91wholecallback-admitted peertransportbranch; nativeopcode/
format/method/parser/handler/phase/fullroute0/globalcountdeltas0. TW156/252/world74=
50partial11control13unconnected; CN156/280phase/253length separate. Whole/TWpercent
denominatornull; parser67.6% notcompletion. Unique report
20261013-tw-native-party-callback-admission-source-357. FullTWfirst/CN/fourWS/common64/
coin99999999999/stack99/nativelevels/saves/frozen/fonts/conversion preserved.
PHASE1 nocompiler/build/tests/runtime/native/API/CRT/VM/emulator/parser/codec/resource/
gameDBSQL/import/migrate/activate/deploy. Ownerrequestedpause applies afterreceipt.


## Round358 actual delivered party lifecycle and common skills priority (2026-10-13)

Previous35781566a8a7efb75e7ea768bb5f767e1e5f1ad9324 exactHEAD notification
38290924662 success. Owner '繼續工作' resumes after applied357pause; historical
stop/receipt remains unchanged. Goal active, complete TW-first/CN/fourWS/common64/
coin99999999999/stack99/nativelevels/saves/frozen/fonts/conversion unchanged.

Actual delivered on_disconnect and Directory world_ready first statements retire
matching courier flights on recorded game thread/exactstrongSession object.
Fresh-only revoke and committed-only exactheldpeer close; exactnode capacity/erase
once, no ID/successor/retry/rollback/newtimer. Uncommitted Prepared retains retired
Data currentfalse and cannot double-decrement/close. Already allQueued nodesabsent
so queuedWrite Data not revoked. Scan noallocation; existingclose post mayallocate
under existingcontainedcatch. Actual Sessiontail retiresnormaloutput before game
ready; close/fail beforegame disconnect. This closes deliveredhook seam only:
finish logger/commoncleanup beforeApp/postdrop/Schedulerrearm/context convergence
stillOPEN. TwoexistingCpp exactwholeinverses to81566, allotherSession/Scheduler/
models/config/protocol/storage/native135/frozenchat byteexact; defaultoff noactivation.

Authentic49DE50 group5/base866E8 andgroup7/base867A8 directchild49E0C0..49E19D
221B/73sites/RET8/fivebranches; selectedprior14ranges nooverlap, qualified1body
notglobalnovelty. Eightaux24B rows rereadkeys aroundopaquechildren, no direct
nonstackstore/canonicalprefix readwrite. Nativecanonicalfull25/1215/acquisition/
permission/grant/fullroute0; opaquechild effectsunknown.

Actualhosted2A/both2C legacycommit251..308 cannotreplace twoowners through incoming
singleowner remint. Future sameDBdetachcells/aliases thenreattach preservesglobalID.
Genuine sameeventdonor/full25/both actualdeliveryreceipts and completeafter1215 source
missing; nofactory/newSQL/settlementcredit.

Owner newpriority requires ONEcommon skillcore/catalog allskills, TWTraditional
skillChinese primary, actualclientformulas primary and playerguides secondary.
Poison ownerrule target CURRENT MAXIMUM HP /10. Nativeidentity/wire/clientgate
differences belongto adapters; unequalrows don'tauthorize separateregional gameplay.
Differentabilities samerawkey cannotoverwrite. Coremerge/tickstatus notimplemented
by thisround's existingcourier change.

Three actualraw plain112660B BIN sources: originalTW448(121/129/87/111)7676,
installedTW453(126/129/87/111)3adc, CN453(125/130/87/111)857. Original448 fully
unchangedinstalled, fiveadditions are4reserved0/122..125 +CUSTOM0058 0/126.
Originalshared448 physicaltail equal445/different3(0/95,1/83,1/129); notformulas.
Installedshared452/union454 withTWonly0/126/CNonly1/130; nofake453nativeclaim.
Common64Battle hasHP/maxHP butnoactualpoisonstatus/turnexecutor/checkpointfields.
Nextqualified commonnativebinding/effectdescriptor/turnboundary/stagedmaxHPdiv10/
checkpoint publication required; noarbitrarytimer/unusedhelper/fakeformula/grant.

Sevenupstreamseals +finalcanonicalreview,15successfulLFcopiedhelpers notrerun,
failedpartials additive. Oldgoalbinaryprefix/priorledgerfields/frontierv23 exact;
RexacttwoLF/K3. Twoconditional lifecyclebranches/nativebody1; nativeopcode/format/
parser/handler/phase/fullroute0/globaldeltas0. TW156/252/world74=50partial11control
13unconnected; CN156/280phase/253length separate. Whole/TWdenominatorpercentnull;
parser67.6% notcompletion. Unique report20261013-tw-native-party-lifetime-source-358.
PHASE1 no compiler/build/tests/runtime/native/API/CRT/VM/emulator/productparser/
codec/resource decoder/gameDBSQL/import/migrate/activate/deploy. Goalactive.


## Round359 actual common skill definition consumers (2026-10-13)

Previous3588520e6330e32631df630fecc46204f040a6f911a exact-head notification
38352661594 success; prior root plus8 packages1197members72,070,834B individually
verified. Owner resumed goalactive. TW-first/CN/fourWS/common64/coin99999999999/
stack99/nativelevels/saves/frozen/fonts/conversion and PHASE1 limits preserved.

ONE shared owning definition carries full110 regional profiles, source/key/
ordinal/offset/hash, separate requested_native and chosen parameter base.
9 existing Cpp/3 new files: NativeSkillSource move preserves original record,
SharedSkillDefinition pure composition907 exactrawpins, MainLua actual last
optionalprovider retained ininitial/rebuiltVm, CNprivate actualselection owning
Facts intoexistingapply/delivery. Oldnative getter/equality/lookup and original
CN453 private gate remain. No shared chosenTW record replaces CN entitlement.

Owner complete-source preference: borrowCNfull0/122..125 for confirmedTWreserves,
CN1/83 for pinnedemptyTW; TWcomplete0/95 and1/129 conflictbase, retainCN originals.
This composition CUSTOM0138 notnativeformula/permission; AGENTS binaryprefix
and135 oldcustom entries preserved, new136th/maxID138. TWTraditional nonempty
names primary; confirmedreserve usesactualCNname/short converted separately.
Bounded2..1F/20..3D excludesWORD3E, notnativeUIwidth. 907 arrays99,770B exact,
publicdigest flag/enum cannot promote mismatchingraw; inputregion guard explicit.
Owner allows futureCN CUSTOM0058瞬影126 and0059牛踏150 commonrules/learnedrights,
separatequalifiedCNwire/effects. OriginalCN857453 notforged; noCNcustomprofile
orcastactivation thisround. Preserve TWcastershadow/direction/clones/fourphases.

ActualBIN originalTW4487676/installedTW4533adc/CN453857; original448 unchanged,
4TWreserves+custom126 additions. Original448shared445equalphysical50/3paramdiff
sameIDs0/95,1/83,1/129. Installed452shared/454union; TWonly0/126,CNonly1/130.
Equalrecordtail isnot equalformula/learnedpermission/activeability.

CN knownS83type3 selectedwhole54C5101699B441sites/556D401713B574sites/55E2F0
70B29sites=3482B1044sites. Parentunion239B67sites/overlap83 separate;175tableB
padding4 excluded. Actualbanklookup includes+4header. Source2/masks5,7/key11/
WORD9low16/markers13,14 preserved. 5634E0 only664B199site prefix; type3/type17
signedHP/mathtail563A3E OPEN; state5MOVSX notproof type3damage. PinnedinplacePE
no independentmappedmemorypair/newknownmethod credit. ActualTW/CN MPgate only
comparesWORD42/currentMP/B67; noMPdebit. HPdelta clampconsumer notdamageproducer.

Ownerpoison targetCURRENTMAXIMUMHP/10, actualstatus/turn/checkpoint stillOPEN.
No isolatedunusedhelper/arbitrarytimer/ordinaryattackreplacement. Clientactual
formulas priority, playerguides secondary. Futureactualcommon cast/debit/status
and CNcustomwire/effect integration remain; metadata branch notfullroute.

Source branches2(MainLua/CNselection), nativecredits/formulas/opcode/format/
parser/handler/phase/fullroute0; globaldeltas0. TW156C2S/252S2C/world74=50partial
11control13unconnected; CN156C2S/280phase/253length separatelycounted. Whole/TW
denominatorpercentnull; parser67.6% notcompletion. Canonicalreview/memberseals/
existingCppwholeinverses retained; successfulLFhelpers notrerun, failedprewrites
additive. Oldgoalbinaryprefix/priorledgerfields/frontierv23exact; RtwoLF/K3.
Unique report20261013-tw-cn-shared-skill-source-359 before rootseal/publication.
PHASE1 no compiler/build/tests/runtime/native/API/CRT/VM/emulator/productparser/
codec/resource decoder/gameDBSQL/import/migrate/activate/deploy. Goalactive.


## Round360 common owner skill definitions without native rows (2026-10-13)

Previous359a4ca93050ec0416325b3d83abf54552a9f244af3 exact-head notification
38361009768success. Priorroot+6packages1349members81,953,643B individuallyverified.
Baseline330/20,139,208B includes328canonical+L/F; extra27/152,572B actualowner/
learned/checkpoint/native dependencies. FailedwrongLua-path baselinepartial
retained; corrected gameplay/combat_health64 path capturedonce. Goalactive.

Actualcommongetter nowreturns owningformalCUSTOM0058 kind0/126 and0059 kind0/150
when BOTHoriginalTW448/CN453 rawrowsabsent. Source6existingCpp/new0, complete
inversea4ca; newOwnerSkillRule appendsSharedDefinition, directlyreferences existing
class key/power/cost/limit/designID/name; no duplicated300/1000/20/100 rules or
authorize/owned_action execution. Classesnames-only, methods/trials/clones/
realcastershadow/direction/fourphases exact. 907pintable784107B unchanged.
Absentrequested_native/profiles/chosen/nativeSourceText remainabsent, othermissing
keysnull; invalidselectors/corruptrowchecks original. Present unknownrawstatus/
qualification retained. Luaowner_rule/display_name ownvalues, TWTraditional,
falsegameplayauthority/native_source; no fakeNative110/Current/learnedgrant.
Versioned docs/integration/SHARED_SKILL_SERVER_SOURCE_V1.json pinsSource6,
source-only capability; CNcast/extendedprofile/encode/effects/runtimefalse.

Actual Appcustom savedbootstrap operatesexistingdiagnosticencounter only. Common
Battle oneMPcharge/checkpoint-beforepublish retained. Genuine savedreadset exists;
original448same149c SharedTaiwanOwnedDeitySkillSourceObservation notcustomissuer.
CNselection requiresactualoriginal453/listbank fullrawCurrent; nativekind0count125
rejects126/150. CN actualcustomsaved/actor/list/resource compatibility+real87event/
revision/flags+WorldOwner host required, notmanufacturedbydefinition metadata.

OriginalCN5634E0..563C19 complete1849B540sites/soleRET20h, table36B/literals20B
padding3/nextentry17B separately. 359prefix664exact+1185extension; knownmethodcredit0.
S83type03h/17h(decimal23) samearm; decimal17default. Formal5rawSI storedWORD
actor+28A+2BYTE239; signedMOVSX HP-labelled formatting under rawmarkers7/8 and
resource/state branches. No directHPadd/clamp/death/damageproducer or64client
proof. 42opaquechildren unexpanded; actual55709E→562510/readers remainnextsource.
CurrentPE582f in-place pinned, no mappedmemorypair/nativeexecution claim.

No poison status/turn/checkpoint source yet: ownercurrentMAXHP/10 preserved;
rounding/immunity/stack/timing/lethality OPEN. No timer/unusedhelper/sourceguess.
Clientformulas primary, guides secondary. No CNoriginal857453 fakeextension.
Main4899878/source3 handoff reference-only, peerfiles/scripts notmodified/run.

Native/authority/implementation/independentreview+canonicalseals individually
readback; 6Cppwholeinverses/oldmethods907pins/frozendependencies exact. Public
successfulLFsingleEOF captures notrerun, failedpartials/applyoriginal retained.
AGENTS/custom136 unchanged; oldG binaryprefix/RtwoLF-K3/Lparsedfields/Fexact.
Sourcebranches2 owner126/150 metadata; nativecredit/formula/opcode/format/parser/
handler/phase/fullroute0; globaldeltas0. TW156/252/world74=50partial11control
13unconnected, CN156/280phase/253length distinct. Whole/TWdenominatorpercentnull,
parser67.6% notcompletion. Unique report20261013-tw-cn-common-owner-skill-definition-source-360.
PHASE1 no compiler/build/tests/runtime/native/API/CRT/VM/productparser/codec/
resource execution/gameDBSQL/import/migrate/activate/deploy. Goalactive.


## Round361 — common owner skill action saved readset (2026-10-13)

CUSTOM-0139 connects the actual selected deity learned observation for both
kind0/126 CUSTOM-0058 and kind0/150 CUSTOM-0059 after authenticated complete
C35 selection. Actual Application forwards the typed readset to active and
terminal checkpoints and noncheckpoint resources/settlement writers, with
same-connection private full-row checks inside BEGIN IMMEDIATE before writes
and immediately before COMMIT. Owned canonical settlement replay version4
pins complete saved selection/deity/provenance/skill bytes. No saved requests
or schemas are rewritten. Ordinary/trial/revival/formulas/effect bodies stay
unchanged. Existing isolated nonpersistent owner casts are explicitly scoped.
Nested operations poison the action; removal is deferred to RAII cleanup.
Final memory-publication fence cannot undo an already successful COMMIT; the
existing synchronous no-reentry/no-send callback contract still applies.

Actual Application hosting remains the existing TW diagnostic encounter,
not a completed CN cast/list/actor/resource/87/effect pipeline. Original
CN453 remains unchanged and provides no fabricated126/150 rows or rights.
Server source capability is versioned in SHARED_SKILL_SERVER_SOURCE_V2.json.
Bounded CN562510 complete152B/46sites only maps modifiers and calls564A30;
80B table data, queuedHP/death/64-bit consumer child remains OPEN. Native
package19/67662 seal6347e4dfa8da5523bf4926a53d2b88773cc708bb9cb634188895d93acd16a824.

New actual source persistence branches4; complete bidirectional routes0;
native opcodes/method credit/formulas0. TW156C2S/252S2C, world74=50partial+
11control+13unconnected; CN156C2S/280phase/253supported lengths unchanged.
Whole route denominator/percentage unknown. PHASE1 only: no build/tests/
runtime/native/VM/codec/gameDBSQL/migration/activation/deployment. Goalactive.


## Round362 — actual common owner skill bootstrap/write custody (2026-10-13)

CUSTOM-0140 replaces actualApp two owned-skill booleans with ONE complete
saved deity roster for126/150; existing shared definition getter consumes
formal owner-rule key/design only, not raw native data or learned grants.
Keep original87/id/80 flags/order and finalvitals. Sameframe encoded once,
captured by actualSession WorldResponseWrite before realservice bind, then
returned through the same original world callback/FIFO. Typed fullroster
qualifier guards actualbinding/controller/keyset/private receipt/Session
around actualrepository observer with reentry poison/deferredremove. Fence
originaltuple before existing InBattle transition and freeze only its actual
result epoch, separate from cosmeticpose; no predicted increment or rebase.
Optedowned C35 requires localWritten/current plus361 fresh savedreadset/CAS.
Written is not nativeACK/cache/listadoption/turngrant or inputbarrier; Pending
earlyarrival/native scheduling acceptance remainsOPEN. No-afterCOMMIT rollback
is claimed. Ordinary/trial/revival packet/rule defaults and TW effects remain.

OriginalCN564A30..564C6D closes573codeB/166sites/29branches/6RET14h.
It consumes lowBYTE modifiers and updates actionstate/packedtarget arrays;
no ownqueuedHP28A/arithmetic/death/64-bit reader proved. Opaquechildren OPEN.
N36217/78839 seal908e600e85b79a696b2045997bfd786b1d2be0db6e5c25b6a1a3750db5bf000c.
ActualCNhost/actor/list/resources/native87/effects and fullTWnativeprimary/
secondary/control/auxiliary/roster providers remainOPEN; originalCN453 and
full907 compiled row pins unchanged. Sourcecontract shared-skills/source/3.

New actual ownedbootstrap sourcebranches2; completebidirectional routes0;
nativeopcode/methodcredit/formulas0. TW156C2S/252S2C, world74=50partial+
11control+13unconnected; CN156C2S/280phase/253supported lengths unchanged.
Whole denominator/percentage unknown. PHASE1 no compiler/build/tests/runtime/
native/API/CRT/VM/codec/gameDBSQL/migrate/activate/deploy. Goal active.


## Round363 — actual owned bootstrap input continuation (2026-10-13)

CUSTOM-0141 connects the actual126/150 bootstrap private response Attempt
to original input continuation: atomic game publication before handoff,
bounded raw bytes and old batch/read/deadline ownership; identical FIFO
full write plus successful old bookkeeping/current phase+epoch releases
once. Failure/drop/exception retires first, before fallible logging. Local
Written is not native ACK/cache/list adoption/turn grant or durable rollback.
Source contract shared-skills/source/4; 3existing C++files, 2existing owner
bootstrap branches, 0complete bidirectional routes/opcodes/native formulas.
TW156/252 world74=50partial+11control+13unconnected; CN156/280phase/253
supported lengths unchanged. CN actual host/list/resources/87/effects and
full native roster/control/auxiliary/queuedHP/poison status remain OPEN.
PHASE1 static only: no compiler/build/tests/runtime/native/VM/codec/gameDBSQL/
migrate/activate/deploy. Whole denominator/percentage unknown; goal active.


## Round364 - common definition at existing CN command handoff (2026-10-13)

CUSTOM-0142 retains original CN raw plus full common definition through actual
existing DataAuthority current/prepare/execute. Same sequential snapshot and
old Skill-prefix private holders retained across Append continuations; no
cross-source atomic CAS, learned/cost/actor/default-host or postCOMMIT rollback.
CN126/150 extended profile/resources/actual actor/list/87/commonhost remainOPEN.
Original553BC0 complete710B/190sites/RET24h plus actual54A6DF caller9formals
closed; opaque children/currentness remainOPEN. Localbodyclosure1, globalnew
method/opcode/fullroute/formula credit0. TW156/252 world74=50partial+11control+
13unconnected; CN156/280phase/253 supported unchanged. Sourcecontract source/5.
PHASE1 no build/tests/native/runtime/VM/codec/gameDBSQL/migrate/activate/deploy.
Owner requests stop after round364: finalize publication then pause goal; no
next round until resume. Whole denominator/percentage unknown.


## Round365 - common definition at existing TW command interface (2026-10-13)

Owner resumed; round364 stop is historical/revoked. CUSTOM-0143 adds owning
common Scope to actual existing TW qualification/current/action/after_action
handoff. Original digestchecked TW/issued/requested-native exact row and all
primary/secondary grammar/actor/list gates stay. Preaction same common value
reobserved, no rebase; after action only actual next receipt, no consumed old
catalog/grant reread or durable retry/rollback. Sequential cuts not atomic CAS.
Two source handoff branches; no actual default host/formula/opcode/fullroute
credit. TW156/252 world74=50partial+11control+13unconnected; CN156/280phase/253
supported unchanged. CN126/150 profile/resources/actor/learned/87/effects open.
Sourcecontract source/6; native slice facts retained in immutable N365 upstream.
PHASE1 no build/tests/native/runtime/API/VM/codec/gameDBSQL/migrate/activate/deploy.
Whole denominator/percentage unknown; full goal active.


## Round366 - Taiwan world skill C56 native ingress (2026-10-13)

Original logical7 preserves targetWORD, savedkind/id, live raw byte and
unwritten tail. Independently default-off request option passes real Others/
chat/host-plan/Application/Session to existing mandatory wholebatch and ordered
run callbacks. No C35 continuation/grant reuse, fallback action/reply or default
Main activation. One raw ingress branch, zero complete bidirectional routes,
zero formulas. Native234B=whole69+partial165,72sites; targetnamespace/rawbyte
writer/learned/current player selection/MP/effect/native replies remainOPEN.
Saved deity ownership cannot stand in for unproved player skill ownership.
TW parser75=50partial+11control+14unconnected; TW156/252 andCN156/280phase/253
unchanged. Whole denominator/percentage unknown. PHASE1 no build/tests/runtime/
native/API/VM/codec/gameDBSQL/migrate/activate/deploy. Owner requests continued
work; no new pause request. Sourcecontract source/7.


## Round367 - saved selected skill owning common definition (2026-10-13)

CUSTOM-0144 adds full owning common definition to existing saved selected-skill
Observation, alongside unchanged original TW and private learned readset/scope.
Exact requested_native equality and whole common Current around saved observers;
no rebase/atomicCAS/native grant/charge/action/Main host. Two C++ files, one
existing source enrichment, zero new Python/opcode/formula/full routes. Native
menu152B48sites (whole107/partial45) follows selected S30/31/34 roster; do not
invent independent player bank. Postopaque fresh reread and ignored failure
prevent atomic earlierMPgate-to-key claims. Actual C67 changes selection revision
and stales old restoration; future source needs final complete original response
receipt and committed selection, not an inner S31 or old entry epoch. Source/8
21pins; TW156/252/parser75=50partial+11control+14unconnected, CN156/280phase/253
unchanged. Whole denominator/percentage unknown. PHASE1 no build/tests/runtime/
native/API/VM/codec/gameDBSQL/migrate/activate/deploy. Capacity cleanup exact
duplicates5.04GB authorized but tool policy blocked even after consent; zero
deleted, roughly33.43GB still over30GB. Full goal remains active.


## Round368 - world skill self target source (2026-10-13)

CUSTOM-0145 keeps raw7 request/private actual normal INIT with existing owning
common/saved skill observation. Actual native context+28 publisher481833 gives
U8688C=R and actual self C56 follows R0; qualified2A writes masked14-bit handle.
No intervening mutation remains premise; zero new native bytes/methods/opcodes.
Actual own callback/InWorld/Written/current entry37 mask3FFF equals ready lease;
incoming C56 target is compared FULL WORD without masking or DBID truncation.
Old kind/id path unchanged. One Read, pure afterobserve attach, same retained
private INIT before/after current observers; sequential not atomic CAS. No Main
C56 action/MP/formula/selected-menu adoption/full reply/complete route credit.
Two existing C++ files, no new Python. Source/9 pins26. TW156/252/parser75 =
50partial+11control+14unconnected; CN156/280phase/253supported unchanged.
Whole denominator/percentage unknown; full goal active. No build/tests/runtime/
native/API/VM/codec/gameDBSQL/migrate/activate/deploy. Approved duplicate cleanup
still policy blocked, zero deleted; prior sources/history remain immutable.


## Round369 - selected deity full row commit and S31 handoff (2026-10-13)

CUSTOM-0146 fixes actual Main C67 helper stale-row reply and postCOMMIT const
wire copy. Private owning proof binds requested full row/raw19/raw29/ordered34,
revision/provenance/full64owner/repoorigin and before/afterselection inside the
actual reserved transaction. Owner/main/TEMP/reentry/noPendingBattle/fullrow/
selectionCAS/readback and intendedwritecount beforeCOMMIT, includingnoop;
allocateproof/preencodewire beforeCOMMIT then no-throw moves only. Legacy
repo method unchanged; actual Main helper API delegates typed path. Final whole
world response/Written/publication to skillprovider/nativeadoption remainOPEN;
one selected row is not the whole roster or cast authority. Four existing C++,
one actualsource branch improved, no newPython/opcode/formula/phasebinding/full
route. Source/10 pins28; TW156/252/parser75=50partial+11control+14unconnected,
CN156/280phase/253supported unchanged. Whole denominator/percentage unknown.
PHASE1 no build/tests/runtime/native/API/VM/codec/gameDBSQL/migrate/activate/
deploy. Full goal active; authorized cleanup still policyblocked/zero deleted.


## Round370 - actual mixed C67 whole-response publication (2026-10-14)

CUSTOM-0147 connects actual constructed mixed C67 singleton runs to SAME Context
game-owned source/helper/repository/catalog/presence. Default-off capability;
actual max_sessions and game-affine drains. Original C24/movement/tick order
and CurrentPoints retained; actual before/after commit chain and original S31
holders, LAST Application wrapper captures ONE entire original response/write/
inputhold. Ordered frame-boundary matching consumes separate identical frames.
Last actual commit publishes preallocated private candidate; exact private
map pointer/Session/full64owner/lease/phase/gen/normal INIT and Written/current
receipt/full savedrow/common definition fenced. Final v6 corrects observer gap:
full pure private/local tuple checked AFTER ready_lease as well as before,
including retained active presence registry and common readiness/delivery.
73 literal edits invert11 current files to exact originals/Git; v4 review and
v5 intermediate report historical, final v6 independent addendum. Source/11 pins29; no new Python.
One C67 branch improved; 2 opt-in unhosted phase associations C2S67/S2C31,
no new chain/opcode/formula/complete route. TW156/252/parser75=50partial+
11control+14unconnected, unhosted3chains/40bindings/36unique. CN156/280phase/
253supported/35chains/93bindings/71unique unchanged. Whole denominator/%null.
Default CLI and C56 action/nativeadoption/cast rights remain OPEN; local Written
is not client processing. Postcommit later aggregate allocation can fail:
retire/close, no SQL retry/rollback. Shared453/TWTraditional/native formula
priority and owner maxHPdiv10 poison rule retained. CNcustom126/150 adapter/
resources/effects remain qualified separately. PHASE1 no build/tests/runtime/
native/API/VM/codec/gameDBSQL/migrate/activate/deploy. Goal active; approved
duplicate cleanup still auto-review blocked, zero deleted/no alternate retry.


## Round371 - native WORLD35 flag event and bounded selector (2026-10-14)

Same149c S2C WORLD35 fixedlogical4/body3 key/kind/id: lengthcell4013F8->401264,
WORLDcell46B6A8->469FF1/call469FF9->4AA830. Complete receiver422B/111sites,
separate complete4A92D0 kind/id selector198B/72sites and actualpartialcaller18B/
5sites;638codeB/188sites plus8tabledataB. Old lengthleaf6B/S34/reset/menu refs
reused in place; no global whole-image or newmethod coverage claim. AtAA907
first matching bankpointer flag overwritten3, no append/count/pointer write;
S34 appends0. Opaque child and fresh-role affinity remain premises; armedDWORD
clearAA995 is not rowflag clear. Separate key-selector requiresdefBYTE67 and
rowflag&1, but no qualified actualcaller; known directselector/type2 shortcuts
do not establish universalflag gate forC56. Raw5 writer stillOPEN, bounded
literalcandidate zero is not globalabsence. Existing actualnormalprefix only
30/31/34, flags0; real authoritativeWORLD35 event/save/orderedpublication/current
issuer remainsmissing. Preserve shared453/TWTraditional and all current C++.
Source/12 exactsame29pins, CUSTOM registry unchanged, C++changes0/newPY0.
Frontierv24 adds independent-format-only35:16->17, unclassified110->109; no
reply/push/phasebinding/fullroute/formula/newopcode. TW156/252/parser75=
50partial+11control+14unconnected, unhosted3/40/36; CN156/280phase/253supported/
35chains/93bindings/71unique unchanged. Whole denominator/%null. C56default
Main/action/targets/cost/status/effects/persistence/replies/nativeadoption remain
OPEN. Goal active; PHASE1 no build/tests/runtime/native/API/VM/codec/gameDBSQL/
migrate/activate/deploy. No resources/save/account/EXE/frozen feature changes.


## Round372 - actual C28 retained presence observer fence (2026-10-14)

Two existing C++ ready lambdas in owneditem Selection and RequestOwner now
include pure retained_ready_current(fullLease), so existing before/finalafter
ready_lease/saved_position virtual observers recheck actual active registry.
Confirmed final load_position observer could release/replace lease yet return
same pose/Session, yielding stale true before actualAction.handle or after its
durableprefix. Preserve all privateC28/owner/phase/gen/pose/fullcustody/catalog/
reply cuts and existing failure path. No oldconsumedcustody reread, query,
SQLretry/rollback/newrules/wire/defaultactivation.2literal edits/2whole inverses
exactoldrefs/Git63edc90; independent2CPP reviewPASS. Source/13 pins36, old29
unchanged; canonical443; newPY0/newCUSTOM0. Historicaldefinition source is only
TWP/WPN/EQU/TEQ, genuineSKB learning/action/subject/right/itemconsume/WORLD35
event/atomiconce persistence stillmissing.371 selector requirespositivecount,
no uppercountbound; not universalC56gate. OneactualC28sourcebranch improved,
newopcode/formula/phase/ownerchain/fullroute0. TW156/252/parser75=50partial+
11control+14unconnected, unhosted3/40/36; CN156/280phase/253supported/35/93/71
unchanged. S2Cindependentformats17/unclassified109; frontier24immutable.
Whole denominator/%null. Goalactive; PHASE1 no build/tests/runtime/native/API/
VM/codec/gameDBSQL/migrate/activate/deploy. Shared453/TWTraditional/maxHPdiv10
poison/CNcustom126/150/common64 and all frozen/account/save requirements retained.
