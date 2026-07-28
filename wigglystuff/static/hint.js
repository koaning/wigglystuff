// A pure overlay: it owns no content. It finds the two [data-hint-box] boxes
// that Hint laid out -- "target" and "note" -- and draws one quadratic bezier
// from the note to the target's edge, with a chevron arrowhead.
const SVGNS = "http://www.w3.org/2000/svg";
const CLEARANCE = 4; // px of air left between an anchor and its box
const BOW_RATIO = 0.14; // how far the control point leaves the chord
const BOW_MIN = 8;
const BOW_MAX = 26;
const HEAD_LENGTH = 8;
const HEAD_HALF_WIDTH = 4.5;

// Where the arc leaves the note and where it lands on the target, plus the
// control point. Horizontal sides bow upward, vertical sides bow to the right,
// so the curve is always predictable rather than mirroring per side.
function arcPoints(side, target, note) {
  let from, to, vertical;
  if (side === "right") {
    from = { x: note.left - CLEARANCE, y: note.cy };
    to = { x: target.right + CLEARANCE, y: target.cy };
    vertical = false;
  } else if (side === "left") {
    from = { x: note.right + CLEARANCE, y: note.cy };
    to = { x: target.left - CLEARANCE, y: target.cy };
    vertical = false;
  } else if (side === "bottom") {
    from = { x: note.cx, y: note.top - CLEARANCE };
    to = { x: target.cx, y: target.bottom + CLEARANCE };
    vertical = true;
  } else {
    from = { x: note.cx, y: note.bottom + CLEARANCE };
    to = { x: target.cx, y: target.top - CLEARANCE };
    vertical = true;
  }
  const dx = to.x - from.x;
  const dy = to.y - from.y;
  const bow = Math.min(BOW_MAX, Math.max(BOW_MIN, Math.hypot(dx, dy) * BOW_RATIO));
  const mid = { x: (from.x + to.x) / 2, y: (from.y + to.y) / 2 };
  const control = vertical
    ? { x: mid.x + bow, y: mid.y }
    : { x: mid.x, y: mid.y - bow };
  return { from, control, to };
}

// An "open V" head at `to`. For a quadratic bezier the end tangent is
// simply to - control, so no curve sampling is needed.
function headPath(control, to) {
  const dx = to.x - control.x;
  const dy = to.y - control.y;
  const len = Math.hypot(dx, dy) || 1;
  const ux = dx / len;
  const uy = dy / len;
  const backX = to.x - ux * HEAD_LENGTH;
  const backY = to.y - uy * HEAD_LENGTH;
  // perpendicular to the tangent
  const px = -uy * HEAD_HALF_WIDTH;
  const py = ux * HEAD_HALF_WIDTH;
  return (
    `M ${backX + px} ${backY + py} L ${to.x} ${to.y} ` +
    `L ${backX - px} ${backY - py}`
  );
}

function render({ model, el }) {
  // el is sealed inside a <marimo-anywidget> shadow root. Climb out to the
  // host, find the light-DOM container Hint made, and draw the SVG there so it
  // shares a coordinate space with the two boxes.
  const host = el.getRootNode().host || el;
  Object.assign(host.style, { position: "absolute", width: "0", height: "0" });
  const root = host.closest("[data-hint-root]");
  if (!root) return;
  // Only clear an overlay this root owns. A bare querySelectorAll would reach
  // into a nested hint's root and delete its arc instead.
  [...root.querySelectorAll("svg.hint-overlay")]
    .filter((s) => s.parentElement === root)
    .forEach((s) => s.remove());
  const svg = document.createElementNS(SVGNS, "svg");
  svg.setAttribute("class", "hint-overlay");
  svg.setAttribute("shape-rendering", "geometricPrecision");
  Object.assign(svg.style, { position: "absolute", left: 0, top: 0,
    width: "100%", height: "100%", pointerEvents: "none", overflow: "visible" });
  root.appendChild(svg);

  function draw() {
    [...svg.querySelectorAll("path.hint-arc")].forEach((p) => p.remove());
    // Hints nest, so a plain querySelector on an outer root would happily match
    // an inner hint's boxes. Keep only the boxes this root owns directly.
    const own = (which) =>
      [...root.querySelectorAll(`[data-hint-box="${which}"]`)].find(
        (b) => b.closest("[data-hint-root]") === root,
      );
    const target = own("target");
    const note = own("note");
    if (!target || !note) return;
    const base = root.getBoundingClientRect();
    const rect = (node) => {
      const r = node.getBoundingClientRect();
      return {
        left: r.left - base.left,
        right: r.right - base.left,
        top: r.top - base.top,
        bottom: r.bottom - base.top,
        cx: r.left - base.left + r.width / 2,
        cy: r.top - base.top + r.height / 2,
      };
    };
    const color = model.get("color");
    const { from, control, to } = arcPoints(model.get("side"), rect(target), rect(note));
    const arc = `M ${from.x} ${from.y} Q ${control.x} ${control.y} ${to.x} ${to.y}`;
    // The head is a separate path rather than an SVG <marker>: markers need a
    // document-unique id, and two hints in one notebook share the light DOM.
    for (const [d, width] of [[arc, 1.5], [headPath(control, to), 1.6]]) {
      const p = document.createElementNS(SVGNS, "path");
      p.setAttribute("class", "hint-arc");
      p.setAttribute("d", d);
      p.setAttribute("fill", "none");
      p.setAttribute("stroke", color);
      p.setAttribute("stroke-width", width);
      p.setAttribute("stroke-linecap", "round");
      p.setAttribute("stroke-linejoin", "round");
      svg.appendChild(p);
    }
  }

  requestAnimationFrame(draw);
  setTimeout(draw, 80);
  setTimeout(draw, 400);
  new ResizeObserver(draw).observe(root);
  root.querySelectorAll("img").forEach((im) => im.addEventListener("load", draw));
  model.on("change:color", draw);
  model.on("change:side", draw);
}
export default { render };
