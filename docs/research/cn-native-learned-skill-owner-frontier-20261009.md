# 原生學習技能的主體與存檔來源（第195輪）

本輪完成三項可追溯研究：限定陸服 WORLD 主體與 battle 初始化的真正同源地址；恢復三個純資料 getter 的117 bytes；盤點實際技能存檔與其 origin/profile 限制。沒有增加 C++ 介面或把原始旗標當權限。來源串接段維持186，完整雙向玩法新增0，全遊戲分母及百分比仍未知。

## WORLD 與 battle 的實際來源橋

固定 CN582f 映像及實際呼叫中，令 P 為原始 world owner、R=P+1478084、U=P+89B26C。`48DA4A` LEA U、`48DA8A` 存到 EBP-A10；傳入 `54A320` 的 bundle base 是 `48DE03` LEA EBP-A18、`48DE09` PUSH、`48DE0A` CALL。因此 U 在 slot2；`54A375/378` 讀 `[bundle+8]` 寫 H+20，**H+20=U**。R 是 LEA 地址而非解參考 R+0，放在 slot4，`54A381/384` 寫 H+14。

WORLD mode0 的真正 caller `48E3EB/48E48F/48E4AC` 以同 P 的 U/R 呼叫 `4AF370(R,0)`，`4AF493/496` 進 `4D2D30(R+90)`，後者寫 U+430A8。Battle initializer 使用 H14+90。這限定了同原 P、同實際生命週期時的 WORLD 與 battle 來源關係；原生地址仍不是共用64位 actor ID。

初版把 EBP-A0C 錯算成 slot2，因而誤稱 H20 是另一個 loaded context。實際相對 EBP-A18 的 A0C 是 slot3，loaded `[P+A69F1C]` 經 `54A37B/37E` 寫 H24。代理和 Root 的錯誤初版、完整修訂、diff及逐slot stack ledger另存，Root獨立讀原 bytes後更正，沒有重寫193/194基準。

Battle mode1 `54A7C4` 呼叫 `4AF370(R,1)`，沒有進入 mode0 的 `4D2D30` reattachment 分支。因此同源證明仍需真正原 owner/current epoch；不能因一個地址關係就重綁或刷新舊主體。WORLD34/35 caller ECX=U；battle34/35 caller經 H20 指向該同源 U。原 canonical phase2 case35 尚有 D1／4C9530 continuation，這個後續 consumer 未宣稱完成，也沒有跟進 GUI/callee。

WORLD34/35 的原生 subject BYTE 比較實際 row WORD，U430A8 的列表以 D8、3EC stride 找列，row+1F0 為 count、1F1 為原 flags、258 為原 pointer array。S34追加完整 bank-relative110B技能指標、flag0；S35對匹配 pointer 設flag3。這些原生資料變動不等於服務端 acquired/learned/cast grant，不能按相同kind/id自動鏡像成 S87。Battle group+2D4 持 R90+D8+n*3EC 的 row來源，但主列表仍有自己獨立的初始化、S87到達順序及狀態。

Native主體代理保存16 retained spans／1405B（2 complete／890B、14 bounded／515B），381 instruction sites、65主要來源sites。全部為既有原生範圍，本輪不重計新原生函式、opcode或玩法。

## 三個新定點資料 getter

| 原始完整函式 | 大小 | 確認的窄資料語義 |
|---|---:|---|
| 5537E0 | 37B | BYTE ordinal<count(component+5)，回傳 component+ordinal*2D0+26C 的原 auxiliary BYTE array地址 |
| 553810 | 27B | component+2D10 的 BYTE selector<3，回傳 component+selector*54+2D50 的 secondary state array地址 |
| 553B40 | 53B | primary selector≤F、signed count>0且index<count，從原 WORD+14+2*index讀bit15；原生沒有index≥0检查 |

Root讀完整三份 canonical C與全部原指令；新增的117B限定於本輪定點比較的193/194 span/input manifests，metadata列名不算原始C或raw coverage，不宣稱全歷史從未讀過。另三段636B initializer證據保留舊分類。現有 `CnBattleSkillSelection::Snapshot` 已保存完整 component351C/rawWORD與 current，不另造等價 reader，更不把 getter 的bit15設為權限。原生負index分支缺少下界檢查也不是服務端可接受負index的規則。

552870/553220 的完整 top-level實際寫的是外部GUI WORD handle及3510/3512=FFFF，矩形／控制來源字段保留；在這兩個限定 top-level沒有找到 subject skill array 到 battle 主列表的資料複製，不用GUI名稱作全局缺席證明。沒有追入render、字型、glyph或155/52F330/52F170停止鏈。

## 真正既有存檔及可共用界線

`RecoveredCharacterRepository` 完整介面包含角色、資源、等級、經驗、位置與戰鬥結算，沒有 learned-skill load/commit方法。具體技能資料在 `SqliteCompanionRepository` 的 character_deities：完整TW S34四byte陣列、19B declaration、29B status，使用實際 account/character所有權、expected revision CAS、transaction/readback、pending-battle限制；selection有自己的revision。

這組存檔固定 TW70a4來源，provenance接受 NATIVE_VERIFIED／CUSTOM_DESIGNED／CUSTOM_TEST_NOT_NATIVE；CUSTOM0039包含持久化／選擇政策，TW icon gates及CUSTOM0058/0059診斷caller也有自己的界線。`selected_deity_has_skill` 只以選中owned row的rawkind/id判斷，沒有CN mapping或origin類別區分，不能直接拿該bool當CN學習權。

可以共用的是所有權、CAS/revision、transaction/readback及既有 native_data_sources/native_skill_catalog 表的來源機制。CN catalog本來就在共用表，以正確dataset/source/完整110B原件限定453定義；TW來源381定義或技能書綁定不自動等於同一共用玩法skill ID。NativeSkillBookCatalog只含來源／道具／定義binding，沒有owned learned row、消耗或學習transaction。

CN preborn source的必要apply／postcommit qualifier、WORLD34/35 publisher與battle87 publisher目前仍要求真正供應者；BattleData必要DataAuthority也沒有從data membership推定權限。在保留的介面、SQL源文字與限定Application caller中，未找到可直接當CN learned owner的具體實作；這不是對所有未讀檔案／DB內容的全局缺席宣稱。既有fixture／CUSTOM0006/0007/0008不冒稱CN原生規則。

## 網頁新交接

已現讀並保存契約新增段、commands v5.1及runtime v9完整新epoch，兩份指定SHA核對相符。角色／服務端欄位研究明確排除World+84330的FightComm資源管理器／stride108；+528共用5列是 Eft2_8301.rom，附屬6/9是action0/depth51。原九筆位置WORD掃描與必要選擇數上限5分開；真正Input12018／三flag→54F360及54AAA0清12018/12020都是client操作生命週期，不當server grant／settlement receipt。

C35 logical17／payload16、offset5陣形兩WORD／255及普通mask、03/83與獨立待接17/97保持。完整God/compound/GUI/autoreset、actual actor/context/grant/learning/cost/formation/once settlement/native replies/Main仍OPEN。已依所有者既有授權發送來源ACK，保存exact draft和actual tool receipt；來源ACK不等於全遊戲完成、發布或共同驗收。未修改網頁客戶端。

## 本輪計數與接續

| 範圍 | 當前值 | 本輪增量 |
|---|---:|---:|
| TW／CN C2S opcode聯集 | 各156，phase/variants未列齊 | 0 |
| TW S2C世界支援長度 | 252＝230固定＋22變長 | 0 |
| TW S2C戰鬥索引 | 110＝9特殊＋101預設 | 0 |
| CN S2C分階段 | 帳號6／世界206／戰鬥68，共280 | 0 |
| Endpoint紀錄／source groups | 958／28 | 0 |
| 來源串接段 | 186 | 0（本輪研究） |
| C++新增／修改 | 0／0 | 0 |
| 完整雙向玩法新增／全遊戲總數／完成率 | 0／未知／null | 未建立分母 |

繼續從限定的同P/U/R來源追真正 common actor/owned subject映射、學習取得／變動規則、原 revision及durable replay／事件、獨立S86/S87完整歷史、MP/item/range/target/formation/cost、一次結算和完整native回覆／Main供應者；不能自動把WORLD更新當battle87清單。

before1398與prior194完整2562封存成員、Root current/C原件、三代理所有初版訂正及final來源、網頁新epoch、唯一round報告分開保留。帳號存檔／字型／繁簡轉換／IME／認證／頭像／客戶端及凍結功能不改；共用表、台陸網頁全部玩法、共用64位與明確wire/object/飄字、仙幣僅99999999999、stack99、等級不改的完整目標保持active。

PHASE1只執行原件保存、PE／Capstone靜態恢復、文本、hash及檔案帳務，沒有建置、逐項測試、native／C++／Lua／codec／API／runtime、DB／SQL執行、遷移、部署或客戶端驗收。所有來源串接後才集中全面驗證修復發布。
