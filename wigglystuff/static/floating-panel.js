/**
 * @module floating-panel
 *
 * Companion for the marimo-only ``FloatingPanel`` display helper. The helper
 * lays out ``[data-fp-root]`` (the panel) with the child inside a
 * ``[data-fp-body]`` box, then drops this content-less anywidget alongside it.
 * This ESM owns no content of its own: it climbs out of its shadow root to
 * ``[data-fp-root]`` in the composed light DOM, builds the drag header there,
 * promotes the root to a ``position: fixed`` panel, and wires drag and the
 * minimize toggle (which collapses the panel to just its header).
 *
 * A ``position: fixed`` element pins to the viewport as long as no ancestor
 * establishes a containing block (a ``transform``, ``filter``, ``contain``,
 * ...); notebook cells set none, so the panel tracks the viewport -- and the
 * iframe viewport in molab -- even though it lives in a cell's DOM.
 */

/** A drag-handle grip, drawn on the left of the header. */
const GRIP_ICON = `<svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor"
  aria-hidden="true">
  <circle cx="9" cy="6" r="1.6"/><circle cx="15" cy="6" r="1.6"/>
  <circle cx="9" cy="12" r="1.6"/><circle cx="15" cy="12" r="1.6"/>
  <circle cx="9" cy="18" r="1.6"/><circle cx="15" cy="18" r="1.6"/>
</svg>`;

/**
 * The minimize toggle: a plus whose vertical bar scales away to leave a minus,
 * so the icon morphs instead of swapping glyphs.
 */
const TOGGLE_ICON = `<svg viewBox="0 0 24 24" width="14" height="14" fill="none"
  stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true">
  <line x1="5" y1="12" x2="19" y2="12"/>
  <line data-fp-bar x1="12" y1="5" x2="12" y2="19"
    style="transform-box: fill-box; transform-origin: center"/>
</svg>`;

/**
 * Collapse/expand motion: a strong ease-out so the panel responds instantly
 * and settles softly. Closing is a touch faster than opening -- getting out of
 * the way should feel snappier than arriving.
 */
const EASE_OUT = "cubic-bezier(0.23, 1, 0.32, 1)";
const EXPAND_MS = 240;
const COLLAPSE_MS = 180;
const BODY_PADDING = 10;

/**
 * Colors track the notebook's theme without hard-coding a palette: the opaque
 * surface is the ``Canvas`` system color, which follows the ``color-scheme`` an
 * ancestor sets (light or dark) -- so ``color-scheme`` is left to inherit, not
 * pinned. Everything else derives from ``currentColor``, the notebook's own
 * text color, which already flips with the theme.
 */
const PANEL_STYLE = {
  position: "fixed",
  zIndex: "99999",
  boxSizing: "border-box",
  maxHeight: "80vh",
  maxWidth: "90vw",
  display: "flex",
  flexDirection: "column",
  border: "1px solid color-mix(in srgb, currentColor 22%, transparent)",
  borderRadius: "10px",
  background: "Canvas",
  boxShadow: "0 8px 28px rgb(0 0 0 / 0.28)",
  overflow: "hidden",
};

const HEADER_STYLE = {
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  padding: "4px 6px 4px 8px",
  background: "color-mix(in srgb, currentColor 10%, transparent)",
  cursor: "move",
  touchAction: "none",
  userSelect: "none",
};

const TITLE_STYLE = {
  fontSize: "13px",
  fontWeight: "600",
  whiteSpace: "nowrap",
  overflow: "hidden",
  textOverflow: "ellipsis",
  opacity: "0.85",
};

const BTN_STYLE = {
  display: "grid",
  placeItems: "center",
  width: "22px",
  height: "22px",
  padding: "0",
  border: "none",
  borderRadius: "6px",
  background: "transparent",
  color: "currentColor",
  fontSize: "18px",
  lineHeight: "1",
  cursor: "pointer",
  opacity: "0.7",
};

function render({ model, el }) {
  // ``el`` is sealed inside a ``<marimo-anywidget>`` shadow root. Climb out to
  // the host, find the light-DOM panel the helper laid out, and wire it there.
  const host = el.getRootNode().host || el;
  Object.assign(host.style, { position: "absolute", width: "0", height: "0" });
  const root = host.closest("[data-fp-root]");
  if (!root) return;
  // marimo can render a widget more than once; only wire the panel the once.
  if (root.getAttribute("data-fp-wired") === "yes") return;
  root.setAttribute("data-fp-wired", "yes");

  // The header (drag handle + minimize) is built here, not in the helper's HTML:
  // a raw-HTML header string inside marimo's HTML block breaks the passthrough.
  const header = document.createElement("div");
  header.setAttribute("data-fp-header", "");
  Object.assign(header.style, HEADER_STYLE);

  const grip = document.createElement("span");
  grip.style.display = "inline-flex";
  grip.style.opacity = "0.5";
  grip.innerHTML = GRIP_ICON;

  // Grip + optional title share the left of the header; the title truncates
  // with an ellipsis rather than forcing the panel wider.
  const left = document.createElement("div");
  Object.assign(left.style, {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    minWidth: "0",
    overflow: "hidden",
  });
  const titleEl = document.createElement("span");
  titleEl.setAttribute("data-fp-title", "");
  Object.assign(titleEl.style, TITLE_STYLE);
  left.append(grip, titleEl);

  const toggleBtn = document.createElement("button");
  toggleBtn.type = "button";
  toggleBtn.setAttribute("data-fp-toggle", "");
  Object.assign(toggleBtn.style, BTN_STYLE);
  toggleBtn.innerHTML = TOGGLE_ICON;
  const bar = toggleBtn.querySelector("[data-fp-bar]");

  header.append(left, toggleBtn);
  root.prepend(header);
  applyTitle();

  // Promote the root to the fixed panel and give the body room to scroll.
  // With no explicit width the panel shrink-wraps to its content (a fixed
  // element with `width: auto` hugs its content), which fits arbitrary marimo
  // content far better than a forced box. A ``width`` opts into a fixed size,
  // e.g. to reflow long text.
  Object.assign(root.style, PANEL_STYLE);
  applyWidth();
  const body = root.querySelector("[data-fp-body]");
  if (body) {
    Object.assign(body.style, {
      padding: `${BODY_PADDING}px`,
      overflow: "auto",
    });
  }

  // Escape the cell's stacking context by portaling the panel to
  // ``document.body``: inside a cell, ``z-index`` only competes within that
  // cell, so marimo raises a *hovered* cell above the panel. At the top level
  // the panel's ``z-index`` wins over every cell. Moving the node keeps the
  // child widgets' model connections, so they stay live. Tag by cell id and
  // drop any prior portal from the same cell so a re-run leaves just one.
  const cellEl = root.closest("[data-cell-id]");
  const cellId = cellEl ? cellEl.getAttribute("data-cell-id") : "";
  if (cellId) {
    document
      .querySelectorAll(`body > [data-fp-portal="${cellId}"]`)
      .forEach((old) => old.remove());
    root.setAttribute("data-fp-portal", cellId);
  }
  document.body.appendChild(root);

  /** Sets a fixed panel width, or clears it to shrink-wrap the content. */
  function applyWidth() {
    const w = model.get("width");
    root.style.width = w ? `${w}px` : "";
  }

  /** Shows the optional panel title in the header. */
  function applyTitle() {
    titleEl.textContent = model.get("title") || "";
  }

  /** True when the user asked the OS to cut down on motion. */
  function reducedMotion() {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  /** Sets the body's transition, or clears it with ``ms`` of 0. */
  function setBodyTransition(ms) {
    body.style.transition = ms
      ? `height ${ms}ms ${EASE_OUT}, padding ${ms}ms ${EASE_OUT}, ` +
        `opacity ${ms}ms ${EASE_OUT}`
      : "none";
  }

  /** Expanded resting state: natural height, so content can grow and scroll. */
  function finishExpand() {
    setBodyTransition(0);
    body.style.height = "";
    body.style.overflow = "auto";
    applyWidth(); // restore the shrink-wrap (or fixed) width
  }

  // The height transition only ends on its own when it runs to completion; an
  // interrupted run (a second click mid-way) simply retargets from wherever it
  // got to, so a stale end never lands. Checking ``isCollapsed`` covers the
  // case where the last completed transition was a collapse.
  let isCollapsed = null; // unknown until the first paint
  if (body) {
    body.addEventListener("transitionend", (e) => {
      if (e.target !== body || e.propertyName !== "height") return;
      if (!isCollapsed) finishExpand();
    });
  }

  /**
   * Collapses the panel to just its header, or expands it again. The body's
   * height slides between its content height and 0 with a CSS transition
   * rather than keyframes, so a click mid-animation reverses from the current
   * height instead of jumping. The first paint applies instantly.
   */
  function applyCollapsed() {
    const collapsed = model.get("collapsed");
    const firstPaint = isCollapsed === null;
    toggleBtn.title = collapsed ? "Expand" : "Minimize";
    toggleBtn.setAttribute("aria-label", toggleBtn.title);
    bar.style.transition = firstPaint ? "none" : `transform ${EXPAND_MS}ms ${EASE_OUT}`;
    bar.style.transform = collapsed ? "scaleY(1)" : "scaleY(0)";
    // The click handler and ``change:collapsed`` can both call in; only act
    // on a real change of state.
    if (collapsed === isCollapsed) return;
    isCollapsed = collapsed;
    if (!body) return;
    const ms = firstPaint || reducedMotion() ? 0 : collapsed ? COLLAPSE_MS : EXPAND_MS;

    if (collapsed) {
      // Freeze the current width before closing the body so the collapsed
      // header keeps the panel's expanded width instead of shrinking to fit
      // just the grip and toggle. A fixed ``width`` already holds itself.
      if (!model.get("width")) root.style.width = `${root.offsetWidth}px`;
      // Pin the current height in px (transitions cannot start from ``auto``),
      // force a layout, then slide to 0.
      setBodyTransition(0);
      body.style.height = `${body.offsetHeight}px`;
      body.style.overflow = "hidden";
      void body.offsetHeight;
      setBodyTransition(ms);
      body.style.height = "0px";
      body.style.paddingTop = "0px";
      body.style.paddingBottom = "0px";
      body.style.opacity = "0";
      body.inert = true; // hidden controls must not take focus
      return;
    }

    body.inert = false;
    // Target height: the content plus its padding, capped at what the panel's
    // 80vh limit leaves below the header (past that the body scrolls).
    const cs = getComputedStyle(body);
    const padNow = parseFloat(cs.paddingTop) + parseFloat(cs.paddingBottom);
    const content = body.scrollHeight - padNow;
    const room = window.innerHeight * 0.8 - header.offsetHeight - 2; // 2px border
    const target = Math.max(0, Math.min(content + 2 * BODY_PADDING, room));
    setBodyTransition(0);
    body.style.height = `${body.offsetHeight}px`;
    body.style.overflow = "hidden";
    void body.offsetHeight;
    setBodyTransition(ms);
    body.style.height = `${target}px`;
    body.style.paddingTop = `${BODY_PADDING}px`;
    body.style.paddingBottom = `${BODY_PADDING}px`;
    body.style.opacity = "";
    // No transition runs (and so none ends) when it is instant or the height
    // is already there; settle straight away.
    if (!ms || Math.abs(body.offsetHeight - target) < 1) finishExpand();
  }

  /** Places the panel from ``x``/``y``, or from ``corner`` when they are unset. */
  function place() {
    const x = model.get("x");
    const y = model.get("y");
    if (x >= 0 && y >= 0) {
      root.style.left = `${x}px`;
      root.style.top = `${y}px`;
      root.style.right = "";
      root.style.bottom = "";
      return;
    }
    const [v, h] = model.get("corner").split("-");
    root.style.top = v === "top" ? "16px" : "";
    root.style.bottom = v === "bottom" ? "16px" : "";
    root.style.left = h === "left" ? "16px" : "";
    root.style.right = h === "right" ? "16px" : "";
  }

  // Drag by the header; the toggle opts out so a click still minimizes.
  let dragging = false;
  let offX = 0;
  let offY = 0;
  header.addEventListener("pointerdown", (e) => {
    if (e.target.closest("[data-fp-toggle]")) return;
    dragging = true;
    const r = root.getBoundingClientRect();
    offX = e.clientX - r.left;
    offY = e.clientY - r.top;
    header.setPointerCapture(e.pointerId);
  });
  header.addEventListener("pointermove", (e) => {
    if (!dragging) return;
    const maxX = window.innerWidth - root.offsetWidth;
    const maxY = window.innerHeight - root.offsetHeight;
    const nx = Math.min(Math.max(0, e.clientX - offX), Math.max(0, maxX));
    const ny = Math.min(Math.max(0, e.clientY - offY), Math.max(0, maxY));
    root.style.left = `${nx}px`;
    root.style.top = `${ny}px`;
    root.style.right = "";
    root.style.bottom = "";
  });
  header.addEventListener("pointerup", () => {
    if (!dragging) return;
    dragging = false;
    const r = root.getBoundingClientRect();
    model.set("x", r.left);
    model.set("y", r.top);
    model.save_changes();
  });

  toggleBtn.addEventListener("click", () => {
    model.set("collapsed", !model.get("collapsed"));
    model.save_changes();
    // Repaint immediately: a value written from the frontend does not reliably
    // fire the local ``change:collapsed`` listener, so relying on it alone would
    // leave the click with no visible effect.
    applyCollapsed();
  });

  model.on("change:x", place);
  model.on("change:y", place);
  model.on("change:corner", place);
  model.on("change:width", applyWidth);
  model.on("change:title", applyTitle);
  model.on("change:collapsed", applyCollapsed);

  place();
  applyCollapsed();
}

export default { render };
