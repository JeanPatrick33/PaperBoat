#!/bin/bash
# usage: runall.sh PAL|US  -> writes /home/claude/work/all_$V/*.txt for files with errors
V=$1; OUT=/home/claude/work/all_$V; rm -rf $OUT; mkdir -p $OUT
cd /home/claude/PaperBoat
find src -name '*.c' -not -path 'src/port/*' -not -path 'src/os/*' -not -path 'src/boot/*' | sort > /tmp/allc_$V.txt
if [ $V = US ]; then
  grep -v '\.pal\.c$' /tmp/allc_$V.txt | grep -Ev '/[^/]*_(jp|fr|es|de|en|en_de|pal|ique)\.c$' | grep -v filemenu_selectlanguage > /tmp/allc2_$V.txt
else
  grep -Ev '/[^/]*_(jp|ique)\.c$' /tmp/allc_$V.txt > /tmp/t.txt
  : > /tmp/allc2_$V.txt
  while read f; do b="${f%.c}"; case "$f" in *.pal.c) ;; *) [ -f "$b.pal.c" ] && continue;; esac; echo $f >> /tmp/allc2_$V.txt; done < /tmp/t.txt
fi
grep -Ev '\.inc\.c$|\.inc$' /tmp/allc2_$V.txt | xargs -P 16 -I{} bash -c 'o='$OUT'/$(echo {} | tr / _).txt; /home/claude/work/syn.sh '$V' /home/claude/PaperBoat/{} 2>&1 | grep -E "error" > $o; [ -s $o ] || rm $o'
echo "files: $(wc -l < /tmp/allc2_$V.txt) failing: $(ls $OUT | wc -l)"
