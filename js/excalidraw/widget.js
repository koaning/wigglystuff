// Excalidraw widget loader.
//
// Excalidraw + React are ~8MB bundled, so instead of shipping that blob inside
// the wheel we load them from a CDN (esm.sh) the first time a widget renders.
// Trade-off: this needs network access on first render and does NOT work fully
// offline or under WASM (molab). Everything is pinned by version below.

const EXCALIDRAW_VERSION = "0.18.1";
const REACT_VERSION = "19.0.0";
const CDN = "https://esm.sh";
// Where Excalidraw fetches its fonts/icons from at runtime.
const ASSET_PATH = `${CDN}/@excalidraw/excalidraw@${EXCALIDRAW_VERSION}/dist/prod/`;
const CSS_URL = `https://unpkg.com/@excalidraw/excalidraw@${EXCALIDRAW_VERSION}/dist/prod/index.css`;

let libPromise = null;
function loadLib() {
  if (libPromise) return libPromise;
  libPromise = (async () => {
    // Tell Excalidraw where to fetch fonts/icons from before it initializes.
    if (typeof window !== "undefined" && !window.EXCALIDRAW_ASSET_PATH) {
      window.EXCALIDRAW_ASSET_PATH = ASSET_PATH;
    }
    // Pin React via ?deps so Excalidraw's internal react import resolves to the
    // same esm.sh URL we import directly — one shared React instance, no
    // "invalid hook call".
    const deps = `react@${REACT_VERSION},react-dom@${REACT_VERSION}`;
    const [react, reactDomClient, excal] = await Promise.all([
      import(/* @vite-ignore */ `${CDN}/react@${REACT_VERSION}`),
      import(/* @vite-ignore */ `${CDN}/react-dom@${REACT_VERSION}/client`),
      import(/* @vite-ignore */ `${CDN}/@excalidraw/excalidraw@${EXCALIDRAW_VERSION}?deps=${deps}`),
    ]);
    return {
      React: react.default ?? react,
      createRoot: reactDomClient.createRoot,
      Excalidraw: excal.Excalidraw,
      serializeAsJSON: excal.serializeAsJSON,
      exportToBlob: excal.exportToBlob,
    };
  })();
  return libPromise;
}

let cssTextPromise = null;
function getCssText() {
  if (!cssTextPromise) {
    cssTextPromise = fetch(CSS_URL).then((r) => (r.ok ? r.text() : ""));
  }
  return cssTextPromise;
}

async function injectCss(root) {
  // marimo mounts anywidget inside a shadow root, so Excalidraw's CSS must live
  // inside that root; document.head covers the portals Excalidraw mounts onto
  // document.body.
  const css = await getCssText();
  if (!css) return;
  // Hide UI that isn't useful on a notebook sketch surface: the "Library"
  // (shape library) trigger and the top-left hamburger main menu (its
  // file/export/theme actions don't apply in an embedded widget — use
  // get_pil()/save() and the notebook theme instead).
  const extra =
    "\n.excalidraw .default-sidebar-trigger," +
    '\n.excalidraw [data-testid="main-menu-trigger"],' +
    "\n.excalidraw .main-menu-trigger," +
    '\n.excalidraw [data-testid="toolbar-more-tools"],' +
    "\n.excalidraw .App-toolbar__extra-tools-trigger{display:none !important;}\n";
  for (const target of [root, document.head]) {
    if (!target || !("querySelector" in target)) continue;
    if (target.querySelector("style[data-wigglystuff-excalidraw]")) continue;
    const style = document.createElement("style");
    style.setAttribute("data-wigglystuff-excalidraw", "");
    style.textContent = css + extra;
    target.appendChild(style);
  }
}

// Detect the notebook's dark mode by walking up from the widget element,
// crossing the shadow boundary, looking for the usual markers; fall back to the
// OS preference.
function detectDark(el) {
  let node = el;
  while (node) {
    if (node.nodeType === 1) {
      const cl = node.classList;
      if (cl && (cl.contains("dark") || cl.contains("dark-theme"))) return true;
      if (node.getAttribute && node.getAttribute("data-theme") === "dark") return true;
    }
    node = node.parentNode || node.host || null;
  }
  return (
    typeof window !== "undefined" &&
    window.matchMedia &&
    window.matchMedia("(prefers-color-scheme: dark)").matches
  );
}

function blobToDataURL(blob) {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onloadend = () => resolve(reader.result);
    reader.readAsDataURL(blob);
  });
}

function makeApp(React, Excalidraw, serializeAsJSON, exportToBlob, model, el) {
  return function App() {
    const apiRef = React.useRef(null);
    const saveTimer = React.useRef(null);
    const pending = React.useRef(null);
    // True while a flush is mid-export. exportToBlob is async, so without this
    // guard a fast burst of edits would kick off several overlapping exports;
    // whichever finished last would win image_base64 — possibly an older one —
    // leaving the PNG out of sync with the (synchronously written) scene. The
    // flush below drains serially so scene and PNG always describe the same edit.
    const flushing = React.useRef(false);
    const throttleMs = model.get("sync_throttle_ms") || 1000;

    // theme: explicit `theme` traitlet wins ("light"/"dark"); otherwise follow
    // the notebook and react to live theme toggles.
    const forced = model.get("theme");
    const [dark, setDark] = React.useState(() =>
      forced ? forced === "dark" : detectDark(el),
    );
    React.useEffect(() => {
      if (forced) return; // pinned by the user, don't track the notebook
      const update = () => setDark(detectDark(el));
      const obs = new MutationObserver(update);
      const opts = { attributes: true, attributeFilter: ["class", "data-theme"], subtree: true };
      obs.observe(document.documentElement, opts);
      const host = el.getRootNode && el.getRootNode().host;
      if (host) obs.observe(host, opts);
      const mq = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)");
      if (mq && mq.addEventListener) mq.addEventListener("change", update);
      return () => {
        obs.disconnect();
        if (mq && mq.removeEventListener) mq.removeEventListener("change", update);
      };
    }, [forced]);

    // Excalidraw doesn't always re-theme from the `theme` prop after mount, so
    // also push it imperatively whenever the detected theme flips.
    React.useEffect(() => {
      if (apiRef.current) {
        apiRef.current.updateScene({ appState: { theme: dark ? "dark" : "light" } });
      }
    }, [dark]);

    const refresh = () => apiRef.current && apiRef.current.refresh();

    // Excalidraw maps pointer -> canvas using its container's position, which it
    // measures on mount. In a notebook the widget sits well down the page, so
    // that initial measurement is stale and drawings land offset from the
    // cursor. refresh() recomputes it; re-run on scroll/resize (capture: true so
    // we catch the notebook's own scroll container, not just window).
    React.useEffect(() => {
      const t = setTimeout(refresh, 100);
      window.addEventListener("scroll", refresh, true);
      window.addEventListener("resize", refresh);
      return () => {
        clearTimeout(t);
        window.removeEventListener("scroll", refresh, true);
        window.removeEventListener("resize", refresh);
      };
    }, []);


    React.useEffect(() => {
      const t = setTimeout(() => {
        if (apiRef.current) {
          apiRef.current.refresh();
    
          // Scroll/zoom to fit all elements, capped at 100%
          const elements = apiRef.current.getSceneElements();
          if (elements.length > 0) {
            apiRef.current.scrollToContent(elements, {
              fitToContent: true,
              viewportZoomFactor: 1,   // max 100% — won't zoom *in* beyond this
              animate: false,
            });
          }
        }
      }, 100);
    
      window.addEventListener("scroll", refresh, true);
      window.addEventListener("resize", refresh);
      return () => {
        clearTimeout(t);
        window.removeEventListener("scroll", refresh, true);
        window.removeEventListener("resize", refresh);
      };
    }, []);

    // Capture the starting scene once; we don't push later Python edits back
    // into the live canvas (that would fight an in-progress drawing).
    // Defaults: a normal (non-hand-drawn) font, straight (non-rough) strokes,
    // and a closed filled-triangle arrowhead. FONT_FAMILY.Nunito === 6
    // ("Normal"), ROUGHNESS.ARCHITECT === 0, "triangle" is the filled head.
    const baseAppState = {
      currentItemFontFamily: 6,
      currentItemRoughness: 0,
      currentItemEndArrowhead: "triangle",
      currentItemArrowType: "elbow",
    };
    const scene = model.get("scene");
    const initialData =
      scene && Object.keys(scene).length
        ? {
            elements: scene.elements ?? [],
            appState: { ...baseAppState, ...(scene.appState ?? {}) },
            files: scene.files ?? {},
          }
        : { appState: baseAppState };

    const onChange = React.useCallback((elements, appState, files) => {
      pending.current = { elements, appState, files };
      // Skip if a sync is already scheduled (saveTimer) or in progress
      // (flushing). Either way the latest edit now lives in pending.current and
      // the in-flight flush below will pick it up — we never want two flushes
      // running at once (see the flushing ref's comment for why).
      if (saveTimer.current || flushing.current) return;
      saveTimer.current = setTimeout(async () => {
        saveTimer.current = null;
        // Drain pending.current to completion. Each iteration writes the scene
        // and its matching PNG together, so the two traitlets can never
        // disagree. Edits that land mid-export update pending.current and get
        // handled on the next loop turn instead of racing this one — draw
        // quickly and the last edit still wins both scene and image_base64.
        flushing.current = true;
        try {
          while (pending.current) {
            const p = pending.current;
            pending.current = null;
            // The `elements` Excalidraw hands onChange is a reference to its
            // LIVE, mutable scene array — undo/redo mutate it in place. If we
            // read it once for the scene and again for the PNG (which we must,
            // because exportToBlob is async), a fast undo landing between those
            // two reads makes the scene and the PNG describe different drawings
            // — the "split brain" where get_pil() disagrees with the canvas.
            // So snapshot ONCE up front and drive both traitlets from it.
            // serializeAsJSON deep-copies and strips deleted elements, so the
            // snapshot is frozen: nothing the user does during the export await
            // can change what we've already committed to `scene`.
            const snapshot = JSON.parse(
              serializeAsJSON(p.elements, p.appState, p.files, "local"),
            );
            model.set("scene", snapshot);
            // Export a PNG of the same snapshot so Python can grab it via
            // get_pil(). snapshot.elements already excludes deleted ones, so an
            // empty length means an erased canvas — skip exportToBlob (it throws
            // on empty) and clear the image to match.
            try {
              if (snapshot.elements.length) {
                const blob = await exportToBlob({
                  elements: snapshot.elements,
                  appState: snapshot.appState,
                  files: snapshot.files,
                  mimeType: "image/png",
                });
                model.set("image_base64", await blobToDataURL(blob));
              } else {
                model.set("image_base64", "");
              }
            } catch (e) {
              /* export is best-effort; keep the scene sync regardless */
            }
            model.save_changes();
          }
        } finally {
          flushing.current = false;
        }
      }, throttleMs);
    }, []);

    React.useEffect(
      () => () => {
        if (saveTimer.current) clearTimeout(saveTimer.current);
      },
      [],
    );

    return React.createElement(Excalidraw, {
      excalidrawAPI: (api) => {
        apiRef.current = api;
      },
      initialData,
      onChange,
      theme: dark ? "dark" : "light",
    });
  };
}

// --- Shadow-DOM clipboard shim --------------------------------------------
// Excalidraw's copy/cut/paste handlers gate on "is Excalidraw focused / is the
// pointer over the canvas?" using document.activeElement and
// document.elementFromPoint(x, y). Neither pierces the shadow DOM that marimo
// mounts anywidget in: activeElement returns the shadow HOST (<marimo-anywidget>)
// and elementFromPoint stops at it. So those checks fail and copy/cut/paste
// silently bail. Excalidraw is loaded prebuilt from a CDN, so we can't patch it
// — instead we make those two document APIs shadow-aware while a widget is
// mounted, which lets Excalidraw's existing checks succeed.
//
// Scoped on purpose: we only descend into a shadow root that actually hosts an
// Excalidraw instance (.excalidraw). So document.activeElement /
// elementFromPoint behave EXACTLY as before for everything else on the page
// (marimo's own focus handling, code cells, other widgets) — they only change
// when focus/pointer is genuinely inside an Excalidraw canvas. The shim is
// reference-counted: installed once when the first widget mounts, fully restored
// after the last one unmounts.
let shimRefCount = 0;
let restoreShim = null;

function hasExcalidraw(shadowRoot) {
  return (
    shadowRoot &&
    typeof shadowRoot.querySelector === "function" &&
    shadowRoot.querySelector(".excalidraw")
  );
}

function installShadowDomShim() {
  shimRefCount += 1;
  if (shimRefCount > 1) return; // another widget already installed it

  // The native activeElement getter lives up the prototype chain (Document /
  // DocumentOrShadowRoot), so walk up to grab it before shadowing it.
  let proto = document;
  let desc = null;
  while (proto && !(desc = Object.getOwnPropertyDescriptor(proto, "activeElement"))) {
    proto = Object.getPrototypeOf(proto);
  }
  const nativeActiveGet = desc && desc.get;

  if (nativeActiveGet) {
    Object.defineProperty(document, "activeElement", {
      configurable: true,
      get() {
        let a = nativeActiveGet.call(document);
        while (a && a.shadowRoot && a.shadowRoot.activeElement && hasExcalidraw(a.shadowRoot)) {
          a = a.shadowRoot.activeElement;
        }
        return a;
      },
    });
  }

  const nativeEFP = document.elementFromPoint.bind(document);
  document.elementFromPoint = function (x, y) {
    let node = nativeEFP(x, y);
    while (node && node.shadowRoot && hasExcalidraw(node.shadowRoot)) {
      const inner = node.shadowRoot.elementFromPoint(x, y);
      if (!inner || inner === node) break;
      node = inner;
    }
    return node;
  };

  restoreShim = () => {
    if (nativeActiveGet) delete document.activeElement; // re-expose prototype getter
    document.elementFromPoint = nativeEFP;
  };
}

function uninstallShadowDomShim() {
  shimRefCount -= 1;
  if (shimRefCount <= 0) {
    shimRefCount = 0;
    if (restoreShim) restoreShim();
    restoreShim = null;
  }
}

async function render({ model, el }) {
  el.style.display = "block";
  el.style.height = `${model.get("height") || 600}px`;

  const mount = document.createElement("div");
  mount.style.cssText = "width:100%;height:100%";
  // Stop marimo / Jupyter from swallowing Excalidraw's keyboard shortcuts.
  mount.addEventListener("keydown", (e) => e.stopPropagation());
  mount.addEventListener("keyup", (e) => e.stopPropagation());
  el.appendChild(mount);

  // Make document.activeElement / elementFromPoint shadow-aware so Excalidraw's
  // clipboard handlers work inside marimo's shadow root (see shim comment above).
  // Only needed when we're actually in a shadow root — light DOM (classic
  // Jupyter) is left untouched.
  const inShadow = el.getRootNode() instanceof ShadowRoot;
  if (inShadow) installShadowDomShim();

  let root = null;
  try {
    const { React, createRoot, Excalidraw, serializeAsJSON, exportToBlob } =
      await loadLib();
    await injectCss(el.getRootNode());
    const App = makeApp(React, Excalidraw, serializeAsJSON, exportToBlob, model, el);
    root = createRoot(mount);
    root.render(React.createElement(App));
    requestAnimationFrame(() => window.dispatchEvent(new Event("resize")));
  } catch (err) {
    mount.textContent =
      "Failed to load Excalidraw from CDN. This widget needs network access " +
      "on first render and does not work fully offline. (" + err + ")";
    mount.style.cssText = "padding:1rem;color:#b00;font-family:sans-serif";
  }

  return () => {
    if (root) root.unmount();
    if (inShadow) uninstallShadowDomShim();
  };
}

export default { render };
