# 第206輪：原生技能更新與完整角色列來源

本輪是使用者指定203至207共五輪中的第4輪。目標仍active，207結束後暫停並停止子代理，不開始208。只做靜態來源串接，沒有建置、測試、原生／codec／runtime、DB／SQL操作、遷移或部署。

004D5E60／004D5CC0對WORLD34／35的角色列遍歷，都會繼續處理所有符合incoming subject BYTE零擴展WORD的列。不是first-roster-only，也不是只改currently selected row。每次續行重新取得role／count；source arithmetic及角色原生識別碼不等共用actor identity。本輪保留196／201的7段資料原始區間814B／233 instructions，新原生覆蓋0，原seal不改。

WORLD34每matching row先要求count BYTE小於100，依原始指標順序比較definition BYTE kind／ID。第一duplicate走diagnostic callsite，之後原生重新讀count；不能猜該回呼沒有副作用。新append寫flag0、bank-relative原指標、count++，page bytes3E8為0、3E9為ceil(count／25)，呼叫pure auxiliary helper。WORLD35用精確bank DWORD pointer找該列第一筆匹配，寫flag3，不移除、去重或調整count；原生沒有35的count100上界guard。兩者subject match會繼續所有同識別碼列。

純004D5830先只清auxiliary count5C，依primary flag bit2把指標抄到60的prefix；保留null、重複、順序及未覆寫的舊尾端。不是把所有auxiliary bytes清零，也不能把任何flag當成common learned／cast grant。assert、diagnostic、selected-row refresh、mode menu refresh及selected35 pending table分支的未知callee／實際資料仍明列缺口，沒有進入UI、formatter或render內部。

新增CnWorldSubjectSkillUpdateSource擁有actual object4508、所有16個完整3EC row（包含inactive／stale內容）、完整112656B bank、原生catalog強生命週期與實際Current。先複製所有borrowed input，再確認actual UI+430A8／object+90、bank身份與釘定payload逐byte一致。來源Scope與server post-commit revision分開；Current失敗永久terminal、caught reentry不能復活，Operation還擁有strong self跨observer，避免外部最後持有者在回呼中釋放this。

project_updates按原始record順序，對每一筆的所有matching rows保存完整before與primary／aux data stage、原生definition及選中／menu／pending表的待補條件。Source只獨立限定captured16-row／100-pointer安全幾何，不宣稱原生有這些guard，也不clip count、造default row或拿同key fallback。34 capacity row直接保存無primary變動；35不安全prefix拒絕qualification。完整bank/source/raw/hash/file offset維持精確來源。

staged continuation是條件式資料來源。當走duplicate diagnostic、append menu refresh或selected35時，requires_unchanged_unmodeled_call_roster明確為true；實際權威owner必須獨立限定未知回呼前後仍是同row／count／role域。Source Current本身不能证明未知callback effects。沒有將這個階段投影冒稱完整原生封包副作用或正向common學習流程。

既有SharedSubjectSkillPublication新增明示的optional actual BEFORE-event source與QualifyNative成對輸入；任一邊缺失便拒絕，不fallback。原mandatory common post-commit Qualify仍保留。輸出前將每筆projected definition和same-store CnSharedSkillCatalog的actual source、kind／ID、raw、hash及offset完整比較。immutable projection及strong source穿過BeforeQueue／QueueAccepted，並要求實際native-stage qualifier涵蓋所有匹配列與未知診斷／UI／pending表／rebindings。沒有default issuer、沒有Main啟用、沒有由檔案來源冒出技能權利。

本輪新增2個C++檔、修改2個，來源區段195→196；新完整雙向玩法route0。CMake既有recursive source配置涵蓋新cpp，未執行建置。初版new2及修訂前publisher header確有全文read但沒有實體全檔snapshot，審查明列缺失；existing pub2的before原件與final4來源均完整保留，不重建初版或冒稱所有epoch齊全。所有歷史client／native／source seals原樣保留。

| 範圍 | 本輪結束數量 | 計數範圍 |
|---|---:|---|
| TW C2S observed opcode union |156|151 generic＋5 supplemental／6 branches|
| CN C2S observed opcode union |156|本輪無新增opcode|
| TW WORLD S2C length entries |252／256|230 fixed＋22 variable、4 unsupported|
| TW BATTLE S2C indexed entries |110|9 special＋101 default；83 actions23／86 selectors7|
| CN S2C phase entries |280|account6／world206／battle68|
| CN receiver contexts |14、12具體限定|47DE70／4812B0仍unknown|
| TW WORLD parser review |42／65＝64.6%|僅這個parser範圍的review比例|
| partial owner chains |38|CN35／TW3，非完整routes|
| endpoint rows／source groups |958／28|非全遊戲分母|
| partial source segments |196|195→196|
| 本輪新增完整雙向玩法route |0|native data stage不算完整玩法|
| 全遊戲完整路徑總數／百分比 |unknown／null|全方向、狀態、變體、deferred inventory未齊|

下一輪把這份原生stage接到combined ordered roster publication，遇30／31／32／33／39等介入時要求實際state checkpoint，不能從目前selected row或未知callback推斷；原生UI／diagnostic完整effects及真實common learned／custody／扣書／save／durable／精確native reply／Main issuer／WORLD→battle materializer仍待接。TW／CN／web完整雙向玩法、64位數值與stack99亦未完成；全部來源打通後才全面測試及修復。下一輪207為本次最後一輪，結束暫停目標並停止。
