# Current WPN definition / instance → world selector field audit

## 結論與本輪新增證據

本輪未找到可整合的原生 `owned item → DA binary/category/ordinal/variant`
映射。這是下列限定路徑的結果，並非宣稱整個客戶端不可能有映射。
沒有修改 runtime、client、DB、桌面或既有來源；未讀退役來源。

新增獨立工具 `tools/strike_lab/current_weapon_mapping_fields_20260926.py`
完成 **16 組原生 definition parser 差分**，正常／`-O` 均 PASS。
新證據不是 icon 順序或名稱比對：它直接測試疑似 source mapping 欄位是否進入
客戶端 396-byte definition。兩個基準都是當前真實來源：WPN key1／TWP key19001。
測試修改值只存在離線 VM 輸入，不能作為正式物品資料。

| 0-based source 欄位 | 原生差分結果 | 使用界線 |
|---|---|---|
| 1 | 改成99後，396 bytes 完全不變，parser未讀此欄 | 全部WPN值0..10，TWP值0..11。2026-09-27已核對RowDesc原名「類別代碼」及ItemType分類清單；仍不能把它當DA category，見current-weapon-category-source-20260927.md |
| 2 | 改成`Probe_Tag`後完全不變，未讀 | `Wpn01001`等source tag沒有經這個loader保留 |
| 30、31 | 分別改成17、18，完全不變，未讀 | 實際630 WPN及629 TWP的這兩欄全為0 |
| 26 | 僅metadata+11C改變 | 已知tooltip第一數值的range width |
| 27 | 僅metadata+11D改變 | 已知tooltip第二數值的range width |
| 28 | 僅metadata+11E WORD改變 | 已知encoded level顯示欄位 |
| 29 | 僅metadata+120 BYTE改變 | 已知攻擊距離consumer讀取欄位 |

每组比較完整396 bytes，不只比較預期offset；另外核對原生token accessor的實際欄位紀錄。
原生 `4599B0` 逐row讀column0作key，配置396-byte記錄並呼叫`459420`。
本輪離線執行`459420`至完整return，再執行`459A60` lookup。
`4599B0`只作靜態對照，沒有宣稱整個來源載入器的動態驗收。

## Definition tail：已知路徑與不能成立的外觀假設

此段引用已存在的 `current-weapon-attributes-snapshot-20260926.md`，
不是重新宣稱恢復的新戰鬥公式。

- `459420` WPN/TWP selector1/25，source26/27/28/29保留到+11C/+11D/+11E/+120。
- `4B45B0`把20-byte instance轉為六個WORD，交给`4B4200`文字formatter。
  `4B4414`讀definition+11C；`4B448B`讀+11D；`4B4467..4B4479`
  算`value+width`／`value-width`並送sprintf。labels520/522是物攻／魔攻。
  所以5、3（菜刀）和6、4（精淬菜刀）在已追到的消費路徑是tooltip範圍值。
  這不排除某欄可能另有用途，但沒有證據可把它兼作DA selector。
- `4B6020`以definition+11E產生等級條件顯示；`517940`附近由本角色slot34
  itemkey→`459A60`→definition+120取得reach。這條明確的裝備查詢沒有產生DA component。

## Instance：排除容易混淆的型別分支

普通武器WPN/TWP的instance family為1／25（DWORD0 bits16..21），
tooltip `4B5BE0`相應case進`4B45B0`，與外觀resolver是兩條資料流。

本輪核對`4D53F0`／`4D5970`：它們也讀definition+11C及instance bits25..31，
但`4D53F0`原生assert文字直接標為 **`CPMenu::PetEgg_Open`**，
其實際特殊分支是family0E／0F。這裡的7種轉換及UI動畫選擇不能拿來推普通WPN外觀。

`4B4AB0`另外從instance DWORD+4／+16各取兩個11-bit值，非零時加10000再
經`459A60`取得附加item的名稱／描述並組tooltip。它不是把這些bit直接交給HeroDoll。
此處只是靜態資料流核對，未擴大為完整tooltip執行驗收。

`4999C0`掃裝備30..37及bag0..29，比較同key與instance DWORD+0C的bits8..14，
使用`<=2`／`>=3`門檻選替換來源並送`496550`。這裡尚未給該bitfield任意命名，
也沒有將其值提升為world variant。

沒有證明20-byte instance每個未解bit都與外觀無關。只能排除以上已追路徑作為
目前映射的直接證據；其餘bits仍要保存，不能清成推測的外觀值。

## Producer / consumer 缺失邊

沿用已合格的 `current-player-equipment-frontier-20260926.md` 與
`current-weapon-appearance-20260926.md`：

- C2S28 `496550`只送key、source slot、flag（完整5 bytes），沒有DA component。
- S2C3B保存完整20-byte instance；S2C41只改count及key低WORD，沒有外觀重算。
- ordinary self DA consumer`503D30`從收到的payload+6取8 bytes交给`461270`，
  再保存world+1539ADC0／+1539ADC4；此條路徑沒有`459A60`的item查詢。
- `461270`對weapon component3解binary/category/ordinal；variant由第二byte高3bits。
  這能消費一個已權威提供的selector，不能反推哪個WPN應該提供它。

**仍缺的精確邊：** 同一已知owned key及完整instance裝備前後，對應原服權威DA
8-byte after-state；或當前原始server資料／程式直接提供該轉換。
Source column1仍可作來源側的下一個候選，但本轮已證明它不經標準item definition
loader保留；應找它的另一個原生消費者或原服paired transaction，不能用值域／suffix配對。

## 可重跑證據、身份與限制

```
python -X utf8 -B -m tools.strike_lab.current_weapon_mapping_fields_20260926 --output artifacts/research/current-weapon-mapping-fields-20260926/native.json
python -O -X utf8 -B -m tools.strike_lab.current_weapon_mapping_fields_20260926 --output artifacts/research/current-weapon-mapping-fields-20260926/native-optimized.json
```

兩次exit0。JSON保留1259來源rows的欄位分佈，以及全部16組修改值、accessed columns、
完整metadata比較的實際changed offsets。對source column1每個不同值，額外保存第一份
真實row的全部32個欄位（CP950文字及原始hex），附key與精確來源行號。
此欄實際是ASCII十進位數字token；WPN有11種值，TWP有11種值（TWP缺9，有11）。
來源沒有宣告它的C++型別，標準loader也沒有把它讀成某種整數寬度。
這是欄位資格測試，不是完整遊戲功能驗收。

- current PE SHA256 `6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`
- gamedata CSVZ SHA256 `70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`
- 現存current-native mapped image SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`

工具先核對目前PE的完整hash，再比對NativeItemMetadata所有實行code spans與現存映像，
確保本輪parser結果符合當前build。本lane沒有重跑world ROM loader。父代理其後已在
獨立VM修正fixture累積heap問題，四個selector完整461270 return正常／-O通過，
見更新後`current-weapon-selector-authority-20260926.md`及`selector-authority.json`。
該資源consumer成功仍不提供WPN→DA mapping。按有界任務在此停止。
