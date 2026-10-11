# 崑崙仙界出生位置：原生證據邊界

2026-09-26，只讀當前 Data2、現用 EXE 重建結果及既有 current 路徑分析。
未讀取退役實作／資料庫，未啟動客戶端、修改玩家位置或正式資料。

## 結論

**本輪未找到可證實的新角色原生出生 XY。**
可確認崑崙仙界的地圖身分 `area=4, scene=3, kind=0`，資源為
`Data2/map/Island03/CityI2/cityi2.mdtZ`，且原生對話明確將這裡描述為
初來者學習基本功的地方。這些證據不足以選定出生格。

`Map_City_Coordniate` 的318/363超出這張252×252地圖範圍，不能當出生點。
任務文字中的花／師傅座標也不是玩家出生點。未提供替代、猜測或隨機座標。

## 當前資源的直接核對

`artifacts/world-atlas/current-maps.json` 的來源行21097保留：

* area4、kind0、scene3；名稱原始CP950 `b158b15ba550acc9`（崑崙仙界）。
* 圖層寬252、高252；catalog_x318/catalog_y363。
* MDT路徑 `Island03\CityI2\cityi2.mdt`；記錄SHA256
  `f6d2d9389b1656741a548a85b4be608f35289cf958235331a2b36b55d3d7fd2d`。
* catalog 的 `spawn` 本來就是null，沒有來源出生欄位。

本輪重新從原始 `Data2/map/Island03/Island03.can` 執行既有有界解析器：

* SHA256 `5a176c2bde2c1c98e4e853213cb7017d114eb4ac0f7dae9e0810f91fc806e727`。
* 16個檔案記錄、20個scene索引；**scene3→file index3**。
* file3路徑 `cityi2/cityi2.mdt`，原始tag2；tag不是網路kind值。
* file3原始記錄SHA256
  `266a6eb23eb2625680001086c5e5c4de637b4cd24ebd256a53652f43e4dcea3b`。

當前 `cityi2.mdtZ` 可由既有LZSS解碼器直接解開，開頭為
`MDT v1.2`、`DTime 1091766271`、`MAPNUM 12 12`、`RomFile 3`。
其壓縮SHA256 `292d0011561d97214fd77adcd0e0121a31b491b13bb26309c96fe4617630695e`，
解碼SHA256 `b8332fae2c3b0472a67a16fb1c7ed689002c859cf223e68003d0052638d22080`。
MAPNUM為資源組成資訊，不是出生座標。

## 原生新人指引：地點有據，XY仍缺

`Data2/Patch/Comm/NPCNormal02.csvZ` 壓縮SHA256：
`84a7ea509e4da4fbcb6b971d5c2f149fb944311aa4654f6c6c913267ed4335fa`。

* 實體line639、text ID1637：描述「這裡是崑崙仙界」，教導初來者基本功，
  要先晉見元始天尊；没有數值XY。
* line637、ID1635：中央轉生台找元始天尊。
* lines634..636、IDs1632..1634：東南恭讀房、東北神仙密室、北方練功房。
  這些是指引方向，沒有精確出生位置／出生marker。

`Mission_data.csvZ` SHA256
`659c8f38ffd9c34107969b449afd16488665a08970110910c9aed8448a0bb716`：
lines216..234的任務44..50包含新人基礎知識、採花、澆水、合成、掃地、戰鬥。
line219的140/87指仙花；lines226..229的153/157、153/162、153/174、153/179
指各合成師傅。不能把任何一個轉成玩家spawn。
text ID、Mission_data ID和NPC世界身分也是不同命名空間。

## 當前原生載入相容性

重建函式VA `500180` 的場景切換路徑先用 `46BB60/46BC00` 取area的scene0
資源基底，再由 `46C620→444F70` 載入CAN。actor kind2走室內HMD分支；
kind0走另一分支，用CAN的scene索引取相對路徑，經 `46C520→444B80` 進入
戶外MDT loader。因此area4/scene3/kind0與現有CityI2 CAN/MDT資源相容。
area4的scene0記錄指向 `Island03/Island03.mdt`，不會誤用Island01根目錄。

這是原生分支及原始資產相符的靜態證據。既有
`test_current_scene_resolver.py::test_town_packet_selects_native_outdoor_loader`
實際跑的是area2/scene4；**本輪未把它冒稱成CityI2完整loader／renderer驗收**。
CityI2的地形、碰撞、可行走格和實際原生進場仍需個別驗證。

正常world-entry consumer VA468160由S2C2A讀位置：RVA68636..68659解析body+28
的kind:2、x:15、y:15；這是伺服器輸入的欄位，不是本地新角色出生生成器。
空參數的離線分支RVA688D0寫2E8/326等診斷actor值，並未建立新角色出生身分，
不可拿來當崑崙spawn。既有area2/scene15/(17,13)保存進場記錄也不是新角出生證據。

## 可做與尚缺

可持續實作area4/scene3/kind0的**地圖載入相容性**，但不能以地圖中央、
任務NPC、地圖catalog數字或任選可走格代替原生出生點。
缺少的直接證據是：匹配當前build、已確認fresh-character流程的原服S2C2A
位置記錄，或具有明確新角色用途的原生spawn表／生成函式。
本輪已確認的新人文字可以定位應追的教學流程，尚不能填這個XY欄位。
