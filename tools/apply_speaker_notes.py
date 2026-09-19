#!/usr/bin/env python3
"""
Apply an edited speaker-notes document back into the deck sources.

    python3 tools/apply_speaker_notes.py speaker_notes_<date>.md [--dry-run]

The inverse of build_speaker_notes.py. That script generates the document from
the `::: {.notes}` blocks in the .qmd files; this one writes edited notes back
into those same blocks. The heading line is the contract, so the slide id in
`## [12] #method - ...` is what each block is keyed on.

WHAT IT DOES NOT TOUCH. The title slide's notes live in the JS array in
includes/title-slide-notes.html and the generator's HTML-to-Markdown pass is
lossy, so a
change there is reported and left for a person. The ON SCREEN blocks are
reference only and are never read.
"""
import re, os, sys

# tools/ lives one level below the project root.
ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASTER = os.path.join(ROOT, 'master')
# Every .qmd that can hold a `::: {.notes}` block, includes as well as the main
# deck. Add yours here; a file left out is silently never written to.
import glob as _glob
QMDS   = sorted(os.path.basename(p) for p in _glob.glob(os.path.join(MASTER, '*.qmd')))

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_speaker_notes import parse_back, parse_slides


def slide_blocks(lines):
    """(start, end, id) for every `## ` slide heading in one file, fences aside."""
    out, fence = [], False
    for n, ln in enumerate(lines):
        if ln.startswith('```'):
            fence = not fence; continue
        if not fence and ln.startswith('## '):
            m = re.search(r'#([A-Za-z0-9_-]+)', ln[3:])
            out.append([n, None, m.group(1) if m else ''])
            if len(out) > 1: out[-2][1] = n
    if out: out[-1][1] = len(lines)
    return out


def notes_span(lines, start, end):
    """The line range inside a slide's `::: {.notes}` block, or None."""
    i, fence = start, False
    while i < end:
        ln = lines[i]
        if ln.startswith('```'): fence = not fence
        elif not fence and re.match(r'^:::+\s*\{\.notes\}\s*$', ln):
            j, depth, f2 = i + 1, 1, False
            while j < end:
                l2 = lines[j]
                if l2.startswith('```'): f2 = not f2
                elif not f2 and re.match(r'^:::+\s*\{', l2): depth += 1
                elif not f2 and re.match(r'^:::+\s*$', l2):
                    depth -= 1
                    if depth == 0: return (i + 1, j)
                j += 1
            return None
        i += 1
    return None


def main():
    path = sys.argv[1]
    dry  = '--dry-run' in sys.argv
    want = parse_back(os.path.join(ROOT, path))
    have = {s['id']: s['notes'].strip() for s in parse_slides()}

    changed = {k for k in want if k in have and want[k].strip() != have[k]}
    print('%d slides in the document, %d differ from the deck' % (len(want), len(changed)))
    for k in sorted(set(want) - set(have)):
        print('  UNKNOWN ID, skipped:', k)

    if 'title-slide' in changed:
        print('  ⚠️  title-slide changed. It lives in title-slide-notes.html and is')
        print('      not written by this script. Edit it by hand.')
        changed.discard('title-slide')

    written = 0
    for fn in QMDS:
        p = os.path.join(MASTER, fn)
        lines = open(p).read().split('\n')
        edits = []
        for start, end, sid in slide_blocks(lines):
            if sid not in changed: continue
            span = notes_span(lines, start, end)
            if span is None:
                print('  NO .notes BLOCK in %s for #%s, skipped' % (fn, sid)); continue
            edits.append((span, sid))
        for (a, b), sid in reversed(edits):
            lines[a:b] = want[sid].split('\n')
            written += 1
            print('  %-22s #%s  %d -> %d chars' % (fn, sid, len(have[sid]), len(want[sid])))
        if edits and not dry:
            open(p, 'w').write('\n'.join(lines))
    print('%s %d slide(s)' % ('would write' if dry else 'wrote', written))
    left = changed - set()
    return 0


if __name__ == '__main__':
    sys.exit(main())
