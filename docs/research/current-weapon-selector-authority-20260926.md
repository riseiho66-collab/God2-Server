# 武器 selector authority：本輪新增的原生資源邊

2026-09-26。有界追查；只讀目前台灣客戶端、既有 current native image 與重建EXE，沒有操作UI、修改正式client／DB或讀取退役資料。

## 結論

本輪補齊的是 **WPN→物品圖示 action** 與 **DA packed selector→HeroDoll 世界武器 art** 兩條各自可驗證的路徑。沒有找到連接它們的原生 item→世界武器 selector 規則，不能把 `Wpn01001` 的數字後綴直接轉為 `r1w000`。

上一份 `current-weapon-appearance-20260926.md` 的缺口仍成立，但現在已能指出確切資源層斷點；不需再重複檢查59420是否讀source tag。

## 新證據一：+118其實是物品圖示 action cache

當前source RomMaps第0列涵蓋icon ID1..6000，路徑為 `data2\ItmImg\WPN01.rom`，實際檔案是 `Data2/ItmImg/WPN01.romZ`。

481700在UI初始化階段遍歷物品metadata；對有效group做：

1. metadata+116的RomMaps group加0x41，成為UI resource bank index。
2. 將metadata+114的icon ID交給41AE70。
3. 41AE70從該ROM record+108C取得action count，再逐一比較record+1090指向的ACT_DATA第一DWORD ID；把找到的ordinal存入metadata+118。
4. 找不到時另有fallback action1000，並非世界武器selector的fallback。

因此WPN1／2解析後的+118=FFFF只是圖示初始化前的cache狀態。本輪執行原生ROM載入＋41AE70後，兩者得到action index0／1（這些檢查在稍後world-loader失敗之前已通過）。這個數字属于UI圖示ROM，不能直接用作DA weapon ordinal。

當前WPN01.romZ有180個ACT_DATA。它的前兩個action ID是1／2，內嵌CP950名称為菜刀／砍刀，與原生metadata的名稱相符。這提供真正的item-art identity，但只到物品圖示。

## 新證據二：HeroDoll源表有明確世界刀 art selector

當前HeroDoll.csvZ採用兩欄合成key：例如`r1`＋`w000`。完整key不能只搜尋第一欄。

| source key | 源表標籤 | 未騎乘、action0時component3兩bytes | 實際ROM |
|---|---|---|---|
|r1w000|刀01|00 00|r01w000.romz|
|r1w001|刀02|00 01|r01w001.romz|
|r2w000|刀01|01 00|r02w000.romz|
|r2w001|刀02|01 01|r02w001.romz|

r1w000／r1w001位於解碼HeroDoll第208／209行；r2w000／r2w001為第293／294行。以上命名是源表自己的「刀01／刀02」，**不是證明它們分別就是菜刀／砍刀**。

原生lookup52460先以52260轉換component category/action，再用`r%d%c%d%02d`格式化key並做原生hash lookup。對component3，52260在合法action0..2保留輸入category。461270未騎乘路徑從DA兩bytes抽出binary低4bits、category高4bits、ordinal低5bits；第二byte高3bits另作variant。已有的mounted強制category8/ordinal0限制不變。

## ROM／CAN內容為何沒有補上item映射

r01w000與r01w001內容確實不同，卻都有ACTINDEX4201及19個ACT_DATA；前兩個動作名稱是一般角色動作，不是菜刀／砍刀。ACTINDEX不是WPN ID，也不是唯一art identity。r02對應ROM的ACTINDEX另為0；四個來源的完整載入與461270返回均在下述隔離重測中通過。

這些RoleDoll ROM的ACT_DATA／ACT_STEP／ACT_POOL／ACTBLOCK描述動畫及圖塊。已解碼檔案沒有`Wpn01001`／`Wpn01002`字串。這只是這五個具名檔案的有界結果，沒有宣稱全客戶端不存在其他映射。

**精確缺失邊：** owned item key或源tag → authoritative world `binary/category/ordinal/variant` after-state。現在左右兩端各有native consumer/source，尚無原生程式、源表欄位或可信原服同一次equip的before/after packet將兩端連在一起。源表上的「第1階」和HeroDoll的「刀01」只能產生待驗假設；不能升級為native rule。

下一份真正能改變實裝資格的證據應是：同一角色已知WPN key與完整instance，對應原生裝備操作及S2C DA的before/after；或當前來源中實際的server item→appearance欄位／程式。僅再找到同名或相鄰編號art檔不會補齊這條邊。任何先行指定對應只能標記custom，並另做own-server current-client acceptance。

## 本輪獨立工具與範圍

`tools/strike_lab/current_weapon_selector_authority_20260926.py`。

```
python -X utf8 -B -m tools.strike_lab.current_weapon_selector_authority_20260926
```

**更新重測：PASS，四個獨立未快取案例均到461270真實return。** 輸出保存在 `artifacts/research/native-weapons-20260926/selector-authority.json`。四個weapon handle均為3（各自VM中的bank ordinal），對應原生cache與實際載入的ROM路徑，不能把handle3当成跨VM或跨客戶端的固定weapon ID。

先前共用VM執行失敗保留作為歷史：新增配置診斷後，失敗實際位於第三案例r02w000，請求 `0xf00000`，單調配置heap已達 `0x10c24000`，固定上限 `0x11000000`。前兩個案例已返回，舊報告的「只完成第一個lookup」範圍過窄。受限CRT adapter記錄free但不重用頁面，累積案例耗盡fixture額度；此次每案例建立獨立VM，原有128MiB heap、16MiB單次配置界線均未提高。每案例使用67,178,496 bytes；沒有改遊戲函式回傳、ROM、resource cache或以假handle通過。

工具固定目前EXE SHA `6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`，並核對lookup／selector相關code bytes與current native image一致。HeroDoll／Drv來源沿用既有pin，五個新增art檔的壓縮與解码SHA均寫在本檔工具中。成功輸出包含source行號、原生handle、檔名、action資訊及完整hash；input/output canary與cache/path一致性全部檢查。

UI icon與各world案例使用分離的離線VM bank。原生ROM loader、解壓、action parser、41AE70、52460與完整461270執行原碼；Windows/CRT I/O與allocation沿用既有受限唯讀adapter。新weapon ROM確實含零長度ACTBLOCK，局部adapter將標準`malloc(0)`適配為unique可free pointer（實體配置1byte）；此適配本身未解決累積heap額度問題，獨立VM才讓四個案例完成。未改原生ROM、遊戲lookup回傳或renderer；此擴展只保存在本研究檔內。

不包含完整DA的503D30／remote redraw tail、graphics blit、畫面驗收或server公式。四種世界刀selector即使載入成功，也不建立WPN1／2 mapping。

## 本輪已固定的新增原始art hashes

- WPN01.romZ SHA256 `caa72d4dccafacd44a27346f3a8db2e15319960bf003966b835416ed6c189499`，decoded `eef95acad680643cdf07f570f124a273f7dfe112061596ef074736732ff9395f`。
- r01w000.ROMZ `e1b3ffeab4430ab92867094f4dd4a3a0f20942130cf704a5de5d94c0dd81e1ef`。
- r01w001.ROMZ `55a5a82b3095e1b3db1ac3f74b3d818befaea5eec5a043293ed8a0eabb523631`。
- r02w000.ROMZ `258e8757582e1f8a7a6373691e1ab3751914c8777c3e7fe6d36ba69314384a45`。
- r02w001.ROMZ `ff79ed937e1d0d85158a1485892b1470274c96d9cd00ad50f10da0d91edc16f7`。

其他decoded pins在新工具ASSETS中。源表selector與檔案標籤屬靜態native source證據；完整世界ROM consumer資格未取得，兩者分開報告。

