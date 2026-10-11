# 第217輪：台服原生廣告路由與實際世界連線目的地

修改5個既有C++檔，新增0個C++檔；來源串接段206→207，新增完整雙向玩法路徑0。上一輪有實際2新增／5修改，屬progress。台服完整來源串接100%才停止，完整分母與百分比仍未知。本輪只靜態恢復與來源修改，沒有build／test／native／codec／runtime／DB／SQL／deployment執行。

## 已接入的具體來源

RecoveredTaiwanServerAdvertisement原先只留下04 mask row，現在另保留完整已解碼04／05／06連續資料與原始接收順序；真正成功寫出的外層wire仍在Session private advertisement。新增primary_destination(Table,token,raw75)明確區分native table group／subgroup／實際configured count與儲存snapshot group／server，不把A6低BYTE或mask當目的地權限。

投影先取raw07第一個token低3bit相等的完整row，再取該row BYTE32非0路由key。按原生順序重放廣告：04重設endpoint counter但不清既有endpoint tail；05即使subgroup改變仍增加endpoint counter，每筆05重設route counter；06保存完整DWORD，查找只比最低BYTE，重複key取j0..9／r0..9第一個實體匹配。

使用原生0x260 subgroup／0x30 endpoint／4-byte route實體byte offset，而非彼此獨立的(k,j,r)容器；相鄰subgroup endpoint範圍可能重疊，最後實際byte寫入決定讀取值。初始配置endpoint區域按13FE3..1403B清零，後來重複04不再清零。沒有把重複記錄錯當account-latest或清除高tail。

這是明確的server-owned bounded primary subset：actual configured count1..10、subgroup<count、endpoint／route index<10、完整raw75且row count1..2、確實matched row／非0key。原生寫入端沒有同等index界限，不能把這些安全邊界冒稱原生總容量或已支援全部變體。原生12250 fallback與不完整來源保留OPEN，沒有改成默認目的地。

Session只在native_select明確選用的God2CharacterConnection，於constructor body讀取真正accepted socket.local_endpoint，保存不可變private session／mode／IPv4／實際port；全部Session atomic已初始化，沒有在Impl constructor提前存取未建構欄位。沒有public setter，不用remote_ip、config.port或factory前尚未listen的port候選。觀察失敗不改既有socket／認證結果，只讓後續明確來源缺失時拒絕。

Handoff Authority現在必須返回DestinationAuthority，包含實際native Table／configured count與Current。每個候選都核對原L實際A6低BYTE必要相等條件、原始完整廣告、已發raw07及真正G local endpoint；只有原生primary查找產生的IPv4／port與實際接受連線一致才繼續。caller仍須資格化實際table／source epoch／local backing變體與權限；低BYTE相等不是原始UI WORD高位或配置來源證明。

Link.current攜帶完整native Table與Destination（完整05 body8／06 body4及row／j／r），重查全部候選時要求來源與實體查找結果完全相同。保留獨立G00帳號認證、Session private選角輸入、完整snapshot／roots、Live／Authority Current及候選歧義拒絕；沒有把L A6填進G Scope，亦沒有憑IP／port匹配創造帳號或角色授權。

## 原生依據與界限

原生子代理保留14段code，1048 bytes／342 instruction sites，另保留format literal12 bytes；新增全域原生覆蓋與opcode0。S05 logical9／body8：body0 subgroup k、body1 opaque、body2..5 IPv4、body6..7 unsignedLEport。S06 logical5／body4：低BYTE為lookup key，剩餘3 bytes仍opaque。從12310／130E3／13165／12440／11D30追到真正獨立G connect參數；formatter、assert、logger／status內部保持opaque，沒有API執行。

目前仍需真正配置／issuer生命週期與權限政策、完整raw07 issuer與創角後來源、localbacking／clamp／fallback及較大配置變體、全2A／initial scene／5D／Main正式選用。新的端點對應不能取代admission CAS、防重播或parallel-G結算租約，前後Current也不是wire寫出瞬間原子。未正式掛載或驗收。

TW盤點C2S156；world S2C252（fixed230／variable22）；battle S2C110，83 actions23／86 selectors7。CN C2S156；S2C phase rows280（account6／world206／battle68）。盤點與來源段數不代表完整玩法分母。全方向／狀態／變體／deferred、其餘台服13組玩法、numeric64及stack99仍待接通；保留CN／web、共用資料表、存檔、聊天、認證、IME、原生字體與轉換。全部來源串接後才全面測試與修復。
