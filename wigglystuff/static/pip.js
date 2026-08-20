/**
 * @module pip
 *
 * Draws a child widget either inline in the notebook or in a floating
 * Document Picture-in-Picture window.
 *
 * The child is drawn by rendering a view of it into a container, so moving it
 * between the two is a teardown of one view and a render of another. Views of
 * one model stay in sync on their own, and exactly one is kept alive here.
 *
 * The floating window is a document in its own realm, which shapes this
 * module. Its elements are created from that document, and the widget runtime
 * mounts a child's CSS per view keyed on `el.getRootNode()`, so a view
 * rendered there is styled there. Opening one also needs transient
 * activation, which constrains where the first await may go.
 */

/** A monitor with an inset rectangle, drawn in the button and the placeholder. */
const PIP_ICON = `<svg viewBox="0 0 24 24" width="16" height="16" fill="none"
  stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
  aria-hidden="true">
  <rect x="2" y="4" width="20" height="16" rx="2"/>
  <rect x="12" y="12" width="8" height="6" rx="1" fill="currentColor" stroke="none"/>
</svg>`;

/** Class names a notebook sets on an ancestor to mean "dark". */
const THEME_CLASSES = ["dark", "dark-mode", "dark-theme"];

/**
 * Mirrors the notebook's theme signals onto the floating document.
 *
 * Widget stylesheets select dark mode through an ancestor the notebook marks
 * -- `.dark`, `.dark-theme`, `[data-theme="dark"]`. The floating document has
 * no such ancestor, so those rules never match there and a widget would render
 * light inside a dark notebook. The signals are copied on open and kept in
 * step until `signal` aborts, so a theme toggle reaches the window too.
 *
 * @param {Window} pipWindow
 * @param {AbortSignal} signal
 */
function mirrorTheme(pipWindow, signal) {
  const sources = [document.documentElement, document.body];
  const target = pipWindow.document.body;
  const apply = () => {
    let dark = false;
    for (const name of THEME_CLASSES) {
      const on = sources.some((source) => source.classList.contains(name));
      target.classList.toggle(name, on);
      dark ||= on;
    }
    const theme = sources.map((source) => source.dataset.theme).find(Boolean);
    if (theme) {
      target.dataset.theme = theme;
      dark ||= theme === "dark";
    } else {
      delete target.dataset.theme;
    }
    // Without this the window's canvas follows the operating system, which
    // leaves a white page behind a dark widget in a dark notebook.
    target.style.colorScheme = dark ? "dark" : "light";
  };
  apply();
  const observer = new MutationObserver(apply);
  for (const source of sources) {
    observer.observe(source, {
      attributes: true,
      attributeFilter: ["class", "data-theme"],
    });
  }
  signal.addEventListener("abort", () => observer.disconnect(), { once: true });
}

export default {
  /**
   * Mounts the inline view, the button that floats it, and the placeholder
   * that stands in its place.
   *
   * @param {object} props Render props from the widget runtime.
   * @param {import("@anywidget/types").AnyModel} props.model
   * @param {HTMLElement} props.el Container for this view.
   * @param {import("@anywidget/types").Host} props.host Resolves the child.
   * @param {AbortSignal} props.signal Aborts when this view is torn down.
   */
  async render({ model, el, host, signal }) {
    const child = await host.getWidget(model.get("child"));

    const root = document.createElement("div");
    root.className = "pip-root";

    // Where the child lives while it is docked in the notebook.
    const stage = document.createElement("div");
    stage.className = "pip-stage";

    // Stands in for the child while it is floating.
    const placeholder = document.createElement("div");
    placeholder.className = "pip-placeholder";
    placeholder.title = "Bring it back to the notebook";
    placeholder.innerHTML = PIP_ICON;
    const caption = document.createElement("div");
    caption.className = "pip-caption";
    caption.textContent = "In picture-in-picture";
    const backBtn = document.createElement("button");
    backBtn.className = "pip-back";
    backBtn.type = "button";
    backBtn.textContent = "Bring it back";
    placeholder.append(caption, backBtn);

    const popBtn = document.createElement("button");
    popBtn.className = "pip-pop";
    popBtn.type = "button";
    popBtn.title = "Open in picture-in-picture";
    popBtn.setAttribute("aria-label", popBtn.title);
    popBtn.innerHTML = PIP_ICON;
    // Unsupported browsers (Safari): the chip is disabled and CSS hides it.
    popBtn.disabled = !("documentPictureInPicture" in window);

    root.append(popBtn, stage, placeholder);
    el.append(root);

    let inlineController = null;
    let pipController = null;
    let pipWindow = null;
    let opening = false;

    /** Renders the child into the notebook, replacing whatever the stage held. */
    async function mountInline() {
      inlineController = new AbortController();
      stage.replaceChildren();
      await child.render({
        el: stage,
        signal: AbortSignal.any([signal, inlineController.signal]),
      });
    }

    /** Reports the current placement to Python, if it differs from `value`. */
    function syncFloating(value) {
      if (model.get("floating") !== value) {
        model.set("floating", value);
        model.save_changes();
      }
    }

    /**
     * Returns the child to the notebook.
     *
     * Runs for every close: the placeholder, Python, the window's own
     * controls, and view teardown. The container holds its height across the
     * swap, so the notebook does not reflow while the render is in flight.
     */
    async function onWindowClosed() {
      pipWindow = null;
      pipController?.abort();
      pipController = null;
      if (signal.aborted) return; // the whole view is going away with it
      const active = placeholder.getRootNode().activeElement;
      const hadFocus = active != null && placeholder.contains(active);
      const { height } = placeholder.getBoundingClientRect();
      if (height > 0) {
        root.style.minHeight = `${Math.round(height)}px`;
      }
      root.classList.remove("pip-is-floating");
      syncFloating(false);
      try {
        await mountInline();
      } catch (error) {
        console.error(error);
      }
      root.style.minHeight = "";
      if (!matchMedia("(prefers-reduced-motion: reduce)").matches) {
        stage.animate([{ opacity: 0, transform: "scale(0.985)" }, {}], {
          duration: 160,
          easing: "ease-out",
        });
      }
      // The panel that had focus is gone, so move focus somewhere real.
      if (hadFocus) {
        popBtn.focus({ preventScroll: true });
      }
    }

    /**
     * Moves the child into a new picture-in-picture window.
     *
     * `requestWindow` needs transient activation, so nothing may be awaited
     * before it, and `pagehide` is attached as soon as the window exists so a
     * close during setup is not missed.
     */
    async function popOut() {
      if (pipWindow || opening) return;
      opening = true;
      try {
        pipWindow = await documentPictureInPicture.requestWindow({
          width: model.get("width"),
          height: model.get("height"),
        });
        pipWindow.addEventListener("pagehide", onWindowClosed, { once: true });
        pipController = new AbortController();

        // Anchored top-left at a window-derived width. A centered
        // shrink-to-fit box re-centers whenever the child's intrinsic width
        // changes, which reads as jitter.
        pipWindow.document.body.style.cssText =
          "margin:0;height:100vh;overflow:auto;" +
          "font:14px/1.4 system-ui,sans-serif";
        mirrorTheme(pipWindow, pipController.signal);
        const box = pipWindow.document.createElement("div");
        // 8px is the body margin a browser would have applied if `body` above
        // had not zeroed it.
        box.style.cssText =
          "width:100%;min-height:100%;box-sizing:border-box;padding:8px";
        pipWindow.document.body.append(box);

        // Hold the child's footprint so the notebook doesn't reflow while
        // it is away (min-height: a short child must not overflow the panel).
        const { height } = stage.getBoundingClientRect();
        if (height > 0) {
          placeholder.style.minHeight = `${Math.round(height)}px`;
        }

        inlineController?.abort();
        stage.replaceChildren();
        root.classList.add("pip-is-floating");

        await child.render({
          el: box,
          signal: AbortSignal.any([signal, pipController.signal]),
        });
        syncFloating(true);
      } finally {
        opening = false;
      }
    }

    popBtn.addEventListener("click", () => {
      popOut().catch((error) => {
        if (error.name === "AbortError") return; // closed while opening
        console.error("[Pip] could not open the window", error);
        // Close if it opened; pagehide then restores the inline view.
        pipWindow?.close();
      });
    });

    placeholder.addEventListener("click", () => pipWindow?.close());

    /** Applies a `floating` write from Python: it may close, but not open. */
    function onFloatingChange() {
      if (!model.get("floating") && pipWindow) {
        pipWindow.close();
      } else if (model.get("floating") && !pipWindow) {
        console.warn(
          "[Pip] cannot open a picture-in-picture window from Python: the " +
            "browser requires a user gesture. Use the button on the widget.",
        );
        syncFloating(false);
      }
    }
    model.on("change:floating", onFloatingChange);

    signal.addEventListener("abort", () => {
      model.off("change:floating", onFloatingChange);
      pipWindow?.close(); // don't orphan the window when the view goes away
    });

    await mountInline();
  },
};
