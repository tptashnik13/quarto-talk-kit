#!/usr/bin/env python3
"""
Does every slide fit the canvas? Run this before any presentation.

    python3 tools/check_fit.py           # checks master/talk.html
    python3 tools/check_fit.py --usb     # checks the portable build
    python3 tools/check_fit.py --band 0  # ignore the control-icon band
    python3 tools/check_fit.py --self-test   # prove it still catches a planted overflow
    python3 tools/check_fit.py --fences  # ::: balance per source file

WHY THIS IS SCREEN-INDEPENDENT, which is the whole point. Reveal lays every slide
out at exactly the configured canvas size, 1280x720 here, and then applies ONE
uniform `transform: scale()` to fit the display. Verified in reveal 5.1.0's own
layout(): it sets `slides.style.width/height` to the canvas size, always clears
`zoom`, and never reflows. `html`, `body` and `.reveal-viewport` are all
`overflow: hidden`, so the page itself cannot scroll.

**So a bigger screen cannot change what fits.** A slide that overflows on a
projector overflows on a laptop too; projection at 1.4x to 2.0x just makes the
same overflow big enough to notice. That is why this check needs no screen size.

THE ONE SCREEN-DEPENDENT PATH is reveal's scroll view, which activates BELOW
`scrollActivationWidth` (435px by default). It is a phone-width feature, not a
big-screen one.

WHAT IT MEASURES, per slide and in canvas pixels:
  - every element's bottom against the section's content-box bottom
  - every element's right against the section's content-box right
  - text rectangles as well as element boxes on the VERTICAL axis, because a
    clipped glyph does not move its parent's box
  - every fragment state, because an unshown fragment still occupies its full
    layout box and a shown one can be taller
  - every CLICK-DRIVEN open state. A component that expands on a click handler rather
    than on fragments may permit only one open item, in which case all-open is NOT
    a reachable state and measuring it is measuring fiction. A component may additionally STEP: an open row reveals one
    more branch per click, and its tightest state is the LAST step, not the first.
    Each handler's full class contract must be reproduced, not approximated

TWO FALSE POSITIVES THIS SCRIPT USED TO PRODUCE, both fixed, and both worth
knowing because a checker that cries wolf gets ignored:

  - Transitions do not advance in a headless or backgrounded browser, so an
    animating slide got measured mid-flight. One slide read 56.8px OVER while
    frozen at its pre-transition size, and had 21.7px of slack once settled.
    Every transition is now killed before anything is measured.
  - Range rectangles span the full width of a block's line boxes, so using them
    horizontally reported overflow where none exists. Text rects are now
    vertical-only.
  - A CSS `animation` is not a `transition` and is not stopped by setting one.
    A slide whose content arrives as a keyframe animation rather than a transition
    and, frozen part-way, reported 27.8px of horizontal overflow. Both properties
    are now cleared.

THE BOTTOM BAND IS SPENT. Reveal draws the chalkboard, menu and slide-number
controls over the bottom-left of the canvas, measured at roughly y=682 to y=710.
Content reaching that low measures as fitting and is unreadable, so the default
budget treats the last 40px as gone. That figure is a deliberate round-up of a
38px band; when it disputes a screenshot by a few pixels, the screenshot wins.
"""
import json, os, re, subprocess, sys, tempfile, shutil

# tools/ lives one level below the project root.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The deck's filename stem. Change this and the usb `output-file` in
# _quarto-usb.yml together, or the two builds stop pairing up.
DECK = 'talk'
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

PROBE = r"""
<script>
(function () {
  function ready(fn){ if (window.Reveal && Reveal.isReady && Reveal.isReady()) fn();
    else setTimeout(function(){ready(fn);}, 120); }
  function run(){
    var scale = Reveal.getScale();
    var secs = [].slice.call(document.querySelectorAll('.reveal .slides section'))
                 .filter(function(s){ return !s.querySelector(':scope > section'); });
    var out = [];
    secs.forEach(function(sec){
      var i = Reveal.getIndices(sec);
      Reveal.slide(i.h, i.v);
      var cs = getComputedStyle(sec);
      var isDivider = /divider-slide/.test(sec.className);
      var isPhoto   = /photo-slide/.test(sec.className);
      var frags = [].slice.call(sec.querySelectorAll('.fragment'));
      var states = [];
      // state -1 is arrival; then one state per fragment shown cumulatively.
      for (var n = -1; n < frags.length; n++) states.push(n);

      // ⚠️ FRAGMENTS ARE NOT THE ONLY WAY A DECK CHANGES STATE, and a checker
      // that only knows about fragments will pass a slide that overflows the
      // moment someone clicks it. Any component driven by a CLICK HANDLER opens
      // states no fragment sequence reaches. This kit ships one such component,
      // the expandable card row, so its open states are driven from here.
      //
      // ADD YOUR OWN COMPONENTS TO THIS SELECTOR, and reproduce each handler's
      // FULL class contract below rather than approximating it. An early version
      // of this script just toggled `.is-open`, which invented a state the deck
      // cannot reach and reported a card row 234px over. The real handler ALSO
      // collapses the other card to a spine and sets the grid's column widths.
      // That was the checker's fault, not the deck's, and a checker that cries
      // wolf gets ignored.
      var openers = [].slice.call(sec.querySelectorAll('.cards.expandable > .card'));
      // KILL EVERY TRANSITION FIRST. Headless and backgrounded tabs do not advance
      // CSS transitions, so a slide that animates between states gets measured
      // MID-FLIGHT and reports overflow that does not exist. That cost a false
      // positive on a slide whose question shrinks over one second: frozen at
      // its pre-transition size it measured 56.8px over, and settled it has 21.7px
      // of slack. Same trap CLAUDE.md records for reading a fragment's opacity.
      // ANIMATIONS TOO, and they are a SEPARATE property. content that arrives as a
      // keyframe animation, not a transition, is left frozen part-way through
      // its travel by killing transitions alone. One slide here reported 27.8px
      // of horizontal overflow that the screenshot showed was not there.
      [].slice.call(sec.querySelectorAll('*')).forEach(function(e){
        e.style.transition = 'none';
        e.style.animation = 'none';
      });
      // ⚠️ IF YOU ADD A COMPONENT THAT SETS A CLASS FROM REVEAL'S FRAGMENT
      // EVENTS, rather than from the fragment class itself, drive that class by
      // hand here too. Otherwise this measures a state the deck never shows.

      var worstV = 1e9, worstH = 1e9, worstAt = '', lowest = '';
      states.forEach(function(n){
        frags.forEach(function(f, k){
          if (k <= n) f.classList.add('visible'); else f.classList.remove('visible');
        });
        void sec.offsetHeight;
        measure(n === -1 ? 'arrival' : 'fragment ' + (n + 1));
      });

      // Then the click-driven states, on top of the fully-revealed fragment state.
      if (openers.length) {
        frags.forEach(function(f){ f.classList.add('visible'); });
        // ⚠️ EACH HANDLER'S CLASS CONTRACT HAS TO BE REPRODUCED, NOT APPROXIMATED.
        // A first version here just toggled `.is-open` and invented two states the
        // deck cannot reach: a card row read 234px over, because the real handler
        // ALSO collapses the other card to a spine and sets the grid's column
        // widths, and #apx-items read 516px over with all eight panels open, which
        // its handler forbids. Both were the checker's fault, not the deck's.
        var grid = sec.querySelector('.cards.expandable');
        // An accordion that permits only ONE open item at a time has no
        // all-open state, so measuring one is measuring fiction.
        var oneAtATime = !!grid;

        function setOpen(idx){
          openers.forEach(function(x){ x.classList.remove('is-open', 'is-collapsed'); });
          if (grid) grid.classList.remove('open-left', 'open-right');
          if (idx === null) return;
          openers[idx].classList.add('is-open');
          if (grid) {
            // card-expand.html: the open card takes the row, the other becomes a
            // spine, and the grid's column widths come from a class on the GRID.
            grid.classList.add(idx === 0 ? 'open-left' : 'open-right');
            openers[1 - idx].classList.add('is-collapsed');
          }
        }

        openers.forEach(function(o, k){
          setOpen(k);
          void sec.offsetHeight;
          measure('open ' + (k + 1) + ' of ' + openers.length);
          // ⚠️ IF A COMPONENT OF YOURS ALSO STEPS — an open row that reveals one
          // more branch on each further click — walk every step it can reach.
          // The LAST step is the state that binds, and a checker that measures
          // only the first will call the slide clean.
        });
        // Only INDEPENDENTLY-toggled rows can all be open at once, and when a
        // component allows it that is usually its tightest state.
        if (!oneAtATime && openers.length > 1) {
          openers.forEach(function(x){ x.classList.add('is-open'); });
          void sec.offsetHeight;
          measure('all ' + openers.length + ' open');
        }
        setOpen(null);
      }

      function measure(label){
        var r = sec.getBoundingClientRect();
        var bl = (r.bottom / scale) - parseFloat(cs.paddingBottom);
        var rl = (r.right  / scale) - parseFloat(cs.paddingRight);
        var mb = -1e9, mr = -1e9, who = '';
        [].slice.call(sec.querySelectorAll('*')).forEach(function(e){
          var b = e.getBoundingClientRect();
          if (b.height === 0 && b.width === 0) return;
          var c = (e.className || '').toString();
          if (/cursor-|drag/.test(c)) return;           // plotly hit-targets
          var bb = b.bottom / scale, rr = b.right / scale;
          if (bb > mb) { mb = bb; who = (c || e.tagName).slice(0, 30); }
          if (rr > mr) mr = rr;
        });
        // Text rects catch a glyph clipped at the BOTTOM without moving its box,
        // which element geometry misses. VERTICAL ONLY, deliberately. A Range over
        // a block element returns its line boxes, and a full-width line box reaches
        // the container edge whether or not anything is clipped, so using these
        // horizontally reported one slide as 27.8px over while its text sat
        // 161px inside the edge. Horizontal stays on element boxes.
        [].slice.call(sec.querySelectorAll('p,li,h1,h2,h3,td,th,figcaption')).forEach(function(e){
          var rg = document.createRange(); rg.selectNodeContents(e);
          [].slice.call(rg.getClientRects()).forEach(function(t){
            var bb = t.bottom / scale;
            if (bb > mb) { mb = bb; who = 'text in ' + ((e.className||e.tagName).toString().slice(0,24)); }
          });
        });
        var v = bl - mb, h = rl - mr;
        if (v < worstV) { worstV = v; worstAt = label; lowest = who; }
        if (h < worstH) worstH = h;
      }
      frags.forEach(function(f){ f.classList.remove('visible'); });
      out.push({ id: sec.id || ('slide' + i.h), divider: isDivider, photo: isPhoto,
                 states: states.length,
                 display: getComputedStyle(sec).display,
                 kids: sec.querySelectorAll('*').length,
                 v: Math.round(worstV * 10) / 10, h: Math.round(worstH * 10) / 10,
                 at: worstAt, lowest: lowest });
    });
    var pre = document.createElement('pre');
    pre.id = 'fit-report';
    pre.textContent = JSON.stringify({
      canvas: [Reveal.getConfig().width, Reveal.getConfig().height],
      revealVersion: Reveal.VERSION,
      slides: out
    });
    document.body.appendChild(pre);
  }
  ready(run);
})();
</script>
"""


def selftest():
    """Prove the checker fails when it should. A checker nobody has seen fail is a
    checker nobody should trust.

    Run this after any change to the probe, and run it once before you trust a
    clean report on a deck you are about to present."""
    src = os.path.join(ROOT, 'master', DECK + '.html')
    if not os.path.exists(src):
        sys.exit('no %s. Render first.' % src)
    html = open(src, encoding='utf8').read()

    # Pick two real slides out of the rendered deck rather than naming them here,
    # so the self-test survives you renaming every slide in the file. Dividers and
    # photo slides are skipped because the report excludes them by design, so a
    # plant on one of those would look like a MISS.
    ids = [m.group(1) for m in re.finditer(
        r'<section[^>]*\bid="([^"]+)"[^>]*>', html)]
    skip = re.compile(r'divider-slide|photo-slide')
    good = []
    for m in re.finditer(r'<section([^>]*)\bid="([^"]+)"([^>]*)>', html):
        attrs = m.group(1) + m.group(3)
        if skip.search(attrs) or m.group(2) == 'title-slide':
            continue
        good.append(m.group(2))
    if len(good) < 2:
        sys.exit('need at least two ordinary slides to plant on; found %d' % len(good))
    bottom_id, right_id = good[0], good[1]

    # Plant a real box past each edge. ⚠️ IT HAS TO BE A BORDER BOX, NOT A MARGIN.
    # The first version of this self-test used `margin-bottom: 200px` and the
    # checker correctly did not flag it, because `getBoundingClientRect()` excludes
    # margins and nothing had actually moved. The self-test was wrong, not the
    # checker. That is the whole reason for having one.
    rig = """<script>
    (function(){
      function r(f){ if(window.Reveal&&Reveal.isReady&&Reveal.isReady())f();
        else setTimeout(function(){r(f);},120); }
      r(function(){
        var plant = function(id, css){
          var sec = document.getElementById(id); if(!sec) return;
          var d = document.createElement('div');
          d.className = 'fit-selftest-plant';
          d.style.cssText = 'position:absolute;width:60px;height:60px;background:red;' + css;
          sec.appendChild(d);
        };
        plant('__BOTTOM__', 'left:40px; top:860px;');   // 200px below a 720px canvas
        plant('__RIGHT__',  'top:100px; left:1420px;'); // 200px right of a 1280px one
      });
    })();
    </script>""".replace('__BOTTOM__', bottom_id).replace('__RIGHT__', right_id)

    tmp = os.path.join(ROOT, 'master', '_fitselftest.html')
    open(tmp, 'w', encoding='utf8').write(html.replace('</body>', rig + PROBE + '</body>', 1))
    try:
        dom = subprocess.run(
            [CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars',
             '--window-size=1280,720', '--virtual-time-budget=20000',
             '--dump-dom', 'file://' + tmp],
            capture_output=True, text=True, timeout=180).stdout
    finally:
        os.remove(tmp)
    m = re.search(r'<pre id="fit-report">(.*?)</pre>', dom, re.S)
    if not m:
        print('SELF-TEST FAILED: the probe did not report at all.')
        return 1
    rep = json.loads(re.sub(r'&quot;', '"', re.sub(r'&amp;', '&', m.group(1))))
    by = {s['id']: s for s in rep['slides']}
    ok = True
    t = by.get(bottom_id)
    if not t or t['v'] >= 0:
        print('SELF-TEST FAILED: a 200px bottom overflow on #%s was not caught '
              '(v=%s).' % (bottom_id, t and t['v'])); ok = False
    else:
        print('  caught the planted bottom overflow on #%s, v=%+.1f' % (bottom_id, t['v']))
    r = by.get(right_id)
    if not r or r['h'] >= -2:
        print('SELF-TEST FAILED: a 200px right overflow on #%s was not caught '
              '(h=%s).' % (right_id, r and r['h'])); ok = False
    else:
        print('  caught the planted right overflow on #%s, h=%+.1f' % (right_id, r['h']))
    print('SELF-TEST:', 'OK' if ok else 'FAILED')
    return 0 if ok else 1


def fences():
    """::: depth per source file. An unclosed fence nests every following slide
    inside the last open one, which is invisible in the .qmd and catastrophic in
    the render."""
    import glob
    bad = 0
    for f in sorted(glob.glob(os.path.join(ROOT, 'master', '*.qmd'))):
        depth, fence = 0, False
        for ln in open(f, encoding='utf8'):
            if ln.startswith('```'):
                fence = not fence; continue
            if fence:
                continue
            if re.match(r'^:::+\s*\{', ln):
                depth += 1
            elif re.match(r'^:::+\s*$', ln):
                depth -= 1
        flag = 'OK' if depth == 0 else '*** UNBALANCED ***'
        if depth:
            bad += 1
        print('%-32s depth %+d  %s' % (os.path.basename(f), depth, flag))
    return 1 if bad else 0


def main():
    if '--self-test' in sys.argv:
        return selftest()
    if '--fences' in sys.argv:
        return fences()
    usb  = '--usb' in sys.argv
    band = 40
    if '--band' in sys.argv:
        band = float(sys.argv[sys.argv.index('--band') + 1])
    name = (DECK + '-usb.html') if usb else (DECK + '.html')
    src  = os.path.join(ROOT, 'master', name)
    if not os.path.exists(src):
        sys.exit('no %s. Render first.' % src)

    html = open(src, encoding='utf8').read()
    if '</body>' in html:
        html = html.replace('</body>', PROBE + '</body>', 1)
    else:
        html += PROBE

    # The probe copy lives beside the real one so its relative asset paths resolve.
    tmp = os.path.join(ROOT, 'master', '_fitcheck.html')
    open(tmp, 'w', encoding='utf8').write(html)
    try:
        # ⚠️ THE BUDGET HAS TO SCALE WITH THE FILE. The usb build is ~9MB with every
        # asset inlined and needs far longer to parse and lay out than the 440KB
        # linked build. At a flat 20s it silently produced no report at all.
        budget = max(20000, int(len(html) / 1024 * 6))
        dom = subprocess.run(
            [CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars',
             '--window-size=1280,720', '--virtual-time-budget=%d' % budget,
             '--dump-dom', 'file://' + tmp],
            capture_output=True, text=True, timeout=600).stdout
    finally:
        os.remove(tmp)

    m = re.search(r'<pre id="fit-report">(.*?)</pre>', dom, re.S)
    if not m:
        if usb:
            sys.exit(
                "Chrome's --dump-dom returns nothing for the usb build, which is %.1fMB\n"
                "with every asset inlined. Tried up to %.0fs. This is a limit of the\n"
                "dump-dom approach on a file that size, not a fault in the deck.\n\n"
                "CHECK THE DEFAULT BUILD INSTEAD, which is what this script does with no\n"
                "arguments. Both builds render from the same .qmd and the same theme; the\n"
                "usb profile changes how assets are EMBEDDED, not how anything is laid\n"
                "out. If you want the usb build verified directly, open it and look."
                % (len(html) / 1048576, budget / 1000))
        sys.exit('the probe did not report after %.0fs. Chrome may have failed to load '
                 'the deck.' % (budget / 1000))
    rep = json.loads(re.sub(r'&quot;', '"', re.sub(r'&amp;', '&', m.group(1))))

    # ⚠️ A SLIDE THAT WAS NEVER MEASURED MUST FAIL LOUDLY. `worstV` starts at 1e9, so
    # a slide whose elements all measured zero-size came back as a huge POSITIVE
    # slack and sailed through as "fine". That is how this script once reported a
    # clean deck while 44 of 54 slides had collapsed into one, after an unclosed
    # `:::` fence nested every following slide inside an earlier one. A checker that
    # passes when it did not run is worse than no checker.
    unmeasured, over, tight = [], [], []
    for s in rep['slides']:
        if s['v'] > 1e8 or s['display'] == 'none':
            unmeasured.append(s)
            continue
        if s['divider'] or s['photo']:
            continue                      # both bleed past the canvas by design
        if s['v'] < 0 or s['h'] < -2:
            over.append(s)
        elif s['v'] < band:
            tight.append(s)

    print('%s · reveal %s · canvas %dx%d · %d slides'
          % (name, rep['revealVersion'], rep['canvas'][0], rep['canvas'][1], len(rep['slides'])))
    print('checked every fragment state; dividers and photo slides excluded, both bleed by design\n')

    if unmeasured:
        print('NOT MEASURED (%d) — THIS IS A FAILURE, NOT A PASS.' % len(unmeasured))
        print('A slide reporting `display: none` here was never laid out, so nothing')
        print('about it has been checked. The usual cause is an UNCLOSED ::: FENCE,')
        print('which nests every following slide inside the last open one. Run the')
        print('fence audit: a `.qmd` whose ::: depth does not return to zero is the')
        print('one to fix.')
        for s in unmeasured[:8]:
            print('  %-22s display=%-6s descendants=%d' % (s['id'], s['display'], s['kids']))
        if len(unmeasured) > 8:
            print('  ... and %d more' % (len(unmeasured) - 8))
        print()

    if over:
        print('OVERFLOWING (%d) — these are off the canvas on every screen:' % len(over))
        for s in over:
            print('  %-22s v=%+7.1f h=%+6.1f  worst at %s, lowest is %s'
                  % (s['id'], s['v'], s['h'], s['at'], s['lowest']))
        print()
    if tight:
        print('UNDER THE CONTROL ICONS (%d) — measured as fitting, but the bottom %dpx'
              % (len(tight), band))
        print('is drawn over by reveal\'s chalkboard, menu and slide-number buttons.')
        print('Look at a screenshot before acting; the picture wins over this number.')
        for s in tight:
            print('  %-22s v=%+7.1f  worst at %s, lowest is %s' % (s['id'], s['v'], s['at'], s['lowest']))
        print()
    if not over and not tight and not unmeasured:
        print('Every slide clears the canvas and the control band.')

    return 1 if (over or unmeasured) else 0


if __name__ == '__main__':
    sys.exit(main())
