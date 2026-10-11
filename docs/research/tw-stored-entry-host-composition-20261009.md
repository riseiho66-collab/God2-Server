# 第210輪：台服儲存入場來源接入Application組裝

本輪修改4個C++來源檔，接通第209輪完整2A儲存來源的實際組裝呼叫端：Application的共同Database → 明確選用的Context reader → StoredSourceFactory → StoredNativeSource → 既有guarded Factory/Owner → Entry、initial scene與movement facade → game vault → Session原生entry handler。部分來源段199→200，新增完整雙向玩法通路0；Main與正式服務沒有啟用此plan，完整台服與全遊戲分母、完成百分比仍未知。

`SharedWorldHostPlan::Context`新增借用的`native_world_entries`reader；只有明確`requires_native_world_entry_snapshots=true`才由Application取同一Database的optional accessor，並對實際accounts/characters做`owns_sources`。legacy/generic plan維持false/nullptr，不額外開資料庫、安裝schema或製造資料。這輪只修改來源，沒有執行Application或SQL。

`SharedTaiwanNativeWorldHostPlan::create_from_stored_entry`要求實際build SHA及完整StoredSourceFactory。該factory在既有game-owner guarded建構內執行，取回必要的real Qualify、entered、movement rules/resources/capacity與選用mixed records，然後由Context的精確reader、角色及地圖建立209的NativeSource，交回既有Sources/Owner。沒有先造一個空entry來佔位；既有泛用SourceFactory API保留。Owner.same也比較reader指標，不能換一個Application的storage來延續原owner。

實際Database/catalog仍借用，Source與Current持有其owned snapshot與game-affine guard；既有Application的handler/vault、listener/controller清理必須在Database解構前排空。本輪没有宣稱將borrowed Database改為shared ownership。full raw40、root/profile/name metadata、位置版本、map、actual issuer/Qualify及其後續scene/queue/current資格仍是必要實際來源；factory組裝不代替這些語義，也不證明完整native acceptance。

原生定點追查辨明2A初始化器的外部參數：connected路徑65186從64910第二arg取名字指標，65194呼叫68160；role參數指向world inline角色物件W+1539683C，third out-flag來自Application+A4。名字指標在正常40E0D6 caller指向DE80的local+30；既有selected-copy5BD2..5BDB從rawList+2+36*selected複製40B至這個buffer，wire stride36與copy40保留為各自原生觀察。名字後續進入role+B7，不是2A37 logical內的名字欄位。disconnected分支使用NULL與內部fallback，不能拿此離線fallback當服務端真實名字來源。

這些caller邊界與已知selected-copy data site合計7段保留原生raw404B、106條指令；新增native coverage/opcode/完整通路皆0。4DA0等GUI/text/render內部不展開；caller的原始buffer輸出與已知copy來源分開記錄，不能把client指標當伺服器權限或假造指標回包。需要將實際selected record/name/codepage/current、同一共同角色root與完整2A frame分開資格化後串在同一選角/入場epoch。

盤點沿用：TW C2S已觀察156個opcode；WORLD S2C252（fixed230/variable22）；BATTLE S2C110；83 action23、86 selector7。WORLD parser65、已審來源42；此比例不是完成率。CN C2S156，S2C分phase280。endpoint958、群組28及部分來源段200均不是完整玩法通路分母。

下一步優先接實際selected record/name/codepage與完整2A issuer，再接初始scene material、WorldOwner/delivery與全5D Authority，最後才選用Main正式SourceFactory。其餘TW gameplay/state/variant/deferred路徑、numeric64與stack99完整變動鏈、CN/web共用支援仍在同一目標內。台服全部來源串接實際達100%才停止；全面建置、測試、驗證與修復依使用者順序留待全部串接後。
