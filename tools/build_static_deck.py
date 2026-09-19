#!/usr/bin/env python3
"""
Build the STATIC deck: the last-ditch backup whose charts cannot fail to draw.

    python3 tools/build_static_deck.py

It takes the single-file usb build and swaps every live plotly figure for a PNG
captured from that same figure at three times display size. Everything else, every
slide, word, number and click, is untouched.

WHY YOU WANT THIS. A live Plotly figure is the part of a deck most likely to fail
on someone else's machine, and it fails by drawing nothing rather than by
erroring. A static copy cannot fail that way, because the charts are pictures.

RUN IT AFTER THE USB BUILD, EVERY TIME. It reads the usb file, so a static deck
built before the usb render is a static copy of the PREVIOUS deck. A hand-made
static copy on the deck this kit came from silently fell four days behind, which
is the reason this is a script and not a procedure.

HOW THE CAPTURE WORKS. Chrome is driven headless with a capture harness injected
into a throwaway copy of the deck. The harness forces every slide visible, lets
the widgets initialise, calls Plotly.toImage on each figure at scale 3, and parks
the results in a <textarea> as JSON. Chrome is then asked for the finished DOM
with --dump-dom and the JSON is read back out.

⚠️ THE DUMPED DOM IS NEVER REUSED AS THE DECK. reveal.js rewrites its own DOM at
runtime, so saving that back out would produce a deck that no longer works. Only
the images are taken from it; the swap is then made textually against the
PRISTINE usb build.

⚠️ WHAT THIS DECK LOSES. Everything INSIDE a chart:
  - hover tooltips on every figure
  - any click target that is part of the chart, such as a legend entry that
    toggles a series, or buttons Plotly itself draws. The capture freezes each
    figure in whatever state it is showing when captured.
Everything OUTSIDE the charts still works, including your own click handlers and
every reveal fragment. Treat this build as the last resort, not the default.
"""
import os, re, sys, json, time, shutil, subprocess, datetime

# tools/ lives one level below the project root.
ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DECK    = 'talk'
STAMP   = os.environ.get('NOTES_DATE') or datetime.date.today().isoformat()
SRC     = os.path.join(ROOT, 'master', DECK + '-usb.html')
OUT     = os.path.join(ROOT, 'master', DECK + '-static_%s.html' % STAMP)
CHROME  = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
SCRATCH = os.environ.get('NOTES_SCRATCH') or os.path.join(
    os.environ.get('TMPDIR', '/tmp'), DECK + '-static')

SCALE = 3

HARNESS = """
<script>
(function () {
  function done(payload) {
    var ta = document.createElement('textarea');
    ta.id = '__harvest__';
    ta.value = payload;
    ta.textContent = payload;
    document.body.appendChild(ta);
  }
  window.addEventListener('load', function () {
    // reveal hides every slide but the current one, and a hidden div can size
    // to zero. Force them all visible for the capture only; this DOM is thrown
    // away afterwards.
    var st = document.createElement('style');
    st.textContent = '.reveal .slides section{display:block!important;' +
                     'visibility:visible!important;opacity:1!important;' +
                     'position:relative!important;}';
    document.head.appendChild(st);
    setTimeout(function () {
      // ⚠️ The size MUST come from the deck's own declared box, not from
      // _fullLayout. Forcing the slides visible changes plotly's autosize, and
      // capturing at the autosized height shifted every figure about 12px down
      // the slide. DIMS_ is injected from the source HTML.
      var dims = DIMS_;
      var gds = [].slice.call(document.querySelectorAll('.js-plotly-plot, .plotly.html-widget'));
      var out = {}, pending = gds.length;
      if (!pending) { done(JSON.stringify({__error__: 'no figures found'})); return; }
      gds.forEach(function (gd) {
        var d = dims[gd.id] || {};
        var w = d.w || (gd._fullLayout && gd._fullLayout.width)  || 1280;
        var h = d.h || (gd._fullLayout && gd._fullLayout.height) || 720;
        Plotly.toImage(gd, {format: 'png', scale: SCALE_, width: w, height: h})
          .then(function (uri) { out[gd.id] = uri; })
          .catch(function (e) { out[gd.id] = 'ERROR:' + (e && e.message); })
          .then(function () { if (--pending === 0) done(JSON.stringify(out)); });
      });
    }, 4000);
  });
})();
</script>
"""


def harness(dims):
    return (HARNESS.replace('SCALE_', str(SCALE))
                   .replace('DIMS_', json.dumps(dims)))


def run_chrome(src_html, dump_path):
    """Chrome does not exit on this machine, so poll the dump and kill it.

    Same hazard as build_notes_pdf.py. See that file's render() for the detail.
    """
    if os.path.exists(dump_path):
        os.remove(dump_path)
    prof = os.path.join(SCRATCH, 'profile-%d' % os.getpid())
    dump = open(dump_path, 'w')
    err  = open(os.path.join(SCRATCH, 'chrome.log'), 'w')
    proc = subprocess.Popen(
        [CHROME, '--headless', '--no-sandbox', '--disable-gpu',
         '--disable-extensions', '--user-data-dir=' + prof,
         '--virtual-time-budget=60000', '--dump-dom', 'file://' + src_html],
        stdout=dump, stderr=err)
    try:
        last, stable, waited = -1, 0, 0.0
        while waited < 300:
            time.sleep(1.0); waited += 1.0
            size = os.path.getsize(dump_path) if os.path.exists(dump_path) else 0
            stable = stable + 1 if size == last and size > 0 else 0
            last = size
            if stable >= 3:
                return
        raise SystemExit('Chrome produced no DOM in 300s. See %s/chrome.log' % SCRATCH)
    finally:
        proc.kill(); proc.wait(); dump.close(); err.close()
        shutil.rmtree(prof, ignore_errors=True)


def main():
    os.makedirs(SCRATCH, exist_ok=True)
    src = open(SRC, encoding='utf-8').read()

    widgets = re.findall(
        r'<div class="plotly html-widget[^"]*" id="(htmlwidget-\w+)"'
        r' style="width:([\d.]+)px;height:([\d.]+)px;">\s*</div>', src)
    if not widgets:
        sys.exit('no plotly widgets found in %s' % SRC)
    print('figures in the deck: %d' % len(widgets))

    dims = {wid: {'w': float(w), 'h': float(h)} for wid, w, h in widgets}
    cap = os.path.join(SCRATCH, 'capture.html')
    open(cap, 'w', encoding='utf-8').write(
        src.replace('</body>', harness(dims) + '</body>'))

    dump = os.path.join(SCRATCH, 'dump.html')
    print('capturing at %dx ...' % SCALE)
    run_chrome(cap, dump)

    dom = open(dump, encoding='utf-8', errors='replace').read()
    m = re.search(r'<textarea id="__harvest__"[^>]*>(.*?)</textarea>', dom, re.S)
    if not m:
        sys.exit('capture failed: no harvest block in the dumped DOM')
    images = json.loads(m.group(1).replace('&amp;', '&').replace('&lt;', '<')
                                  .replace('&gt;', '>').replace('&quot;', '"'))
    if '__error__' in images:
        sys.exit('capture failed: %s' % images['__error__'])

    bad = {k: v for k, v in images.items() if not str(v).startswith('data:image')}
    if bad:
        sys.exit('capture failed for: %s' % ', '.join(bad))
    print('captured: %d images' % len(images))

    # Swap against the PRISTINE source, never the dumped DOM.
    out, swapped = src, 0
    for wid, w, h in widgets:
        if wid not in images:
            sys.exit('no image captured for %s' % wid)
        div = re.compile(
            r'<div class="plotly html-widget[^"]*" id="%s"'
            r' style="width:[\d.]+px;height:[\d.]+px;">\s*</div>' % re.escape(wid))
        # ⚠️ THE PICTURE GOES IN AS A BACKGROUND, NOT AS AN <img> CHILD.
        # These divs carry html-fill-item, so an element inside them changes the
        # flex box and pushes everything below the figure about 12px down the
        # slide. That moved the legend cards and the source line, which are not
        # part of the figure at all. Leaving the div EMPTY and painting the
        # capture behind it keeps the box model byte-for-byte what the live deck
        # produces.
        img = ('<div class="plotly html-widget html-fill-item" id="%s"'
               ' style="width:%spx;height:%spx;'
               'background-image:url(%s);background-size:contain;'
               'background-position:center;background-repeat:no-repeat;">'
               '</div>' % (wid, w, h, images[wid]))
        out, n = div.subn(img, out, count=1)
        if not n:
            sys.exit('could not swap %s' % wid)
        # drop the widget payload so nothing tries to draw over the picture
        out = re.sub(r'<script type="application/json" data-for="%s">.*?</script>'
                     % re.escape(wid), '', out, count=1, flags=re.S)
        swapped += 1

    open(OUT, 'w', encoding='utf-8').write(out)
    print('wrote %s  ·  %d figures swapped  ·  %d MB'
          % (os.path.basename(OUT), swapped, os.path.getsize(OUT) // (1024 * 1024)))

    left = len(re.findall(r'<script type="application/json" data-for="htmlwidget-', out))
    print('live widget payloads remaining: %d  (must be 0)' % left)
    if left:
        sys.exit('a figure is still live')
    return 0


if __name__ == '__main__':
    sys.exit(main())
