# CN 世界流程返回後的退出來源

本輪 `20261008-cn-post-world-exit-source`，保持 PHASE1。上一個 goal 回合只查閱及回報狀態，分類為 no progress；這輪接續此前已保存 before snapshot 的實作，不重啟另一套工作。完整目標仍包含 TW／CN 原生與既有網頁客戶端、共用世界和資料、全部玩法與數值擴充，最後集中測試、修復及發布。

## 原生發送點與舊紀錄更正

以固定 CN EXE `582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8` 的 primary bytes 為準。`0044A470` 在世界流程呼叫 `0048DA20` 後把實際 EAX 存入 EBX，銷毀 main+460 世界物件，再以 `EBX-1`、unsigned 上界 5 分派到六格 `0044A960` table。table 位於該函式 metadata envelope 之外，另外保存 24 bytes。這裡證明的是流程返回後的連線生命週期，尚未追完 EBX 所有上游原因，也不宣稱完整世界／戰鬥狀態機。

|實際 EBX|primary table target|本分支發送|callsite|
|---:|---|---|---|
|1|0044A7A7|02 01，wait=1|0044A8C8|
|2|0044A79D，落入0044A7A7|02 01，wait=1|0044A8C8|
|3|0044A8A7|02 00，wait=1|0044A8B3|
|4|0044A7B9|此 switch 分支無該 close 發送|不推導其他流程無發送|
|5|0044A8BC|02 00，wait=1|0044A8C8|
|6|0044A7B0|02 02，wait=1|0044A8C8|
|其他|0044A8CD|此 switch default 無該 close 發送|不推導其他流程無發送|

`0044A8C0` 共用 tail 寫 ECX=main+458、push opcode2，再呼叫 `00480B10`。必須沿 table target 的 upstream pushes；不能只採實體相鄰的 `0044A8BC` control0。此前 `cn-close-producer-variants-01` 的 25 direct callsites／control0:23、3:1、4:1 是局部最近 push 觀察，並非各 callsite 全路徑 repertoire。原封存及紀錄全部保留，本輪新增 correction receipt，補上此點控制值1／2，不增加 direct callsite、不把五個發送案例或三個控制值算成新 opcode／完整玩法。這條 post-world context 的 form 為0／1／2；先前 pre-world create/delete 的3／4仍在獨立契約，不能混成通用權限或原因碼。

`00449F50` primary constructor 顯示 main+454／+458 是分別以 `0047D6C0` 建立、`0047FA20` 初始化的網路物件。main+450 由 `0053B880` 建立，不是本發送點的遊戲連線。`00445040` 把 main+454／+458 分別綁至 UI+1617C／+16180。現有 ACCOUNT／WORLD／BATTLE 接收 context 名稱保持；這些物件證據不證明另有獨立 battle socket。

`00480B10` 使用 `00481440` 發送 opcode 加一個 byte，呼叫 `0047F430` flush；wait 非零會等待收到03。既有 `CnPreWorldCloseReply` 保存03整筆3 bytes，兩個 payload bytes仍不透明。本輪沿用已保存的 world03接收及 close-drain 證據；不補0、不發 opcode-only ACK、不把 local write/drain 視為客戶端接受。

## 服務端來源增量

新增 `CnPostWorldExitControl` 精確讀取2 bytes／opcode02／control0..2；其形式名稱只描述原生 byte，不賦予 backend reason、權限、存檔或戰鬥含義。新增 `SharedPostWorldExit`，要求同一 World connection、已認證 account、offered character、ready presence 及精確 lease generation。收到一次退出後，在呼叫 issuer 前固定 terminal scope，包含當前共同存檔位置及 revision；禁止第二次 source／重试 scope。

實際退出權威必須提供完整 native03及帶生命週期的 current predicate，確認真實規則、未完成操作、儲存和重播的 quiescence。這個 supplier 不得 yield、發包或任意寫存檔；沒有預設成功來源。傳出前與排入後沿用同一連線既有 `close_after_native_world_reply`，之後 drain-and-close，既有 OnClosed 維持 admission／presence／visibility／scene reservation 清理。這是既有 send_batch 契約，不宣稱新增更強的 held-publication gate 或跨程序原子保證。

`SharedWorldGameplay::Sources.post_world_exit` 是明確可選的實際 supplier；未配置時該分支仍不可用。它在原生1C publication 的 ready activation 後與既有 controllers 一起安裝。aggregate 先完整檢查形狀：退出2-byte記錄必須最後，control3／4不交給這個 owner；既有移動等前綴仍逐筆處理，沒有整批原子交易宣稱。terminal完成後停止 pump，成功 completion 只表示本地 write/drain，不能再以關閉後失效的 ready/source 判成失敗或執行後續玩法。`SharedWorldReady` 已直接轉交 InWorld remainder及原 completion，毋須修改。

## 計數與缺口

新增 partial／unhosted post-world來源鏈1；C2S02／S2C03在 world-entered 的來源綁定各1。新增原生控制值觀察1／2共2，直接callsite新增0，opcode新增0，完整雙向路徑新增0。完整總數／已完成數／百分比仍 null。EBX原因、所有phase／state／variant、03兩個opaque bytes、實際退出／儲存／戰鬥規則及正式 Application hosting未完成；不能把可選issuer介面算成實際權威已實作。其他所有玩法、TW／CN／web／WSS、64-bit數值、堆疊99與集中測試修復發布保持完整目標。

本輪僅讀檔、primary反組譯、來源編輯、靜態帳本及雜湊封存。沒有建置、測試、C++／native／API／codec執行、資料庫讀寫、遷移或部署；帳號存檔、認證、聊天、IME、頭像、原生字體、繁簡轉換、等級與客戶端二進位維持。
