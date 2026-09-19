# The demo deck's one chart: two groups over four waves, with error bars.
#
# ⚠️⚠️ THE NUMBERS IN figures/data/demo_results.csv ARE INVENTED. They exist to
# show the plumbing. Delete them before this repo becomes your deck.
#
# THE PATTERN WORTH COPYING, and it is the only rule here that matters:
#
#   NEVER TYPE A NUMBER INTO A SLIDE.
#
# A figure reads a .csv that some analysis script wrote. A slide calls the
# figure. Nothing in between holds a number a human typed. That means a rerun
# that moves a coefficient moves the slide too, and it means you can answer
# "where did that come from" by naming a file rather than by remembering.
#
# The same goes for any number in the PROSE of a slide. Compute it in a chunk
# and interpolate it with `r ...` rather than writing the digits out. A hardcoded
# N survives a database update; the figure beside it does not, and then the two
# disagree on the screen in front of a room.
#
# WHY THE FIGURE IS SIZED HERE AND NOT IN CSS. reveal's canvas is a fixed
# 1280x720 that is scaled by one CSS transform. Plotly measures itself in real
# browser pixels, so a figure sized in a relative unit resolves against the
# window rather than the canvas and lands at the wrong size on every display but
# yours. State the size in canvas pixels, here, once.

library(plotly)
source(file.path("..", "figures", "R", "palette.R"))

demo_figure <- function() {

  d <- read.csv(file.path("..", "figures", "data", "demo_results.csv"),
                stringsAsFactors = FALSE)

  cols <- c(Treatment = PAL$primary, Control = PAL$grey)

  p <- plot_ly(width = 900, height = 430)

  for (g in c("Control", "Treatment")) {
    dg <- d[d$group == g, ]
    p <- add_trace(
      p, data = dg, x = ~wave, y = ~estimate, name = g,
      type = "scatter", mode = "lines+markers",
      line   = list(color = cols[[g]], width = 4),
      marker = list(color = cols[[g]], size = 11),
      error_y = list(array = dg$se, color = cols[[g]], thickness = 1.5, width = 6),
      hovertemplate = paste0(g, ", wave %{x}<br>%{y:.2f}<extra></extra>")
    )
  }

  layout(
    p,
    # A transparent paper lets the slide's own ground show through. Set it to
    # white and the chart sits in a visible rectangle on any tinted slide.
    paper_bgcolor = "rgba(0,0,0,0)",
    plot_bgcolor  = "rgba(0,0,0,0)",
    font   = list(family = "Helvetica Neue, Arial, sans-serif",
                  size = 17, color = PAL$ink),
    margin = list(l = 60, r = 20, t = 10, b = 50),
    xaxis  = list(title = "Wave", dtick = 1, zeroline = FALSE,
                  showgrid = FALSE, linecolor = PAL$grey),
    yaxis  = list(title = "Estimate", zeroline = FALSE,
                  gridcolor = "#EDF1F4", rangemode = "tozero"),
    legend = list(orientation = "h", x = 0, y = 1.12,
                  bgcolor = "rgba(0,0,0,0)")
  ) |>
    # The mode bar is a row of Plotly's own icons in the corner. Nobody needs it
    # on a projector and it is the first thing a photograph of your slide shows.
    config(displayModeBar = FALSE, staticPlot = FALSE)
}
