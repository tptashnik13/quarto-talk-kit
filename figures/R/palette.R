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
  primary   = "#1B5834",  # Primary accent. The favorable direction in a chart.
  deep      = "#04351B",  # Dark grounds and headings.
  gold      = "#FAB716",  # Emphasis. The unfavorable direction in a chart.
  gold_dark = "#C4900E",  # Gold darkened for strokes on white.
  ink       = "#262626",
  grey      = "#C3CCCE",
  tint      = "#EBF3EE",
  # Diverging ramp, gold (unfavorable) through neutral to primary (favorable).
  ramp_bad  = "#FAB716",
  ramp_bad2 = "#F7E3B2",
  ramp_mid  = "#F2F5F3",
  ramp_good2= "#AFCCBB",
  ramp_good = "#1B5834"
)

# Short names used by the figure scripts.
PRIMARY <- PAL$primary
TEAL  <- PAL$primary   # kept as an alias so older figure scripts keep working
AMBER <- PAL$gold
DEEP  <- PAL$deep
GREY  <- PAL$grey
INK   <- PAL$ink
