# TW 原生格子讀取與移動場景來源（第171輪）

接續第170輪真正的移動入口，本輪新增原生格子 reader 及具體 TW 移動 WorldOwner，共三個 C++ 來源檔。既有 C++、Lua、客戶端及保存資料不變。格子資料取自真正原生位址相連的完整快照，不用候選導航、共識格子或 CN 資料格式替代。

原生快照及生命週期供應者、真正伺服器權限／時序／完整5D仍未配置，普通 Main 也尚未選用。新增具體 scene/current/authorize/publish 來源不能算新增完整可玩路徑。

## 固定原生來源

TW mapped image 雜湊為 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`，使用已存在的完整本機輸入。本輪沒有開啟封存 DB，也沒有還原歷史客戶端或建置樹。

原生 map getter 為 RVA `00046FF0`／VA `00446FF0`，mode2 所呼叫的格網 getter 為 RVA `00036B60`／VA `00436B60`。兩者位址域分開記錄，不能把 VA 當成 RVA。

- **mode0**：map `+50` 內嵌 `63×63` 原始格子；從 `+103C/+1040` 讀出實際 signed 中心，目的座標減中心再加21，經原生 signed 範圍檢查後讀取。`+FEC` 是原生初始化檢查欄位；原生零值會 assert 後繼續，新來源明確要求非零已初始化快照。
- **mode2**：map `+1030` 指向真正格網，格網 `+8C` 指向原始格子，`+90/+94` 為 signed 寬高，索引 `y*width+x`。來源確認原生32位指標相等、保留地址範圍與完整格網大小，運算使用較寬型別避免 C++ overflow。
- 實際格子 `0/2/254/255` 等 byte 原樣保留。缺資料、不支援 mode 或越界回傳 unknown，不能拿原生 fallback zero 冒充實際採樣。

上述 mode 名稱只表示 getter 的原生分支；本輪不單憑數值推定全部地圖種類或移動權限。原生指標只是快照身分，不在服務端當宿主指標解參考。原生 initializer／原始 byte 寫入亦保存精確跨度，不能因此假設當前快照已正確載入。

## 接入具體移動場景

`SharedTaiwanNativeMovementScene` 保留真正 Session／共用 presence／完整 lease、原生 map／grid／cells 位址與擁有的 bytes，以及真正 scene/resource generation 與 Current。每一步從原生 reader 取得實際目的格子、目前角色方向及場景身分，重新確認共用保存位置。

場景工廠與第170輪 `SharedTaiwanMovementSource::Factory` 使用同一入口；現有入口與 controller／Lua／唯一共用位置 CAS／收件者原生5E／Session5D不需改写。所有原生內容必須由實際供應者提供，沒有任意格子、預設授權或假5D。

授權先取得完整兩byte5D與一次性真正 authority publication。提交後，具體場景核對已保存的 after 位置，保留角色位置／方向及來源 publication incarnation，供下一步 scene 使用。來源自己的 incarnation 不宣稱是客戶端原生 counter。失敗不回退已提交前綴；原生快照／權威回呼過期或被捕捉的重入不能授權下一次 CAS。

這個保留快照分支尚未恢復 runtime cache/window/resource replacement、渲染時鐘、path/corner/dynamic actor、轉場及戰鬥權限。這些仍需真正原生 issuer 與權威來源，不能用檔案存在或型別齊全代替。

## CN 定點追查

CN PE 雜湊仍為 `582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`。新增九個有界完整原生 function spans，共553byte，七項精確關係；上一輪槽位跨度與全域掃描不重算。

- `0043EAF0/00443E80` 確實把 scene `+16180+104` 傳入 ECX，但實際 callee `0047C680/0047C970` 讀 global，未使用 ECX；這項槽位傳遞不能當成接收器選擇證據。
- `00449060` 的實際 state `0x12`（18）先呼叫 `00449310`；result0 分支在 owner `+2CB8` 非零時以 scene `+16180` 呼叫 `00480B10`，再以 scene `+1617C` 呼叫 `0047F310`。不把這些已知呼叫強配到未知 helper。
- `+40D4` 的定點消費者傳入鎖定 context。`0047B6E0/0047B920` 經 context `+8` gate，以 `+3C` 傳入宣告的 Enter／LeaveCriticalSection IAT。僅讀原生描述與 byte，沒有呼叫 Windows API；觀察到鎖定用途不代表證明該欄位全域沒有其他用途。

`0047DE70/004812B0` 的 phase／calling slot 仍未知，接收 context 維持14個、其中12個有階段條件；沒有新增原生階段綁定、opcode、完整來源链或可玩路徑。

## 進度與保留證據

| 項目 | TW | CN |
|---|---:|---:|
| C2S opcode 盤點 | 156（151一般＋5補充） | 156 |
| S2C opcode／階段紀錄 | 252（230固定、22變長） | 280（帳號6、世界206、戰鬥68） |
| 本輪新增 opcode／階段綁定 | 0／0 | 0／0 |
| 本輪新增完整雙向可玩路徑 | 0 | 0 |

TW256長度槽位中的4個不支援槽位、110個戰鬥索引及30項 action／selector 追蹤紀錄均保留。CN280為階段紀錄，不是全域不同 opcode 數量。TW63解析追蹤中的42項範圍內來源（66.7%）不能作全遊戲百分比。958個 endpoint index、28個範圍群組都不是完整路徑分母。全遊戲總路徑及完成百分比仍未知，來源帳本162段增加至163段。

Fresh before1225雜湊為 `dbb88d3d5d0fdb6b6e89e86c6b679766209f14cd17f2ba8dc1e04676f7bdac4f`。完整保留上一輪2071個封存成員，1220份受保護來源不變。三組交付均保存完整原始來源、before／intermediate／current、原生 input／function spans、精確位置與未完成項目；receipt 不冒充原始檔。四份 CLI 原始報表先另存，再擴充為四份最終報表，各交付與 catalog 分別封存。

TW／CN／web 全目標保持 active。其餘未完成項包含原生場景 issuer／完整觀察者政策、mixed dispatcher、CN 帳號及場景權威、普通 Main 選用、64位金錢／EXP／傷害／HP完整儲存與線路／物件／飄字、堆疊99全操作、web WSS／TLS與正式可玩發布。等級、原生字體、繁簡轉換、保存資料與凍結功能不变。

本輪只做來源與靜態逆向：沒有 build、測試、測試式驗證、native／C++／Lua／API 執行、emulation、DB／SQL 存取、部署或服務重啟。靜態來源盤點不作原生驗收。
