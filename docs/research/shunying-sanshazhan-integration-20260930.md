# 瞬影三煞斬：實裝進度與接入界線

設計編號 CUSTOM-0058。使用者授權新增技能；以下保留各階段實測與失敗紀錄。

## 最新正式部署狀態（優先於下方歷史紀錄）

2026-09-30 使用者接受目前修正並授權更新正式服。正式服務端及客戶端已部署，
126 登記 active，122～125 保留。程序重啟、檔案雜湊、資料庫既有角色資料與
正式 launcher `/verify-client` 均核對通過，測試 F1／高屬性未帶入。
取得技能流程與正式多怪遭遇不在本次部署範圍；驗證證據、已知界線與備份見
[正式部署紀錄](shunying-production-release-20260930.md)。

## 最新隔離測試狀態（2026-09-30，優先於下方歷史紀錄）

本次最新：使用者確認「目前都正常」。8D1EC1C4版背景恢復修正及SKB6897=SpcA126名稱對照已實機部署；工具畫面確認「瞬影三煞斬 MP:20」與地圖正常，log確認surface recovery後補回背景。使用者接受此次修復；不將此誤記為所有BB案例或正式服推广已完成。技能視覺沿用先前接受版本。

使用者於本次後續明確確認「OK 特效技能完成」。B368775B版技能視覺定案，凍結分身/刀3外觀與時序。新開問題僅為切換視窗戰場背景變黑，以及F1提示/技能名稱亂碼；不得為此重做已接受特效。視覺接受不等於全部BB案例已執行。

20:42補充：卡住根因確認為 manual fixture 的普通攻擊僅回83/86，未送88；原生客戶端等待88，而server等待0B，雙方互等。Application通用編碼器僅在diagnostic_shunying_manual啟用時改用basic helper，回原生83/86/88；126既有路線不變。兩項C++測試與frozen gate通過。20:39部署server SHA256 62334836725B4B18F8F2EDA41D56D4EA6AACACC4BDD376CE196242677E5F64B7，PID19064，client24280。新log stdout-basic88-fixed.log：20:41:51.559收到type7普通攻擊，回156bytes；20:41:53.226收到原生完成0B並重開輸入。舊版相同路線只有35bytes後永久等待。實機畫面已見多次技能後回合選單恢復。F1實讀綁定(2,0,126)且技能啟用；卡住時ready禁止快捷，不能由卡住後狀態推論最初為何送成普通攻擊。

新版DLL B368775B78381520752DF8B9FC6F7D45652A2B889B1B178C6E6FE79C43266E51追蹤41C360/41B9C0/41B330發出的獨立ACT。ROM9006根20510/20/30在opcode10發出50510/20/30寬藍光及60001/2/3紅光，並不屬於+27A子樹。405項visual mock、27項hook、21項ABI檢查通過；實機log已記錄emitted=6/displays=9。完整分身刀光仍需清楚連續實機畫面驗收，不以log宣稱成功。

20:18再次實機失敗：B6F80272版已補RTG完整子樹與426AB0繪圖前同步，285項mock通過；但用戶及工具畫面均顯示分身缺完整寬藍刀弧。log為tracks=6、roots=3、ACTs=3、displays最大3，須继续確認寬刀光來源，不能把子樹修補認定解決。

20:05版本在實機已出現分身刀光，但使用者截圖再次拒絕：分身僅有零碎暗紫刀弧，本體才有完整藍色刀光。248項mock測試僅涵蓋RTG軌道ACT的主Display，未覆蓋原生ACT的附屬圖層，因此不能證明完整特效。
原生0041B330／0041B560／0041B740／0041C060顯示，ACT除+0E主Display，另有+AC（數量+254）的Display，以及+256的17個子ACT、+27A的6個自動子ACT。正在補齊唯讀視覺遍歷與重複／循環保護；技能仍未通過實機驗收。

19:53隔離實機已正常進中央slot2戰鬥，女性神仙可見，至少3回合指令/回條
成功。修復19:48進場斷線：原生518E50的0B/2未寫logical4及13..16，
manual fixture不再將堆疊殘值要求為零；actor/side/context/mask/state照舊
驗證。原生VM8案及256種逾時殘值回歸通過。只修改manual政策。
但使用者仍回報「分身沒有刀3特效」，故整招未驗收通過：人物圖層複製
不涵蓋原生RTG斬擊軌道，正在接入分身目標的原色同步斬擊。

19:31使用者實機再次拒絕：刀3斬擊未出現。原生日誌指出 war.cpp:3423
`rtgPlaySpc->rtgRomIdx>=0 && rtgPlaySpc->rtgDataIdx>=0` 失敗。
查明00516AE0先以126載入效果，但0052C520才映射8，造成載入索引與播放
索引不一致；正在同時修正preload及result的限定映射。此失敗證明144項
分身mock與資源檔案存在不能替代完整播放路徑驗證，不能標記驗收通過。
19:20版本已接入透明分身、召喚/返程粒子、輪廓光及女性神仙83召出；
實機已見女性神仙，但整體技能仍未完成。使用者另要求測試人物移至中央。

實機後使用者拒絕第一版分身呈現：與核准網頁預覽不同，女性神仙也未在戰鬥出現。第一版僅拷貝施法者圖層，缺少 `app.js::cloneActors/cloneBurst/returnStream` 的0.42透明度、0.15飽和/0.72明度、召喚粒子、瞬移和弧形縮小回收；不得視為交付完成。已確認女性神仙持有/選中/world36不等於戰鬥附件召出。

18:56實機另外發現，等待輸入逾時產生native action2/self mask後，manual政策拒絕並斷線。新增僅此非持久化、無反擊fixture的嚴格action2輸入重開分支；驗證本人、側別、context、自身mask及latches，保持全部HP/MP/revision不變。三次逾時後正常技能仍可由單元測試提交；實機重測待新版部署。

- 真正客戶端已接受 mode16 的三個目標指令，顯示14名敵人並對三名敵人結算；當時沒有分身。因此不能把先前實測算作完整技能驗收。
- 新增 `tools/skills/native_clone` Win32 DLL 與限定檔案雜湊的獨立啟動檔安裝器。接收126結果、保留原生8動作與命中事件，額外目標使用當次施法者的顯示圖層。60項模擬渲染測試、原生ABI與啟動入口靜態驗證通過；新DLL尚待實機檢查，不代表黑箱通過。
- 使用者指定暫定物理三倍：隔離政策為 `magical=false, power_percent=300`，沿用 CUSTOM-0006 計算順序。這是攻擊係數300%，不是已恢復的原生刀3公式，也不等同扣防後傷害必定是原值三倍。
- 重複、友方、死亡或超額目標在隔離手動測試中會拒絕整次操作並重新開放輸入，保持HP/MP及戰鬥狀態不變，避免普通重複點選造成斷線。
- 只對隔離資料庫 character_id6 / account6 / `test` 設置等級50、四屬性666、HP/MP9999，先備份並檢查其他角色不變。風晶裝備與女性轉生神仙的原生投影正在接入；未完成實機驗收。
- 正式服務端、正式角色資料與現役客戶端未部署這些測試設定。技能編號126的資料庫登記保留，122～125仍預留。

使用者後續指定：實裝後須檢查程式、修復並反覆驗證，且必須以真正客戶端模擬玩家做黑箱測試。交付驗收採用 [玩家黑箱驗收案例](shunying-player-blackbox-acceptance.md)。目前黑箱狀態為實機失敗、修復中；不可將既有單元測試或原生指令oracle的通過當作玩家驗收。

## 本次已完成

- 依使用者指定，在第0類原生最後編號121之後保留122～125，新技能 identity 為 kind0/id126；原生刀3為 kind0/id8，原技能不覆蓋。候選新招式使用reach7涵蓋敵陣，這是CUSTOM選敵設計，未冒稱原生刀3範圍。
- `tools/skills/build_shunying_client.py` 產生獨立候選 cbspec2、原生 Ski01 圖標ROM及 SpgEft 路由。圖標來源是使用者提供的紅底發光刀圖，轉為40×40原生ABGR4444，不另畫替代品。
- `ShunyingSanshazhan::authorize` 把自選最多3人限制與獨立結果編碼callback接入 `RecoveredBattleService`。呼叫方必須已授權技能，並供給正式驗證的刀3傷害／消耗政策；此函式不授予角色技能、不杜撰公式。
- 原有Battle交易負責拒絕友方、死亡、不存在、重複目標；多目標整次只扣一次MP。超過3人由技能政策拒絕。
- 本體＋分身的分配由實際有效結果建立：1人無分身、2人1分身、3人2分身。每個分身均引用當次caster，不能把預览人物烘焙為固定角色圖。
- 每技能結果編碼callback只作用於該施法，後续反擊使用原callback。callback出錯時HP/MP及revision不提交。

## 已驗證的範圍

`shunying_sanshazhan` CTest涵蓋兩陣營、1/2/3目標、4人拒絕、重複／友方／空位／死亡拒絕、剩1/2名敵人、單次消耗、視覺分配及編碼失敗回滾。
傷害10、消耗4只存在於測試fixture，未成為正式平衡設定。
既有 `recovered_battle_service` 回歸通過；凍結聊天檢查通過。原生指令產生器另已驗證新ID雙側各1/2/3個目標的封包；此驗證人工供給選取列表，不能證明UI提前確認已正常。reach7另經14位置×5敵方分布共70項原生helper檢查，結果涵蓋全部有人的敵方位置。證據在artifacts/custom-skills/shunying/target-command-native.json。

## 尚未完成，不能宣稱已實裝

1. 目前Application的戰鬥binding仍是診斷路徑；正式設定啟用 `native_monster_placements_only`，沒有把一般encounter接到此技能政策。不可為新增技能解除既有保護並偽稱正式戰鬥完成。
2. 已有持久化 `character_deities.skills`，但需接到施放白名單。新client版本的圖標能力也需與 `RecoveredDeityState::has_current_skill_icon` 配套；目前保持原版白名單，沒有偷塞新ID到角色存檔。
3. 新ID的客戶端動作選路、手選少於3人後確認、動態分身生成／回收及敵方方向尚需native runtime接入和實機測試。
4. 使用者新增要求：**每名目標的傷害浮字節奏必須與原生刀3相同**。原生83/03結果包沒有時間欄位；應透過原生刀3命中事件呈現傷害。不得猜測RTB特效起點是傷害幀，不得用服務端sleep或另設開頭／結尾浮字冒充同步。
5. 已另外找到 `C:/Users/risei/Desktop/God2-解殼EXE原始碼重建`。其README與CMake確認目前可編譯的只有teleport、packet-queue、teleport-ui等模組，未有戰鬥renderer模組；decompiled為偽碼，不是完整可編譯遊戲。下一步原生追蹤入口包含decompiled/functions/0052c520_FUN_0052c520.c（技能結果消費）、0052c000_FUN_0052c000.c（target outcome）、0051ee90_FUN_0051ee90.c（選敵設定）。因此不再以找不到這份重建目錄當作缺口，缺口是戰鬥分身／命中播放接點尚未重建。
6. 原生刀3傷害公式尚未恢復；客戶端record+42僅是MP顯示／資格門檻。現有Lua公式CUSTOM-0006不是原生刀3公式，不直接指定為新技能的正式平衡。

## 接入示意

```cpp
// 在已有真實角色技能授權及合格client版本判定之後：
ShunyingSanshazhan::authorize(policy, qualified_blade3_action,
    [&](const BattleSnapshot& state, const BattleActionResult& result) {
        const auto assignments=ShunyingSanshazhan::visual_assignments(result);
        // 接入已驗證native client adapter，綁定當次caster外觀，
        // 保留刀3原生命中與浮字節點；不可用此處的註解代替實作。
        return client_adapter.encode_shunying(state,result,assignments);
    });
```

以上adapter尚未存在，示意不能當成可上線程式。正式服程式及現役客戶端Data未覆寫。資料庫新增獨立custom_skill_registry登記（見下節），沒有替換原生技能或授予正式角色。候選圖檔存放在 `artifacts/custom-skills/shunying/client-candidate`；可以交接檢查，不能直接發布為完成版。

## 編號登記與隔離手動測試（2026-09-30）

`tools/skills/register_shunying_skill.py` 已在現用服務端資料庫 `artifacts/playtests/persistent-launch-20260923-01/town-diagnostic-accounts.db` 完成登記：kind0/id122～125為未命名reserved，kind0/id126為瞬影三煞斬、pending_client_integration、base0/8、最多3目標。先以SQLite backup備份，再以交易登記並讀回；448筆原生catalog各欄位維持相同，quick_check與foreign_key_check通過。備份在 `artifacts/custom-skills/shunying/db-backups`。此狀態不代表正式角色可以施放。

`private-shunying-manual-20260930-01` 是獨立客戶端與DB副本，loopback測試服port2598；F1預設kind0/id126、僅使用者新建角色test（character_id=6），暫時性快捷鍵與session技能授予，不保存至角色技能資料庫。default-off旗標diagnostic_shunying_manual限制具名隔離DB且不保存戰鬥資源。測試場景有14名敵人（slots14..27），每隻HP10000；零MP與傷害是測試政策，不是正式平衡。測試結果暫用原生刀3 id8播放，動態分身未接入。

編譯完成；shunying_sanshazhan、recovered_battle_service、config三項CTest通過，凍結聊天檢查通過。登記工具四項tempdb測試通過（含舊123精確移轉及衝突回滾）。前一版123已在真正客戶端顯示14名敵人及指定圖標，但收到0x35指令後因結構不符斷線，不能宣稱黑箱通過。此次編號同步126，測試服已停止，待實機重測後交付。使用者正式帳號、現役客戶端與正式服未修改。

重跑：`python -B -m tools.skills.build_shunying_client`；
`cmake --build build --config Release --target shunying-sanshazhan recovered-battle-service`；
`ctest --test-dir build -C Release -R "^(shunying_sanshazhan|recovered_battle_service)$" --output-on-failure`。

實機拒包根因：先前target_mode=3產生單包多bit目標，與已恢復每敵一包的語法不符。候選已改原生mode16；原始11EAD0 setup輸出(3,0)實際串入118E50 builder，兩側1/2/3目標六項通過，另驗證舊mode3會重現parser拒絕。此為原生程式驗證，不取代UI重測。
