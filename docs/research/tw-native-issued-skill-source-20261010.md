# 第243輪：台服原生主技能列表到C35來源

前輪242已接完整持有技能資料，本輪繼續接真正獨立的戰鬥列表資格。已寫入具體模型與game registry，並強制接到既有C35來源的action前檢查；沒有把已學技能、catalog membership或bit15當成回合授權。

## 實際變更

新增`TaiwanNativePrimarySkillList`，保留16 banks、完整100 raw WORD／100 auxiliary BYTE、每個active定義的完整110-byte record、獨立nullable auxiliary定義順序、原bank state／row WORD／page count、實際bank count、signed selector及完整DWORD control A/B。輸入必須是實際服務端發送者持有的完整投影；不捏造native地址、預設旗標或客戶端記憶體證明。

S2C87主列表按定義kind/id首個匹配，只替換舊WORD的bit15；新定義才append原WORD與完整定義。append分頁為(count+14)/15。尾段另讀原row+5C count與row+60的獨立pointer順序，略過null，將首個匹配的bit15鏡射到自己的aux位置；不借用主列表ordinal、不新增aux項目。S2C38在離開state2時清全部100 WORD的bit15與全部100aux，state2尋找實際count中第一個same row WORD且不同signed current的bank，並非直接選packet index。原生忽略的out-of-count38／invalid signed primary selector87保留為qualified no-op；secondary／不合來源資料拒絕。

16／100是此owned safe geometry的資格界線，不能說成原native writer有檢查。nullable aux與其原順序由真發送者提供，不能由主列表或存檔列表補零生成。模型限制primary，沒有恢復secondary或全遊戲actor對應。

新增`SharedTaiwanIssuedSkillSource`，在game owner持有真Session／common ready lease／儲存位置／battle_generation的不可跨來源Ticket。install／replace／87／38只有服務端發送者可呼叫；不是C2S handler。完整main＋present aux定義重讀實際同catalog，依private Ticket比較一次替換，local revision只代表記憶體觀察新舊。容量由實際session capacity明確提供，回收expired weak Session，release不刪不同Session的資料；操作及跨observer保存strong Session並防重入。

HostPlan的same-Context factory提供同presence/catalog registry。既有`SharedTaiwanNativeSkillCommandSource`現在必須取得該具體來源，完整C35 DWORD key需與當前issued-list定義相等，並在qualification／action前重讀。strict primary只接受native side0；A==0且B!=0的alternate/side1不能借主列表。原有真WorldOwner仍必須另外驗actor、learned、grant、MP／規則、一次結算與完整回包。action後只驗真next receipt，不能要求已耗用的舊issued state仍Current。release／invalidation已接。

## 原生證據與範圍

原生先對完整signed DWORD index取得nonnull主列表pointer，再讀enable bit，最後從定義byte0/1組成zero-extended C35 DWORD。C35不攜帶UI selected index或S87 flags；本模型查出的ordinal明稱issued-list lookup ordinal，不能冒稱收到／觀測到客戶端選擇索引。獨立enable leaf本身欠負index guard，不能拆出來當任意index權限判斷。

本輪保留11段768B／261指令位置，額外純primary尾段139B及原page段33B共172B／60位置，分開封存。新增全域覆蓋0，沒有執行原生／GUI／formatter／render、codec或SQL。主native seal與tail refinement seal保持獨立，不刷新先前epoch。

## 尚未接通的上游

1. 一般台服非診斷的真battle publisher尚未找到；沒有實際caller安裝本registry或餵87／38。registry存在不是發送／COMMIT／enqueue receipt證明。
2. 原生roster／已選仙靈到controlled battle actor的真綁定、grant incarnation／86完整控制歷史仍缺。registry的local revision不是native nonce或grant epoch。
3. 真MP扣費／退款、技能規則／目標結算、once durable settlement、完整回包與具體WorldOwner實作者仍缺。
4. Main的完整75/token、2A issuer、scene／peer／resources／geometry／5D及其餘台服路線仍缺。舊CUSTOM／diagnostic發送者不能提升為一般native producer。

所有catalog／presence資格是順序觀察，不是跨來源或未來寫入的一筆原子CAS。本輪沒有連線官方服務器，沒有學習取得規則、預設可用技能、任意成功／空回包或新Gameplay CUSTOM。

## 進度與紀錄

修改4個、新增3個C++來源；新增1項已接C35的具體主列表資料資格能力，混合TW/CN部分來源段227→228。新增完整雙向玩法0、opcode0。TW C2S156／world S2C252（230固定22變長）／battle索引110保持，完整方向／phase／state／variant分母與完成百分比未知。不同索引不能直接相加當功能總數。

目標API實際active。帳本current execution plan的舊blocked值本輪依真receipt更新為active；舊完整ledger、241blocked來源及原報告原件保留，不重寫歷史證據。未build/test/runtime/native/codec/遊戲DBSQL/migrate/deploy。共用/CN/web及凍結功能、數值64／仙幣99999999999／stack99／levels保留。

完整來源、差異、分工、native與tail獨立原件：`C:/Users/risei/.codex/artifact-archives/god2-server/20261010/tw-native-skill-selection-source-243`。
