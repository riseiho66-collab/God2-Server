# 第316輪：場景參數位寬與實際持有角色來源

本輪完成靜態原生呼叫來源的進一步收斂，C++新增／修改0，新增完整玩法branch、opcode、雙向route均0；歷史223／226／315及worker封存保持，不改寫原件。這是有效successor，並非全遊戲完成。

## 實際場景參數消費

315已確定461AD0 arg2=(Q&FFFF0000)|(LE16(B24)>>6)，Q来自NPC／enemy resource count運算，不是直接複製B26..27。316沿actual CALL461B05讀完整4619D0：formal arg2從entryESP+8取WORD，三次PUSH後formal arg1從ESP+10取WORD；兩個area/scene cache bank的比較與儲存也是WORD。因此Q高16不參與這個directconsumer。這不等於全461AD0、所有子呼叫／register/global別名或原wire高位都已證無用，未知body欄位仍保留，不填0。

actual2A→45AA70取area低BYTE、scene低WORD。返回NPCList第一匹配record；scene WORD與record首BYTE零擴展比較，超255的WORD無匹配而非截斷別名。caller對返回record+1讀BYTE並零擴展計數。17area／9941stride／142record、count與兩BYTE resource pairs屬既有gamedata NPCList；251groups／1509resourcecodes不是NPC instance數、座標、怪物能力或server授權。

兩方法374B／109sites；相對明確named-reference union新增256B／64sites、重疊118B／45sites。4619D0與45AA70早在20260927已描述，45AA70亦有223完整leaf證據，故不宣稱全域新方法／全域新native coverage。方法存在與格式是否命中分開；沒有重跑全域metadata掃描、沒有展開45A000或CRT/allocator/resource一般樹。完整captured/map/decode不是全部callee語義閉包。

## 共同角色與外觀的真實來源

native create前40B在角色服務與共同repository持久化為profile BLOB，保留原encoded名字和資料來源；這只能供給已證preview／HUD局部欄位。RecoveredWorldEntry::decoded沿用historical_body與預設kind2，無真正B0/B4 resource/status、B8..11、全部opaque／kind及actual149c owned appearance issuer，不能補成完整正式入口。

RecoveredOwnedPlayerAppearance::from_body是36B consumer projection。world_entry覆寫8components、transform0和兩rawscalars，沒有current149c producer／mutation證據。SqlitePlayerAppearanceRepository明確pin6bf與CUSTOM0047；實際Application writer有diagnostic_owned_weapon_appearance及兩synthetic fixture_after前置。origin字串或持久化本身不能升格原生149c。

NativeEquipmentSnapshot尾DA只證delivery witness；OwnedInventory record是instance custody／receipt，不能推WPN→2A外觀規則或任意remote after6F cache。完整NativeWorldEntrySnapshot＋真正Issuer才是既有來源接點；version/root/position/revision/resource/CAS只是校驗真实來源，不生出缺失欄位。未新增另一個generic supplier/serializer，未改凍結路徑。

## 統計與下一步

TW C2S候選156；世界74＝部分來源50／control11／未接13；S2C252＝固定230／可變22，reply48／push11／gated4／未分類117。Battle indexed110／specialized9；86 selectors7／cases6；83 actions23／projections2／outside21。TW未掛載chains3／bindings38 unique34。CN歷史C2S156／S2C phase280／length253各scope獨立，未掛載chains35／bindings93 unique71；本輪CN增量0。Mixed282／CUSTOM135／groups26／pending10保持。

50/74＝67.6%僅世界解析的限定分支比率；全遊戲總數、完整路徑分子／分母、TW及整體完成百分比未知。沒有build/compiler/tests/runtime/native/VM/emulator/resourcecodec/gameDBSQL、migrate/activate/deploy；資料庫只讀其C++原始碼，未開啟或查詢DB。314兩原明文不重計恢復量。所有frozen帳號存檔、認證、聊天、IME、頭像、原字體及繁簡轉換、TW/CN/web、shared64、仙幣99999999999、stack99與等級保持。

下一步直接取得actual149c角色／外觀的真实mutation與完整入口來源，再完成Entered/install及正常worldpublication。不重查已知cache/lookup，也不把NPC资源數／EnyName名字或已存raw witness當完整玩法。

## 固定來源證據

外部包：`C:\Users\risei\.codex\artifact-archives\god2-server\20261012\tw-native-scene-argument-and-owned-entry-source-316`。完整current closure包含每個實際nested seal；partial history不是完整原歷史包，manual scope依各worker/readscope。

```json
{
  "native-entry": {
    "qualified_spans": 2,
    "bytes": 374,
    "sites": 109,
    "new_selected_spans_vs_reference": 1,
    "new_bytes": 256,
    "new_sites": 64,
    "explicit_overlap_bytes": 118,
    "overlap_sites": 45,
    "data_slices": 0,
    "data_bytes": 0,
    "global_new_coverage_claim": false,
    "raw_seal_sha256": "4540a19dd0fc851a28ba2cb7ea1243dc0667c1aae01d12f5ac8dd0ff35193930",
    "canonical_closure_sha256": "f9041cb91fcfc628ba91edcc272df387325076bbcb8079d624f3caea8094c437",
    "closure_members": 60,
    "closure_bytes": 7129421
  },
  "owned-entry-source": {
    "round": 316,
    "complete_primary_source_captures": 12,
    "bounded_caller_captures": 17,
    "governance_captures": 3,
    "input_count": 32,
    "input_bytes": 189539,
    "source_edits": 0,
    "new_native_field_producers": 0,
    "new_source_branch_increment": 0,
    "opcode_increment": 0,
    "full_route_increment": 0,
    "game_completion_increment": 0,
    "completion_percentage": null,
    "global_absence_claim": false,
    "native_execution": 0,
    "sql_execution": 0,
    "tests": 0,
    "builds": 0,
    "source_increment": 0,
    "cpp_increment": 0,
    "branch_increment": 0,
    "native_methods_increment": 0,
    "bounded_field_provenance_facts": [
      "native create payload first40 persists exact common profile40",
      "profile variants/HUD partial projection already existing",
      "6bf/CUSTOM0047 appearance is incompatible with149c producer",
      "current149c equipment DA15 is issuer-dependent delivery witness",
      "owned custody aliases do not derive complete2A appearance"
    ],
    "raw_seal_sha256": "33e8134d3deeea076d0beb04ea1db06e1967a1a5fae5cc333b71309a2a3233c6",
    "canonical_closure_sha256": "4d6e3a6c334541a10da3275435149606c55c78600f71e29a231f1be323bbb9dd",
    "closure_members": 43,
    "closure_bytes": 238965
  }
}
```
