# 台服效果kind上下文與完整回合計數（round466）

本輪修正實際Application的88計數器截斷，並補齊牛轉仙界踏的原生HP投影
檢查；續追kind2／3後確認它們不能套用現有kind1的單筆效果模型。未新增
原服傷害、治療、減傷或五行公式，也未放寬技能權限／啟用新玩法。

## 現用來源與證據

現用TW EXE SHA256：
`aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48`。
453筆BIN仍為`3adcda70a477086da50411fe5d023eec33f915efafd17ec478d55542cae42ea7`。
完整靜態證據外存於
`C:/Users/risei/.codex/artifact-archives/god2-server/20261019/effect-kind-source-round466/`。
重用已保留的REA／原始CFG並重新核對現用PE bytes，沒有重跑相同REA函數。
失敗helper保留原件，修正版另命名、先語法／AST檢查再單次執行。

## 83/action03的kind2／3不能混同

`scalar/scalar-kind23-conclusion-v2.json`重核3128條原始指令、529020的kind
及state13h分派表，並綁定既有REA：
`ev_63a6081b83c7430c9a82b865dc20081a7120ba872c39154c98fad215fbf4344d`、
`ev_a152758bd1284528c0b1307da26fb61452ae363900844fd4b7bb43ff27213e8e`。

| 原生定義類別 | consumer | 額外限制 |
|---|---|---|
| kind2 ID69..71 | 526890 | 516C4E先把mask目標改成施術者 |
| kind2其餘非零BYTE ID | 5251A0 | 同樣改成施術者，不能當敵方scalar hit |
| kind3 ID105..108 | 524820 | 正常命中讀signed量套用HP |
| kind3其餘非零BYTE ID | 526890 | 在R13=0、R14=0／28語法下仍需絕對HP |

kind3沒有上述kind2接收改向；526890政策仍受raw outcome映射限制，不涵蓋
R14=34的77h加量或R14=27的59h復活。表格只證明consumer分類，沒有恢復
學習／控制／費用／權限／生成公式。現有owned projection只服務kind0／1的
對側單目標結果，故本輪不藉放寬parser宣稱接通kind2／3；程式註解保留界線。

## 83/action0D還依賴前一個主要動作

action0D的WORD11 accumulator kind與action03的definition kind是不同欄位。
52C520的kind2／3尾段52CC01以MOVSX讀raw WORD9，52CC05寫到
`source+B58+8*source239`，即`B60[source239-1]`，不看selector。
outcome也落在`5E8[source239-1]`。這與本筆以source2C4配置的entry index
可能不同，因此連selector7／8／9也不能只按Record.accumulate推定HP不變。

52B870將kind2的destination改為source；kind3仍取packed target，但會NEG
B60的HP量並寫回，MP的B64不翻號。另一consumer52BC50沒有這個kind3 NEG。
兩者都對selector20跳過一般HP／MP套用，且仍有actor／播放／死亡狀態門檻。
不能將kind3固定翻號、將selector9當成必然只有MP，或以單筆mask代替全部
前置action target count、indexed storage、播放owner與重置世代。

因此Battle仍在整批更新／encoder之前拒絕kind!=1；新增註解明確說明缺少的
上下文。這不是永遠不支援：下一步須建立實際主要action→239／2C4→receive
storage→選定consumer的連續owner證據，再將其加入同一原子結算契約。
中毒maxHP/10的精確商餘數保留，未收到取整答案，不自行選floor／ceil或tick。

## 實際可達的88計數器修正

518A90讀logical DWORD1；它不是BYTE回合計數，也不單靠此欄位賦予原生
turn／ack權限。原Application的結算與下一回合兩處只填bulk[1]，把高三bytes
留0。manual模式不受configured rounds上限，31攻對13防的既有自訂basic扣18，
10000HP敵人在255次後仍有5410HP，因此256→0的截斷在現有來源流程可達。
來源證據見`scope/transport-width-source-audit-v1.json`。

RecoveredBattleVitalsBatch新增counter_bits與by-value with_counter，寫完整
little-endian DWORD；拒絕錯opcode與超出DWORD的值，保留其餘actor／opaque
bytes。Application兩處先以uint64計算舊有revival／resume offset，再共用
writer；減法不足拒絕，既有unsigned round map的下一值也在wire／rearm前檢查，
避免整數環繞。沒有變更原有offset語意、發送順序、權限或持久化。
`scope/bulk-counter-implementation-v1.json`保留三份實作及既有native證據pins。

既有C++回歸來源新增255／256、65535／65536、DWORD上界、越界、wrong opcode、
全部14組HP／MP與opaque bytes不變，以及caller input不變；stdin／stdout
probe格式保持。沒有新增或執行Python測試，也未執行這些C++來源。

## 牛轉仙界踏與64位元HP

ThousandBullsReply原本只檢查signed16的實際hit loss。對側actor不在friendly88
中，且存活cast可以省略88，故target current／max HP的native DWORD檢查會遺漏。
現在比照Shunying，在每個target產生83前檢查完整HP值；沒有重加提前HP86，
沒有改自訂倍率、四段顯示或單次MP扣除。

目前Application的這些Battle仍是LegacyCustom，HP上限受既有該profile限制；
不能說現行主流程已使用寬HP。這項修正補齊共用encoder可被ExtendedHealth64
呼叫時的契約。回歸來源經真正Battle::act組合，檢查partial／final兩路遇寬HP時
整份checkpoint（包含MP／revision／RNG）不發布，DWORD位元上界仍可投影。
width檢查不是原生signed cap算術或完整64位元客戶端資格的證明。

## 驗證範圍與剩餘工作

獨立靜態複核、唯一正式靜態盤點、source／storage／publication收據均外存。
格式分類仍沿用v29，完整玩法新增0，全遊戲分母及完成率仍null，goal active。
命中／閃避／暴擊、傷害／治療producer、攻防減傷、五行相剋／抗性、真正持續
狀態owner與tick、MySQL8後端及全部台服來源路徑仍未完成。
PHASE1未建置、測試、執行target／VM／codec、遊戲DB SQL、遷移、啟用或部署。
