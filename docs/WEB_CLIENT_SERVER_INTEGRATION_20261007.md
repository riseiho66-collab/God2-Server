# GOD2 網頁客戶端服務端整合與交接

使用者直接指定分工：chat「打包高清角色圖與 UI」只做網頁客戶端；本 chat
做同一 God2 服務端支援。使用者要求雙方喬好後回報。對方 task id
01a113e8-82eb-7463-aa38-3352bff3e51f；不重啟 paused 原獨立 CN 任務。
對方契約：C:/Users/risei/Desktop/God2/God2/output/web-prototype/WEB_SERVER_INTEGRATION.md。
原文及選定 client wire/login 來源精確雜湊快照保留於
artifacts/continuation/goal-tw-cn-web-20261007/frontend-inputs。

## 已接收的契約與責任

| 部分 | 負責 | 契約 |
|---|---|---|
| 原版素材、HTML/JS/CSS/WebGL、UI/動作/顯示/原生 wire adapters | 網頁 chat | 專心完成客戶端，不再修改服務端來源；現有 Python橋接僅開發用途。 |
| WebSocket 與 native L/G 入口、transport/lifetime/認證/權威狀態/Lua/儲存 | 本 chat | 同一服務端、帳號、角色、存檔及多人世界；PC 和網頁共用一次權威結算。 |
| 原生封包 phase/state/variant 與 client consumer 配對 | 雙方交接 | 來源明確後串接；未恢復 CN 資料不得送入 TW dispatcher 或宣稱可玩。 |
| TW/CN 與簡繁 | 雙方依既有文字邊界 | 協定路徑決定 adapter；顯示偏好只控制文字/UI。四組合獨立。 |

確認四條 WebSocket 路徑承載原生**完整二進位 byte stream**，不是解碼後
logical record，也不按 WebSocket message 等同 native packet。native length
前綴仍由實際 TCP Session/adapter 處理，需保留半包/合包、多 logical records
與分連線 seed/key。禁止用 S2C length 表切 C2S。前端採 native wire codec；
gateway 不解碼帳密/遊戲 opcode、不二次結算或轉簡繁二進位控制資料。

| WS路徑 | Native role | 版本來源 |
|---|---|---|
| /tw/native | Account/L | 沿用既有 TW native-wire/login 及正式來源，未填假版本值。 |
| /tw/native-game | Character/world/G | 實際 TW G listener/catalog 路由，不能拿L當G。 |
| /cn/native | CN Account | transport40；204-byte login payload 的版本欄位200。 |
| /cn/native-game | CN World | transport240；204-byte world00 payload 的版本欄位200。 |

CN版本40/240與login內200是三個不同契約，見CnAccountWire.h及
SharedCredentialStage.cpp。204-byte payload+opcode是205-byte logical record。
CN executable582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8。
TW installed executable99cde6b666101c0702d712a1a15bf4d83f225a1a521a9c601bd32a6e42debe25；
歷史 mapped149c...與當前安裝版分開，不能更新舊驗收基準。

## 現在的可接入界線

2026-10-07本輪唯讀現查 psutil.net_connections：**2592沒有 LISTEN項**。
此觀察不是全系統服務離線判定，也不是部署授權。歷史交接記載的2592/PID
不能用作現在可連線端點。没有為網頁啟動/重啟/測試任何服務。

從歷史 owned-process取得設定檔路徑，再現讀該設定中的非敏感欄位：
artifacts/releases/town-chat-welcome-20260924/server-config.json。
TW L設定127.0.0.1:2592，character_port=0（啟動時動態綁定，非實際G=0）。
TW G須從真正已啟動 listener/catalog 取得，現在無可提供的活躍G數值。
設定protocol mode=god2_legacy_character_list_candidate；原始設定保留且未改。
設定存在不證明當前執行/握手/網頁驗收通過。

CN目前SharedServerPlan的seed/account/world success/controllers和端點需要
實際資格來源；普通main不建立CN plan。沒有可宣稱已啟用的CN L/G端點。
WEB gateway現已接入條件式來源，普通main未啟用且尚未hosting/驗收；ws://127.0.0.1:8767是前端
本機Python開發橋接預設，不是正式可玩服務端。TW/CN功能來源有局部鏈路，
詳細catalog51與round報告範圍不能當正式部署清單。

## 服務端接續方案

本輪來源進展詳見docs/research/web-native-ingress-20261007.md：
WebServerPlan明確opt-in、四路徑、實際bound listener registry、Application
start/stop、Origin及binary stream/fragmentation/限額/背壓來源已加入。
目前不提供可用端點，未建置或啟動，尚未證明正式WebSocket互通。

1. 接收前端契約，封存來源與雙方分工，將WEB加入原目標與每輪帳本。
2. 在C++/Asio服務端做受控WS ingress，四路徑只能對應Application實際
   持有/註冊的native L/G端點；TCP destination由服務端配置/registry供應。
   不接受瀏覽器任意host/port；G動態端口先從真listener取得後才開放路徑。
3. 由同一Application管理gateway/native啟停順序、connection quota、Origin
   明確allowlist、binary fragmentation/控制frame、佇列容量/背壓和雙端關閉。
   第一階段只接來源，TLS/正式反代/正式啟用留最終發布階段。
4. 若CNcatalog開放多個group/server目的地，四個固定path不足以指定任意
   G目的地；先保持固定管理者綁定，另與前端約定只選server registry中
   實際公開的路由鍵。不把前端宣告的gamePort当TCP代理授權。
5. 遊戲處理仍進既有native認證/原生phase/state/共用owner，補齊缺失正式
   seed/success/entry/gameplay suppliers；不建立預設成功或空handler。
6. 前端自行維護簡繁顯示偏好與原版UI；伺服器保留既有UTF8原文及按native
   收件者編碼的CP950/CP936邊界。收到wire文字的本地簡繁呈現，不改sender
   bytes/account/character IDs/credentials。語言切換不換路徑或重登。
7. 每輪分開WEB transport、native TW/CN source、完整玩法、hosting與驗收；
   UI投影/格式/代理不能充當完整遊戲路徑。整體分母未知時percent仍null。

## 請網頁端保持及對齊的接續項

- 同一WS上native流可能分段或合併，多logicalrecords要逐phase解碼。
- 每個L/G peer各自key/seed，CN不沿用TW dispatcher。
- 若request credentials metadata尚未完整恢復，保留unknown與來源區分；
  帳密不可日志/存久或繁簡轉換，front display與native encoding分開。
- CN5C目前普通channel有原生prefix/text容量差異：0/1/2/3/5/6/8/9為252、
  13為255、18為247。依原生完整wire與實際收件者profile，不憑languagebit
  認定TW/CN或CP936。參考docs/research/cn-chat-consumer-capacity-20261007.md與相應證據。
- 保留各個07槽位到1F/1A的實際身分關係與轉服變體，不只按長度判定正確。
- 確認固定四路徑/責任與來源界線後回覆本chat；可接活躍端點未取得前
  保持未連線狀態，不拿本機preview或假資料稱服務端已可玩。

交接狀態：雙方分工與介面已確認。對方已完整讀取本文件，明確接受四條
binary WS stream路徑、獨立L/G key、CN40/240與payload200、CP950/936及
顯示偏好分離、僅用實際registry路由鍵，以及目前未啟用的端點界線。
原生PC素材、布局、操作流程及動作節奏是網頁移植準則，不額外設計。
確認來自對方chat的直接回覆；來源turn/item與原文封存於本輪
artifacts/continuation/goal-tw-cn-web-20261007/peer-handoff-confirmation.json。
此確認只完成責任與契約交接，沒有新增已完成玩法或正式啟用入口。
對方臨時候選gateway在TEMP的資訊只作線索，尚未納入正式來源或完整功能。

## 防改包與權威狀態責任

對方轉交使用者的安全要求已納入服務端方案，尚未宣稱實作完成。
PC與網頁共用權威驗證：身份/owner、phase、物件歸屬、玩法約束、可達位置、
技能/道具/貨幣/掉落只能依服務端狀態與規則結算；每條原生操作按已恢復
語義處理重複提交與重放，不憑opcode存在即允許操作。登入、連線與輸入
設置實際限額、長度上限及背壓；Origin allowlist與正式WSS/TLS由此chat負責。
保持原生PC wire相容，不添加猜測的加密/認證欄位，不以JS混淆作安全邊界。
前端chat負責網頁資源暴露、DOM/chat注入、憑證生命週期及開發靜態站防護。
正式安全測試與啟用仍在全來源串接後的集中驗證/發布階段。
