# 全 NPC 原生位置：重建碼追查與解析器修復

2026-09-27。使用者要求繼續從現有解殼 EXE／重建碼挖取原生擺放，
所有位置須有原始依據。本輪不使用退役資料，也不以預設方向或任務文字
補出缺少的完整 NPC 記錄。

## 目前可實裝結果

**本輪新增完整 area／scene／NPC身分／x／y／面向配置：0 筆。**
全 NPC 原生擺放仍未完成，正式 native-only 限制保留。
沒有更新正式服務端執行檔、生成測試 NPC 或改寫帳號／存檔。

本輪確實修復地圖來源解析限制，並查到先前反編譯未辨識的座標函式。
這些成果不能換算成已恢復的 NPC 數量。

## 已完成的新增追查

| 路線 | 新證據 | 是否能生成原服 NPC |
|---|---|---|
| NPC pool／writer | 核對51函式、145引用、12段未索引程式；補4CCEC0座標setter，本地467CD0是FFFF滑鼠標記 | 否；座標來源仍是caller／接收記錄 |
| 當前資產 | 8,365檔頭；109CSVZ全解碼；190RTB結構核對；4INI串到IP／port／socket | 否；無完整身分＋場景＋位置＋方向配置 |
| 地圖座標表 | 原生144鍵lookup與UI anchor完整返回；區分地圖投影基準、網路actor標記與worldNPC | 否；不能把同樣packedXY欄位跨命名空間拼接 |
| npcAD模型 | ROM→6 TileModel→ModelDat→3來源placement；確認是佈告欄，原始grid92/72、93/72、94/75 | 未證明互動NPC身分或面向；不重複生成 |
| CityI2 MBD | 原生MAP writer確認TileIdx／LinkIdx／TileNum／SpriteNum／Pass／PalNum；補未export438210 | 否；地形／資源欄位不是NPC世界配置 |
| MDL解析器 | 零寬／零高Pass與ROM路徑字串保存資格化；明確分析選項完整解析142／142份來源 | 解析修復；不自動認證其模型為NPC |

完整來源解析保留12,140筆模型定義、169,522筆靜態模型位置，
以及15個檔案中的34個零尺寸格。這些是地圖模型數量，**不是NPC數量**。
預設ROM路徑限制與正式runtime保持原狀；明確分析選項不會開啟ROM引用。
原生Pass10案例、634個來源路徑字串複製及13個拒絕案例通過，
正常與最佳化模式均有收據。

相關回歸：binary producer 10／10、outdoor MBD 11／11通過。
Town MDL完整執行先有5項通過；第6項保留的舊「兩層parent路徑必拒絕」
假設與新原生證據矛盾。已更新為明確分析選項下的合法來源路徑，並保留
三層parent、絕對路徑、UNC、前置slash與中途parent拒絕；該項單獨重跑通過。
沒有為了通過測試而放寬預設模式或runtime檔案讀取。

Data3另做有界補查：未列出新的MDL／HMD；兩個CSVZ頭部分別為
Message2的BlockMsg／ReserveMsg，以及SpgEft戰鬥特效表。
頭部與全檔／解碼雜湊另存
`artifacts/research/npc-asset-inventory-20260927/data3-csv-headers.json`；
這只是頭部辨識，不宣稱完整解讀其所有欄位。

## 證據與重跑

- [NPC位置寫入與漏辨識函式](current-npc-position-writers-20260927.md)
- [資產與網路配置調查](current-npc-asset-inventory-20260927.md)
- [地圖座標與佈告欄完整鏈](current-npc-map-coordinate-join-20260927.md)
- [MBD欄位原生執行](current-npc-mbd-cell-followup-20260927.md)
- [MDL零維度解析修復](current-mdl-zero-pass-20260927.md)

現用God2.exe SHA256：
`6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`。
相應工具各自保留原始位元組、offset、hash、執行邊界和測試資料來源。
研究資料輸出不替代實際原生NPC擺放驗收。

## 剩餘缺口與可追位置

已確認的NPC建立分支讀服務端72記錄的方向和packed位置；
新補本地入口／移動／初始化分支尚未提供原服完整配置表。
完整重建客戶端接收程式也不會自動還原未儲存在程式內的原服輸入資料。

尚未全域封閉的程式邊界包括4CCEC0的間接／interior-entry可達性，
以及world owner464910／46BCC0跨函式別名對NPC record的存取。
地圖靜態模型能否產生真正互動NPC身分，亦須沿hit／C2S鏈另行證明。
當前資料中沒有資格化這些缺失關係，不能將查不到的面向填0或把名稱
相同的模板／模型強行合併。

整體工程完成度仍約11%的規劃估計；不是封包覆蓋率或NPC實裝百分比。
