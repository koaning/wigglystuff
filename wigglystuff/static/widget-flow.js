// WidgetFlow's overlay. It owns no content: it climbs out of its shadow root
// to the [data-wf-root] container that WidgetFlow laid out and draws the
// arrows, edge labels and note arrows there, so everything shares one
// coordinate space with the live widgets.
//
// All routing happens in a "frame" where layers stack top to bottom. For
// direction="right" every box is transposed into that frame (x <-> y) before
// routing, the SVG is drawn under a transposing group, and labels are mapped
// back -- so one router serves both directions.
const SVGNS = "http://www.w3.org/2000/svg";
const CORNER = 8;
const HEAD_LEN = 7;
const HEAD_HALF = 3.6;
const GAP = 3;
const STUB = 16;
const CLEAR = 10;
const SLOT_GAP = 16; // closest an arrow tip may land to another arrow's straight drop
const SLOT_INSET = 6; // closest an arrow tip may land to a widget's corner
const NORMAL = { top: [0, -1], bottom: [0, 1], left: [-1, 0], right: [1, 0] };
// a real side's name in the transposed frame (and back: the map is its own inverse)
const FLIP = { top: "left", left: "top", bottom: "right", right: "bottom" };
const SHIFT = { after: "0", before: "-100%", center: "-50%" };

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

// Does the axis-aligned segment p→q pass through box `o`?
function hits(p, q, o) {
  if (Math.abs(p.y - q.y) < 0.5) {
    return p.y > o.top && p.y < o.bottom && Math.max(p.x, q.x) > o.left && Math.min(p.x, q.x) < o.right;
  }
  return p.x > o.left && p.x < o.right && Math.max(p.y, q.y) > o.top && Math.min(p.y, q.y) < o.bottom;
}

const flat = (p, q) => Math.abs(p.y - q.y) < 0.5;
const overlap = (a0, a1, b0, b1) => Math.min(Math.max(a0, a1), Math.max(b0, b1)) - Math.max(Math.min(a0, a1), Math.min(b0, b1));

// How the leg p→q meets the already-drawn polylines `lines`: legs it runs on
// top of (parallel, within a few px, overlapping) and legs it crosses.
function meets(p, q, lines) {
  let along = 0;
  let cross = 0;
  for (const line of lines) {
    for (let i = 1; i < line.length; i++) {
      const [u, v] = [line[i - 1], line[i]];
      if (flat(p, q) === flat(u, v)) {
        const near = flat(p, q) ? Math.abs(p.y - u.y) < 6 && overlap(p.x, q.x, u.x, v.x) > 2
                                : Math.abs(p.x - u.x) < 6 && overlap(p.y, q.y, u.y, v.y) > 2;
        if (near) along++;
      } else {
        const [h0, h1, w] = flat(p, q) ? [p, q, u] : [u, v, p];
        const [w0, w1] = flat(p, q) ? [u, v] : [p, q];
        if (w.x > Math.min(h0.x, h1.x) && w.x < Math.max(h0.x, h1.x)
            && h0.y > Math.min(w0.y, w1.y) && h0.y < Math.max(w0.y, w1.y)) cross++;
      }
    }
  }
  return { along, cross };
}

// Axis-aligned polyline from exit point `a` to arrow tip `b`. Each port
// carries its outward normal; try a few elbow shapes and keep the one with the
// fewest bends that leaves `a` along its normal and enters `b` against its own,
// preferring shapes that stay clear of the `obstacles` (other cards' boxes).
// The middle leg of the three-bend shapes may also run along any obstacle's
// edge, which is what lets a route detour around a card in its way. It also
// steers clear of the arrows already drawn (`lines`): never on top of one,
// and crossing as few as it can.
function orthoRoute(a, b, obstacles = [], lines = []) {
  const d0 = [a.nx, a.ny];
  const d1 = [-b.nx, -b.ny];
  const p1 = { x: a.x + a.nx * STUB, y: a.y + a.ny * STUB };
  const p2 = { x: b.x + b.nx * STUB, y: b.y + b.ny * STUB };
  const legs = lines.flatMap((l) => l.slice(1).map((q, i) => [l[i], q]));
  const yms = [
    (p1.y + p2.y) / 2,
    ...obstacles.flatMap((o) => [o.top - CLEAR, o.bottom + CLEAR]),
    ...legs.filter(([u, v]) => flat(u, v)).flatMap(([u]) => [u.y - CLEAR, u.y + CLEAR]),
  ];
  const xms = [
    (p1.x + p2.x) / 2,
    ...obstacles.flatMap((o) => [o.left - CLEAR, o.right + CLEAR]),
    ...legs.filter(([u, v]) => !flat(u, v)).flatMap(([u]) => [u.x - CLEAR, u.x + CLEAR]),
  ];
  const shapes = [
    [],
    [{ x: a.x, y: b.y }],
    [{ x: b.x, y: a.y }],
    [p1, { x: p1.x, y: p2.y }, p2],
    [p1, { x: p2.x, y: p1.y }, p2],
    ...yms.map((ym) => [p1, { x: p1.x, y: ym }, { x: p2.x, y: ym }, p2]),
    ...xms.map((xm) => [p1, { x: xm, y: p1.y }, { x: xm, y: p2.y }, p2]),
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
    let blocked = 0;
    let along = 0;
    let cross = 0;
    for (let i = 1; i < pts.length; i++) {
      len += dist(pts[i - 1], pts[i]);
      for (const o of obstacles) if (hits(pts[i - 1], pts[i], o)) blocked++;
      const m = meets(pts[i - 1], pts[i], lines);
      along += m.along;
      cross += m.cross;
    }
    const score = blocked * 1e6 + along * 1e5 + (pts.length - 2) * 1000 + cross * 300 + len;
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


const box = (b, pad) => ({ left: b.left - pad, right: b.right + pad, top: b.top - pad, bottom: b.bottom + pad });
const overlaps = (a, b) => a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top;

// Fallback label spots: either side of each long leg of an arrow, longest
// leg first, for when the preferred spot near the arrow tip is crowded. A spot
// is a frame point plus which way the label extends from it along each axis
// ("after" = towards +x/+y, "before" = towards -x/-y, or "center").
function along(line) {
  const legs = line.slice(1).map((q, i) => [line[i], q]).filter(([p, q]) => dist(p, q) > 28);
  legs.sort((u, v) => dist(v[0], v[1]) - dist(u[0], u[1]));
  return legs.flatMap(([p, q]) => {
    const [mx, my] = [(p.x + q.x) / 2, (p.y + q.y) / 2];
    return Math.abs(p.y - q.y) < 1
      ? [{ x: mx, y: my - 4, h: "center", v: "before" }, { x: mx, y: my + 4, h: "center", v: "after" }]
      : [{ x: mx + 6, y: my, h: "after", v: "center" }, { x: mx - 6, y: my, h: "before", v: "center" }];
  });
}

// A filled arrowhead with its tip at `b`, pointing along the unit vector d.
function headPath(b, d) {
  const bx = b.x - d[0] * HEAD_LEN;
  const by = b.y - d[1] * HEAD_LEN;
  const [qx, qy] = [-d[1] * HEAD_HALF, d[0] * HEAD_HALF];
  return `M ${b.x} ${b.y} L ${bx + qx} ${by + qy} L ${bx - qx} ${by - qy} Z`;
}

// Every ordering of `items` (fine for the handful of tracks in one gap).
function* permutations(items) {
  if (items.length <= 1) { yield items.slice(); return; }
  for (let i = 0; i < items.length; i++) {
    const rest = [...items.slice(0, i), ...items.slice(i + 1)];
    for (const p of permutations(rest)) yield [items[i], ...p];
  }
}

function render({ model, el }) {
  const host = el.getRootNode().host || el;
  Object.assign(host.style, { position: "absolute", width: "0", height: "0" });
  const root = host.closest("[data-wf-root]");
  if (!root) return;
  const board = root.querySelector(":scope > .wf-board");
  board.querySelectorAll(":scope > .wf-svg, :scope > .wf-labels").forEach((n) => n.remove());

  const routes = model.get("routes");
  const edgeLabels = model.get("edge_labels") || {};
  const edgeStyles = model.get("edge_styles") || {};
  const T = model.get("direction") === "right";
  const fside = (side) => (T ? FLIP[side] : side);
  const ports = {};
  for (const [key, p] of Object.entries(model.get("ports") || {})) {
    ports[key] = {};
    for (const k of ["exit", "enter"]) if (p[k]) ports[key][k] = { side: fside(p[k].side), at: p[k].at };
  }
  const ac = new AbortController();
  const on = (n, type, fn) => n.addEventListener(type, fn, { signal: ac.signal });

  const svg = svgEl("svg", { class: "wf-svg" });
  const canvas = svgEl("g", T ? { transform: "matrix(0 1 1 0 0 0)" } : {});
  svg.append(canvas);
  const labels = document.createElement("div");
  labels.className = "wf-labels";
  board.append(svg, labels);

  // node boxes (real widgets and the invisible lanes long edges run through)
  const nodes = {};
  const notes = {};
  board.querySelectorAll("[data-wf-node]").forEach((n) => {
    if (n.closest("[data-wf-root]") === root) nodes[n.dataset.wfNode] = n;
  });
  board.querySelectorAll("[data-wf-note]").forEach((n) => {
    if (n.closest("[data-wf-root]") === root) notes[n.dataset.wfNote] = n;
  });
  const layerEls = [...board.children].filter((n) => n.classList.contains("wf-layer"));
  const rowOf = {};
  layerEls.forEach((layer, i) => {
    // (a flow nested inside a node has its own n0, n1, ...: leave those be)
    layer.querySelectorAll("[data-wf-node]").forEach((n) => {
      if (n.closest("[data-wf-root]") === root) rowOf[n.dataset.wfNode] = i;
    });
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

  function draw() {
    if (!root.isConnected) return;
    canvas.replaceChildren();
    labels.replaceChildren();
    const base = board.getBoundingClientRect();
    // an element's box relative to the board, in frame coordinates
    const rel = (n) => {
      const r = n.getBoundingClientRect();
      const b = { left: r.left - base.left, right: r.right - base.left, top: r.top - base.top, bottom: r.bottom - base.top };
      return T ? { left: b.top, right: b.bottom, top: b.left, bottom: b.right } : b;
    };
    // put a label at a frame spot, translated back to the board's real axes
    const placeLabel = (lab, o) => {
      const [x, y, h, v] = T ? [o.y, o.x, o.v, o.h] : [o.x, o.y, o.h, o.v];
      Object.assign(lab.style, { left: `${x}px`, top: `${y}px`, transform: `translate(${SHIFT[h]}, ${SHIFT[v]})` });
    };
    const boxOf = {};
    for (const id in nodes) boxOf[id] = rel(nodes[id]);
    const noteBox = {};
    for (const id in notes) noteBox[id] = rel(notes[id]);
    const layerBox = layerEls.map(rel);
    const mid = (b) => (b.left + b.right) / 2;
    const segs = [];
    const pending = [];
    const keyOf = (r) => `${r[0]}->${r[r.length - 1]}`;
    // Arrows are drawn one source at a time, each line over a halo in the
    // notebook's background color, so where a later arrow crosses an earlier
    // one there's a clear gap under it. Arrows from one source share a group,
    // so the stem they share doesn't get notched where they branch apart.
    const groups = {};
    const drawEdge = (src, dst, d, head) => {
      if (!groups[src]) {
        const g = svgEl("g", {});
        groups[src] = { halos: svgEl("g", {}), lines: svgEl("g", {}) };
        g.append(groups[src].halos, groups[src].lines);
        canvas.append(g);
      }
      const line = svgEl("path", { class: "wf-edge", d });
      const tip = svgEl("path", { class: "wf-head", d: head });
      const style = edgeStyles[`${src}->${dst}`];
      if (style?.color) {
        line.style.stroke = style.color;
        Object.assign(tip.style, { fill: style.color, stroke: style.color });
      }
      if (style?.dashed) line.style.strokeDasharray = "5 4";
      groups[src].halos.append(svgEl("path", { class: "wf-halo", d }));
      groups[src].lines.append(line, tip);
    };

    // 1. default arrows: each one's x positions -- the stem, any lanes, and a
    //    landing slot spread across the target's top edge
    const all = routes.filter((r) => r.every((id) => id in boxOf && id in rowOf));
    const live = all.filter((r) => !ports[keyOf(r)]);
    const arrows = live.map((route) => ({
      src: route[0],
      dst: route[route.length - 1],
      route,
      xs: [mid(boxOf[route[0]]), ...route.slice(1, -1).map((w) => mid(boxOf[w]))],
    }));
    const placed = all.filter((r) => ports[keyOf(r)]).map((r) => {
      const p = ports[keyOf(r)];
      const end = (k, fallback) => ({ side: p[k]?.side || fallback, at: p[k]?.at ?? null });
      return { key: keyOf(r), src: r[0], dst: r.at(-1), exit: end("exit", "bottom"), enter: end("enter", "top") };
    });
    // every arrow that lands on a target's top edge -- default ones and ported
    // ones without a position -- gets its own slot, ordered by where it comes from
    const incoming = {};
    arrows.forEach((a) => (incoming[a.dst] ||= []).push({ a, from: a.xs.at(-1) }));
    for (const e of placed) {
      if (e.enter.side !== "top" || e.enter.at != null) continue;
      const s = boxOf[e.src];
      const from = e.exit.side === "left" ? s.left : e.exit.side === "right" ? s.right : s.left + (e.exit.at ?? 0.5) * (s.right - s.left);
      (incoming[e.dst] ||= []).push({ e, from });
    }
    for (const [dst, list] of Object.entries(incoming)) {
      const b = boxOf[dst];
      const w = b.right - b.left;
      const span = Math.min(w * 0.6, 40 * list.length);
      list.sort((p, q) => p.from - q.from);
      // spread evenly across the middle of the edge...
      const xs = list.map((_, k) => mid(b) - span / 2 + (span * (k + 0.5)) / list.length);
      // ...but an arrow whose source sits right above the edge drops straight
      // down, and the others make room for it rather than run alongside it
      // (only when the arrows sorted to either side of it still fit there)
      const [left, right] = [b.left + SLOT_INSET, b.right - SLOT_INSET];
      const straight = [];
      list.forEach((item, k) => {
        const ok = item.from - left >= SLOT_GAP * (k + 1) && right - item.from >= SLOT_GAP * (list.length - k);
        if (ok && straight.every((j) => item.from - list[j].from >= 2 * SLOT_GAP)) straight.push(k);
      });
      straight.forEach((k) => { xs[k] = list[k].from; });
      for (let k = 0; k < list.length; k++) {
        if (straight.includes(k)) continue;
        let e = k;
        while (e + 1 < list.length && !straight.includes(e + 1)) e++;
        const lo = k > 0 ? xs[k - 1] : left;
        const hi = e + 1 < list.length ? xs[e + 1] : right;
        const fits = xs.slice(k, e + 1).every((x) => x > lo + (k > 0 ? SLOT_GAP : 0) && x < hi - (e + 1 < list.length ? SLOT_GAP : 0));
        if (!fits) for (let j = k; j <= e; j++) xs[j] = lo + ((hi - lo) * (j - k + 1)) / (e - k + 2);
        k = e;
      }
      list.forEach((item, k) => {
        const x = xs[k];
        if (item.e) {
          item.e.enter.at = (x - b.left) / (b.right - b.left);
          return;
        }
        item.a.xs.push(x);
        item.a.labelLeft = list.length > 1 && k < (list.length - 1) / 2;
      });
    }

    // 2. one horizontal track per source in each gap it jogs through, so the
    //    arrows from one node share a bus. The tracks are stacked in whichever
    //    order makes the fewest crossings: a track above another crosses the
    //    lower one's stem, a track below crosses the upper one's drop.
    const jogs = {};
    for (const a of arrows) {
      a.xs.forEach((x, k) => {
        if (k === a.xs.length - 1 || Math.abs(a.xs[k + 1] - x) < 1) return;
        const g = rowOf[a.route[k]];
        ((jogs[g] ||= {})[a.src] ||= []).push({ from: x, to: a.xs[k + 1] });
      });
    }
    const inside = (x, s) => x > Math.min(s.from, s.to) + 0.5 && x < Math.max(s.from, s.to) - 0.5;
    const costAbove = (P, Q) => {
      let n = 0;
      for (const p of P) for (const q of Q) n += inside(q.from, p) + inside(p.to, q);
      return n;
    };
    const tracks = {};
    for (const [g, bySrc] of Object.entries(jogs)) {
      const srcs = Object.keys(bySrc).sort((p, q) => mid(boxOf[p]) - mid(boxOf[q]));
      let best = srcs;
      if (srcs.length <= 7) {
        const cost = (order) => {
          let n = 0;
          for (let i = 0; i < order.length; i++)
            for (let j = i + 1; j < order.length; j++) n += costAbove(bySrc[order[i]], bySrc[order[j]]);
          return n;
        };
        let bestCost = cost(srcs);
        for (const order of permutations(srcs)) {
          const c = cost(order);
          if (c < bestCost) [best, bestCost] = [order, c];
        }
      }
      tracks[g] = best;
    }
    const trackY = (g, src) => {
      const top = layerBox[g].bottom;
      const h = layerBox[+g + 1].top - top;
      return top + (h * (tracks[g].indexOf(src) + 1)) / (tracks[g].length + 1);
    };

    // 3. draw: down out of the source, along the track, down into the target
    for (const a of arrows) {
      const y0 = boxOf[a.src].bottom;
      let d = `M ${a.xs[0]} ${y0}`;
      const line = [{ x: a.xs[0], y: y0 }];
      let lastY = layerBox[rowOf[a.dst] - 1].bottom;
      a.xs.forEach((x, k) => {
        if (k === a.xs.length - 1) return;
        const next = a.xs[k + 1];
        if (Math.abs(next - x) < 1) return;
        const ty = trackY(rowOf[a.route[k]], a.src);
        const s = Math.sign(next - x);
        const r = Math.min(CORNER, Math.abs(next - x) / 2);
        d += ` L ${x} ${ty - r} Q ${x} ${ty} ${x + s * r} ${ty}`;
        d += ` L ${next - s * r} ${ty} Q ${next} ${ty} ${next} ${ty + r}`;
        line.push({ x, y: ty }, { x: next, y: ty });
        lastY = Math.max(lastY, ty);
      });
      const end = a.xs.at(-1);
      const tip = { x: end, y: boxOf[a.dst].top - GAP };
      d += ` L ${end} ${tip.y - HEAD_LEN * 0.8}`;
      line.push(tip);
      segs.push(line);
      drawEdge(a.src, a.dst, d, headPath(tip, [0, 1]));
      const text = edgeLabels[`${a.src}->${a.dst}`];
      if (text) {
        const m = (lastY + tip.y) / 2;
        const side = (left) => ({ x: left ? end - 6 : end + 6, y: m, h: left ? "before" : "after", v: "center" });
        pending.push({ text, options: [side(a.labelLeft), side(!a.labelLeft), ...along(line)] });
      }
    }

    // 4. arrows with ports: an elbow route between the two named sides that
    //    steers around every other widget, note and arrow
    // ends that share a side of one node (arrows in or out) and have no
    // position spread out evenly along it, ordered by the far end's position
    const shared = {};
    for (const e of placed) {
      for (const [k, id, far] of [["exit", e.src, e.dst], ["enter", e.dst, e.src]]) {
        if (e[k].at == null) (shared[`${id}|${e[k].side}`] ||= []).push({ end: e[k], far });
      }
    }
    for (const list of Object.values(shared)) {
      const horiz = ["top", "bottom"].includes(list[0].end.side);
      const c = (id) => (horiz ? mid(boxOf[id]) : (boxOf[id].top + boxOf[id].bottom) / 2);
      list.sort((p, q) => c(p.far) - c(q.far));
      list.forEach((x, k) => { x.end.at = list.length === 1 ? 0.5 : 0.2 + (0.6 * (k + 0.5)) / list.length; });
    }
    for (const e of placed) {
      const a = portPoint(boxOf[e.src], e.exit.side, e.exit.at, 0);
      const b = portPoint(boxOf[e.dst], e.enter.side, e.enter.at, GAP);
      const obstacles = [
        ...Object.keys(nodes).filter((id) => id !== e.src && id !== e.dst && !id.startsWith("!")).map((id) => box(boxOf[id], 4)),
        ...Object.values(noteBox).map((n) => box(n, 4)),
      ];
      const pts = orthoRoute(a, b, obstacles, segs);
      segs.push(pts);
      const d1 = [-b.nx, -b.ny];
      const stop = { x: b.x - d1[0] * HEAD_LEN * 0.8, y: b.y - d1[1] * HEAD_LEN * 0.8 };
      drawEdge(e.src, e.dst, roundedPath([...pts.slice(0, -1), stop]), headPath(b, d1));
      const text = edgeLabels[e.key];
      if (text) pending.push({ text, options: along(pts) });
    }

    // 5. edge labels: the first spot that clears the arrows, the widgets, the
    //    notes and the labels already placed; the preferred one otherwise
    const blockers = [...Object.keys(boxOf).filter((id) => !id.startsWith("!")).map((id) => boxOf[id]), ...Object.values(noteBox)];
    for (const { text, options } of pending) {
      if (!options.length) continue;
      const lab = document.createElement("div");
      lab.className = "wf-edge-label";
      lab.textContent = text;
      labels.append(lab);
      let pick = null;
      for (const opt of options) {
        placeLabel(lab, opt);
        const r = box(rel(lab), 2);
        const clash = blockers.some((o) => overlaps(r, o))
          || segs.some((line) => line.some((q, i) => i && hits(line[i - 1], q, r)));
        if (!clash) { pick = opt; break; }
      }
      placeLabel(lab, pick || options[0]);
      blockers.push(rel(lab));
    }

    // 6. notes: a short straight arrow from the note onto its widget's edge
    //    (the note sits after the widget across the flow: right of it going
    //    down, below it going right -- both "right" in the frame)
    for (const [id, n] of Object.entries(noteBox)) {
      const c = boxOf[id];
      const y = Math.max(c.top + 8, Math.min(c.bottom - 8, (n.top + n.bottom) / 2));
      const from = { x: n.left - 6, y };
      const to = { x: c.right + 5, y };
      if (from.x - to.x < 8) continue;
      canvas.append(svgEl("path", {
        class: "wf-note-arrow",
        d: `M ${from.x} ${y} L ${to.x} ${y} M ${to.x + 5} ${y - 3.5} L ${to.x} ${y} L ${to.x + 5} ${y + 3.5}`,
      }));
    }
  }

  const ro = new ResizeObserver(() => requestAnimationFrame(draw));
  ro.observe(root);
  Object.values(nodes).forEach((n) => ro.observe(n));
  Object.values(notes).forEach((n) => ro.observe(n));
  root.querySelectorAll("img").forEach((im) => on(im, "load", draw));
  draw();
  const timers = [setTimeout(draw, 80), setTimeout(draw, 400)];
  return () => {
    ro.disconnect();
    themeObserver.disconnect();
    ac.abort();
    timers.forEach(clearTimeout);
  };
}
export default { render };
