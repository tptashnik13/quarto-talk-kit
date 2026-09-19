---
name: audit-talk
description: Adversarial layout audit of a rendered reveal.js deck. Flags overflow, font drift, box fatigue, spacing, contrast, and slide-count/time budget problems. Use when the user says "audit the talk", "check the layout", "does this overflow", "is this too long", or before any rehearsal. Checks appearance only.
argument-hint: "[deck path; defaults to master/talk.html]"
allowed-tools: ["Read", "Grep", "Glob", "Bash"]
---

# Layout audit

**Render first.** Overflow does not exist until the deck is laid out, so auditing a `.qmd`
alone finds nothing. If there is no `.html` newer than the `.qmd`, run `/render-talk` first.

## Run the tools before you form an opinion

```
python3 tools/check_fit.py --fences        # instant, run it first
python3 tools/check_blank_slides.py master/talk.html
python3 tools/check_fit.py
```

`check_fit.py` measures every slide, in every fragment state and every click-driven open
state, against the 1280x720 canvas on both axes. It is screen-independent, and the docstring
explains why.

**Then look at the deck.** Screenshot every slide and page through them. Three classes of
defect pass every one of these checks:

- **An absolutely-positioned `::after`.** A pseudo-element is not in `querySelectorAll('*')`
  and overlap is not overflow, so a mark sitting directly on top of an author's name reports
  clean.
- **A line break in an ugly place.** Fits perfectly, reads badly.
- **A blank slide.** Nothing to overflow, nothing to misalign.

When a screenshot and a number disagree, the screenshot wins.

## What to audit

**OVERFLOW.** The most common defect and the most damaging, because the cut-off content is
usually the punchline at the bottom of the slide. Suspect any slide with more than about six
rows, a figure plus more than three points, or a table over about eight rows.

**TIME BUDGET.** A campus talk is typically 45 minutes of content and 15 of questions. At
roughly a minute a slide, **flag anything over about 45 counted slides.** Appendix slides
marked `visibility="uncounted"` do not count and should not be counted against the user, which
is the whole point of them. Report counted and uncounted separately.

**FONT DRIFT.** Inline `font-size` overrides scattered through the deck. Each one is a place
someone fixed overflow by shrinking text instead of cutting it. Never below `0.85em`.

**BOX FATIGUE.** Two or more coloured callout boxes on one slide, or the same component on
more than about a third of the slides. The emphasis cancels out. `.cards` is the one people
overuse; `.keylines`, `.versus` and `.statement` exist so it does not have to carry everything.

**CONTRAST.** Anything relying on a light stroke or a pale fill. Seminar-room projectors are
badly calibrated and wash out exactly those. The theme palette is chosen for this and inline
colour overrides defeat it.

## The spacing-first fix order

Never open with a font-size reduction. In order:

1. **Cut content.** A slide that is too full is usually saying two things.
2. Reduce vertical spacing with negative margins
3. Consolidate lists
4. Move displayed equations inline
5. Reduce figure size
6. Last resort only: font size, never below `0.85em`

## Report format

By slide, with severity, the specific problem, and the specific fix. Not a general note that
the deck "could be tightened" — name the slide and say what comes off it.
