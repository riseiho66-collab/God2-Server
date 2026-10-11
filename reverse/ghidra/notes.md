# Ghidra Analysis Notes

No Ghidra project or decompilation was produced. The static source is x86 PE32, preferred base 0x00400000. Use the reconstructed image only after its provenance and unresolved imports are documented.

Record source hash, Ghidra version, PE loader/language/compiler settings and base. Review section permissions and executable ranges manually: this packed file declares unusual uniform section characteristics. Do not silently treat a guessed OEP as the program entry.

Trace recovered imports to buffer handling and opcode dispatch. Check decompiler interpretation against instruction-level sizes, sign extension, calling convention and cross-references. Preserve unknown function roles until the data path supports a name.

Export only reviewed symbol records with RVAs and evidence links to the canonical map. If Ghidra and IDA disagree, record the disagreement and underlying bytes instead of taking tool agreement as proof.
