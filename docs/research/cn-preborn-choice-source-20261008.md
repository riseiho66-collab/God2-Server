# CN 原生 preborn 選擇來源串接

本輪 `20261008-cn-preborn-choice-source`，PHASE1。前一輪128已保存A0／A3與UI來源並封存186檔，屬progress。修改前先保存107檔before snapshot及128封存manifest；不覆写舊native基準、catalog或報告。未建置、測試、native／C++／API執行、DB存取、遷移或部署。

固定 CN EXE SHA256 `582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`，FileView只讀原始VA。沒有整份反編譯巨檔、21xxxxxx映射別名或原生執行。

## A0 的兩個 byte 用途

00534D10複製A0 bytes1／2至同一owner+F74／F75。005335E0在mode0讀F74−D20，mode1讀F75−C3C，顯示剩餘次數；同時使用global009F1174／009F1178的文字。00534320從primary WORD table008A4588讀281／282，經同一ProgramMsg resource+B2F60與signed+B2F64綁該global。CP936 ProgramMsg281是「可选择拟态次数」、282是「可选择特技次数」，與原生assertion字串的 `playlib/preborn.cpp` 一致。

因此這兩個byte是此原生UI的擬態／特技選擇次數顯示欄位，不能當成HP、傷害或server權限／重生規則。保留上一輪類別名稱與歷史證據；新增CnPrebornChoices::Limits作此限定context的欄位投影，原生A0格式和client不改。兩個limit不套用背包99、仙幣上限或等級調整。

00534640只有signed UI handle非負且該window的mask10非零才重建可選清單：取owner+430AC物件的+160指標；清A44及8B4的400 bytes，依實際資料的byte flags與kind／角色值過濾，重建分頁與0..3擬態候選，然後呼叫原生UI helpers。這只資格化consumer的讀寫與条件，未實作server eligibility公式，也未宣稱所有helper副作用／例外完整。

## producer 完整範圍與 phase

004AE370只有事件WORD匹配同一owner+1C8500才呼叫00534810；原生這個owner是world+89B26C。00534810的恢復metadata envelope僅162B，內部direct branches及7項table實際到00534CF4前的三個ret8；不能把162B當完整producer。

另保存entry-rooted primary CFG的1252B程式範圍00534810..00534CF4與28B表00534CF4，只從root及真正branch/table targets解碼，表格不當指令。表0..6分別定位005348B2／005348D6／005348F6／0053491A／0053493A／00534A98／00534AB9。CFG只含正常call-return與局部靜態分支，不是native執行、整個callgraph或例外證明。

實際發送branch為flags&02==0、flags&01!=0、signed item6、mode1，且owner+8A8==0。00534B07先用00481440送81的1-byte body；00534B61再送83的WORD長度及原始WORD清單，之後00534B6D寫8A8=1。00481440先加opcode再複製body，所以C2S81完整2B，C2S83完整長度為3+2N，WORD長度包含opcode。81的bit mask來自已選擇的原始候選索引；83每項直接取資料指標前兩bytes，不加入猜測技能ID或權限。

這屬WORLD connection1的preborn UI context；不得與同opcode的BATTLE用途混用。此producer正常return為0，不是直接server save或退出完成。原生GUI gate不替代server操作狀態、權限、費用或儲存transaction。

## S2C consumer 與來源程式

原生WORLD A1→00533290，native length2，讀payload低四個bits 0..3並避免重複、受F74選擇次數影響；上四bits仍保留。A2→00533300，native length標記-2，從record+1的WORD讀完整logical length，計算(length−3)/2並逐WORD保留低byte ID、高byte kind；實際native resource索引、已選擇去重、F75及client容量都須真正issuer資格化。source reader只接受精確3+2N形狀，沒有自行把最大選擇數當成100或255的server規則。

新增CnPrebornChoices.h的C2S81／83與S2CA1／A2格式reader、A0 limits投影及已定位family reply形狀檢查；A0／A3沿用上一輪完整3B view。

新增SharedPrebornChoices.h/.cpp，並接入SharedWorldGameplay在真正1C publication後的初始化與世界分派。實際WorldOwner必須提供已發出A0的操作scope、common lease／revision／limits、真正rule與transaction／save／replay operation及post-commit output資格化。81只暫存scope+raw mask；83匹配同一scope才一次呼叫實際apply，先指定issued fence避免本地再次使用同scope。所有opaque原始值保留，沒有native ACK、預設成功、費用、重生或技能繼承規則。

apply後改以真正committed revision與publication資格化，不能再把過期pre-commit scope當目前來源。完整A0／A1／A2／A3的實際選擇、bytes與順序由issuer提供，透過既有send_world_batch_with_publication在實際world身份仍有效且source-qualified時才釋出。沒有從81／83推定唯一回包配對；其他原生輸出變體仍待獨立接齊。local duplicate fence不等於跨重連的完整持久化replay防護。

Sources.preborn_choices未配置時不安裝81／83分支。CMake既有src/*.cpp遞迴glob會收錄新cpp，未修改build設定或執行build。共用資料庫／權威資料表維持預設，沒有新建_tw／_cn遊戲表或匯入CN資料庫。

## 計數與仍缺

本輪新增一個未正式掛入的局部owner composition，來源phase關聯C2S81／83、S2CA0／A1／A2／A3共6個；均為原有已盤點opcode。新增完整雙向遊戲路徑0，formal Application未掛入，真正operation owner／A0初始issuer／重生費用及資格／技能來源／持久化replay／存檔transaction仍未提供。UI flags和分類resource只能說明client用途，不能補成native server規則。

全TW／CN／PC／web／WSS、common帳號世界、所有玩法、numeric64、背包99與分母繼續；全遊戲total／completed／percent=null。保留帳號存檔、認證、聊天、IME、頭像、原生字體、繁簡轉換、等級、客戶端與全部舊基準。下一步接實際common preborn operation／skill state及完整輸出條件，再回到正式登入世界providers與全玩法來源鏈。
