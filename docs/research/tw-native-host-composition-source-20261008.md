# 共用世界正式來源組裝（第176輪）

使用者明確要求「現在恢復串接，全部打通後才驗證」。第175輪的停止紀錄保留；本輪恢復實作，沒有建置、遊戲執行、測試或部署。目標仍是 TW／CN／網頁全部遊戲雙向路徑，不能縮為這輪的世界入口、移動或選角。

本輪優先處理真正呼叫端。新增 `SharedTaiwanNativeWorldHostPlan`，由 Application 的同一個實際 Context 一次組裝完整 entry source、既有 initial scene publisher 和 native movement host，供既有 `run_server(..., world_plan)` 路徑選取。完整原生 entry、初始玩家集合、規則、資源、Current、Authority、完整 5D 與實際容量都必須由真實供應端提供，沒有猜測或預設成功。一般 Main 仍未選取此 plan。

計畫工廠只弱持有 game owner。真正的 entry／entered／movement callable 強持有 owner，隨 Application 既有 game vault 一起釋放；不把遊戲執行期資源留在 main 上最後解構。同一工廠不能再綁另一個資料庫、地圖目錄、executor 或 common world；初始化捕捉到的重入也會使本次建構失效。取消時先撤下精確移動來源，再交既有初始場景 owner 清理，兩條清理都會執行。

新增 `SharedTaiwanNativeMovementHost`，直接持有實際資源 owner 與既有 movement source/controller。第一次移動依精確 ready Lease 和目前共同儲存位置呼叫實際資源供應端，完整 install 後才取得場景；後续移動沿用既有來源，不重造一個虛構場景。替換／移除先撤下相同 Session 與完整 Lease 的 controller，再處理該份資源；`SharedTaiwanMovementSource` 增加精確 `retire`，保留既有 release 介面，不釋放共同 Presence／Visibility 或後繼 generation。

CN 新增 `SharedSelectedCharacterLocationSource`，並在 `compose_native_login` 的實際 account 呼叫端、完整目錄資格完成後明確綁入選角來源。state `0x1A` 的被選 row／共同角色身分、權限、來源 revision 仍由必要供應端提供；只資格化明確的被選 row，不默認所有角色允許。完整原始 75-byte 07 保持原樣。原生 Location 對 character row `+0x20`／`+0x21`／WORD `+0x22` 的本地結果另存供觀察，不當成伺服器原始 07、不寫成共同 map／spawn 資料。

TW 靜態追查進一步區分實際 C2S 傳送條件、pending 與原生本地動畫／尋路。客戶端 5D consumer 儲存一個 byte 並 pop pending，不證明伺服器可以 echo request index；客戶端時間與動畫更新也不是原生伺服器移動權限。61 在同 scene 特定旗標下有不同分支，不能全部稱為 reset。歷史名稱包含 movement 的 golden seed 檔實際只到 seed／登入後輸入，沒有 world 2E／5D；保留原件與此限制，沒有刷新舊驗收基準。真正 server 5D producer 仍開放。

| 本輪項目 | TW | CN |
|---|---:|---:|
| C2S opcode 索引 | 156（151一般＋5補充） | 156 |
| S2C opcode／phase entries | 252（230定長＋22變長） | 280（帳號6／世界206／戰鬥68） |
| 新增 opcode／phase binding | 0／0 | 0／0 |
| 新增完整雙向遊戲路徑 | 0 | 0 |

六個新 C++ 檔、五個既有 C++ 檔的接入變更，來源紀錄167增為168；這些不是打通封包數。既有30個戰鬥 action／selector entries、958個 endpoint rows、28個群組不重計，也不當全遊戲分母。全遊戲總路徑、完整已打通總數與百分比仍未知。

仍欠缺真正 TW entry／reservation／初始 peer／動態資源與 Current、移動 Authority／pending／reset／timing／完整 5D 供應端，以及 CN 原生 account／rights／selected phase／summary／world issuer、mixed dispatcher 和正式 Main 選取。64位元數值的儲存、線路、物件、飄字及網頁、stack99全部變動路徑、網頁 WSS／TLS／hosting 與其餘全遊戲路徑持續保留。仙幣99999999999、其他上限另定、等級不改、原生字體與繁簡轉換保持原要求。

本輪 fresh before1260 SHA256 `58c05401e6e9145a44641e5842e875cdab3051ddd9968102859ecacca0cec9ca`；第175輪完整2160個封存成員保留。原始來源、初版、修補前版本、實際 native inputs 與衍生範圍分開保存，原始 CLI 與最终報告各四份。這是來源及檔案記錄，沒有執行 native／C++／Lua／API／DB／SQL、建置、測試、部署或重啟。
