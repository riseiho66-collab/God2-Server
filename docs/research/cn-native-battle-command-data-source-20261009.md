# 第192輪：陸服戰鬥命令接入共用技能與道具資料來源

本輪完成來源增量，不代表完整戰鬥玩法或客戶端驗收完成。陸服實際 C2S35 logical17／body16 的有序請求，現在可經 `SharedWorldGameplay` 的明確 data configuration，接入 `SharedNativeBattleCommandData`、既有 Groups、既有 CommandSource。單一 direct／grouped／data owner 擇一，沒有預設成功、戰鬥權限或虛構扣費。四個新 C++ 檔加兩個修改檔，共六檔51,879B；來源段183→184。新增 opcode、phase binding 與完整雙向玩法路徑均為0；全遊戲分母與百分比保持未知。

## 實際來源變更

- `src/cn/protocol/CnBattleSkillDefinition.h`：完整110B技能定義的 owned readonly view，保留原始ID／kind、WORD3E、BYTE45與所有未知位元組。結構讀取不製造 Native Source revision，也不證明學習權、MP、成本或實際目錄來源。
- `src/cn/protocol/CnBattleInventorySlot.h`：完整36B client memory record 的 owned readonly view，只命名 BYTE0 quantity 與 WORD4/5 item；其餘33B保留不透明。這不是36B wire decoder。
- `src/cn/world/SharedNativeBattleCommandData.h/.cpp`：實際共用技能 catalog lookup／完整 inventory dictionary snapshot，連到必要的真正 DataAuthority。所有 physical requests 依原到達順序保存，包含 Opaque，沒有任意去重或規格化。
- `src/cn/world/SharedWorldGameplay.h/.cpp`：compose 限制 direct、grouped、data 擇一；initialize 把真正 data authority 交既有 Groups，再交原 CommandSource。既有整批拷貝、dispatch、held replies、私有 transport token 與清理路徑沿用；Main 未選用本來源。

技能資料讀取前，必須由實際 `catalog_current` 資格判定 catalog、borrowed shared reader 與 store lifetime 的關係。強指標非空不代表關係成立。真正 `CnSharedSkillCatalog::lookup` 保留完整 NativeSkillRecord 與釘定 CN453 定義來源；不用 TW CUSTOM 的 MP 門檻代替 CN 規則。來源程式沒有開啟 DB 或匯入資料。

道具讀取由必要 InventorySource 供應完整實際 dictionary、lease、generation 和所有36B記錄；前後完整讀取比對 key、全部 bytes 與 generation。inventory memory budget 不冒稱原生容量。結算後的 Current 使用原始 before image 與 actual Result，沒有重新讀取後偷偷替換基準。真正 learned skills、custody、grant、expiry、target、rules、成本、結算與回覆都保留給必須實作的 DataAuthority。

## 原生位元組與來源界線

獨立固定 CN582f PE 的 skill frontier 新恢復三個完整 local functions：549A70 59B、553920 53B、55D770 333B，共445B；553A50 50B及190輪54FFC0 1268B為保留來源，共1318B。五個 spans 共1763B，531個 instruction sites。55D770 的原 metadata50B只是 entry island；完整本地控制流程依實際 switch/table 恢復為333B，external assert53E3D0僅記 callsite。八個 data copies445B為五DWORD跳轉地址20B、17BYTE selector及六個完整68B row408B，不是封包數。

550184 `80 FB 03` 與550189 `80 FB 17`證明技能命令是十六進位 **0x03／0x17**；0x17是十進位23，對應特定原生續包為 **0x83／0x97**。190／191輪歷史 `3/17` 簡寫原件不改，192輪明確補上基數。Root 初期訊息誤讀17為十進位而提到0x11／0x91，已在任何 C++ 修改前依原始 bytes 修正；獨立 clarification receipt 保留。程式不通用移除 bit80、不截斷未合格的 high16，也不因記錄存在而授權。

549A70 依實際 ownerA970F8／A970FC 選 primary553A50 或 secondary553920；ownerA8CBFC是 signed selected slot，不是技能ID。primary／secondary list writer 與載入 catalog 的同一 pointer／epoch 關係仍 OPEN。定義 BYTE0 ID／BYTE1 kind 在兩個實際技能分支組成 zeroextended WORD operand。WORD3E!=FF5 的 kind2特殊分支，把 owner4A4／4A9 的兩WORD放入 target field，不是通用 mask。BYTE45 只在實際 owner468!=0 的分支供 helper；owner468／target list producer仍待追。

55D770 modes1..4、11、12、17只在實際正 count 時 OR target bits；mode5不讀 count，把選中半WORD寫3FFF而保留另一半；mode6及7..10、15依真正 table row及 first match寫選中半WORD，無 match保持先前 bytes。13、14、16走 assert call／不寫；0或unsigned>17不寫。16／17計算過的 row address不代表讀取資料，不製造 row或預設零 mask。helper缺少獨立 target bound不授權服務端越界或錯誤權限。

inventory frontier 新恢復 getter4C9AE0 47B及 reset4C73E0 74B，共121B；保留四個 spans1793B及 WORLD41 dispatch cell4B。getter unsigned WORD<=0x25，即38個 getter位置，每筆36B，WORD+4非零才回 pointer。reset backing page0x708=50×36B及 S41 updater slot0..49是另外的範圍；不能用38、50或bag30互相替代，亦不代表 quantity99。54A9A0用實際 battle owner+20作 getter receiver，signed BYTE經 CBW→WORD；負值不通過getter。

保留190輪 item scan29向下的原生 edge：requested30..37不進scan，selected BYTE仍29，item WORD仍取 initial requested record。不得「修正」成slot29 ownership。C35 item05／0C operand為高BYTE signed slot、middleBYTE0、lowWORD item。Data 選用Item domain時必須精確匹配實際 supplied cell與item；domain及所有權由真正權威資格判定，不憑相同item猜 custody。S41→4C72E0是既有 wrapper relation，並非新增opcode或phase；最初4913E8未對齊 locating dump完整保留，但不作instruction證據，正式bounded block為4913FF..491413。

## 生命週期與實際缺口

Data保存原私有 transport Token、完整 ordered raw requests、actual Plan issuer/group共享所有权与generation，所有資格失敗與throw均單向terminal，guard退出才清理自身input。Single／Final在真正 callback前消耗 once標記；Append由既有Groups保持explicit intermediate Reply，不結算。Data observation cache只在replace／terminal／destruction／last strong reference時清除；Group release清自己的pending，不是直接取消Data或Core。

既有 Source 的 native no_reply只走三個可用Current stages；held native replies另有before／after release兩個。不能聲稱每次都執行五個。請求與資料來源已串接，不等於實際 battle issuer、actor／formation／target／learned／MP／item custody、一次結算、C++／Lua原生規則、回覆供應者或Main完成。這些仍是下一個真正來源工作，不用猜測值或TW CUSTOM補成CN原生。

## 網頁來源交接

完整保存 web peer 的 current contract119743B、commands v3.1 174627B與 runtime v6 609672B，現讀本輪相關契約條款、implementationStatus、sourceCorrections、sourceConnections、API與剩餘缺口。手動道具 -10是type5/self，-6依actual range6／War target發type5，手動equip -7是type12/self即0C，無C28；generic551A00 equipment path需要C28仍OPEN。actual received82-owned input／WM203/12014／bag hit／token／same C35來源，不產生單擊冒充double-click、browser local扣費或server atomicity。web peer 的 private source token不是服務端authority。kind2 nonFF5／formation／第二actor／quantity字体貨幣與global input lifetime等OPEN由原交接保留。原件及本輪服務端ACK分開記錄，沒有操作或修改網頁客戶端。

## 靜態盤點與保留

TW C2S目前156 opcode union（151 generic＋5 supplemental），CN C2S156；TW S2C252項length support（230fixed＋22variable），另battle110 indexed；CN S2C280 phase/opcode entries（account6、world206、battle68）。958 endpoint rows／28 source groups不是全遊戲路徑分母；phase／state／variant與間接／延後來源仍未全部限定。原有完整玩法路徑0、全遊戲百分比null，不把本輪函式、instructions、資料rows、來源段或partial owner算成完成封包。

fresh before1373完整原件／前輪1912448封存成員／Root6 CPP complete final copies与diffs／三个agent实际原件、初稿和修订epoch／四份原始及四份最终报告另存。Inventory reporting32→33 opaque訂正保留舊epoch。Service agent一次model capacity observation後以同agent續接，没有重跑已完成native工作或更换模型。路徑glob搜尋失敗與訂正查詢也保留receipt。只用files／hash／CSV／PE／Capstone及來源accounting，沒有建置、測試、遊戲／native／C++／Lua／codec／Windows API／DB／SQL／runtime或部署，沒有重試155 formatter/capacity/render/glyph或52F330／52F170停止鏈路。

完整TW／CN／web共用服務端、共用表及具體不相容才用_tw／_cn後綴、64位共用計算與同步wire／物件／飄字、仙幣99999999999、qualified stack99、level不改、原生字體与繁簡轉換、存檔／聊天／IME／認證／頭像及其他凍結功能維持目標。全部來源打通後才集中建置／測試／驗證／修復／發布。本輪不是目標完成。
