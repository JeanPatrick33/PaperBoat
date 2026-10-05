#!/usr/bin/env python3
"""Generate the PAL message assets from a PAL (Europe) Paper Mario ROM.

Outputs (relative to the repository root):
  assets/yaml/pal/messages.yml        English bank  -> __OTR__messages/MSG_*
  assets/yaml/pal/messages_de.yml     German bank   -> __OTR__messages_de/MSG_*
  assets/yaml/pal/messages_fr.yml     French bank   -> __OTR__messages_fr/MSG_*
  assets/yaml/pal/messages_es.yml     Spanish bank  -> __OTR__messages_es/MSG_*
  include/assets/messages_pal.h       path tables, indexed [language][section][index]
  include/message_ids_pal.h           MSG_* ids for the PAL numbering

Usage: gen_pal_messages.py <pal rom .z64>
The ROM is only used to read the bank layout (section / message offsets); message
text is never copied into the repository.
"""
import struct
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
BANKS = [("en", "", 0x2030000), ("de", "_de", 0x21B0000), ("fr", "_fr", 0x2330000), ("es", "_es", 0x24B0000)]
BANK_SPAN = 0x180000
SECTION_NAMES = None  # filled from the message names (prefix before the first '_')


def parse_bank(rom, base):
    data = rom[base : base + BANK_SPAN]
    secs, pos = [], 0
    while True:
        off = struct.unpack(">I", data[pos : pos + 4])[0]
        if off == 0:
            break
        secs.append(off)
        pos += 4
    msgs = []
    for si, so in enumerate(secs):
        pos, j = so, 0
        while True:
            off = struct.unpack(">I", data[pos : pos + 4])[0]
            if off == so:
                break
            msgs.append((si, j, off))
            j += 1
            pos += 4
    # exact size: first 0xFD terminator, rounded up to 4 bytes (matches the US layout)
    out = []
    for si, j, off in msgs:
        end = data.index(0xFD, off)
        out.append((si, j, off, (end + 1 - off + 3) & ~3))
    return len(secs), out


def main():
    rom = Path(sys.argv[1]).read_bytes()
    if len(rom) not in (0x3000000, 0x4000000):
        sys.exit(f"unexpected ROM size 0x{len(rom):X} (expected 48 MB or 64 MB PAL dump)")
    names = {(a, b): c for a, b, c, *_ in yaml.safe_load((ROOT / "tools/splat_ext/msg_pal_en.yaml").read_text())}

    layout = None
    all_sections = None
    for lang, suffix, base in BANKS:
        nsec, msgs = parse_bank(rom, base)
        key = [(s, i) for s, i, _, _ in msgs]
        if layout is None:
            layout, all_sections = key, nsec
        elif key != layout:
            sys.exit(f"bank {lang} has a different message layout than the English bank")
        lines = [":config:", "  segments:", f"    - [1, 0x{base:X}]", "  no_compression: true", ""]
        for s, i, off, size in msgs:
            n = names.get((s, i)) or f"Unnamed_{s:02X}_{i:04X}"
            lines += [f"MSG_{n}:", f"  {{ type: BLOB, offset: 0x{off:X}, size: 0x{size:X} }}"]
        out = ROOT / "assets/yaml/pal" / f"messages{suffix}.yml"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("\n".join(lines) + "\n")
        print(f"{out.relative_to(ROOT)}: {len(msgs)} messages")

    def mname(s, i):
        return names.get((s, i)) or f"Unnamed_{s:02X}_{i:04X}"

    # ---- include/message_ids_pal.h
    ids = ["#ifndef _MESSAGE_IDS_PAL_H_", "#define _MESSAGE_IDS_PAL_H_", "", '#include "messages.h"', ""]
    for s, i in layout:
        ids.append(f"#define MSG_{mname(s, i)} MESSAGE_ID(0x{s:02X}, 0x{i:03X})")
    ids += ["", "#endif", ""]
    (ROOT / "include/message_ids_pal.h").write_text("\n".join(ids))

    # ---- include/assets/messages_pal.h
    h = ["#pragma once", "", '#include "alignment.h"', "", "#define PAL_NUM_LANGUAGES 4", ""]
    sections = {}
    for s, i in layout:
        sections.setdefault(s, []).append(i)
    for lang, suffix, _ in BANKS:
        h.append(f"// ---- {lang} ----")
        for s, i in layout:
            n = mname(s, i)
            h.append(f'static const ALIGN_ASSET(2) char gMsgPal_{lang}_{n}[] = "__OTR__messages{suffix}/MSG_{n}";')
        for s in sorted(sections):
            h.append(f"static const char* const gMsgPalPaths_{lang}_sec{s:02X}[] = {{")
            h += [f"    gMsgPal_{lang}_{mname(s, i)}," for i in sections[s]]
            h.append("};")
        h.append(f"static const char* const* const gMsgPalSectionPaths_{lang}[] = {{")
        h += [f"    gMsgPalPaths_{lang}_sec{s:02X}," for s in sorted(sections)]
        h += ["};", ""]
    h.append("static const char* const* const* const gMsgPalSectionPaths[PAL_NUM_LANGUAGES] = {")
    h += [f"    gMsgPalSectionPaths_{lang}," for lang, _, _ in BANKS]
    h += ["};", ""]
    (ROOT / "include/assets/messages_pal.h").write_text("\n".join(h))
    print("headers written;", all_sections, "sections,", len(layout), "messages per language")


if __name__ == "__main__":
    main()
