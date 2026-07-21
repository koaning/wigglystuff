// A pure overlay: it owns no content. It finds the [data-wdag-node] boxes
// that WidgetDAG laid out and connects them per `routes` with SVG arrows.
// Each route is a chain [src, ...waypoints, dst]; a long edge is drawn through
// its (invisible) waypoint boxes so it never crosses a widget.
const SVGNS = "http://www.w3.org/2000/svg";
const TURN_HALF_WIDTH = 7;

function edgePaths(pointRoutes) {
  const bands = pointRoutes.map((points) => Array(Math.max(0, points.length - 1)).fill(null));
  const byColumns = {};
  pointRoutes.forEach((points, routeIndex) => {
    for (let segmentIndex = 0; segmentIndex < points.length - 1; segmentIndex++) {
      const a = points[segmentIndex], b = points[segmentIndex + 1];
      // Boxes in one layer share a centre x. Group every segment crossing the
      // same pair of layers so they all turn through one common clear band.
      const key = `${Math.round(a.columnX)}:${Math.round(b.columnX)}`;
      (byColumns[key] ||= []).push({ routeIndex, segmentIndex, a, b });
    }
  });
  Object.values(byColumns).forEach((segments) => {
    const clearLeft = Math.max(...segments.map(({ a }) => a.x));
    const clearRight = Math.min(...segments.map(({ b }) => b.x));
    if (clearRight <= clearLeft) return;
    const turnX = (clearLeft + clearRight) / 2;
    const halfWidth = Math.min(TURN_HALF_WIDTH, (clearRight - clearLeft) / 2);
    segments.forEach(({ routeIndex, segmentIndex }) => {
      bands[routeIndex][segmentIndex] = { turnX, halfWidth };
    });
  });
  return pointRoutes.map((points, routeIndex) => {
    let d = `M ${points[0].x} ${points[0].y}`;
    for (let segmentIndex = 0; segmentIndex < points.length - 1; segmentIndex++) {
      const a = points[segmentIndex], b = points[segmentIndex + 1];
      const band = bands[routeIndex][segmentIndex];
      if (Math.abs(a.y - b.y) < 0.01) {
        d += ` H ${b.x}`;
      } else if (band) {
        const { turnX, halfWidth } = band;
        d += ` H ${turnX - halfWidth}`;
        d += ` C ${turnX} ${a.y}, ${turnX} ${b.y}, ${turnX + halfWidth} ${b.y}`;
        d += ` H ${b.x}`;
      } else {
        // Degenerate/custom geometry with no shared corridor: retain the old
        // x-monotonic curve instead of routing through an occupied node area.
        const dx = (b.x - a.x) * 0.5;
        d += ` C ${a.x + dx} ${a.y}, ${b.x - dx} ${b.y}, ${b.x} ${b.y}`;
      }
    }
    return d;
  });
}

function render({ model, el }) {
  const routes = model.get("routes");
  // el is sealed inside a <marimo-anywidget> shadow root. Climb out to the
  // host, find the light-DOM container WidgetDAG made, and draw the SVG there
  // so it shares a coordinate space with the node boxes.
  const host = el.getRootNode().host || el;
  Object.assign(host.style, { position: "absolute", width: "0", height: "0" });
  const root = host.closest("[data-wdag-root]");
  if (!root) return;
  root.querySelectorAll("svg.wdag-overlay").forEach((s) => s.remove());
  const svg = document.createElementNS(SVGNS, "svg");
  svg.setAttribute("class", "wdag-overlay");
  svg.setAttribute("shape-rendering", "geometricPrecision");
  Object.assign(svg.style, { position: "absolute", left: 0, top: 0,
    width: "100%", height: "100%", pointerEvents: "none", overflow: "visible" });
  // Chevron ("open V") arrowhead in the same gray as the line.
  svg.innerHTML = '<defs><marker id="wdag-ah" viewBox="0 0 10 10" refX="7.5" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path d="M1.5,1 L8.5,5 L1.5,9" fill="none" stroke="#9aa0a6" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></marker></defs>';
  root.appendChild(svg);
  function draw() {
    [...svg.querySelectorAll("path.edge")].forEach((p) => p.remove());
    const boxes = {};
    root.querySelectorAll("[data-wdag-node]").forEach((n) => { boxes[n.dataset.wdagNode] = n; });
    const base = root.getBoundingClientRect();
    const rect = (id) => {
      const r = boxes[id].getBoundingClientRect();
      return { left: r.left - base.left, right: r.right - base.left,
               cx: r.left - base.left + r.width / 2,
               top: r.top - base.top, h: r.height, cy: r.top - base.top + r.height / 2 };
    };
    const rs = routes.filter((r) => r.every((id) => boxes[id]));
    const last = (r) => r[r.length - 1];
    // Fan out shared real endpoints: group by source (exits) and target
    // (entries), ordered by the height of the adjacent point so lines don't cross.
    const outBySrc = {}, inByDst = {};
    rs.forEach((r, i) => { (outBySrc[r[0]] ||= []).push(i); (inByDst[last(r)] ||= []).push(i); });
    for (const s in outBySrc) outBySrc[s].sort((a, b) => rect(rs[a][1]).cy - rect(rs[b][1]).cy);
    for (const d in inByDst) inByDst[d].sort((a, b) => rect(rs[a][rs[a].length - 2]).cy - rect(rs[b][rs[b].length - 2]).cy);
    const slot = (r, idx, n) => r.top + (r.h * (idx + 1)) / (n + 1);
    const pointRoutes = rs.map((route, i) => {
      const src = rect(route[0]), dst = rect(last(route));
      const out = outBySrc[route[0]], inn = inByDst[last(route)];
      // waypoints route through their box centres; endpoints use fan-out slots
      const points = [{
        x: src.right,
        y: slot(src, out.indexOf(i), out.length),
        columnX: src.cx,
      }];
      for (let k = 1; k < route.length - 1; k++) {
        const waypoint = rect(route[k]);
        points.push({ x: waypoint.cx, y: waypoint.cy, columnX: waypoint.cx });
      }
      points.push({
        x: dst.left - 3,
        y: slot(dst, inn.indexOf(i), inn.length),
        columnX: dst.cx,
      });
      return points;
    });
    const paths = edgePaths(pointRoutes);
    rs.forEach((route, i) => {
      const p = document.createElementNS(SVGNS, "path");
      p.setAttribute("class", "edge");
      p.setAttribute("d", paths[i]);
      p.setAttribute("fill", "none"); p.setAttribute("stroke", "#9aa0a6");
      p.setAttribute("stroke-width", "1.5"); p.setAttribute("stroke-linecap", "round");
      p.setAttribute("stroke-linejoin", "round");
      p.setAttribute("marker-end", "url(#wdag-ah)");
      svg.appendChild(p);
    });
  }
  requestAnimationFrame(draw);
  setTimeout(draw, 80); setTimeout(draw, 400);
  new ResizeObserver(draw).observe(root);
  root.querySelectorAll("img").forEach((im) => im.addEventListener("load", draw));
}
export default { render };
