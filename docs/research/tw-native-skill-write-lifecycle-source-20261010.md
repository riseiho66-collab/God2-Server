# 台服技能清單實際寫出生命週期，第245輪

本輪修改 Session 與 SharedTaiwanIssuedSkillSource 的4個既有C++檔。
具體接上來源 registry → 戰鬥 held Write → 真 async_write 成功 → game
來源核對 → 新ticket。沒有把入隊當成寫出，也沒有把寫出當client處理ACK。
實際一般native issuer、完整battle authority與普通Main仍未安裝；完整
雙向玩法新增0、opcode新增0，台服全遊戲分母／百分比仍未知。

## 實際發送與取消

Session新增獨立 NativeBattleSkillDelivery，保存完整 logical aggregate、
真session/account/character/common generation/battle generation及來源本地
sequence。sequence不是native nonce或turn grant。新方法只接受actual
ASYNC common-ready game owner；讀game欄位前檢查已確立的owner thread，
不以任意first caller認領thread，也不放寬舊world sender。

單Session只能有一個private pending marker，保留同一common identity
實例、immutable delivery及weak lifecycle source。新生命週期介面只用於
transport前後通知，由具體registry實作，不提供玩法權限或預設成功。
網路Write／closure只保存資料與weak source；來源只在game lock及析構。

完整87／38／86-5 native record邊界資格化後，預留既有queue budget，
建立精確buffer的held Write；game-before核對通過才解除hold。只有同一
Write的真socket成功回呼能設定written getter。game complete須再核對
實際written pointer、common identity、phase與battle generation。最後
strand在退marker前再次核對同一identity／phase／generation。

close／fail／timeout經同一once completion取消；finish等待marker退役，
不把尚未排空的game source丟在network析構。既有executor必須持續接收並
排空handoff；executor停機或post分派本身失敗的全面shutdown處理仍待
正式host與集中驗證，不能宣稱任何環境都保證callback執行。

## 真實registry連接

`publish_updates`接收真issuer提供的完整有序87／38／direct86-5 aggregate
與private previous Ticket。先擁有所有bytes、逐筆以本輪以前的具體model
投影，再完整資格化before／next main及aux catalog、真Session/common
lease／位置／battle generation。只有資格化完才建立private pending。
本地revision在stage時保留，其他Session可前進；完成時不回退全局sequence。

pending時，select／current／replace／apply／install均拒絕，還共同檢查
Session transport marker，涵蓋source commit後、transport marker退役前的
窗口。release取消該Session的確切pending並close。發送前與寫出後必須
核對同一private delivery、before slot與完整before／next來源；失敗只刪
對應舊slot並close，不刪新incarnation、不恢復臆測的client舊狀態。
已寫出bytes無法撤回，也沒有重試已消耗的durable玩法前綴。

公開Publication是private observation handle，沒有任意user completion
callback。`observe_publication`只在transport marker已退役、結果ticket仍
當前且完整catalog／ready scope仍吻合時交付current_ticket，避免在舊
transport slot尚佔用時inline接下一次發送。Written是歷史上的本地寫出
及來源post-current觀察；之後關閉或換代會令current_ticket缺席，不能用
歷史status代替當前權限。

## 輸入與原生權威界線

新發布開始前若已有world_input、不完整外框、world_pending_records、
83 deadline或native_skill_generation，會保守拒絕並close；partial tick
也可能被拒，這是目前opt-in來源子集限制。舊prefix grammar未改。
pending時read／resume／feed／game dispatch皆設barrier；已在途read可
暫存bytes，完成後才解析。與發布競爭、已排入game的舊batch保守拒絕，
不把它下傳handler。此機制沒有改寫既有game_busy。

尚未接收及發布期間inflight bytes屬於哪個native grant無法僅由transport
推知。既有buffer guard不是完整跨grant隔離、semantic replay權威或
native nonce；實際WorldOwner仍須提供actor／turn incarnation／once
settlement。86-5仍只投影direct control／actor，不恢復完整UI／rearm／
clock／本地cleanup；已學技能、bit15、可見清單與寫出都不能當授權。

## 接續工作與紀錄

實際初始清單／有序87／38／86 issuer、actor對saved deity的所有權、
native MP charge／refund／rules、once durable settlement、完整reply、
secondary清單及普通Main仍OPEN。現有factory可以建立同Context具體
registry，但不是實際issuer已存在。不得以CUSTOM診斷發送冒充一般native。

本輪未build、test、compiler、runtime、native、codec、遊戲DB／SQL、
migration或部署。外部完整before／候選／終版來源與靜態差異紀錄位於
`C:/Users/risei/.codex/artifact-archives/god2-server/20261010/tw-native-skill-write-lifecycle-source-245`。
保留舊封存及接受證據；目標active，接續台服優先。
