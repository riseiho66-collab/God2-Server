# 第191輪：陸服戰鬥指令整組來源與原生context傳遞

新增3個、修改4個C++來源檔，共7檔。既有Gameplay可明確選用真正的Grouped Authority，將完整有序C35請求交給有界整組來源：Append只保存請求並返回權威明確提供的中間回覆，Single／Final才呼叫一次真正execute_group。這是實際輸入到必要權威供應者的來源接線；原生分組規則、戰鬥授權、成本、結算、完整回覆及Main仍OPEN，不能宣稱戰鬥玩法已打通。來源增量182→183；新增opcode、phase binding及完整雙向玩法均0，全遊戲分母與百分比未知。

## 原生S82到C35的來源

獨立固定CN God2_opt.exe SHA256為582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8。世界接收表492BE0的82項定位4921E8；長度表567EAC定位567BA8，回傳logical9。Consumer將logical+1／+5的DWORD複製到實際輸入物件T+28／+2C，再回傳本地phase4。

物件身分從實際caller追蹤：48DA36將localT=EBP-9F0存到bundle[1]，48DAB2傳T到48A4D0；48A508／48A50B保存真正argument，48A77C再傳同一pointer到48AA10。48AA10保存輸入pointer，48B177送48FCC0；48FCD3保存pointer後，4921E8寫入其+28／+2C。phase4返回後，48DE03將同一bundle交54A320，54A40C取bundle[1]，54A459／54A45F複製到真正戰鬥owner+3C／+40。第190輪已保留的C35 producer再讀owner+3C。不是因為offset相同便推論不同物件相同。

新CnBattleContext82::Record私有擁有完整9bytes，只讀body8及raw_context_a／raw_context_b，decode只要求82與exact9。沒有encode、猜測BattleID、共同角色ID、nonce、grant或回覆。原生客戶端接收／複製context不證明服務端發行與授權規則已恢復。

S86 subtype5的選定呼叫將真正record傳54CD80；原生旗標設定與actor欄位是客戶端操作狀態。旗標bit缺席不表示清除歷史狀態；取消、過期及真正服務端grant生命周期仍待補齊。既有50輪gate／190輪command證據保持原件，不重計為本輪新完整恢復。

本輪21個machine spans共1331B：新完整549750／549770兩個leaf共78B，新限定54A320 initializer兩區共160B，其餘17個保留區共1093B。352 instruction sites、6 data cells、122 primary sites與52 C++ sites不是封包或完整演算法數。21份完整輸入共50,932,935B，包含原PE、metadata與19份primary C；全檔保存不表示全函式已恢復。actor selector在primaryflag0且secondary非0才選owner52，其餘返回owner51，兩旗標均0也不代表有權限；type selector優先primary，再secondary，無旗標走客戶端assert／0。initializer的actor51／52清為FFFF，不證明所有flags同時清零或全生命周期已追回。

## 完整有序指令與一次執行來源

SharedNativeBattleCommandGroups實作既有WorldOwner介面。create必須收到實際connection、完整Lease、同一native Transports、強持有的真正Authority，以及明確正值request record／logical byte budgets；沒有預設14、假battle owner或自動成功。永久receiver為弱引用，每次操作先取得強connection，再核對完整連線tuple與原私有registration。

必要Authority.prepare是純觀察，明確供應Single／Append／Final、真正issuer／group capability及各自實際generation。capability比較包含pointer與shared ownership，generation逐項比對且可為0；它們是實際供應者的API資料，不冒稱原生wire欄位。來源不從kind80、context bytes、GUI token、hash或相同請求製造分組權限。Authority仍須核對context／grant／actor incarnation、命令變體、目標、技能、MP、物品、時效、重播及續送順序。

每筆完整17-byte Request保持未知kind、padding、raw target field與operand。原始順序的完整請求先複製並受雙budget限制；特殊kind2的2WORD分支不套通用mask，續包不作通用duplicate。Append必須有權威明確提供的intermediate_reply，可以是權威明確no_reply，來源不預設任何ACK或no_reply；它只保存pending，不呼叫成本／結算。Final必須有同一issuer／group／generation的既存pending；Single不可吞掉未完group。Single／Final消費prepared並退休本地pending後，只呼叫一次真正execute_group，失敗、throw或已提交前綴都不重試、不假回滾。

私人Receipt繼承新增OperationEvidence，保存exact Request、原Token、Plan、完整有序group及真正底層Result。post觀察核對本adapter身分、私人Receipt、原registration及完整回覆，再將實際Result／完整group交Authority.current；borrowed pointer與span不得被外部保留。這是內部來源身分，不是封包傳輸確認、持久化或官方授權。

## 連線、資格與退休

Source::Scope新增原Pending.native_token，沿既有完整Lease／common character／saved position共同觀察，same_scope額外要求same_registration。Source仍在每個實際Current前後重讀完整共同root／position；Groups負責其接收的exact Scope與實際transport registration fence，不宣稱自行重讀repository。原有五種Current階段保留；有回覆的held queue使用BeforeRelease／AfterRelease，明確no_reply沿既有AfterExecute／BeforeQueue完成，不宣稱每筆請求都執行五次callback。

WorldOwner.release_binding(Lease, original Token) noexcept預設空，保留既有直接owner。Source先terminal，再一次性消費／清除原registered能力後才呼hook；Current／Execute／submitting內的release延後到stage外，失敗與非法後續輸入走同一路徑。沒有原Token時不造hook argument。Groups只退休exact Token私有storage的本地prepared／pending／latest，即使原registration已退也能清自己的暫存；不清共同presence、transport registry、後繼連線或已提交core成本。callback重入使來源terminal，待callback退出再清暫存；清除capability時仍保持重入fence。

Gameplay::Sources新增grouped_battle_commands與battle_command_group_budgets，和原battle_commands互斥。compose要求同一Transports及既有reply budgets，group request bytes至少容納logical17。initialize建立實際Groups再交既有Source::create；原split／全批copy／順序dispatch／native held reply／失敗與斷線release保持。Main尚未選用真正Authority，沒有因此啟用服務或補造規則。

## 盤點、網頁交接與未完工作

| 盤點口徑 | TW | CN |
|---|---:|---:|
|已知C2S opcode|156：151 generic＋5 supplemental|156，完整phase仍待釐清|
|S2C口徑|252長度支援：230 fixed＋22 variable；world非default206|280 phase／opcode entries：account6＋world206＋battle68|
|本輪新增opcode／phase／完整雙向玩法|0／0／0|0／0／0|

TW parser65、reviewed42、18 reviewed／10 pending groups保持，局部42／65=64.6%不是全遊戲。TW battle110 indexed／9 special、83 actions23與86 selectors7亦不是全部變體；CN receiver14 contexts／12 qualified，47DE70／4812B0未知。958 endpoint rows／28 source groups與183來源增量都不能當全遊戲玩法分母。

現讀網頁checkpoint-v12完整7054B、SHA0b9e12c88e33bc2e21d09edf2e17bb6c1d370ab06f6b51aaf7c6fa13820f2f43，契約完整118371B、SHAb474f1ec762d197c07c1fe4befdc2c2cd2c8190ed3592ef02b94c8269e531c71及實際190 ACK完整原件均另存本輪epoch；不刷新189／190歷史hash。契約已補raw target field的特殊2WORD／padding alias限制。v12仍是SOURCE_INTEGRATION_UNVERIFIED，客戶端完整技能、第二actor、道具、controller等來源未全接，來源估計不是本服務端完成度，也不是独立原生證據。

已依使用者既有協調授權，實際回傳本輪来源與S82／S86限定給指定網頁chat，工具回傳目標threadId，完整訊息與結果保存web-peer/coordination.json。這證明訊息已送出，沒有把來源交接視為成本／結算、完整相容或聯合驗收完成。

接續供應真正S82 context／86 grant發行者、戰鬥actor與技能／inventory來源、native group權威規則、成本／結算／完整replies及Main。全遊戲總表、close/window／target／entry／appearance／audience、Web C56、TW/CN/web共同64位計算／storage／wire／object／飄字、仙幣99999999999、合格stack99、共用資料表、WSS／TLS／hosting仍是完整目標，等級不改。

本輪只做實際來源修改、file／hash及有界原生靜態讀取。沒有建置、測試、C++／Lua／native／API／codec執行、DB／SQL、遷移、重啟或部署；沒有重試155停止formatter／capacity／render／glyph鏈及52F330／52F170。保留帳號、存檔、聊天、IME、認證、頭像、原生字體、繁簡轉換及凍結功能。freshbefore1365、prior190完整2295封存成員、初版／refinement／實際current／代理原件與四原始及四最終報告各自保存。目標保持active，全部來源串接後才集中全面驗證、修復與發布。
