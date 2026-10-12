#pragma once

// Translation layer for the PaperBoat ImGui menu.
// English strings used in the menu code are the lookup keys; Tr() returns the
// translation for the selected language, or the key itself when none exists.
// Languages mirror the PAL game: 0 = English, 1 = Deutsch, 2 = Francais, 3 = Espanol.

#define CVAR_MENU_LANGUAGE "gSettings.MenuLanguage"

#ifdef __cplusplus
namespace MenuI18n {
int GetLanguage();
const char* Tr(const char* english);
} // namespace MenuI18n
using MenuI18n::Tr;
#endif
