// AttractorWidget entry point. Picks GPU (WebGL2) when available, falls back
// to a CPU Canvas2D renderer otherwise. Wires traitlets to renderer methods.

import { tryCreateGPU, GPURenderer } from "./gpu.js";
import { CPURenderer } from "./cpu.js";

function render({ model, el }) {
  const wrap = document.createElement("div");
  wrap.style.cssText = "position:relative;display:inline-block;line-height:0;";
  el.appendChild(wrap);

  // First try a WebGL2-capable canvas.
  let canvas = document.createElement("canvas");
  canvas.width = model.get("width");
  canvas.height = model.get("height");
  wrap.appendChild(canvas);

  const badge = document.createElement("div");
  badge.style.cssText =
    "position:absolute;right:6px;bottom:6px;font:11px ui-monospace,monospace;" +
    "color:#9ca3af;background:rgba(0,0,0,0.35);padding:2px 6px;border-radius:3px;pointer-events:none;";
  wrap.appendChild(badge);

  const gl = tryCreateGPU(canvas);
  let renderer;
  let mode;
  if (gl) {
    try {
      renderer = new GPURenderer(canvas, gl);
      mode = "gpu";
    } catch (e) {
      console.warn("AttractorWidget: GPU init failed, falling back to CPU.", e);
    }
  }
  if (!renderer) {
    // Replace canvas with a fresh one bound to 2D context.
    wrap.removeChild(canvas);
    canvas = document.createElement("canvas");
    canvas.width = model.get("width");
    canvas.height = model.get("height");
    wrap.insertBefore(canvas, badge);
    renderer = new CPURenderer(canvas);
    mode = "cpu";
  }
  badge.textContent = mode;

  // Initial configuration order matters: params (and therefore param names) must
  // be set before compiling formulas.
  renderer.setParams(model.get("params"));
  renderer.setColormap(model.get("colormap"));
  renderer.setColorSpeed(model.get("color_speed"));
  renderer.setColorPhase(model.get("color_phase"));
  renderer.setBackground(model.get("background"));
  renderer.setView(model.get("view"));
  renderer.setIterationsPerFrame(model.get("iterations_per_frame"));
  renderer.setNPoints(model.get("n_points"));
  renderer.setExprs(model.get("x_expr"), model.get("y_expr"));

  // Only run the render loop while the canvas is on-screen and the tab is
  // visible. Multiple attractor widgets in one notebook would otherwise stack
  // up and starve the main thread.
  let visible = true;
  let documentVisible = !document.hidden;
  let started = false;
  const updateRunning = () => {
    const shouldRun = visible && documentVisible;
    if (shouldRun && !started) {
      renderer.start();
      started = true;
    } else if (!shouldRun && started) {
      renderer.stop();
      started = false;
    }
  };
  const io = new IntersectionObserver((entries) => {
    visible = entries[0].isIntersecting;
    updateRunning();
  }, { threshold: 0 });
  io.observe(wrap);
  const onVis = () => {
    documentVisible = !document.hidden;
    updateRunning();
  };
  document.addEventListener("visibilitychange", onVis);
  updateRunning();

  // Pan/zoom interaction. We mirror the `view` traitlet locally so that
  // continuous gestures don't have to round-trip through the comm channel.
  // The model is updated on a small trailing throttle.
  let currentView = model.get("view").slice();
  let viewFromSelf = false;
  let viewSyncTimer = null;
  const syncViewToModel = () => {
    if (viewSyncTimer != null) return;
    viewSyncTimer = setTimeout(() => {
      viewSyncTimer = null;
      viewFromSelf = true;
      model.set("view", currentView);
      model.save_changes();
    }, 80);
  };

  canvas.style.cursor = "grab";

  const onWheel = (e) => {
    e.preventDefault();
    const rect = canvas.getBoundingClientRect();
    const fx = (e.clientX - rect.left) / rect.width;
    const fy = 1 - (e.clientY - rect.top) / rect.height; // world-y is up
    const [xmin, xmax, ymin, ymax] = currentView;
    const cx = xmin + fx * (xmax - xmin);
    const cy = ymin + fy * (ymax - ymin);
    // Normalise the wheel delta. Mouse wheels report deltaY≈100/notch; trackpads
    // fire many small events. exp(deltaY * 0.0015) gives ~1.16×/notch for a
    // mouse, ~1.006×/event for a trackpad — both feel like a gentle zoom.
    const factor = Math.exp(e.deltaY * 0.0015);
    currentView = [
      cx + (xmin - cx) * factor,
      cx + (xmax - cx) * factor,
      cy + (ymin - cy) * factor,
      cy + (ymax - cy) * factor,
    ];
    renderer.setView(currentView);
    syncViewToModel();
  };
  canvas.addEventListener("wheel", onWheel, { passive: false });

  let panning = false;
  let panLastX = 0;
  let panLastY = 0;
  const onMouseDown = (e) => {
    if (e.button !== 0) return;
    panning = true;
    panLastX = e.clientX;
    panLastY = e.clientY;
    canvas.style.cursor = "grabbing";
    e.preventDefault();
  };
  const onMouseMove = (e) => {
    if (!panning) return;
    const dx = e.clientX - panLastX;
    const dy = e.clientY - panLastY;
    panLastX = e.clientX;
    panLastY = e.clientY;
    const rect = canvas.getBoundingClientRect();
    const [xmin, xmax, ymin, ymax] = currentView;
    const dxw = -(dx / rect.width) * (xmax - xmin);
    const dyw = (dy / rect.height) * (ymax - ymin); // screen y is flipped
    currentView = [xmin + dxw, xmax + dxw, ymin + dyw, ymax + dyw];
    renderer.setView(currentView);
    syncViewToModel();
  };
  const onMouseUp = () => {
    if (!panning) return;
    panning = false;
    canvas.style.cursor = "grab";
  };
  canvas.addEventListener("mousedown", onMouseDown);
  window.addEventListener("mousemove", onMouseMove);
  window.addEventListener("mouseup", onMouseUp);

  const onParams = () => { renderer.setParams(model.get("params")); };
  const onExpr = () => {
    try {
      renderer.setExprs(model.get("x_expr"), model.get("y_expr"));
    } catch (e) {
      console.error("Attractor formula error:", e);
    }
  };
  const onView = () => {
    if (viewFromSelf) {
      viewFromSelf = false;
      return;
    }
    currentView = model.get("view").slice();
    renderer.setView(currentView);
  };
  const onN = () => { renderer.setNPoints(model.get("n_points")); };
  const onCS = () => { renderer.setColorSpeed(model.get("color_speed")); };
  const onCP = () => { renderer.setColorPhase(model.get("color_phase")); };
  const onCM = () => { renderer.setColormap(model.get("colormap")); };
  const onBG = () => { renderer.setBackground(model.get("background")); };
  const onIPF = () => { renderer.setIterationsPerFrame(model.get("iterations_per_frame")); };
  const onSize = () => {
    renderer.resize(model.get("width"), model.get("height"));
    if (renderer.setNPoints) renderer.setNPoints(model.get("n_points"));
  };

  model.on("change:params", onParams);
  model.on("change:x_expr", onExpr);
  model.on("change:y_expr", onExpr);
  model.on("change:view", onView);
  model.on("change:n_points", onN);
  model.on("change:color_speed", onCS);
  model.on("change:color_phase", onCP);
  model.on("change:colormap", onCM);
  model.on("change:background", onBG);
  model.on("change:iterations_per_frame", onIPF);
  model.on("change:width", onSize);
  model.on("change:height", onSize);

  return () => {
    model.off("change:params", onParams);
    model.off("change:x_expr", onExpr);
    model.off("change:y_expr", onExpr);
    model.off("change:view", onView);
    model.off("change:n_points", onN);
    model.off("change:color_speed", onCS);
    model.off("change:color_phase", onCP);
    model.off("change:colormap", onCM);
    model.off("change:background", onBG);
    model.off("change:iterations_per_frame", onIPF);
    model.off("change:width", onSize);
    model.off("change:height", onSize);
    document.removeEventListener("visibilitychange", onVis);
    canvas.removeEventListener("wheel", onWheel);
    canvas.removeEventListener("mousedown", onMouseDown);
    window.removeEventListener("mousemove", onMouseMove);
    window.removeEventListener("mouseup", onMouseUp);
    if (viewSyncTimer != null) clearTimeout(viewSyncTimer);
    io.disconnect();
    renderer.dispose();
  };
}

export default { render };
