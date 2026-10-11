# 第225輪：同一Application場景內容接入入場供應來源

新增實際資料流：Application同一SqliteDatabase既有EnyName reader → Context.native_enemy_displays → StoredSources::scene_entry_offer → with_scene_content → 完整SceneSupply → 既有Offer／writer CAS／stored-entry讀回流程。NPCList由224的完整75c3 decoded不可變原件供應，EnyName由224的完整資格場景讀取器供應。本輪修改6個既有C++檔，新增0；來源段213→214，新增完整雙向玩法路徑0。目標保持active，台服全部串通才停止。

SceneContent私有建構並只公開readonly資料，強持完整NPC原件及擁有完整EnyName Scene（完整source tuple、raw列、ordinal、generation、source occurrence）。真正封包producer收到這些實際完整內容後仍必須提供完整40B2A及真實Issuer。NPC群缺席／空群、完整EnyName下的缺場景是資源觀察，不能自動授予入場；EnyName全目錄未載回nullopt，無fallback空bank。area保持入場1..16，scene保持原2A可表達的0..1023；NPC對256..1023仍WORD完整比較而缺席，不窄化到BYTE別名。

供應前後及原writer的Prepared／BeforeWrite／BeforeCommit三個Issuer邊界前後重新比較完整EnyName場景觀察，同時保留強NPC原件及exactissued完整snapshot。三階段仍呼叫原始真正Issuer；資源Current不能代替原生權限／規則／完整狀態。新SceneState同步owner／caught-reentry拒絕，callback入口先強持owner／content／issuer，不以catch後的true資格復活。原Offer::create的common-root／position／Selected／Presence與完整tuple CAS流程保留，不在BeforeCommit比較已過時的old entry，不在COMMIT後重讀／provider／重試。

Context追加const catalog指標，預設null維持其他來源可建構；Application只在既有Context aggregate加入已migrated同一Database的既有無SQL／DDL accessor。Host Owner保留同ptr並在same(Context)比對；helper要求同writer／reader物件及實際account／character／common根。generic with_scene_content只是borrowedcatalog adapter，不能證任意reader／writer同連線；同DB與lifetime保證來自實際Application Context與既有game-owner vault drain。沒有新增Schema、資料庫表、migration、import或Main啟用。

本輪未替未知2A B26..27、高位資源／狀態、native142B／26B padding、場景權限、怪物HP／雙攻雙防／技能或spawn造值。現encoded gamedata ef297仍不是歷史70a4；未解碼／恢復／換基準，完整75c3 NPC輸入未聲稱現已載入。尚待真正完整SceneSupply producer、一次性admission、lifecycle／scene／reply、Main明確選用與全部剩餘TW路徑；這是來源鏈進展，尚非部署或遊戲完成。

盤點維持TW C2S156；世界S2C252（230定長／22變長，另4不支援）、battle110（9專門／101預設）、83動作23／86 selector7；65解析分支中42已review＝64.6%僅解析review率。CN C2S156／S2C280階段項（account6／world206／battle68）。跨版958端點／28群、38部分未hosting owner chains維持；不同層級不能相加當全遊戲分母。TW及全遊戲完整路徑分母／完成率仍null。

兩個子代理僅做靜態來源閱讀／原件封存；全新覆蓋bytes／opcode／完整路徑均0。本輪沒有build／tests／runtime／native或VM／codec／server／DB／SQL執行／migration／deploy。保留CN／web、共用資料與核心、64位共用數值、仙幣99999999999、合資格重疊99、原字體／文字轉換、accounts／saves／chat／IME／auth／portraits及全部凍結功能。新增完整root／agent原件與報告在本任務外部archive，Desktop只保留小型指標及catalog metadata，舊封存不移動不刪除。
