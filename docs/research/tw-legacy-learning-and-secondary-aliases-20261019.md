# 舊流程學習來源與技能欄位續追（round475）

本輪修正舊世界流程在真實技能書提交後的完整來源延續，並補查兩組
尚未閉合的原生欄位邊界。全部仍是 PHASE1 原始碼／靜態作業；沒有
建置、執行測試、執行遊戲、SQL、遷移、啟用或部署。原始戰鬥公式
及全遊戲完成率仍未證明，百分比維持 unknown/null。

## 舊世界流程的實際修正

上一輪 `advance_companion_successors` 把 CommonWorld 與 `InWorld`
同時當成所有完整資料延續的前置條件。但 legacy world-ready 只綁定
movement，合法角色仍可在 `CharacterSelected`；既有學習服務也允許
沒有 common presence 的這條真實流程。

現在正常學習延續使用原本的 private WrittenLearningSource、完整保存
狀態、normal INIT、同一 Session、完整 account/character、battle generation
與實際記錄的 phase。phase 必須完全相等，且只接受原本合法的
`CharacterSelected`／`InWorld`。CommonWorld 只在 PK 成對來源分支要求；
PK 的實際 presence、原始 attempt、private ancestry 與 `InWorld` 資格
沒有放寬，也沒有從 legacy 捏造 lease。

另移除 `CanonicalCompanionSource` 未被讀取的整串 `previous` 強引用。
當前 `latest_learning`、學習 Entry／publication 的原始 anchor、private
PK observations 自己的必要 predecessor 仍保留。選神 draft 的
`PendingCompanionSelection.previous` 也保留，用來核對同一次實際來源。
此修正讓正常流程可釋放不再需要的 root 節點；沒有截短原始 logical
history、刪除 PK ancestry 或重新啟用失效 token。

## 完整保存狀態的測試來源

新增 fixture 經實際 repository issuer／restore 取得 private Restoration
與兩筆真選神提交，覆蓋 16 列、非空 inventory／alias、完整 1215-byte
equipment，以及 activation header／event／link。測試來源檢查只有選取
狀態改變、原始 S30/S34/S35 history 不變，並只追加兩筆真正的 S31。

五種 after-state 變更各用獨立 fixture：背包、裝備、header、event、
未選取列。每個案例先建立符合 Current 的正向來源，再只變動一項，
避免後續拒絕只是先前污染的結果。另涵蓋錯誤 private issuer、錯誤
順序、重複／空提交及舊 before source 不會重新 Current。

這些都是尚未執行的測試原始碼。activation 使用明示
`CUSTOM_TEST_NOT_NATIVE` 的合成保存材料，沒有冒充真正學習提交。
目前仍未覆蓋完整 learning commit→selection→learning、完整 PK 資料圖
或 Application／Session transport 的整合執行。

## REA 的新增界線

現用 EXE 與 453 筆 BIN 身分維持上一輪。本輪新增兩個 REA 靜態
session、六個函數分析，session 均已關閉。分析映像的 13 個原始 PE
sections 逐位元組符合現用 EXE，沒有執行目標。

- `51C4F0` 對 3 個 secondary bank 各 10 個 WORD 做 `AND 7FFF`，
  清除最高位元；它沒有寫入 header `+2D12/+2D13`。`51C4B0` 則清除
  primary bank 的 WORD bit15 與 auxiliary 資料。兩者都不是完整
  secondary header 清零的證明。
- 已追到實際動態配置鏈 `464910→55B406→5109D0→51B7B0`。已核對的
  allocation wrapper 不能提供整個物件原本為零的證明；更深的 provider
  與 whole-object alias 仍待追。兩個未知位元組不能改填零，也不能
  直接判為永遠沒有用途的 padding。
- 新追的 `523FF0` 是 selected definition `+45` 所驅動的結果播放目標
  展開；它與 C35 的輸入目標 grammar 是不同 consumer。不能把播放
  target count 套回輸入 mask，更不能當成傷害係數。
- `520300` 的 bulk clear 位於 actor `+DF8..+EC3`，另清除 `+EC4`；
  這個精確範圍沒有直接寫入 amount bank `+28A`。這是有限候選排除，
  不是所有 computed/bulk aliases 都沒有量值公式的全域證明。

本輪沒有新找到原始傷害、治療、命中、閃避、暴擊、攻防、五行或抗性
的完整產生公式，也沒有新增持續效果 tick owner、issued87 或施法權限。

## Legacy C67 的下一個實際接點

已核對 legacy guild ordered adapters 會把 C67 的 S31 放在 prefix
side-send；中間還可能有自己的 guild output 或對自己的 fanout。
所以最終 return 並不一定包含全部原始回覆，不能把目前 Shared 的
單筆 whole-Written token 直接套過去。

若採單筆完整回覆，下一步必須在真實 world callback 收集全部 self
output，保留呼叫順序與原有 observed batch custody，再抽離共同的
selection registry；其他 peer 的 fanout 仍需保留。另一條路是定義
實際多筆寫出的 composite receipt。兩種都需要真正接到 sender，
不能用假 lease、bytes 比對或一個放寬條件宣稱已完成。本輪未實作這條
C67 transport 接合，仍保留既有行為並明列缺口。

可機讀摘要與證據雜湊見同名 JSON；完整證據保存於專案外
`combat-field-alias-round475`，不成為執行依賴。
