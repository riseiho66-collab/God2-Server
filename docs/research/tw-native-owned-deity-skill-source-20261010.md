# 第242輪：台服已選仙靈的完整持有技能來源

本輪新增實際儲存來源，優先續接台服C35所需的持有資料。沒有新增抽象成功回調，沒有啟動測試、原生程式、遊戲資料庫或部署。此來源還不是完整戰鬥施法。

## 已寫入來源

`SqliteCompanionRepository::load_selected_deity_skill`在自身連線的一筆唯讀交易中取得帳號／角色所有權、已選仙靈key與selection revision、完整19-byte declaration／29-byte status／全部有序4-byte已存技能、仙靈revision及原來源provenance。不存在的selection／skill回傳缺失；破損、來源不符、TEMP遮蔽或已開交易則拒絕。`selected_deity_skill_current`攜帶不可跨repository重用的觀察身分，重讀並比較全部上述資料。舊bool及其他load/write內容保留。

`SharedTaiwanOwnedDeitySkillSource`將該實際readset與完整110-byte技能定義連在一起，明確釘住same149c image／raw kind/id／原row geometry。NativeSkillCatalog檢查hash字串格式並保留完整raw及metadata，本輪未新增raw payload SHA重算。觀察另帶實際Session身分、common ready lease、儲存位置、phase及battle_generation；使用前重新讀取。操作期間持有自身、內部狀態與真Session，拒絕錯game owner及重入。

Application的既有Context現在附上同一Database實例的companion reader；HostPlan保存並比較該實際pointer。`RecordSources::owned_deity_skills(context)`建立具體來源，不安裝虛構WorldOwner、S87、扣費或Main。一般create僅借用給定來源，不能自行證明不同參數共用同一SQL connection；同Database關係由實際Application caller提供。

資料庫內的一致讀不等於catalog／common lease／companion跨來源的一筆原子結算。此能力只適用觀察和action前資格；未來真action需在自己的交易中資格化並一次耗用完整readset。既有開放交易不支援嵌套這個唯讀來源。

## 原生來源界線

S34把已學技能寫入roster row的count／flags／definition pointer list。戰鬥initializer先清空primary bank，再保存原roster row pointer；本輪保留的資料前綴沒有把S34技能列表複製成戰鬥列表。S87獨立以WORD建置／更新primary battle list；86/5另設控制狀態與actor nibble。因此已選仙靈key、已學技能、戰鬥可用技能與受控actor不能互相代替。

4A90D0比較definition WORD+42與owner->86888物件的DWORD+64；selected row另由該物件+D0取得。這段沒有扣除或寫入，不能據此發明服務端MP收費或把標量當受控actor資源。

既有仙靈持有資料使用70a4來源與CUSTOM-0039保存規則，`RecoveredDeityState::valid`仍沿用6bf display及原CUSTOM資格。保留該來源原貌，不將它提升為same149c原生戰鬥caster／learning／grant證明。

## 真正尚缺的producer

1. 原roster／已選仙靈到本次battle controlled actor的真綁定與生命週期。
2. 有序S87可用技能發送、86/5控制歷史、精確context與本回合grant incarnation。
3. 真正受控actor的MP／資源、扣費時機、折扣／退款規則及一次性耗用。
4. 完整目標與規則結算、所有action/effect/MP回包及完整WorldOwner實作者。
5. 普通Main的完整75角色列表與發行token、2A世界入口材料與issuer、entered scene／peer／resources、原生geometry／5D及world owner。

Application中的`pk_rooms`目前未實例化，RoomAuthority getter仍回傳空值。既有OwnedPkRoomState／SqliteOwnedPkRoomRepository的CUSTOM-0086結算能力不等於本次原生WorldOwner；其caller-supplied owned_attack_skills、單actor規則、未接caller和後續grant限制不補齊上述缺口。既有CUSTOM／診斷／凍結路徑未被擴權。

## 本輪進度

修改6個、新增2個C++檔；新增1項完整持有資料觀察能力，混合TW/CN部分來源段226→227。新增完整雙向玩法0，新增opcode0。TW C2S候選156、world S2C252（230固定／22變長）、battle索引110不變；這些是不同索引，不能相加當遊戲功能總數。完整方向／phase／state／variant分母與台服完成百分比仍未知。

三個分工保留各自原件／讀取epoch。原生分工本輪保留8段1,025 bytes／297指令位置，新增全域原生覆蓋0。封存verified僅指檔案長度與hash會計，不是功能驗收。

目標API本輪實際讀取為active，舊第241輪blocked紀錄留作歷史。繼續依使用者要求先完成台服全部來源串接，沒有自行暫停或另建替代目標。

本輪未build、test、runtime、native、codec、遊戲DB/SQL、migrate、deploy。共用/CN/web、帳號存檔、聊天、IME、認證、原生字體及繁簡轉換、數值64、仙幣99999999999、堆疊99及既有等級設定保留。

完整來源原件、差異、分工封存與回報：`C:/Users/risei/.codex/artifact-archives/god2-server/20261010/tw-native-skill-authority-source-242`。
