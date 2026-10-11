# 新角色出生地圖修正（2026-09-26）

## 實裝範圍與來源

- 新建／尚無位置存檔角色的世界進入封包改用崑崙仙界：area4、scene3、kind0；不再套用楓華鎮2/4的新角色預設。
- 地圖身分依當前客戶端資料、Island03.can scene3資源選擇，以及使用者確認。來源詳見 native-kunlun-birthplace-evidence-20260926.md。
- **原生出生XY尚未還原**。126/126為CUSTOM-0040暫用座標，僅有通行資料及實機走動依據，不是原服出生點證明。
- 已儲存位置的角色按原位置登入；不搬動玩家、不修改帳密或客戶端EXE。

## 通行與封包

CityI2原生MDT/MBD/MDL建立144個63x63視窗，12x12區塊；C++與Python視窗逐位元組核對。252x252整圖共53,782格具有一致資訊，461格視窗衝突一律拒絕。126/126附近5x5均為一致可走格。導航JSON SHA256：d429b1f94a9c1e2cf1bb8d0194213a25de22b9bb86c036a335d5c6952ddd95aa。

RecoveredMovementService以area及scene驗證移動與存檔，4/3重新登入維持kind0。既有楓華鎮／室內／島嶼轉移保持area2限制，不能將崑崙角色套入診斷城鎮門路。世界首次tick、背包、聊天及同地圖可見性接納4/3；本項不製造NPC、怪物或任務位置。

## 驗證

- CTest：kunlun_birthplace、recovered_movement_service、config、database，4/4通過。
- 隔離TCP／SQLite：test_owned_companions_server.py，4/4通過，含4/3首次進入、移動、伺服器重啟回存及既有town儲存相容。
- 隱藏God2Lab實際客戶端：private-kunlun-birthplace-20260926-03通過。只讀原生actor root（UI+86888指向root+90）確認kind0/scene3/area4；實際滑鼠走動後SQLite為4/3/126/128/revision2，客戶端仍存活。
- 第一輪觀測器錯把role source當actor root導致map0；已修正觀測偏移，沒有改伺服端封包配合錯誤測試。
- 第二輪混入既有合成神仙／戰寵圖像測試，不適合作為出生走動驗收；出生專用fixture已移除隔離DB內該批合成companion，未動正式玩家資料。測試範圍不宣稱合成companion圖像已完整。
- 全程不切換使用者桌面、不截圖、不寫入客戶端記憶體；來源DB及正式／隔離客戶端EXE雜湊不變。

## 發佈

候選：build-town-visibility/Release/god2-server-kunlun.exe。
發佈資料夾：artifacts/releases/kunlun-birthplace-20260926-01，保存原執行檔、設定及SQLite線上備份。正式啟用與資料保留結果依verification.json；最終相同候選的實機結果依private-kunlun-birthplace-20260926-04/run-result.json。

本輪出生「地圖」改正與封包／存檔串接已驗證；精確原生出生XY仍是缺口。全專案完成度維持約11%的規劃估計，並非所有原生封包已實裝的量測百分比。

正式套用已完成：port2592監聽、PID1808；verification.json全部通過，所有既有資料表內容未變，4帳號／3角色保留。最終04實機驗收與正式候選EXE雜湊一致，走動存檔4/3/126/128/revision2，使用者輸入桌面保持Default。
