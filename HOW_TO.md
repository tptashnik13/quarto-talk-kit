# HOW_TO — building a talk with this kit

Written for a person. The agent's instructions are in `AGENTS.md`.

---

## Installing Quarto

Quarto is the tool that turns a text file into slides. Get it from
[quarto.org/docs/get-started](https://quarto.org/docs/get-started/).

**Check your OS version against the release you install.** Quarto 1.10 and later ship a
component that requires macOS 14. On an older Mac it installs without complaint and then
fails the first time you render, with an error that never mentions your OS version. 1.9.38 is
the last release that works on macOS 12.

### Installing without an admin password

If you cannot run an installer, Quarto unpacks into your home folder from the same `.pkg`.

```
mkdir -p ~/.local/quarto && cd ~/.local/quarto
pkgutil --expand ~/Downloads/quarto-1.9.38-macos.pkg /tmp/qx
cat /tmp/qx/quarto-core.pkg/Payload | gunzip -dc | cpio -i --quiet
ln -sf ~/.local/quarto/bin/quarto ~/.local/bin/quarto
```

Nothing else on the system is touched, and uninstalling is `rm -rf ~/.local/quarto`. Make
sure `~/.local/bin` is on your `PATH`.

Check it worked:

```
quarto --version
quarto check        # every dependency should say OK
```

---

## Making slides

The deck is a text file, `master/talk.qmd`. Write in plain Markdown. `##` starts a new slide.
A slide with `.divider-slide` is a full-bleed section break.

**While drafting**, this is better than rendering repeatedly. It opens a browser that
refreshes as you save.

```
quarto preview master/talk.qmd
```

**To build it properly:**

```
quarto render master/talk.qmd --profile usb
rm -rf master/talk_files
quarto render master/talk.qmd
```

**Both commands, in that order, every time.** They produce two different things and the order
is not optional. See below.

---

## Why two builds

| | What it is | Use it for |
|---|---|---|
| `master/talk.html` **+ `talk_files/`** | A folder | **Presenting.** Has the chalkboard |
| `master/talk-usb.html` | One single file | **The backup on the USB stick.** No chalkboard |
| `master/talk-static_<date>.html` | One single file | **The last resort.** Charts are pictures, so they cannot fail to draw |

Slides that let you draw on them cannot also be squeezed into a single file. That is a hard
limitation in reveal.js, not a setting anyone chose. So there are two.

Present from the folder. Carry the single file as insurance, because one file always opens on
any machine, and a folder can lose its `_files` directory in transit and then renders as
unstyled text.

**Neither build needs the internet.**

### The order is not cosmetic

The `usb` profile produces a single self-contained file and clears `master/talk_files/` on its
way out. The default build needs that directory, because it keeps its CSS and JavaScript there
rather than inlining them. Render `usb` second and the default deck is left pointing at a
stylesheet that is no longer on disk.

**What that failure looks like, so you recognise it.** The deck opens. Every slide is there.
Nothing errors. But the cards are stacked instead of side by side, the headings are small, and
the colours are gone, because the whole theme silently failed to load. It looks like the deck
broke. Nothing broke. Re-render the default profile last and it comes back.

This was found while auditing layout, after four slides were measured against an unstyled page
and read as fitting when they did not.

### The static build

```
python3 tools/build_static_deck.py
```

It takes the usb build and swaps every live chart for a picture captured from that same chart.
**It must run AFTER the usb build, because it reads it.** A static deck built first is a copy
of the previous deck.

You lose everything inside a chart, meaning hover tooltips and any click target the chart
itself draws. Everything outside the charts still works.

---

## Presenting

| Key | Does |
|---|---|
| `s` | **Presenter view.** Your notes and a timer, on your screen only |
| **`c`** | **Draw directly on the slide.** Everything stays visible underneath. `c` again to put the pen away |
| `b` | Blank chalkboard *over* the slide, hiding it. Rarely what you want |
| `x` / `y` | Next / previous pen colour |
| `DEL` | Erase what you drew on this slide |
| `m` | Menu. Searchable list of every slide, including the appendix |
| a number, then Enter | Jump straight to that slide |
| `Esc` | Grid of all slides. Escape again to go back |
| `f` | Fullscreen |

**`c` is the one you want for annotating a figure.** It drops a transparent layer over the
current slide, so you can circle a coefficient or draw an arrow on a plot while the audience
still sees the plot. `b` is a different thing, an opaque board that covers the slide, for when
you want to work something out from scratch.

**On presenter view:** it opens a second browser window. If your laptop is *extending* to the
projector, the room may see the wrong window. **Mirror the displays instead**, or check it in
the room before you start.

**The deck will not fill a large screen, and that is on purpose.** You will see white bars
around the edges on any display bigger than 1280x720. The deck is pinned to its native size
deliberately, because scaled up beyond it the browser stops drawing most of every chart and
the axis labels vanish. The bars are the fix, not a fault.

---

## The appendix

Everything in `master/appendix.qmd` is marked `visibility="uncounted"`. Those slides do not
count toward the progress bar and the audience never sees them unless you go there.

They exist for questions. Someone asks about identification, you type the slide number, and
the answer is on the screen instead of in a sentence you improvise.

**Learn the numbers for three or four of them.** Hunting through a menu while a senior person
waits costs you more than the slide gains you. Write the numbers on a card.

---

## Speaker notes

Notes live in `::: {.notes}` blocks inside each slide. That is a bad place to write them and a
good place to keep them, so there is a round trip.

```
python3 tools/build_speaker_notes.py
```

Writes `speaker_notes_<date>.md` and `.docx` with every note in deck order. Edit the document,
or send it to a coauthor, then:

```
python3 tools/apply_speaker_notes.py speaker_notes_<date>.md --dry-run
python3 tools/apply_speaker_notes.py speaker_notes_<date>.md
```

The heading line is the contract. **Do not edit a heading**, because the slide id in it is
what each block is keyed on. The `ON SCREEN` blocks are reference only and are never read
back.

### The printed notes, for your pocket

```
python3 tools/build_notes_pdf.py
```

A two-column PDF of every speaker note, slide number and title as the header. Made to be
printed and carried as a backup in case the deck or the laptop lets you down. Slides with no
notes are left out, so the numbers skip.

**Re-run it after any notes edit**, because it reads the `.qmd` files directly and nothing
updates it for you.

**If it says OVER BUDGET**, the notes grew past `MAX_PAGES`. Open the script and lower
`FONT_PT` by a few tenths. Nothing else needs touching.

**It takes about twenty seconds and looks like it has frozen near the end.** That is normal.
Chrome finishes the PDF and then refuses to quit, so the script waits for the file and then
stops Chrome itself.

---

## Changing how it looks

`theme/talk.scss`. The first four colour values control everything else.

⚠️ **Retheming is a two-file change.** Change `figures/R/palette.R` too, because Plotly cannot
read CSS variables and its colours have to be stated separately. Change only the SCSS and you
get a retheme with every chart still in the old colours, which is easy to miss on a laptop and
obvious on a projector.

Slide dimensions and behaviour are in `_quarto.yml`, which has a comment on every setting
worth knowing about.

### Adding your institution's logo

Uncomment the `&::after` block inside `#title-slide` in `theme/talk.scss` and paste your own
base64 SVG.

**Use a vector, not a PNG.** A raster mark is crisp only at or below its native size. Render a
230x93 PNG at 300px wide and it is a 1.3x upscale, which a 1080p projector then scales again.

⚠️ **Set `padding-bottom` on `#title-slide` to match.** It is 0 because no mark ships. The
mark is absolutely positioned, so no layout check can see it, and without that padding it
lands on top of your affiliation and every check still reports clean. **Look at a screenshot
after you add it.**

---

## Before a talk

1. `python3 tools/check_fit.py --fences` — instant, run it first
2. Render both builds, usb first
3. `python3 tools/check_blank_slides.py master/talk.html`
4. `python3 tools/check_fit.py`
5. **Page through every slide and look at it**
6. Copy `master/talk-usb.html` to a USB stick
7. **Open that copy on a different machine** to confirm it works

---

## Three defects this deck has actually shipped with

Each of these survived every automated check of its day. They are the reason step 5 above is
not optional.

**A blank slide 2, from the day the deck was built.** Quarto turns *anything* between the YAML
header and the first `##` into its own slide, and an HTML comment counts. The design notes
that used to sit up there were producing a permanently blank slide. It has nothing to
overflow, nothing to misalign and no text to proofread, so every layout audit passed it. It is
only visible if you page through the deck and count. `tools/check_blank_slides.py` now catches
it, and the notes live inside the `include: false` setup chunk where they cannot be emitted.

**Every slide cut off on the right, for weeks.** reveal gives each slide `width: 100%` against
a fixed 1280px canvas. The theme adds padding on each side, and because the browser default is
`content-box` that padding was **added** to 1280 instead of taken out of it. Every slide
rendered 1346px wide inside a 1280px frame and lost 66px off the right. One line fixed it,
`box-sizing: border-box`. It lasted so long because every layout audit measured whether slides
were too TALL and none measured whether they were too WIDE. **Check both edges.**

**An unclosed `:::` fence nested 44 of 54 slides inside one.** The fit check reported the deck
CLEAN, because a slide that was never laid out came back as enormous positive slack rather
than as a failure. The checker now fails loudly on any slide it did not measure, and
`--fences` catches the cause in no time at all. **Run the cheap structural check before the
expensive visual one.**
