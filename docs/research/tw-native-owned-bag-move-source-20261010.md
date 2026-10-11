台服第237輪集中接 C24 背包移位／交換。新增具體處理器，原始 mixed records 中的 C24 分成 singleton，先於聊天 Others 複製段派送。實際服務自行讀取完整持有物品與 native1215 狀態、決定完整下一態、預製兩筆41、同庫全量 CAS 交易，再於 durable receipt 與目前 Session／lease／位置一致時回傳。沒有要求外部再提供 Action／next-state issuer 的空處理器。

原生依據為既存149c C24 producer 與41 consumer。41 只改數量和 key；兩格原有尾18 bytes 必須相同，其他 prefix1..3、所有剩餘格、DA15 完整保留。這個限定讓原生41能完整表達本次 cache 欄位結果；不猜3B未知 WORD、不用C28 receipt冒充C24、不宣稱UI helper或原生驗收已完成。

CUSTOM-0093 明示服務端全物件移位／交換政策：只用兩個已明確存在的共同 bag 位置0..29，來源非空、兩格不同；整個 instance 連同 ID、definition、acquisition、raw20 與數量搬移，不合併、不拆堆、不新增物品。更動的 instance 只允許單一149c item20 alias，避免猜改其他版本位置；其 revision 與 alias slot 同步更新，完整 inventory/equipment revision 同交易遞增。全50格目前 alias 與 native witness 逐格一致才處理。保留其他版本資料與既有 CUSTOM-0037 限定，不把此政策說成原版服務端規則。

透過實際 Application Context 的 with_owned_bag_moves 安裝新處理器，要求真正共同帳號／角色／presence 及兩個既有 writer。Main、資料表安裝、初始真正 acquisition／完整 native witness supplier 尚未啟用，缺資料直接拒絕，不把舊 diagnostic 格轉成新持有權。

來源 provenance 保留完整原文並只首次附加固定 CUSTOM-0093 尾標記；後續移位不繼續增長紀錄字串。每次狀態改變仍透過完整 CAS 及 header／instance／native revision 前進，不截斷 provenance、不把來源SHA誤稱下一態雜湊。初版逐次追加操作的候選完整保留為歷史，最終候選修正此限制。

本輪新增2個、修改7個C++來源檔，增加1段條件式來源串接。聊天適配組裝保留新C24 binding，安裝順序不會使它遺失，既有聊天行為不變。TW觀測C2S156、世界S2C252（230固定／22可變）不變；新增整個opcode全變體完成數0。完整遊戲分母仍未建立，台服整體百分比未知，不能把此子集或來源段數換算成100%。待補一般 metadata 不同格移位的完整3B來源、其他C24目的區／同格與空格行為、裝卸完整規則與回覆，以及正式 caller 與其他台服玩法。

按使用者先串接要求，本輪未建置、測試、啟動原生或服務端、執行codec、DB／SQL、遷移或部署。目標API現讀仍為blocked，保留真實狀態與原目標，使用者已授權的本輪手動工作持續。
