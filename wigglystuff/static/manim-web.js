/**
 * ManimWeb – run a manim-web scene in the notebook.
 *
 * Loads the manim-web engine from CDN on first use, then executes the
 * user-supplied JS (the `code` traitlet) as the body of an async function
 * with the manim-web module namespace and a container element in scope.
 * The recommended entry point is manim-web's own `Player`, which renders a
 * full playback UI (play/pause, scrub timeline with segment markers, speed,
 * fullscreen and export) into the container:
 *
 *     const player = new manim.Player(container, {
 *       width, height, autoPlay: true,
 *     });
 *     player.sequence(async (scene) => {
 *       await scene.play(new manim.Create(new manim.Circle({ radius: 1.5 })));
 *     });
 *
 * See: https://github.com/maloyan/manim-web
 */

// Cache the CDN import promise per version so the ~engine is fetched once.
const _cache = {};

function loadManim(version) {
  if (!_cache[version]) {
    _cache[version] = import(
      "https://cdn.jsdelivr.net/npm/manim-web@" + version + "/dist/manim-web.browser.js"
    );
  }
  return _cache[version];
}

function render({ model, el }) {
  el.classList.add("manim-web-root");

  const container = document.createElement("div");
  container.className = "manim-web-container";
  el.appendChild(container);

  const errorBox = document.createElement("pre");
  errorBox.className = "manim-web-error";
  errorBox.style.display = "none";
  el.appendChild(errorBox);

  // Bumped on every (re)run so a stale async run can't clobber a newer one.
  let runToken = 0;

  function applySize() {
    container.style.width = model.get("width") + "px";
  }

  function showError(message) {
    errorBox.textContent = message;
    errorBox.style.display = "block";
    model.set("error", message);
    model.save_changes();
  }

  function clearError() {
    errorBox.textContent = "";
    errorBox.style.display = "none";
    if (model.get("error")) {
      model.set("error", "");
      model.save_changes();
    }
  }

  async function run() {
    const token = ++runToken;
    clearError();
    container.innerHTML = "";

    // `code` is already plain JavaScript — Python resolved any file/URL source.
    const code = model.get("code");
    if (!code) return;

    let manim;
    try {
      manim = await loadManim(model.get("version"));
    } catch (err) {
      if (token !== runToken) return;
      showError("Failed to load manim-web: " + (err && err.message ? err.message : err));
      return;
    }
    if (token !== runToken) return;

    try {
      const fn = new Function(
        "manim",
        "container",
        "width",
        "height",
        "model",
        "return (async () => {\n" + code + "\n})();"
      );
      await fn(manim, container, model.get("width"), model.get("height"), model);
    } catch (err) {
      if (token !== runToken) return;
      showError((err && err.stack) || String(err));
    }
  }

  applySize();
  run();

  model.on("change:code", run);
  model.on("change:version", run);
  model.on("change:width", () => {
    applySize();
    run();
  });
  model.on("change:height", () => {
    applySize();
    run();
  });

  return () => {
    // Invalidate any in-flight run so it stops touching the removed DOM.
    runToken++;
  };
}

export default { render };
