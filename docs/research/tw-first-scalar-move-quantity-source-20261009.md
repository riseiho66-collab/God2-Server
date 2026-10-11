# 第208輪：台服優先與實際scalar物品數量來源

使用者最新要求：「現在繼續工作 先把台服完全串接起來 達到100% 在停止工作」。先前203至207五輪停止已撤銷，實際goal API現讀active；本輪後繼續TW。TW100%必須是完整方向／階段／狀態／變體／間接與延後的權威雙向來源分母；parser、endpoint及局部來源段不能代替。保留CN/web共用核心既有成果，優先完成TW。

本輪修改4份C++：InventoryMoveService.h/.cpp、SqliteInventoryMove.cpp、SqliteRecoveredCharacterRepository.h。CUSTOM-0089數量99域現在接入既有Application的CUSTOM-0037合格scalar bag swap；這不是僅增加一個未呼叫codec。Application先以既有source/catalog／slot資格化並讀取owned snapshots，InventoryMoveService逐slot驗99及occupancy／revision，再準備原生完整回覆，最後到既有SQLite whole-slot CAS；writer在原本交易內再次檢查99、empty destination及非零bounded revisions，保存兩槽完整內容及各physical slot新revision並readback。

原生C2S24是3 bytes、來源slot與目的slot，沒有client-supplied quantity。回覆沿用完整兩槽41(clear)／3B／41(absolute)投影；空格只有41(clear)，不是3C。编码與allocation在commit前。此數量上限來自使用者自訂需求，不冒稱原生stack規則。實際production commit_inventory_move在src中只有InventoryMoveService一個呼叫；Application已有inventory_moves.move呼叫，但本輪未讀當前正式配置／進程，也未部署或宣稱正在執行新程式。

只接已資格化scalar whole-stack swap，不新增stackability、merge、split、equipment／PET／weapon／gem instance規則或item grant。普通背包30格、native50位置、獨立shop購買30及完整instance分路保留。原生signedBYTE127讀取／projection仍保留，以免剪截既有100..127存檔；這些既有rows不遷移，新此類swap被拒絕。所有完整metadata、來源SHA與owner仍由既有資格化來源提供，不以quantity域代替權威。

本輪沒有build、tests、native、codec、runtime、服務重啟、DB／SQL執行或部署；只靜態來源編輯、全文來源保存與帳本雜湊。保留帳號存檔、聊天、IME、認證、頭像、EXE、原生字體、繁簡轉換、等級與原凍結功能。本輪沒有新opcode／phase／原生bytes，也沒有新增完整雙向遊戲路線。

TW上游缺口已重新對齊當前來源：Main目前仍使用不含world-plan的run_server overload，完整TW NativeWorldHostPlan／Application安裝接點已存在，但實際NativeSourceFactory、完整2A材料、初始peer／scene材料、movement timing／permission／complete5D Authority仍未供應。舊historical2A候選不能冒稱完整當前角色材料。現有部分6E／A3／CB typed來源亦不能說全無程式；正確缺口是實際owner／issuer／Main及完整native效果還未接入。

下輪先接實際TW完整entry／scene材料與正式source factory，推進正向2E權威位置CAS及完整native回覆；其餘已知缺口包括PK35／69、A9傳送、D6 PET2 revert、D8每日任務、6B companion control、9E活動、E4控制、BF商店、C2對話、6E觀戰與A3／CB close，還有已審閱42個分支中未完的變體、玩法與儲存／推播。它們不能因本轮99寫入域已接入而刪除。

| 最新有限範圍 | 數量 | 說明 |
|---|---:|---|
| TW C2S觀測聯集 | 156 | 151generic＋5補充opcode／6分支，未窮盡phase／variant |
| TW WORLD S2C | 252有效／256表項 | 230固定、22變長、4不支援 |
| TW BATTLE S2C | 110 | 9special、101default；83 action23／86 selector7 |
| TW WORLD parser／已審閱 | 65／42 | 64.6%僅此parser審閱比例，非台服完成度 |
| TW已審閱reply下界／control／unconnected | 43／10／13 | 現有partial來源仍保留完整權威與變體缺口 |
| TW未hosting phase binding | 10／10不同值 | 非完整遊戲路線 |
| CN C2S／S2C階段項 | 156／280 | account6、world206、battle68；既有成果保留 |
| 全域endpoint／source groups | 958／28 | 索引不是遊戲功能分母 |
| partial owner chains | 38 | CN35＋TW3，不因本輪局部writer而增加 |
| 部分來源段 | 198 | 197→198，本輪＋1 |
| 新C++／改C++ | 0／4 | 已有Application呼叫的實際service/writer接入 |
| 新完整雙向路線／台服100% | 0／未達成 | 全TW分母及完成百分比仍未知 |

before4、第一候選4、final4與實際Application／projection／quantity／SQL source依賴分別完整保留，不重写207及更早封存。兩個bounded子代理交付208後停止自己的小任務，主目標仍active。全God2容量維持50,000,000,000 bytes以下。每輪仍提供唯一報告與路徑帳本；達TW全部來源串接100%才按使用者指示停止，集中測試／全面修復保持後續階段。
