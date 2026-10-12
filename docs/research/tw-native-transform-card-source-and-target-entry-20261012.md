# 第313輪：台服變身卡資料與世界入口的目標資源

本輪將已取得的卡片列語義接成實際C++來源：新增2個檔案、修改4個檔案。原生卡片資料元件已接到既有explicit世界入口供應／快照CAS；完整原生入口產生器與正式掛載仍未完成，因此新增完整玩法路徑和opcode均0。

## 已串接的來源

TaiwanNativeTransformCards只接受呼叫者提供的絕對decoded來源及完整bytes。先複製持有，再核對原SHA256 `0f04cc27292e4b3bc08c030dce8b2564e2fad52bf0d87f227414d63f4ca6acef`。它保留完整原文、header、每行raw bytes／line／offset、39個原始欄位與實際選取的signed32整數，再按原native store取低BYTE／WORD。文字欄位保留原bytes，不做繁簡或字體變更；未選取欄位不生成語義。

field0→48B索引與WORD0；field1→WORD4；field3→BYTEC(area)，field4→WORDE(scene)，field5→WORD10(ordinal)；field8..22→WORD12..2E。field2是原生另一allocated label指標，在本C++保留原欄位bytes，不重造native pointer；6/7沒有被所選loader取用。這些是card resource identity／增益資料，不能冒稱野生怪物的HP、雙攻雙防、五行或技能。

新card-aware StoredSources.scene_entry_offer透過原Context的同一NativeEnemyDisplayCatalog及既有完整SceneSupply。SceneContent持有實際immutable卡片來源，完整producer產生Offer後，既有entry_appearance_baseline讀其2A transform WORD；0沿原分支不查卡，非0必須exact row-key match，再讀card-derived target scene及one-based ordinal，不能用current-world scene代替。

完整target Scene強持有並在每次實際Issuer的Prepared／BeforeWrite／BeforeCommit前後與現讀觀察比對；target與world scene分開，原full next snapshot和opaque bytes完全保留。沒有生成任意success或新版2A格式。原無cards binding沿原契約；CMake的既有src/*.cpp遞迴來源清單與Windows bcrypt link包含新元件，未執行建置。

## 原生解析與來源邊界

Native loaded-bound在45BB10中沒有先清零，更新依舊signedWORD與accepted key比較；max-key+1只在初始化條件成立時成立。45C100 inclusive guard不能授權來源列；factory使用原101個key0..100的exact rows，拒絕將額外calloc slot101當原列。

Native451BE0先找comma，沒有comma才找LF，按owner WORD count處理380B槽，未含CSV quote／escape語法。Actual enclosing reader456130配置52；451920 clamp5..52。歷史研究工具固定39 slots／38commas是其fixture subset，不是原生硬上限。本factory的106lines／header第5行／101 ordered rows／39fields是原decoded pin的既有歷史來源subset，嚴格數字解析拒絕失敗、trailing junk及overflow，並非完整重現native sscanf的所有接受行為。

本輪唯讀現取4565B encoded ChangeDollCard.csvZ，SHA256仍為 `4d51b22d51c14bc98b6ec96c16a40384a226e9fa1f90543ea58a36fb4b56ebd2`。沒有恢復／讀取新的decoded plaintext、執行資源codec或載入catalog；當前C++構造器需要後續actual owner提供精確原bytes。原header行ending仍未新取得，沒有偽造原明文。原始metadata及歷史基準保持。

## 遠端角色追查

Actual S2CDA case的bodyWORD0與local identity原樣比較，不套3FFF mask；self走503D30，nonself在46938F呼叫4FC990。完整4FC990只掃128×268 pool並回傳actor pointer或0，沒有setter store，先前lead名已更正。

Actual appearance方法傳wholeactor A給4FD160；它直接写A79（A38為16/17/18對應1/2/3，其他0），在條件分支才將低WORD selector送到C=A224的4FF8E0；其他A38的signed A38+A3A >=19時bypass。後者直接寫C26=A24A，讀component／signed座標／Action owner；opaque Action children未展。這些直接欄位不供給A220、full6F body8／10或logicalDWORD9／17，不把不同opcode格式互填。前後lookup之間有opaque children，角色／slot穩定性未由此證明。歷史已資格lookup與DA prefix扣除重疊，不稱全域新發現。

## 尚未完成與統計

資料來源資格嵌在existing pre-COMMIT issuer流程，不等於full2A生成、native installed-resource currentness、COMMIT後交付fence、socket Written／ACK、world publication或正式Main啟用。完整SceneSupply、entry_qualify、Entered、Current、install及其餘遊戲來源仍必要。

TW：C2S候選156；世界解析74＝部分來源50／控制11／未接13。S2C252＝固定230／可變22，nondefault206／default46，reply48／push11／gated4／未分類117；battle110／specialized9；86selectors7／cases6；83actions23／projections2／outside21。TW未掛載chains3／bindings38 unique34。

CN：歷史C2S156／S2C phase-opcode280／length253，各scope獨立；未掛載chains35／bindings93 unique71。Mixed282／CUSTOM135／groups26／pending10不變。新source材料元件1；新完整玩法分支／路徑／opcode0。全遊戲總封包數、完整路徑數／分母、TW／全遊戲百分比仍未知。50/74＝67.6%僅是限定解析分支比例。

沒有build／compiler／tests／runtime／native／VM／emulator／resourcecodec／game DB SQL／migration／activation／deployment。保留帳號存檔、shared64、仙幣99999999999、stack99、原生等級、TW/CN/web、原字體及繁簡轉換。最新來源313為progress；前次status-only回合為no progress，已重新核對312 commit及實際來源後採取本轮源碼串接。

下一步恢復精確原card plaintext並提供到實際source owner，補完整2A與後续Current/Entered；續追真正遠端Action children及full6F原始來源。目標保持active。

## Fixed evidence capsule

完整captured inputs不等於整檔manual/callgraph，限定閱讀scope與原生區間分別在封存包。Actual nested seals全納入closure；局部historical參照不聲稱其原完整執行封存已複製。

```json
{
  "native-entry": {
    "qualified_spans": 14,
    "bytes": 1943,
    "sites": 640,
    "new_selected_spans_vs_reference": 14,
    "new_bytes": 1943,
    "new_sites": 640,
    "explicit_overlap_bytes": 0,
    "overlap_sites": 0,
    "data_slices": 2,
    "data_bytes": 19,
    "global_new_coverage_claim": false,
    "raw_seal_sha256": "9c9cb70e9b1a7c98e60f89077ff8fdc920364fb72ac3cf26850bd31eb1a2f8ad",
    "canonical_closure_sha256": "3d7954d0ff1bbf47a2ff9a6d18716e15c3d48fa0cbee280844493281c30363ca",
    "closure_members": 105,
    "closure_bytes": 7061289
  },
  "native-remote": {
    "round": 313,
    "qualified_intervals": 6,
    "qualified_bytes": 1630,
    "qualified_instruction_sites": 524,
    "qualified_instruction_bytes": 1630,
    "complete_methods": 4,
    "complete_selected_case": 1,
    "selected_prefix": 1,
    "relative_named_reference_overlap_bytes": 401,
    "relative_named_reference_new_bytes": 1229,
    "reference_sets": [
      {
        "file": "inputs/history312/inputs/history290/qualified-spans.json",
        "sha256": "06df2f16d8925a69d7b1d4191759a1ee7d06c5d9a8b8d6785cd918fe9d874a0b",
        "intervals": [
          [
            5251600,
            5252280
          ],
          [
            4609592,
            4610246
          ],
          [
            4618336,
            4619459
          ],
          [
            5247424,
            5248525
          ],
          [
            5246048,
            5247418
          ],
          [
            4638368,
            4638465
          ],
          [
            5245984,
            5246036
          ],
          [
            4614912,
            4617876
          ],
          [
            4619632,
            4619666
          ],
          [
            4614416,
            4614419
          ],
          [
            5221488,
            5221657
          ]
        ]
      },
      {
        "file": "inputs/history312/inputs/history307/qualified-spans.json",
        "sha256": "9dbf615030690db369c42a68eb160421d9e18c53a0a4e81046e7384b1e57c218",
        "intervals": [
          [
            4623072,
            4623208
          ],
          [
            4632082,
            4632141
          ],
          [
            4610223,
            4610270
          ],
          [
            5313462,
            5313564
          ],
          [
            5314497,
            5314564
          ],
          [
            5331388,
            5331402
          ],
          [
            5331883,
            5331918
          ],
          [
            5331545,
            5331677
          ],
          [
            5320832,
            5320901
          ],
          [
            5323796,
            5323863
          ],
          [
            5319104,
            5320330
          ],
          [
            5344848,
            5346009
          ],
          [
            4741088,
            4741202
          ],
          [
            4723952,
            4724111
          ],
          [
            4879696,
            4879812
          ],
          [
            5207328,
            5207670
          ],
          [
            5207760,
            5207775
          ],
          [
            5537151,
            5537185
          ]
        ]
      },
      {
        "file": "inputs/history312/inputs/history308/inputs/tw-current-actor-source-301-native-220/qualified-spans.json",
        "sha256": "0a77daf4bb5829b2d3c9d34f87ec3a758cfa75f79dbf169ab57831a5007fad43",
        "intervals": [
          [
            5221296,
            5221460
          ],
          [
            5223520,
            5223653
          ],
          [
            5227872,
            5228116
          ],
          [
            5228896,
            5228938
          ],
          [
            5300736,
            5300997
          ],
          [
            5299344,
            5299380
          ],
          [
            5244765,
            5244908
          ],
          [
            5243264,
            5243486
          ],
          [
            4626929,
            4626984
          ],
          [
            5226944,
            5227859
          ],
          [
            4609063,
            4609082
          ]
        ]
      },
      {
        "file": "inputs/history312/inputs/history308/inputs/tw-pk-phase-owner-gate-305-native-resource/qualified-spans.json",
        "sha256": "f08556d0330991ebc581c3c500d5dcd009e00285467f5d1bba9bf3808183baf7",
        "intervals": [
          [
            5230000,
            5230541
          ],
          [
            5227651,
            5227671
          ],
          [
            5227117,
            5227186
          ],
          [
            5240080,
            5240391
          ],
          [
            5240400,
            5240721
          ],
          [
            5241440,
            5241487
          ],
          [
            5239744,
            5239791
          ],
          [
            5239840,
            5239888
          ],
          [
            5242096,
            5242169
          ]
        ]
      },
      {
        "file": "inputs/history312/inputs/history308/inputs/tw-remote-actor-fields-298-native-fields/qualified-spans.json",
        "sha256": "46a2429700cb474b7bf0f8a0c442b0ad7c68f9bb84d8d0dea06c13398fd84735",
        "intervals": [
          [
            4625864,
            4626984
          ],
          [
            5226944,
            5227859
          ],
          [
            5226800,
            5226932
          ],
          [
            5230000,
            5230541
          ],
          [
            5231424,
            5232036
          ],
          [
            5232496,
            5232544
          ],
          [
            5225296,
            5225377
          ],
          [
            5282656,
            5282824
          ],
          [
            5282192,
            5282432
          ]
        ]
      },
      {
        "file": "inputs/history312/inputs/history308/qualified-spans.json",
        "sha256": "ac4c33f3ad5e0c666752c2d7e163973c3d5161236a49eafe0fdcd188db3e6c3b",
        "intervals": [
          [
            5232544,
            5232687
          ],
          [
            5224672,
            5224827
          ],
          [
            5228192,
            5228241
          ],
          [
            5228320,
            5228799
          ],
          [
            5299312,
            5299335
          ],
          [
            5299392,
            5299995
          ],
          [
            5302160,
            5302222
          ],
          [
            5301632,
            5301820
          ],
          [
            5301824,
            5302160
          ],
          [
            5301008,
            5301631
          ],
          [
            5241840,
            5241926
          ],
          [
            5241936,
            5242022
          ]
        ]
      },
      {
        "file": "inputs/history312/qualified-spans.json",
        "sha256": "adad2aeab49efc5d92be55a5ead5d0dc026cf1e322be8be2cd6a5ccc0ffbc33e",
        "intervals": [
          [
            4623072,
            4623208
          ],
          [
            4627465,
            4627720
          ],
          [
            5225520,
            5226165
          ],
          [
            5300000,
            5300556
          ],
          [
            5300560,
            5300725
          ],
          [
            5229664,
            5229679
          ]
        ]
      },
      {
        "file": "inputs/history227/native-spans.json",
        "sha256": "fb2f9500cc4eebc7f3ac1121e008d6fc8e502ad3b14acd71bc7d7389dfced8c7",
        "intervals": [
          [
            4621096,
            4621131
          ],
          [
            5259105,
            5259252
          ],
          [
            5259252,
            5259288
          ],
          [
            5226800,
            5226932
          ],
          [
            5239888,
            5239917
          ],
          [
            5241376,
            5241403
          ],
          [
            5228944,
            5229006
          ],
          [
            5228896,
            5228938
          ],
          [
            4625257,
            4625310
          ],
          [
            4625699,
            4625747
          ],
          [
            5232688,
            5232764
          ],
          [
            5232905,
            5232931
          ]
        ],
        "selected_raw_spans_captured": [
          "remote-pointer-lookup",
          "da-dispatch-prefix",
          "remote-resource-call-boundary",
          "remote-scalar-save",
          "remote-setter-call"
        ],
        "other_intervals": "Metadatareferences only; notcurrentmanualrequalification"
      }
    ],
    "global_historical_novelty_claim": false,
    "identity_setter_recovered": false,
    "opaque9_17_source_recovered": false,
    "data_bytes": 4,
    "source_branch_increment": 0,
    "completed_opcode_increment": 0,
    "full_route_increment": 0,
    "completion_credit": 0,
    "completion_percentage": null,
    "excluded_exploratory": [
      "identity_setter_exploratory includesunreachedfollowingmethods",
      "identity_case_exploratory wrongstart4692D0/incompleteend",
      "identity_remote_case includesnext4Acase notqualified",
      "da_actor_update_exploratory includesunreachedfollowingfunctions andtruncatedlastinstruction",
      "actual_remote_refresh_child_exploratory includesfollowing4FD320 notqualified",
      "component_refresh_exploratory includesfollowing4FF9C0 notqualified"
    ],
    "next_actual_cut": "Search/qualify an actualfull6Fbodypointer indirectchild or remoteA220 use fromactualpoolcaller; allnewDAcomponentrefresh custody stopsatC=A224 andActionownerC28. Actoridentitylookup4FC990 isnowclosedpurelookup, cannotremainadvertisedsetterfrontier. Fullserverissuer/currentmarkersrequireactualserverauthority separately.",
    "raw_seal_sha256": "1b9c01a474b1f012ca594e0eaa21bafd943218b2636c86be4a0fff3d1e42d084",
    "canonical_closure_sha256": "ad30472c51012caba1c0653922c5c42406c4121fe9a9b2123d7324c52c76b31c",
    "closure_members": 113,
    "closure_bytes": 7183880
  },
  "source-entry": {
    "complete_source_inputs": 23,
    "complete_input_bytes": 212916,
    "existing_Cplusplus_modified": 4,
    "new_Cplusplus_added": 2,
    "source_material_components_added": 1,
    "new_connected_gameplay_branches": 0,
    "new_complete_bidirectional_routes": 0,
    "new_opcodes": 0,
    "decoded_source_recovered": false,
    "current_encoded_bytes_match": true,
    "global_native_new_coverage_claim": false,
    "raw_seal_sha256": "8a686c98b3eaf4c316e8ca4a02c805fda48fcad1e86146715bc39c8cfc97f56b",
    "canonical_closure_sha256": "0d73e76d68b97b857323ef206ffc0e8ccb2579bc211f76a6f486c5b57c9456bd",
    "closure_members": 28,
    "closure_bytes": 223690
  }
}
```
