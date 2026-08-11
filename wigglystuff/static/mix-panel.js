async function render({ model, el, host, signal }) {
  el.innerHTML = "";

  const root = document.createElement("div");
  root.className = "mix-panel";
  const width = model.get("width");
  if (width) root.style.width = width + "px";
  el.appendChild(root);

  let controller = null;

  function teardown() {
    if (controller) {
      controller.abort();
      controller = null;
    }
  }

  async function build() {
    teardown();
    root.innerHTML = "";

    const titleText = model.get("title");
    if (titleText) {
      const h = document.createElement("div");
      h.className = "mix-panel-title";
      h.textContent = titleText;
      root.appendChild(h);
    }

    const strips = document.createElement("div");
    strips.className = "mix-panel-strips";
    root.appendChild(strips);

    const controls = model.get("controls") || [];
    const names = model.get("names") || [];

    if (!host || typeof host.getWidget !== "function") {
      const err = document.createElement("div");
      err.className = "mix-panel-error";
      err.textContent =
        "MixPanel needs a host that supports anywidget composition (anywidget >= 0.11).";
      strips.appendChild(err);
      return;
    }

    controller = new AbortController();
    // Tear the children down when the parent view goes away.
    if (signal) signal.addEventListener("abort", teardown, { once: true });
    const childSignal = controller.signal;

    for (let i = 0; i < controls.length; i++) {
      const strip = document.createElement("div");
      strip.className = "mix-panel-strip";

      const nameEl = document.createElement("div");
      nameEl.className = "mix-panel-strip-name";
      nameEl.textContent = names[i] ?? `channel ${i + 1}`;
      strip.appendChild(nameEl);

      const mount = document.createElement("div");
      mount.className = "mix-panel-mount";
      strip.appendChild(mount);
      strips.appendChild(strip);

      try {
        const child = await host.getWidget(controls[i]);
        if (childSignal.aborted) return;
        await child.render({ el: mount, signal: childSignal });
      } catch (e) {
        mount.classList.add("mix-panel-error");
        mount.textContent = "⚠ " + (e && e.message ? e.message : "failed to mount");
      }
    }
  }

  model.on("change:controls", build);
  model.on("change:names", build);
  model.on("change:title", build);
  model.on("change:width", () => {
    root.style.width = model.get("width") ? model.get("width") + "px" : "";
  });

  await build();

  return teardown;
}

export default { render };
