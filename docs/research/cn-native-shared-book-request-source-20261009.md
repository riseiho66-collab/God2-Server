# 第201輪：陸服共用技能書來源接入使用請求

本輪新增3份、修改6份C++來源。部分來源段190→191；完整雙向玩法新增0，全遊戲路徑分母／完成百分比未知。上一輪200的共用raw SKB importer及reader保留，本輪把精確同庫來源接到實際選用的C25 source composition。不是學習權限、扣書、持久化事件與原生回覆已完成；不啟用Main或預設owner。

## 實際來源改動

新增 `CnSharedSkillBookSourceCatalog.h/.cpp`：strong實際store lifetime加上pure StoreCurrent，必須在借用任何DB/native來源前限定同一真實DB、當前來源epoch／population及兩個borrowed reader lifetime。對原生386筆逐item與index核對全部metadata、offset、hash、CRLF原始bytes，lookup再讀兩個完整owned rows。resource Current或非空placeholder不能代替DB資格；matching386 expected rows也不宣稱獨立COUNT排除額外異常rows。無SQL執行、schema installation、匯入、alias反推或TW fallback。Game owner及重入terminal guard保留。

`SharedNativeSkillBookUseSource.h/.cpp` 的C25 Pending保留完整native Book與stored source row。每個階段先請真正WorldOwner做BeforeCatalog觀察，再經stored binder取得並重核相同原始資料，最後把兩份owned values交給實際owner，execute保持一次。Book／StoredBook變化不可用舊資料放行；完整輸出、原生token／root、same held queue、發布前後資格及原本取消語義保持。`SharedWorldGameplay.h/.cpp`要求owner、native Books、shared skill catalog、stored binder配對及同一Books指標。compose/create只做指標資格，不讀catalog；每個真實ready請求才讀當前來源。独立ready1F不讀任何書籍catalog，也不推論C25结果。

新增 `CnInlineRoleCounters24.h`：原生WORLD24固定logical17/body16；保存完整owned Record並展開四個原始unsigned DWORD，wire順序對應inline-role+5C/+64/+60/+68。來源是WORLD dispatcher004912E8傳packet+1、actualU、mode0，lengthcell00567D34→00567B9A回17，WORLDcell00492A68→004912E8。mode6的selectedrow+2C/+30及S22不供inline+64，兩者不混用。沒有S24 serializer、HP/MP名稱、cap、numeric64完成或C1F→S24因果宣稱。靜態read dependency時將whole logical accessor保留原始span型別，未建置／執行修正前草稿。

`CnPrebornSubjectState.h/.cpp`保留同actualR/U/epoch來源：額外owned inline DWORD原值，在最終Current fence前完成複製。Selection保存row+5C BYTE指定的actual DWORD+60 prefix，保留零／重複／舊值與完整3EC原始row；own geometry界限不冒稱原生cap。`native_auxiliary_matches_flag_projection`只描述捕獲bytes是否符合當前rawflags&2順序，不表示函式剛執行或取得學習／戰鬥權利。WORLD30可以只清primary count，不清auxiliary prefix，故不能強制auxcount≤primarycount或把stale auxiliary丟失。初稿只將匹配prefix標為可取得的做法已收斂為完整保留actual prefix與獨立描述旗標；保留review refinement紀錄，沒有假造未physicalcapture的歷史全原檔。

## 子代理原生證據

角色counter代理保存7段542B／158sites：展開已存在callers83B、保留459B，new native code0；新增的是固定S24 shape與inline counter來源資格。兩個原data cells共8B，原PE582f完整hash原位，21完整原件＋3原位references；final view／dependency另存。沒有進入formatter／glyph／renderer／155／52F停止鏈。

技能列代理新增純資料leaf4D5830完整76B／26sites；3段caller128B／31sites保留舊分類。實際row+1F0 primarycount BYTE、+1F1 flags、+258 pointer array；helper先清+5C BYTE，再按原ordinal把flags&2的DWORD pointer寫+60並增加auxcount。無去重、null check或tail clearing。保存4D4E00／WORLD34／WORLD35實際供參數caller及舊WORLD30 count-reset81B歷史證據，後者不重計增量。這只恢復世界row輔助陣列來源，沒有證明WORLD→battle primary skill list materialization、common subject分類、cast或learned grant。

共用來源代理新增實際binder及全文靜態審閱Root Source／Gameplay四檔，full before／initial／current／Root final epochs分開保存。初稿來源關係修訂與未physicalcapture的Root intermediate epoch缺口誠實保留，不冒稱原件齊全。所有同庫來源符合條件的讀取仍是程式來源，未存取DB或執行SQL。

## 計數及接續

|範圍|當前數量|本輪增量／限制|
|---|---:|---|
|TW／CN C2S observed opcode union|各156|0；phase/state/variants未全列齊|
|TW世界S2C長度表|252/256＝230固定＋22變長|不是完成遊戲分母|
|TW戰鬥分派|110＝9特殊＋101 default|83 action23／86 selector7|
|CN S2C phase rows|280＝account6／world206／battle68|0|
|CN receiver contexts|14／12有資格|47DE70／4812B0仍未知phase|
|Endpoint rows／source groups|958／28|0；不等於遊戲功能數|
|部分来源段|191|＋1同庫來源到C25 request composition|
|未host來源phase bindings|CN93／71 distinct、TW10／10 distinct|本輪0|
|部分owner chains|38＝CN35＋TW3|本輪0|
|TW世界parser branch review|42/65＝64.6%|限定review，不是全遊戲完成率|
|完整雙向玩法新增|0|權利／扣書／儲存／回覆／Main仍有缺口|
|全遊戲分母／完成百分比|未知／null|不能由opcode／來源段換算|

接續追實際primary-list population與common actor／owned skill／custody supplier，然後一次 learned＋book＋durable event mutation及完整native replies。獨立battle主列表、S87到達歷史與once/group/cost/current規則仍待接，不能用auxiliary/resource membership替代。共用64位元、仙幣僅99999999999、合格stack99、等級不變及TW/CN/web全遊戲原目標保持。

依使用者「下一輪結束後停止工作」，目前201收尾後再完成202即暫停目標模式並停止代理，不開203。201目標仍active但已保存stop-after202要求；所有三名代理完成201後停止，不提前啟動202代理。PHASE1未build／test／native／codec／runtime／API／DB／SQL／migration／deploy；保存帳號、聊天、IME、認證、頭像、原EXE、原生字體／繁簡轉換及其他凍結功能。

唯一report：`20261009-cn-native-shared-book-request-source`；唯一catalog：`endpoint-catalog201`。證據入口：`artifacts/integration/packet-connections-20261006/cn-native-shared-book-request-source-01`。前200輪全部2492 members逐檔保留核對；不刷新歷史基準。全Desktop/God2容量沿用regular-file/no-junction口徑，與清理chat其他口徑分開。
