# 台服選神／學習時間鏈與 HMD prefix（2026-10-19，第482輪）

PHASE1 僅源碼／靜態工作。前輪71c3a84已接上 Legacy Written 選神到完整
restoration／learning Entry；本輪補強回歸源碼，並閉合下一個主場景資源來源。
沒有編譯、執行測試、SQL、產品／native／VM／codec、遷移、啟用或部署。
目標保持 active；完整玩法分母／完成率 unknown/null，盤點分類不增加。

## 已核對的選神／學習行為

同一 TCP read 的兩個獨立原生 frame 並不合併為一個學習交易：
Session.cpp 於解析完整 frame 後停止，只有真正 skill continuation 才續收。
同一 logical frame 混合 C67／claimed 技能書會被學習 preflight 拒絕，
Session 在 result.has_value() 為 false 時關線；未發現可存活的舊來源污染。
不存在的 C67 key 也從 helper／registry／service 逐層返回 nullopt，再關線，
並非成功的 NoOutput。這些核對不能當成同 frame 混合交易已支援。

recovered_legacy_selection_learning_reanchor 保留空背包模式，新增 with_book：
真正 bootstrap 原始 WWR Written → C67 Written → reanchor → use_with_source
產生實際 Lua／repository 扣書與 private publication → bind 原始 WWR →
Pending 拒絕 → Written → 同鍵／不同鍵 C67 → reanchor → 第二位神明再學習。
新增檢查 follows(previous)、舊 learning Current 退休、兩次數量扣除、完整
inventory／equipment bank／opaque bytes 及實際 activation event lineage。

取得與 SKB binding 是明示 CUSTOM_TEST_NOT_NATIVE 測試資料；110-byte 技能列
複製既有精確歷史 Taiwan row，不是新453資料或原服授權。activation／learning
資料由真實 repository issuer 產生，沒有直接塞入成功事件。實際 Session
負責原始回覆的 Pending／Written；測試 peer callback 不冒充完整 Application。
靜態覆核補上明確 RecoveredTaiwanInventoryItemRecord 標頭依賴。
這是已寫入的回歸源碼，尚未編譯／執行，不能宣稱測試通過。

## 已閉合：HMD logical request → model+1C

目前 aaf0 台服 EXE 已重新用 REA／Ghidra 靜態分析，完整原始13節的 mapping
與 raw bytes 都未變；分析專用 synthetic callers 不是原生來源且從未執行。
七次有界分析共回傳16個函數，包含既有函數對讀及字串支持函數；不把這個
數量當成新增16個原生玩法或已完成 Main。

1. 436337／436342 在 map+0x98 建構44BE40 model manager；其+0x1C 是 CString。
2. 437991..4379AA 把437900實際收到的 logical pathname 複製到 stack+0xB4。
   4379B4 找最後 byte0x5C；4379C0 在反斜線之後寫 NUL，保留斜線；
   找不到時4379C6將首 byte 清零。這個 byte 規則不能換成任意 dirname 正規化。
3. 4379D9 把 directory prefix 保存到 map+0x78。
4. 437AC8 的4-byte stack保留使437AC9的 ESP+0xB8 仍指向先前 stack+0xB4。
   437ADC經55ADA3建立 by-value CString；複製的是已截斷 prefix，非完整路徑。
5. 437AE8使 EDI=map+0x98；4370C9對同一物件 ADD ECX,0x1C，經55AE6E
   把字串值保存至 model+1C＝map+0xB4；437AFD同一 EDI呼叫44D750。
   既有44D520／44C6D0 ROMFILE鏈因此可讀到該前綴。
6. 55ADA3依 lstrlenA 建立字串；55ABA2初始化有效 storage 的 refcount／長度。
   55AE6E一般分支共享值並增加引用，locked分支55AE41依來源長度進行
   byte transfer並補NUL；54A8C0可見前後向／對齊的 byte複製分支。
   沒有觀察到以繁簡、大小寫或分隔符轉換改寫 prefix 的步驟。

map+0x78、map+0xB4、stack+0xB4 是三個不同記憶體位置；相同文字值來自
上述傳遞，不是把 map+78 誤當 model+1C alias。

448300 另顯示：相對名稱可先經目前選中的 manager base 展開，再送437900。
故應從437900真正收到的 logical request取得prefix，不是只從 CAN raw相對名稱，
更不是從 loader最終選中的 .hmdZ 檔名推定。root／cwd／manager base的實際
配置及43C170、52F550 context仍需來源持有者閉合；不宣稱全呼叫圖已還原。
46BB60／46BC00同取59D80(area,0)的row+B0，前者截最後反斜線、後者替換
最後副檔名再交52F550；這不單獨證明 CAN tag1 到室內建構的 dispatcher。

## 預載期間的矩形寫入

4606D0 在既有時間分支把 world+A7F2F50 的地址與 world+A7F2F62 的 WORD
交41BDC0。41BDC0檢查低WORD<4096，取 manager+0x10+index*0x290，
在row+0x50寫16 bytes或用SetRect歸零；row+0xE的handle<5000才交425BA0。
後者以manager+0x1258+index*200定位：nonnull時複製16 bytes至row+0x98，
並使row+0xB8指向內部副本；null則清指標。null與指向全零矩形不是同一狀態。
這兩層的nonnull結果沒有保留 caller矩形指標；其餘 native物件生命週期不因此
被證明。數值4096／5000是此處 manager bounds，不能變成遊戲NPC／怪物上限。
顯示用途是上下文推論；完整裁切效果與其他預載helper是否泵送事件仍未證明。
不能把這段會寫狀態的 native preload當成server純Current observer。

## 現用 CAN／HMD／ROM 與真正下一步

重新讀取目前原檔，Island01.can 2580B，SHA256
73156f4c2060f92e1be59fa9c2df30841b3df204121491a765c1ca21e68796ad，
與舊文檔的歷史雜湊不同。36 files／130 scene slots，scene15選record12，
record byte780，raw tag1，原始路徑 indoor\groceryl.hmd。只觀察資料不代表
native selector已執行或server已安裝；raw tag不能直接當2A entry kind。
現有 groceryL.hmdZ 329B／groL.romZ 222205B 的完整hash見相鄰JSON與封存。

最小實作應是實際 immutable CAN／HMD／ROM bundle owner，直接供應
Sources.movement_resources：bounded C++ CAN issuer → 真正 logical request／
選檔結果 → 完整HMD、ROM、placements／sort／Grid → owner發行新epoch →
精確weak Session／完整Lease／私有entry的Current、install、replace、cleanup。
不需要再增加一個未供應資料的HostPlan wrapper。

server immutable asset epoch可由真正發布者發行，不必冒充遠端client計數器；
TaiwanNativeActorResourceSource的next_epoch_是可參考模式，其Hero／Drv／DrvDoll
ResourceInput與epoch不能直接借作地圖bundle身份。現有TaiwanNativeMapAsset
已有ROM binding、物件排序與Grid；HMD物件不可改塞成NPC72，戶外MDL幾何子集
也不是完整HMD替代。完整2A、saved facing、初始actor／NPC選定與次序仍需真來源，
歷史2A候選／硬釘6bf的appearance不能冒充目前aaf0權威。

全部16個函數的完整MCP Evidence／assembly／close、三份分析映像的原始節
mapping proof、目前檔案、source pins及唯一正式盤點收據保存於：
C:/Users/risei/.codex/artifact-archives/god2-server/20261019/selection-learning-chronology-round482。
