# CN 世界5F怪物移動來源

輪次 `20261007-cn-world-monster-motion`；前輪catalog47。
階段一靜態原生恢復、來源整合、不可變封存與來源帳本；未建置、測試、
執行C++／Lua／原生client或server、存取正式DB或部署。

## 主指令與owner

CN固定PE SHA256 `582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`。
世界表004929D8[5F]→004919F4..00491A0A，logical21bytes，明確
this=main+1499FA0，body=logical+1，第二參數1，call004FC6A0。
同owner收71、74、78；不是player5E，也不是60的main+147C720。
世界60→00491DC0..00491DD6、第二參數3、call004FC7A0；來源不串入
71綁定。5F的第二參數不在限定004FC6A0內消費，保持傳入契約，不猜語義。

004FC6A0在256筆stride1D8 pool以bodyDWORD0 low16查已存在實例。
不存在則返回，不分配、spawn、回錯誤或補值。直接primary reads：

| logical offset | 欄位／操作 |
|---|---|
| WORD1 | zero-extended16-bit實例 |
| byte4 low5 | native state，改變時更新entry+E及title狀態；不是戰鬥能力 |
| DWORD9 | targetX=(word>>2)&7FFF、targetY=word>>17；low2保留 |
| WORD13／WORD15 | 供應anchor X／Y，兩個都是MOVZX，非decompiler所示signed short |
| WORD17 | clock delta=zero-extended word−40，以32bit machine arithmetic加本地clock |
| 其餘 | byte3、5..8、19..20與已知word內未消費bits保留，不默認0 |

primary004FC6E7／004FC6F2／004FC75C／004FC766明確zero extension，
所以anchor32768..65535不翻成負數。時間word<40沒有原生consumer
拒絕分支，不添加假最小值；不把本地_clock值當真正服務端tick或期限。
entry+20保存deadline；+180／+184保存anchor、+188／+18C保存target。

004FAC00若entry目前整格位置與anchor任一軸差>1就改為anchor；
清理queue read/write兩byte，再00481B90產生路徑，複製到slot的waypoints。
00481B90是逐格線段演算法與真實00470310格子查詢，最多20步；格子
拒絕就中止。因此target存在不證明路徑完整走到target，不把所有21byte
移動當傳送。slot queue使用另一組40容量的消費索引，但此產生器20步。
原生frame004FB5B0消費queue與插值；本輪只封存其bounded CFG，
沒有模擬clock／frames／render，沒有宣稱服務端已提供native路徑資格。

## 點擊研究的實際界線

0048AA10 entry-connected CFG找到：
0048AD07明確main+147C720→004FB5B0取得click slot；限定距離／返回37
及dialog advance資格後，0048ADEA→004B1FA0→C2S37 generic queue。
004B1FA0使用完整4bytes參數（保留high16）、low16寫本地選擇記錄；
原生timeGetTime差必須>1000才送。這是另一pool限定互動來源，不能
配成71怪物遭遇／戰鬥請求。

同0048AA10另外明確main+1499FA0的0048AF7C click和0048B924按level
區間選怪；使用的是entry+17B顯示低BYTE，而非完整能力，尚未封閉其
C2S producer／battle入場的完整路徑。0048AA10尚有0048AB01間接
jump未資格化，保留frontier；不因看到某callsite宣稱所有case完成。
4B1FA0之外31／68／6D等包裝路徑保留原盤點，未建立假C2S/S2C配對。

## 實際來源整合

新增 `CnWorldMonsterMotion.h`，只接受完整原生5F21bytes；完整保存
opaque欄位，公開unsigned anchor、target、raw state和timing word。
無空白builder、無硬塞速度／期限／方向，無自創response。

`SharedMonsterPublication` 擴充既有實際來源鏈：current common怪物
來源revision→原71私有binding／native low16 instance→真正world
qualify_motion(previous/current source, recipient, expected, full5F)
→當前ready/account/character/同場景再次核對→原始5F送入該連線。
required qualifier必須供應真正移動權威、anchor、格子／path、native
queue/clock與state。沒有實際authority supplier或Application掛載。

show71保存初始target/state；每次5F入佇列保存last_submitted_motion，
後續更新／刪除仍是同monster incarnation。保存的是最後傳送target，
**不是當前插值位置、完成path、client clock或已觀測native memory**；
qualifier不能直接把它当下一次anchor。原78更新來源revision不清除
expected motion；74／實際reset／輸出失敗失效原binding，舊5F不能
移動後來重用ID的新實例。仍要求同game thread並拒絕callback重入。
沒有新增DB表，怪物真實gameplay資料仍預設共用，TW凍結路徑未改。

本輪既有partial owner chain擴充，不再新增chain；CN WORLD5F來源
binding新增1筆。60及37只封存scope/owner研究，不算來源已接或新phase。
完整雙向路徑新增0，階段／變體總分母與完成率仍未知。

## 下輪未解

實際shared怪物spawn/移動/storage/visibility owner、nativecache、格子、
frame/clock/queue資格與Application仍需接入。點擊／自動選怪的真正
C2S戰鬥請求與1C入場identity，TW/CN同怪物呈現與跨版推播、全部
雙攻雙防／四維／五行／HPMP／攜帶技能及原生規則仍未完成。
