# 第314輪：台服世界入口的資源有效性與原始資料恢復

本輪修改4個C++檔案，把原本只有入口issuer/CAS前的資源檢查延伸至快照讀取與後續Current；仍是部分來源串接，新增完整玩法／opcode／雙向路徑均0。

## 來源輸入

已從verified=true的歷史封存索引，按原SHA恢復兩份明文，保存於本輪外部證據包：

- `ChangeDollCard.csvZ.decoded`：15,455B，`0f04cc27292e4b3bc08c030dce8b2564e2fad52bf0d87f227414d63f4ca6acef`。
- `gamedata.csvZ.decoded`：2,783,008B，`75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815`。

這次只做一般archive解封，未執行csvZ codec或研究VM。卡片原檔106個CRLF行，第5行`ChangeDollCount,101`內容19B／含CRLF整行21B，101筆key0..100、39欄；GameData29,672個CRLF行。原始bytes未改。第313輪的缺明文紀錄保持歷史，這次恢復解除那個輸入缺口。

這些是指定歷史資源，不表示當前encoded GameData ef297與原70a4相同；沒有更新基準、安裝資料、執行C++構造器或宣稱目前原生客戶端驗收。

## 實際來源串接

`StoredSources::with_scene_entry_content`要求同一Application Context的帳號／角色／entry reader-writer／EnyName catalog，以及實際完整SceneSupply與原entry_qualify。它拒絕覆蓋已存在的entry_offer，將offer及qualify一次接入既有`create_from_stored_entry`。兩closure共用資源State、執行緒與重入guard，強持immutable NPC/card；借用catalog的生命期必須涵蓋全部issuer、Native與Current drain。

原offer仍保留完整next snapshot、Prepared／BeforeWrite／BeforeCommit前後issuer及CAS。新的stored qualifier先擁有Snapshot/Scope/Frame，核對40B frame完全一致、完整root與position，取得完整world Scene及非零transform exact card row指向的可能另一target Scene、one-based ordinal，再呼叫真正完整qualifier。Check::Supply/Current原樣傳入，之後重新比較同一完整資源觀察。0 key沿原native bypass；不改wire、不推造opaque欄位、padding或success。

既有StoredSource仍負責same-owner、selection/root/position/map、exact snapshot/revision與Current前後儲存有效性。這裡每次新讀資源，不持續保證全部時間或socket交付原子性；COMMIT後失效只能抑制交付，不能倒推撤銷已提交資料。Main仍未選用此計畫；full2A producer、Entered與正式world publication沒有因此完成。

## 遠端原生界線

actual full6F existing-actor replacement→4FC560→ECX=A224→4FFCF0清理四個component WORD handle。完整73B／28sites全部已在305及更早證據資格化，本輪只是實際caller-context拼接，新native bytes0。合法handle<0x1000才把Actionrecord送41B330；四handle最後各寫FFFF。直接store不碰A220，opaque Action children仍未知，不能推定A220不變、無用或padding。full6F DWORD9/17來源仍未恢復，停止重跑known cleanup/allocator。

## 統計與剩餘

TW：C2S候選156；世界解析74＝部分來源50／控制11／未接13。S2C252＝固定230／可變22；nondefault206／default46；reply48／push11／gated4／未分類117；battle indexed110／specialized9；86 selectors7／cases6；83 actions23／projections2／outside21。未掛載TW chains3／bindings38 unique34。

CN：歷史C2S156／S2C phase-opcode280／length253，各scope獨立；未掛載chains35／bindings93 unique71，本輪CN增量0。Mixed282／CUSTOM135／groups26／pending10保持。修改C++4、新增0、資源資格延伸1、精確恢復輸入2；新完整玩法branch/opcode/fullroute0。50/74＝67.6%僅限定解析分支比例；全遊戲總數、完整路徑數／分母、TW與全遊戲百分比未知。

尚缺完整2A producer與後續publication、full6F未知來源、其餘遊戲權威規則及全路徑分母。沒有build/compiler/tests/runtime/native/VM/emulator/resourcecodec/gameDBSQL/migration/activation/deployment；一般archive恢復與唯讀tool index另列，不冒稱沒有做任何SQL。保留存檔、字體、繁簡轉換、TW/CN/web、shared64、仙幣99999999999、stack99及等級。

## 固定證據

外部證據包：`C:\Users\risei\.codex\artifact-archives\god2-server\20261012\tw-native-resource-custody-and-remote-opaque-314`。全部實際captured nested seals計入closure，局部歷史capture不等於完整歷史package或完整manual/callgraph。

```json
{
  "native-entry": {
    "raw_seal_sha256": "1f89cd887163e4add5405c4f8798584dec7a1bc6936d2d86099abfb5d81f220b",
    "canonical_closure_sha256": "9e8ea1d8f30990316b46b48c0cd2c661847f1d6b123ffc832e7a4a538f73828e",
    "members": 42,
    "bytes": 3569938
  },
  "native-remote": {
    "raw_seal_sha256": "4b7a3a3251e0b1204e550226bc685342898092377f91292d0a2fd1f2f80806b9",
    "canonical_closure_sha256": "67b11815cd328b45e951e63bafa8b300bca2b75f43ac53bc0b0ab2aaaf028eee",
    "members": 62,
    "bytes": 6772103
  },
  "source-entry": {
    "raw_seal_sha256": "2521a37c0ed962a157fb4d0b50d2fb13b72a809c34fc3f77224c7f509b6dbf13",
    "canonical_closure_sha256": "195d831674c8d2eeb2de48ad2f3509c399e6253a1bbbf3747cb9270508831bed",
    "members": 24,
    "bytes": 2973614
  }
}
```
