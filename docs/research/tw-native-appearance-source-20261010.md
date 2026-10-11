# 第227輪：實際入場資料直接供應場景外觀基準

本輪新增兩個唯讀C++存取器，修改2個header，新增C++檔0，來源串接段維持214，新增完整雙向玩法路線0。子代理分別獨立恢復149c原生資料流及審閱實際來源／caller。沒有建置、執行測試、原生程式、codec、資料庫／SQL或部署。台服及全遊戲分母、百分比仍未知；目標保持active，優先完成台服來源100%。

`RecoveredWorldEntryView::entry_appearance_baseline()` 直接從既有完整37B logical資料按值取得bound actor、B12..19全8個component、B32..33完整transform WORD及B34／B35兩個raw scalar。保留所有variant bit和非零transform，不經6bf／CUSTOM-0047型別、不補值、不encode或授權。`SharedTaiwanWorldEntered::Scope::entry_appearance_baseline()` 將同一view的投影直接提供給既有實際場景source；沒有新增資料表、callback、cache或獨立Current wrapper。

實際來源鏈是完整NativeWorldEntrySnapshot／entry Qualify→SharedTaiwanWorldEntrySource→Session生命週期→Binding或AsyncBinding保存完整view→SharedTaiwanWorldEntered持有的Scope→真正scene source讀取此基準。新增nested型別與member function不新增View／Scope資料成員，不改既有聚合初始化、送包、生命週期或凍結功能。來源的full root、position/revision、source／client／kind、完整40B、record revision及原writer CAS繼續各自資格化；存取器不取代它們。

本輪同149c靜態資料流確認：normal2A 468328／46833F將兩個DWORD保存至R+4584／R+4588；local DA的普通transform0分支在503FF4..504018將兩個完整DWORD寫到相同W+1539ADC0／C4。前面的502210及之後501810維持CALL閱讀邊界，其副作用與完整rendered after-state未恢復。B32..35同版DA寫入延用226的獨立原生證據，不借舊6bf測試結果。

remote DA不可稱為完整8B保存：4FC130只將incoming odd BYTE高3位寫到actor+251+2*i並保留原low5；override actor+61 bit10時只強制live variant7，該路徑不更新saved odd BYTE。4FD830先寫兩個raw scalar到actor+264／265，再呼叫component更新；所讀前綴未證明remote transform WORD的持久store。實際lookup必須先找到已有actor，128筆、stride0x268，缺席不spawn。純handle／variant setter與呼叫邊界各自保留，不進入GUI／render／場景函式內部。原生consumer行為不自動成為服務端權威規則。

這些值明確只叫「入場外觀基準」。後續DA及36／37事件會改變外觀，舊2A無法單獨證明當前after-state；原樣load相同witness也不能消除這個缺口。仍須真正同源觀察證明沒有中間mutation，或讓實際appearance mutation commit同步更新完整witness。新存取器不授DA發送、observer已出現、transform合法性或裝備到component映射；完整2A issuer、B0／B4、opaque欄位和全遊戲其餘路線仍待完成。

目前TW C2S觀察156值；世界S2C有效252項（230固定、22變長）；戰鬥分派110項（9特殊、101預設），83動作23、86 selector7。CN維持C2S156值、S2C階段280項。65個TW parser中42個具範圍限定來源分支，64.6%只代表該parser分支覆蓋，不是台服完整度。帳本仍不把958個endpoint、214個串接段或唯讀投影當完整玩法分母。

下一步追真正149c appearance mutation issuer及裝備／transform來源，維持同root／revision的完整after-state後再接DA與已出現observer；不以基準投影代替它。CN／web、共用表、64位數值、stack99、仙幣上限、原生字體、繁簡轉換與既有存檔保留。完整來源、原生切片、實際before／candidate／final和報告保存在外部封存區，本地保留精確雜湊索引。
