# CN 世界狀態、實際返回值與退出控制

本輪 `20261008-cn-world-return-state-frontier`，PHASE1；前一輪已實作並封存退出來源，分類 progress。完整TW／CN／PC／web／全部遊戲目標保持，這輪不執行任何遊戲、建置、測試、API或資料庫。

## 八格世界狀態與六個終止返回

固定CN EXE雜湊 `582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`。`0048DA20` metadata宣告void，但primary在六個terminal branch明確設定EAX，caller `0044A727`實際把EAX存入EBX；不得依decompiler void型別忽略返回值。

`0048DA80`先設world+89B178=3；`0048DAA0`取同一member，以unsigned7上界與`0048E080`八格table分派。table在metadata envelope之外，獨立保存32 bytes。state3呼叫`0048A4D0`，把實際EAX写回world+89B178再循環；state4走transition cleanup／reinitialize，重設3。大於7的原生值回到讀取迴圈，沒有猜測terminal default。

|world+89B178|table target|實際terminal EAX|main的02 control|呼叫00480C50|
|---:|---|---:|---|---|
|0|0048DFA4|1|1|是|
|1|0048DFF4|2|1|是|
|2|0048DFCC|6|2|是|
|3|0048DAB2|frame返回再循環|此分支非terminal|否|
|4|0048DAC8|transition後再循環|此分支非terminal|否|
|5|0048E01C|4|該main switch不發close|否|
|6|0048E061|5|0|否|
|7|0048E039|3|0|是|

六條terminal皆呼叫`004AE2B0`，但它只是三個實際callee與一個member gate的client cleanup鏈；沒有由此恢復服務端存檔、交易或退出規則。`00480C50` primary處理owner+40F8的FILE、fclose與+40FC字串，不能叫作transport reset或當成socket成功關閉。以上helper side effects與完整原因仍待追。

所有terminal在設定EAX後只做epilogue與`00749104` cookie check。cookie相等的normal path是compare、conditional branch、ret，沒有寫EAX；失敗路徑跳去GS failure，沒有把它当成正常返回。這輪保存primary cookie envelope17 bytes，才把caller觀察到的EAX與六個constant return配對。

新增既有`CnPostWorldExitControl::native_world_return`唯讀投影，完整保存raw world state、實際main EAX、optional control以及是否呼叫00480C50。state5的no-close不能用default0補成close；3／4／>7沒有這個terminal投影。它描述內部client lineage，不是wire欄位、server權限或客戶端可指定的backend reason。原2-byte收包reader和退出權威supplier保持原樣。

## frame來源與03觸發關係

`0048A4D0` 的每個frame呼叫`0048AA10`。EAX不等於3便回傳該實際值；等於3但global00886060=0則先xor EAX=0再返回。world+8885C4非空且該owner+FEF7C非零，另走相同xor0出口。原native API、UI及timing未執行，這些僅為指令與原始member條件。

`0048AA10` 以`004AE370`返回值加26，unsigned<=24後先查25-byte selector `0048BD68`，再查五格target `0048BD54`。兩個table均在4929-byte metadata之外：

|實際signed selector|target|frame EAX|world terminal→main→control|
|---:|---|---:|---|
|-26|0048AB16|2|2→6→02 02|
|-15|0048AB27|5|5→4→該main switch不發close|
|-9|0048B198|1|1→2→02 01|
|-2|0048AB08|0|0→1→02 01|

其他21個range內selector落default0048AB38；range外也落該default。不能把21格視為21玩法，也未從負數值命名退出原因或補UI命令。`004AE370`的實際command producer、回傳值6及其他state sources仍是下一個frontier。

沿既有world03 primary cell `004929E4`→`00492936`，獨立保存24-byte terminal range，包含完整ret4；cookie正常時實際返回8。初次靜態擷取使用23-byte範圍，未包括完整ret4，已被primary operand檢查拒絕，未寫findings或ledger；該部分輸出及原工具保存於recovery receipt，不覆寫它們，另外保存完整24-byte範圍。`0048B185..0048B192`做4／3／1減法分派，只有原始8走0048B198／0048B19F EAX1／0048B1A4直達epilogue，frame返回1。其後world state1→main EAX2→`0044A79D`／`0044A7A7`→shared0044A8C8發0201。這是**S2C03引發後續C2S0201的特定native lifecycle關係**，不是「收到0201必須回某個成功03」的服務端規則，也不代表正式回覆已配置。03兩個payload bytes、實際server issuance／存檔／重播／取消條件依然未知。

`0048AA10`另對raw consumer7寫frame結果7、raw4寫結果4；這輪只記錄原始數值與branch，沒有把相同返回值套到所有opcode。先前封存的world03及monster lifecycle CFG保留；舊0048DA20 CFG在第一個indirect jump停止，這輪透過primary八格table扩展該bounded function的entry-rooted正常返回CFG。函式局部圖與table qualification不證明所有callers、exception、runtime state或全遊戲分母封閉。

## 本輪計數與缺口

八格table／六個terminal EAX映射、四個負selector分支、world03→0201條件式關係、唯讀投影各自記錄；它們不是新opcode、完整authority chain或全雙向玩法。來源片段新增1；opcode／source phase binding／source owner chain／完整雙向路徑新增均0。保持whole-game total／completed／percent=null。

真正03 reply issuer、退出權威、全部phase／state／variant分母及正式Application未完成。仍須接齊TW／CN共用帳號、世界、社交、物品、交易、任務、戰鬥、技能、怪物、寵物、公會／同盟、城鎮／室內、PC／web／WSS、64-bit數值與堆疊99；最後集中全面測試、修復、回歸、發布。凍結功能、資料存檔、原生字體、繁簡轉換、等級及二進位不改。
