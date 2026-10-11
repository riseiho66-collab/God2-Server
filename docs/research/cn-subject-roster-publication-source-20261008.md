# 陸服 WORLD30 名冊宣告與同事件30/31/34/35發布來源

本輪 `20261008-cn-subject-roster-publication-source` 接續143。
原生 EXE SHA256：
`582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`。
PHASE1只做靜態來源，未建置、測試、原生／API／服務／Lua／SQL執行
或部署。TW CUSTOM及其他凍結功能保留。

## 原生WORLD30來源

0048FCC0 primary world table4929D8的30 cell492A98指向491324，
同一world+89B26C owner呼叫004D5B20。長度cell567D64指向567C11，
明確return19。這不是C2S30→S2C30因果配對；C2S30的背景請求獨立。

004D5B20 primary metadata只有99B，含未資格化的switch jump與外部
tail，不能把99B當成完整函式。本輪以入口root加primary compressed
31-byte case index4D5CA0和兩個target cell4D5C98/9C，追至兩個真正ret。
限定code至primary table4D5C98，完整局部CFG114sites；helper／例外／
runtime／全部上游仍未完成。

ID為signed BYTE取絕對值，包含-128→128；0直接return。實際BYTE
名冊count先檢查<16，容量已滿時連duplicate reset也不進入。
可用時在count-indexed inactive slot寫WORD ID、BYTE5B和name。
5B=1的ID恰為4/8/10/31/32/33/34，其他為0，不是技能權限。

低ID<100的name取實際resource owner65364的lookup(ID+AF0)+8；
lookup為null使用7EFB9C的一個空格。高ID>=100從payload+1 strcpy。
高ID/control payload17==1再掃描實際active prefix，第一個匹配只清
既有row+1F0技能count並return，不增加count、不改選取、不刷新UI；
inactive slot已先被寫過，不能丟掉該副作用或預設該slot全零。
未命中才append。其他控制值、低ID都直接append；不是通用去重。
負signed ID在append後選取新row並寫ordinal；正ID保留舊選取。
新增後呼叫4D5030/4D4B80，未知初始化／名稱／規則仍要實際來源。

## 程式來源接合

新增 `CnSubjectDeclaration30` 精確19B view和唯讀native_effect。
保存原始bytes/control/name，不猜NUL、不模擬越界strcpy；沒有記錄內
終止字元時明確回報unknown。native_effect讀實際有序名冊，保留
capacity／reset／append／select／staged inactive slot條件，不作共用ID。
TW的portrait限制、CUSTOM技能與選取政策不移作CN規則。

新增 `SharedSubjectRosterPublication`，由實際共用已提交事件提供
原生30／31／34／35有序records，保持單一held aggregate。
原生技能definition由實際同一CN shared catalog解析並與records對齊。
實際owner於BeforeQueue／QueueAccepted兩次post-commit觀察中必須
資格化主體／收件者、真實pre-event roster、inactive slot／name來源、
capacity／reset／selection、逐筆演變次序、所有欄位／技能、規則、
存檔、持久重播、event／新revision。沒有自行發明建立事件或初始資料。

綁定於真正1C安裝的同一ready lease，綁定不發包。與既有獨立31及
34/35 publisher互斥選擇，避免競爭issuer；舊來源保留。Plan與definitions
跟随transport completion保存。local event fence不等於durable replay。
實際common issuer／Application尚未配置，不要求原生記憶體或pointer。

## 未完成與計數

本輪新增CN部分owner1，新增WORLD S2C30來源關聯1；31/34/35重用
既有opcode來源，不新增封包值。完整雙向路徑增量0，分母／完成數／
百分比未知。名冊16只是本consumer容量，不是全遊戲人物數或進度。

完整共用主體／名冊／模板名與欄位語義、rules/save/replay/committed
issuer/Application、CN skill import/provider、preborn初始issuer與84
caller／phase、全部TW/CN/PC/網頁/WSS玩法與變體仍未完成。
64位元數值、合格堆疊99、仙幣99,999,999,999、其他上限另定、等級
不變、集中全面測試修復及可恢復發布的完整目標保留。
