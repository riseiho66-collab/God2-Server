# 全任務 RAM 文字的座標／NPC 名稱候選（2026-09-27）

## 執行範圍與結果

新增 `tools/strike_lab/current_all_memory_coordinate_hints_20260927.py`，僅離線讀取先前成功的 actual-RAM 收據與當前兩份原始資料；**沒有啟動客戶端、讀新程序、登入、注入或寫 DB**。

- 輸入：`artifacts/research/live-memory-references-20260927-03/memory-result.json`
- 輸入 SHA256：`e568326018cc531193d4271a926e585cfd27dbdbb5ea190ca75f0d9339701bba`
- 輸出：`artifacts/research/all-memory-coordinate-hints-20260927/evidence.json`
- normal / `-O` 完全一致：`76c166c66dd15b66b85cd6af1f2b34557afaf1fbfae1a89d4b3287ef80d73c9e`

| 覆蓋／候選 | 數量 |
|---|---:|
| 逐筆核對的原生40-byte任務記錄 | 418 |
| 逐段 source[:379] 長度／SHA核對的 RAM 文字 | 2014 |
| 逐筆核對 source row、名稱、94-byte地址的 RAM NPC目錄 | 4043 |
| NPC非空不同名稱字串／空名rows | 2564／408 |
| 非空重名群組 | 288 |
| 含括號座標的文字／座標token | 560／665 |
| 同文字內有NPC目錄名稱字串 | 518 |
| 名稱字串／保留重名後所有候選key | 265／436 |
| 名稱緊鄰括號座標的文字關係 | 327 |
| 其中多key或多名稱關係 | 85 |
| 可直接作世界spawn的記錄 | 0 |

265 個字串是**詞面候選**，不是265位已定位 NPC。例如「蝸牛肉」含目錄單字「牛」，資料仍保留並標記 `lexical_match_only`、`short_name_requires_review`，不能把它與旁邊廚師座標綁定。名稱重疊也保存 `contained_in_other_mentions`，不把「仙鶴道僮」中的「仙鶴」當成另一個出生點。

## 驗證方式

兩個 agreement 階段的418-record catalog必須完全一致；raw40中的名稱／count／pointer、record address都須吻合。每個 source_quests() description只取原生上限379 **bytes**，比對收據的長度與SHA；保存原source全長／hash及native截斷狀態。沒有以字元數截斷，保留原生可能留下CP950半字的界線。

每個NPC key保留其RAM address、source行號／row hash、record94 hash。重名群組使用list保存所有key，沒有字典覆寫成最後一個。4043筆中含空名的408筆仍保存在完整inventory，僅不參與空字串搜尋。

文字中所有token、句段及名稱都有CP950 **byte span、character span、實際收據base加byte offset的地址**；raw hex可直接重切驗證。只為文字中「名稱緊接括號」建立hint relation；其他名稱與座標分列，沒有全組合綁定。括號內場景prefix保留原文，不解析成area／scene，也不填方向或instance。

## 能改變追查順序的具體例子

1. **元始天尊不能誤綁119/119。** 任務31 description2，Mission_data行122，RAM `0x16672d0`：先提元始天尊，再指向楓華鎮的仙鶴道僮(119/119)。元始天尊候選key `[760,1701,1702,4146]` 保留為獨立mention；唯一直接相鄰關係是仙鶴道僮候選 `[1704,1825]`。沒有產生元始天尊→119/119。
2. **同名姜尚保留兩個key。** 任務401 description0，行2284，RAM `0x169fef0`：`姜尚(雨龍森林-望潮台828，407))`。座標token byte span `[142,167)`；候選 `[5943,5999]`。場景prefix原文保留，沒有挑任一key或補方向。後面崑崙仙界(67，110)沒有被配給姜尚。
3. **關卡入口不綁怪物。** 任務166 description0，行1102，RAM `0x16847a0`：天絕陣（參天林300，626）挑戰秦天君。秦天君 `[577,5535]` 是同文字mention，但沒有緊鄰坐標的關係；不當成秦天君spawn。
4. **果力村直接文字提示可精確定位字節。** 任務234 description0，行1488，RAM `0x168d140`；廚師梁禎(108/110)座標token byte span `[16,25)`，字串hash `fb46f8ae14920a5130d8315026dfd2abc5becb15e1d428812d1b003fda17fb08`。直接相鄰key2936；同段「廚師」2128及「牛」的一組key並未綁到該座標。這仍只證明來源提示，不恢復72 spawn selector或面向。

純數字括號regex會漏掉大量 `NPC(場景x，y)`、`NPC(場景 x y)`。本工具額外保留這類prefix，例如（果城135 140）、（九天冰屋3F100 175）。早期純數字版本397段／492tokens；擴充後560段／665tokens。這個差異是抽取語法覆蓋，不能當作新增世界NPC數量。

## 怪物與後續界線

同一收據的怪物arena已有7815條source records及96個可lookup群組，本次只核對完整數量並引用它們，不重跑loader，也不把怪物ordinal或任務挑戰文字變成spawn。

此包可供下一步逐段人工／結構化核對：優先處理括號內帶場景prefix且名稱直接相鄰的候選，再以其他RAM資料確認具體catalog key、服務端instance與selector。完整source表、實際RAM載入、文字座標提示與世界出生authority仍是不同層次。

## 重現

```powershell
python -X utf8 -B -m tools.strike_lab.current_all_memory_coordinate_hints_20260927 --output artifacts/research/all-memory-coordinate-hints-20260927/evidence.json
python -X utf8 -B -O -m tools.strike_lab.current_all_memory_coordinate_hints_20260927 --output artifacts/research/all-memory-coordinate-hints-20260927/evidence-optimized.json
```

两次通過完整資格檢查且輸出SHA相同。另逐token、逐mention重切raw bytes並核對地址，以及廚師2936直接關係，均通過。未接runtime座標spawn。
