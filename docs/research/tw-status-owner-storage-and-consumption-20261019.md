# 台服效果目標選取、消費與存檔契約（round463）

本輪修正實際核心錯誤：83/action0D、非零WORD11的kind1效果，原生只選取
兩個mask中的第一個目標，原服務端卻對全部set bits套用同一量。現依原始
順序選side0的slot0..13，再選side1的slot0..13，找到即停止。raw mask與
逐筆結算順序保留；沒有猜測傷害生成公式或啟用中毒tick。

## 現用來源與連續目標鏈

TW EXE：`aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48`。
453筆BIN未改：`3adcda70a477086da50411fe5d023eec33f915efafd17ec478d55542cae42ea7`。
完整證據外存於
`C:/Users/risei/.codex/artifact-archives/god2-server/20261019/status-owner-round463/`。

516AE0的限定CFG為509條指令，沒有未展開跳轉。516BB1取得logical pointer，
516BBD令EBP=logical+1；516C38..46把EBP+4，即logical+5的兩個WORD masks，
交給51E5E0。該35指令helper先掃side0，再掃side1，各掃14 bits；51E610到
51E626在第一個set bit立即返回。516AE0只有一處517183呼叫52C520，沒有
逐目標呼叫迴圈。所選action0D非零WORD11分支將傳入side/slot打包存入
actor+62E[index]。這是連續caller／producer證據，不是單由consumer猜測。

516C4E的來源改向只適用action03且logical12==2；它不等於action02或
WORD11的accumulator kind2。後者另在52B870改向source，核心仍拒絕kind!=1。
現有parser的非空低14-bit masks、selector20及outcome限制保持；不把raw
parser縮成singleton。空mask、其他action及actor播放條件未因此取得權威資格。

## 初始化、逐筆套用與本地播放邊界

52C553檢查actor+239，僅其為0時清actor+2C4，並於52C57D/583以140 DWORD
清除`[actor+B60, actor+D90)`。51FDE0初始化亦清此範圍，51FF2C清+239。
不能描述成每筆接收都重設全部效果，也不從清除span推定新玩法上限。

kind1..3分支52CAD0取有號WORD+2C4索引，52CAE3加一，分別保存kind、
packed target、selector及B60/B64量。52B870從index0依+2C4逐項消費，
52BC0C..37推進量指標8 bytes、kind指標2 bytes及索引。重複目標仍是不同
entry，須逐筆clamp；HP100/max200依序+150、−150得到50，先合併會錯成100。

兩已知caller推進+233播放substate，所選後續state不再直接呼同一consumer。
這只是限定本地播放流程；consumer尾端未清量，不代表跨重連、新動作或
其他writer的持久化once-only保證，也不是中毒回合遞減或tick。

兩次新REA Evidence：
`ev_a8e53cf5a4f4fcc893d9b37012baae88966a4327a729981667e0a4dc6a1ade75`、
`ev_63a6081b83c7430c9a82b865dc20081a7120ba872c39154c98fad215fbf4344d`。
3498條原始指令資料已逐bytes核對，兩session已close且terminal exit0。
v24分析映像SHA為`a59348ed7cea9701de06701d9a3d1eb8c5a5dfaa636884786f65407f50de14c5`；
101個analyst seeds不是原始caller，13個原始sections不變，映像未執行。
完整結果見`native/consume-native-conclusion-v1.json`，warnings及限定範圍保留。

## 核心修正與回歸來源

`RecoveredBattleDelta::Record::selected_mask_target`新增原始選取順序，
targetMask／parse／encode／accumulate保持。`Battle::apply_native_deltas`
先驗證整批各自選中的target存在，再只對它套用HP／MP與outcome檢查。
未選bit不改actor，也不因該actor缺席阻擋有效首目標；首目標缺席則在任何
更新或encoder前拒絕，不試後面的bit。這仍是既有可信服務端結果接口，非C2S。

既有C++回歸來源補入兩側優先序、同側最低bit、未選目標缺席、首目標缺席
且不呼encoder／不改checkpoint、同目標多筆效果的clamp順序。Application
原有enemy HP−30／self MP−10兩筆singleton診斷記錄保持。
獨立靜態複核見`scope/delta-first-target-static-review-v2.json`；未編譯或執行測試。

## 持續狀態的儲存缺口

`scope/storage-contract-v1.json`核對Battle、兩repository及實際RoomState：
checkpoint v1／v2嚴格維持9／10-key及十欄actor格式。角色診斷與paired PK
持久化僅接受v1 LegacyCustom；PK還限制0／14兩actor、HP／MP以外權威不變，
以及由兩份已收動作產生的最多兩次revision增量。直接塞status／額外tick
會破壞契約；vector加入snapshot亦會破壞現有nothrow-copy提交保證。

本輪沒有改checkpoint、schema、玩家存檔或PK交易。持續效果仍須狀態取得、
實例／世代、觸發、清除／疊加及恢復權限，與HP和outbox共同交易；單獨加
版本或sidecar不能提供這些權限。中毒maxHP/10保留round462的精確商餘數，
取整答案尚未收到，未自行floor／ceil／minimum1或跨tick累積。

PHASE1維持source/static：未建置、測試、target／VM／codec執行、遊戲DB SQL、
遷移、啟用或部署。唯一正式靜態報告沿用v29格式分類，新增完整玩法0，
全遊戲分母及完成率仍null。命中／暴擊、傷害／治療producer、減傷與五行／
抗性原始判定仍依各自未閉合來源追查，不以本次目標修正冒稱已恢復。
