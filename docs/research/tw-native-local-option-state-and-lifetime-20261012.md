# 第311輪：角色選項的本地來源與指標生命期

本輪沿既有S2C「1B」追到本地角色物件的實際指標設定與2A初始化來源，也追清清理指標背後的配置／回收結構。只做靜態原生恢復與來源追查；沒有修改C++、執行遊戲、測試、資料庫操作或部署。

## 本地物件與原生入口

外層world為W，子物件I=W+A7F2F6C。實際465BC0 trueentry把R=W+1539683C送給481C20的mode0路徑；481C81取得R+90，經4E7C80及4A7D60→4A97E0寫I+86888。這條路徑的O=R+90，屬本地aggregate，不能當遠端6F物件。這些方法有289歷史重疊，未宣稱全域新發現；其他mode與後續指標替換仍需追查。

資格化的468160 nonnull-name路徑，呼叫415690檢查packet2A並複製36B body；成功且原map等guard成立後，468315..468326以EAX0／ECX1141清除[R+90,R+4594)（末端不含），也就是[O,O+4504)。此cut涵蓋O+449C的WORD與O+449E的BYTE。20260920既有廣泛zeroing紀錄保留；本輪補的是current named2A條件與同一R／O指標來源，不重算全域新zeroing bytes。415690底下transport helpers的實際長度權威未展開。這證明指定條件下的本地記憶體初始化，不證明2A線路中有一個449E欄位，也不代表後續子呼叫保持零值。

| 路徑 | 已資格化的欄位效果 | 尚未證明 |
|---|---|---|
| 成功2A的指定初始化段 | 清本地aggregate，涵蓋449C與449E | 全部2A條件、後續writes、完整服務端issuer |
| 既有S2C1B→4F5030 | body WORD直接寫449C..449D | 449E由body供給或跨opaquechildren保持 |
| 4F55F0／4F5670 | 16-bit wrapping lowWORD加法後signed16 clamp0..10，直接寫44A0／44A2 | 所到506390／44EA80／44EAC0子呼叫的全部副作用 |
| 本地403／405訊息 | scalar運算及通知方向延續310資格 | 官方服務端ACK、玩法權威、完整6F欄位來源 |

完整4F5150反覆重讀當前I+86888的449C／449E／44A0／44A2，直接方法未讀傳入formalpointer arg；無已資格的direct objectstore／explicit persistence，opaquechildren的副作用未遞迴排除。完整方法的selected直接store集合與opaquechildren的副作用分開。指標持有本地物件，不會讓本地flags自動變成服務端權限、角色資料或遠端81B opaque DWORD9／DWORD17。

## 清理指標的配置／回收

55ABA2的非零配置路徑以header+0=1、+4=length、+8=capacity建立資料，回傳header+C。55AC24所到完整5463B5在critical section中，把被釋放header第一DWORD改成舊free-listlink，再將pool+C設為此header；55ABC4所到546326的正常配置路徑從同一poolhead取回並彈出link，之後重新設定live header。因此同一DWORD在配置與回收狀態具有不同結構角色，不能把其回收時寫入當作遊戲Timer36 U18供應者。

55B42F→5479FF的fallback有原始PE匯入的HeapFree及另一路opaque heap children。原始PE的5A0B60／64分別指向5A0B74／68，header68為(-1,0,0)，payload74首byte為0；這只是歷史靜態初始化。實際current global writers、P=U24別名、重新配置與不明子呼叫的完整所有權仍未恢復。len0僅指定global empty pointer，不能套用非零配置的header重設推論。

## 現有服務端選項來源的界線

RecoveredWorldRecords一直解析C1D logical3全WORD；B1 logical2只有selectors7／8在owned_client_options gate內解析。現有CUSTOM-0100先由實際C1D取得全WORD，同一Session／account／character／phase／battle及private current written-entry receipt綁定，再讓B1只改bit0200並保留其他bits。這是預設關閉的暫存偏好與S1B回包政策，非官方服務端因果回覆或持久化玩法。

S1B frame配置在state publication之前準備，但仍是普通回傳wire；後續原handler失敗、重入、allocation或IO可能影響回包。不能宣稱整批state與delivery原子提交、socket Written或client ACK。停用CUSTOM-0100時，既有C1D仍可作ready-world的standalone transport-only通知，無state change／reply。

正常entry receipt只記錄實際發行2A、raw tail及ready hook：entry Written需async_write完整長度、frame bytes、當前Entry／Session／未退休／queueidentity吻合。它不證明遠端初始化、449E當前值、共同lease或完整world source供應者；歷史36B bootstrap候選亦不能填掉未取得的profile／opaque資料。

## 來源範圍與進度

本輪封存於外部tw-native-visibility-state-and-source-311。source-options有10份完整byte inputs，人工閱讀僅readscope記錄區段；native包保留trueentry／PE／連續邊界／selected寫入與named reference重疊。所有nested seals納入closure，完整byte capture不代表整個來源或client callgraph已人工讀完。

990個既有src檔未變；新opcode／串接來源分支／完整雙向路徑增量均0。TW世界解析74＝部分來源50／控制11／未接通13；全遊戲總數、完整雙向路徑分母与百分比仍未知。shared64、TW／CN／web、native fonts、繁簡轉換、帳號存檔及其他凍結功能保留。

網頁v103 commit／CI／builder來源及容量只保存為peer-reported交接，沒有本輪獨立採用、回傳ACK、執行client或據此宣稱共同wire／native驗收或root目前容量現讀。

下一步沿2A的實際本地初始化與後續寫入，把wire body、derived/default memory與真正權威來源分開；追完整6F 81B的原始producer與opaque9／17，具備真正scene/current/install/publication供應者後才接Main factory。不把generic allocator、零值、空回覆或CUSTOM偏好政策算成遊戲完整串接。

## Qualified evidence capsule

Selected static scope only; no complete gameplay credit.

```json
{
  "native-visibility": {
    "qualified_code_intervals": 19,
    "qualified_code_bytes": 3139,
    "qualified_instruction_sites": 926,
    "unique_qualified_code_bytes": 3139,
    "explicit_overlap_bytes": 596,
    "new_local_bytes_vs_captured310_306_289_qualified_bounds": 2543,
    "reference_scope": "Exactcaptured310/306/289qualifiedspan bounds only; historicalzeroing20260920 andother enclosingstudies acknowledged, no globalnovelty.",
    "qualified_native_data_slices": 0,
    "qualified_native_data_bytes": 0,
    "global_historical_novelty_claim": false,
    "new_source_branches": 0,
    "new_opcode_values": 0,
    "new_full_routes": 0,
    "completion_credit": 0,
    "completion_percentage": null,
    "raw_seal_sha256": "412ef7f142508e83fd8c5d5690b642acf2b38e6019d4db53efc933ba27bec4b4",
    "canonical_closure_sha256": "e2cde5f03686a5df8adc7ebce6f5e3aa3556ff32743c9352661f97e3658443a0",
    "closure_members": 219,
    "closure_bytes": 7537292,
    "canonical_format": "Whole seal excluding own canonical_closure_sha256; defaultASCII compact sorted JSON no newline"
  },
  "native-lifetime": {
    "qualified_spans": 13,
    "bytes": 805,
    "sites": 299,
    "new_selected_spans_vs_reference": 10,
    "new_bytes": 585,
    "new_sites": 230,
    "explicit_overlap_bytes": 220,
    "overlap_sites": 69,
    "data_slices": 6,
    "data_bytes": 132,
    "global_new_coverage_claim": false,
    "raw_seal_sha256": "740a657dc7aebcf9fa81cc15683c1f69856889946363ffa29b5fffb3ec7b01f1",
    "canonical_closure_sha256": "ca9dfa54226540c7565d53e2c11846cfa4e5b740794ec93a5cff386dbd035943",
    "closure_members": 96,
    "closure_bytes": 6636718,
    "canonical_format": "Whole seal excluding own canonical_closure_sha256; defaultASCII compact sorted JSON no newline"
  },
  "source-options": {
    "complete_inputs": 10,
    "input_bytes": 1029187,
    "raw_seal_sha256": "617815297ebad21290f892e52ceccabaa4d9837c34af0812514b69f55070eb72",
    "canonical_closure_sha256": "a3211499a24bd455da3e5c3934236906a24ff62b62680da8b15d6f63f559b7db",
    "closure_members": 14,
    "closure_bytes": 1041239,
    "canonical_format": "Whole seal excluding own canonical_closure_sha256; defaultASCII compact sorted JSON no newline"
  }
}
```
