# 第211輪：台服原生選角列表與共同角色來源

本輪新增2個C++來源檔並修改8個既有檔，將實際儲存的TW07原生列表、原生選角token與完整共同角色ID接入同一個Application／Session流程。來源串接段由200增加到201；本輪新增完整雙向玩法路徑為0。TW全遊戲方向、階段、狀態、變體與延後分派分母仍未知，完成百分比為null。使用者的最新順序是台服優先，實際全部串接完成才停止；先前五輪停止条件不再適用。

## 已寫入的實際接線

`SharedTaiwanNativeCharacterListSource`借用實際共同帳號、角色與`NativeCharacterSummarySnapshotRepository`。同一reader必須`owns_sources`配對；固定原生build雜湊、目的地來源TargetSource、目的地Current與完整Qualify均由實際供應者提供。沒有預設group0/server0、猜測6B欄位、成功fallback或自造原生列表。資料缺失、角色歸属變更、名字編碼或來源不一致時，不能輸出假成功。

列表來源保留完整75個logical bytes（opcode07＋74本文），保留旗標、資源、外觀、routeBYTE32及名字NUL後的原始位元組。只核對真正共同角色名字的原始codepage與CP950嚴格轉換是否等同原生列內名字；不改字體、不改名、不進行名字繁簡呈現替換。舊codepage0僅能處理確定ASCII，非ASCII資料需其實際原始codepage。輸出使用既有frame envelope的C++來源路徑；本輪未執行codec。

列表行依真實issuer ordinal與原生token綁定共同角色；原生token的低3bit不當成共同slot。選角來源在實際Authenticated且尚未選角色的Session內，重新觀察完整帳號角色集合、同一列表完整tuple與實際目的地Current／Qualify，再傳回完整共同角色ID。創角後若帶有實際pending_created_character，token必須指向該完整ID；沒有共同slot或14bit actor ID替代。

`SharedWorldHostPlan::Context`新增可選實際帳號／summary reader；Application只在明確`requires_native_character_summaries`時取得同一Database的reader，檢查其共同來源後交給Context。`create_from_stored_entry(...,native_characters=true)`從實際StoredSources的ListSources建立上述Binding，與既有stored-entry、scene、movement及mixed-record來源共用同一guarded Owner。一般`create(...,true)`同樣選取此capability，Owner要求實際account／summary非空且`owns_sources`一致，避免兩個工廠走不同資料庫資格。

Application將native list/select/invalidate來源保留在game owner的WorldLifecycleVault。帳號與角色兩個真實listener中的Session handler僅持有弱facade；revocation在Database還存在時清除實際來源。兩listener使用exclusive native_list/native_select，舊list/select_created/select_existing分支不能混用。Session的選服後列表與角色選取分派實際呼叫這些facade；新操作鎖與來源invalidate_active使供應者捕捉巢狀reentry也不能授權外層繼續。

同時將summary reader/writer的既有SELECT/DML鎖定`main.accounts`、`main.recovered_characters`與兩個共用summary表，避免TEMP同名遮蔽。新增writer reentry poison，實際issuer callback捕捉巢狀writer拒絕後，外層fulltuple核對仍會失敗。canonical v1 schema原始suffix保持逐位元組相同；未修改資料表布局、default migration、舊快照基準或持久化資料。另有獨立removal來源檔的歷史處理未在此有限範圍修改，不能宣稱其全部租約邊界也已完成。

## 原生資料邊界

兩個既有子代理分工：一個定點釐清已保留原生receiver／data-copy證據，一個審本輪10個C++全檔雜湊、實際diff、依賴與owner接線。原生覆蓋本輪新增0，保留11段共528 bytes／174 instructions。TW07 receiver只複製74個本文bytes；本文第一BYTE是count，下一BYTE是opaque flags，不是WORD count。共同兩角色／fixed75幾何預算不是原生permission，receiver沒有自行clamp count。

原生行stride36而選中後複製40 bytes。第一行多出的4 bytes來自下一行前綴；第二行最後4 bytes超出本次receiver寫入範圍，其中包含Application相鄰另一domain。不能補零、當checksum、當創角profile40或宣稱完整selected40已由07提供。保留原始列表與外部selected-name來源；原生名字傳入世界角色的既有caller鏈也不能取代服務端權威資料。

## 本輪明確未完成的接續

- native list/select Current是game owner pre-use觀察；network strand queue-current原子性、實際發出列表的跨socket版本／生命周期尚未接上，不得在strand呼叫SQLite Current，也不能以copied frame＋closing核對冒稱原生完成。
- 真正raw07 issuer、post-create後列表重發、create response/header來源、未明目的地與實際route/resource／visibility權限仍由真實供應者提供，尚未有完整Main工廠。非ASCII的未知原始codepage不能自動填950。
- 從已發出的列表／已選角色到完整2A原生材料的同epoch來源資格、第二行外部selected40 suffix來源、完整initial scene/peer material、publication queue及5D Authority仍開放。storedblob與共用ID綁定本身不等於上述權威。
- 台服13組其餘玩法與全方向／狀態／變體／延後分派、64位元數值全路徑與stack99仍待實際串接。共同資料表預設共用；CN與web成果保留，只有已證明儲存不能共用才考慮`_tw`／`_cn`尾綴。

TW已觀察C2S opcode156；世界S2C有效252（fixed230／variable22），戰鬥S2C110；83 actions23、86 selectors7。TW world parser65，其中42組已做來源盤點，這不是遊戲完成百分比。CN C2S156；S2C phase rows280（帳號6／世界206／戰鬥68），亦非去重後完整雙向玩法分母。來源段201、endpoint958／group28與上述opcode只用來描述盤點範圍。

第一階段未build、test、執行原生、codec、runtime、DB/SQL、migration或deploy；沒有新增正式原生驗收或宣稱已部署。全面測試、修復與可恢復發布保持在全部來源串接之後。
