# Opcode Dispatcher Research

Client dispatcher location is unknown. Begin at the decoded discriminator and trace switch branches, indexed tables, indirect calls or state-dependent dispatch. Do not assume a single global table or 16-bit opcode.

For each mapping record discriminator width, masking/normalization, direction, relevant state, branch/table RVA, target handler RVA, bounds check, default path and evidence ID. Track aliases and shared handlers without claiming distinct semantics from addresses alone.

Validate meanings through field consumers and observable client behavior, not just nearby strings. Compare encoder-side C2S mappings with inbound S2C dispatch independently. Unknown opcodes in the server scaffold must be logged and handled safely; that policy is not a recovered client default.

Acceptance: concrete opcode bytes link through verified extraction to a handler, payload schema and state/response observations. Publish in OPCODE_TABLE and PACKET_HANDLER_MAP only after that chain is recorded.
