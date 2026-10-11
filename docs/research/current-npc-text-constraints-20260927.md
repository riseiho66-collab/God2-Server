# 當前 NPC 名稱、地圖與座標文字約束 — 2026-09-27

## 結果

從當前客戶端 **25 個指定來源檔**抽出 **1,170 個座標文字 token**；其中416個座標前緊鄰 NPCAppearData 精確名稱。逐句審核得到 **48條名字／地圖／xy文字約束，去重後47組**。其中兩組只有原文人物名稱，沒有 NPCAppearData 精確同名記錄。

**完整原生 spawn 新增0筆。** 所有結果的 `direction`、`world_instance_id` 都是 null，`placement_eligible=false`。此處的座標是原始文字提示，沒有把缺失面向補0，也沒有將 catalog index 當作世界實例ID。

這是既有851條文字提示審計的進一步關係核對，沒有重做109CSV／8,365資產清單。範圍包含 gamedata、Mission_data、NPCMission、NPCNormal、MultiMessage、DailyMission、DayMissionDesc 的當前非GB檔案；不是所有資產、所有NPC都已完成語義解讀。

## 可驗證的新候選

以下欄位皆保留原名，不做刪除稱謂、異體字、同義名或部分名稱合併。area/scene 是**精確地圖名稱的 catalog 候選**，不是已驗證出生實例。

| 原文人物 | 明寫地圖 → catalog area/scene | 文字xy | NPCAppearData候選 | 來源 |
|---|---|---|---|---|
| 廚師梁禎 | 果力村 →13/12 |108/110|2936|Mission_data:1488|
| 李樂 | 果力村 →13/12 |113/69|2937|Mission_data:1492|
| 阿銀嬸 | 果力村 →13/12 |69/72|2938|Mission_data:1494|
| 馬老伯 | 果力村 →13/12 |68/116|2939|Mission_data:1496|
| 張佑 | 果力村 →13/12 |75/123|2940|Mission_data:1506|
| 仙華僮子 | 果力村 →13/12 |110/114|3058|Mission_data:125|
| 成範永 | 茄城 →13/3 |82/66|2952|Mission_data:1498|
| 金熙 | 茄城 →13/3 |119/88|2955|Mission_data:1507|
| 農夫車允浩 | 茄城 →13/3 |143/150|2959|Mission_data:1518|
| 守衛大將軍 | 甘城 →16/2 |122/81|4622|Mission_data:2041|
| 傷病蘿蔔人 | 果城 →14/21 |131/62|5573|Mission_data:2164|
| 腰痛老人 | 昆吾鎮 →5/27 |150/61|5574|Mission_data:2165|
| 肥胖男子 | 暮汐村 →6/19 |55/70|5575|Mission_data:2166|
| 凍傷女子 | 焰霜鎮 →11/22 |170/97|5576|Mission_data:2167|
| 仙童 | 崑崙仙界 →4/3 |148/85|1673/1703/1819/1824/1836/1837/1838/1843/2014/2206/2866|Mission_data:577，另明寫藥草園|

果力村 catalog 指向 `North002/Cityjiu02/Cityjiu02.mdt`。來源字串是「**廚師梁禎**」，不是任意縮寫「梁禎」。馬老伯的當前原文是 **68/116**；本工具沒有讀取外部網站或用歷史座標覆蓋它。

其他已審核名字包括楓華鎮的涂諦頌、田清郎、齊慕、段嵐、曹大娘、仙鶴道僮、哪吒、董古、美食家、馴獸師、聖獸仙童；葛城的葛／錢／李員外、公孫望、百戲藝人、鄭立、鄭中、賣花的小女孩；南原部落的李管家、孫劭；昆吾鎮的燕三郎、宣逢、宜逢、林雄。逐條xy、原文、來源行、全部候選與hash都在JSON，沒有以同一城鎮的預設點替代。

## 舊座標格式搜尋遺漏：空格分隔

`NPCNormal02.csvZ` **line821、文字ID1819** 明寫：

```text
千里傳影I：請找一位「年輕女子」楓華鎮(71 69)
千里傳影II：請找一位「擔心的小女孩 」果力村 (51 85)
千里傳影III：請找一位「淘旨 」 (157/114)
```

本輪新增空格分隔座標支援，原來僅辨識斜線／逗號的模式漏掉前兩個。前兩者加入人工文字約束，**catalog候選空集合**；不可因找不到同名就挑另一名年輕女子／女孩代替。第三者保留提示，但這句沒有提供明確地圖，沒有擅自延用上一個果力村。

## 必須保留條件性與多義性

`NpcMission13.csvZ` **line309、文字ID12307** 有明確誅仙陣副本內容：

| 原名 | xy | 精確同名 catalog候選 |
|---|---|---|
| 秦天君 |48/41|577、5535|
| 趙天君 |35/165|580、5536|
| 孫天君 |167/170|590、5537|
| 張天君 |167/46|593、594、595、596、5538|
| 通天教主 |104/101|5539|

精確地圖名稱候選為 area8/scene3/kind3。原文同時說明天君被擊敗會暫時消失、持有對應封印道具時不能再次挑戰、進出副本會收走道具。這是需要保留的**條件性文字**，不等於已恢復伺服器觸發、冷卻或消耗程式；不能將五者作為永久無條件spawn。多個同名catalog仍全部保留，未按ID大小選取。

田清郎的同一句原文說他是看不見的隱形人；齊慕涉及真假身分；仙童共有11個精確同名候選，且另帶藥草園子位置。即使名稱／地圖／xy齊全，這些狀態／身分仍不應被靜態生成掩蓋。

## 具體排除的錯誤 join

自動結果中的 `map_names_elsewhere_in_same_row` 只是同一行共現，**不是地圖綁定**。人工約束才逐句指定人物關係：

* Mission_data line12 同時出現田清郎117/52與截仙遺址的玉鼎位置625/91；不能把田清郎移到截仙遺址。
* line34 曹大娘屬楓華鎮，曹爾在金鰲牌坊；不能讓整行所有名字共用楓華鎮。
* line380/385 的豹斑駒含追逐、移動與多位置，不列為靜止人物NPC。
* line1581 箱子312/240是取物目標，不列為人物NPC。
* line2168／NpcMission13 line435 明寫「九天冰屋2F」；不能丟棄樓層限定直接選地圖。
* 玩家位置、傳送目的地、採集物、地圖UI欄位即使含括號數字，也只保留未審核提示，不因regex命中就取得NPC權威。

名字匹配採最長精確名稱，避免把「聖獸仙童」降格為「仙童」，或把「傷病蘿蔔人」合併為「蘿蔔人」。人工選錄保留的是可核對約束，不是已完成所有NPC的宣告。

## 證據與重跑

工具：`tools/strike_lab/current_npc_text_constraints_20260927.py`。

每個來源保留壓縮／解碼SHA256；每條提示保留實體行、完整原始行hex與行SHA256。人工約束另附NPCAppearData原行和Map_City_Coordniate原欄位／來源hash。行hash不含行結尾；整檔hash保留檔案身分。

* Current God2.exe：`6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`。
* Current gamedata.csvZ：`70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`。

```powershell
python -X utf8 -m tools.strike_lab.current_npc_text_constraints_20260927 --output artifacts/research/npc-text-constraints-20260927/evidence.json
python -X utf8 -O -m tools.strike_lab.current_npc_text_constraints_20260927 --output artifacts/research/npc-text-constraints-20260927/evidence-optimized.json
```

Normal／`-O` 完成且輸出逐byte相同，SHA256：
`87a82fbb71bc4212af11cb778484b3a475111273491736329798857a7ad3e0ed`。

本輪沒有native actor執行、spawn驗收或runtime／DB／client變更。下一步可將這些source約束拿去核對原生actor記錄或原服配置；沒有方向與實例權威前，不生成NPC。
