# 第212輪：台服帳號階段A6選取資料來源

本輪修改5個既有C++來源檔，新增來源串接段1（201→202），新增完整雙向玩法路徑0。TW方向／階段／狀態／變體／延後分派分母仍未知，TW與全遊戲百分比均為null。台服先完整串接100%再停止的優先要求保持；此輪結束不暫停目標。

## 實際原生格式與來源

已保留的原生producer `147D0`將兩個實際參數的低BYTE寫入2-byte本文，`147EA`使用opcodeA6。實際caller `B490`從Main+8F4與Main+B40的WORD取值；這兩個線路BYTE不能擅自當成group ID、server ID、IP或port。`12506`是通用framer／send回傳位置，多個opcode共用，不能單憑該PC判定封包種類。舊「6B」標籤與歷史receipt保留作歷史，不改掉基準或冒稱舊raw trace已找回。

在現有明確recovered zero-seed／feedback0、未壓縮、原logical queue為空且只含一筆A6 logical3的profile下，standalone envelope為6 bytes。原生`10670`校驗是clear header長度bytes及每個logical BYTE加0x3C之和mod256；`10690`使用key與先前clear feedback。key、feedback與加密旗標仍是profile條件，不將此source extension泛化成任意dynamic seed或混合queue。此次已保留11段726 bytes／264 instructions，新原生coverage為0；未執行codec或原生。

`ParseNativePostServerSelectRequest`針對上述現有profile處理完整wire6、length、A6 opcode與校驗，保留完整raw、logical、checksum與consumed；兩個selector bytes原樣可供真正來源使用。原`ParsePostServerSelectRequest`仍保留舊exact-fixture gate。Session僅在實際native_list opt-in時選擇一般A6 parser，其他default／legacy模式仍走舊gate；避免把任意selector接到candidate成功列表。

## 已接入的來源鏈

實際Session strand parser取得owned request value後，在真正`character_operation` game工作內傳遞，並只在native-list分支、Authenticated、帳號非0、未選角色、未closing且尚未安裝時，發布`RecoveredServerSelection{session,account,request}`。該不可變observation由私有atomic shared_ptr保存，沒有public setter。網路端不讀取game-owned帳號欄位，不以已清除的strand輸入buffer或strand狀態作game來源。

`SharedTaiwanNativeCharacterListSource::Scope`持有同一不可變observation。實際TargetSource／Target.Current／Qualify能取得真正收到的A6輸入；Current核對同一observation identity以及session／account、原有phase／closing與完整角色／snapshot來源。List缺少這個真實輸入便拒絕，沒有猜測目的地或成功fallback。Scope仍保留原生selected-token與完整common ID資格，既有reentry poison路徑保留。

獨立God2CharacterConnection世界socket直接登入後不經帳號A6階段，其Select.Scope中的observation誠實為null。不能填造另一socket的A6、不能將相同raw bytes當成跨socket已發行列表receipt。observation是每Session一次發布的輸入來源；pointer identity防止equal-byte ABA，本身不是權限ticket、目的地grant或列表送達證明。

兩個既有子代理分工：原生代理釘producer／framer原始證據；來源代理審本輪5個C++全檔、實際caller與diff、所有實際依賴。原生代理的`RecoveredPostServerSelect.h`副本是真實before212 epoch，因root後續修改而與final不同，會在source epoch reconciliation如實對到完整before；該代理未審final C++，final來源由另一代理fresh審閱。兩份封存各自保留，不能偷偷refresh原始檔。

## 仍未完整的部分

- 真正已廣告table／目的地／phase／visibility／resource Current與native07 issuer仍須接上；native兩BYTE不是通用server索引資格。A6解析與輸入保留不等於選服玩法完成。
- 實際發出的列表epoch與跨account／world socket選角來源、queue-current原子性、post-create native header／issuer與完整2A材料鏈仍開放。不能在strand跑SQLite Current。
- 原生dynamic seed、其他feedback／加密flags、混合logical queue與其他選服variant需其實際證據與來源；不藉此修改凍結認證／hello／seed profile。
- 完整initial scene／peer publication、5D Authority、真正Main工廠與台服13組其餘玩法仍待串接；64位元數值全路徑、stack99、CN與web共用成果保持原範圍。

TW盤點C2S156、世界S2C有效252（fixed230／variable22）、戰鬥S2C110、83 actions23／86 selectors7；TW world parsers65與已盤點來源組42不變。CN C2S156、S2C階段列280（帳號6／世界206／戰鬥68）。endpoint958／group28，來源段202；opcode與來源段都不是全遊戲完成百分比。

本輪沒有build、test、原生執行、codec execution、runtime、DB／SQL、migration、deploy或新的原生驗收。帳號存檔、聊天、IME、認證、頭像、客戶端、原生字體與繁簡轉換等凍結功能保留。先完成全部来源串接，再集中全面測試與修復。
