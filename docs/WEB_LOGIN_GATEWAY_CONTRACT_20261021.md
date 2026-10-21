# 台服網頁登入 gateway 與選線契約

狀態：PHASE1 SOURCE_STATIC_ONLY。這是源碼接線及修改後審查，沒有編譯、測試、
啟動服務、遊戲、VM、codec、遊戲 SQL／schema／migration 或部署。
目前沒有可確認已部署、可用的 L/G WebSocket URL；下列 path 不是現成連線網址。
使用者本人在 God2-WebClient-Main 的限定問題回答「恢復登入串接源碼整合（建議）」；
已讀取真正 userMessage 核實。只恢復本項，不恢復完整目標或4-discord heartbeat。

## Main 的明確入口

普通 PC CLI 保留原來行為。只有明確提供 `--web-config <web-policy.json>`，才經
WebMainOptions 走 `run_server(config, web_plan, seconds)`；可同時指定原有
`--config <native-server.json>`、`--run-for <seconds>`。Web 分支先於現有操作工具辨識；
與 schema／migration／import／capacity 等操作旗標混用或重複／未知旗標會拒絕。
Web help 不載入檔案。沒有自動預設 Web port、原生目的地或三世界來源。

獨立 JSON 最大64 KiB，是 CUSTOM 宿主輸入預算，不是原服容量。所有欄位必填，
另限制 parser nesting 為32；未知欄位、原始檔重複 key、錯型別、非整數、負值、
越界、重複角色及未知版本拒絕：

| 欄位 | 契約 |
| --- | --- |
| `version` | 整數1 |
| `listen.address` | 明確 IPv4／IPv6 loopback literal，不作 DNS |
| `listen.port` | 明確0..65535；0表示請核心配真正 bound port，不猜替代 port |
| `origins` | 非空且不重複的明確 Origin 字串；不是登入或玩法權限 |
| `limits.max_sessions`、`sessions_per_address`、`accepts_per_second` | 各自正整數、宿主可表示範圍 |
| `limits.message_bytes` | 正整數且不超過16 MiB |
| `limits.queue_bytes` | 至少65546，保留一筆原有 native TCP read 與 WS header 的空間 |
| `limits.queue_frames`、`frames_per_second`、`bytes_per_second` | 各自正整數、宿主可表示範圍 |
| `timeouts_seconds.handshake`、`idle`、`message`、`close` | 各自可轉為 steady-clock duration 的正整數秒；執行時另核 now＋duration 不溢位 |
| `routes` | 非空且唯一的 `tw_account`／`tw_world` 角色陣列，最多兩項 |

不接受 JSON 指定 native host／port、任意 path、query、分流權限或自製來源。
Main loader 與 Application 共用純 policy／role 檢查；Application 在 DB／listener
建構前亦檢查真正 native authentication 模式及 G 所需 dual connection。
三分流若開 world route 必須亦開 account route；其餘原有 native plan gates 保留。
這些是配置前置檢查，不能證明尚未呼叫的完整來源 factory 一定成功。

有效服務啟動仍沿用既有 Application 的 DB initialize／migrate 生命周期；本次
沒有執行它，也沒有把 opt-in 稱為「有效啟動完全不碰DB」或增加另一套 migration。

## 真正 held listener 到固定路由

| 實際宿主 | 路徑與來源 |
| --- | --- |
| Account/L | `/tw/native`，來自當前 account_server 的完整 bound endpoint |
| 單一 G | `/tw/native-game`，來自當前 character_server 的完整 bound endpoint |
| 真正三分流 G | `/tw/native-game/0`、`/1`、`/2`，分別來自當前 TaiwanChannelServers::endpoint(k) |
| 公開路由資料 | 精確 HTTP GET `/tw/native-routes`，不連 native TCP，不產生選角／入場權利 |

wildcard listener 只在宿主內換成同族 loopback 可達地址；不由瀏覽器提供目標。
三個 indexed G 必須完整且 endpoint 互異、同一 group、subgroup 與 suffix 一致，
並帶同一宿主的 L route；不混入舊單 G path。缺任何來源拒絕整個候選。
所有 native 邏輯位元組、L/G 各自身份與既有 framing／seed 流程保持原來所有者。

WebServerPlan 的一項 `tw_world` 在真正三世界宿主展開全部三條路徑，沒有新增
讓每筆 request 猜 ordinal 或傳入 target 的介面。原有停止順序仍先撤銷 native
source／listener binding，再清理及排空 NET／GAME；Web route 只保留純資料，
不在 NET 保存或銷毀 GAME world、Session issuer 或 DB callback。

## 客戶端可消費的路由資料

JSON schema 為 `version:1`，`account` 是 `{path}` 或未掛 L 時的 `null`，`games`
是陣列，每項有 `path`、`native_address`、`native_port`；真正三分流另有 `group`
與 `subgroup`。單 G 不捏造 group／subgroup。資料由同一 immutable held route map
產生，不包含帳密、native packet、ticket 或角色資料，不是可兌換的權限憑證。

GET 回覆 no-store 後關閉 HTTP 連線。提供 Origin 時必須在原有白名單內才回覆
該 Origin 的 CORS 欄位；沒提供 Origin 可讀公開 metadata，沒有跨來源許可反射。
WS upgrade 仍須原有 Origin 白名單，維持 binary 原生串流，不在 native 協定插 JSON。

客戶端依序處理：

1. 由受控 gateway base 讀 route catalog，核版本與結構；base 不是從 native
   封包任意 IP／port 或使用者 query 直接組出的代理目的地。
2. 使用 account.path 建 L WebSocket，照原生順序完成 L handshake／登入／選擇。
3. 從真正 L 名單及原生已選 Table／角色資料算出原來 primary destination；
   以完整地址／port及有提供的 group／subgroup 精確找唯一 game route。
   缺失或不唯一便拒絕，不取第一筆／最新筆／channel0，也不改寫 native bytes。
4. 只把找到的固定 path 接到同一受控 gateway base，建立獨立 G WebSocket，
   繼續原有 G authentication／selection／entry。metadata 不能跳過任何一步。

前端仍須將這份 schema 接到自己的 C++ LoginDriver，並完成真正 Main／完整 actor／
EntryPort／正式 host。離線地圖、NPC ROM 或 mock port 成功不是實際登入入場成功。

## 可信選線仍由 native G 判定

在真正已綁定的三 G 宿主，NativeTaiwanChannelBinding 將接受的 Session 固定到
該 listener/world。SharedTaiwanCharacterListHandoff 另核真正 L 的 selection pair、
已成功 native TCP write 的 advertisement、完整 issued list／roots、來源活性、
獨立 G authentication 與實際 local endpoint。選錯 G 不能靠換 URL、metadata、
A6／07 bytes 或 Origin 改寫這條資格；重解析多份 active 候選仍拒絕歧義。

既有 Selected／pre-use entry、full64 角色獨占、terminal cleanup 及失敗 quarantine
不變。native TCP Written 是寫到本機 gateway 的觀察，不是瀏覽器／動畫 ACK。
路由 map 不是新的 Session 綁定權限、持久交接、重放豁免或逾時清票規則。

上述 private 三 G 證明不能套給未綁定的 legacy 單 G。Main 的 opt-in 只是包住它
原本會使用的 PC source 模式，不把候選 list／未實作 handler 提升為可信 native entry。
真正三分流仍須呼叫既有 typed overload，提供完整 TaiwanThreeChannelPlan 的
configuration、Live／Authority、三份真正 world plans 等來源；Main 尚無這套供應者。
本次只讓已具完整方案的宿主能掛 Web routes，沒有捏造缺少的權威或預設成功。

既有 native handoff／offer 仍釘149c來源；沒有改 pin 成 aaf0 或借 current-client
研究冒充舊 decoded 材料。這項來源資格缺口亦須另行解決，不能由 Web transport 蓋過。
實際 ticket retire 入口、重登入歧義、持久 save／recovery／target admission、
六向切換、公開 TLS／部署及真正台服聯合驗收仍待完成。

## 審查與交付界線

新增純 policy／route map／manifest、CLI／配置及 pre-DB 相容性 SOURCE 案例，
登錄為獨立測試；本輪未執行。每條修改後檢查相關入口、授權、失敗、生命週期及
回覆順序，並由另一位審查者複查。純源碼已有完整證據的部分未另造 REA；
未知 native 契約保留既有 current-TW REA 追查要求，沒有新增未證 native 規則。
唯一正式靜態報告、精確 SHA、授權及審查收據保存在：
`C:/Users/risei/.codex/artifact-archives/god2-server/20261021/web-login-source-integration-pass1`。

## 2026-10-21 pass2：來源供應者逐項核對與實際封口

本節回應使用者直接要求繼續 Main 三分流供應者與可信 L→G 源碼整合。
本輪不編譯、測試、開服務、讀寫遊戲DB、codec、schema／migration或部署。

實際追到的必要材料如下；表格中的「仍缺」不是可用 JSON 開關代替的權威：

| 來源 | 已有實作 | Main 仍缺少的真正輸入 |
| --- | --- | --- |
| 三個世界與G端點 | SharedTaiwanChannelWorlds、獨立完整GAME frame、TaiwanChannelServers與私有listener binding | 真正三份可構造的完整native world plan；不能把一份已綁owner快取複用三次 |
| L名單 | 完整75-byte07／角色順序與root snapshot reader、真正Written／Issued及offer交易adapter | Target／Qualify與完整07 issuer，含可見角色順序、token、route及未解位元；profile40不是07生成規則 |
| 跨socket交接 | 真正選擇／實寫advertisement／Issued／獨立G authentication及完整destination重核 | 真正Live／Authority來源；不能把JSON group／subgroup或true lambda當授權 |
| 初次2A | 原完整snapshot reader及條件式writer／Selected pre-use fence | 完整40-byte wire（37-byte logical記錄）、root／位置／身份／不透明位元來源及entry qualifier；不能以幾何或codec自動補齊 |
| Entered／場景 | 完整initial publication、精確6F對應與資源readset adapter、私有lease／失敗cleanup | 真正Source的原始aggregate、incoming／outward全集、Current、Install／Cleanup；空場景或true回呼不是一般地圖完成 |
| 移動 | CAN／HMD與原件資源owner、Written2A pose、明示CUSTOM ordinary movement adapter | 與同一初次scene／lease一致的Input／Authority；資源存在本身不准移動或發5D |

這次沒有新增「Main provider registry」或只有std::function欄位的空方案來冒充供應者。
以上缺失源在現有src只到 mandatory supplier 介面，沒有可直接掛Main的實作者。
沒有因這份調查開啟DB去找或生成資料，也沒有改存檔／放置NPC怪物。

實際補了兩個可由現有來源證實的接線問題：

1. `TaiwanThreeChannelPlan::validate` 原本只核SHA字面格式；不同的合法64位hex會
   通過，直到Application完成DB初始化後，handoff才因既有149c pin拒絕。
   現在沿用後段已存在的精確版本要求，在啟動前同樣拒絕。這不證原件檔案真實性，
   也不把當前aaf0 EXE換成149c的資料來源；原件資格缺口仍保留。
2. 原來三個world plan只需交出非空名單callbacks；沒有核這些callbacks是否來自
   Application剛建立的同一個shared L handoff。現在專用source工廠從同一handoff
   取得真正publish/link，核同一accounts／characters／summary reader、build與capacity，
   並封存私有的canonical callback bundle。HostPlan先還原該bundle，再包回既有
   host-owner／生命週期檢查；Application只接受同一shared handoff的canonical版本。
   公開可改的facade不能把另一套callbacks和合法身份標記拼在一起冒充通過。
   該私有來源確認只在GAME使用，不建立Session／ticket，也不呼叫供應者或查SQL。

generic callback API仍可供原來非三分流來源使用，但不能因此取得三分流來源資格。
此修正關閉的是「三份來源必須用真shared handoff」的接線缺口，不是發明缺少的
Live／Authority、名單可見規則或完整場景生成者。角色full64獨占、錯G拒絕、
失敗quarantine、原native位元組與固定WS路徑／manifest schema繼續保持原樣。

REA界線亦逐項核對：當前aaf0的40B490→4147D0、40BA00→414C50與412310
路由consumer已有保留的反編譯／組語證據。重跑同一consumer不能因此取得
原服07／2A issuer、伺服端可見性及場景授權；因此本輪沒有造一輪REA
來冒充找到producer。後續若定位新的未分析shipped函數，仍直接依REA追查。
純來源身份、版本pin與callback生命周期問題由完整源碼直接修正。

客戶端契約不改：讀version1清單，先完成真正L選擇，再以完整native destination
及提供的group／subgroup找唯一固定G path，獨立完成G登入與入場；缺失／歧義拒絕。
不得把本節的canonical server binding送到瀏覽器、造JSON token、跳過native認證，
或把nativeTCP Written提升為瀏覽器／動畫ACK。前端Main／actor／EntryPort、真正
Main三世界supplier、持久復原／target admission與部署URL仍沒有本輪完成證據。

作者／修改後獨立讀碼、未執行SOURCE案例、唯一正式靜態報告與精確SHA收據保存於：
`C:/Users/risei/.codex/artifact-archives/god2-server/20261021/web-login-source-integration-pass2`。
