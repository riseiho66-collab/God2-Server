# OEP Notes

PE-001 reports preferred image base 0x00400000 and packed entry RVA 0x00302001 / VA 0x00702001 in .aspack. Entry file offset is 0xA2C01. This is the PE's declared entry, not a recovered OEP.

REQ-001 proposes original entry VA 0x0054A3E8 / RVA 0x0014A3E8. Static range checking places it inside .text virtual memory but outside that section's raw bytes. The file cannot supply original code at this RVA through normal section mapping. Confidence is unverified.

## Evidence Needed

Record actual load base, executed branch into restored code, surrounding disassembly, call stack, memory contents after unpack, and whether control returns to the packer. Validate application initialization and import resolution. Reaching the candidate once is insufficient if it is a helper function or transient stage.

At a different base, use module_base + 0x0014A3E8, not the fixed preferred VA. Store any new candidate alongside the old hypothesis with reasons; do not silently overwrite history.

Unpacked dump: absent. Repaired executable: absent. IAT repair: not attempted. Follow [restore plan](../../docs/EXE_RESTORE_PLAN.md).
