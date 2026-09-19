---
name: render-talk
description: Render this Quarto reveal.js deck and verify it is genuinely presentable. Use when the user says "render the talk", "build the deck", "rebuild the slides", "make the USB version", or after editing any .qmd. Produces both the presenting build and the single-file fallback, in the order that matters, then checks the failure modes that only appear after rendering.
argument-hint: "[deck path; defaults to master/talk.qmd]"
allowed-tools: ["Read", "Bash", "Glob", "Grep"]
---

# Render the deck

## The two builds, and why there are two

revealjs's chalkboard plugin is **incompatible with `embed-resources: true`**. Quarto errors
rather than picking for you. So every deck renders twice.

| Build | Command | Output | Chalkboard |
|---|---|---|---|
| **Presenting** | `quarto render master/talk.qmd` | `talk.html` + `talk_files/` | yes |
| **USB fallback** | `quarto render master/talk.qmd --profile usb` | one `talk-usb.html` | no |

The presenting build is what the user presents from. The USB build goes on a stick as
insurance and must be regenerated whenever the presenting build changes, or they will hand
someone a stale deck under pressure.

## Render the USB build FIRST. This is not stylistic.

An `embed-resources` render deletes the `_files/` directory after inlining its contents. Both
builds share one input file and therefore one `_files/`, so running them presenting-first
leaves the presenting `.html` pointing at a directory the USB render just removed.

**What that failure looks like, so you recognise it.** The deck opens. Every slide is there.
Nothing errors. But the cards are stacked instead of side by side, the headings are small, and
the colours are gone, because the whole theme silently failed to load. Nothing is broken.
Re-render the default profile last and it comes back.

**Always: `--profile usb` first, `rm -rf master/talk_files`, then the plain render.**

## Steps

1. **Check fences before rendering.** `python3 tools/check_fit.py --fences` is instant. An
   unclosed `:::` nests every following slide inside the last open one, and once made a fit
   check report CLEAN while 44 of 54 slides had collapsed into one. Run the cheap structural
   check before the expensive visual one.

2. **Render both builds, USB first.** Report any error verbatim rather than summarizing it.
   Quarto's SCSS and plugin errors name the exact cause.

3. **Verify the presenting build:**
   - `talk.html` exists and `talk_files/` exists beside it
   - `grep -oE 'src="https?://' master/talk.html` returns **nothing**. Any hit is a resource
     fetched at display time and will fail on a disconnected podium. `href` hits inside a
     Plotly bundle are attribution links, not loads, and are fine.

4. **Verify the USB build:**
   - Exactly one `.html`, **no** `_files/` directory beside it
   - Copy it alone to a temp directory and confirm it still opens. A single file that only
     works in its build directory is not a fallback.

5. **Run the checks.** `python3 tools/check_blank_slides.py master/talk.html`, then
   `python3 tools/check_fit.py`.

6. **Report** both output paths, both sizes, the external-reference count, and the check
   results.

## What this skill does not do

It does not check layout by eye, and it does not check content. Rendering succeeds on a deck
with the punchline hanging off the bottom of the slide. Run `/audit-talk` after this, always.
