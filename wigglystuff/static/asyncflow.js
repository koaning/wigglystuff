// Build per-task swimlane data from the flat event stream, ordered as a tree.
function buildLanes(events, nowMs, running) {
  const byTask = new Map();
  const parent = {}; // task -> parent task name (from the "by <task>" spawn detail)
  let maxT = nowMs || 0;

  for (const e of events) {
    if (!byTask.has(e.task)) {
      byTask.set(e.task, { task: e.task, coro: e.coro, events: [] });
    }
    const lane = byTask.get(e.task);
    lane.events.push(e);
    if (e.event === "SPAWN") {
      if (e.coro) lane.coro = e.coro;
      const m = /by (.+)$/.exec(e.detail || "");
      parent[e.task] = m ? m[1] : null;
    }
    if (e.t_ms > maxT) maxT = e.t_ms;
  }
  if (maxT <= 0) maxT = 1;

  // Turn each task's events into run/wait segments + timing totals.
  const laneMap = new Map();
  for (const lane of byTask.values()) {
    const evs = lane.events.slice().sort((a, b) => a.t_ms - b.t_ms);
    const segs = [];
    let segStart = null;
    let mode = null;
    let done = false;
    let spawnT = evs[0].t_ms;
    let doneT = null;
    let lastT = spawnT;
    let runMs = 0;
    let waitMs = 0;

    const closeSeg = (end) => {
      if (segStart !== null && mode !== null && end > segStart) {
        segs.push({ start: segStart, end, mode });
        if (mode === "run") runMs += end - segStart;
        else waitMs += end - segStart;
      }
    };

    for (const e of evs) {
      lastT = e.t_ms;
      closeSeg(e.t_ms);
      switch (e.event) {
        case "SPAWN": spawnT = e.t_ms; segStart = e.t_ms; mode = "run"; break;
        case "RESUME": segStart = e.t_ms; mode = "run"; break;
        case "SUSPEND": segStart = e.t_ms; mode = "wait"; break;
        case "RETURN": segStart = e.t_ms; mode = "run"; break;
        case "DONE": segStart = null; mode = null; done = true; doneT = e.t_ms; break;
        default: break;
      }
    }
    if (!done && segStart !== null && mode !== null) {
      closeSeg(running ? Math.max(nowMs, lastT) : lastT);
    }
    const endT = done ? doneT : running ? Math.max(nowMs, lastT) : lastT;
    laneMap.set(lane.task, {
      task: lane.task, coro: lane.coro, depth: 0, segs, done,
      spawnT, endT, durMs: Math.max(0, endT - spawnT), runMs, waitMs,
    });
  }

  // Group children under parents; roots are tasks whose parent we don't track.
  const children = new Map();
  for (const task of laneMap.keys()) {
    const p = parent[task];
    const key = p && laneMap.has(p) ? p : "__root__";
    if (!children.has(key)) children.set(key, []);
    children.get(key).push(task);
  }
  for (const arr of children.values()) {
    arr.sort((a, b) => laneMap.get(a).spawnT - laneMap.get(b).spawnT);
  }

  // Depth-first order: each parent immediately followed by its descendants.
  const lanes = [];
  const walk = (task, depth) => {
    const obj = laneMap.get(task);
    obj.depth = depth;
    lanes.push(obj);
    for (const c of children.get(task) || []) walk(c, depth + 1);
  };
  for (const r of children.get("__root__") || []) walk(r, 0);
  return { lanes, maxT };
}

function fmt(ms) {
  return ms >= 1000 ? (ms / 1000).toFixed(2) + "s" : Math.round(ms) + "ms";
}

function render({ model, el }) {
  const root = document.createElement("div");
  root.className = "asyncflow";
  el.appendChild(root);

  // One floating tooltip, reused across hovers.
  const tip = document.createElement("div");
  tip.className = "af-tip";
  tip.style.display = "none";
  root.appendChild(tip);

  function showTip(ev, html) {
    tip.innerHTML = html;
    tip.style.display = "block";
    const r = root.getBoundingClientRect();
    let x = ev.clientX - r.left + 14;
    let y = ev.clientY - r.top + 14;
    // Keep it inside the widget: clamp horizontally, and flip above the cursor
    // when it would run off the bottom (fixes the last lanes being cut off).
    if (x + tip.offsetWidth > r.width) x = r.width - tip.offsetWidth - 4;
    if (y + tip.offsetHeight > r.height) y = ev.clientY - r.top - tip.offsetHeight - 14;
    tip.style.left = Math.max(0, x) + "px";
    tip.style.top = Math.max(0, y) + "px";
  }
  const hideTip = () => { tip.style.display = "none"; };

  function laneTip(lane) {
    return (
      `<div class="af-tip-title">${lane.coro}<span class="af-tip-task"> ${lane.task}</span></div>` +
      `<div class="af-tip-row"><span>total</span><b>${fmt(lane.durMs)}</b></div>` +
      `<div class="af-tip-row"><span>ran</span><b>${fmt(lane.runMs)}</b></div>` +
      `<div class="af-tip-row"><span>waited</span><b>${fmt(lane.waitMs)}</b></div>` +
      `<div class="af-tip-foot">${lane.done ? "finished at " + fmt(lane.endT) : "still running…"}</div>`
    );
  }

  function draw() {
    const events = model.get("events") || [];
    const nowMs = model.get("now_ms") || 0;
    const running = model.get("running");
    const width = model.get("width") || 0;

    root.style.width = width > 0 ? width + "px" : "";
    // Rebuild everything except the persistent tooltip node.
    for (const child of Array.from(root.children)) {
      if (child !== tip) root.removeChild(child);
    }
    hideTip();

    const header = document.createElement("div");
    header.className = "af-header";
    const nTasks = events.filter((e) => e.event === "SPAWN").length;
    const nDone = events.filter((e) => e.event === "DONE").length;
    header.innerHTML =
      `<span class="af-status ${running ? "af-running" : "af-idle"}">` +
      `${running ? "● running…" : "✓ done"}</span>` +
      `<span class="af-meta">${nDone}/${nTasks} tasks done · ${fmt(nowMs)}</span>`;
    root.appendChild(header);

    if (events.length === 0) {
      const empty = document.createElement("div");
      empty.className = "af-empty";
      empty.textContent = running ? "waiting for events…" : "no events captured";
      root.appendChild(empty);
      return;
    }

    const { lanes, maxT } = buildLanes(events, nowMs, running);
    const grid = document.createElement("div");
    grid.className = "af-grid";

    for (const lane of lanes) {
      const row = document.createElement("div");
      row.className = "af-lane";

      const name = document.createElement("div");
      name.className = "af-lane-name";
      name.style.paddingLeft = 8 + lane.depth * 16 + "px";
      const label = document.createElement("span");
      label.className = "af-coro";
      label.textContent = lane.coro;
      label.title = `${lane.coro} (${lane.task})`;
      name.appendChild(label);
      row.appendChild(name);

      const track = document.createElement("div");
      track.className = "af-track";

      if (lane.done) {
        const bar = document.createElement("div");
        bar.className = "af-seg af-solid";
        bar.style.left = (lane.spawnT / maxT) * 100 + "%";
        bar.style.width = Math.max(0.5, ((lane.endT - lane.spawnT) / maxT) * 100) + "%";
        track.appendChild(bar);
      } else {
        for (const s of lane.segs) {
          const seg = document.createElement("div");
          seg.className = `af-seg af-${s.mode}`;
          seg.style.left = (s.start / maxT) * 100 + "%";
          seg.style.width = Math.max(0, ((s.end - s.start) / maxT) * 100) + "%";
          track.appendChild(seg);
        }
      }

      // Hover anywhere on the lane → floating tooltip with timings.
      const html = laneTip(lane);
      track.addEventListener("mousemove", (ev) => showTip(ev, html));
      track.addEventListener("mouseleave", hideTip);
      name.addEventListener("mousemove", (ev) => showTip(ev, html));
      name.addEventListener("mouseleave", hideTip);

      row.appendChild(track);
      grid.appendChild(row);
    }
    root.appendChild(grid);

    const axis = document.createElement("div");
    axis.className = "af-axis";
    axis.innerHTML = `<span>0ms</span><span>${fmt(maxT / 2)}</span><span>${fmt(maxT)}</span>`;
    root.appendChild(axis);
  }

  model.on("change:events", draw);
  model.on("change:now_ms", draw);
  model.on("change:running", draw);
  model.on("change:width", draw);
  draw();
}

export default { render };
export { buildLanes }; // exported for tests
