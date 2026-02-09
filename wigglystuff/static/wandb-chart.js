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

function exponentialSmooth(points, alpha) {
    if (alpha <= 0 || points.length === 0) return points;
    const out = [{ x: points[0].x, y: points[0].y }];
    for (let i = 1; i < points.length; i++) {
        const prev = out[i - 1].y;
        out.push({ x: points[i].x, y: alpha * prev + (1 - alpha) * points[i].y });
    }
    return out;
}

function gaussianSmooth(points, sigma) {
    if (sigma <= 0 || points.length === 0) return points;
    const radius = Math.ceil(3 * sigma);
    const kernel = [];
    let kernelSum = 0;
    for (let j = -radius; j <= radius; j++) {
        const w = Math.exp(-0.5 * (j / sigma) * (j / sigma));
        kernel.push(w);
        kernelSum += w;
    }
    for (let j = 0; j < kernel.length; j++) kernel[j] /= kernelSum;

    return points.map((p, i) => {
        let sum = 0, wSum = 0;
        for (let j = -radius; j <= radius; j++) {
            const idx = i + j;
            if (idx < 0 || idx >= points.length) continue;
            const w = kernel[j + radius];
            sum += w * points[idx].y;
            wSum += w;
        }
        return { x: p.x, y: sum / wSum };
    });
}

const SLIDER_CONFIG = {
    rolling:     { label: "Rolling mean:",   min: 0, max: 50,   step: 1,    fmt: v => v === 0 ? "off" : String(Math.round(v)),  toParam: v => v < 2 ? null : v },
    exponential: { label: "EMA weight:",     min: 0, max: 0.99, step: 0.01, fmt: v => v === 0 ? "off" : v.toFixed(2),           toParam: v => v === 0 ? null : v },
    gaussian:    { label: "Gaussian \u03c3:", min: 0, max: 10,   step: 0.1,  fmt: v => v === 0 ? "off" : v.toFixed(1),           toParam: v => v === 0 ? null : v },
};

const COLORS = [
    "#4e79a7","#f28e2b","#e15759","#76b7b2","#59a14f",
    "#edc948","#b07aa1","#ff9da7","#9c755f","#bab0ac"
];

function prepareSeries(runData, runs, key, smoothKind, smoothParam) {
    return runs.map((run, i) => {
        const rd = runData[run.id];
        const color = COLORS[i % COLORS.length];
        if (!rd) return { label: run.label, color, points: [], raw: [] };
        const raw = rd.rows
            .filter(r => r[key] !== undefined && r._step !== undefined)
            .map(r => ({ x: r._step, y: r[key] }));

        let smoothed = raw;
        if (smoothParam != null && smoothParam > 0) {
            if (smoothKind === "rolling" && smoothParam >= 2) {
                smoothed = rollingMean(raw, smoothParam);
            } else if (smoothKind === "exponential") {
                smoothed = exponentialSmooth(raw, smoothParam);
            } else if (smoothKind === "gaussian") {
                smoothed = gaussianSmooth(raw, smoothParam);
            }
        }
        const hasSmoothing = smoothed !== raw;
        return {
            label: run.label,
            color,
            points: smoothed,
            raw: hasSmoothing ? raw : [],
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
    const pollSec = model.get("poll_seconds");
    const w = model.get("width") || 700;

    const container = document.createElement("div");
    container.style.fontFamily = "system-ui, sans-serif";
    container.style.padding = "12px";
    container.style.width = w + "px";
    container.style.boxSizing = "border-box";

    // Controls row: smoothing controls left, refresh button right
    const controlsRow = document.createElement("div");
    controlsRow.style.cssText = "display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;font-size:13px;color:#666";

    // Smoothing controls (left side)
    let kind = model.get("smoothing_kind") || "gaussian";
    let cfg = SLIDER_CONFIG[kind] || SLIDER_CONFIG.rolling;

    const smoothGroup = document.createElement("div");
    smoothGroup.style.cssText = "display:flex;align-items:center;gap:8px";

    // Smoothing kind dropdown
    const kindSelect = document.createElement("select");
    kindSelect.style.cssText = "font-size:12px;padding:1px 4px;border:1px solid #ccc;border-radius:3px;background:#fff;font-family:system-ui,sans-serif";
    for (const [value, label] of [["rolling", "Rolling"], ["exponential", "Exponential"], ["gaussian", "Gaussian"]]) {
        const opt = document.createElement("option");
        opt.value = value;
        opt.textContent = label;
        if (value === kind) opt.selected = true;
        kindSelect.appendChild(opt);
    }

    // Slider
    const smoothSlider = document.createElement("input");
    smoothSlider.type = "range";
    smoothSlider.min = String(cfg.min);
    smoothSlider.max = String(cfg.max);
    smoothSlider.step = String(cfg.step);
    const initParam = model.get("smoothing_param") ?? 0;
    smoothSlider.value = String(initParam);
    smoothSlider.style.width = "120px";
    const smoothValEl = document.createElement("span");
    smoothValEl.textContent = cfg.fmt(parseFloat(smoothSlider.value));

    function configureSlider() {
        cfg = SLIDER_CONFIG[kind] || SLIDER_CONFIG.rolling;
        smoothSlider.min = String(cfg.min);
        smoothSlider.max = String(cfg.max);
        smoothSlider.step = String(cfg.step);
        smoothSlider.value = "0";
        smoothValEl.textContent = "off";
    }

    smoothGroup.appendChild(kindSelect);
    smoothGroup.appendChild(smoothSlider);
    smoothGroup.appendChild(smoothValEl);
    if (model.get("show_slider")) controlsRow.appendChild(smoothGroup);

    // Refresh button (right side, manual mode only)
    const refreshBtn = document.createElement("button");
    refreshBtn.textContent = "\u21bb Refresh";
    refreshBtn.style.cssText = "padding:2px 8px;font-size:12px;cursor:pointer;border:1px solid #ccc;border-radius:4px;background:#f5f5f5;font-family:system-ui,sans-serif;margin-left:auto";
    if (pollSec === null) controlsRow.appendChild(refreshBtn);

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

    // Status line (below chart)
    const statusEl = document.createElement("div");
    statusEl.style.cssText = "margin-top:4px;color:#666;font-size:12px";
    statusEl.textContent = "Waiting for runs...";

    container.appendChild(controlsRow);
    container.appendChild(chartWrapper);
    container.appendChild(statusEl);
    el.appendChild(container);

    let lastSeries = [];

    function getSliderParam() {
        const v = parseFloat(smoothSlider.value);
        return cfg.toParam(v);
    }

    function redraw() {
        const runs = model.get("_runs") || [];
        const key = model.get("key");
        const w = model.get("width") || 700;
        const h = model.get("height") || 300;
        lastSeries = prepareSeries(runData, runs, key, kind, getSliderParam());
        drawChart(chartCanvas, lastSeries, { title: key, width: w, height: h });
    }

    kindSelect.addEventListener("change", () => {
        kind = kindSelect.value;
        model.set("smoothing_kind", kind);
        configureSlider();
        model.set("smoothing_param", null);
        model.save_changes();
        redraw();
    });

    smoothSlider.addEventListener("input", () => {
        let v = parseFloat(smoothSlider.value);
        if (kind === "rolling" && v === 1) { smoothSlider.value = "2"; v = 2; }
        smoothValEl.textContent = cfg.fmt(v);
        model.set("smoothing_param", cfg.toParam(v));
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

            if (interval && runs.every(r => runData[r.id]?.state !== "running")) {
                clearInterval(interval);
                statusEl.textContent = totalRows + " points — done (" + now + ")";
            }
        } catch (err) {
            statusEl.textContent = "Error: " + err.message;
            statusEl.style.color = "red";
        }
    }

    let interval = null;

    pollAll();

    if (pollSec !== null) {
        interval = setInterval(pollAll, (pollSec || 5) * 1000);
        return () => clearInterval(interval);
    } else {
        refreshBtn.addEventListener("click", () => pollAll());
    }
}

export default { render };
