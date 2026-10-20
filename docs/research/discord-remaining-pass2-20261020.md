# 非座標問題續查：羽毛、前後排、SOS、Windows（2026-10-20 第二批）

接續775e473。獨立PHASE1來源／靜態工作，沒有恢復完整目標或4-discord排程。
本輪沒有重新擷取Discord；沿用既有96組清點，外服回報不是本服重現證據。
NPC／怪物世界座標、原版EXE／BIN、玩家存檔及正式DB未修改。

## 已做來源修正與再審

1. **銀行跨服務撤銷。** 金錢服務現在提供不可由呼叫者捏造的LeaseSource，
   以同一個私有State的weak引用與不可逆valid撤銷標記識別這次開啟。
   關閉、拒絕、斷線、重開會退役舊來源；相同角色／NPC重開也不會復活。
   正常續期只更新同一來源，已逾期不能靠續期重新取得權限。
   普通物品、防具、武器／珠、混合／PET四條選定路徑都在開啟時捕獲實際
   金錢來源，保存於context；每次回呼後與最後SQL readback後的純檢查沿用
   同一來源，不在最後檢查呼叫SQL、網路或重新發行權限。
   Application中typed open之前的空容量provision也已接這個來源，核對
   原owner，並在返回投影前再核；失敗一併退役物品context。
   二審另修兩點：金錢提交使用真實到期來源，不只看早先admission now；
   malformed batch及早期catch recovery也要先核來源，不能送舊owner資料。
   已跨COMMIT的結果仍是committed，失效只撤銷操作狀態並抑制舊投影。
   沒有改費用、容量、疊數、物品資格、DB schema或正式啟用開關。
2. **材料回覆資料壽命。** SharedTaiwanOwnedInventoryReplySource::prepare
   在虛擬presence／character回呼前，保留輸入、Selection及Session；material
   take也保留self、提交憑據與Session。最後presence回呼後重新核對inventory
   與equipment兩份durable tuple，防止釋放後續用或送出過期材料。
   只修既有條件式C28 component；這不是已串通羽毛銀行的聲明。
3. **PK房間回呼。** OwnedPkRoomState按每個room防同步重入，保留呼叫輸入；
   外層staged Battle不再繞過容器的生命週期。mutable入口、outbox／grant
   提交、terminal resource save及finished return preparation／commit／retire
   一起查。持久化期間失效會保留claim／歷史並要求durable recovery，不能
   拿舊model重試或假稱已rollback。Publication需要的read-only重讀保留，
   不同room沒有共用全域鎖。沒有改傷害、封包或兩人0／14的既有玩法。
4. **登入回呼與重試。** async入口先保存原始帳密bytes，repository回呼改掉
   caller buffer不會改變重試身份。既有64筆配額在prepare前保留，失敗／
   worker拒收會歸還；來源競態最多一次原憑證重試。completion拋例外不會
   被當repo失敗重呼。worker回owner後核對id／username／created_at／hash；
   目前沒有帳號更名writer，因此後者只列防禦性來源漂移，不冒稱更名bug。
   Application的worker pool在帳號owner之前join；未宣稱任意失效executor
   或worker到game dispatch OOM已獲完整shutdown保證。

修改者逐項重讀差異，主控再查實際呼叫、資料壽命、權限、保存、回覆與
失敗分支；銀行另作獨立交叉審查，兩個P2均再修後重讀。新增銀行與登入
回歸僅為待執行來源，沒有通過宣稱。PK Room及材料source沒有現成完整
fixture，必要動態場景明列，沒有新增私有權限後門或假static測試。

## REA結果與仍未完成的實際功能

現用目標SHA256：
`aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48`。
分析映像13個原始section逐byte相同；synthetic CALL僅為分析種子，不是
原生caller，映像未執行。失敗／錯cut證據保留，所有開啟session已關閉。

- **羽毛倉儲仍OPEN。** 只讀重用SHA精確75c3的歷史plaintext，找到4422
  原文；沒有解碼目前ef297資源，也不將歷史來源冒稱目前資源已資格。
  REA 4723A0／4722B0按原生instance分類隔離bank特殊0／1格；普通銀行
  未見因MIS羽毛而拒絕，471E50回覆完整20 bytes＋quantity。49B770的30／1
  是客戶端數量對話選擇，不是服務端99疊數權利；mode2的7F是另一種
  storage，不能混入普通63／64。
  真正缺口是0092完整實例尚未接普通銀行host：需同一ID原位custody移動、
  bag50／bank300別名分域、page／local slot、完整25 opaque保留、設備聯合
  CAS及48全倉重開投影。不能把0092實例複製到legacy銀行造成雙重持有，
  也不能猜split／新ID／初始metadata或私服規則來湊完成。
- **前後排保存仍OPEN。** action6是FLEE，action9才完整六layer交換。
  本輪排除把C1D或B1 selectors7／8猜為世界前後排的捷徑。新取得人物
  panel ctor4E7C80與真正updater4E8580／4E8600入口；保存owner、世界
  producer／consumer、戰後保留及重登規則仍需沿此追查，沒有捏造欄位。
- **完整SOS仍OPEN。** 512790→5156E0→518E50 action8會依primary／secondary
  grant選擇來源；83/action8的WORD9零／非零只影響side0的+488旗標，不能
  命名成HP或當加入權限。現服務端缺same-room admission／多人PvE roster，
  不能以兩人PK或觀戰6E冒充。新加入者須沿實際當前Battle投影死亡狀態及
  寵物grant，不能重放初始roster；這仍是待實作的一致性條件。
- **Windows相容仍待實機證據。** 531BC0→70A0A8只在ACP936回0804，其他
  ACP回0404；與70A000實際依GetACP轉碼相比，ACP非936／950時有條件性
  旗標不一致風險。未觀測到遊戲過程使用65001，Launcher又固定經Locale
  Emulator，不能據作業系統版本推斷根因。literal問號無法由服務端還原。
  Launcher主UI等待helper、repair完成通知失敗及panel timer丟失程序追蹤
  三項來源待辦只讀保留，未跨repo修改或宣稱Windows7／10／11已驗收。

本輪沒有build／test／game／VM／codec／遊戲DB SQL／migration／deploy。
上一輪唯讀codec偏差不抹除；本輪沒有重跑。沒有新增完整玩法完成數、
全遊戲分母或完成率，也未將上述四項勾為完成。

證據根目錄：
`C:/Users/risei/.codex/artifact-archives/god2-server/20261020/discord-remaining-pass2/`。
`materials`、`formation-sos`、`windows`、`bank-lease`各保留REA、來源雜湊、
再審與未知項；正式盤點仍沿既有packet index，與現用REA目標不同時另附
來源註記，不能當成現版原生或黑箱驗收。
