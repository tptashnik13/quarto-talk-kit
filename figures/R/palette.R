# Deck palette for the Plotly figures.
#
# ⚠️ ONE OF TWO PLACES COLOURS LIVE. The other is the `:root` custom-property
# block near the top of theme/talk.scss, which drives the CSS and any hand-drawn
# SVG. Plotly cannot read CSS variables, so its colours have to be stated here
# as literals.
#
# TO RETHEME: edit BOTH files. Keep them in step or the figures drift away from
# the slides around them, which is easy to miss on a laptop and obvious on a
# projector.
#
# THE RULE THAT MAKES A PALETTE WORK: one colour carries the deck and the second
# is held back. Here `primary` does the structural work and `gold` is rare, so
# the eye goes to it because it is rare. If you use both equally you have no
# emphasis left to spend.

PAL <- list(
  primary   = "#1F4E79",  # Primary accent. The favorable direction in a chart.
  deep      = "#10243A",  # Dark grounds and headings.
  gold      = "#E0A106",  # Emphasis. The unfavorable direction in a chart.
  gold_dark = "#B87F05",  # Gold darkened for strokes on white.
  ink       = "#262626",
  grey      = "#C3CCCE",
  tint      = "#EAF0F6",
  # Diverging ramp, gold (unfavorable) through neutral to primary (favorable).
  ramp_bad  = "#E0A106",
  ramp_bad2 = "#F6E0AE",
  ramp_mid  = "#F2F4F6",
  ramp_good2= "#AEC2D6",
  ramp_good = "#1F4E79"
)

# Short names used by the figure scripts.
TEAL  <- PAL$primary
AMBER <- PAL$gold
DEEP  <- PAL$deep
GREY  <- PAL$grey
INK   <- PAL$ink
