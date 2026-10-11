# 台服原生遮罩與地圖材料產生端（第173輪）

第172輪已完成台服 mode2 格網合成及場景串接。本輪繼續恢復其實際輸入：原生 ModelDat／Pass 宣告、地圖 placement、frame 選取及物件順序。目標是讓已資格化的原始圖資內容直接進入既有格網與移動場景，仍保留真正資源生命週期、移動權限及完整原生5D來源的缺口。

## 原生資料與來源鏈

TW 使用既有 mapped image，SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`。原生 `0044C980` 讀取 v1.6 ModelDat：三組 layer index／offset、frame 數與 anchor、八個 marker 整數，以及每個 Pass frame 的寬高和 signed32 十進位 cell。`00441730` 寫入 cell 的 low BYTE，不能將原始 `254／255` 一律改為零。

`00441560` 的原生 mask slots 與宣告 frame 範圍分開處理。零維度宣告保留原始欄位及消費游標，不能假造正尺寸遮罩。未宣告、缺失或不完整的選取保持未知；ModelDat mask 物件不等於 IGSROM 檔案物件。

`TaiwanNativeTileMasks` 持有完整 decoded 原文、typed model／frame 及精確消費位置，提供 frame0 與實際 selector 對應的完整正尺寸遮罩。`TaiwanNativeMapAsset` 負責已資格化 HMD v1.6 header／ROMFILE／TileModel／placements，產生實際 mask selection 與 ordered overlay material，接入既有 `TaiwanNativeGrid` 及 `SharedTaiwanNativeMovementScene::Resources::compose_mode2`。

原生 `00437250` 在 v1.6 讀每個 placement 的六個整數；first base 沒有 object-only extras，其餘物件保留額外欄位與 flag1 script 的原始 token。`004365D0→004425F0` 按 signed `screen_y + ModelDat[4]` stable ascending 插入，ties 保留檔案順序；這個 height 是實際模型幾何，不是 Pass mask height。需要未恢復 ROM 幾何的物件不能用遮罩尺寸或預設值替代。

目前安裝圖資中觀察到 `.hmdZ`，例如 `Data2/map/island01/indoor/ARMOR.hmdZ`，開頭 `05 16`，decoded 內容為 HMD v1.6。此存在觀察不能冒稱已讀取不存在的 plain `.map`，也不能冒稱 runtime 資源載入、動態 frame／物件生命週期或原生權限已成立。完整實際 encoded／decoded 輸入、雜湊與解析來源由子代理證據另存。

所有 TW 行為依 TW 原始指令獨立限定；既有 CN parser 只作定位線索。資源標籤、script token 和原文保留 byte identity，不套用聊天繁簡轉換。沒有修改字體、客戶端 EXE、存檔或資料表。

初始 frame 選取也有直接原生寫入來源：`0043730F／00437318` 將第六個 placement 整數寫到物件 `+30`；`004374CC／004374D0` 寫到 base 物件 `+30`。格網初始化再呼叫座標／資源設定函式時不覆蓋該 selector。這只限定初始已宣告 frame，後續動畫／動態物件仍要由實際生命週期 Current 資格化。

`native_scene` 同時持有原始資產及精確合成 Grid 的不可變 Storage，delegate 前後都核對唯一 ComposedMode2、兩個資源世代與 retained Grid identity；回傳的 public Native 在 adopt 前不能換成完整但無關的格網。原始 Current 仍必須由真正提供者提供，沒有改造移動權限或5D回覆。

## 陸服接收資格條件

CN PE SHA256 `582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`。本輪定點追 `0047FC50`、`0047F310` 與 `0047C5E0` 的3份新有界完整函式，共498 byte、4項生命週期關聯，釐清兩個未知 receiver 同樣依賴的 `+2CB8` entry gate 何時開啟與失效。完整 owner `+104` 傳給 initializer／disconnect；base socket `+64C` 對應完整 owner `+750`，與前輪 nested receive object `+758` 分開。

Gate qualification 與 receiver selection 分開計數。`0047DE70／004812B0` 的 phase／calling slot 尚未釘定，不能只因前置旗標成立就推定其 opcode、階段或完整雙向路徑。既有 receiver prologue、nested receive object、frame 算法與前輪 spans 只作保留見證，不重算本輪新增格式。

## 計數與保存

| 項目 | TW | CN |
|---|---:|---:|
| C2S opcode 盤點 | 156（151一般＋5補充） | 156 |
| S2C opcode／phase entry | 252（230固定＋22變長） | 280（帳號6＋世界206＋戰鬥68） |
| 本輪新增 opcode／phase 綁定 | 0／0 | 0／0 |
| 本輪新增完整雙向可玩路徑 | 0 | 0 |

兩版計數單位不同，不能相加為全遊戲分母。保留30個既有 action／selector frontier entry、110個台服戰鬥索引及256個長度位置。958個 endpoint index／28個來源群組也不是完整路徑分母。全遊戲總路徑、完成路徑及百分比維持未知；來源帳本由164段增至165段。

本輪新增4個 C++來源檔，保留既有格網、場景、其他 C++與全部 Lua。Fresh before1238 SHA256 `ec12b1b0d1b67396ae8fa89f8c94efd76753d10f3da2ef01365180147f28e644`；上一輪2047個封存成員先現讀，再保存完整來源 before。每組來源、原生輸入、精確指令、差異、缺口與最終原檔各自保存，原始 CLI 報告與 final 報告分開封存。

TW／CN／web 完整目標維持 active。未完成項目仍包含實際地圖／資產選擇與生命週期、runtime cache／動態物件、世界入口／peer policy、完整移動權限與5D、mixed dispatcher、CN真正登入與世界來源、普通 Main、64位元數值全鏈路、堆疊99所有變動入口，以及 web WSS／TLS／hosting。

本輪只做靜態逆向與來源串接，不建置、測試、測試式驗證、執行 native／C++／Lua／API、存取 DB／SQL或部署；全面測試與修復留待全部來源路徑串接後。
