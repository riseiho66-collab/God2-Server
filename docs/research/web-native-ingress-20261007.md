# 同一Application原生WebSocket入口來源

本輪來源接到四個已交接路徑，使用WebServerPlan明確opt-in，原main/Config
不啟用gateway。Application只依本次實際持有的TW TcpServer bound port及
CN SharedCredentialServer bound_endpoints registry建立目的地；TW G包含
動態綁定端口，CN World需要已註冊group/server，沒有browser host/port。
CN供應者仍必須是完整SharedServerPlan；沒有猜測seed或登入成功資料。

新增WebClientGateway.h/.cpp、WebSocketHandshake.inc與WebServerPlan.h；
Application.h/.cpp接明確TW/web及TW/CN/web overload、啟動與停止；CN server
新增game-owner唯讀的bound registry。CMake現有src/*.cpp遞迴清單包含新來源，
但本輪不建置。對方TEMP候選兩檔已精確封存；僅公共upgrade checksum helpers
沿用，連線state/HTTP/流控由此chat重寫，不包含靜態檔案站或前端修改。

握手與frame規則依[RFC6455](https://www.rfc-editor.org/rfc/rfc6455.html)：
bounded HTTP讀取、GET/HTTP1.1、version13、16-byte canonical nonce、明確Origin；
無extension/subprotocol回覆。只收masked binary及continuation，保留順序、
允許片段間ping/pong/close；限制frame/message/queue/速率/逾時，校驗close
code及UTF8 reason。每WS對應獨立native TCP，key/seed及native length仍歸既有
Session，WS message不等同native record，不修改C2S/S2C或遊戲結算。

browser→native在前一段async_write完成才讀下一段；native→browser在待送
佇列未預留下一次TCP讀取空間時暫停讀取，送完再恢復。close標記放在每筆
queue item，避免已排隊資料使close flag遺失。close drain有獨立期限，取消
native時不讓回調跳過待送close。所有transport狀態在network strand；停止
gateway先於native listeners，網路/遊戲executor沿用Application原本drain。

## 明確缺口

- 沒有建置、WS互通/fragmentation/關閉/背壓測試、native或瀏覽器驗收。
- 只有explicit overload source，普通main不建立WebServerPlan；正式入口未啟用。
- TLS不在此loopback listener實作；正式WSS反代與發布仍待全來源集中驗證。
- gateway不解決既有未恢復native gameplay/登入供應者或假定所有數值可用。
- per-address計數以直接TCP來源為準；反代會共用該位址。不信任X-Forwarded-For，
  真實client-IP節流需要受控反代及其edge policy，不能以現有quota宣稱齊全。
- 四固定paths只綁一個CN World target；多group轉服公開route-key契約尚未實作。
- Windows SHA1 checksum沿用BCrypt；其他平台需供應checksum provider才可用。
- Native owner/phase/玩法/重放檢查仍在原生authority，不能以Origin取代身份。

本輪增加4個路徑的**條件式來源轉送**，完整native遊戲路徑新增0，部署0；
不把gateway轉送或HTTP拒絕算成遊戲封包完成率。
