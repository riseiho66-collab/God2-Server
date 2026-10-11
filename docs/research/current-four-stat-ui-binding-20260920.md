# Current 四攻防欄位的原生 UI 語意，2026-09-20

## 結論

角色 `role+94/98/9C/A0` 已由原始 GUI 圖像與原生 control 座標逐欄綁定為
**物理攻擊、物理防禦、法術攻擊、法術防禦**。

同伴 `companion+38/3A/3C/3E` 已由另一張原始 GUI 圖像逐欄綁定為
**體力、力量、智力、速度**。這四個欄位是四維，不能稱為四攻防，也不能
沿用角色四攻防的順序或名稱。

這是 current asset 解碼、圖像目視辨讀與 pinned x86 靜態資料流證據。
沒有執行原生客戶端、Unicorn、DirectDraw 或連線遊戲，沒有宣稱 live render。
沒有重做第 1 路寫入算式。**新增怪物原生 stat 真值數量仍為 0**；這個 0
是已建立真值的數量，不代表任何怪物欄位的值為零。UI 語意不能取代怪物值的來源。

## 地址與輸入邊界

工作根：`C:/Users/risei/Desktop/God2/God2-Server`。
唯一客戶端根：`C:/Users/risei/Desktop/God2/God2`。
唯一 mapped image：
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`。
SHA256：`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`。

以下程式地址、結構 offset、action/image ordinal 均用十六進位；
**control ID、CSV slot、座標及檔案大小用十進位**。
image base 為 `400000`；RVA 等於 mapped image 的 file offset。
ROM chunk offset 是解壓後 ROM 內的 offset，不是 executable RVA。

既有 `current-world-ui-resource-20260919.md`、
`current-indoor-resources-20260919.md`、
`current-npc-resource-groups-20260919.md` 與 companion state 研究作為導航。
本次語意證據只取自上列 pinned image 和下列三個 current asset。
只重用既有 `omega_assets.decode_csvz`，未修改任何共享 helper；
未採用 legacy corpus 或其他 build 的標籤／數值。

| Current 輸入 | 壓縮大小 | 解壓大小 | 壓縮 SHA256 | 解壓 SHA256 |
| --- | ---: | ---: | --- | --- |
| `Data2/Patch/FieldComm3.csvZ` | 依既有 pinned source | 3,753 | `197b0952d33bddb6f3682779208dd396fcecbe451c1b9dc68ec86209ed1a7e05` | `2c76b311dfcfba4ceb2b23c0faf5011339365673bd01c8a4ed371fb174fd43ac` |
| `Data3/Flow/FS2_GUI.romZ` | 386,190 | 916,314 | `956fbfa857ba578a3d26b8d1973692817e37ea36707a7173cf09282963a360df` | `6b8cec27e130d3eb488c06aab2bff1a226383d7d03d7ffc6467696fb96529413` |
| `Data3/Flow/God.romZ` | 85,476 | 217,944 | `8fa680341a565fe84dfcc4e07a856e8d7a3848d5caf8958f51c6f47fe6cbc844` | `86e767605bfaa7b539a458258c31be7a9cd1199ab67fd19af74e2ded70ad7dd1` |

## CSV、Bank 與圖像的接點

FieldComm3 的實際記錄是：

```text
physical line 39: slot 34, \Data3\Flow\FS2_GUI.rom, ROM_FS2_GUI
physical line 34: slot 29, \Data3\Flow\God.rom,     ROM_GOD
```

`81610..81682` 初始化 EDI=0、EBX=0。`81620` 取 `[UI+E2164]`，
以 EBX 選 `108` bytes 的 CSV record，`81628` 取 record+4 的路徑。
`8164F` 將 EDI 作為 slot 推入，`81651 -> 29820` 載入，
`81673` 寫回 record ID，`81675/8167B` 同步增加 record stride 與 slot。
迴圈覆蓋 slot 0..46，包含 29 與 34。這個接點建立 CSV index 與 UI ROM
bank index 的關係，不依賴猜測後來的動態 handle。

ROM 格式為 `IGSROM02` 加上 tag/size/payload chunks。
`FS2_GUI` 有 12 palettes、53 images、73 actions；`God` 有 7 palettes、
26 images、31 actions。`TGA_RWIF` 與 `PCX_RWIF` 都佔 image ordinal；
例如 FS2_GUI 的 image `03` 是 TGA，不能略過它而使後面圖號差一。

原生 `2A8F3..2A949` 把 ACT_POOL 的兩個座標 WORD、兩個 flag BYTE、
image WORD 分別保留到 native pool `+0/+2/+4/+5/+6`。
`1E727` 按 action ordinal 取 native action，`1E72E` 取第一條 step stream，
`1E731..1E739` 找 opcode 0；`1E73E` 用 step byte+3 選 pool，
`1E74A/1E755` 用 pool WORD+6 選 image，`1E767..1E76D` 以
`step byte+5 & 1F` 選 palette。下列三組選到的 palette 都是 0。

| 面板 | CSV slot | Open/Close action | ACT_DATA chunk offset（Open） | ACT_POOL offset（Open） | Image | PCX chunk offset | 像素尺寸 |
| --- | ---: | --- | --- | --- | --- | --- | --- |
| 角色一般版 | 34 | `26/27`，`Status_BGOpen/Status_BGClose` | `DE9DA` | `DEA42` | `1A` | `675DA` | 252×427 |
| 角色 Muye 版 | 34 | `43/44`，`Status_Muye_BGOpen/Status_Muye_BGClose` | `DF86A` | `DF8D2` | `30` | `CA5E5` | 252×427 |
| 同伴 | 29 | `00/01`，`God_BGOpen/God_BGClose` | `3442C` | `34494` | `00` | `E6E` | 261×570 |

這三個 Open 的第一條 step 都是 `00000100010000000000`。
其 pool bytes 依序是 `0000000000001a000046`、
`00000000000030000d46`、`00000000000000000d18`。
Close action 分別使用與 Open 相同的 image、palette。

## 角色四攻防

`E66F1..E66F8` 把 `[UI+86888]` 傳給 `E6710`；`E6711` 將它載入 EBX。
四個 DWORD 經下表的直接 load 送入 `1077C0`，格式 literal
VA `5823B4` 為 `%d`，不是中文 label。

`E7C80` 建構角色面板，`E7CC9..E7D06` 依旗標選 action `26/27` 或
`43/44`，並在 `E7D06` 推入 group `22`（十進位 34）。
`E7D0A -> 104EA0`，`E7D10` 將回傳 panel handle 存在 `UI+232DDA`。
`E7D17` 的 EBX 初值為 VA `596DCA`，它指向首筆 descriptor 的 `+12`。
`E7D23` 從 EBX-12 取 control ID，EBX/+2 取 x/y；
`E7D42` 的 stride 是 **`16` hex = 22 bytes**，合計 32 筆。
表頭是 RVA `196DB8`，entry layout 為 `<h16s2h>`。

| Role 欄位 | Width | 原生讀取 RVA | Formatter call RVA | Control ID | Descriptor RVA | 圖像內數字座標 (x,y) | 原圖中文 |
| --- | --- | --- | --- | ---: | --- | --- | --- |
| `+94` | DWORD | `E6ACC` | `E6AE3` | 23 | `196FB2` | (194,217) | **物理攻擊** |
| `+98` | DWORD | `E6AB0` | `E6AC7` | 24 | `196FC8` | (194,242) | **物理防禦** |
| `+9C` | DWORD | `E6B04` | `E6B1B` | 30 | `19704C` | (194,267) | **法術攻擊** |
| `+A0` | DWORD | `E6AE8` | `E6AFF` | 31 | `197062` | (194,292) | **法術防禦** |

這是欄位到 control 的個別資料流，不是照執行順序猜排列：
實際 refresh 次序是 `98 -> 94 -> A0 -> 9C`。
兩張角色面板均已解碼並目視讀出相同四個中文 label；四個 label 區的
indexed pixels 也逐 byte 相同。圖像上方另有「體力、力量、智力、速度」，
不能把它們與右下方四攻防混為一組。

descriptor 內的 `9999` 等字串是樣本文字，不能當中文 label 或實際 stat。
建構迴圈 `E7D27` 實際推入的是 VA `5B4640` 的空字串。
中文名称已烘在原始 PCX 中，這個結論不使用 ProgramMsg 520..523。

## 同伴四維

`A9AF7` 取 `[UI+86888]`，`A9AFD` 取其 `+D0` 的 selected companion
pointer 到 EDI。該指標為空或 panel handle 不可用時不走四欄 refresh。

`A7D60` 建構同伴面板，`A7DB6..A7DB9` 推 action 1、0 及 group
`1D`（十進位 29），`A7DBD -> 104EA0`；`A7DC2` 將 panel handle
存入 `UI+232DDC`。`A7DC9` 指向 VA `591EBA`，因此 descriptor 起點為
RVA `191EA8`，同樣 stride `16` hex，共 16 筆。

RVA `191E60` 的 panel rect 為 `(539,0,799,569)`。
`A7DD5/A7DDA` 將 descriptor 的 y/x 分別扣掉該 rect 的 top/left，
因此下表的 (612,y) 換算成原圖內 (73,y)，不能直接用 x=612 取圖。

| Companion 欄位 | Width | 一般分支讀取 RVA | Formatter call RVA | Control ID | Descriptor RVA | 表內座標 | 原圖數字座標 | 原圖中文 |
| --- | --- | --- | --- | ---: | --- | --- | --- | --- |
| `+38` | WORD | `A9D49` | `A9D57` | 6 | `191F2C` | (612,165) | (73,165) | **體力** |
| `+3A` | WORD | `A9D65` | `A9D73` | 7 | `191F42` | (612,185) | (73,185) | **力量** |
| `+3C` | WORD | `A9D81` | `A9D8F` | 8 | `191F58` | (612,205) | (73,205) | **智力** |
| `+3E` | WORD | `A9D9D` | `A9DAB` | 9 | `191F6E` | (612,225) | (73,225) | **速度** |

一般分支先清掉 32-bit register 再 load WORD，故輸入 `%d` 的值是
zero-extended WORD。另一分支在 companion key WORD 位於 `65..6C`
時會加上 UI 內另四個 WORD，再送同一組 control：

| Companion 讀取 RVA | 另一顯示輸入 | Formatter call RVA | Control ID |
| --- | --- | --- | ---: |
| `A9C0D` | `UI+866BC` | `A9C1D` | 6 |
| `A9C34` | `UI+866BE` | `A9C44` | 7 |
| `A9C5B` | `UI+866C0` | `A9C6B` | 8 |
| `A9C82` | `UI+866C2` | `A9C92` | 9 |

這裡只記錄顯示分支仍綁在同四個 label；不追該附加輸入的生產者，
不將它解釋成伺服器公式，也不賦予 key 範圍未證實的類型名稱。

## 可重驗的圖像證據

數字 control 的建立路徑是 `107710 -> 1E3D0 -> 25FE0`；
`2609B/260B3` 將傳入 x/y 加到 render object 的位置。
數字更新路徑 `1077C0 -> 146CF7 -> 1E500` 更新已建立 control 的文字。
因此 descriptor 是與該背景共用位置基準的數字座標。
本文的座標為 asset/panel local coordinates，並非 live desktop 點擊座標。

工具從原始 ROM 解出 8-bit PCX indices，再用原生選中的 RGB555 palette 0
作診斷預覽；5-bit channel 展開為 8-bit，最近鄰放大，沒有補字、重畫或 OCR。
PCX_RWIF 尾部的每列 4-byte span table 亦驗證界線；原生
`2C239..2C247` 會讀取這段。Pillow 獨立解碼的全部像素與工具結果一致。

| 面板 | 原始 indexed pixels SHA256 |
| --- | --- |
| Role image `1A` | `c100cbb9401a8336f2c18237aa4cc24d251287aa31235f64c581164bbcb4b234` |
| Role Muye image `30` | `42612989ec7cacc927225b30b417d5a5d0c4ff772a455173846baec23aaf75c1` |
| Companion image `00` | `28d310763e7bce5c6515dd750e95695360c00fc18cae39e2e11ce3629c1c093e` |

三者 palette 0 bytes SHA256 都是
`5356b948bad6b52d3d6c163bced0230010e5d48d04006e9336d1ab3fd8a37f55`。

下列 crop 使用 `(left,top,right,bottom)`，右／下界不含，hash 是按列
連續的未上色 8-bit index pixels。中文名稱是本次實際目視轉錄；
自動測試只驗證那些已目視的圖像 bytes 與接線，沒有自稱能理解中文。

| 中文 | 原圖 crop | Crop SHA256 |
| --- | --- | --- |
| 物理攻擊 | Role `(120,210,190,234)` | `1535a0bbc28f39bc8783aa0c20f0af7c5967db87214a9bbb6b136001ba774629` |
| 物理防禦 | Role `(120,235,190,259)` | `2f9b26e43a5877509a1dcac200dad8007b82441441db16bdd413443e0bd8dfe1` |
| 法術攻擊 | Role `(120,260,190,284)` | `3dcf5f50ff1b2ae7f401f944de08950d85f6ada0ac39197c3ed8bb38290d354f` |
| 法術防禦 | Role `(120,285,190,309)` | `f52f249601a5257208dedacbca95e3bd859d3d7794f7d74c3f272447ec5a2201` |
| 體力 | Companion `(20,161,70,180)` | `39ca90a7c294be61621943076ae8a5d2ee48a8d23b2731f48b2be727de6a37e8` |
| 力量 | Companion `(20,181,70,200)` | `ab739e5cb772e48b19d87180462c4476e58b59e0fa090847c10638fe5bde501d` |
| 智力 | Companion `(20,201,70,220)` | `83962658d9cc77a158d493769da2ae9205a3af01d595be42302ff20752ec8122` |
| 速度 | Companion `(20,221,70,240)` | `b4cb3b9ab34193ed42c0b6c2d397e3dfd66e4076f1c3fa3eb85579507b16e25e` |

## Changed Files、Tested Commands 與進程

只新增三個本路檔案：

- `docs/research/current-four-stat-ui-binding-20260920.md`
- `tools/strike_lab/current_four_stat_ui_binding.py`
- `tests/research/test_current_four_stat_ui_binding.py`

在工作根執行：

```powershell
python -B -m tools.strike_lab.current_four_stat_ui_binding
python -B -m tools.strike_lab.current_four_stat_ui_binding --disassembly
python -B -m tools.strike_lab.current_four_stat_ui_binding --images
python -B -m unittest discover -s tests/research -p test_current_four_stat_ui_binding.py -v
```

工具輸出到 stdout，沒有額外 JSON/PNG artifact 或 bytecode 檔案；
`--images` 的 JSON 含三個 PNG/base64 預覽，本次已直接顯示並目視核對。
`--disassembly` 包含精確 code slices 和各 slice 的 SHA256。
測試 **4 passed，0.533 秒**，涵蓋八欄接線與座標、companion 兩分支、
三張全圖與 Pillow 像素一致、Open/Close action、Muye label 一致性，
以及截斷 chunk／錯誤 span 表的拒絕。沒有重跑任何 bootstrap 或空白場景測試。

開發時修正過工具迴圈括號及 PCX_RWIF 尾部 span-table 處理，之後上述
完整 focused suite 通過；這些不是原生程式缺陷，也不是新找到的 stat 值。

停止的進程：**無**。未啟動遊戲、伺服器、debugger、常駐服務或子代理；
本路 PowerShell/Python 短命令均已結束，沒有需要主代理清理的程序。
未操作桌面、未連線遊戲、未改正式 DB、current client、shared helper 或其他路檔案。

交付邊界：八個 requested field 的原生 UI 名稱已定；monster 原生值、
戰鬥公式與寫入來源仍由主代理及第 1 路另行建立。本路可由主代理撤掉。
