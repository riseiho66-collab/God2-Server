# 台服完整神祇回包的實際寫入觀察，第250輪

本輪修改3個既有C++檔，把第249輪實際Application fresh-world保存的Restoration批次接到原Session enqueue與真正async_write，並在後續實際world-records game callback聯讀完整已存神祇來源。這是已接呼叫者的被動寫入觀察，不是新增未使用sender，也不是普通戰鬥入場、initial issuer、grant或完整施法。

## 實際呼叫與原傳輸路線

Session新增私有建構的WorldRecordsWrite handle，Data保存實際Session弱參照、當時account／character、phase、battle generation與不可變exact logical bytes，status只有Pending／Written／Failed。Game owner不是public第一個caller自認：只有原已post(game)的world_records callback入口安裝私有thread_local RAII scope，正常返回及例外均清除；新sender／current先核scope與同Session才讀game-owned IDs。舊sender不需要此scope。

原生bootstrap完成world-ready後可以仍是CharacterSelected；fresh Tick沒有改成InWorld。本輪新sender允許已ready CharacterSelected或InWorld，保存真正phase，沒有改原state或假造common identity。current核同實際Session、owner、phase、ready、未closing及battle generation；這不是缺失的world／common lease epoch。

send_world_records_observed與原void send_world_records共用send_world_records_impl。原budget、logical限制、world-tail gate、編碼、FIFO、timeout與原回包次序保留；新增觀察沒有held frame、input barrier或任意Completion callback。Application原249 companion loop已實際改呼新sender並逐批保留handle，原submission_calls_completed仍只表示呼叫返回。

獨立WorldWriteAttempt marker由post／Write保留，與Application保存的Data不同。最後一個attempt owner析構會CAS Pending→Failed；因此close／fail清queue、排隊拒絕、post或encode失敗及未完成提交不因game保活Data而永遠Pending。只有原async_write成功且exact front.bytes等於捕獲buffer、attempt.frame同buffer、完整transferred size及同Session時，才CAS Pending→Written。已失敗的marker不能被遲到completion復活。這證明本地實際完整frame寫入，不是遠端消費或ACK；不推定部分失敗前客戶端狀態能回滾。

## 寫入結果回到已存神祇來源

實際guild_ordered_world_records入口在後續game callback觀察該同map材料。先核exact map slot／Session incarnation／account／character／phase／battle generation，再核呼叫數、批次數、每個handle的exact logical／current／Written，接著呼真正restoration_current完整重讀神祇，回來再核local。空batches明列NoRecords，沒有用all_of(empty)冒稱socketWritten。

觀察結果明列historical last_observed_write；後續callback重新核對，不可當永久current、future CAS或施法權限。若這次被動full-current觀察拋例外，明確記Failed後交回原handler，避免新增旁觀者令無關玩法斷線；不把壞資料當空清單，也不攔截原玩法自己的權威讀取例外。transport沒有保留repository、game owner或callback，沿原network／game work-guard drain即可；disconnect仍先精確清除249來源map。

同批包含pet bytes時，Written可證那些bytes一同寫入；full current只資格化神祇readset，沒有pet修訂或跨family原子快照。來源在整段寫入期間始終未變、原生客戶端實際消費、同root初始化及battle actor仍未證明。新的handle不能充當這些缺口的授權。

## 原生reset真caller與同根分派

same149c有界保留13段698B／182指令位置與6個table cell共24B，全域新增覆蓋0。465176計算Main+1539683C作468160 initializer第二實參，4681F6載入EBP；4687CC PUSH EBP至468827 CALL468120之間沒有其他CALL，確定真正reset使用此root。只證明到達該initializer路徑，不按world entry名稱推定已reset。

世界dispatcher table[CF]在46B910指向46B30E。成功分支同樣以Main+1539683C呼468120；但46CD90必須返回非0、415690必須返回0，之後另有opaque46BCC0，不能收到CF就宣稱清零或完整consumer完成。本輪只資格化已知42B純資料reset前綴，沒有進入其GUI suffix或以上opaque helpers。

30／31／34／35 case均把logical指標INC成body，以同Main+A7F2F6C為ECX呼各自4AA040／200／660／830，再走共同46B517 mode1 consume／status／下一dispatch控制。這確定逐case先後控制，不擴成opaque queue內部或任意wire排序證明。世界table[2A]在這個dispatcher實際是default46B517，不能把它發明為normal initializer直接入口。同收件owner不等於已資格化其+86888 actor-root綁定。

因此下一個真正資料接點是同Main／connection成功reset occurrence與U+86888綁定epoch，再按實際發送／消費順序把saved30／31／34連到roster；不能從saved快照或socketWritten直接造learned flags／inactive tails為0。原CF producer／完整觸發規則仍未知，沒有猜造新CF回包。

## 進度與缺口

3改0新C++，混合TW/CN部分來源234→235；新增完整雙向玩法0、opcode0。TW C2S156、世界S2C252（230固定／22變長）、battle索引110不變，CN既有156／280也未變。完整台服方向／階段／狀態／變體路徑分母與完成百分比仍未知。

下一步接真正reset occurrence／同root綁定及ordinary battle admission／actor／initial issuer，接著grant incarnation、MP／resources／rules、once settlement、fullreply／WorldOwner／Main與其餘台服流程。未build／test／compiler／runtime／native／codec／遊戲DBSQL／migration／deploy，未連官方服務。保持台服優先、goal active及common／CN／web與凍結功能。

完整before／候選／終版、具體phase blocker修正與native／transport／review材料：
C:/Users/risei/.codex/artifact-archives/god2-server/20261010/tw-native-roster-publication-source-250
