#!/usr/bin/env python3
"""
Build the PRINTABLE speaker-notes PDF: the paper backup you carry to the podium.

    python3 tools/build_notes_pdf.py          # writes speaker_notes_print_<date>.pdf
    python3 tools/build_notes_pdf.py --html   # stop at the HTML, do not call Chrome

THIS IS NOT THE ROUND-TRIP DOCUMENT. `build_speaker_notes.py` writes the .md and
.docx you EDIT and hand back, and its output has to parse back exactly. This one
is write-only and optimised for reading on paper under pressure: two columns,
slide number and title as the header, notes beneath, nothing else.
SLIDES WITH NO NOTES ARE OMITTED and the #id labels are not printed. The numbers
in the headers are still the DECK's numbers, so they stay correct despite the
gaps.

It reuses `build_speaker_notes.parse_slides()` so there is ONE parser for the
deck and this file cannot drift from the .qmd. Do not re-implement extraction
here.

PAGE BUDGET. Set MAX_PAGES to however many pages you are willing to carry, then
set FONT_PT to the largest size that fits. The script FAILS LOUDLY over budget
rather than quietly handing you a longer document, because the whole point is a
fixed number of sheets in a pocket. The fix when it fails is to drop FONT_PT by
a few tenths; COL_GAP and MARGIN_IN are the next knobs after that.

Re-run this after ANY notes edit. Nothing else updates it.

Chrome is the renderer because it does CSS multi-column with `break-inside`
correctly and the usual alternatives do not.

⚠️ IT TAKES ABOUT TWENTY SECONDS AND LOOKS FROZEN NEAR THE END. Chrome finishes
the PDF and then refuses to quit; the script waits for the file, then stops
Chrome itself.
"""
import os, re, sys, html, subprocess, datetime, shutil, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_speaker_notes as B

# tools/ lives one level below the project root.
ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAMP = os.environ.get('NOTES_DATE') or datetime.date.today().isoformat()
HTML  = os.path.join(ROOT, 'speaker_notes_print_%s.html' % STAMP)
PDF   = os.path.join(ROOT, 'speaker_notes_print_%s.pdf' % STAMP)

MAX_PAGES = 6
FONT_PT   = 11.6     # The largest type that fits MAX_PAGES. Tune it down when
                     # the script reports OVER BUDGET, a tenth at a time. On a
                     # real 54-slide deck this settled at 11.0, so treat 11.6 as
                     # a starting point rather than a ceiling.
MARGIN_IN = 0.42
COL_GAP   = '0.30in'

CHROME  = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
SCRATCH = os.environ.get('NOTES_SCRATCH') or os.path.join(
    os.environ.get('TMPDIR', '/tmp'), 'talk-notes-pdf')


def inline(t):
    """Escape, then the only two inline marks the notes actually use."""
    t = html.escape(t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])', r'<em>\1</em>', t)
    return t


def render_notes(txt):
    """Blank-line paragraphs. A paragraph opening with '-' becomes a hanging bullet.

    A note may start '-Withdrawal can build...' with no space after the dash, so the
    space is optional here. That is deliberate, not sloppy matching.
    """
    out, buf, bullet = [], [], False

    def flush():
        if buf:
            out.append('<p class="b">%s</p>' % inline(' '.join(buf)) if bullet
                       else '<p>%s</p>' % inline(' '.join(buf)))
        buf.clear()

    for raw in txt.strip().split('\n'):
        line = raw.strip()
        if not line:                       # blank line ends whatever is open
            flush(); bullet = False
        elif line.startswith('-'):         # a NEW bullet, even mid-paragraph
            flush(); bullet = True
            buf.append(line[1:].strip())
        else:                              # continuation of the open block
            buf.append(line)
    flush()
    return '\n'.join(out)


def build_html(slides):
    # ncount is taken BEFORE filtering, so the "7/33" tags still refer to the
    # deck's own numbering rather than to this document's.
    ncount = sum(1 for s in slides if not s['uncounted'])
    slides = [s for s in slides if s['notes'].strip()]
    blocks = []
    for s in slides:
        title = B.label(s)
        cls   = 'slide apx' if s['uncounted'] else 'slide'
        tag   = 'APPENDIX' if s['uncounted'] else '%d/%d' % (s['shown'], ncount)
        blocks.append(
            '<section class="%s">'
            '<h2><span class="n">%d</span>%s<span class="tag">%s</span></h2>'
            '%s</section>'
            % (cls, s['pos'], html.escape(title), tag, render_notes(s['notes'])))

    css = """
@page { size: letter portrait; margin: %(m)sin; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: %(fs)spt; line-height: 1.30; color: #111;
  column-count: 2; column-gap: %(gap)s; column-fill: auto;
  -webkit-print-color-adjust: exact; print-color-adjust: exact;
}
.slide { break-inside: auto; margin: 0 0 .50em 0; }
h2 {
  break-after: avoid; break-inside: avoid;
  font-size: %(hs)spt; line-height: 1.18; margin: 0 0 .22em 0;
  padding: .13em .3em .13em .26em; background: #e9efee;
  border-left: 2.4pt solid #1f5f57; color: #10302c;
  display: flex; align-items: baseline; gap: .38em;
}
.apx h2 { background: #f3efe6; border-left-color: #9a7b23; color: #3a2f10; }
h2 .n { font-weight: 700; font-size: %(ns)spt; min-width: 1.45em; }
h2 .tag {
  margin-left: auto; font-weight: 400; font-size: %(ts)spt;
  color: #5c6d6a; white-space: nowrap;
}
.apx h2 .tag { color: #7a6a44; }
p { margin: 0 0 .26em 0; orphans: 2; widows: 2; }
p.b { padding-left: .58em; text-indent: -.58em; }
p.b::before { content: "\\2022\\00a0"; color: #1f5f57; }
strong { font-weight: 700; }
""" % {'m': MARGIN_IN, 'fs': FONT_PT, 'gap': COL_GAP,
       'hs': round(FONT_PT + 0.3, 1), 'ns': round(FONT_PT + 1.2, 1),
       'ts': round(FONT_PT - 1.4, 1)}

    return ('<!doctype html><html><head><meta charset="utf-8">'
            '<title>Speaker notes</title><style>%s</style></head><body>%s'
            '</body></html>' % (css, '\n'.join(blocks)))


def render(src_html, out_pdf):
    """Chrome writes the PDF and then never exits on this machine.

    ⚠️ DO NOT "FIX" THIS BY RAISING A TIMEOUT. Headless Chrome 150 on macOS 12
    finishes printing, logs "N bytes written to file", and hangs, spewing
    CVDisplayLinkCreateWithCGDisplay errors. A plain subprocess.run() therefore
    blocks forever on a job that is already done. So: poll for the file, wait for
    its size to settle, then kill the process ourselves. Exit code is meaningless
    here and is deliberately not checked.
    """
    if os.path.exists(out_pdf):
        os.remove(out_pdf)
    prof = os.path.join(SCRATCH, 'chrome-profile-%d' % os.getpid())
    log  = open(os.path.join(SCRATCH, 'chrome.log'), 'w')
    proc = subprocess.Popen(
        [CHROME, '--headless', '--no-sandbox', '--disable-gpu',
         '--disable-extensions', '--user-data-dir=' + prof,
         '--no-pdf-header-footer', '--virtual-time-budget=8000',
         '--print-to-pdf=' + out_pdf, 'file://' + src_html],
        stdout=log, stderr=log)
    try:
        last, stable, waited = -1, 0, 0.0
        while waited < 120:
            time.sleep(0.5); waited += 0.5
            if not os.path.exists(out_pdf):
                continue
            size = os.path.getsize(out_pdf)
            stable = stable + 1 if size == last and size > 0 else 0
            last = size
            if stable >= 4:                     # 2s unchanged, and non-empty
                return
        raise SystemExit('Chrome produced no PDF in 120s. See %s'
                         % os.path.join(SCRATCH, 'chrome.log'))
    finally:
        proc.kill(); proc.wait(); log.close()
        shutil.rmtree(prof, ignore_errors=True)


def page_count(path):
    """Count pages without a PDF library. /Count is the page-tree total."""
    data = open(path, 'rb').read()
    counts = [int(m.group(1)) for m in re.finditer(rb'/Count\s+(\d+)', data)]
    return max(counts) if counts else 0


def main():
    os.makedirs(SCRATCH, exist_ok=True)
    slides = B.parse_slides()
    open(HTML, 'w').write(build_html(slides))
    print('html  %s' % os.path.basename(HTML))
    if '--html' in sys.argv:
        return 0
    if not os.path.exists(CHROME):
        sys.exit('Chrome not found at %s' % CHROME)

    render(HTML, PDF)

    n = page_count(PDF)
    kb = os.path.getsize(PDF) // 1024
    print('pdf   %s  ·  %d pages  ·  %d KB' % (os.path.basename(PDF), n, kb))
    print('      %d slides, %d with notes'
          % (len(slides), sum(1 for s in slides if s['notes'].strip())))
    if n > MAX_PAGES:
        sys.exit('OVER BUDGET: %d pages against a limit of %d. '
                 'Lower FONT_PT before anything else.' % (n, MAX_PAGES))
    return 0


if __name__ == '__main__':
    sys.exit(main())
