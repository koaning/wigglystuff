// Click-to-load facade for the marimo WASM demos on the reference pages. A cold
// pyodide boot pulls several MB, so nothing is requested until the user clicks.
//
// The listener is delegated on `document` so it survives the theme's instant
// navigation, and guarded on window because extra_javascript re-runs on every
// page swap (without the guard, listeners would pile up).
if (!window.__wigglyDemoBound) {
  window.__wigglyDemoBound = true;

  // One place for the URL grammar. The documented
  // /github/<org>/<repo>/blob/main/<path>.py/wasm form 307s to this one.
  const SRC =
    "https://marimo.app/gh/koaning/wigglystuff/main" +
    "?embed=true&mode=read&utm_source=wigglystuff&entrypoint=demos%2F";

  function buildFrame(card) {
    const frame = document.createElement("iframe");
    frame.className = "demo-frame";
    frame.src = SRC + encodeURIComponent(card.dataset.demo + ".py");
    frame.title = card.dataset.demoTitle || "Live marimo demo";
    frame.setAttribute(
      "sandbox",
      "allow-scripts allow-same-origin allow-downloads allow-popups allow-forms",
    );
    frame.setAttribute("allow", "microphone");
    frame.allowFullscreen = true;
    return frame;
  }

  document.addEventListener("click", (event) => {
    const card = event.target.closest("[data-demo]");
    if (!card || !card.isConnected) return;

    card.replaceWith(buildFrame(card));
  });
}
