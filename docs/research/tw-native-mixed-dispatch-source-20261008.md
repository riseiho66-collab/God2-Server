# 原生世界混合封包分派來源（第177輪）

目標模式維持 active，接續使用者要求的「現在恢復串接，全部打通後才驗證」。本輪只做來源實作與靜態原生追查；沒有建置、遊戲執行、測試、資料庫存取或部署。

新增 `SharedTaiwanWorldRecordSource`，讓同一個實際世界輸入批次按原順序分成最大連續的 Movement／Others 區段。Movement 直接交給同一 native movement host 的原始 binding；Others 必須由真正的原生處理端接收完整區段，包括 tick、diagnostic 和其他已解析變體，不丟棄、不補假 ACK。必要的 Current 在整批、每段之前／之後及回傳之前資格化完整輸入、精確 Session／Lease、目前共同位置、phase、battle generation 和累積輸出；普通 movement ring 條件及全部區段準備在遊戲回呼前完成。

原始加密回覆 envelope 保留位元組與次序，只在來源邊界處檢查完整 envelope 與真實供應的 bytes／frames 預算；既有 Session 完整 checksum 邏輯保持原樣。沒有回覆必須由 Others 明確提供原生 `no_reply` 決定。處理失敗、資格失效或捕捉到重入時，該份精確來源不再使用；已結算的前段不倒退、不重播。舊 Session 或不同 Lease 的拒絕不能失效另一份來源。

`SharedWorldHostPlan` 增加明確的 mixed-record 工廠，`SharedTaiwanNativeWorldHostPlan` 增加可選 `MixedRecords` 模式。Application 在同一個真正 Context 上先組裝 native movement，再組裝同源 record handler，安裝到既有 game vault／Session 呼叫端；網路 facade 不遞迴呼叫另一個 movement facade。斷線與撤銷時先釋放 record bookkeeping，再撤下 movement／scene；回呼在 game owner、資料庫結束前釋放。原 MovementOnly 模式與一般 Main 選取保持原設定。真正的 Others、Current、權限、初始場景與完整 native 5D 仍須供應，不能把這份可接入來源算成已完成玩法。

台服子代理恢復了原生尋路的完整算法關係：8 鄰格只查目標 raw cell，沒有自行加上雙側斜角限制；搜尋有 10 次展開預算，可回傳未到目的地的結果。回傳序列是 closed-pop 歷史鏈，不是 parent 最短路徑；固定長度的中點修補最多 32 次呼叫，不能改寫成一般 A* 或宣稱一定到達。原始函式、堆疊參數與修正前追查記錄分開保留。這些是客戶端導航規則，不能替代原生服務端移動權限或 ACK。

陸服子代理新增兩個完整函式範圍（684 bytes）、五條具體關係：實際 owner／map raw getter 和 packed-coordinate 中點修補。既有 `CnMapPassability` 已有對應 reader，不另建重複類別。固定 126-byte 複製保留 header，沒有寫 count pointer；未恢復的完整容量／fallback／權限／5D 仍開放。既有 14 個 receiver context／12 個 qualified context 不變，未知 phase 保持未知。

| 本輪統計 | TW | CN |
|---|---:|---:|
| C2S opcode 索引 | 156（151一般＋5補充） | 156 |
| S2C opcode／phase entries | 252（230定長＋22變長） | 280（帳號6／世界206／戰鬥68） |
| 新增 opcode／phase binding | 0／0 | 0／0 |
| 新增完整雙向遊戲路徑 | 0 | 0 |

本輪兩個新 C++ 檔、四個既有 C++ 檔實際變更，來源紀錄由168增為169。958個 endpoint rows、28個群組及30個戰鬥 action／selector entries 沿用原帳本，不能當全遊戲路徑分母。完整已打通路徑總數、全遊戲總數與完成百分比仍未知。

後續優先接真正的 native Others／Current 與權威 producer、原生導航來源 owner／資源生命周期，以及 TW／CN 完整 entry／權限／world supplier／Main。全遊戲剩餘玩法、64位元儲存／線路／物件／飄字／網頁、stack99完整變動路徑、網頁 WSS／TLS／hosting 全部保留。仙幣上限99999999999、其他上限另定、等級不改、原生字體及繁簡轉換維持原要求。

fresh before1270 SHA256 `399a29a063b59bccba1f27350e6d91991eba4c0604c979bfb52bf47ab58cf596`，第176輪完整2290個封存成員保留。新代理封存、完整實際原生輸入、來源初版／修補前版本、當前來源和四份原始／四份最終報告分別保存。Application 的閱讀範圍是全部修改定義與實際呼叫上下文，另保留整份來源原件；不冒稱這輪重新讀完所有未改玩法。
