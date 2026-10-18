# 台服中毒精確比例與真正tick缺口（round462）

本輪將使用者指定「當前最大HP的十分之一」接成C++／Lua的精確、唯讀計算，
而非繼續從顯示倒數猜扣血。Battle直接取current snapshot的target maxHP，
Lua5.4保留商與十分位餘數，C++驗證完整比例。登記為CUSTOM-0157：這是
使用者規則，不是REA恢復的原服中毒公式，也尚未接成實際扣血／持續技能。

## 來源、方法與現況

目前TW EXE為`aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48`，
453筆BIN仍為`3adcda70a477086da50411fe5d023eec33f915efafd17ec478d55542cae42ea7`。
完整外部證據根目錄：
`C:/Users/risei/.codex/artifact-archives/god2-server/20261019/poison-owner-rule-round462/`。
新helper先AST／語法檢查後單次執行；沒有新增專案Python。
REA仍使用既有公開launcher／Ghidra，原始13個sections不變、94個analyst seed
不作原始caller，分析映像未執行。所有session已close且terminal exit0。

## 現有核心沒有真正的中毒tick owner

逐份來源稽核見`scope/poison-source-scope-v1.json`。目前：

- BattleActor／Snapshot及checkpoint v1／v2沒有status instance、tick identity、
  剩餘次數、next_due、expiry、清除或疊加資料。
- OwnedPkRound是CUSTOM-0086兩人輸入／回執收齊政策，diagnostic rearm只是
  重開輸入；Application排程或C9顯示時間不能直接當原生中毒tick。
- RecoveredBattleService的staged→encode→checkpoint callback→publish骨架
  可參考，但callback可未配置；不能由有接口就宣稱一定持久化。
- 真正paired PK settlement會先存checkpoint／round／outbox再publish，但限定
  LegacyCustom／v1、兩人及最多兩個revision增量，並凍結HP／MP以外actor欄位。
  不能悄悄加poison revision或status再聲稱符合既有交易契約。

本輪沒有改動這些存檔版本、repository約束、schema、Application scheduler、
玩家資料、C35 grant或原生封包。真正status取得、tick時機、清除／到期／疊加、
持久化及完整native回覆仍須實際來源與共同交易。

## 精確十分之一，不替取整政策做決定

shared64 HP是整數`[0,INT64_MAX]`表示域，沒有小數定點HP。使用者已指定分母10，
但目前來源沒有證明餘數時原服floor／ceil或跨tick累積方式；取整問題已另詢問。
在尚無答案時保留精確結果：

```text
maximum = actual current target max_hp
whole_hp = maximum // 10
remainder_tenths = maximum % 10
exact share = whole_hp + remainder_tenths / 10
```

例如123的精確結果是12又3/10，不能將商12直接稱為已決定的整數扣血量。
正數不足10時也沒有minimum1；不丟餘數、不進位、不自行跨tick累積。
`PoisonShareResult::exact_integer_hp`在有餘數時回nullopt，整除時才提供整數。
這不是擴充存檔HP成小數或改動既有HP表示域。

## C++／Lua來源與驗證

新增`PoisonRule.h`及`gameplay/poison.lua`。Lua使用5.4 integer的`//`與`%`，
不經double。`LuaEngine::poison_share`使用既有protected invocation／指令預算，
在轉lua_Integer之前拒絕超出shared64表示域的入值；檢查module、callback、
單一table結果與兩個精確非負整數，再驗證：

```text
0 <= whole_hp <= maximum / 10
0 <= remainder_tenths < 10
whole_hp * 10 + remainder_tenths == maximum
```

乘法前先限制商，乘積不超過INT64_MAX；再加最多9在uint64中仍安全。
這是精確結果驗證，不是新玩法HP／傷害上限。Lua錯誤、預算耗盡、float、
錯誤形狀或更動比例會throw；不能用既有combat_health64的自訂floor順序替
中毒決定餘數政策。

`Battle::poison_share`先確認active／current revision／存在且存活target，
從該snapshot取得max_hp，再呼純rule並重查revision／target／maxHP。
它不使用cast-time maximum、current remaining HP或來自封包的任意數字。
callback必須純且不可重入：post-check不是通用reentry blocker或rollback，
不會回復惡意callback經外部alias造成的副作用。

此操作本身不改HP、MP、RNG、revision、checkpoint或outbox。沒有gameplay
caller、tick觸發器、grant或packet producer，沒有啟用中毒功能。新Lua模組也
未由bootstrap掛上排程；未執行Lua或C++。
六份來源的獨立靜態複核為`scope/poison-six-file-static-review-v1.json`，
PASS只適用上述唯讀比例能力與callback契約，不是編譯／回歸／遊戲驗收。

## REA繼續追action04／07／09，沒有把收到量當公式

原先已知的52C520→+286 receive stores不重計為新公式。本輪新增後續真正
scheduler callee的閉合：

| wire action | internal播放state／callee | 新限定結果 |
|---|---|---|
| 04 | 14h／5291D3→528140 | 五階段renderer流程，328指令 |
| 07 | 89h／5291C9→5273C0 | 六階段播放／packed selector，660指令 |
| 09 | 97h／5291A1→525B90 | 兩個side／slot的六層actor pointer交換，337指令 |

internal state不同於wire opcode。兩個原始switch展開後無剩餘CFG stop；
含receive片段的1424條指令逐bytes對回目前EXE。REA三函數Evidence：
`ev_4835aa14e9f6cdd67b5502f052fc984fc386e938d1f5ce1c50e67d163d526432`。
warnings原樣保留，以原始指令及限定來源為準。

07的52799A讀收到的+286，5279B0取低10bits再更新+DB4，不能統稱HP量。
09將+25A／+268各除14／取餘數，交換兩位置六層pointer並更新actor+234；
此處+286只判非零成功，不是傷害或毒量。精確+552掃描無候選、+5E8候選
包含stack及既有播放／reset；這不是全域沒有毒狀態或bulk／computed alias的證明。
`native/dot-native-conclusion-v1.json`保留完整關聯與來源限制。

## 剩餘工作與唯一盤點

本輪只增加owner quantity與current-snapshot觀察能力；沒有增加已完成玩法、
parser opcode或部署。分母與完成率仍null，goal保持active。
source ledger／唯一正式靜態報告及storage receipts外存，原生格式分類沿用v29。
需接真正status取得／tick boundary／expiry／清除／stack／存檔與outbox owner，
並確認餘數政策及完整回覆，才能算可用中毒。shared64亦須checked native投影，
不能截斷或虛構擴寬封包。所有其他命中／暴擊／傷害／治療／減傷／五行公式仍
維持各自未閉合來源，不藉本使用者規則冒稱恢復。
未建置、測試、target／VM／codec執行、遊戲DB SQL、遷移、啟用或部署。
