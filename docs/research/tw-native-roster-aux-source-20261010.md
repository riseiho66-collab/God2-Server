# 台服真正roster輔助技能producer，第248輪

本輪修改3個既有C++檔，將same149c實際4A9750純資料producer接入247初始化資料前綴與既有private Ticket／有序S87／C35來源資格。這是具體資料來源能力，普通戰鬥入場、真initial issuer、grant、MP與完整玩法仍未安裝。沒有改凍結的世界神仙存檔／發送路線，沒有把已學清單直接當成戰鬥主清單。

## 已恢復的同一來源列

完整4A9750..4A97A0（80B，含RET）接actual roster row，先讀unsigned BYTE+1F0 learned_count，再寫BYTE+5C aux_count=0；按原learned物理順序檢查BYTE+1F1+i的bit1。只有flags&2成立才把原pointer+258+4*i原值複製到+60+4*aux_count，count++。NULL、重複指標照原樣保留，不查definition、不清inactive aux tail，count0也保留全部tail。原生每圈重讀learned_count；本owned純投影限定game owner持有的穩定完整輸入，不冒稱原生只讀一次或允許並行原生記憶體變更。

S34真consumer前置以rowWORD比zeroextended subjectBYTE；unsigned count<100、id>0且沒有既有kind/id匹配才append，新增flag0、真catalog pointer、count++，經page helper後4AA7C7將同ESIrow傳入4A9750。既有pointer掃描直接dereference而無NULLguard，不能把owned保護叫成原生guard。S35真consumer以同rowWORD找subject，按真catalogpointer的physical equality搜尋第一個匹配，將該learned flag覆寫3，再於4AA90F將同EBXrow傳helper。此局部直到該write沒有S02 latch讀取，但不代表完整dispatcher／lifecycle沒有其他條件。

因此aux與learned仍是不同count／pointer陣列，但本輪確證兩者的真派生關係：aux是flags&2的有序可NULL子序列；不是整份S34、不是S87 battle main，更不是角色學習／施法／回合授權。S34 flag0新項自身不納入aux，卻會重建之前flags&2項；S35 flag3會納入其首個物理pointer匹配。原件及先前247說明均保留，不偷偷改歷史基準。

## 具體C++串接

新增RosterSkillRow保留真rowWORD、learned_count、完整100 flags／nullable learned definitions、aux_count及完整100 nullable aux definitions，包括全部inactive tail。兩組完整definition使用owned vector並嚴格要求各100格，避免16列的大型record全部inline堆到by-value Snapshot的Windows stack；不是裁掉tail。純rebuild_roster_auxiliary按原footprint只改aux_count與compact前綴，保留其他資料。100是owned安全幾何；helper沒有100guard，S34 append的100guard是獨立來源。所有present完整110B definition以同source資格化，NULL與duplicates不濾除。

RosterInitializationPrefix明列16列真rebuild前輸入及真controls／actors／selector／catalog／optional secondary。from_roster_rebuild_initialization_prefix對16列做純helper，將各自rowWORD及實際active aux前綴交給既有247 primary初始化；main保持原REP清0，不從learned填入。全16列完整rebuild結果另保留於Snapshot::roster_rows，Ticket equality、S87／38／86／clear及replacement均保留，不能只保留active aux而遺失tail。

registry install_from_roster_rebuild_initialization_prefix直接走原install_from_issued單一guard與private ticket流程。model_current重讀全部present learned與aux定義，含inactive tails；安裝、選取、replacement及有序發送前後沿既有common ready lease／battle generation／pending／exact Ticket CAS。這是源資料和catalog freshness，不是對神仙存檔修訂、native pointer／客戶端執行或grant的證明。

普通owner仍須提供真正同一roster的穩定來源及實際helper事件。此API沒有猜初始化時會重建、沒有創造socket receipt、沒有把可呼叫API當成Main已接通。現有直接提供linked aux的247 API保持可用；缺完整roster_rows時不捏造learned flags。

## 真正入場producer仍缺的部分

實際RecoveredOwnedCompanions::restore確實從同game的database.companions讀30／31／34並由Application fresh-world逐批send_world_records；目前回傳只有bytes，沒有保留完整selection／row revision／provenance到發送觀察，projected marker也只代表排入傳輸。它是世界saved roster來源，還不是battle actor→deity source。

已有owner+position同一實體僅CUSTOM0086的private PK Ticket角色0／14投影；沒有神仙欄位，RoomAuthority仍未裝。普通入場須真正spawn/admission event串battle incarnation、viewer lease、完整S1C、canonical owner及saved deity readset。沒有用S88 vitals、S1C identityWORD等於deity key或新抽象Current callback代替此缺口。

## 本輪進度

3改0新C++，混合TW/CN部分來源232→233；新增完整雙向玩法0、opcode0。TW C2S156、世界S2C252（230固定／22變長）、battle索引110不變，台服全遊戲方向／階段／狀態／變體分母及百分比未知。靜態保留7段698B／206指令位置，其中本地producer80B；全域新增原生覆蓋0。

下一步沿實際世界saved roster發送保留完整來源修訂，並接真正ordinary battle admission／initial issuer；secondary key-search、grant incarnation、native MP／resources／rules、once settlement、fullreply／WorldOwner／Main與其餘TW流程仍OPEN。未build／test／compiler／runtime／native／codec／遊戲DBSQL／migration／deploy，未連線官方服務。goal active，持續TW優先，保留common／CN／web與凍結功能及數值要求。

完整before／候選／終版及native／actor／review原件：
C:/Users/risei/.codex/artifact-archives/god2-server/20261010/tw-native-roster-aux-source-248
