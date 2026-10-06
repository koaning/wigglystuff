const SVG_NS = "http://www.w3.org/2000/svg";
const CHART_W = 240;
const CHART_H = 120;
const PAD = { left: 8, right: 8, top: 22, bottom: 20 };
const N_POINTS = 160;
// Pixels of movement ignored on each axis before it starts changing, so a
// horizontal drag doesn't nudge the vertical parameter (and vice versa).
const DEAD_ZONE = 4;
const SQRT_2PI = Math.sqrt(2 * Math.PI);

// Lanczos approximation of log(Gamma(z)), needed by the gamma and beta pdfs.
const LANCZOS = [676.5203681218851, -1259.1392167224028, 771.32342877765313,
    -176.61502916214059, 12.507343278686905, -0.13857109526572012,
    9.9843695780195716e-6, 1.5056327351493116e-7];
function logGamma(z) {
    if (z < 0.5) return Math.log(Math.PI / Math.sin(Math.PI * z)) - logGamma(1 - z);
    z -= 1;
    let x = 0.99999999999980993;
    for (let i = 0; i < LANCZOS.length; i++) x += LANCZOS[i] / (z + i + 1);
    const t = z + LANCZOS.length - 0.5;
    return 0.5 * Math.log(2 * Math.PI) + (z + 0.5) * Math.log(t) - t + Math.log(x);
}

// One entry per scipy.stats family; keep in sync with wigglystuff/_distributions.py.
// `drag` lists the [horizontal, vertical] parameters (poisson has only one),
// `pdf` is the density (the pmf for discrete families), `range` is where it is
// drawn, and `support` clips the chart's padding (no x < 0 for positive families).
const FAMILIES = {
    norm: {
        drag: ["loc", "scale"],
        pdf: (x, p) => Math.exp(-0.5 * ((x - p.loc) / p.scale) ** 2) / (p.scale * SQRT_2PI),
        range: (p) => [p.loc - 4 * p.scale, p.loc + 4 * p.scale],
        support: [-Infinity, Infinity],
        moments: (p) => [p.loc, p.scale],
    },
    lognorm: {
        drag: ["scale", "s"],
        pdf: (x, p) => x <= 0 ? 0
            : Math.exp(-0.5 * ((Math.log(x) - Math.log(p.scale)) / p.s) ** 2) / (x * p.s * SQRT_2PI),
        // Up to the ~99.4th percentile; the full tail would squash the bulk.
        range: (p) => [0, p.scale * Math.exp(2.5 * p.s)],
        support: [0, Infinity],
        moments: (p) => {
            const e = Math.exp(p.s * p.s);
            return [p.scale * Math.sqrt(e), p.scale * Math.sqrt((e - 1) * e)];
        },
    },
    gamma: {
        drag: ["scale", "a"],
        pdf: (x, p) => x <= 0 ? 0
            : Math.exp((p.a - 1) * Math.log(x) - x / p.scale - logGamma(p.a) - p.a * Math.log(p.scale)),
        range: (p) => [0, p.a * p.scale + 5 * Math.sqrt(p.a) * p.scale],
        support: [0, Infinity],
        moments: (p) => [p.a * p.scale, Math.sqrt(p.a) * p.scale],
    },
    expon: {
        drag: ["scale"],
        pdf: (x, p) => (x < 0 ? 0 : Math.exp(-x / p.scale) / p.scale),
        range: (p) => [0, p.scale * Math.log(1000)],
        support: [0, Infinity],
        moments: (p) => [p.scale, p.scale],
    },
    weibull_min: {
        drag: ["scale", "c"],
        pdf: (x, p) => {
            if (x <= 0) return 0;
            const z = x / p.scale;
            return (p.c / p.scale) * z ** (p.c - 1) * Math.exp(-(z ** p.c));
        },
        range: (p) => [0, p.scale * Math.log(1000) ** (1 / p.c)],
        support: [0, Infinity],
        moments: (p) => {
            const g1 = Math.exp(logGamma(1 + 1 / p.c));
            const g2 = Math.exp(logGamma(1 + 2 / p.c));
            return [p.scale * g1, p.scale * Math.sqrt(g2 - g1 * g1)];
        },
    },
    uniform: {
        drag: ["loc", "scale"],
        pdf: (x, p) => (x >= p.loc && x <= p.loc + p.scale ? 1 / p.scale : 0),
        range: (p) => [p.loc, p.loc + p.scale],
        support: [-Infinity, Infinity],
        moments: (p) => [p.loc + p.scale / 2, p.scale / Math.sqrt(12)],
    },
    laplace: {
        drag: ["loc", "scale"],
        pdf: (x, p) => Math.exp(-Math.abs(x - p.loc) / p.scale) / (2 * p.scale),
        range: (p) => [p.loc - 6.5 * p.scale, p.loc + 6.5 * p.scale],
        support: [-Infinity, Infinity],
        moments: (p) => [p.loc, Math.SQRT2 * p.scale],
    },
    logistic: {
        drag: ["loc", "scale"],
        pdf: (x, p) => 1 / (4 * p.scale * Math.cosh((x - p.loc) / p.scale / 2) ** 2),
        range: (p) => [p.loc - 7 * p.scale, p.loc + 7 * p.scale],
        support: [-Infinity, Infinity],
        moments: (p) => [p.loc, (p.scale * Math.PI) / Math.sqrt(3)],
    },
    beta: {
        drag: ["a", "b"],
        pdf: (x, p) => x <= 0 || x >= 1 ? 0
            : Math.exp((p.a - 1) * Math.log(x) + (p.b - 1) * Math.log(1 - x)
                - (logGamma(p.a) + logGamma(p.b) - logGamma(p.a + p.b))),
        range: () => [0, 1],
        support: [0, 1],
        moments: (p) => {
            const n = p.a + p.b;
            return [p.a / n, Math.sqrt((p.a * p.b) / (n * n * (n + 1)))];
        },
    },
    poisson: {
        drag: ["mu"],
        discrete: true,
        pdf: (k, p) => (k < 0 ? 0 : Math.exp(k * Math.log(p.mu) - p.mu - logGamma(k + 1))),
        range: (p) => [0, Math.ceil(p.mu + 4 * Math.sqrt(p.mu) + 1)],
        support: [0, Infinity],
        moments: (p) => [p.mu, Math.sqrt(p.mu)],
    },
    binom: {
        drag: ["p", "n"],
        discrete: true,
        integer: ["n"],
        pdf: (k, p) => (k < 0 || k > p.n ? 0
            : Math.exp(logGamma(p.n + 1) - logGamma(k + 1) - logGamma(p.n - k + 1)
                + k * Math.log(p.p) + (p.n - k) * Math.log1p(-p.p))),
        // Only the bulk: with n = 1000 the full 0..n would be a thousand slivers.
        range: (p) => {
            const mean = p.n * p.p;
            const sd = Math.sqrt(p.n * p.p * (1 - p.p));
            return [Math.max(0, Math.floor(mean - 4.5 * sd)), Math.min(p.n, Math.ceil(mean + 4.5 * sd))];
        },
        support: [0, Infinity],
        moments: (p) => [p.n * p.p, Math.sqrt(p.n * p.p * (1 - p.p))],
    },
    nbinom: {
        drag: ["p", "n"],
        discrete: true,
        pdf: (k, p) => (k < 0 ? 0
            : Math.exp(logGamma(k + p.n) - logGamma(p.n) - logGamma(k + 1)
                + p.n * Math.log(p.p) + k * Math.log1p(-p.p))),
        range: (p) => {
            const mean = (p.n * (1 - p.p)) / p.p;
            const sd = Math.sqrt(p.n * (1 - p.p)) / p.p;
            return [Math.max(0, Math.floor(mean - 4 * sd)), Math.ceil(mean + 5 * sd)];
        },
        support: [0, Infinity],
        moments: (p) => [(p.n * (1 - p.p)) / p.p, Math.sqrt(p.n * (1 - p.p)) / p.p],
    },
    geom: {
        drag: ["p"],
        discrete: true,
        pdf: (k, p) => (k < 1 ? 0 : Math.exp((k - 1) * Math.log1p(-p.p)) * p.p),
        // Up to the 99.9th percentile.
        range: (p) => [1, Math.max(2, Math.ceil(Math.log(0.001) / Math.log1p(-p.p)))],
        support: [1, Infinity],
        moments: (p) => [1 / p.p, Math.sqrt(1 - p.p) / p.p],
    },
    randint: {
        drag: ["low", "high"],
        discrete: true,
        integer: ["low", "high"],
        pdf: (k, p) => (k >= p.low && k < p.high ? 1 / (p.high - p.low) : 0),
        range: (p) => [p.low, p.high - 1],
        support: [-Infinity, Infinity],
        moments: (p) => {
            const w = p.high - p.low;
            return [(p.low + p.high - 1) / 2, Math.sqrt((w * w - 1) / 12)];
        },
        // high is excluded, so low must stay below it: dragging high down pushes
        // low along, and low stops just under high.
        constrain: (p) => {
            if (p.low >= p.high) p.low = p.high - 1;
        },
    },
};

// Walk up through shadow roots looking for a theme marker; fall back to the OS.
function isDark(el) {
    let node = el;
    while (node) {
        if (node.closest) {
            if (node.closest('.dark, .dark-theme, [data-theme="dark"]')) return true;
            if (node.closest('.light, .light-theme, [data-theme="light"]')) return false;
        }
        const root = node.getRootNode ? node.getRootNode() : null;
        node = root && root.host ? root.host : null;
    }
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
}

function palette(dark) {
    return dark
        ? { bg: "#1f2328", border: "#3d444d", text: "#e6edf3", muted: "#9198a1",
            fill: "rgba(88, 166, 255, 0.18)", band: "rgba(88, 166, 255, 0.35)",
            line: "#58a6ff", ghost: "#9198a1" }
        : { bg: "#ffffff", border: "#d0d7de", text: "#1f2328", muted: "#656d76",
            fill: "rgba(0, 102, 204, 0.12)", band: "rgba(0, 102, 204, 0.28)",
            line: "#0066cc", ghost: "#8c959f" };
}

function svgEl(tag, attrs) {
    const node = document.createElementNS(SVG_NS, tag);
    for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
    return node;
}

// Sample a pdf on [from, to] as [x, y] pairs.
function sampleCurve(family, p, from, to) {
    const pts = [];
    for (let i = 0; i <= N_POINTS; i++) {
        const x = from + ((to - from) * i) / N_POINTS;
        pts.push([x, family.pdf(x, p)]);
    }
    return pts;
}

function render({ model, el }) {
    let params = { ...model.get("params") };
    let dragging = false;

    const family = () => FAMILIES[model.get("distribution")];

    const container = document.createElement("div");
    container.classList.add("tangle-container");
    el.style.display = "inline-flex";
    el.appendChild(container);

    const valueEl = document.createElement("span");
    valueEl.className = "tangle-value";
    valueEl.style.color = "#0066cc";
    valueEl.style.textDecoration = "underline";
    valueEl.style.cursor = "move";
    valueEl.style.touchAction = "none";
    valueEl.style.userSelect = "none";
    container.appendChild(valueEl);

    function fmt(v) {
        return v.toFixed(model.get("digits"));
    }

    // Whole-number parameters (binom's n) never show decimals.
    function fmtParam(name, v) {
        return (family().integer || []).includes(name) ? v.toFixed(0) : fmt(v);
    }

    // Fill the template: {name} or {name:.Nf}, where name is a parameter, mean or sd.
    function renderText() {
        const [mean, sd] = family().moments(params);
        const values = { ...params, mean, sd };
        return model.get("template").replace(/\{(\w+)(?::\.(\d+)f)?\}/g, (match, name, decimals) => {
            if (!(name in values)) return match;
            return decimals === undefined ? fmtParam(name, values[name]) : values[name].toFixed(Number(decimals));
        });
    }

    function renderValue() {
        const [h, v] = family().drag;
        valueEl.title = v ? `Drag left/right for ${h}, up/down for ${v}` : `Drag left/right for ${h}`;
        valueEl.textContent = renderText();
    }

    // Python-side changes. Ignored mid-drag so a late echo can't yank the value back.
    ["params", "distribution", "bounds", "steps", "pixels_per_step", "template", "digits"]
        .forEach((name) => {
            model.on(`change:${name}`, () => {
                if (dragging) return;
                params = { ...model.get("params") };
                renderValue();
            });
        });

    // While dragging only `live_params` moves; `params` keeps the old (committed)
    // values until release, so Python sees both old and new at once.
    // model.set() is local, so we set on every move and throttle save_changes().
    let syncTimer = null;
    let syncPending = false;

    function queueLiveSync() {
        model.set("live_params", { ...params });
        const ms = model.get("sync_throttle_ms");
        if (ms <= 0) {
            model.save_changes();
            return;
        }
        // A trailing flush makes sure the last position is never dropped.
        syncPending = true;
        if (syncTimer !== null) return;
        syncTimer = setTimeout(() => {
            syncTimer = null;
            if (syncPending) {
                syncPending = false;
                model.save_changes();
            }
        }, ms);
    }

    function commit() {
        clearTimeout(syncTimer);
        syncTimer = null;
        syncPending = false;
        model.set("params", { ...params });
        model.set("live_params", { ...params });
        model.set("dragging", false);
        model.save_changes();
    }

    // ---- Floating chart ---------------------------------------------------

    let overlay = null;
    let chart = null; // { svg, colors, start }

    function showOverlay() {
        // Clear any preview left behind, e.g. by a view that was re-rendered
        // mid-drag and never got its pointerup.
        document.querySelectorAll("[data-tangle-distribution-overlay]").forEach((n) => n.remove());
        const colors = palette(isDark(el));
        overlay = document.createElement("div");
        overlay.dataset.tangleDistributionOverlay = "";
        Object.assign(overlay.style, {
            position: "fixed",
            zIndex: "99999",
            pointerEvents: "none",
            background: colors.bg,
            border: `1px solid ${colors.border}`,
            borderRadius: "8px",
            boxShadow: "0 6px 24px rgba(0, 0, 0, 0.18)",
            padding: "6px",
            opacity: "0",
            transition: "opacity 120ms ease",
            fontFamily: "system-ui, -apple-system, sans-serif",
            fontSize: "11px",
        });
        const svg = svgEl("svg", { width: CHART_W, height: CHART_H, viewBox: `0 0 ${CHART_W} ${CHART_H}` });
        svg.style.display = "block";
        overlay.appendChild(svg);
        document.body.appendChild(overlay);

        // Place above the number, or below when there is no room up top.
        const rect = valueEl.getBoundingClientRect();
        const boxW = CHART_W + 14;
        const boxH = CHART_H + 14;
        const left = Math.min(Math.max(8, rect.left + rect.width / 2 - boxW / 2), window.innerWidth - boxW - 8);
        let top = rect.top - boxH - 10;
        if (top < 8) top = rect.bottom + 10;
        overlay.style.left = `${left}px`;
        overlay.style.top = `${top}px`;

        chart = { svg, colors, start: { ...params } };
        drawChart();
        requestAnimationFrame(() => { if (overlay) overlay.style.opacity = "1"; });
    }

    function hideOverlay() {
        if (!overlay) return;
        const node = overlay;
        overlay = null;
        chart = null;
        node.style.opacity = "0";
        setTimeout(() => node.remove(), 150);
    }

    function drawChart() {
        if (!chart) return;
        const { svg, colors, start } = chart;
        const fam = family();

        // Fit both the start-of-drag distribution and the current one, recomputed
        // every frame: the view zooms back in when you reverse, and the dashed
        // start shape stays on screen as the reference to compare against.
        const [startLo, startHi] = fam.range(start);
        const [nowLo, nowHi] = fam.range(params);
        const lo = Math.min(startLo, nowLo);
        const hi = Math.max(startHi, nowHi);
        // Discrete bars are centred on whole numbers, so leave half a bar either side.
        const pad = fam.discrete ? 0.5 : 0.05 * (hi - lo);
        const xLo = fam.discrete ? lo - pad : Math.max(fam.support[0], lo - pad);
        const xHi = fam.discrete ? hi + pad : Math.min(fam.support[1], hi + pad);

        const x0 = PAD.left;
        const x1 = CHART_W - PAD.right;
        const base = CHART_H - PAD.bottom;
        const yTop = PAD.top;
        const sx = (x) => x0 + ((x - xLo) / (xHi - xLo)) * (x1 - x0);
        const [mean, sd] = fam.moments(params);

        const marks = fam.discrete
            ? discreteMarks(fam, start, [startLo, startHi], [nowLo, nowHi], sx, base, yTop, mean, sd, colors)
            : continuousMarks(fam, start, [startLo, startHi], [nowLo, nowHi], sx, base, yTop, mean, sd, colors);
        svg.replaceChildren(
            svgEl("line", { x1: x0, x2: x1, y1: base, y2: base, stroke: colors.border }),
            ...marks,
        );

        const label = (text, x, y, anchor, fill, weight) => {
            const t = svgEl("text", { x, y, "text-anchor": anchor, fill, "font-weight": weight || "normal" });
            t.textContent = text;
            svg.appendChild(t);
        };
        const [h, v] = fam.drag;
        label(`↔ ${h} = ${fmtParam(h, params[h])}`, x0, 13, "start", colors.text, 600);
        if (v) label(`↕ ${v} = ${fmtParam(v, params[v])}`, x1, 13, "end", colors.text, 600);
        const tick = (x) => (fam.discrete ? x.toFixed(0) : fmt(x));
        label(tick(fam.discrete ? lo : xLo), x0, CHART_H - 5, "start", colors.muted);
        label(tick(fam.discrete ? hi : xHi), x1, CHART_H - 5, "end", colors.muted);
    }

    // Filled curve, a darker band over mean ± sd, a mean line, and the dashed start curve.
    function continuousMarks(fam, start, [startLo, startHi], [nowLo, nowHi], sx, base, yTop, mean, sd, colors) {
        const startPts = sampleCurve(fam, start, startLo, startHi);
        const nowPts = sampleCurve(fam, params, nowLo, nowHi);
        // Skip the end points for the height: gamma/beta shapes below 1 shoot to
        // infinity at the edge of their support, which would flatten everything.
        const interior = (pts) => pts.slice(2, -2).map(([, y]) => y).filter(Number.isFinite);
        const yMax = Math.max(...interior(startPts), ...interior(nowPts)) * 1.1 || 1;
        const sy = (y) => base - Math.min(Number.isFinite(y) ? y / yMax : 1.1, 1.1) * (base - yTop);
        const line = (pts) => pts.map(([x, y]) => `${sx(x).toFixed(1)},${sy(y).toFixed(1)}`).join(" L");
        // Start and end on the baseline so flat-topped shapes (uniform) get their edges.
        const outline = (pts) =>
            `M${sx(pts[0][0]).toFixed(1)},${base} L${line(pts)} L${sx(pts[pts.length - 1][0]).toFixed(1)},${base}`;
        const bandPts = sampleCurve(fam, params, Math.max(nowLo, mean - sd), Math.min(nowHi, mean + sd));
        return [
            svgEl("path", {
                d: outline(startPts),
                fill: "none", stroke: colors.ghost, "stroke-width": 1, "stroke-dasharray": "3 3",
            }),
            svgEl("path", { d: outline(nowPts) + " Z", fill: colors.fill, stroke: colors.line, "stroke-width": 1.5 }),
            svgEl("path", { d: outline(bandPts) + " Z", fill: colors.band, stroke: "none" }),
            svgEl("line", {
                x1: sx(mean), x2: sx(mean), y1: base, y2: sy(fam.pdf(mean, params)),
                stroke: colors.line, "stroke-width": 1.5,
            }),
        ];
    }

    // One bar per whole number (darker within mean ± sd), a mean line, and the
    // start distribution as a dashed step outline.
    function discreteMarks(fam, start, [startLo, startHi], [nowLo, nowHi], sx, base, yTop, mean, sd, colors) {
        const ks = (from, to) => Array.from({ length: to - from + 1 }, (_, i) => from + i);
        const startBars = ks(startLo, startHi).map((k) => [k, fam.pdf(k, start)]);
        const nowBars = ks(nowLo, nowHi).map((k) => [k, fam.pdf(k, params)]);
        const yMax = Math.max(...startBars.map(([, y]) => y), ...nowBars.map(([, y]) => y)) * 1.1 || 1;
        const sy = (y) => base - (y / yMax) * (base - yTop);
        const unit = sx(1) - sx(0);
        const barW = Math.max(1, unit * 0.7);

        const marks = nowBars.map(([k, y]) => svgEl("rect", {
            x: (sx(k) - barW / 2).toFixed(1), y: sy(y).toFixed(1),
            width: barW.toFixed(1), height: Math.max(0, base - sy(y)).toFixed(1),
            fill: Math.abs(k - mean) <= sd ? colors.band : colors.fill,
        }));
        const steps = startBars.map(([k, y]) =>
            `L${(sx(k) - unit / 2).toFixed(1)},${sy(y).toFixed(1)} L${(sx(k) + unit / 2).toFixed(1)},${sy(y).toFixed(1)}`);
        const ghostStart = (sx(startLo) - unit / 2).toFixed(1);
        const ghostEnd = (sx(startHi) + unit / 2).toFixed(1);
        marks.push(svgEl("path", {
            d: `M${ghostStart},${base} ${steps.join(" ")} L${ghostEnd},${base}`,
            fill: "none", stroke: colors.ghost, "stroke-width": 1, "stroke-dasharray": "3 3",
        }));
        marks.push(svgEl("line", {
            x1: sx(mean), x2: sx(mean), y1: base, y2: yTop,
            stroke: colors.line, "stroke-width": 1.5,
        }));
        return marks;
    }

    // ---- Dragging ---------------------------------------------------------

    // Shift = 10x coarser, Alt/Option = 10x finer (Alt wins if both are held).
    function modMultiplier(ev) {
        if (ev.altKey) return 0.1;
        if (ev.shiftKey) return 10;
        return 1;
    }

    function stepsFrom(delta) {
        const beyond = Math.sign(delta) * Math.max(0, Math.abs(delta) - DEAD_ZONE);
        return Math.trunc(beyond / model.get("pixels_per_step"));
    }

    // Move one parameter by n steps, respecting its bounds (either end may be null).
    function moved(name, from, n, mult) {
        const [low, high] = model.get("bounds")[name];
        const integer = (family().integer || []).includes(name);
        // Whole numbers ignore Alt's 10x finer mode and always land on an integer.
        let v = from + n * model.get("steps")[name] * (integer ? Math.max(1, mult) : mult);
        if (integer) v = Math.round(v);
        if (low !== null) v = Math.max(low, v);
        if (high !== null) v = Math.min(high, v);
        return +v.toFixed(10); // drop float noise like 0.30000000000000004
    }

    let drag = null; // anchor state for the active drag

    function applyMove(clientX, clientY, mult) {
        if (mult !== drag.mult) {
            // Rebase the anchor so the new scale applies from here without a jump.
            drag = { x: clientX, y: clientY, params: { ...params }, mult };
        }
        const [h, v] = family().drag;
        params[h] = moved(h, drag.params[h], stepsFrom(clientX - drag.x), mult);
        // Screen y grows downward, so dragging up (negative dy) increases it.
        if (v) params[v] = moved(v, drag.params[v], stepsFrom(drag.y - clientY), mult);
        if (family().constrain) family().constrain(params);
        renderValue();
        drawChart();
        queueLiveSync();
    }

    let lastX = 0;
    let lastY = 0;

    function onPointerDown(e) {
        if (e.button !== 0) return;
        e.preventDefault();
        valueEl.setPointerCapture(e.pointerId);
        dragging = true;
        model.set("dragging", true);
        model.save_changes();
        lastX = e.clientX;
        lastY = e.clientY;
        drag = { x: e.clientX, y: e.clientY, params: { ...params }, mult: modMultiplier(e) };
        valueEl.style.cursor = "grabbing";
        showOverlay();
        document.addEventListener("keydown", onKeyChange);
        document.addEventListener("keyup", onKeyChange);
    }

    function onPointerMove(e) {
        if (!dragging) return;
        // No button held means we missed the release; stop instead of scrubbing on.
        if (e.buttons === 0) {
            endDrag();
            return;
        }
        lastX = e.clientX;
        lastY = e.clientY;
        applyMove(e.clientX, e.clientY, modMultiplier(e));
    }

    function onKeyChange(e) {
        if (dragging) applyMove(lastX, lastY, modMultiplier(e));
    }

    // Ends a drag however it stops: release, cancel, lost capture, context menu,
    // window blur, or a click elsewhere. Always takes the preview down.
    function endDrag() {
        if (dragging) {
            // Commit while `dragging` is still true: model.set("params") fires our
            // own change handler, which must not reset the local params mid-commit.
            commit();
            dragging = false;
            drag = null;
            valueEl.style.cursor = "move";
            document.removeEventListener("keydown", onKeyChange);
            document.removeEventListener("keyup", onKeyChange);
        }
        hideOverlay();
    }

    function onDocumentPointerDown(e) {
        // composedPath() sees through the shadow DOM marimo renders widgets in.
        if (!e.composedPath().includes(valueEl)) endDrag();
    }

    valueEl.addEventListener("pointerdown", onPointerDown);
    valueEl.addEventListener("pointermove", onPointerMove);
    valueEl.addEventListener("pointerup", endDrag);
    valueEl.addEventListener("pointercancel", endDrag);
    valueEl.addEventListener("lostpointercapture", endDrag);
    valueEl.addEventListener("contextmenu", endDrag);
    window.addEventListener("blur", endDrag);
    document.addEventListener("pointerdown", onDocumentPointerDown, true);

    renderValue();

    return () => {
        clearTimeout(syncTimer);
        document.removeEventListener("keydown", onKeyChange);
        document.removeEventListener("keyup", onKeyChange);
        window.removeEventListener("blur", endDrag);
        document.removeEventListener("pointerdown", onDocumentPointerDown, true);
        if (overlay) overlay.remove();
    };
}

export default { render };
