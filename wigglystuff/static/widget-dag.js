// A pure overlay: it owns no content. It finds the [data-wdag-node] boxes
// that WidgetDAG laid out and connects them per `edges` with SVG arrows.
const SVGNS = "http://www.w3.org/2000/svg";
function render({ model, el }) {
  const edges = model.get("edges");
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
  svg.innerHTML = '<defs><marker id="wdag-ah" viewBox="0 0 12 12" refX="8.5" refY="6" markerWidth="12" markerHeight="12" markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path d="M0.5,0.5 L11.5,6 L0.5,11.5 Q4,6 0.5,0.5 Z" fill="#8a9096"/></marker></defs>';
  root.appendChild(svg);
  function draw() {
    [...svg.querySelectorAll("path.edge")].forEach((p) => p.remove());
    const boxes = {};
    root.querySelectorAll("[data-wdag-node]").forEach((n) => { boxes[n.dataset.wdagNode] = n; });
    const base = root.getBoundingClientRect();
    const rect = (id) => {
      const r = boxes[id].getBoundingClientRect();
      return { left: r.left - base.left, right: r.right - base.left,
               top: r.top - base.top, h: r.height, cy: r.top - base.top + r.height / 2 };
    };
    const es = edges.filter(([s, d]) => boxes[s] && boxes[d]);
    // Fan out shared endpoints: group by source (exits) and target (entries)...
    const outBySrc = {}, inByDst = {};
    es.forEach((e, i) => { (outBySrc[e[0]] ||= []).push(i); (inByDst[e[1]] ||= []).push(i); });
    // ...and order the slots by the other end's height so lines don't cross.
    for (const s in outBySrc) outBySrc[s].sort((a, b) => rect(es[a][1]).cy - rect(es[b][1]).cy);
    for (const d in inByDst) inByDst[d].sort((a, b) => rect(es[a][0]).cy - rect(es[b][0]).cy);
    const slot = (r, idx, n) => r.top + (r.h * (idx + 1)) / (n + 1);
    es.forEach((e, i) => {
      const rs = rect(e[0]), rd = rect(e[1]), out = outBySrc[e[0]], inn = inByDst[e[1]];
      const x1 = rs.right, y1 = slot(rs, out.indexOf(i), out.length);
      const x2 = rd.left - 5, y2 = slot(rd, inn.indexOf(i), inn.length);
      const dx = Math.max(24, (x2 - x1) * 0.5);  // horizontal tangents -> smooth S
      const p = document.createElementNS(SVGNS, "path");
      p.setAttribute("class", "edge");
      p.setAttribute("d", `M ${x1} ${y1} C ${x1 + dx} ${y1}, ${x2 - dx} ${y2}, ${x2} ${y2}`);
      p.setAttribute("fill", "none"); p.setAttribute("stroke", "#9aa0a6");
      p.setAttribute("stroke-width", "1.5"); p.setAttribute("stroke-linecap", "round");
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
