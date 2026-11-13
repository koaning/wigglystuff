// WidgetFlow's overlay. It owns no content: it climbs out of its shadow root
// to the [data-wf-root] container that WidgetFlow laid out and draws the
// arrows, notes, groups and toolbar there, so everything shares one
// coordinate space with the live widget cards.
const SVGNS = "http://www.w3.org/2000/svg";
const CORNER = 8;
const HEAD_LEN = 7;
const HEAD_HALF = 3.6;
const GAP = 2;
const STUB = 16;
const NORMAL = { top: [0, -1], bottom: [0, 1], left: [-1, 0], right: [1, 0] };
const CHEVRON =
  '<svg width="10" height="10" viewBox="0 0 10 10"><path d="M2 3.5 L5 6.5 L8 3.5" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>';

function resolveDark(el) {
  for (let n = el; n; n = n.parentNode || n.host) {
    if (n.nodeType !== 1) continue;
    const cls = n.classList;
    const mode = n.getAttribute("data-theme") || n.getAttribute("data-color-mode");
    if (cls.contains("dark") || cls.contains("dark-theme") || mode === "dark") return true;
    if (cls.contains("light") || cls.contains("light-theme") || mode === "light") return false;
  }
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false;
}

function svgEl(tag, attrs) {
  const e = document.createElementNS(SVGNS, tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  return e;
}

const dist = (p, q) => Math.hypot(q.x - p.x, q.y - p.y);
const dirOf = (p, q) => [Math.sign(Math.round(q.x - p.x)), Math.sign(Math.round(q.y - p.y))];
const same = (u, v) => u[0] === v[0] && u[1] === v[1];

// Axis-aligned polyline from exit point `a` to arrow tip `b`. Each port
// carries its outward normal; try a few elbow shapes and keep the one with the
// fewest bends that leaves `a` along its normal and enters `b` against its own.
function orthoRoute(a, b) {
  const d0 = [a.nx, a.ny];
  const d1 = [-b.nx, -b.ny];
  const p1 = { x: a.x + a.nx * STUB, y: a.y + a.ny * STUB };
  const p2 = { x: b.x + b.nx * STUB, y: b.y + b.ny * STUB };
  const xm = (p1.x + p2.x) / 2;
  const ym = (p1.y + p2.y) / 2;
  const shapes = [
    [],
    [{ x: a.x, y: b.y }],
    [{ x: b.x, y: a.y }],
    [p1, { x: p1.x, y: p2.y }, p2],
    [p1, { x: p2.x, y: p1.y }, p2],
    [p1, { x: p1.x, y: ym }, { x: p2.x, y: ym }, p2],
    [p1, { x: xm, y: p1.y }, { x: xm, y: p2.y }, p2],
  ];
  let best = null;
  for (const mid of shapes) {
    const pts = simplify([a, ...mid, b]);
    if (!pts) continue;
    const dirs = pts.slice(1).map((q, i) => dirOf(pts[i], q));
    if (!same(dirs[0], d0) || !same(dirs[dirs.length - 1], d1)) continue;
    if (dirs.some((d, i) => i && d[0] === -dirs[i - 1][0] && d[1] === -dirs[i - 1][1])) continue;
    if (dist(pts[pts.length - 2], b) < HEAD_LEN + 3) continue;
    let len = 0;
    for (let i = 1; i < pts.length; i++) len += dist(pts[i - 1], pts[i]);
    const score = (pts.length - 2) * 1000 + len;
    if (!best || score < best.score) best = { pts, score };
  }
  return best ? best.pts : [a, p1, { x: p1.x, y: p2.y }, p2, b];
}

function simplify(pts) {
  const out = [];
  for (const p of pts) {
    if (out.length && dist(out[out.length - 1], p) < 0.5) continue;
    if (out.length && Math.abs(out[out.length - 1].x - p.x) > 0.5 && Math.abs(out[out.length - 1].y - p.y) > 0.5) return null;
    if (out.length > 1 && same(dirOf(out[out.length - 2], out[out.length - 1]), dirOf(out[out.length - 1], p))) out.pop();
    out.push(p);
  }
  return out.length > 1 ? out : null;
}

function roundedPath(pts) {
  let d = `M ${pts[0].x} ${pts[0].y}`;
  for (let i = 1; i < pts.length - 1; i++) {
    const [p, c, n] = [pts[i - 1], pts[i], pts[i + 1]];
    const r = Math.min(CORNER, dist(p, c) / 2, dist(c, n) / 2);
    const u = dirOf(p, c);
    const v = dirOf(c, n);
    d += ` L ${c.x - u[0] * r} ${c.y - u[1] * r} Q ${c.x} ${c.y} ${c.x + v[0] * r} ${c.y + v[1] * r}`;
  }
  const last = pts[pts.length - 1];
  return `${d} L ${last.x} ${last.y}`;
}

function portPoint(box, side, at, out) {
  const [nx, ny] = NORMAL[side];
  const x = side === "left" ? box.left : side === "right" ? box.right : box.left + at * (box.right - box.left);
  const y = side === "top" ? box.top : side === "bottom" ? box.bottom : box.top + at * (box.bottom - box.top);
  return { x: x + nx * out, y: y + ny * out, nx, ny };
}

// The side of `box` closest to (x, y), and where along it (snapped to 5%).
function nearestPort(box, x, y) {
  const w = box.right - box.left;
  const h = box.bottom - box.top;
  const clamp = (v) => Math.min(1, Math.max(0, v));
  const tx = clamp((x - box.left) / w);
  const ty = clamp((y - box.top) / h);
  const px = box.left + tx * w;
  const py = box.top + ty * h;
  const [side, t] = [
    ["top", tx, Math.hypot(x - px, y - box.top)],
    ["bottom", tx, Math.hypot(x - px, y - box.bottom)],
    ["left", ty, Math.hypot(x - box.left, y - py)],
    ["right", ty, Math.hypot(x - box.right, y - py)],
  ].sort((p, q) => p[2] - q[2])[0];
  return { side, at: Math.round(Math.min(0.9, Math.max(0.1, t)) * 20) / 20 };
}

function colorVars(node, color) {
  node.style.setProperty("--wf-c-light", color.light);
  node.style.setProperty("--wf-c-dark", color.dark);
}

function render({ model, el }) {
  const host = el.getRootNode().host || el;
  Object.assign(host.style, { position: "absolute", width: "0", height: "0" });
  const root = host.closest("[data-wf-root]");
  if (!root) return;
  const board = root.querySelector(":scope > .wf-board");
  root.querySelectorAll(":scope > .wf-toolbar").forEach((n) => n.remove());
  board.querySelectorAll(":scope > .wf-svg, :scope > .wf-labels").forEach((n) => n.remove());

  const routes = model.get("routes");
  const edges = model.get("edges");
  const edgeLabels = model.get("edge_labels");
  const ports = JSON.parse(JSON.stringify(model.get("ports") || {}));
  let editing = false;
  let dragging = null;
  const colors = model.get("colors");
  const edgeColors = model.get("edge_colors") || {};
  const beside = model.get("beside") || {};
  const groups = model.get("groups");
  let direction = model.get("direction");
  const collapsed = new Set(model.get("collapsed"));
  let selected = model.get("selected") || null;
  let hovered = null;

  const groupSvg = svgEl("svg", { class: "wf-svg wf-svg--groups" });
  const svg = svgEl("svg", { class: "wf-svg wf-svg--edges" });
  const labels = document.createElement("div");
  labels.className = "wf-labels";
  board.append(groupSvg, svg, labels);

  const cards = {};
  const items = {};
  root.querySelectorAll(".wf-card[data-wf-node]").forEach((c) => {
    if (c.closest("[data-wf-root]") !== root) return;
    cards[c.dataset.wfNode] = c;
    items[c.dataset.wfNode] = c.parentElement;
  });
  const lanes = {};
  board.querySelectorAll(":scope > .wf-layer > .wf-lane").forEach((l) => { lanes[l.dataset.wfNode] = l; });
  const layerEls = [...board.children].filter((n) => n.classList.contains("wf-layer"));
  const rowOf = {};
  layerEls.forEach((layer, i) => {
    for (const child of layer.querySelectorAll(":scope > *, :scope > .wf-cluster > *")) {
      const id = child.dataset.wfItem || child.dataset.wfNode;
      if (id) rowOf[id] = i;
    }
  });

  // ---- theme ---------------------------------------------------------------
  const theme = model.get("theme");
  function setTheme() {
    const dark = theme === "dark" || (theme === "auto" && resolveDark(root));
    root.classList.toggle("wf--dark", dark);
  }
  setTheme();
  const themeObserver = new MutationObserver(setTheme);
  [document.documentElement, document.body].forEach((n) =>
    themeObserver.observe(n, { attributes: true, attributeFilter: ["class", "data-theme"] }));

  // ---- toolbar -------------------------------------------------------------
  const dirButtons = {};
  let foldAll;
  let portBtn;
  if (model.get("toolbar")) {
    const bar = document.createElement("div");
    bar.className = "wf-toolbar";
    const seg = document.createElement("div");
    seg.className = "wf-seg";
    for (const [d, text] of [["down", "↓ top-down"], ["right", "→ left-right"]]) {
      const b = document.createElement("button");
      b.className = "wf-btn";
      b.textContent = text;
      b.addEventListener("click", () => setDirection(d));
      dirButtons[d] = b;
      seg.append(b);
    }
    const seg2 = document.createElement("div");
    seg2.className = "wf-seg";
    foldAll = document.createElement("button");
    foldAll.className = "wf-btn";
    foldAll.addEventListener("click", () => {
      const ids = Object.keys(cards);
      const fold = ids.some((id) => !collapsed.has(id));
      ids.forEach((id) => (fold ? collapsed.add(id) : collapsed.delete(id)));
      applyCollapsed();
    });
    seg2.append(foldAll);
    const seg3 = document.createElement("div");
    seg3.className = "wf-seg";
    portBtn = document.createElement("button");
    portBtn.className = "wf-btn";
    portBtn.textContent = "✥ ports";
    portBtn.title = "drag arrow ends onto any side of a card";
    portBtn.addEventListener("click", () => {
      editing = !editing;
      portBtn.classList.toggle("is-on", editing);
      root.classList.toggle("wf--edit", editing);
      showCode();
      draw();
    });
    seg3.append(portBtn);
    bar.append(seg, seg2, seg3);
    root.prepend(bar);
  }
  root.querySelectorAll(":scope > .wf-ports-code").forEach((n) => n.remove());
  const code = document.createElement("div");
  code.className = "wf-ports-code";
  root.append(code);

  const pyStr = (v) => JSON.stringify(v);
  function pyPort(p) {
    return p.at == null ? pyStr(p.side) : `(${pyStr(p.side)}, ${p.at})`;
  }
  function showCode() {
    const lines = [];
    for (const [s, d] of edges) {
      const key = `${s}->${d}`;
      const p = ports[key];
      if (!p || !(p.exit || p.enter)) continue;
      const opts = [];
      if (edgeLabels[key]) opts.push(`"label": ${pyStr(edgeLabels[key])}`);
      if (p.exit) opts.push(`"exit": ${pyPort(p.exit)}`);
      if (p.enter) opts.push(`"enter": ${pyPort(p.enter)}`);
      lines.push(`(${pyStr(s)}, ${pyStr(d)}, {${opts.join(", ")}}),`);
    }
    code.replaceChildren();
    if (!editing) return;
    const hint = document.createElement("div");
    hint.className = "wf-ports-hint";
    hint.textContent = lines.length
      ? "drag the dots onto any side of a card · double-click a dot to reset · paste these edges back into Python:"
      : "drag the dots onto any side of a card · double-click a dot to reset";
    code.append(hint);
    if (!lines.length) return;
    const pre = document.createElement("pre");
    pre.textContent = lines.join("\n");
    const copy = document.createElement("button");
    copy.className = "wf-btn wf-copy";
    copy.textContent = "copy";
    copy.addEventListener("click", () => {
      navigator.clipboard?.writeText(lines.join("\n"));
      copy.textContent = "copied";
      setTimeout(() => (copy.textContent = "copy"), 1200);
    });
    code.append(pre, copy);
  }

  function resolveNoteSides() {
    for (const [id, item] of Object.entries(items)) {
      const note = item.querySelector(":scope > .wf-note");
      if (!note) continue;
      const side = note.dataset.side;
      item.dataset.noteSide = side === "auto" ? (direction === "down" ? "right" : "bottom") : side;
    }
  }

  function setDirection(d) {
    direction = d;
    root.dataset.direction = d;
    Object.entries(dirButtons).forEach(([k, b]) => b.classList.toggle("is-on", k === d));
    resolveNoteSides();
    model.set("direction", d);
    model.save_changes();
    draw();
  }

  function applyCollapsed() {
    for (const [id, card] of Object.entries(cards)) {
      card.classList.toggle("is-collapsed", collapsed.has(id));
      items[id].classList.toggle("is-collapsed", collapsed.has(id));
    }
    if (foldAll) {
      const all = Object.keys(cards).every((id) => collapsed.has(id));
      foldAll.textContent = all ? "expand all" : "collapse all";
    }
    model.set("collapsed", [...collapsed]);
    model.save_changes();
    draw();
  }

  // ---- per-card controls -----------------------------------------------------
  for (const [id, card] of Object.entries(cards)) {
    const head = card.querySelector(":scope > .wf-head");
    const fold = head.querySelector(".wf-fold");
    fold.innerHTML = CHEVRON;
    fold.addEventListener("click", (e) => {
      e.stopPropagation();
      collapsed.has(id) ? collapsed.delete(id) : collapsed.add(id);
      applyCollapsed();
    });
    head.addEventListener("mouseenter", () => { hovered = id; applyFocus(); });
    head.addEventListener("mouseleave", () => { hovered = null; applyFocus(); });
    head.addEventListener("click", () => {
      selected = selected === id ? null : id;
      model.set("selected", selected || "");
      model.save_changes();
      applyFocus();
    });
  }

  // ---- geometry --------------------------------------------------------------
  // Route in (cross, main) coordinates: main runs along the flow (y when
  // flowing down, x when flowing right), cross runs across it.
  const down = () => direction === "down";
  const P = (c, m) => (down() ? `${c} ${m}` : `${m} ${c}`);
  const A = (r) => (down()
    ? { c0: r.left, c1: r.right, m0: r.top, m1: r.bottom }
    : { c0: r.top, c1: r.bottom, m0: r.left, m1: r.right });

  let edgeEls = [];

  function draw() {
    if (!root.isConnected) return;
    svg.replaceChildren();
    groupSvg.replaceChildren();
    labels.replaceChildren();
    edgeEls = [];
    const base = board.getBoundingClientRect();
    const rel = (n) => {
      const r = n.getBoundingClientRect();
      return { left: r.left - base.left, right: r.right - base.left, top: r.top - base.top, bottom: r.bottom - base.top };
    };
    const cardBox = {};
    for (const id in cards) cardBox[id] = rel(cards[id]);
    const boxOf = (id) => A(cardBox[id] || rel(lanes[id]));
    const layerBox = layerEls.map((l) => A(rel(l)));
    const mid = (b) => (b.c0 + b.c1) / 2;

    // groups: a dashed region around the member cards, label inside its corner
    for (const g of groups) {
      const boxes = g.nodes.filter((n) => cardBox[n]).map((n) => {
        const b = cardBox[n];
        const note = items[n].querySelector(":scope > .wf-note");
        if (!note || collapsed.has(n)) return b;
        const nb = rel(note);
        return { left: Math.min(b.left, nb.left), right: Math.max(b.right, nb.right), top: Math.min(b.top, nb.top), bottom: Math.max(b.bottom, nb.bottom) };
      });
      if (!boxes.length) continue;
      const pad = 12;
      const r = {
        left: Math.min(...boxes.map((b) => b.left)) - pad,
        right: Math.max(...boxes.map((b) => b.right)) + pad,
        top: Math.min(...boxes.map((b) => b.top)) - pad - 16,
        bottom: Math.max(...boxes.map((b) => b.bottom)) + pad,
      };
      const rect = svgEl("rect", { class: "wf-group", x: r.left, y: r.top, width: r.right - r.left, height: r.bottom - r.top, rx: 14 });
      if (g.color) rect.style.setProperty("--wf-g", g.color);
      groupSvg.append(rect);
      const lab = document.createElement("div");
      lab.className = "wf-group-label";
      lab.textContent = g.label || g.name;
      if (g.color) lab.style.setProperty("--wf-g", g.color);
      Object.assign(lab.style, { left: `${r.left + 12}px`, top: `${r.top + 8}px` });
      labels.append(lab);
    }

    // 1. each arrow's cross positions: the stem, any lanes, the landing slot
    const keyOf = (r) => `${r[0]}->${r[r.length - 1]}`;
    const custom = (r) => {
      const p = ports[keyOf(r)];
      return (p && (p.exit || p.enter)) || r[0] in beside || r[r.length - 1] in beside;
    };
    const all = routes.filter((r) => r.every((id) => cards[id] || lanes[id]) && r.every((id) => id in rowOf));
    const live = all.filter((r) => !custom(r));
    const handles = [];
    const incoming = {};
    live.forEach((r, i) => (incoming[r[r.length - 1]] ||= []).push(i));
    const arrows = live.map((route) => {
      const src = route[0];
      return { src, dst: route[route.length - 1], route, xs: [mid(boxOf(src)), ...route.slice(1, -1).map((w) => mid(boxOf(w)))] };
    });
    for (const [dst, list] of Object.entries(incoming)) {
      const b = boxOf(dst);
      const w = b.c1 - b.c0;
      const span = Math.min(w * 0.6, 40 * list.length);
      list.sort((p, q) => arrows[p].xs[arrows[p].xs.length - 1] - arrows[q].xs[arrows[q].xs.length - 1]);
      list.forEach((ai, k) => {
        arrows[ai].xs.push(mid(b) - span / 2 + (span * (k + 0.5)) / list.length);
        arrows[ai].labelLeft = list.length > 1 && k < (list.length - 1) / 2;
      });
    }

    // 2. one track per producer in each gap it jogs through, so arrows from
    //    the same node share a bus, ordered by where they start
    const jogs = {};
    for (const a of arrows) {
      a.xs.forEach((x, k) => {
        if (k === a.xs.length - 1 || Math.abs(a.xs[k + 1] - x) < 1) return;
        const g = rowOf[a.route[k]];
        (jogs[g] ||= new Set()).add(a.src);
      });
    }
    const tracks = {};
    for (const [g, set] of Object.entries(jogs)) tracks[g] = [...set].sort((p, q) => mid(boxOf(p)) - mid(boxOf(q)));
    const trackM = (g, src) => {
      const top = layerBox[g].m1;
      const h = layerBox[+g + 1].m0 - top;
      return top + (h * (tracks[g].indexOf(src) + 1)) / (tracks[g].length + 1);
    };

    // 3. draw: out of the source, jog along the track, into the target
    for (const a of arrows) {
      const srcB = boxOf(a.src);
      const dstB = boxOf(a.dst);
      let d = `M ${P(a.xs[0], srcB.m1)}`;
      let lastM = layerBox[rowOf[a.dst] - 1].m1;
      a.xs.forEach((x, k) => {
        if (k === a.xs.length - 1) return;
        const next = a.xs[k + 1];
        if (Math.abs(next - x) < 1) return;
        const ty = trackM(rowOf[a.route[k]], a.src);
        const s = Math.sign(next - x);
        const r = Math.min(CORNER, Math.abs(next - x) / 2);
        d += ` L ${P(x, ty - r)} Q ${P(x, ty)} ${P(x + s * r, ty)}`;
        d += ` L ${P(next - s * r, ty)} Q ${P(next, ty)} ${P(next, ty + r)}`;
        lastM = Math.max(lastM, ty);
      });
      const end = a.xs[a.xs.length - 1];
      const tip = dstB.m0 - GAP;
      d += ` L ${P(end, tip - HEAD_LEN * 0.8)}`;
      const color = edgeColors[`${a.src}->${a.dst}`] || colors[a.src];
      const path = svgEl("path", { class: "wf-edge", d });
      colorVars(path, color);
      const head = svgEl("path", {
        class: "wf-head-tip",
        d: `M ${P(end, tip)} L ${P(end - HEAD_HALF, tip - HEAD_LEN)} L ${P(end + HEAD_HALF, tip - HEAD_LEN)} Z`,
      });
      colorVars(head, color);
      svg.append(path, head);
      const els = [path, head];
      const text = edgeLabels[`${a.src}->${a.dst}`];
      if (text) {
        const lab = document.createElement("div");
        lab.className = "wf-edge-label";
        lab.textContent = text;
        colorVars(lab, color);
        const m = (lastM + tip) / 2;
        if (down()) {
          const shift = a.labelLeft ? "translate(calc(-100% - 12px), -50%)" : "translateY(-50%)";
          Object.assign(lab.style, { left: `${end + 6}px`, top: `${m}px`, transform: shift });
        } else {
          Object.assign(lab.style, { left: `${m}px`, top: `${end - 4}px`, transform: "translate(-50%, -100%)" });
        }
        labels.append(lab);
        els.push(lab);
      }
      edgeEls.push({ src: a.src, dst: a.dst, els });
      const xy = (c, m) => (down() ? { x: c, y: m } : { x: m, y: c });
      handles.push({ key: keyOf(a.route), src: a.src, dst: a.dst, end: "exit", ...xy(a.xs[0], srcB.m1), color });
      handles.push({ key: keyOf(a.route), src: a.src, dst: a.dst, end: "enter", ...xy(end, tip), color });
    }

    // 4. arrows with explicit ports: an elbow route between any two sides
    const defaultSide = (end) => (end === "exit" ? (down() ? "bottom" : "right") : (down() ? "top" : "left"));
    // a node placed beside its neighbour faces it: exit and entry on the
    // sides that look at each other ("left" reads as "above" when flowing right)
    const facing = (src, dst) => {
      const b = beside[src]?.anchor === dst ? beside[src] : beside[dst]?.anchor === src ? beside[dst] : null;
      if (!b) return null;
      const before = (b.anchor === dst) === (b.side === "left");
      const [lo, hi] = down() ? ["left", "right"] : ["top", "bottom"];
      return before ? { exit: hi, enter: lo } : { exit: lo, enter: hi };
    };
    const placed = all.filter(custom).map((r) => {
      const p = ports[keyOf(r)] || {};
      const src = r[0];
      const dst = r[r.length - 1];
      const face = facing(src, dst);
      const end = (k, id) => ({ side: p[k]?.side || face?.[k] || defaultSide(k), at: p[k]?.at ?? null, id });
      const e = { key: keyOf(r), src, dst, exit: end("exit", src), enter: end("enter", dst) };
      const side = (end) => ["left", "right"].includes(end.side);
      if (face && side(e.exit) && side(e.enter) && e.exit.at == null && e.enter.at == null) {
        // run straight across, at the middle of the shorter card
        const [s, d] = [cardBox[src], cardBox[dst]];
        const y = (s.bottom - s.top < d.bottom - d.top ? s.top + s.bottom : d.top + d.bottom) / 2;
        e.exit.at = (y - s.top) / (s.bottom - s.top);
        e.enter.at = (y - d.top) / (d.bottom - d.top);
      } else if (face && !side(e.exit) && !side(e.enter) && e.exit.at == null && e.enter.at == null) {
        const [s, d] = [cardBox[src], cardBox[dst]];
        const x = (s.right - s.left < d.right - d.left ? s.left + s.right : d.left + d.right) / 2;
        e.exit.at = (x - s.left) / (s.right - s.left);
        e.enter.at = (x - d.left) / (d.right - d.left);
      }
      return e;
    });
    const center = (id, horiz) => (horiz ? (cardBox[id].left + cardBox[id].right) / 2 : (cardBox[id].top + cardBox[id].bottom) / 2);
    const shared = {};
    for (const e of placed) {
      if (e.enter.at == null) (shared[`${e.dst}|${e.enter.side}`] ||= []).push(e);
      if (e.exit.at == null) e.exit.at = 0.5;
    }
    for (const list of Object.values(shared)) {
      const horiz = ["top", "bottom"].includes(list[0].enter.side);
      list.sort((p, q) => center(p.src, horiz) - center(q.src, horiz));
      list.forEach((e, k) => { e.enter.at = list.length === 1 ? 0.5 : 0.2 + (0.6 * (k + 0.5)) / list.length; });
    }
    for (const e of placed) {
      const a = portPoint(cardBox[e.src], e.exit.side, e.exit.at, 0);
      const b = portPoint(cardBox[e.dst], e.enter.side, e.enter.at, GAP);
      const pts = orthoRoute(a, b);
      const d1 = [-b.nx, -b.ny];
      const stop = { x: b.x - d1[0] * HEAD_LEN * 0.8, y: b.y - d1[1] * HEAD_LEN * 0.8 };
      const color = edgeColors[e.key] || colors[e.src];
      const path = svgEl("path", { class: "wf-edge", d: roundedPath([...pts.slice(0, -1), stop]) });
      colorVars(path, color);
      const bx = b.x - d1[0] * HEAD_LEN;
      const by = b.y - d1[1] * HEAD_LEN;
      const [qx, qy] = [-d1[1] * HEAD_HALF, d1[0] * HEAD_HALF];
      const head = svgEl("path", { class: "wf-head-tip", d: `M ${b.x} ${b.y} L ${bx + qx} ${by + qy} L ${bx - qx} ${by - qy} Z` });
      colorVars(head, color);
      svg.append(path, head);
      const els = [path, head];
      const text = edgeLabels[e.key];
      if (text) {
        let seg = 1;
        for (let i = 1; i < pts.length; i++) if (dist(pts[i - 1], pts[i]) > dist(pts[seg - 1], pts[seg])) seg = i;
        const [p, q] = [pts[seg - 1], pts[seg]];
        const lab = document.createElement("div");
        lab.className = "wf-edge-label";
        lab.textContent = text;
        colorVars(lab, color);
        const flat = Math.abs(p.y - q.y) < 1;
        Object.assign(lab.style, flat
          ? { left: `${(p.x + q.x) / 2}px`, top: `${p.y - 4}px`, transform: "translate(-50%, -100%)" }
          : { left: `${p.x + 6}px`, top: `${(p.y + q.y) / 2}px`, transform: p.x < center(e.dst, true) ? "translate(calc(-100% - 12px), -50%)" : "translateY(-50%)" });
        labels.append(lab);
        els.push(lab);
      }
      edgeEls.push({ src: e.src, dst: e.dst, els });
      handles.push({ key: e.key, src: e.src, dst: e.dst, end: "exit", x: a.x, y: a.y, color });
      handles.push({ key: e.key, src: e.src, dst: e.dst, end: "enter", x: b.x, y: b.y, color });
    }

    // 5. ports mode: a draggable dot on both ends of every arrow
    if (editing) {
      for (const h of handles) {
        const dot = document.createElement("div");
        dot.className = `wf-port wf-port--${h.end}`;
        dot.title = `${h.key} ${h.end} · drag to a side, double-click to reset`;
        colorVars(dot, h.color);
        Object.assign(dot.style, { left: `${h.x}px`, top: `${h.y}px` });
        if (dragging && dragging.key === h.key && dragging.end === h.end) dot.classList.add("is-grabbed");
        dot.addEventListener("pointerdown", (ev) => startDrag(ev, h));
        dot.addEventListener("dblclick", () => setPort(h.key, h.end, null, true));
        labels.append(dot);
      }
    }

    // notes: a soft curve from the note onto the side of its card
    for (const [id, item] of Object.entries(items)) {
      const note = item.querySelector(":scope > .wf-note");
      if (!note || collapsed.has(id)) continue;
      const n = rel(note);
      const c = cardBox[id];
      const side = item.dataset.noteSide;
      let from, to, ctrl;
      if (side === "right" || side === "left") {
        const y = Math.min(n.top + 11, c.bottom - 12);
        from = { x: side === "right" ? n.left - 6 : n.right + 6, y };
        to = { x: side === "right" ? c.right + 5 : c.left - 5, y: Math.min(y + 6, c.bottom - 8) };
        ctrl = { x: (from.x + to.x) / 2, y: Math.min(from.y, to.y) - 9 };
      } else {
        const x = Math.min(n.left + 16, c.right - 16);
        from = { x, y: side === "bottom" ? n.top - 5 : n.bottom + 5 };
        to = { x: x + 6, y: side === "bottom" ? c.bottom + 5 : c.top - 5 };
        ctrl = { x: x - 8, y: (from.y + to.y) / 2 };
      }
      const dx = to.x - ctrl.x, dy = to.y - ctrl.y;
      const len = Math.hypot(dx, dy) || 1;
      const ux = dx / len, uy = dy / len;
      const bx = to.x - ux * 7, by = to.y - uy * 7;
      const arrow = svgEl("path", {
        class: "wf-note-arrow",
        d: `M ${from.x} ${from.y} Q ${ctrl.x} ${ctrl.y}, ${to.x} ${to.y} M ${bx - uy * 4} ${by + ux * 4} L ${to.x} ${to.y} L ${bx + uy * 4} ${by - ux * 4}`,
      });
      if (note.style.getPropertyValue("--wf-note-c")) arrow.style.setProperty("--wf-note-c", note.style.getPropertyValue("--wf-note-c"));
      svg.append(arrow);
    }
    applyFocus();
  }

  // ---- ports: drag an arrow end onto any side of its card --------------------
  function setPort(key, end, value, commit) {
    const p = { ...(ports[key] || {}) };
    p[end] = value;
    if (p.exit || p.enter) ports[key] = p;
    else delete ports[key];
    if (commit) {
      model.set("ports", JSON.parse(JSON.stringify(ports)));
      model.save_changes();
      showCode();
    }
    draw();
  }
  function startDrag(ev, h) {
    ev.preventDefault();
    ev.stopPropagation();
    const id = h.end === "exit" ? h.src : h.dst;
    dragging = { key: h.key, end: h.end };
    root.classList.add("wf--dragging");
    cards[id].classList.add("is-port-target");
    const move = (e) => {
      const base = board.getBoundingClientRect();
      const r = cards[id].getBoundingClientRect();
      const box = { left: r.left - base.left, right: r.right - base.left, top: r.top - base.top, bottom: r.bottom - base.top };
      setPort(h.key, h.end, nearestPort(box, e.clientX - base.left, e.clientY - base.top), false);
    };
    const up = () => {
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", up);
      root.classList.remove("wf--dragging");
      cards[id].classList.remove("is-port-target");
      dragging = null;
      setPort(h.key, h.end, (ports[h.key] || {})[h.end] || null, true);
    };
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", up);
  }

  // ---- hover & selection: keep the focused node's ancestry, dim the rest -----
  function reach(start, forward) {
    const seen = new Set();
    const todo = [start];
    while (todo.length) {
      const n = todo.pop();
      for (const [s, d] of edges) {
        const [a, b] = forward ? [s, d] : [d, s];
        if (a === n && !seen.has(b)) { seen.add(b); todo.push(b); }
      }
    }
    return seen;
  }
  function applyFocus() {
    const f = hovered || selected;
    for (const [id, card] of Object.entries(cards)) card.classList.toggle("is-selected", id === selected);
    if (!f) {
      Object.values(items).forEach((n) => n.classList.remove("is-dim"));
      edgeEls.forEach((e) => e.els.forEach((x) => x.classList.remove("is-dim")));
      return;
    }
    const up = reach(f, false);
    const dn = reach(f, true);
    up.add(f);
    dn.add(f);
    for (const [id, item] of Object.entries(items)) item.classList.toggle("is-dim", !up.has(id) && !dn.has(id));
    for (const e of edgeEls) {
      const keep = (up.has(e.src) && up.has(e.dst)) || (dn.has(e.src) && dn.has(e.dst));
      e.els.forEach((x) => x.classList.toggle("is-dim", !keep));
    }
  }

  setDirection(direction);
  applyCollapsed();
  const ro = new ResizeObserver(() => requestAnimationFrame(draw));
  ro.observe(root);
  Object.values(cards).forEach((c) => ro.observe(c));
  root.querySelectorAll("img").forEach((im) => im.addEventListener("load", draw));
  setTimeout(draw, 80);
  setTimeout(draw, 400);
  return () => { ro.disconnect(); themeObserver.disconnect(); };
}
export default { render };
