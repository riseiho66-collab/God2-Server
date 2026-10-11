# 陸服同事件名冊／狀態／技能的跨frame合批來源

本輪 `20261008-cn-subject-roster-frame-packing-source` 接續144。
保留此前seal及來源快照，PHASE1未建置／測試／執行C++、native、
Windows API、server、Lua、SQL或部署。

## 實際缺口与修補

144的publisher把整個事件logical总量限制為0xA00，且每個19B／29B／
4B record獨立作frame。大量真實record因此可能先碰整體限制或既有
transport的256-frame限制，而非原生單筆record能力。

既有 `CnTransportSession::send_batch_with_publication` 的界線是每frame
logical<=0xA00、同一batch最多256frames、pending/output frame容量與
1MiB實際wire queue容量。所有frame先編碼、容量資格化並以同一held
head阻擋，再在game executor作一次真正publication，才釋出整批。
本輪不改transport／codec／identity／持久化或socket barrier行為。

既有 `SharedSubjectRosterPublication::publish` 改為依序將完整實際
19/29/4B record追加至frame；放不下下一筆時才開下一frame。原始
record的bytes／次序／技能definition對齊保留，沒有padding、新opcode、
拆半record、重新排序、預設ACK或客戶端數值裁切。
整體logical界線來自每frame×256，即655360B；不足的frame尾端不用
填滿，256frame上限可能先於此byte上限觸發。這是傳輸操作預算，
不是遊戲名冊、技能數或原生玩法上限。實際queue已佔容量仍由strand
處理，沒有假設空queue，失敗不發布prefix或另造成功事件。

新增 `Framing` 描述各frame的first_record、record_count、logical_bytes
與total，兩次post-commit qualifier都收到同一owned不可變layout，
與Plan／definitions保留至local queue completion。先檢查typed record
最小4B所導出的總record操作預算，再解析真正技能來源。

## 原生串流來源

原生 `0047D8D0` 按opcode的00567B50長度逐byte建立logical record，
`0047D2E0`向`0047A120`取一byte。0047A120從owner+C10+cursor拷貝
實際bytes並增加owner+1814，remaining來自1810−1814；0047A290
檢查cursor是否到decoded extent。logical record的讀取不把每個outer
frame當成一個opcode。0047A170的outer receive完成後呼叫0047A590，
decoder／compressed變體的完整runtime和helper仍未因此驗收。
本輪保留primary metadata／入口CFG／定點operand來源，不執行模型。

原生EXE SHA256：
`582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`。
所有record仍限定已知WORLD30/31/34/35；沒有套用S2C長度表去拆C2S。

## 未完成項目

來源frame合批1、同一layout的兩階段觀察1、existing publisher操作
容量強化1；新增opcode／phase／owner／完整雙向路徑均0。
不能據此宣稱所有名冊／技能已還原，或frame數等於完成封包數。

真正common subject／recipient／roster／inactive row／name／fields／
skills語義、規則、存檔、持久重播、已提交issuer、Application、全部
native時序／狀態／變體仍未配置。原生接受合批的runtime／雙版及
網頁互動／全部玩法驗收留待全來源接齊後集中進行。
完整TW/CN/PC/web/WSS、numeric64、stack99、仙幣99999999999、
其餘上限另定、等級不變、凍結功能及集中修復發布目標保留。
