# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "anywidget",
#     "wandb",
#     "traitlets",
#     "marimo>=0.19.9",
# ]
# ///

import marimo

__generated_with = "0.19.9"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    mo.md("""
    # Live wandb charts via anywidget

    This demo starts multiple wandb runs with different learning rates, logs
    metrics with a delay, and the widget polls the wandb GraphQL API from
    JavaScript to render live-updating line charts. No iframe, no cookies needed.

    Each widget shows **one metric** as a line chart. Pass multiple runs
    via `runs` to compare them side by side in the same chart.
    """)
    return


@app.cell(hide_code=True)
def _():
    import anywidget
    import traitlets

    class WandbLiveWidget(anywidget.AnyWidget):
        api_key = traitlets.Unicode().tag(sync=True)
        entity = traitlets.Unicode().tag(sync=True)
        project = traitlets.Unicode().tag(sync=True)
        _runs = traitlets.List(traitlets.Dict()).tag(sync=True)
        key = traitlets.Unicode().tag(sync=True)
        poll_seconds = traitlets.Int(5).tag(sync=True)
        rolling_mean = traitlets.Int(None, allow_none=True).tag(sync=True)
        show_slider = traitlets.Bool(True).tag(sync=True)
        width = traitlets.Int(700).tag(sync=True)
        height = traitlets.Int(300).tag(sync=True)

        def __init__(self, *args, runs=None, **kwargs):
            if runs is not None:
                kwargs["_runs"] = [
                    {"id": r.id, "label": r.name} if hasattr(r, "id") else r
                    for r in runs
                ]
            super().__init__(*args, **kwargs)

        @traitlets.validate("rolling_mean")
        def _validate_rolling_mean(self, proposal):
            value = proposal["value"]
            if value is None:
                return value
            if value < 2:
                raise ValueError("rolling_mean must be None (no smoothing) or >= 2")
            return value

        _esm = """
        // ── Data layer ──────────────────────────────

        async function fetchHistory(apiKey, entity, project, runId, key, minStep) {
            const query = `
                query RunSampledHistory($project: String!, $entity: String!, $name: String!, $specs: [JSONString!]!) {
                    project(name: $project, entityName: $entity) {
                        run(name: $name) {
                            sampledHistory(specs: $specs)
                        }
                    }
                }
            `;
            const specObj = { keys: [key, "_step"], samples: 500 };
            if (minStep > 0) specObj.minStep = minStep;
            const variables = { entity, project, name: runId, specs: [JSON.stringify(specObj)] };
            const creds = btoa("api:" + apiKey);

            const resp = await fetch("https://api.wandb.ai/graphql", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": "Basic " + creds,
                },
                body: JSON.stringify({ query, variables }),
            });

            if (!resp.ok) throw new Error("HTTP " + resp.status);
            const data = await resp.json();
            if (data.errors) throw new Error(data.errors.map(e => e.message).join(", "));
            return data.data.project.run.sampledHistory[0] || [];
        }

        async function fetchRunState(apiKey, entity, project, runId) {
            const query = `
                query RunState($project: String!, $entity: String!, $name: String!) {
                    project(name: $project, entityName: $entity) {
                        run(name: $name) {
                            state
                        }
                    }
                }
            `;
            const variables = { entity, project, name: runId };
            const creds = btoa("api:" + apiKey);

            const resp = await fetch("https://api.wandb.ai/graphql", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": "Basic " + creds,
                },
                body: JSON.stringify({ query, variables }),
            });

            if (!resp.ok) throw new Error("HTTP " + resp.status);
            const data = await resp.json();
            if (data.errors) throw new Error(data.errors.map(e => e.message).join(", "));
            return data.data.project.run.state;
        }

        function rollingMean(points, win) {
            if (win <= 1) return points;
            return points.map((p, i) => {
                const start = Math.max(0, i - win + 1);
                let sum = 0;
                for (let j = start; j <= i; j++) sum += points[j].y;
                return { x: p.x, y: sum / (i - start + 1) };
            });
        }

        const COLORS = [
            "#4e79a7","#f28e2b","#e15759","#76b7b2","#59a14f",
            "#edc948","#b07aa1","#ff9da7","#9c755f","#bab0ac"
        ];

        function prepareSeries(runData, runs, key, rmWin) {
            return runs.map((run, i) => {
                const rd = runData[run.id];
                const color = COLORS[i % COLORS.length];
                if (!rd) return { label: run.label, color, points: [], raw: [] };
                const raw = rd.rows
                    .filter(r => r[key] !== undefined && r._step !== undefined)
                    .map(r => ({ x: r._step, y: r[key] }));
                return {
                    label: run.label,
                    color,
                    points: rmWin > 1 ? rollingMean(raw, rmWin) : raw,
                    raw: rmWin > 1 ? raw : [],
                };
            });
        }

        // ── Render layer (swap this to use D3, etc.) ─

        function drawChart(canvas, series, opts) {
            const { title, width, height } = opts;
            const dpr = window.devicePixelRatio || 1;
            canvas.width = width * dpr;
            canvas.height = height * dpr;
            canvas.style.width = width + "px";
            canvas.style.height = height + "px";

            const ctx = canvas.getContext("2d");
            ctx.scale(dpr, dpr);

            const pad = { top: 30, right: 120, bottom: 40, left: 60 };
            const plotW = width - pad.left - pad.right;
            const plotH = height - pad.top - pad.bottom;

            ctx.clearRect(0, 0, width, height);

            // Compute extents across all series
            let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
            for (const s of series) {
                for (const p of s.points) {
                    if (p.x < minX) minX = p.x;
                    if (p.x > maxX) maxX = p.x;
                    if (p.y < minY) minY = p.y;
                    if (p.y > maxY) maxY = p.y;
                }
            }

            if (!isFinite(minX)) {
                ctx.fillStyle = "#999";
                ctx.font = "13px system-ui, sans-serif";
                ctx.textAlign = "center";
                ctx.fillText("Waiting for data...", width / 2, height / 2);
                return;
            }

            // Pad y range by 5%
            const yPad = (maxY - minY) * 0.05 || 0.1;
            minY -= yPad;
            maxY += yPad;

            const scaleX = (v) => pad.left + ((v - minX) / (maxX - minX || 1)) * plotW;
            const scaleY = (v) => pad.top + plotH - ((v - minY) / (maxY - minY || 1)) * plotH;

            // Grid
            ctx.strokeStyle = "#e0e0e0";
            ctx.lineWidth = 0.5;
            ctx.setLineDash([4, 4]);

            const nY = 5;
            for (let i = 0; i <= nY; i++) {
                const y = scaleY(minY + (i / nY) * (maxY - minY));
                ctx.beginPath(); ctx.moveTo(pad.left, y); ctx.lineTo(pad.left + plotW, y); ctx.stroke();
            }
            const nX = 6;
            for (let i = 0; i <= nX; i++) {
                const x = scaleX(minX + (i / nX) * (maxX - minX));
                ctx.beginPath(); ctx.moveTo(x, pad.top); ctx.lineTo(x, pad.top + plotH); ctx.stroke();
            }
            ctx.setLineDash([]);

            // Tick labels
            ctx.fillStyle = "#666";
            ctx.font = "11px system-ui, sans-serif";
            ctx.textAlign = "right";
            ctx.textBaseline = "middle";
            for (let i = 0; i <= nY; i++) {
                const v = minY + (i / nY) * (maxY - minY);
                ctx.fillText(v.toPrecision(3), pad.left - 6, scaleY(v));
            }
            ctx.textAlign = "center";
            ctx.textBaseline = "top";
            for (let i = 0; i <= nX; i++) {
                const v = minX + (i / nX) * (maxX - minX);
                ctx.fillText(Math.round(v).toString(), scaleX(v), pad.top + plotH + 6);
            }

            // Title
            ctx.fillStyle = "#333";
            ctx.font = "bold 13px system-ui, sans-serif";
            ctx.textAlign = "center";
            ctx.textBaseline = "top";
            ctx.fillText(title, pad.left + plotW / 2, 6);

            // X-axis label
            ctx.fillStyle = "#999";
            ctx.font = "11px system-ui, sans-serif";
            ctx.fillText("step", pad.left + plotW / 2, pad.top + plotH + 22);

            // Raw data lines (low opacity, behind smoothed)
            for (const s of series) {
                if (s.raw.length === 0) continue;
                ctx.globalAlpha = 0.2;
                ctx.strokeStyle = s.color;
                ctx.lineWidth = 1;
                ctx.beginPath();
                for (let i = 0; i < s.raw.length; i++) {
                    const px = scaleX(s.raw[i].x);
                    const py = scaleY(s.raw[i].y);
                    i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
                }
                ctx.stroke();
                ctx.globalAlpha = 1;
            }

            // Polylines (smoothed or raw if no smoothing)
            for (const s of series) {
                if (s.points.length === 0) continue;
                ctx.strokeStyle = s.color;
                ctx.lineWidth = 1.5;
                ctx.beginPath();
                for (let i = 0; i < s.points.length; i++) {
                    const px = scaleX(s.points[i].x);
                    const py = scaleY(s.points[i].y);
                    i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
                }
                ctx.stroke();
            }

            // Legend
            let ly = pad.top + 4;
            ctx.font = "11px system-ui, sans-serif";
            ctx.textAlign = "left";
            ctx.textBaseline = "top";
            for (const s of series) {
                ctx.fillStyle = s.color;
                ctx.fillRect(pad.left + plotW + 10, ly + 2, 12, 3);
                ctx.fillStyle = "#333";
                ctx.fillText(s.label, pad.left + plotW + 26, ly);
                ly += 16;
            }
        }

        // ── Widget glue ─────────────────────────────

        function render({ model, el }) {
            const runData = {};

            const container = document.createElement("div");
            container.style.fontFamily = "system-ui, sans-serif";
            container.style.padding = "12px";

            // Status line
            const statusEl = document.createElement("div");
            statusEl.style.marginBottom = "8px";
            statusEl.style.color = "#666";
            statusEl.style.fontSize = "13px";
            statusEl.textContent = "Waiting for runs...";

            // Smoothing slider
            const smoothRow = document.createElement("div");
            smoothRow.style.marginBottom = "8px";
            smoothRow.style.display = model.get("show_slider") ? "flex" : "none";
            smoothRow.style.alignItems = "center";
            smoothRow.style.gap = "8px";
            smoothRow.style.fontSize = "13px";
            smoothRow.style.color = "#666";

            const smoothLabel = document.createElement("span");
            smoothLabel.textContent = "Rolling mean:";
            const smoothSlider = document.createElement("input");
            smoothSlider.type = "range";
            smoothSlider.min = "0";
            smoothSlider.max = "50";
            smoothSlider.value = String(model.get("rolling_mean") || 0);
            smoothSlider.style.width = "120px";
            const smoothValEl = document.createElement("span");
            smoothValEl.textContent = smoothSlider.value === "0" ? "off" : smoothSlider.value;

            smoothRow.appendChild(smoothLabel);
            smoothRow.appendChild(smoothSlider);
            smoothRow.appendChild(smoothValEl);

            // Chart canvas + tooltip wrapper
            const chartCanvas = document.createElement("canvas");
            chartCanvas.style.display = "block";

            const tooltip = document.createElement("div");
            tooltip.style.cssText = "position:absolute;display:none;background:rgba(0,0,0,0.8);color:#fff;padding:6px 10px;border-radius:4px;font-size:12px;pointer-events:none;white-space:nowrap;z-index:10";

            const chartWrapper = document.createElement("div");
            chartWrapper.style.position = "relative";
            chartWrapper.style.display = "inline-block";
            chartWrapper.appendChild(chartCanvas);
            chartWrapper.appendChild(tooltip);

            container.appendChild(statusEl);
            container.appendChild(smoothRow);
            container.appendChild(chartWrapper);
            el.appendChild(container);

            let lastSeries = [];

            function getSliderRmWin() {
                const v = parseInt(smoothSlider.value, 10);
                return v < 2 ? null : v;
            }

            function redraw() {
                const runs = model.get("_runs") || [];
                const key = model.get("key");
                const w = model.get("width") || 700;
                const h = model.get("height") || 300;
                lastSeries = prepareSeries(runData, runs, key, getSliderRmWin());
                drawChart(chartCanvas, lastSeries, { title: key, width: w, height: h });
            }

            smoothSlider.addEventListener("input", () => {
                const v = parseInt(smoothSlider.value, 10);
                if (v === 1) { smoothSlider.value = "2"; }
                const rmWin = getSliderRmWin();
                smoothValEl.textContent = rmWin === null ? "off" : String(rmWin);
                model.set("rolling_mean", rmWin);
                model.save_changes();
                redraw();
            });

            // Hover tooltip
            chartCanvas.addEventListener("mousemove", (e) => {
                if (lastSeries.length === 0) { tooltip.style.display = "none"; return; }
                const rect = chartCanvas.getBoundingClientRect();
                const mx = e.clientX - rect.left;
                const my = e.clientY - rect.top;
                const w = model.get("width") || 700;
                const h = model.get("height") || 300;
                const pad = { top: 30, right: 120, bottom: 40, left: 60 };

                let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
                for (const s of lastSeries) {
                    for (const p of s.points) {
                        if (p.x < minX) minX = p.x; if (p.x > maxX) maxX = p.x;
                        if (p.y < minY) minY = p.y; if (p.y > maxY) maxY = p.y;
                    }
                }
                if (!isFinite(minX)) return;
                const yPad = (maxY - minY) * 0.05 || 0.1;
                minY -= yPad; maxY += yPad;
                const plotW = w - pad.left - pad.right;
                const plotH = h - pad.top - pad.bottom;
                const sx = (v) => pad.left + ((v - minX) / (maxX - minX || 1)) * plotW;
                const sy = (v) => pad.top + plotH - ((v - minY) / (maxY - minY || 1)) * plotH;

                let bestDist = 25, bestS = null, bestP = null;
                for (const s of lastSeries) {
                    for (const p of s.points) {
                        const dx = sx(p.x) - mx, dy = sy(p.y) - my;
                        const d = Math.sqrt(dx * dx + dy * dy);
                        if (d < bestDist) { bestDist = d; bestS = s; bestP = p; }
                    }
                }

                if (bestP) {
                    tooltip.style.display = "block";
                    tooltip.style.left = (sx(bestP.x) + 12) + "px";
                    tooltip.style.top = (sy(bestP.y) - 10) + "px";
                    tooltip.textContent = bestS.label + " | step " + bestP.x + " | " + bestP.y.toFixed(4);
                } else {
                    tooltip.style.display = "none";
                }
            });
            chartCanvas.addEventListener("mouseleave", () => { tooltip.style.display = "none"; });

            // Polling
            async function pollAll() {
                const apiKey = model.get("api_key");
                const entity = model.get("entity");
                const project = model.get("project");
                const runs = model.get("_runs") || [];
                const key = model.get("key");

                if (!apiKey || runs.length === 0) {
                    statusEl.textContent = "Waiting for runs...";
                    return;
                }

                try {
                    const results = await Promise.allSettled(
                        runs.map(async (run) => {
                            const rd = runData[run.id] || { rows: [], maxStep: -1, state: "running" };
                            runData[run.id] = rd;

                            if (rd.state !== "running") return { id: run.id, newRows: 0, state: rd.state };

                            const [newRows, state] = await Promise.all([
                                fetchHistory(apiKey, entity, project, run.id, key, rd.maxStep + 1),
                                fetchRunState(apiKey, entity, project, run.id),
                            ]);

                            const seen = new Set(rd.rows.map(r => r._step));
                            const unique = newRows.filter(r => !seen.has(r._step));
                            if (unique.length > 0) {
                                rd.rows.push(...unique);
                                rd.rows.sort((a, b) => a._step - b._step);
                                rd.maxStep = rd.rows[rd.rows.length - 1]._step;
                            }
                            rd.state = state;
                            return { id: run.id, newRows: unique.length, state };
                        })
                    );

                    const now = new Date().toLocaleTimeString();
                    const totalNew = results
                        .filter(r => r.status === "fulfilled")
                        .reduce((s, r) => s + r.value.newRows, 0);
                    const totalRows = Object.values(runData).reduce((s, rd) => s + rd.rows.length, 0);

                    statusEl.textContent = totalNew > 0
                        ? "+" + totalNew + " points (total: " + totalRows + ") at " + now
                        : totalRows + " points (checked " + now + ")";
                    statusEl.style.color = "#666";

                    redraw();

                    if (runs.every(r => runData[r.id]?.state !== "running")) {
                        clearInterval(interval);
                        statusEl.textContent += " — all runs finished, polling stopped.";
                    }
                } catch (err) {
                    statusEl.textContent = "Error: " + err.message;
                    statusEl.style.color = "red";
                }
            }

            pollAll();
            const interval = setInterval(pollAll, (model.get("poll_seconds") || 5) * 1000);
            return () => clearInterval(interval);
        }

        export default { render };
        """

    return (WandbLiveWidget,)


@app.cell
def _():
    import wandb
    import math
    import random

    api = wandb.Api()
    api_key = api.api_key

    # Start a baseline run and log all data immediately (no delay)
    baseline = wandb.init(project="jupyter-projo", name="baseline")
    for _step in range(60):
        _t = _step / 59
        _noise = random.gauss(0, 0.05)
        baseline.log({"loss": math.exp(-2 * _t) + 0.05 + _noise, "acc": 1 - math.exp(-2 * _t) + _noise})
    baseline.finish()
    print(f"Baseline run finished: {baseline.name} ({baseline.id})")

    # Start an experiment run that will be logged slowly in a later cell
    experiment = wandb.init(project="jupyter-projo", name="fast-lr", reinit=True)
    print(f"Experiment run started: {experiment.name} ({experiment.id})")
    return api_key, baseline, experiment, math, random


@app.cell
def _(WandbLiveWidget, api_key, baseline, experiment):
    loss_chart = WandbLiveWidget(
        api_key=api_key,
        entity=baseline.entity,
        project=baseline.project,
        runs=[baseline, experiment],
        key="loss",
        rolling_mean=5,
        poll_seconds=1,
    )
    loss_chart
    return (loss_chart,)


@app.cell(hide_code=True)
def _(WandbLiveWidget, api_key, baseline, experiment):
    acc_chart = WandbLiveWidget(
        api_key=api_key,
        entity=baseline.entity,
        project=baseline.project,
        runs=[baseline, experiment],
        key="acc",
        rolling_mean=5,
        poll_seconds=2,
    )
    acc_chart
    return (acc_chart,)


@app.cell
def _(acc_chart, experiment, loss_chart, math, random):
    import time

    loss_chart
    acc_chart

    # Simulate training for the experiment run with a faster learning rate
    for _step in range(60):
        _t = _step / 59
        _noise = random.gauss(0, 0.05)
        experiment.log({"loss": math.exp(-5 * _t) + 0.01 + _noise, "acc": 1 - math.exp(-5 * _t) + _noise})
        time.sleep(2)

    experiment.finish()
    print("Experiment done!")
    return


if __name__ == "__main__":
    app.run()
