const ROW_H = 34;
const INDENT = 18;
const SVG_NS = "http://www.w3.org/2000/svg";

function el(tag, cls, text) {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text !== undefined && text !== null) node.textContent = text;
  return node;
}

function svg(tag, attrs) {
  const node = document.createElementNS(SVG_NS, tag);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  return node;
}

function fmt(ms) {
  if (ms < 1) return ms.toFixed(2).replace(/\.?0+$/, "") + "ms";
  if (ms < 1000) return Math.round(ms) + "ms";
  if (ms < 10000) return (ms / 1000).toFixed(1).replace(/\.0$/, "") + "s";
  if (ms < 60000) return Math.round(ms / 1000) + "s";
  const m = Math.floor(ms / 60000);
  const s = Math.round((ms % 60000) / 1000);
  return s ? `${m}m ${s}s` : `${m}m`;
}

function compact(n) {
  if (Math.abs(n) >= 1e6) return (n / 1e6).toFixed(1).replace(/\.0$/, "") + "M";
  if (Math.abs(n) >= 1e3) return (n / 1e3).toFixed(1).replace(/\.0$/, "") + "K";
  return String(Math.round(n * 100) / 100);
}

// ~5 round-numbered ticks (1/2/5 × 10^k ms) covering [0, dur].
function ticks(dur) {
  const raw = dur / 5;
  const pow = Math.pow(10, Math.floor(Math.log10(raw || 1)));
  const step = [1, 2, 5, 10].map((m) => m * pow).find((s) => s >= raw) || raw;
  const out = [];
  for (let t = 0; t <= dur + 1e-9; t += step) out.push(t);
  return out;
}

// Group spans by trace, ordered by when each trace started.
function groupTraces(spans) {
  const traces = new Map();
  for (const s of spans) {
    if (!traces.has(s.trace_id)) traces.set(s.trace_id, []);
    traces.get(s.trace_id).push(s);
  }
  return Array.from(traces.entries())
    .map(([id, list]) => {
      const start = Math.min(...list.map((s) => s.start_ms));
      const ids = new Set(list.map((s) => s.span_id));
      const root = list.find((s) => !s.parent_id || !ids.has(s.parent_id)) || list[0];
      return { id, spans: list, start, root };
    })
    .sort((a, b) => a.start - b.start);
}

// Relative timings + state of each span at time `t` (ms since trace start).
function spanState(s, t0, t) {
  const start = s.start_ms - t0;
  const end = s.end_ms === null || s.end_ms === undefined ? null : s.end_ms - t0;
  if (start > t) return { state: "pending", start, end: null };
  if (end === null || end > t) return { state: "running", start, end: t };
  return { state: s.status === "error" ? "error" : "ok", start, end };
}

// Depth-first rows (children under parents, by start time), skipping collapsed subtrees.
function buildRows(spans, collapsed) {
  const ids = new Set(spans.map((s) => s.span_id));
  const children = new Map();
  for (const s of spans) {
    const key = s.parent_id && ids.has(s.parent_id) ? s.parent_id : "__root__";
    if (!children.has(key)) children.set(key, []);
    children.get(key).push(s);
  }
  for (const list of children.values()) list.sort((a, b) => a.start_ms - b.start_ms);

  const rows = [];
  const walk = (span, depth, parentRow) => {
    const kids = children.get(span.span_id) || [];
    const row = { span, depth, parentRow, nKids: kids.length, index: rows.length };
    rows.push(row);
    if (collapsed.has(span.span_id)) return;
    for (const kid of kids) walk(kid, depth + 1, row);
  };
  for (const r of children.get("__root__") || []) walk(r, 0, null);
  return rows;
}

function formatValue(v) {
  if (typeof v === "string") return v;
  return JSON.stringify(v, null, 2);
}

function render({ model, el: host }) {
  const root = el("div", "traceview");
  host.appendChild(root);

  // The header controls are built once and only updated on redraw: replacing a
  // button or slider mid-gesture (we redraw every frame while replaying) would
  // swallow clicks and break dragging.
  const header = el("div", "tv-title-row");
  const titleEl = el("span", "tv-title");
  const subtitleEl = el("span", "tv-subtitle");
  const picker = el("select", "tv-picker");
  const playBtn = el("button", "tv-play");
  const scrub = el("input", "tv-scrub");
  scrub.type = "range";
  scrub.min = 0;
  const clock = el("span", "tv-clock");
  header.append(titleEl, subtitleEl, picker, playBtn, scrub, clock);
  const content = el("div");
  root.append(header, content);

  let playing = false;
  let localCursor = model.get("cursor_ms"); // follows the model, but moves locally while scrubbing
  let clockOffset = model.get("now_ms") - Date.now();
  let dur = 1; // duration of the trace on screen, as of the last draw
  let frame = null;
  let liveFrame = null;
  let lastLiveDraw = 0;
  // Live-follow state. A rerun starts a new trace that replaces the one on
  // screen; we keep the old row count and time scale while it runs so the page
  // doesn't shrink and regrow (moving everything below) and bars don't rescale
  // on every frame.
  let shownTraceId = null;
  let shownRows = 0;
  let heldRows = 0;
  let scale = 0;
  let lastFrameT = 0;
  let scrollTop = 0;
  let pickerKey = "";

  function current() {
    const traces = groupTraces(model.get("spans") || []);
    const wanted = model.get("trace_id");
    const trace = traces.find((t) => t.id === wanted) || traces[traces.length - 1] || null;
    return { traces, trace };
  }

  // Trace duration "so far": running spans extend it up to the kernel's now.
  function extent(trace) {
    const now = Date.now() + clockOffset;
    let end = 0;
    let anyRunning = false;
    for (const s of trace.spans) {
      if (s.end_ms === null || s.end_ms === undefined) {
        anyRunning = true;
        end = Math.max(end, now - trace.start);
      } else {
        end = Math.max(end, s.end_ms - trace.start);
      }
    }
    return { dur: Math.max(end, 1), anyRunning };
  }

  function setCursor(value, save) {
    localCursor = value;
    if (save) {
      model.set("cursor_ms", value);
      model.save_changes();
    }
  }

  function stopPlaying() {
    playing = false;
    if (frame) cancelAnimationFrame(frame);
    frame = null;
  }

  function startPlaying() {
    if (localCursor === null || localCursor >= dur) localCursor = 0;
    playing = true;
    // Replays take 3–12s of wall time, whatever the trace's real length.
    const speed = dur / Math.min(Math.max(dur, 3000), 12000);
    lastFrameT = performance.now();
    const tick = (now) => {
      if (!playing) return;
      const next = localCursor + (now - lastFrameT) * speed;
      lastFrameT = now;
      if (next >= dur) {
        stopPlaying();
        setCursor(null, true);
        draw();
        return;
      }
      localCursor = next;
      draw();
      frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
  }

  picker.addEventListener("change", () => {
    stopPlaying();
    setCursor(null, false);
    model.set("trace_id", picker.value);
    model.set("cursor_ms", null);
    model.set("selected_span_id", null);
    model.save_changes();
  });
  playBtn.addEventListener("click", () => {
    if (playing) {
      stopPlaying();
      setCursor(localCursor, true);
    } else {
      startPlaying();
    }
    draw();
  });
  scrub.addEventListener("input", () => {
    stopPlaying();
    const v = Number(scrub.value);
    setCursor(v >= dur ? null : v, false);
    draw();
  });
  scrub.addEventListener("change", () => setCursor(localCursor, true));

  // Rows are rebuilt on every draw, so a plain "click" can be lost when the row
  // under the pointer is replaced between press and release. Instead, act when
  // press and release land on the same [data-action] target.
  const actionKey = (ev) => {
    const target = ev.target.closest("[data-action]");
    return target ? `${target.dataset.action}:${target.dataset.span}` : null;
  };
  let downKey = null;
  content.addEventListener("pointerdown", (ev) => {
    downKey = ev.button === 0 ? actionKey(ev) : null;
  });
  content.addEventListener("pointerup", (ev) => {
    const key = actionKey(ev);
    if (key && key === downKey) {
      const [action, spanId] = key.split(":");
      if (action === "select") select(spanId);
      if (action === "toggle") {
        // Hold the current height until the pointer leaves: if collapsing shrank
        // the page, the browser would scroll and move the toggle away from the
        // pointer, so a second click could no longer undo the first.
        content.style.minHeight = content.offsetHeight + "px";
        toggleCollapsed(spanId);
      }
    }
    downKey = null;
  });
  root.addEventListener("pointerleave", () => {
    content.style.minHeight = "";
  });

  function select(spanId) {
    const next = model.get("selected_span_id") === spanId ? null : spanId;
    model.set("selected_span_id", next);
    model.save_changes();
  }

  function toggleCollapsed(spanId) {
    const list = model.get("collapsed") || [];
    const next = list.includes(spanId) ? list.filter((id) => id !== spanId) : [...list, spanId];
    model.set("collapsed", next);
    model.save_changes();
  }

  function action(node, name, spanId) {
    node.dataset.action = name;
    node.dataset.span = spanId;
    return node;
  }

  function drawHeader(traces, trace, t, services) {
    titleEl.textContent = model.get("title");
    subtitleEl.textContent = services.join(", ");
    const key = traces.map((tr) => tr.id).join(",");
    if (key !== pickerKey) {
      pickerKey = key;
      picker.replaceChildren(
        ...traces.map((tr, i) => {
          const opt = el("option", null, `#${i + 1} · ${tr.root.name} · ${new Date(tr.start).toLocaleTimeString()}`);
          opt.value = tr.id;
          return opt;
        }),
      );
    }
    picker.style.display = traces.length > 1 ? "" : "none";
    if (trace && picker.value !== trace.id) picker.value = trace.id;
    playBtn.textContent = playing ? "Pause" : "Replay";
    playBtn.classList.toggle("tv-playing", playing);
    for (const node of [playBtn, scrub, clock]) node.style.display = trace ? "" : "none";
    scrub.max = dur;
    scrub.step = dur / 1000;
    scrub.value = t;
    scrub.style.setProperty("--tv-fill", (t / dur) * 100 + "%");
    clock.textContent = fmt(t);
  }

  function draw() {
    const prevScroller = content.querySelector(".tv-rows");
    if (prevScroller) scrollTop = prevScroller.scrollTop;
    content.replaceChildren();

    const { traces, trace } = current();
    if (!trace) {
      shownTraceId = null;
      drawHeader(traces, null, 0, []);
      content.appendChild(el("div", "tv-empty", "No spans yet — start a span, or load an OTLP export."));
      scheduleLive(false);
      return;
    }

    const ext = extent(trace);
    const prevDur = dur;
    dur = ext.dur;
    if (trace.id !== shownTraceId) {
      const following = shownTraceId !== null && ext.anyRunning;
      heldRows = following ? shownRows : 0;
      scale = following ? Math.max(scale, prevDur) * 1.1 : 0;
      shownTraceId = trace.id;
    }
    if (!ext.anyRunning) {
      heldRows = 0;
      scale = dur;
    } else if (scale < dur) {
      scale = Math.max(1000, dur * 1.5); // grow in steps, not every frame
    }
    const cursor = localCursor === null || localCursor === undefined ? null : Math.min(localCursor, dur);
    const t = cursor === null ? dur : cursor;
    const services = [...new Set(trace.spans.map((s) => s.service).filter(Boolean))];
    const multiService = services.length > 1;
    drawHeader(traces, trace, t, services);

    // --- status line ------------------------------------------------------------
    const states = trace.spans.map((s) => spanState(s, trace.start, t).state);
    const nRunning = states.filter((s) => s === "running").length;
    const nErrors = states.filter((s) => s === "error").length;
    const nExceptions = trace.spans.reduce(
      (n, s) => n + s.events.filter((e) => e.name === "exception" && e.t_ms - trace.start <= t).length,
      0,
    );
    const warnings = Math.max(nErrors, nExceptions);
    const statusRow = el("div", "tv-status-row");
    const status = el("span", "tv-status");
    if (nRunning) {
      status.appendChild(el("span", "tv-spinner"));
      status.appendChild(document.createTextNode(cursor !== null ? "Replaying" : "Running"));
    } else if (spanState(trace.root, trace.start, t).state === "error") {
      status.classList.add("tv-st-error");
      status.textContent = "✕ Failed";
    } else {
      status.classList.add("tv-st-ok");
      status.textContent = cursor !== null ? "● Replaying" : "✓ Completed";
    }
    statusRow.appendChild(status);
    const meta = el("span", "tv-meta");
    meta.appendChild(el("span", null, `${trace.spans.length} spans`));
    if (warnings) meta.appendChild(el("span", "tv-warn", `${warnings} ${warnings === 1 ? "error" : "errors"}`));
    statusRow.appendChild(meta);
    content.appendChild(statusRow);

    // --- table ----------------------------------------------------------------
    // Column widths depend only on the whole trace (never on what is folded), so
    // expanding/collapsing a row never shifts anything under the pointer.
    const collapsed = new Set(model.get("collapsed") || []);
    const rows = buildRows(trace.spans, collapsed);
    const isNum = (v) => typeof v === "number" && isFinite(v);
    const hasProgress = trace.spans.some(
      (s) => isNum(s.attributes["progress.done"]) && isNum(s.attributes["progress.total"]),
    );
    const cols = ["minmax(220px, 2.2fr)", "92px"];
    if (hasProgress) cols.push("96px");
    cols.push("minmax(160px, 3fr)", "60px");
    root.style.setProperty("--tv-cols", cols.join(" "));

    // Tree geometry: each level indents by INDENT; a row's dot sits just left of
    // its name and an elbow joins it to its parent's dot.
    const dotX = (depth) => 14 + Math.min(depth, 12) * INDENT;
    const nameIndent = (depth) => dotX(depth) + 10;

    const head = el("div", "tv-row tv-head");
    const spanHead = el("div", null, "Span");
    spanHead.style.paddingLeft = nameIndent(0) + 18 + "px";
    head.appendChild(spanHead);
    head.appendChild(el("div", null, "State"));
    if (hasProgress) head.appendChild(el("div", null, "Progress"));
    const axis = el("div", "tv-axis");
    for (const tick of ticks(scale)) {
      if (tick / scale > 0.9) continue; // would collide with the Duration header
      const label = el("span", null, fmt(tick).replace(/^0ms$/, "0"));
      label.style.left = (tick / scale) * 100 + "%";
      axis.appendChild(label);
    }
    head.appendChild(axis);
    head.appendChild(el("div", "tv-right", "Duration"));
    content.appendChild(head);

    const scroller = el("div", "tv-rows");
    const height = model.get("height");
    if (height > 0) scroller.style.maxHeight = height + "px";
    const body = el("div", "tv-body");
    body.style.height = Math.max(rows.length, heldRows) * ROW_H + "px";
    shownRows = rows.length;
    scroller.appendChild(body);

    const selectedId = model.get("selected_span_id");
    const maxDepth = Math.max(0, ...rows.map((r) => r.depth));
    const gutter = svg("svg", { class: "tv-gutter", width: dotX(maxDepth) + 10, height: rows.length * ROW_H });
    body.appendChild(gutter);

    const cy = (row) => row.index * ROW_H + ROW_H / 2;
    const rowById = new Map(rows.map((r) => [r.span.span_id, r]));
    const nameById = new Map(trace.spans.map((s) => [s.span_id, s.name]));
    const ticksList = ticks(scale);

    for (const row of rows) {
      const s = row.span;
      const st = spanState(s, trace.start, t);
      const isSelected = s.span_id === selectedId;
      const x = dotX(row.depth);
      const y = cy(row);

      if (row.parentRow) {
        const px = dotX(row.parentRow.depth);
        gutter.appendChild(svg("path", {
          d: `M${px},${cy(row.parentRow) + 5} V${y - 7} Q${px},${y} ${px + 7},${y} H${x - 5}`,
          class: `tv-edge tv-edge-${st.state}`,
        }));
      }
      // Span links (e.g. a queue consumer pointing at its producer): dashed
      // curve bowing out to the left edge.
      for (const linkId of s.links || []) {
        const other = rowById.get(linkId);
        if (!other) continue;
        const ox = dotX(other.depth);
        const oy = cy(other);
        gutter.appendChild(svg("path", {
          d: `M${ox - 5},${oy} C2,${oy} 2,${y} ${x - 5},${y}`,
          class: "tv-link",
        }));
      }
      gutter.appendChild(svg("circle", {
        cx: x, cy: y, r: isSelected ? 6 : 4.5, class: `tv-dot tv-dot-${st.state}`,
      }));

      const line = action(
        el("div", `tv-row tv-span tv-${st.state}` + (isSelected ? " tv-selected" : "")),
        "select",
        s.span_id,
      );
      line.style.top = row.index * ROW_H + "px";

      const name = el("div", "tv-name");
      name.style.paddingLeft = nameIndent(row.depth) + "px";
      const isCollapsed = collapsed.has(s.span_id);
      if (row.nKids) {
        const toggle = action(el("button", "tv-toggle", isCollapsed ? "+" : "−"), "toggle", s.span_id);
        toggle.title = isCollapsed ? `Expand ${row.nKids} child spans` : "Collapse";
        name.appendChild(toggle);
      } else {
        name.appendChild(el("span", "tv-toggle-spacer"));
      }
      // Name the service only where the trace crosses into a different one.
      const parentService = row.parentRow ? row.parentRow.span.service : null;
      if (multiService && s.service && s.service !== parentService) {
        name.appendChild(el("span", "tv-service", s.service));
      }
      const label = el("span", "tv-label", s.name);
      label.title = s.name;
      name.appendChild(label);
      if (isCollapsed) name.appendChild(el("span", "tv-count", `+${row.nKids}`));
      line.appendChild(name);

      const state = el("div", "tv-state");
      if (st.state === "running") state.appendChild(el("span", "tv-spinner"));
      else state.appendChild(el("span", `tv-pip tv-pip-${st.state}`));
      state.appendChild(document.createTextNode(
        { pending: "Pending", running: "Running", ok: "Ok", error: "Error" }[st.state],
      ));
      line.appendChild(state);

      if (hasProgress) {
        const cell = el("div", "tv-progress");
        const done = s.attributes["progress.done"];
        const total = s.attributes["progress.total"];
        if (st.state !== "pending" && isNum(done) && isNum(total) && total > 0) {
          cell.appendChild(el("span", "tv-progress-label", `${compact(done)}/${compact(total)}`));
          const track = el("span", "tv-progress-track");
          const fill = el("span", "tv-progress-fill");
          fill.style.width = Math.min(100, (done / total) * 100) + "%";
          track.appendChild(fill);
          cell.appendChild(track);
        } else {
          cell.appendChild(el("span", "tv-dash", "—"));
        }
        line.appendChild(cell);
      }

      const lane = el("div", "tv-lane");
      for (const tick of ticksList) {
        const grid = el("span", "tv-grid");
        grid.style.left = (tick / scale) * 100 + "%";
        lane.appendChild(grid);
      }
      if (st.state !== "pending") {
        const width = ((st.end - st.start) / scale) * 100;
        if (width < 0.4 && st.state !== "running") {
          const dot = el("span", `tv-instant tv-bar-${st.state}`);
          dot.style.left = (st.start / scale) * 100 + "%";
          lane.appendChild(dot);
        } else {
          const bar = el("span", `tv-bar tv-bar-${st.state}`);
          bar.style.left = (st.start / scale) * 100 + "%";
          bar.style.width = Math.max(width, 0.4) + "%";
          lane.appendChild(bar);
        }
        for (const ev of s.events) {
          const et = ev.t_ms - trace.start;
          if (et > t) continue;
          const mark = el("span", "tv-event" + (ev.name === "exception" ? " tv-event-exc" : ""));
          mark.style.left = (et / scale) * 100 + "%";
          mark.title = `${ev.name} @ ${fmt(et)}`;
          lane.appendChild(mark);
        }
      }
      if (cursor !== null) {
        const cur = el("span", "tv-cursor");
        cur.style.left = (cursor / scale) * 100 + "%";
        lane.appendChild(cur);
      }
      line.appendChild(lane);

      line.appendChild(el("div", "tv-right tv-dur", st.state === "pending" ? "—" : fmt(st.end - st.start)));
      body.appendChild(line);
    }
    content.appendChild(scroller);
    scroller.scrollTop = scrollTop;

    // --- details drawer for the selected span, else the latest event ----------
    const selected = trace.spans.find((s) => s.span_id === selectedId);
    if (selected) content.appendChild(details(selected, trace, t, nameById));
    else {
      content.appendChild(latestEvent(trace, t));
    }

    const foot = el("div", "tv-foot");
    foot.appendChild(el("span", null, `trace ${trace.id.slice(0, 12)} · ${fmt(dur)}`));
    foot.appendChild(el("span", null, selected ? "click the row again to close" : "click a row for details"));
    content.appendChild(foot);

    scheduleLive(ext.anyRunning && cursor === null && !playing);
  }

  function latestEvent(trace, t) {
    let best = null;
    for (const s of trace.spans) {
      for (const ev of s.events) {
        const et = ev.t_ms - trace.start;
        if (et <= t && (!best || et >= best.et)) best = { s, ev, et };
      }
    }
    if (!best) {
      const empty = el("div", "tv-latest");
      empty.appendChild(el("span", "tv-latest-label", "▸ Latest event"));
      empty.appendChild(el("span", "tv-muted", "none yet"));
      return empty;
    }
    const box = action(el("div", "tv-latest"), "select", best.s.span_id);
    box.appendChild(el("span", "tv-latest-label", "▸ Latest event"));
    box.appendChild(el("span", "tv-mono", fmt(best.et)));
    box.appendChild(el("span", "tv-muted", best.s.name));
    const attrs = best.ev.attributes || {};
    const text = attrs["exception.message"] || attrs.message || attrs["log.message"] || "";
    box.appendChild(el("span", best.ev.name === "exception" ? "tv-err-text" : null, text ? `${best.ev.name}: ${text}` : best.ev.name));
    return box;
  }

  function details(s, trace, t, nameById) {
    const box = el("div", "tv-details");
    const top = el("div", "tv-details-top");
    top.appendChild(el("span", "tv-details-name", s.name));
    const st = spanState(s, trace.start, t);
    top.appendChild(el("span", `tv-badge tv-badge-${st.state}`, st.state));
    const facts = [
      s.service,
      s.kind,
      `starts ${fmt(st.start)}`,
      st.state === "pending" ? null : `took ${fmt(st.end - st.start)}`,
    ].filter(Boolean);
    top.appendChild(el("span", "tv-muted", facts.join(" · ")));
    const close = action(el("button", "tv-close", "×"), "select", s.span_id);
    close.title = "Close";
    top.appendChild(close);
    box.appendChild(top);

    if (s.status_message) box.appendChild(el("div", "tv-err-text tv-status-msg", s.status_message));

    const grid = el("div", "tv-kv");
    const addKV = (k, v, mono) => {
      grid.appendChild(el("div", "tv-k", k));
      grid.appendChild(el("div", "tv-v" + (mono ? " tv-mono" : ""), formatValue(v)));
    };
    addKV("span_id", s.span_id, true);
    if (s.parent_id) addKV("parent_id", s.parent_id, true);
    if (s.links && s.links.length) {
      addKV("links to", s.links.map((id) => nameById.get(id) || id).join(", "), false);
    }
    for (const [k, v] of Object.entries(s.attributes || {})) addKV(k, v, false);
    box.appendChild(grid);

    if (s.events.length) {
      box.appendChild(el("div", "tv-section", "Events"));
      for (const ev of s.events) {
        const et = ev.t_ms - trace.start;
        const row = el("div", "tv-ev-row" + (et > t ? " tv-future" : ""));
        row.appendChild(el("span", "tv-mono tv-muted", fmt(et)));
        row.appendChild(el("span", ev.name === "exception" ? "tv-err-text" : "tv-ev-name", ev.name));
        const attrs = Object.entries(ev.attributes || {});
        if (attrs.length) {
          const kv = el("div", "tv-kv tv-ev-kv");
          for (const [k, v] of attrs) {
            kv.appendChild(el("div", "tv-k", k));
            kv.appendChild(el("div", "tv-v" + (k === "exception.stacktrace" ? " tv-mono" : ""), formatValue(v)));
          }
          row.appendChild(kv);
        }
        box.appendChild(row);
      }
    }
    return box;
  }

  // While spans are running live, redraw every animation frame so bars grow
  // smoothly (a few times a second for big traces, where a redraw costs more).
  function scheduleLive(on) {
    if (on && !liveFrame) {
      const loop = (now) => {
        const big = (model.get("spans") || []).length > 300;
        if (big && now - lastLiveDraw < 250) {
          liveFrame = requestAnimationFrame(loop);
          return;
        }
        liveFrame = null;
        lastLiveDraw = now;
        draw();
      };
      liveFrame = requestAnimationFrame(loop);
    }
    if (!on && liveFrame) {
      cancelAnimationFrame(liveFrame);
      liveFrame = null;
    }
  }

  model.on("change:spans", draw);
  model.on("change:now_ms", () => {
    clockOffset = model.get("now_ms") - Date.now();
  });
  model.on("change:cursor_ms", () => {
    if (!playing) {
      localCursor = model.get("cursor_ms");
      draw();
    }
  });
  for (const name of ["trace_id", "selected_span_id", "collapsed", "title", "height"]) {
    model.on(`change:${name}`, draw);
  }
  draw();

  return () => {
    stopPlaying();
    scheduleLive(false);
  };
}

export default { render };
export { buildRows, groupTraces, spanState, ticks }; // exported for tests
