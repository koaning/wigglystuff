// A pure overlay: it owns no content. It finds the [data-wdag-node] boxes
// that WidgetDAG laid out and connects them per `routes` with SVG arrows.
// Each route is a chain [src, ...waypoints, dst]; a long edge is drawn through
// its (invisible) waypoint boxes so it never crosses a widget.
const SVGNS = "http://www.w3.org/2000/svg";
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
    rs.forEach((route, i) => {
      const src = rect(route[0]), dst = rect(last(route));
      const out = outBySrc[route[0]], inn = inByDst[last(route)];
      // waypoints route through their box centres; endpoints use fan-out slots
      const pts = [[src.right, slot(src, out.indexOf(i), out.length)]];
      for (let k = 1; k < route.length - 1; k++) { const w = rect(route[k]); pts.push([w.cx, w.cy]); }
      pts.push([dst.left - 3, slot(dst, inn.indexOf(i), inn.length)]);
      let d = `M ${pts[0][0]} ${pts[0][1]}`;
      for (let k = 0; k < pts.length - 1; k++) {
        // Horizontal tangents at both ends -> the arrowhead always arrives
        // flat. The handle is exactly half the horizontal gap so the curve is
        // x-monotonic (never doubles back): with the columns already in a
        // crossing-free order, x-monotone edges can't cross. The column gap
        // (set in _display_) gives the room that keeps the arrival gentle.
        const [ax, ay] = pts[k], [bx, by] = pts[k + 1];
        const dx = (bx - ax) * 0.5;
        d += ` C ${ax + dx} ${ay}, ${bx - dx} ${by}, ${bx} ${by}`;
      }
      const p = document.createElementNS(SVGNS, "path");
      p.setAttribute("class", "edge");
      p.setAttribute("d", d);
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
