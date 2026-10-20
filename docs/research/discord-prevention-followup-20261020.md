# Discord 非座標問題：關聯修復續作（2026-10-20）

本輪接續既有96組問題追蹤，未重新宣稱Discord全歷史或最新尾端已更新。
外服回報只作核查線索；NPC／怪物世界放置及座標未修改。這是使用者授權的
獨立來源修復，完整目標與4-discord排程仍paused，沒有恢復排程。

## 本輪來源修復

- 神仙資料：既有可信store_deity只更新status／revision時，原先會令已學
  技能的激活header失效。現在同一交易只延續完整匹配舊header的見證；
  declaration、技能次序、來源不同或原header缺失／已過期都不會補發權利。
  原始學習事件／links不改寫；舊readset仍失效，新登入重新驗證完整來源。
  這不是正常領神、成長或初始技能系統已完成的聲明。
- 交易：完整實例及普通交易的lookup、名稱、資格、投影、receipt、proof
  回呼原可重入disconnect／refresh／handle，撤銷仍在外層使用的context。
  現在整個同步操作有重入防護、自己的請求資料及安全退役；捕捉內層例外
  也不能繼續結算。保存前後仍保留完整owner證據與CAS，最後readback之後
  再查純失效標記。取消、逾時、拒絕、雙owner回覆及重開同時檢查。
- 倉庫：金錢、scalar物品、防具、武器／回程珠、混合及PET分支一併檢查。
  在任何同步回呼前複製context與請求，後續查新iterator，不跨回呼借用
  已被erase的節點；開啟、權限、續期、保存前後及最後readback均保留失效
  檢查。持久化完成後續期失敗不再偽報未提交；失效owner不接收舊投影。
  原本paired before/after metadata proof不以單一舊snapshot比較取代。
- 戰鬥服務：既有Battle物件防護再接到服務層的basic、技能、復活、timeout、
  native delta、初始控制、phase／checkpoint。remove延後到操作離開，阻止
  dangling Bound及獨立staged副本互蓋；每個回呼後核對Session／角色／戰鬥
  世代。跨過持久化回呼後失效會退役，不能假稱外部DB已rollback再重試。
  native delta與encoder在回呼前自有複本，避免呼叫者清掉資料／函數。
- 組隊：同一Session不能靠observe把前角色的組隊／待同意邀請轉給另一
  account／character。必須先disconnect退役；同owner的資源／位置刷新保留。

各項修改者重新讀完整差異；主控再檢查呼叫端、狀態、保存、回覆、失敗與
同族入口。交叉審查另外抓出post-COMMIT renew先失效再拋例外仍送舊輸出，
已修正並補來源案例。此處是源碼審查，不是編譯、黑箱或原版遊戲驗收。

## REA與實際限制

目前台服客戶端SHA256：
`aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48`。
REA分析衍生檔13個原始section均逐byte相同，synthetic入口只是分析種子，
未執行映像；失敗的初次分析及後續有不同seed的成功分析各自保留。

- action6是FLEE；action9才經83/9及52A8D0／525B90交換六層slot指標、
  packed位置與presence／primary／secondary。不能拿action6修前後排。
- 隊友移除自身名字會清原生roster；雙擊頭像走原生定位查詢，不能推測成
  服務端踢人。原生ID與DBID尚無來源的映射不捏造。
- 全部前後排保存、戰鬥換寵、SOS、成長／EXP、正常領神、任務與一般材料
  倉儲仍有實際owner或規則缺口。發光羽毛等完整實例不能塞舊scalar倉庫。
- Windows中文在客戶端轉為literal問號後，服務端無法還原原文；未改正式
  EXE／Windows設定，也未宣稱Win7／10／11已驗收。
- 防護沿現有序列化game-owner執行，並非跨執行緒lock。每服務操作fence
  不等同跨服務全世界epoch；最後純fence也不是SQLite COMMIT trace／hook
  全域取消保證。Application在typed服務前的空容量provision仍缺跨服務純lease來源；`bank_items_disconnect`已有實際統一退役，但這不等於任意獨立callback的全域ABA保證。durable結果不偽裝rollback；這些邊界不列為已完整驗收。

本輪沒有建置、執行測試、遊戲、VM、遊戲DB SQL、遷移或部署。
**材料追查中有一次違反PHASE1的唯讀csvZ解碼，已停止並保留偏差收據**；
沒有改動原檔或遊戲DB。該輸入雜湊與既有資格pin不同，解碼結果未用來
更新來源資格或正式資料，不宣稱本輪codec零次。
新增回歸僅為待執行源碼，不能列為通過。沒有新增完整玩法完成數或百分比，
也未將96組問題標為全部修好。

外部證據：
`C:/Users/risei/.codex/artifact-archives/god2-server/20261020/discord-prevention-followup/`。
原始訊息與完整清點仍在前一份`discord-prevention/`，不改寫原始擷取。
