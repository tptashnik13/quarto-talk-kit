# AGENTS.md — operating manual for this repository

Read this before editing anything. It is short, and every item in it records a defect that
actually shipped in the deck this kit was built from.

`CLAUDE.md` in this directory is a copy of this file, so Claude Code picks it up
automatically. Keep the two in step.

---

## What this repository is

A Quarto reveal.js presentation, plus a theme, plus the checks that catch what rendering does
not. The deck source is `master/talk.qmd`, which includes `master/appendix.qmd`.

The deck that ships is a **demonstration**, not content. Every slide shows one component and
says so in its own `::: {.notes}` block. Read those notes before you write slides. They are
the component reference.

---

## The four rules

### 1. Never put a number on a slide that a human typed

A figure reads a `.csv`. A number in prose comes from an `r ...` call. Nothing in between
holds a literal.

This is not fastidiousness. A hardcoded N survives a database update and the figure beside it
does not, and then the two disagree on a screen in front of a room. If you are handed a number
with no file behind it, **say so and leave a placeholder.** Do not round from memory, do not
carry one over from the demo deck, and do not write "approximately".

**Every number in `figures/data/demo_results.csv` is invented.** Delete that file and
`figures/R/demo_figure.R` as soon as the user's own figures exist.

### 2. Render the usb profile FIRST and the default profile LAST

```
quarto render master/talk.qmd --profile usb
rm -rf master/talk_files
quarto render master/talk.qmd
```

An `embed-resources` render deletes `master/talk_files/` after inlining its contents. Both
builds share one input and therefore one `_files/`, so the other order leaves the presenting
deck pointing at a directory that no longer exists.

**The failure is silent.** The deck opens, every slide is there, nothing errors. But the cards
stack instead of sitting side by side, the headings are small and the colours are gone,
because the whole theme failed to load. Re-render in the right order and it comes back.

### 3. Run the cheap structural check before the expensive visual one

```
python3 tools/check_fit.py --fences        # instant
python3 tools/check_blank_slides.py master/talk.html
python3 tools/check_fit.py
```

An unclosed `:::` fence nests every following slide inside the last open one. On a real deck
this put 44 of 54 slides inside one section, and **the fit check reported CLEAN**, because a
slide that was never laid out came back as enormous positive slack. `--fences` takes no time
and catches it. Run it after any edit to a `.qmd`, before rendering.

### 4. Then look at the deck

Screenshot every slide and page through them. Three classes of defect pass every check above.

- **An absolutely-positioned `::after`.** Not in `querySelectorAll('*')`, and overlap is not
  overflow, so a logo sitting on top of an author's name reports clean.
- **A line break in an ugly place.** Fits perfectly, reads badly.
- **A blank slide**, which has nothing to overflow and nothing to misalign.

**When a screenshot and a number disagree, the screenshot wins.**

A clean report from a checker you have not seen fail is worth nothing. `check_fit.py
--self-test` plants a real overflow and proves the checker still catches it. Run it if you
change the probe.

---

## Choosing a component

The theme has four layout components. **Pick by what the content is, not by what the last
slide used.** A deck built out of one component gets box fatigue, where each slide looks fine
alone and together they read as one slide shown eight times.

| Component | Use it for |
|---|---|
| `::: {.cards}` | Two or three parallel objects of equal weight. Three is the maximum |
| `::: {.versus}` | A genuine binary. Two columns, one hairline, no boxes |
| `::: {.keylines}` | A short list of points. Rule-separated rows, no boxes. **The default** |
| `::: {.statement}` | One sentence that deserves silence around it. Use it two or three times in a deck |

Add `.tight` to any of them when the slide also has a title and a second block, so the
component shares the slide rather than filling it.

`.cards` is the one people overuse. Reach for `.keylines` unless the items really are parallel
objects.

---

## Click handler or fragment

Two interactive components ship here and the choice between them is about **where the user's
hands will be**.

| | Fires from | Can close | Order |
|---|---|---|---|
| `includes/card-expand.html` | mouse or keyboard | yes | any |
| `includes/spotlight-swap.html` | the podium clicker | no | linear |

A presentation clicker drives reveal's next and prev and nothing else. **Anything that has to
happen while the speaker is away from the laptop must be a fragment.**

⚠️ **Do not implement either of these with CSS `:has()`.** A `:has(.fragment.visible)` rule
against a class reveal adds at runtime fires on BACKWARD arrival and not on forward clicks,
and forward is the direction people present in. Read reveal's state from its own
`fragmentshown` and `fragmenthidden` events. Do not count clicks.

⚠️ **If you add a click-driven component, teach `check_fit.py` about it.** Add its selector to
the `openers` query and reproduce its handler's **full** class contract, not an approximation.
A checker that toggles one class invents states the deck cannot reach and reports overflow
that is not there. A checker that cries wolf gets ignored.

---

## Retheming is a two-file change

`theme/talk.scss` drives the CSS. `figures/R/palette.R` drives the charts. **Plotly cannot
read CSS variables**, so the colours are stated twice on purpose.

Change one and not the other and you get a retheme with every chart still in the old colours.
It is easy to miss on a laptop and obvious on a projector.

The four values at the top of `theme/talk.scss` are all you normally need.

---

## Things that will surprise you

**Quarto emits anything between the YAML header and the first `##` as its own slide, and an
HTML comment counts as content.** Notes written up there produce a permanently blank slide 2.
Put them inside the `include: false` setup chunk, where they cannot be emitted.

**Quarto lowercases SVG attribute names** when it re-serializes the document to split slides.
`viewBox` becomes `viewbox` and stops scaling; `markerWidth` becomes `markerwidth` and
arrowheads vanish. It fails silently and a ```` ```{=html} ```` raw block does not avoid it.
`includes/svg-case-fix.html` repairs it in the DOM. Wrap a hand-written SVG in a div with
class `hand-svg` so the fix reaches it.

**Pandoc wraps a line of `[]{.class}` spans in a paragraph.** So a div containing them has
exactly one child, and flexing the div lays out that single `<p>` rather than the spans. The
general shape of most Pandoc layout surprises is that the element you styled is not the
element that got your content.

**Never size a slide component in `vh`.** The reveal canvas is a fixed 1280x720 scaled by one
CSS transform. `vh` resolves against the real browser viewport, so on a large display 68vh
becomes about 880px on a 720px slide and the content is pushed out of view. The slide renders
as blank white with no error anywhere. **Use canvas pixels.**

**`maxScale: 1.0` in `_quarto.yml` is a correctness setting.** Above a scale of 1, Chrome
stops painting most of every Plotly figure. Axis labels go first, then the chart is cropped,
and the visible fraction is exactly `1/scale`. The DOM is provably correct at every size, so
`check_fit.py` cannot catch it and never will. It is a paint failure, not a layout one. The
cost is white bars on a large display, and that is the right trade.

**Quarto generates the title slide from the YAML**, so there is nowhere in the `.qmd` to
attach notes to it. `includes/title-slide-notes.html` injects them instead.

---

## How to report what you did

Say **which slides you checked, against which tool, and which you did not.** "Verified" with
no scope is not a claim anyone can act on.

If a check failed, say so and quote the output. If you skipped a step, say which one. A
rendered deck with one unfixed overflow, reported, is worth more than a clean report that is
not true.
