#pragma once
namespace god2 {
// Explicit owner numeric extension, never inferred from client/version/values.
// LegacyCustom preserves the existing CUSTOM caps and original DWORD operations.
// ExtendedHealth64 is a source capability; it grants no native wire authority.
enum class BattleNumericProfile { LegacyCustom, ExtendedHealth64 };
}
