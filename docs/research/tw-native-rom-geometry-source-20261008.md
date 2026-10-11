# 台服原生 ROM 幾何與地圖來源串接（第174輪）

本輪接續第173輪 HMD／ModelDat／Pass 來源，把需要 ROM 圖像與動作尺寸的台服地圖物件接入既有物件排序、格網及 retained movement scene。這是 PHASE1 來源實作與靜態逆向；完整原生發行、執行與客戶端驗收仍待全遊戲串接完成後進行。

## 台服來源與串接

使用既有完整 TW mapped image，SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`。CN ROM 實作只作比較參考，TW 行為另由本版原始指令確認。

`00429AB0`／`0042A1D0` 是檔案與記憶體 ROM reader。`0042AF40` 對不大於256的 unsigned action operand 進行位置查找，較大值查找第一個相符 DWORD action ID。HMD v1.6 的 action operand 保留完整 DWORD 位元，不預先截為 WORD。`0042D050` 讀取第一個10-byte step 的 command、frame 與 image index；`0042B4C0` 計算圖像尺寸減去 frame anchor 的動作範圍。`0044A800` 在宣告寬度為0時使用原生動作範圍，其他已確認條件使用宣告尺寸與圖像大小計算幾何。

新增 `TaiwanNativeRomAsset` 保有完整來源及已解析的原生 section／action／image 身分。缺少或未確認的 image geometry 保留未知，不用 Pass mask 高度、任意尺寸或自訂圖像填補。PCX 類型限定原生 positive signed16 尺寸、bytes-per-line 與實際寬度相符、逐列 RLE 無越界，以及完整 RWIF 尾表；TGA 類型限定已確認的元資料、像素與可選尾表完整域。這些限定外的輸入拒絕，不能宣稱全部格式完成。圖像幾何不等於渲染、調色盤、腳本或動畫執行完成。

根代理另現讀並保存完整 `0042D050..0042D157` 原始263-byte getter。`0042D0BE..0042D0C6` 只跳過非0 command、每次前移10 byte，沒有執行那些 command；找到0後才取得 frame 與 image。完整 first-step 缺少 terminal、缺少 frame／image 或像素資料不完整時都不能取得幾何，不建立跨 ROM command 支援的假象。

既有 `TaiwanNativeMapAsset` 新增明確的 ROM binding 路徑。每個 slot 必須與完整 ROMFILE 的原檔 ordinal、原文字 byte identity 及實際來源相符，保有各來源實際 resource generation；不從 ACTINDEX 推定 ROMFILE slot。`0044D520`／`0044D350` 提供原生順序與容量來源。`0044C580`／`0044A6F0`／`0044A210` 提供 v1.6 type7 metadata 到 action／image 幾何的呼叫來源。

新增路徑接至 body／layer2 model union、signed `screen_y + actual_model_height` 穩定排序、完整 mask material、既有 mode2 grid 與 scene Resources／Native。舊 explicit-only 方法保留原簽名與適用域。保留 immutable 來源、精確 Grid storage identity、實際 generations，並在真實 ResourceCurrent delegate 前後檢查；來源持有與幾何計算不授予遊戲權限。實際 delegate 仍必須由真正 issuer 檢查每份 ROM／來源 generation；本輪沒有自動取得原生 runtime bank／cache 的 Current。

完整實際 ARMOR／Book 的 HMDZ 與 ROMZ 原始檔、解碼衍生檔分開保存。現有已調查 HMDZ 宣告中沒有找到 type7 width0 的現用記錄；width0 實作依據原生分支與 ROM producer，不是製造變更樣本或執行測試取得的證明。

第171至173輪的 map cell reader、grid composer、HMD／Pass parser、0516 decoder 與初始 placement selector 證據保留，不重算為本輪新發現。實際原生路徑選取、ROM bank／cache、後續物件與動畫變動、來源 issuer、場景生命週期及完整伺服器 Authority／5D 仍需接入；Main 尚未選用這條可玩世界路徑。

## 陸服接收器線索

CN PE SHA256 `582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`。本輪追查舊指標候選的實際資料表與 consumer，沒有把任意 pointer hit 當作 receiver registration。

`007F7C57`／`00841DA7` 兩個候選跨越 DWORD 欄位。對齊後的 key 值為 `0x813`，下一欄是 `nl-BE` 的 UTF16 pointer。實際表基址 `007F77A8`／`008418F8` 的原生 consumers 使用 index×8 查找 key／語系文字，因此這兩個具體候選屬於 locale lookup，不能據此建立 receiver 或 vtable 路徑。`200BAA9F` 仍是待釐清的跨欄位候選，不能推定用途。

第三個候選 `21AFBDAB` 所屬的完整228-row table 與已確認的語系表 byte 相同；這只證明資料相同，沒有證明複本被執行。六個新增完整原生函式共470 byte，六個資料範圍共5608 byte，保存四個有界關係。舊31個 pointer candidates 不重計。

`0047DE70`／`004812B0` 的 calling slot、phase 仍未知；14個 receiver contexts／12個 qualified contexts 不變。排除局部錯誤候選不是全域不存在、不可達或完整接收鏈的證明。

## 本輪統計與保存

| 項目 | TW | CN |
|---|---:|---:|
| C2S opcode 索引 | 156（151一般＋5補充） | 156 |
| S2C opcode／phase entries | 252（230定長＋22變長） | 280（帳號6／世界206／戰鬥68） |
| 本輪新增 opcode／phase binding | 0／0 | 0／0 |
| 本輪新增完整雙向遊戲路徑 | 0 | 0 |

新增兩個 ROM C++ 來源檔、修改兩個地圖來源檔；其他既有 C++、全部 Lua、原生 EXE 與存檔維持原樣。來源整合紀錄165增為166，這不是完成封包數。30個既有戰鬥 action／selector frontier entries、958個 endpoint index rows 與28組群組都不代表完整全遊戲分母。總封包／完整路徑／全遊戲百分比仍未知。

Fresh before1246 SHA256 `7997753644b7d1864cf4d4a42f33fe4a3083efb67b0e7dd5042f2ae450a456ff`，上一輪2134個封存成員與原始來源保留。各代理保存完整 before／current 來源、完整原生輸入、衍生資料分開標示、原生指令與缺口證據；根整合保存原始 CLI 與最終報告後封存。

TW／CN／web 全遊戲目標維持 active。尚需原生 entry／reservation、peer policy、Current／Install／Cleanup、實際時序／權限／完整5D、mixed dispatcher、CN account／summary／world issuer、64位元數值的儲存／wire／object／display、stack99所有變動路徑及 web WSS／TLS／hosting。等級、原生字體、編碼與繁簡轉換保持原要求。本輪沒有 build、測試、native／C++／Lua／API 執行、DB／SQL 存取、部署或重啟。
