# 台服原生格網合成與移動場景串接（第172輪）

本輪承接第171輪已保存的原生格子讀取器與服務端移動場景，恢復 mode2 格網的產生流程，將底圖和實際有序物件遮罩合成為服務端持有的格子資料。來源路徑仍需要真正的資源提供者、世代與生命週期 Current，以及既有完整移動權限和原生 5D 回覆；目前不能計為新增完整可玩路徑。

## 台服原生來源與串接

使用本機已保存的 TW mapped image，SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`。第171輪的 initializer RVA `00036C30`、tile getter RVA `000416B0` 作為保留輸入，不重複計為本輪新增恢復。

本輪新增定點追查 RVA `00049B30`（VA `00449B30`）、RVA `00049BB0`（VA `00449BB0`）、tile 初始化函式 RVA `00041F90`（VA `00441F90`），及設定函式 RVA `00041FC0`（VA `00441FC0`），共4份新有界來源。初始化函式明確將 selector `+30` 設為零，設定函式寫入座標與資源指標，不自行改選 frame。兩個座標 helper 都由 caller 清理參數，必須按每次 push 後的實際 ESP 解讀輸出位置。底圖 origin 與物件轉換輸出在原始指令中可對應，不能將忽略 push 位移造成的錯讀當作缺失原生來源。

`TaiwanNativeGrid` 保存完整原始遮罩與物件順序，分清 frame0 底圖 extent 與實際選定 frame 的遮罩 extent，保留格子原始 byte。原生明確清零初始化與物件遮罩零值覆寫，均與「缺少資料就補零」不同。完整已知 selected mask 的幾何範圍外讀取，沿用已釘定 getter 的 AL1 fallback；這不表示移動許可。缺失、不完整或不能安全表示的材料保持未知，不替代為可通行格子。

`SharedTaiwanNativeMovementScene` 將合成格網接入既有 `SharedTaiwanMovementSource::Factory` 與 `WorldOwner`。合成資料不含假的 x86 map 物件或原生地址；原有實際 pointer-linked snapshot 路徑另行保留。同一份 Resources 只准使用其中一種格子來源。真正的 Session、完整 lease、存檔位置、資源世代與 Current 仍要對應，沿用既有一次位置 CAS、提交後角色位置／方向更新與實際權限 publication。

合成時先完整複製材料，格網持有不可變 Storage；場景另持有 Grid value。呼叫者保留的向量元素指標或可變 Grid alias 不能改變場景持有的材料與格子。來源目前限定正數、完整遮罩及可安全表示的 DWORD 算術範圍，未宣稱涵蓋原生溢位座標。生命週期 Current 仍由真正的擁有者提供。

這不是完整 runtime 資源載入器或真正原生權限提供者。普通 Main 尚未選用這條來源，未替換既有凍結功能、客戶端字體或二進位檔。

## 陸服接收擁有者追查

CN PE SHA256 `582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`。本輪選定接收上游 `0047D2E0`、`0047A290`、`0047A120`、frame-finalizer `0047A590` 的4份新有界函式來源，共444 byte，新增4項機械擁有者／游標關聯。

`0047D2E0` 的 incoming ECX 是完整 owner `+104`；函式再加 `+654`，實際傳給 byte-read helper 的是完整 owner `+758`。nested receive object `+1810/+1814` 對應完整 owner `+1F68/+1F6C`，不能混同邏輯 aggregate `+2CC0/+2CC4`。既有 caller 與既有 framing 只作保留見證，不重算新增格式。

`0047DE70/004812B0` 的 phase／calling slot 仍未釘定。接收 context 維持14個、其中12個具已有條件資格；本輪物件／游標關聯不能替代 phase、opcode 或完整雙向路徑證據。

## 本輪計數與界限

| 項目 | TW | CN |
|---|---:|---:|
| C2S opcode 盤點 | 156（151一般＋5補充） | 156 |
| S2C opcode／phase entry | 252（230固定＋22變長） | 280（帳號6＋世界206＋戰鬥68） |
| 本輪新增 opcode／phase 綁定 | 0／0 | 0／0 |
| 本輪新增完整雙向可玩路徑 | 0 | 0 |

兩版數字的計數單位不同，不能相加為遊戲封包總數。TW256個長度位置中的4個不支援位置、110個戰鬥索引與30個已保存 action／selector frontier entry 仍分開保留。958個 endpoint index 與28個群組也不是完整遊戲路徑分母。整個遊戲總路徑、完成路徑及百分比維持未知；來源帳本由163段增至164段。

本輪修改4個 C++來源：新增格網 header／implementation，延伸既有場景 header／implementation；其他 C++與全部 Lua 保留。三組子代理的完整來源 before／intermediate／current、原生輸入、定點指令、差異、缺口及封存分開保存。

Fresh before1232 SHA256 `0d0b0bed26c2052f436845c9b044aeb8797f2e3524b42419cac8ef341cf4b1cf`；保留前一輪2067個封存成員及30個戰鬥追蹤項目。1232份 before 中，預期1225份受保護來源不變。兩個 CLI 產生的4份原始報告先保存，再加入本輪靜態來源計數，最後另存4份 final 報告；本輪與 catalog 封存不可改寫。

TW／CN／web 完整目標持續 active。尚待實際資源選擇與完整有序物件來源、生命週期／runtime cache、世界入口／peer policy、完整移動權限與5D、mixed dispatcher、CN實際登入與世界來源、普通 Main、64位元金錢／EXP／傷害／HP全鏈路、可堆疊99的所有變動入口，以及 web WSS／TLS／hosting。

本輪僅靜態原生恢復與來源串接，沒有建置、測試、測試式驗證、native／C++／Lua／API 執行、DB／SQL存取或部署。全面測試與修復依使用者要求留待所有來源路徑串接完成後。
