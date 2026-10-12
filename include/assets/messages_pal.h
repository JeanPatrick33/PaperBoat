#pragma once

#include "alignment.h"

#define PAL_NUM_LANGUAGES 4

// One blob per language; index order matches gCurrentLanguage (LANGUAGE_EN/DE/FR/ES).
static const ALIGN_ASSET(2) char gMsgPalBank_en[] = "__OTR__messages/bank";
static const ALIGN_ASSET(2) char gMsgPalBank_de[] = "__OTR__messages_de/bank";
static const ALIGN_ASSET(2) char gMsgPalBank_fr[] = "__OTR__messages_fr/bank";
static const ALIGN_ASSET(2) char gMsgPalBank_es[] = "__OTR__messages_es/bank";
static const char* const gMsgPalBankPaths[PAL_NUM_LANGUAGES] = {
    gMsgPalBank_en,
    gMsgPalBank_de,
    gMsgPalBank_fr,
    gMsgPalBank_es,
};
