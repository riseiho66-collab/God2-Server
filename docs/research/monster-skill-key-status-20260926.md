# 怪物攻防、技能公式與金鑰：本輪核對

## 已確認與尚未找到

| 項目 | 結果 |
|---|---|
| 本機封包金鑰 | 已有零種子握手對應的256-byte展開表，服務端正使用；並非所有種子或資源檔的通用金鑰。 |
| csvZ、gamedata | 0516封裝的LZSS壓縮，載入流程不需要秘密金鑰。 |
| cbspec2.bin | 版本1.03、原生直接讀取的明文固定格式；448筆技能選擇定義已能解析。 |
| 怪物物攻、法攻、物防、法防 | 尚無可對應到原始野怪身分的四項數值。不能拿寵物、變身卡、ROM或特效參數代填。 |
| 技能傷害、命中、暴擊、五行、實際扣魔公式 | 尚無可確認的原始服務端公式。已確認的是部分技能欄位、耗魔顯示／可選判斷，以及收到結果後的套用流程。 |

現有技能來源重新核對：381筆技能書、243項說明中的耗魔數值、448筆
選擇定義、1202筆變身卡效果。這些數量不是已還原的公式數量；公式數仍為0。

## 本輪新增查核

1. 對照分開存放的重建偽碼、目前God2.exe與原始指令範圍，確認csvZ和
   cbspec2的讀取路徑。未知欄位意義不等於資料被加密。
2. 解開三份目前客戶端更新清單；其中9088個Data/Data2/Data3資源路徑全部
   存在，9087個長度也相符。唯一長度差異是已修改成本機連線的
   Data3/config.iniZ。此步只查清單、存在性及長度，未宣稱所有檔案的CRC
   或內部格式都已解析，也不能證明原始服務端資料存在於客戶端。
3. 追S2C83/action7的四個輸出：原生拆值後查GodEft的key、ROM編號及路徑。
   34列來源和6144個原生探測向量確認這條是特效選擇，不能當作四項攻防。
4. 技能新讀取鏈`005259EF→005297D0`只讀種類／ID，再選動畫；1792組
   原生案例確認改動定義其餘數值不影響結果。文字搜尋命中24個技能的24筆
   說明，並非24種獨立倍率或公式：12筆大師技能共用條件式2倍暴擊、2筆
   單次攻擊2倍、6筆其他效果描述，另有4筆是「無法觸發傷害兩倍」的排除
   說明。不同技能可能共用倍率，文字不同也不代表不同規則。這些描述約束
   尚不能補出攻防、隨機、順序與取整公式，不計為24項已完成功能。

## 後續缺的證據

需要能把**怪物身分、四項能力值及結算流程**連起來的原始資料或生產端。
已追到的客戶端傷害路徑從服務端封包讀取傷害／資源變化，再做累加、上下限
及畫面更新；尚未證明它如何從攻防和技能倍率算出傷害。所有未知仍保留未知，
沒有寫成0或套用自訂公式冒充原始數據。

## 證據位置

- `src/protocol/RecoveredZeroSeedKey.h`
- `artifacts/reports/current-server-fill-20260926/resource-decoding-key-boundary.md`
- `artifacts/reports/current-server-fill-20260926/resource-manifest-audit.json`
- `artifacts/reports/current-server-fill-20260926/combat-rules-inventory-summary.json`
- `docs/research/current-monster-stat-frontier-20260926.md`
- `docs/research/current-skill-formula-reader-audit-20260926.md`
- `artifacts/research/current-skill-reader-audit-20260926.json`
- `docs/research/unpacked-client-skill-damage-boundary-20260924.md`

怪物原始四項攻防：目前0筆可交付；原始服務端技能公式：目前0條可交付。
本輪另完成背包移動接線，見`owned-inventory-route-20260926.md`。
