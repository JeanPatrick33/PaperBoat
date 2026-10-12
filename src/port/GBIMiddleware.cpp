// GBI Middleware - Intercepts GBI macro calls to handle OTR path resolution
// This allows static display lists (like curtains.c) to use OTR paths for
// vertices and textures

#include "Engine.h"
#include <libultraship.h>
#include <string>
#include <unordered_map>
#include <cstring>

// G_SETTIMG_OTR_FILEPATH opcode for OTR texture paths (from libultraship gbi.h)
#define G_SETTIMG_OTR_FILEPATH 0x25

extern "C" void gSPVertexOTR(Gfx* pkt, uintptr_t v, int n, int v0) {
    if (GameEngine_OTRSigCheck((const char*) v)) {
        const char* path = (const char*) v;
        void* data = ResourceGetDataByName(path);
        v = (uintptr_t) data;
    }
    __gSPVertex(pkt, v, n, v0);
}

extern "C" void gbi_resolve_vtx_in_static_dl(Gfx* dl) {
    for (Gfx* cmd = dl;; cmd++) {
        unsigned int opcode = (cmd->words.w0 >> 24) & 0xFF;
        if (opcode == G_ENDDL)
            break;
        if (opcode == G_VTX) {
            uintptr_t w1 = cmd->words.w1;
            if (w1 != 0 && (w1 & 1) == 0 && GameEngine_OTRSigCheck((const char*) w1)) {
                void* data = ResourceGetDataByName((const char*) w1);
                if (data != NULL) {
                    cmd->words.w1 = (uintptr_t) data;
                }
            }
        } else if (opcode == G_DL) {
            unsigned int pushFlag = (cmd->words.w0 >> 16) & 0xFF;
            Gfx* subDL = (Gfx*) (cmd->words.w1);
            if (subDL == NULL)
                continue;
            if (!GameEngine_OTRSigCheck((const char*) subDL)) {
                if (pushFlag == G_DL_NOPUSH) {
                    // Branch (no return) — follow the branch and stop walking here
                    gbi_resolve_vtx_in_static_dl(subDL);
                    return;
                }
                // Push (call + return) — recurse into sub-DL, then continue linearly
                gbi_resolve_vtx_in_static_dl(subDL);
            }
        }
    }
}

// PAL: a few effects ship one graphics bank per language (the console DMAs the matching one in
// effects.c). Their OTR resources are extracted per language as <family>_de/_fr/_es, so redirect
// the (language-neutral) static path to the bank of the current language.
#if defined(VERSION_PAL) && VERSION_PAL
extern "C" int32_t gCurrentLanguage;

static const char* ResolveLocalizedEffectPath(const char* path) {
    static const char* const kSuffix[] = { "", "_de", "_fr", "_es" };
    static const char* const kFamilies[] = {
        "__OTR__effects/effect_gfx_attack_result_text/",
        "__OTR__effects/effect_gfx_chapter_change/",
    };
    static std::unordered_map<const char*, std::string> cache[4];

    int32_t lang = gCurrentLanguage;
    if (lang <= 0 || lang > 3 || strncmp(path, "__OTR__effects/effect_gfx_", 26) != 0) {
        return path;
    }
    auto& c = cache[lang];
    auto it = c.find(path);
    if (it != c.end()) {
        return it->second.c_str();
    }
    std::string out = path;
    for (const char* fam : kFamilies) {
        size_t n = strlen(fam);
        if (strncmp(path, fam, n) == 0) {
            out = std::string(fam, n - 1) + kSuffix[lang] + (path + n - 1);
            break;
        }
    }
    return c.emplace(path, std::move(out)).first->second.c_str();
}
#else
static inline const char* ResolveLocalizedEffectPath(const char* path) {
    return path;
}
#endif

extern "C" void gSPDisplayListOTR(Gfx* pkt, const void* dl) {
    if (dl != NULL && GameEngine_OTRSigCheck((const char*) dl)) {
        void* data = ResourceGetDataByName(ResolveLocalizedEffectPath((const char*) dl));
        if (data != NULL) {
            dl = data;
        }
    }
    __gSPDisplayList(pkt, dl);
}

extern "C" void gDPSetTextureImageOTR(Gfx* pkt, int fmt, int siz, int width, uintptr_t img) {
    if (GameEngine_OTRSigCheck((const char*) img)) {
        // Use G_SETTIMG_OTR_FILEPATH opcode for OTR paths
        const char* path = (const char*) img;
        gSetImage(pkt, G_SETTIMG_OTR_FILEPATH, fmt, siz, width, img);
    } else {
        // Regular texture - use normal G_SETTIMG
        gSetImage(pkt, G_SETTIMG, fmt, siz, width, img);
    }
}
