# 台服 PvE 換排與原生播放佇列：PHASE1 source

本輪只有 source／static。沒有編譯、執行測試、SQLite schema／SQL、codec、
原版遊戲或部署；下列接線不能代替後續原生實機驗收。

## 原生已證與 CUSTOM 邊界

分析目標 aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48。
REA 與 close receipts 放在外部 `20261021/sos-row-timing-continuation-pass5/native`。
`5127C0→5156E0→518E50` 的 action9 是17 bytes；target count0，兩個 WORD mask
為0。logical4／DWORD13..16 未初始化，必須原樣保存；context 是 B+3C。
操作者及 side flag 仍須由實際 owner／角色／grant 核對，parser 不授權。

S83/9 是完整15 bytes；WORD5、WORD7 為 flat positions，WORD9 是零／非零的
成功 gate。`52A8D0→525B90` 延後等待動畫後交換六層 renderer／packed position／
座標／presence，再用原 primary／secondary actor pointer 更新 B51／B52。
原生函數未證實官方 player／pet 配對公式，也未證實只能有兩個存活 actor。
因此配對來源仍明示 CUSTOM-0162：DB 提供完整版本 pair，允許已保留的空端點
或死亡 partner，但只有實際存活且有本回合 role grant 的 source 可操作。
不採用 +7、不建立 dummy pet、不由 client mask 指定配對。

新 REA 修正20261020快讀：`51D4E0` 真 FIFO append，`5140C0` 遇同 label83
後若 queue empty，並不 flush；不同 label83 或88／89才進 `52AC20`。
manager 的 expected／complete actor count 由掃描 label 計數，與88 DWORD不同。
group255經 BYTE+1 wrap 跳過掃描，故 CUSTOM label只使用0..254。
88 在 native queue 等目前 group 完成後套用；不能籠統宣稱「83後送88必重扣」。
實作恢復每個83 publication尾完整88 boundary。每個 battle 的88 counter沿用
完整可信 profile固定值；不是 grant_epoch 或動畫 actor 數。

`515AD4` 自動0B直接讀 B51，不經5156E0選 pet；即使 side flag1仍可由 primary
發出。0B共用518E50 cleanup會消耗 client A優先／否則B。因此0B只當未受信
client progress；server只重發該人仍持有的同 epoch角色86/5，不發新grant、不
改RNG／傷害，不對純refresh發88造成無窮0B。action2／target-gone pass另有
明確88 boundary，避免 native sent0B latch未重置而卡回合。

## 真正 canonical swap／保存／返回

MemberInput初入 primary_slot、active44 actor_slot、完整 raw pet、B4 row及
reserved_partner 為不可變來源。Member.assignment另存目前 primary／pet位置及
單調 revision。換排交換完整 optional BattleActor，再修 actor.position；HP、MP、
四維戰鬥能力、controller、死亡狀態、RNG與角色原始 raw資料不互換或重設。
無pet只移 primary到被保留的空端點，pet仍不存在。B4世界設定不隨戰中9改寫。

Repository在任何SQL前檢查唯一配對 permutation與完整 before／after checkpoint，
同 transaction保全所有成員完整 source CAS、實際 player／active44資源、member
live-slot mirror、checkpoint RNG、outbox。保存HP／MP按 live角色位置讀取；原始
pet input actor_slot不變。晚加入只可在既有 publication進度完成後，以當下新位置／
HP／dead roster入場，不能重設既有戰鬥。

Swap持久化 pending_swap。Host另外保留單一 private publication edge：server
sequence、原本 required viewers及assignment revisions、各原生0B觀測。新edge在
送出前建立；last-player／last-AI的Await stage也先建立。所有實際 outbox Written
及該edge每位目前仍繼續戰鬥的原viewer回報後，才能放下一個mutation。提早收到
的合法0B保留一次，不能因另一人的write未完成而丟掉。Tick不占command queue。
queued合法rolecommand保留其原grant epoch／assignment revision；不把舊slot當
換排後另一個角色。換排者的0B必須使用更新後B51 primary位置，舊primary不計。
同flush command＋0B先整批預驗，原0B只記目前edge一次，再從owned queued
command移除，不能replay到下一edge。pending swap舊角色command丟棄時仍保留
同批合格更新後B51回報。所有86/5投影都抑制已有相同epoch／assignment queued
command的角色UI；不改canonical grant，也不把舊epoch佇列壓掉新一輪授權。
完成時只清 exact pending edge及重發真實剩餘86/5，沒有1C／entry重播／HP重設。

動畫／outbox尚有edge時的C6A保留實際Session private prepared binding及輸入hold，
進bounded admission FIFO（最多14份且與retained members共同受界限），不先呼
member、不先開DBclaim／82／Fight title。edge完成後重新核選中target仍active、
完整self／channel／scene、fresh member與CAS，真Session commit後才entered/title。
失敗、disconnect、retire、closed room、stop取消尚未提交的準備並清matching source；
等待中正常終局、SOS關閉或原選target退場，會在member supplier／SQL前取消準備
恢復WORLD，不能把這些合法競態當錯誤踢線。
不是空成功或把準備當入場。終局89後不建需要新0B的edge，只保真正Written與
各人C1C返回，不讓仍存活的viewer卡終局。

這是明示 CUSTOM serialized progress gate。舊C35/0B沒有 turn／group nonce，
因此不能證明真實 renderer動畫已完成，也不能防止有權連線者提前／延遲回報。
退場cleanup不能等已關閉socket輸入；它保存並撤銷exact claims，重新捕捉仍在場
viewers的新edge且丟棄舊觀測。新舊原生回報的真正動畫歸屬仍須實機驗收。
沒有用timer、timeout或Written虛構動畫成功。

退出戰場用HP0 tombstone不等於存檔死亡；退出者收到boundary88時，自己的位置
仍投影真正保存HP／MP以保HUD，其他viewer看到撤除位置0。各人C1C返回保持
既有exact original occurrence與多frame全Written，再個別釋claim、Session更新。

ReturnContinuation為repo私有mint token：唯一newlyReturned transaction完整提交後
才可取得，包含原actual admission完整active44與最後保存資料。讀值不授權新INIT。
消費時要求同actual issuer／完整saved rawsource與row／Returned mirror／原return
ledger／全部Return Written／claim absence，最後完整readset的total_changes與pure
Session fence再核；postCOMMIT source失效保durable事實，不能宣稱rollback。
COMMIT進入後若拋例外，private ticket保uncertain並使core進recovery，禁止舊模型
繼續遊玩；precommit CAS拒絕仍是完整transaction rollback，不混稱durable成功。
後續pet／learning由另外的實際Session continuation owner接入，不靠public struct假授權。

## 回歸 source 與尚待驗收

`test_owned_pve_room_0161.cpp` 增加空pair、寵物不同HP換排、換後傷害保存到
真正角色、原B4／rawpet／RNG保留、pending不可被Written清掉、重複換排revision、
晚成員CAS失敗全房不部分保存、真正return token來源等 source cases。
`test_owned_battle_formation.cpp` 增加action9完整opaque／zero masks／flat result
與nonboolean成功值、83/9→88後才剩餘grant、fixedcounter／label254與255拒絕。
這些測試本輪一律未執行。

原服隊形pair／server費用與授grant規則、原生button完整可操作條件、真實多Session
動畫／0B時序、空pair renderer、戰後HUD／pet／learning聯合流程仍需集中後續
build／tests與原版台服client驗收；不得以source完整接線冒稱原服規則已還原或已實測。
