台版全世界地圖傳送資料 — CUSTOM-0155

本目錄由 C++ 核心讀取，不新增 Python 執行期或玩家資料庫變更。
原始客戶端的 CAN、MapInfo、MDL、HMD、MBD、ROM 資料為主要依據。
NPC 對話／事件傳送另外處理；本目錄不宣稱全遊戲傳送已完成。

資料檔
catalog.json：587 個有來源與導航的場景、2399 條指定座標移動傳送、195 個指定非零例外。
grids/*.json：287 個原資源導航；重複 HMD 實例共用幾何，但保留各自 CAN scene 身份與出口。
source-index.json：全部 613 個原 CAN selector、1619 筆原 MDL 附加引用及逐項狀態。

catalog.json SHA256
0146feeb50d96a99ca5a494900b652b010532295f6f64e4da8addfbb22561c53

導航規則
width／height 為格數；masks_hex 每兩個字元是一個格子的原始觀測集合。
0：沒有已知觀測；1：原值00；2：原值01；4：原值02。
3／5／6／7 為跨已載入窗口的不同觀測集合，不能一律當成可通行。
只有明列的 195 個原 marker 端點允許 mask6；各筆附所有 present-window 原值及來源 pins。
每個例外都只有01／02，沒有00或unknown。其他衝突與未知格維持拒絕。
所有移動傳送都需有可通行相鄰接近格，並在落地後仍有可行走鄰格。

來源與自訂政策的區分
同 MDL：使用互反 model 相同 marker slot 的原始投影座標。
跨 MDL：優先原 primary marker 到互反 model 的 auxiliary marker。
primary 不啟用但原 auxiliary 有值者，另明列 auxiliary 到互反 primary。
22 條 preferred auxiliary 已知不可走者，改用同一精確 target model、原448980查詢的 matching primary slot。
該22條均保留拒絕的原 auxiliary／mask 與選定原 marker／mask；不找最近格，不跨 model 換落點。
這些是已授權的固定服務端啟動／落點規則，不宣稱恢復原官方服務端規則。
HMD 實例先保留26個楓華鎮與6個崑崙既有綁定；其餘只在同area、同canonical HMD路徑及同decodedSHA的未佔用CAN alias之間固定分配。
363 個 HMD placement 綁定與82個未使用alias均有明確證據，runtime不做firstmatch或重新分配。
三份已補公布欄的城市MDL，其現版與原版非空導航material已逐項比對相同；門的record依完整SHA及marker身份重定位，不用過期offset猜測。

驗證界線
142 個 MDL 的32701個完整窗口，C++批次輸出與獨立Python參考逐窗及整張mask一致。
144 個一般HMD的C++與獨立Python逐格一致；Office另以台版REA確認零面積overlay是原生no-op，再由C++與獨立Python核對。
全窗口僅保留摘要與SHA；不在產品內存放重複raw窗口。
所有287個grid在移入本目錄前後均核對完整SHA。
原有280條指定傳送tuple全部保留；這是來源與集中測試資料，不等同2399條都完成原版遊戲人工驗收。

缺口分母
26個CAN selector的canonical asset缺失，維持未登記導航；不能以其他parent的同名檔代替。
99個原候選的端點是blocked／含00衝突，2個沒有可接近或可離開的鄰格，維持來源個案待查。
506個primary／auxiliary slot均未啟用、498個缺matching marker，是原始slot個案，不代表1004個遊戲入口故障。
4個target anchor無唯一／現存候選，以及4個單向引用缺matching marker，不憑空製造落點。
NPC對話、腳本與事件入口的分母另計；whole_game_teleport_complete維持false。

4組HMD的6條返回補充：原outdoor auxiliary缺失或為00時，只使用同一固定source record的matching original primary，逐筆保留被拒aux與選定primary的座標、marker slot、SHA與格值。這是CUSTOM-0155明確返回政策，不是nearestcell或原官方服務端恢復。其中gold與towertop原HMD沒有exit marker，僅這兩間明列CUSTOM返回政策：先走離，再重新踏入原arrival marker返回；原落地與no-op不觸發。不是把缺失exit假稱恢復。全部363個HMD綁定現在至少有一條可接近的進入與返回點；仍需遊戲內驗收。
