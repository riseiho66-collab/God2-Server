# 第199輪：陸服技能書確認請求接入來源

使用者恢復工作後，本輪接續198輪的真實modal3B確認事件。新增3份C++來源、修改4份既有來源，將已定位的C25送包接到ready-world正式來源分派與明確選定的遊戲owner介面；條件式C1F另有獨立owner。此處是來源接入，真實學習規則、扣書持久交易、全回覆及Main啟用仍未完成。本輪沒有建置、測試、遊戲、原生函式、Lua、codec、API、SQL、DB或部署執行。

## 實際改動

`CnSkillBookUse25.h` 保留全部5個原生bytes：opcode25、itemWORD、slotBYTE、opaque尾BYTE。真實modalcaller的MOVZX使特定尾端為0，但產生者未獨立寫入尾端，所以不對全部請求強制補零。獨立C1F控制只採此已定位的logical2 `{1F,00}`，不當學習ACK或初始登入1F。

`CnNativeSkillBookBindings::lookup_item` 按精確item取出已釘定SKB的完整owned來源紀錄，在複製前後觀察current；不反推alias為共同技能ID、category或學習權利。原先技能selector→firstmatching item是單向的原生關係。

`SharedNativeSkillBookUseSource` 強留資料來源與明確actual WorldOwner。操作保留真實原Token、完整common root、saved position、raw request、完整Book與immutable OperationEvidence，按實際owner的current→once execute→實際完整native replies／明確no_reply決策接回原held native queue。BeforeCatalog需先由owner限定實際store/reader生命期，native檔案雜湊不取代DB版本與物品權利。規則owner必須負責實際學習、扣書、持久事件與完整回覆，不提供默认成功或替代規則。

`SharedWorldGameplay` 的Sources、初始化、整個aggregate形狀預檢、C25及C1F分派、取消與清理皆接上該來源。整批若含C25+1F但未選真實ControlOwner，會在任何前綴效果前拒絕；不靜默吞掉1F。這不是多請求的原子交易，已提交前綴不由adapter回滾或重跑。Owner缺失保持來源未啟用，Main不自動選擇。CMake原有src/*.cpp遞迴來源規則已涵蓋新來源，無需改建置設定。

## 原生證據與邊界

4AE370的4AEB89對比事件handle，4AEB9A調4AD5E0。flags mask2先取消；mask1及signed index0進確認分派。selector1C8D6C的3B tableDWORD指到4ADB73。4ADB7B／4ADB83分別MOVZX saved slotBYTE及itemWORD，4ADB8D調4B0720送C25；opaque1C8D70不作item或target。4ADB98調4B1B40(1F,0)，只有4960A0結果非零才經4815E0送body1=00。即使C25的42E3C gate壓掉送包，後面的C1F獨立條件仍執行，不能推論一筆代表另一筆成功。

modal代理保存11段746 B、216個指令位置，另3段table資料共9 B。這是既有來源域的精確operand/event關係擴展，不宣稱746 B為全新或全函式恢復。先前訊息的「empty C1F」描述錯誤與原raw訂正另存，無覆寫舊封存。

接收代理新增限定S3B data-copy與S3C subtract/clear共236 B／63指令，另保留1202 B既有範圍。S3B拷32 B至slot record+4..23h，record+1..3不由該段寫入；stackability位元來自resource+11B，與SKB+11A不同。S3C普通格按BYTE減量、signed<=0清item/count；該callee不讀payload itemWORD，不能用其當exact item ACK。WORLD35只寫flag3，不刪skill pointer/count，也不證明學習權利。

固定CN EXE SHA256 `582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`；完整PE／TSV留原位並全hash，只複製限定raw spans与完整canonical C及实际源码。完整檔案雜湊不是全語義恢復。formatter155、capacity/render/glyph及52F330/52F170內部保持停止邊界。資料表預設共用、既有帳號存檔、原生字體與文字轉換、等級及凍結功能保留。

## 本輪進度

| 項目 | 數據 | 範圍 |
|---|---:|---|
| TW／CN C2S已觀察opcode | 各156 | 非全階段／變體完成數 |
| TW世界S2C長度表 | 252/256 | 230定長、22變長；不是串通比例 |
| TW戰鬥索引／變體 | 110／83動作23、86 selector7 | 9特殊、101預設；變體分母仍未全 |
| CN S2C階段紀錄 | 280 | account6、world206、battle68 |
| CN receiver contexts | 12/14已限定 | 47DE70／4812B0仍unknown phase |
| TW世界C2S來源分支審閱 | 42/65，64.6% | 僅此解析器opcode範圍 |
| 累計部分來源段落 | 189，增加1 | 新C25及獨立ready1F來源接入，不是完整玩法 |
| 本輪C++來源 | 新增3、修改4 | 真owner實作及啟用未完成 |
| 本輪新opcode／完整雙向玩法 | 0／0 | 原生權利、交易、完整回覆與Main仍OPEN |
| 全遊戲完整串接百分比 | 未知 | 全階段、狀態、變體完整路徑分母尚未確定 |

端點與來源綁定明細以本輪endpoint-catalog199和唯一round report為準。部分段落、codec或反組譯行數不能替代完整遊戲路徑；不因新收件入口把全遊戲百分比提高。目標保持active，本輪沒有暫停要求。

下一個具體來源缺口是實際CN native common subject／learned／book custody規則與單一持久交易owner，並追獨立ready1F原生語義／完整回覆、其餘C25家族及C26/C28。全部TW/CN/web串接後才集中建置、全方位驗證及修復。
