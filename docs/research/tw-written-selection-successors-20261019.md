# 台服選神後的完整來源延續（round474）

本輪把 CommonWorld 實際 C67 選神提交，接回完整神祇清單、技能書學習及
既有 PK player／companion 來源。這是原始碼接線與靜態核對；尚未建置、
執行測試、部署或進行原版客戶端驗收。全遊戲完成率仍為 unknown/null。

## 已修正的來源中斷

選神會改變保存的 selection revision。提交後再要求舊清單或舊學習來源
符合 Current，會拒絕合法的新狀態。新流程在 SQL 前保留同一私有來源，
按原 callback 中全部 C67 的次序保留提交，等實際完整原始回覆 Written，
再建立不同的新來源。舊 token 不會重新變成 Current。

- Repository 只接受同一私有 issuer 的提交鏈；逐步比對 before/after
  selection 與完整選取列，最後核對完整保存狀態。
- 完整 16 列、100 格 learned／auxiliary 容量及 inactive tails 沿用原來源；
  只追加真正的 29-byte S31，不補發 S30、重匯清單或重建舊 receipt。
- Application 在開始新選神 callback 前完成舊來源結算與 PK ancestry
  保留，並核對 Session、完整 account/character、normal INIT、holder、
  world 及 prewarm 結果。新 callback 會立即使舊選神 token 失效。
- 全部選神 component 共用原先那一整筆 WorldResponseWrite。Pending
  不可供後續使用；Failed 或喪失 private Written 來源時關閉連線，
  不重做已提交 SQL。Written 是本機寫出結果，不代表遠端採用或回合權限。
- 新 learning entry anchor 指向選神後完整狀態，另外保留最近一次真正
  learning publication；因此「學習→選神→再學習」仍檢查原先 chronology，
  不把選神冒充一次學習。learning origin 與當前完整清單分開保存。
- PK player／companion 只能成對採用同一新來源；缺少原始 ancestry 或
  任一資格失效時維持不可用，不從提交後 DB 回造舊來源。
- PK artifact 增加扁平的來源歷史 metadata：原始 transport 一次、各次
  learning／selection 的整筆 wire、全部 selection ordinal 與提交前後值。
  各 S31 是 component，沒有獨立 Written receipt。沒有新增 schema、
  變更保存資料或提供可由 JSON 還原的 private capability。

## REA 補查與前輪界線更正

現用 God2.exe SHA256 為 `aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48`。
現用 cbspec2.bin 為 `3adcda70a477086da50411fe5d023eec33f915efafd17ec478d55542cae42ea7`，453 筆。
本輪重新核對 12 個函數的 1,426 條原始指令，新增 2 次 REA 靜態 session、
5 個函數分析，兩個 session 均已關閉；分析映像的 13 個原始 PE sections
逐位元組符合現用來源，沒有執行客戶端。

`51BB80` 完整本體會初始化 16 個 primary banks，尾端確實呼叫 `51BD70`
重設 3 個 secondary banks；但是 secondary header `+2D12/+2D13` 沒有
在已核對的建構／重設範圍得到實際寫入來源，不能一律補零。
`5112C0` 完整 parent 尾端也確實把兩個 controls 清零；這只適用於該
完整原生事件的精確時點，不能從 prefix 或網路 Written 推定。
較早的 actor FF 寫入之後還有多個子函數，不等於完整返回時仍必然 FF。

前輪若把缺口概括成「完整 16 列與所有 inactive tails 都沒有來源」，範圍
過大：現有 normal prefix 已保存這些完整資料。本輪仍缺的是特定客戶端
初始化事件與 sameWorld/current epoch、actor、未知 secondary header 及
真正 issued87／grant 的接合。學會的 34、正常選神 31 與戰鬥發放 87
維持不同來源，不能互相替代。

## 尚未完成與驗證限制

Legacy Application C67 分支尚未接入同一 private whole-Written registry；
本輪完成的來源接線範圍是已配置的 CommonWorld Shared 選神路徑。
一般技能 C35 的實際權威 world owner、原始傷害／治療量產生端、持續
效果的 tick owner，以及攻防、五行、抗性等原始公式仍未還原完整。
本輪沒有新增原始公式，也沒有把本機來源延續算成完整玩法驗收。

新增測試原始碼涵蓋完整 roster、私有提交順序、錯誤 issuer/owner、未選列
變更拒絕、inactive tails、實際整筆選神回覆 Pending/Written 與舊 token
失效。完整 PK appearance/equipment 與 learning full-state 混合鏈仍缺少
現成 fixture；不宣稱這些情境已測過。所有新增測試均未執行。

可機讀來源、證據摘要與界線見同名 JSON；詳細 REA 原始輸出及來源雜湊
保存於專案外 `issued-skill-initializer-round474`，不納入執行依賴。
