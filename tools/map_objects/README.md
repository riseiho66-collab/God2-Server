# 台版固定地圖物件補片（CUSTOM-0151）

目標是台版原客戶端連接現用 God2-Server 時的固定裝飾。這套工具產生
客戶端地圖補片；服務端不需要新增假 NPC、改封包、重建核心或寫入遊戲 DB。
它不恢復公布欄任務或點擊互動。

| area/scene/kind | 原地圖 | 補片數量 |
|---|---|---:|
| 2/4/0 | island01/cityi1/cityi1.mdlZ | 1 |
| 5/27/0 | south002/citys02/citys02.mdlZ | 5 |
| 5/51/0 | south002/citys09/citys09.mdlZ | 1 |

## 來源與位置

只接受程式內 SHA256 鎖定的台版 MDL、框架 ROM 及原 npc2584.ROMZ。
後者 SHA256 為
`151033be38448d6f1dabbc1314caad3546f8da80a9be3bab4c754cd85d74b2ed`。
正向用 ACT1101（80×150、pivot80,128），反向用 ACT1701
（80×141、pivot0,120）；每組一片、palette0，原圖像素完全不改。

以第一根柱的全域像素基準推導，正向牌面左上角偏移(80,32)，反向
(-80,40)。加回 ACT pivot 後，模型 anchor 分別偏移(160,160)與
(-80,160)，grid 分別偏移(-2,+6)與(-5,+3)。模型 frame offset 為0；
ACT pivot 管影像位置，frame offset 管深度，不混用兩者。

新增物件歸屬 floor(grid/21) 的既有 block，再反算區塊內像素位置。
5/27 的426/407這組由第一柱 block4,6跨至牌面 block3,6，保持相同全域
像素與grid80,142，避免繼承錯誤的相機區塊啟用範圍。

這七筆是使用者授權、依台版原框架與圖件推導的 CUSTOM 固定裝飾位置。
原檔未提供原服務端 NPC ID 與七組框架的出生連結；不把它標成原生 NPC
出生資料。未來若恢復真正的公布欄 NPC，須撤銷對應地圖補片，避免重複。

## 產生與套用

獨立 C++20/MSVC 工具，不加入服務端主程式，不需要 Python：

```powershell
cmake -S tools/map_objects -B <小型建置目錄> -G "Visual Studio 17 2022" -A x64
cmake --build <小型建置目錄> --config Release
<小型建置目錄>/Release/god2-tw-map-objects.exe --client-root <完整台版目錄> --output-root <全新staging絕對路徑>
```

工具先驗完整候選，再發布 staging；包含三份 MDL、三份位元組相同的
npcboard.ROMZ及manifest.json。來源不符、重複套用或輸出已存在均拒絕。
MDL 保留所有原 Tile、ModelDat、Pass、placement 與換行，只新增列及修改
必要數量；原壓縮 header byte6 保留，輸出使用原生0516的literal編碼。

關閉該客戶端與登入器後，先完成獨立解析及原圖接縫檢查，再套用：

```powershell
./tools/map_objects/Apply-TwBoardPatch.ps1 -ClientRoot <台版目錄> -StagingRoot <staging目錄> -ReceiptRoot <全新驗證收據目錄>
```

套用程式只處理上述六檔，先核對來源及候選雜湊，保留三份小型原 MDL
作回復基準，失敗會回復已寫檔案。收據記錄六檔 hash。回復時關閉遊戲，
以收據 original 下的三份 MDL 複製回原位置，將新增三份 npcboard.ROMZ
移至使用者指定的待刪資料夾；不得誤刪原 npc2584.ROMZ或共用 OTH.ROMZ。

其他玩家使用各自的完整客戶端，亦須套用相同六檔補片；單改服務端
無法改變他們本機缺少的固定地圖裝飾。

## 驗證界線

2026-10-18：獨立工具 Release 建置通過。三張原圖共1852筆 placement、
所有既有模型碰撞資料逐位元組保留；新增1/5/1及單片圖像接縫已獨立核對。
外部證據位於使用者的 `.codex/artifact-archives/god2-server/20261018/board-object-rea`，
含純台版來源hash、七組原圖預覽、staging manifest及獨立QA。

原生依據為既有台版0044D750/0044C420/004421F0載入與繪圖鏈、0041AE20
ACT key查找、0044C980的0×0 Pass，以及00438920/00443DD0/00442F20
區塊登錄與啟用範圍；相關研究文件保留在 docs/research。

v2補片已套用到現用台版客戶端，六檔雜湊核對通過。原版God2.exe已透過
既有繁體登入器啟動，目標127.0.0.1:2592；EXE與現用服務端未更動。
2026-10-18 使用者已成功登入。現用服務端 session2 完成 world initializer，
回報 area2/scene4；原God2.exe視窗已實際呈現楓華鎮新增牌面。
這資格化該圖資在目前客戶端的載入與顯示，尚未完成全部走位遮擋驗收。

原客戶端實際登入、三圖呈現、鏡頭邊緣與前後遮擋仍須獨立實機驗收。
合成預覽或解析通過不代表已在遊戲內驗收完成。

現用服務端的移動scene registry目前未登錄area5的27/51兩張城市地圖。
其六組補片已套用且靜態驗證通過，仍不能算從目前服務端實際進圖驗收；
不得改玩家存檔或偽造NPC來冒充通過。
