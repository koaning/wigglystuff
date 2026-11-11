# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "altair",
#     "dicekit==0.3.0",
#     "marimo",
#     "pandas",
#     "wigglystuff==0.5.39",
# ]
# ///

import marimo

__generated_with = "0.24.0"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # How dicekit orders dice

    Roll a few dice, say a d4, a d6 and a d8, and sort them: how often is the highest
    die a 5? How often is the second highest a 3? [dicekit](https://pypi.org/project/dicekit/)
    answers this with `ordered(d4, d6, d8)`, which returns one `Dice` per position,
    highest first.

    The obvious approach looks at every possible roll: $4 \times 6 \times 8 = 192$ for
    these three, and the count multiplies with every die you add. dicekit uses a trick
    that never looks at a single roll.
    """)
    return


@app.cell
def _(dice_pick):
    dice_pick.hstack(justify="start", gap=1.5)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Brute force: one roll at a time

    Loop over every roll, sort it, and add 1 to one cell per row of the answer table
    (outlined). The grid below the code has one cell per possible roll.
    """)
    return


@app.cell
def _(
    DICE,
    EsmWidget,
    GRID_H,
    StateViewer,
    TABLE_CSS,
    TABLE_JS,
    answer_html,
    brute_force,
    grid_svg,
    mo,
):
    brute_viewer = StateViewer(
        brute_force,
        args=(DICE,),
        max_steps=100_000,
        interval_ms=20,
        sync_throttle_ms=50,
        timeline_func=lambda work: work,
        timeline_label="rolls handled",
        show_code=False,
    )
    # The grid of rolls and the answer table, drawn together below the code.
    brute_picture = EsmWidget(
        TABLE_JS, css=TABLE_CSS, data={"html": ""}, width=0, height=GRID_H + 70 + 32 * len(DICE)
    )

    # A plain widget updated through `observe`, so no cell reruns while playing.
    def redraw_brute(_=None):
        state = brute_viewer.state or {}
        cells = {(j, face) for j, face in enumerate(state.get("ranked") or [])}
        brute_picture.data = {
            "html": grid_svg(state.get("roll"), state.get("work", 0))
            + answer_html(state.get("result"), cells=cells)
        }

    brute_viewer.observe(redraw_brute, names="step")
    redraw_brute()
    mo.vstack([brute_viewer, brute_picture])
    return


@app.cell
def _():
    import time
    from itertools import product

    import altair as alt
    import marimo as mo
    import pandas as pd
    from dicekit import Dice, ordered

    from wigglystuff import EsmWidget, StateViewer

    return Dice, EsmWidget, StateViewer, alt, mo, ordered, pd, product, time


@app.cell
def _(mo):
    dice_pick = mo.ui.dictionary(
        {f"d{sides}": mo.ui.checkbox(value=sides in (4, 6, 8), label=f"d{sides}") for sides in (4, 6, 8, 10)}
    )
    return (dice_pick,)


@app.cell
def _(dice_pick, mo):
    _picked = [int(name[1:]) for name, on in dice_pick.value.items() if on]
    mo.stop(not _picked, mo.md("**Pick at least one die.**"))
    DICE = [list(range(1, sides + 1)) for sides in _picked]
    NAMES = [f"d{sides}" for sides in _picked]
    POSITIONS = ["highest", "2nd highest", "3rd highest", "4th highest"][: len(DICE)]
    HOT = "#f97316"
    return DICE, HOT, NAMES, POSITIONS


@app.cell
def _(product):
    def brute_force(dice):
        result = [{} for _ in dice]
        work = 0
        for roll in product(*dice):
            ranked = sorted(roll, reverse=True)
            for j, face in enumerate(ranked):
                result[j][face] = result[j].get(face, 0) + 1
            work += 1
        return result

    return (brute_force,)


@app.cell
def _(DICE, HOT, NAMES):
    # Up to four dice: the last die runs along the columns of a panel, the one before
    # it down the rows; a third die picks the panel column, a fourth the panel row.
    PANEL_ROWS, PANEL_COLS, ROWS, COLS = [1] * (4 - len(DICE)) + [len(die) for die in DICE]
    GAP = 14
    LEFT = 90 if PANEL_ROWS > 1 else 40
    CELL = max(6, min(22, (640 - LEFT - (PANEL_COLS - 1) * GAP) // (PANEL_COLS * COLS)))
    PANEL_W, PANEL_H = COLS * CELL, ROWS * CELL
    TOP = 64 if PANEL_COLS > 1 else 44
    GRID_W = LEFT + PANEL_COLS * PANEL_W + (PANEL_COLS - 1) * GAP
    GRID_H = TOP + PANEL_ROWS * PANEL_H + (PANEL_ROWS - 1) * GAP + 50

    def panel_xy(pr, pc):
        return LEFT + pc * (PANEL_W + GAP), TOP + pr * (PANEL_H + GAP)

    def grid_svg(roll, work):
        """One cell per possible roll: the `work` handled ones grey, `roll` orange."""
        total = PANEL_ROWS * PANEL_COLS * ROWS * COLS
        width = max(GRID_W, 620)

        def labelled(i, n):
            # Tiny cells only get their first and last face labelled.
            return CELL >= 14 or i in (0, n - 1)

        parts = [
            f'<svg width="{width}" height="{GRID_H}" viewBox="0 0 {width} {GRID_H}" '
            f'style="color: inherit; font-family: sans-serif">',
            f'<text x="0" y="16" font-size="14" fill="currentColor">rolls handled: '
            f'<tspan font-weight="bold">{work}</tspan> of {total}</text>',
            '<g font-size="10" text-anchor="middle" fill="currentColor">',
        ]
        # Face labels: the panel-column die on top, the panel-row die on the left.
        for pc in range(PANEL_COLS):
            x0, _ = panel_xy(0, pc)
            if PANEL_COLS > 1:
                parts.append(
                    f'<text x="{x0 + PANEL_W / 2}" y="{TOP - 22}" font-size="11">{NAMES[-3]} = {DICE[-3][pc]}</text>'
                )
            for col, face in enumerate(DICE[-1]):
                if labelled(col, COLS):
                    parts.append(f'<text x="{x0 + col * CELL + CELL / 2}" y="{TOP - 6}">{face}</text>')
        for pr in range(PANEL_ROWS):
            _, y0 = panel_xy(pr, 0)
            if PANEL_ROWS > 1:
                parts.append(
                    f'<text x="4" y="{y0 + PANEL_H / 2 + 4}" font-size="11" text-anchor="start">{NAMES[0]} = {DICE[0][pr]}</text>'
                )
            if ROWS > 1:
                for row, face in enumerate(DICE[-2]):
                    if labelled(row, ROWS):
                        parts.append(
                            f'<text x="{LEFT - 8}" y="{y0 + row * CELL + CELL / 2 + 3}" text-anchor="end">{face}</text>'
                        )
        axes = f"rows: {NAMES[-2]}, columns: {NAMES[-1]}" if ROWS > 1 else f"columns: {NAMES[-1]}"
        parts.append(
            f'<text x="{GRID_W}" y="{GRID_H - 36}" text-anchor="end" opacity="0.5">{axes}</text></g><defs>'
        )
        # Rolls are visited in reading order, so the handled ones form a run per grid row.
        # Tiling patterns draw those runs as cells while keeping the SVG small.
        for pr in range(PANEL_ROWS):
            for pc in range(PANEL_COLS):
                x0, y0 = panel_xy(pr, pc)
                for name, opacity in [("todo", 0.07), ("done", 0.35)]:
                    parts.append(
                        f'<pattern id="{name}-{CELL}-{pr}-{pc}" x="{x0}" y="{y0}" width="{CELL}" '
                        f'height="{CELL}" patternUnits="userSpaceOnUse"><rect x="1" y="1" '
                        f'width="{CELL - 2}" height="{CELL - 2}" fill="currentColor" '
                        f'opacity="{opacity}"/></pattern>'
                    )
        parts.append("</defs>")
        for pr in range(PANEL_ROWS):
            for pc in range(PANEL_COLS):
                x0, y0 = panel_xy(pr, pc)
                parts.append(
                    f'<rect x="{x0}" y="{y0}" width="{PANEL_W}" height="{PANEL_H}" '
                    f'fill="url(#todo-{CELL}-{pr}-{pc})"/>'
                )
                for row in range(ROWS):
                    first = ((pr * PANEL_COLS + pc) * ROWS + row) * COLS
                    handled = max(0, min(COLS, work - first))
                    if handled:
                        parts.append(
                            f'<rect x="{x0}" y="{y0 + row * CELL}" width="{handled * CELL}" '
                            f'height="{CELL}" fill="url(#done-{CELL}-{pr}-{pc})"/>'
                        )
        if roll is not None:
            pr, pc, row, col = [0] * (4 - len(DICE)) + [DICE[i].index(face) for i, face in enumerate(roll)]
            x0, y0 = panel_xy(pr, pc)
            parts.append(
                f'<rect x="{x0 + col * CELL + 1}" y="{y0 + row * CELL + 1}" width="{CELL - 2}" '
                f'height="{CELL - 2}" fill="{HOT}"/>'
            )
            ranked = sorted(roll, reverse=True)
            parts.append(
                f'<text x="0" y="{GRID_H - 10}" font-size="13" fill="currentColor">'
                f"roll {tuple(roll)} → sorted, then +1 per row below</text>"
            )
        parts.append("</svg>")
        return "".join(parts)

    return GRID_H, grid_svg


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## The trick: turn order into counting

    1. **Ask "at least" instead of "exactly".** The highest is exactly 5 when it is at
       least 5 but not at least 6, so one subtraction turns one into the other.
    2. **"At least" only depends on a count.** The $j$-th highest is at least $t$ exactly
       when at least $j$ dice show $t$ or more. For a threshold $t$, every die is just a
       *yes* (shows $\geq t$) or a *no*, and only the number of yeses matters.
    3. **Count yeses one die at a time.** The table below keeps, for the dice added so
       far, how many rolls have 0, 1, 2, … yeses. Each count either stays (the next
       die says no) or moves one cell right (it says yes). When two counts land on the
       same cell they **merge**: from then on it doesn't matter which dice said yes.

    The code runs that table once per threshold, from the highest face down to 1. It ends
    in the same answer table as brute force, one whole column per threshold instead of
    one roll at a time.
    """)
    return


@app.function
def ordered_ways(dice):
    result = [{} for _ in dice]
    prev_at_least = [0] * (len(dice) + 1)
    for t in sorted({face for die in dice for face in die}, reverse=True):
        passing = [1] + [0] * len(dice)  # before any dice: one empty roll, 0 yeses
        for i, die in enumerate(dice):
            yes = sum(1 for face in die if face >= t)
            no = len(die) - yes
            new = [0] * (len(dice) + 1)
            for c, count in enumerate(passing):
                if count == 0:
                    continue
                new[c] += count * no
                new[c + 1] += count * yes
            passing = new
        at_least = [sum(passing[j:]) for j in range(len(dice) + 1)]
        for j in range(1, len(dice) + 1):
            result[j - 1][t] = at_least[j] - prev_at_least[j]
        prev_at_least = at_least
    return result


@app.cell
def _(DICE):
    def counting_rows(t):
        """The full yes-count table for threshold t: rows[m] holds the counts after m dice."""
        rows = [[1] + [0] * len(DICE)]
        for die in DICE:
            yes = sum(1 for face in die if face >= t)
            no = len(die) - yes
            new = [0] * (len(DICE) + 1)
            for c, count in enumerate(rows[-1]):
                if count:
                    new[c] += count * no
                    new[c + 1] += count * yes
            rows.append(new)
        return rows

    return (counting_rows,)


@app.cell
def _(DICE, NAMES, POSITIONS, counting_rows):
    _final = ordered_ways(DICE)
    _biggest = max(max(row.values()) for row in _final)
    _rolls = sum(_final[0].values())

    def answer_html(result, cells=(), column=None):
        """The shared answer table: rolls where the j-th highest is exactly each face.

        `cells` are (j, face) pairs to outline (brute force: the current roll),
        `column` is a face whose whole column to outline (thresholds: the current t).
        """
        result = result or [{} for _ in DICE]
        faces = sorted({face for die in DICE for face in die}, reverse=True)
        out = [
            '<div class="dk"><p class="title">rolls where the position is exactly this face</p>',
            '<table class="answer"><colgroup><col class="label-col">',
            '<col class="face-col">' * len(faces),
            '<col class="total-col"></colgroup><tr><th></th>',
        ]
        out.extend(f'<th class="{"hot" if f == column else ""}">{f}</th>' for f in faces)
        out.append("<th>counted</th></tr>")
        for j in range(len(DICE)):
            out.append(f'<tr><td class="label">{POSITIONS[j]}</td>')
            for f in faces:
                value = result[j].get(f)
                cls = []
                if (j, f) in cells:
                    cls.append("pick")
                if f == column:
                    # One continuous band down the column: sides on every row, ends on the outer rows.
                    cls.append("band")
                    cls.append("band-top" if j == 0 else "")
                    cls.append("band-bottom" if j == len(DICE) - 1 else "")
                if value == 0:
                    cls.append("zero")
                cls = " ".join(c for c in cls if c)
                if value is None:
                    out.append(f'<td class="{cls}"></td>')
                else:
                    heat = 0.06 + 0.5 * value / _biggest
                    out.append(
                        f'<td class="{cls}" style="background: rgba(79, 70, 229, {heat:.2f})">{value}</td>'
                    )
            out.append(f'<td class="total">{sum(result[j].values())} / {_rolls}</td></tr>')
        out.append("</table></div>")
        return "".join(out)

    def table_html(state, line=None, prev=None):
        """Draw the yes-count table and the answers for one step.

        `line` is the line of `ordered_ways` about to run and `prev` the one that
        just ran. Loop variables keep old values until reassigned, so the line
        says which locals belong to the current step.
        """
        state = state or {}
        t = state.get("t")
        thresholds = sorted({face for die in DICE for face in die}, reverse=True)
        n = len(DICE)
        rows = counting_rows(t) if t is not None else None
        done, building = None, None  # dice counted so far, and the row being built
        if t is not None:
            if line == 5:
                done = 0  # new threshold: `passing` still holds the previous one
            elif line == 6:
                done = rows.index(state["passing"])
            elif 7 <= line <= 15:
                done = state["i"]
                building = state["new"] if line >= 10 else None
            else:
                done = n
        # Line 13 adds the "no" count and line 14 the "yes" count for cell c.
        phase = "start" if line == 13 else "no" if prev == 13 else "yes" if prev == 14 else None
        source, target, merged = None, None, False
        if phase is not None:
            source = state["c"]
            target = {"start": None, "no": source, "yes": source + 1}[phase]
            merged = phase == "no" and building[source] > state["count"] * state["no"]

        out = ['<div class="dk">']
        if t is None:
            out.append(f'<p class="caption">Thresholds go from {thresholds[0]} down to 1, one table each.</p>')
        else:
            out.append(f'<p class="title">threshold <b class="hot">t = {t}</b>: a die says '
                       f'<span class="chip yes">yes</span> when it shows {t} or more</p>')
        out.append('<table class="counts"><colgroup><col class="label-col">')
        out.append('<col class="count-col">' * (n + 1))
        out.append('<col class="total-col"></colgroup><tr><th></th>')
        out.extend(f"<th>{c} yes</th>" for c in range(n + 1))
        out.append("<th>total</th></tr>")
        for m in range(n):
            faces = "".join(
                f'<span class="chip {"yes" if t is not None and f >= t else "no"}">{f}</span>'
                for f in DICE[m]
            )
            label = ("+ " if m else "") + NAMES[m]
            if done is not None and m < done:
                values = rows[m + 1]
            elif m == done and building is not None:
                values = building
            else:
                values = None
            out.append(f'<tr><td class="label">{label} <span class="faces">{faces}</span></td>')
            for c in range(n + 1):
                cls = []
                if m == done and building is not None and c == target:
                    cls.append("merge" if merged else "target")
                # The source count sits in the row above the one being built.
                if source is not None and done > 0 and m == done - 1 and c == source:
                    cls.append("source")
                if values is None or c > m + 1:
                    text = ""  # after m + 1 dice there can't be more than m + 1 yeses
                elif m == done:
                    text = values[c] or ""  # row being built: blank until a count lands
                else:
                    text = values[c]
                out.append(f'<td class="{" ".join(cls)}">{text}</td>')
            total = sum(values) if values is not None else ""
            out.append(f'<td class="total">{total}</td></tr>')
        out.append("</table>")

        # What just happened, in words.
        caption = ""
        if source is not None:
            yes, no, count = state["yes"], state["no"], state["count"]
            if done == 0:
                caption = f"the first die, a {NAMES[0]}: no in {no} ways, yes in {yes}"
            elif phase == "start":
                caption = f"take the {count} rolls with {source} yes so far and add a {NAMES[done]}"
            elif phase == "no":
                caption = f"{NAMES[done]} says no in {no} ways: {count} × {no} = {count * no} rolls stay at {source} yes"
                if merged:
                    caption += (f'<br><b class="hot">merge:</b> the {building[source] - count * no} rolls '
                                f"that reached {source} yes with an earlier yes join them, "
                                f"one number from now on: {building[source]}")
            else:
                caption = f"{NAMES[done]} says yes in {yes} ways: {count} × {yes} = {count * yes} rolls move to {source + 1} yes"
        elif done == n:
            at_least = [sum(rows[n][j:]) for j in range(n + 1)]
            caption = "at least j yeses = j-th highest ≥ t: " + ", ".join(
                f"{POSITIONS[j - 1]} {at_least[j]}" for j in range(1, n + 1)
            )
        out.append(f'<p class="caption">{caption}</p>')

        out.append("</div>")
        # The answers so far: subtracting thresholds gives "exactly t".
        out.append(answer_html(state.get("result"), column=t))
        return "".join(out)

    TABLE_JS = """
    export default {
      render({ model, el }) {
        const update = () => { el.innerHTML = (model.get("data") || {}).html || ""; };
        update();
        model.on("change:data", update);
        return () => model.off("change:data", update);
      },
    };
    """

    TABLE_CSS = """
    .dk { font-family: sans-serif; font-size: 13px; color: inherit; }
    .dk table { border-collapse: collapse; margin-bottom: 6px; table-layout: fixed; width: 100%; }
    .dk col.label-col { width: 210px; }
    .dk col.count-col { width: 64px; }
    .dk col.face-col { width: 38px; }
    .dk col.total-col { width: 92px; }
    .dk td.total { white-space: nowrap; }
    .dk table.answer td { border-bottom: 0; }
    .dk td.pick { box-shadow: inset 0 0 0 2px #f97316; }
    .dk td.band { box-shadow: inset 2px 0 #f97316, inset -2px 0 #f97316; }
    .dk td.band.band-top { box-shadow: inset 2px 0 #f97316, inset -2px 0 #f97316, inset 0 2px #f97316; }
    .dk td.band.band-bottom { box-shadow: inset 2px 0 #f97316, inset -2px 0 #f97316, inset 0 -2px #f97316; }
    .dk td.zero { color: rgba(127, 127, 127, 0.6); }
    .dk th { font-weight: normal; opacity: 0.6; padding: 4px 8px; text-align: right; }
    .dk td { padding: 5px 8px; text-align: right;
             border-bottom: 1px solid rgba(127, 127, 127, 0.25); font-variant-numeric: tabular-nums; }
    .dk td.label { text-align: left; white-space: nowrap; }
    .dk td.total { opacity: 0.6; border-left: 1px solid rgba(127, 127, 127, 0.25); }
    .dk td.source { outline: 2px solid #4f46e5; outline-offset: -2px; }
    .dk td.target { background: rgba(249, 115, 22, 0.25); }
    .dk td.merge { background: rgba(249, 115, 22, 0.6); font-weight: bold; }
    .dk .title { margin: 8px 0 4px; }
    .dk .caption { min-height: 2.6em; margin: 4px 0 12px; }
    .dk .hot { color: #f97316; }
    .dk .faces { margin-left: 6px; }
    .dk .chip { display: inline-block; min-width: 11px; padding: 0 2px; margin-right: 2px;
                border-radius: 3px; font-size: 10px; text-align: center; }
    .dk .chip.yes { background: #f97316; color: white; }
    .dk .chip.no { background: rgba(127, 127, 127, 0.2); }
    """
    return TABLE_CSS, TABLE_JS, answer_html, table_html


@app.cell
def _(DICE, EsmWidget, StateViewer, TABLE_CSS, TABLE_JS, mo, table_html):
    ordered_viewer = StateViewer(
        ordered_ways,
        args=(DICE,),
        interval_ms=250,
        sync_throttle_ms=50,
        timeline_func=lambda t: t,
        timeline_label="threshold t",
        show_code=False,
    )
    ordered_table = EsmWidget(
        TABLE_JS, css=TABLE_CSS, data={"html": table_html({})}, width=0, height=220 + 70 * len(DICE)
    )

    # A plain widget updated through `observe`, so no cell reruns while playing.
    def redraw_ordered(_=None):
        step, steps = ordered_viewer.step, ordered_viewer.steps
        line = steps[step]["line"] if steps else None
        prev = steps[step - 1]["line"] if step > 0 else None
        ordered_table.data = {"html": table_html(ordered_viewer.state, line, prev)}

    ordered_viewer.observe(redraw_ordered, names="step")
    redraw_ordered()
    mo.vstack([ordered_viewer, ordered_table])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Benchmark

    Brute force against `Dice.ordered(n)` from dicekit (all positions of n d6), timed on
    this machine. Brute force stops at 7 dice; 8 would already take seconds.
    """)
    return


@app.cell
def _(Dice, alt, brute_force, pd, time):
    def seconds(fn):
        start = time.perf_counter()
        fn()
        return time.perf_counter() - start

    d6 = Dice.from_sides(6)
    timings = []
    for _n in range(1, 8):
        timings.append({"dice": _n, "method": "brute force", "seconds": seconds(lambda: brute_force([list(range(1, 7))] * _n))})
    for _n in [1, 2, 3, 4, 5, 6, 7, 10, 15, 20, 30]:
        timings.append({"dice": _n, "method": "dicekit ordered()", "seconds": seconds(lambda: d6.ordered(_n))})

    alt.Chart(pd.DataFrame(timings)).mark_line().encode(
        x=alt.X("dice:Q", title="number of dice"),
        y=alt.Y("seconds:Q", scale=alt.Scale(type="log"), title="seconds (log scale)"),
        color=alt.Color("method:N", title=None),
        tooltip=["method", "dice", alt.Tooltip("seconds:Q", format=".5f")],
    ).properties(width=520, height=260)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Where this lives in dicekit

    `ordered(*dice)` is `ordered_ways` with probabilities: the yes count per die becomes
    `P(die >= t)` (precomputed by `_threshold_probabilities`), the `passing` list is
    `pass_count_probs`, and `at_least` is `survival`.
    """)
    return


@app.cell
def _(DICE, Dice, NAMES, mo, ordered):
    from_dicekit = ordered(*[Dice.from_sides(len(die)) for die in DICE])
    ours = ordered_ways(DICE)
    rolls = 1
    for _die in DICE:
        rolls *= len(_die)
    matches = all(
        abs(from_dicekit[j].probs.get(face, 0) - ours[j].get(face, 0) / rolls) < 1e-12
        for j in range(len(DICE))
        for face in set(from_dicekit[j].probs) | set(ours[j])
    )
    mo.vstack(
        [
            mo.md(f"`ordered({', '.join(NAMES)})` matches `ordered_ways` divided by {rolls}: **{matches}**"),
            mo.hstack(from_dicekit, justify="start"),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
