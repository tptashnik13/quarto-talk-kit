# Quarto Talk Kit

A conference or job talk, written as a text file and built into reveal.js slides. You edit
Markdown, a theme does the design, and scripts catch the defects that only appear after the
deck is rendered.

**Open `master/talk-usb.html` in any browser to see what it builds.** One file, no install,
works offline. Press `s` for speaker notes, `Esc` for the slide overview, `m` for the menu.

This is a template, not a presentation. Every slide in the demo deck demonstrates one
component, and its speaker notes explain what that component is for and when to reach for
something else. **Every number in it is invented.**

---

## Why bother, when PowerPoint exists

Four things you get here that a slide editor does not give you.

**The deck is text, so it diffs.** You can see what changed between two versions, revert one
slide, and let git carry the history. Nobody emails `talk_final_v3_REAL.pptx` to themselves.

**No number is ever typed onto a slide.** A figure reads a `.csv` that an analysis script
wrote. A number in prose comes from a function call. When the analysis reruns, the slide moves
with it. This is the single biggest source of embarrassment in an academic talk and it is
structurally eliminated here.

**The layout is checked, not eyeballed.** `tools/check_fit.py` measures every slide against
the canvas, in every click state, on both axes. Content hanging off the bottom of a slide is
invisible until it is on a projector, and by then it is the punchline that got cut.

**It works with the wifi off.** No webfont, no CDN, no network call at display time. There is
also a single-file build you can carry on a stick and open on a stranger's laptop.

---

## The fastest way to use this: hand it to an AI agent

This repo is written to be read by a coding agent as much as by a person. The design decisions
are documented **in the files themselves**, next to the code they explain, including the
mistakes that produced them.

You do not have to learn Quarto, SCSS or reveal.js to get a deck out of this. You can describe
the talk you want and let an agent do the wiring.

### What you need

**Claude Code** ([claude.com/claude-code](https://claude.com/claude-code)) or another agent
that can read and edit files in a folder. Cursor, Codex CLI and similar tools work the same
way. A plain chat window without file access will not, because the agent has to read the theme
and run the checks.

### Step one, get the repo onto your machine

```
git clone https://github.com/tptashnik13/quarto-talk-kit.git my-talk
cd my-talk
```

Or download the ZIP from GitHub and unzip it. Then open a terminal in that folder and start
your agent there.

### Step two, paste this to the agent

Everything between the lines. Fill in the bracketed parts first.

---

> I want to build a conference talk from this repository. Before you write anything, read
> `AGENTS.md` in the repository root and follow it. It is the operating manual for this repo
> and it names the traps that will otherwise cost us a render cycle each.
>
> **My talk.** [Describe it. The title, the audience, how long you have, and what the
> argument is. If you have a paper, an abstract or an outline, say where the file is and let
> the agent read it.]
>
> **What I want you to do.**
>
> 1. Read `AGENTS.md`, then `HOW_TO.md`, then `master/talk.qmd` and `master/appendix.qmd`.
>    The demo deck's speaker notes document every component this theme has.
> 2. Confirm Quarto is installed and tell me how to install it if it is not.
> 3. Ask me whatever you need to know about the content before you start writing slides. Do
>    not guess at my argument.
> 4. Replace the demo deck with my talk. Keep the structure of the file, including the setup
>    chunk and the include of the appendix.
> 5. Retheme it to [your colours, or "leave the default"]. Remember that retheming is a
>    two-file change, `theme/talk.scss` and `figures/R/palette.R`.
> 6. Render both builds in the documented order and run every check in `tools/`.
> 7. **Then screenshot every slide and look at them.** Tell me what is wrong. The checks pass
>    defects that render without error.
>
> **Rules for the whole job.**
>
> - **Never type a number onto a slide.** If I give you results, put them in a `.csv` under
>   `figures/data/` and have a figure or a function read it. If I have not given you a number,
>   say so and leave a placeholder. Do not invent one and do not carry one over from the demo
>   deck, where every number is fabricated.
> - **Delete `figures/data/demo_results.csv` and `figures/R/demo_figure.R`** once my own
>   figures exist, so no invented number can survive into my deck.
> - Render the `usb` profile FIRST and the default profile LAST, every time. The other order
>   breaks the presenting deck silently.
> - Tell me what you checked and what you did not. "Verified" with no scope is not something I
>   can act on.

---

### Step three, work with it

Ask for one change at a time and look at the result. "Make slide four a versus instead of two
cards." "The conclusion slide is too full, what comes off it?" "Add an appendix slide that
answers the identification question."

**Look at the deck yourself before you believe it is done.** The agent will run the checks and
report clean. The checks are good and they are not sufficient.

---

## Or do it by hand

`HOW_TO.md` is the guide for a person. It covers installing Quarto, the two builds and why the
order matters, every presenting key, the appendix, the printable notes, and the three defects
this deck has actually shipped with.

The short version:

```
quarto render master/talk.qmd --profile usb   # the one-file fallback, FIRST
rm -rf master/talk_files                      # clear the leftovers
quarto render master/talk.qmd                 # the real deck, LAST

python3 tools/check_fit.py --fences           # instant, run it first
python3 tools/check_blank_slides.py master/talk.html
python3 tools/check_fit.py
```

While drafting, `quarto preview master/talk.qmd` opens a browser that refreshes as you save.

---

## What is in here

| Path | What it is |
|---|---|
| `master/talk.qmd` | The deck. Markdown. `##` starts a slide, `#` a section divider |
| `master/appendix.qmd` | Slides for questions, excluded from the slide count |
| `theme/talk.scss` | The design. **Change four colour values at the top to retheme** |
| `figures/R/palette.R` | The same colours again, for charts. Plotly cannot read CSS variables |
| `figures/R/demo_figure.R` | One chart, showing how a slide reads a `.csv` instead of a number |
| `_quarto.yml` | Deck settings. Every one worth knowing about carries a comment |
| `_quarto-usb.yml` | The single-file build profile |
| `includes/` | Four small scripts. Two fix Quarto quirks, two add interactions |
| `tools/` | The checks and the builders. See below |
| `.claude/skills/` | Two slash commands for Claude Code, `/render-talk` and `/audit-talk` |
| `AGENTS.md` | The operating manual an AI agent should read first |
| `HOW_TO.md` | The guide for a person |

### The tools

| Script | Does |
|---|---|
| `check_fit.py` | Does every slide fit? Both axes, every fragment and click state. `--self-test` proves it still catches a planted overflow. `--fences` audits `:::` balance |
| `check_blank_slides.py` | Catches a slide that renders blank, which passes every other check |
| `build_speaker_notes.py` | Pulls every `::: {.notes}` block into one `.md` and `.docx` to edit or circulate |
| `apply_speaker_notes.py` | Writes the edited document back into the `.qmd` files |
| `build_notes_pdf.py` | A two-column PDF of the notes, sized to a fixed page budget, for your pocket |
| `build_static_deck.py` | Swaps every live chart for a picture. The last-resort build whose figures cannot fail to draw |

---

## Requirements

**Quarto** is the only hard requirement. Install **1.9.x or later**, and check your OS version
against the release notes, because Quarto 1.10 and later ship a component that requires
macOS 14.

**R with `plotly`** only if you want the demo chart. Delete `figures/` and the `source()` line
in the setup chunk and the deck builds without R at all.

**Python 3** for the tools. No packages needed except `python-docx`, and only for the Word
version of the speaker notes. Everything else uses the standard library.

**Google Chrome** for `check_fit.py`, `build_notes_pdf.py` and `build_static_deck.py`, which
drive it headless. The paths are at the top of each script if yours is somewhere unusual.

---

## Before your first talk

1. Render both builds in the documented order
2. Run all three checks
3. Page through every slide and look at it
4. Copy `master/talk-usb.html` to a USB stick
5. **Open that copy on a different machine.** A fallback you have not opened is not a fallback

---

## Licence

MIT. See `LICENSE`. Use it, change it, no attribution required.

The theme's design decisions and the checks came out of building a real 54-slide talk, and
most of the comments in these files record a defect that actually shipped. That is why they
are long. Read the warnings before you remove one.
