# 陸服 WORLD33／39 目前選取列更新來源

本輪`20261008-cn-selected-subject-update-source`接續146。
PHASE1靜態來源串接，沒有建置、測試、native／C++／API／SQL執行或部署。
保留固定EXE、原始wire、全部歷史報告与既有凍結功能。

## 實際原生分支

原生world primary table4929D8：33 cell492AA4→491374，call49137E→
004D5880；39 cell492ABC→4913B0，call4913BA→004D5A90。兩者ECX均
為world+89B26C，payload=logical+1。case後的490AB1尾段尚未在此閉合。
length table567CA4：33 cell567D70→567B85返回2；39 cell567D88→
567B9A返回17。這是WORLD S2C的階段關聯，不是同opcode的C2S因果。

兩個consumer都先读UI+430A8→role，再讀role+D0目前選取row pointer；
null直接返回，不搜尋名冊、不建立新列，不含封包subject ID。
所以不能對整個名冊廣播相同更新，也不能把封包第一byte當成對象ID。
收件者自己的實際selection、先前30造成的選取變化及逐record次序必須
由真正owner資格化，不能預設第一列、丟棄舊選取或猜共同角色。

WORLD33 logical2的payload BYTE寫row+40，然後tail到004D3E30；
caller40B局部CFG保留這個外部frontier，helper198B另從真入口追查。
helper以signed WORD UI+1C84C8>=0為門檻，在group1D的controls
1A/1B/1C/1D，按bits8/4/2/1選擇資源7/8/9/10，未設bit時為-1。
高四bits仍完整寫row40，但不被這四個icon分支讀取；不猜狀態名稱。

WORLD39 logical17／payload16：

| payload offset | 原生讀取 | 寫入目前選取row | 原生UI |
| --- | --- | --- | --- |
| 0 | DWORD bits | 2C | control4第一個%d |
| 8 | DWORD bits | 30 | control4第二個%d |
| 4 | MOVZX WORD | 34 | control5第一個%d |
| 12 | MOVZX WORD | 36 | control5第二個%d |

literal7EF9B8為`%d/%d`。DWORD原bits保留，傳入signed32 decimal時
可能顯示負數；兩個WORD明確zero-extend，不能稱為signed16。
payload6/7/14/15四bytes在此consumer未讀，原包完整保留。
不自創其語義、HP/MP名稱、padding或零值。這不是64位元擴充完成。

相鄰32是另一種目前選取列的resource string更新：2B logical，
004D5A10讀resource+D5354的signedBYTE最大值及D5356+index*5E，
copy string到row+13，再更新control3。資源／完整邊界未恢復，本輪
不接入32、不拿GOD名字或NPC表替代；保持為具體下一追查位置。

## 來源接合

新增`CnSelectedSubjectUpdate`，精確讀33／39兩種完整record，保留
所有bytes，提供帶原位寬的fields與純readonly selected-row projection。
從實際非null的3EC-byte列只改已資格化的40或2C/30/34/36，其餘
bytes保留；缺實際選取列時不製造zero row。native null-pointer no-op
與缺失／過時來源要由實際owner區分，不能當作通用成功。

既有`CnPrebornSubjectState`可選native-source snapshot現在保留整個
實際選取row原bytes，新增Current前後的project_selected_update，
供研究／實際來源資格化使用。process memory／pointer不是自建服務
運作前置条件；直接使用真正服務端owned row也能做同一readonly projection。
舊skill references／identity／Current／bounds／選取政策保持。

既有`SharedSubjectRosterPublication`有序variant加入33／39，保持原
bytes／次序／held batch，definitions及template name vectors仍逐record
對齊。最低record為2B，preflight bytes budget同步改用2B；同一frame
最多2560B、同一batch最多256frames及實際queue容量政策保持。
required Qualify明列每筆實際selection／null no-op、前面的30／reset／
select演變、common identity／fields／rules／save／durable replay／issuer。
沒有自創handler、回覆、ACK或共同屬性數值。

本輪新增typed forms2、readonly full-row source handoff1、既有有序
publisher forms2；新增WORLD S2C33/39來源關聯2，owner增量0，
新opcode值／完整雙向路徑0。真正common selection／field semantics、
規則、存檔、重播、committed issuer及Application仍未配置。
完整TW/CN/PC/網頁/WSS、全部玩法及變體、numeric64／堆疊99、
集中測試修復／可恢復發布目標保留，百分比未知。仙幣99999999999，
其他上限另定、等級不改，native字體與文字轉換保留。
