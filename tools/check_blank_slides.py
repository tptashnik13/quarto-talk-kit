#!/usr/bin/env python3
"""Fail if the rendered deck contains a slide that renders blank.

WHY THIS EXISTS. A <section> holding only an HTML comment renders as blank white.
It has nothing to overflow, nothing to misalign and no text to proofread, so it
passes every layout audit silently and a human reading the .qmd will never see it.

The usual cause is Quarto's slide splitting. Anything you put between the YAML
header and the first `##` becomes its own slide, and an HTML COMMENT COUNTS AS
ANYTHING. A deck this kit was built from carried a blank slide 2 from the day it
was written, produced by exactly that: a block of design notes above the first
heading. Put such notes inside a `include: false` code chunk instead, which
cannot emit anything.

  python3 tools/check_blank_slides.py master/talk.html
  python3 tools/check_blank_slides.py --self-test

Run it after every render. It is cheap and it catches the one defect a human
reading the .qmd will never see.
"""
import html as H
import re
import sys


def blank_slides(src: str):
    """Ids of sections that render with nothing on them."""
    opens = list(re.finditer(r"<section\b([^>]*)>", src))
    out = []
    for k, m in enumerate(opens):
        end = opens[k + 1].start() if k + 1 < len(opens) else len(src)
        body = src[m.end():end]
        # A vertical STACK wrapper is immediately followed by its first nested
        # section, so its own body is pure whitespace. Its children are checked
        # on their own pass. A genuinely blank slide is NOT whitespace-only,
        # because whatever made it blank (a comment) is still sitting in it.
        if not body.strip() and k + 1 < len(opens):
            continue
        text = re.sub(r"<!--.*?-->", "", body, flags=re.S)          # renders nothing
        text = re.sub(r'<aside class="notes".*?</aside>', "", text, flags=re.S)
        text = re.sub(r"<[^>]+>", " ", text)
        if not H.unescape(text).strip():
            sid = (re.search(r'id="([^"]*)"', m.group(1)) or [None, "(no id)"])[1]
            out.append(sid)
    return out


def self_test():
    stack = '<section><section id="a"><h2>A</h2></section><section id="b"><p>B</p></section>'
    assert blank_slides(stack) == [], "stack wrapper must not be flagged"
    commented = '<section id="x"><h2>X</h2></section><section>\n<!-- notes -->\n</section>'
    assert blank_slides(commented) == ["(no id)"], "comment-only slide must be flagged"
    notes = '<section id="n"><aside class="notes"><p>hi</p></aside></section>'
    assert blank_slides(notes) == ["n"], "speaker-notes-only slide must be flagged"
    real = '<section id="r"><h2>R</h2><p>text</p></section>'
    assert blank_slides(real) == [], "real slide must pass"
    print("self-test OK")


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        self_test()
        sys.exit(0)
    path = sys.argv[1] if len(sys.argv) > 1 else "master/talk.html"
    bad = blank_slides(open(path, encoding="utf8").read())
    if bad:
        print(f"FAIL — blank slide(s) in {path}: {bad}")
        sys.exit(1)
    print(f"OK — no blank slides in {path}")
