# NPC 原生擺放反推：本輪彙整

## 實際新增

本輪完成的是 **47組去重後的人物／場景／座標文字約束**，
不是47個已實裝NPC。完整出生／面向／世界身分配置仍0筆。
沒有隨機擺放、預設面向或復用測試嚮導位置。

| 路線 | 結果 | 完整spawn資格 |
| --- | --- | --- |
| 原始文字與catalog | 25來源、1170座標token；48條逐句核對、47組去重。完整原名與全部候選保存；果力村四位為唯一同名候選 | 未有面向／世界實例／出現狀態權威 |
| 面向反推限制 | 四個原文座標×八方向，32原生slice向量通過；相同位置不能從已查欄位唯一推出方向 | 不生成 |
| 未匯出setter | 14函式、2686指令rows核對、16原生vectors；查明direct／literal候選不是有效外部來源，computed callers仍開放 | 不生成 |
| 地圖模型互動 | 配置field9已追到palette，而非面向；佈告欄action與C2S互動序號不是同一命名空間 | 不冒充worldNPC |

模型互動lane另通過12個完整render初始化、14個原始action查找、
7個hit／NPC gate及4個world caller slice；1302個不同原生instructions
逐byte核對。normal／`-O`收據相同。Image是source PCX尺寸header fixture，
未做pixel decode或實機mouse；其37個案例不換算成37個NPC配置。

原文副本NPC包括擊敗後暫時消失、封印物限制等條件；未將它們改成
永久常駐。田清郎的隱形狀態、多義仙童、真假齊慕與九天冰屋2F等
歧義都有保留，不以同名或同句共現解決。

## 可重跑證據

* [文字約束與完整候選](current-npc-text-constraints-20260927.md)
* [四個座標與原生方向自由度](current-npc-reverse-constraints-20260927.md)
* [setter與場景資源來源](current-npc-reverse-source-20260927.md)
* [靜態模型互動](current-npc-model-interaction-20260927.md)

本輪所有查核不操作使用者桌面、不啟動正式遊戲、不改client或存檔。
本機2592仍由PID13112監聽。本輪沒有部署新的NPC生成配置。

仍待追查：這47組文字约束對應的server-issued world instance／
面向／漫遊及出現條件，與剩餘computed或interior-entry來源。
反編譯consumer只給欄位轉換，不能唯一重建未收到的原服輸入。
文字約束是新進展，但不能用來宣稱所有NPC已還原。

整體完成度約 **11%（工程規劃估計，非實測NPC或封包覆蓋率）**。
