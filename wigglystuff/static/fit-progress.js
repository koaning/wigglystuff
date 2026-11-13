// FitProgress: live view of a scikit-learn callback task tree.
// `tasks` is a flat list of non-leaf tasks, each with its `path` of task ids
// from the root, `total` subtasks, `done` finished subtasks and a `state`.

const keyOf = (path) => path.join("/");
const lastId = (node) => node.path[node.path.length - 1];

function buildTree(tasks) {
  const byKey = new Map();
  for (const t of tasks) byKey.set(keyOf(t.path), { ...t, children: [] });
  let root = null;
  for (const node of byKey.values()) {
    if (node.path.length === 1) root = node;
    const parent = byKey.get(keyOf(node.path.slice(0, -1)));
    if (parent) parent.children.push(node);
  }
  for (const node of byKey.values()) node.children.sort((a, b) => lastId(a) - lastId(b));
  return root;
}

// Fraction done, counting partially finished child tasks (like sklearn's ProgressBar).
function progress(node) {
  if (node.state === "done") return 1;
  if (!node.total) return 0;
  let endedChildren = 0;
  let childProgress = 0;
  for (const child of node.children) {
    if (child.state === "done") endedChildren += 1;
    childProgress += progress(child);
  }
  return Math.max(0, Math.min(1, (node.done - endedChildren + childProgress) / node.total));
}

// sklearn's lbfgs LogisticRegression reserves max_iter + 1 subtasks and always
// ends one extra (empty) one, so its finished subtasks are n_iter_ + 1.
function iterations(node) {
  if (node.max_iter != null && node.total === node.max_iter + 1) return Math.max(0, node.done - 1);
  return node.done;
}

// Estimators count progress differently. A solver reports one subtask per
// iteration (named like "lbfgs-iter"), a Pipeline reports its steps as child
// tasks, and estimators without callback support report nothing at all.
const countsIterations = (node) => Boolean(node.unit && node.unit.endsWith("-iter"));

// The task inside a fit that counts iterations: the fit itself, or e.g. the
// final step of a Pipeline.
function iterationNode(node) {
  if (countsIterations(node)) return node;
  for (const child of node.children) {
    const found = iterationNode(child);
    if (found) return found;
  }
  return null;
}

// A finished task (or one of its steps) that ran out of iterations, i.e. a
// solver that stopped at max_iter before converging.
function notConverged(node) {
  if (node.state === "done" && countsIterations(node) && node.done >= node.total) return node;
  for (const child of node.children) {
    const found = notConverged(child);
    if (found) return found;
  }
  return null;
}

const fitTime = (node) => (node && node.end_ms ? node.end_ms - node.start_ms : null);

// Short live readout for a fit: iterations if it counts them, the fit time
// once done, otherwise the step it is on.
function fitReadout(node) {
  if (!node) return "";
  const it = iterationNode(node);
  if (it) return String(iterations(it));
  if (node.state === "done") return fmtDuration(fitTime(node));
  if (node.total && node.done > 0) return `${node.done}/${node.total}`;
  return "";
}

// Overall progress. For a search every candidate/fold fit and the refit
// count as one fit each; weighting the search and the refit equally (as the
// task tree does) would put the bar at 50% when the search is nearly done.
function overallProgress(tree) {
  if (tree.state === "done") return 1;
  const search = tree.children.find((c) => c.task === "search" && c.n_splits);
  if (!search) return progress(tree);
  const refit = tree.children.find((c) => (c.source_task || c.task) === "refit-with-best-params");
  const refitPlanned = refit || tree.total > 1;
  const fitsDone = progress(search) * search.total + (refit ? progress(refit) : 0);
  return Math.min(1, fitsDone / (search.total + (refitPlanned ? 1 : 0)));
}

function fmtDuration(ms) {
  if (!isFinite(ms) || ms < 0) return "";
  if (ms < 1000) return `${Math.round(ms)}ms`;
  const s = Math.round(ms / 1000);
  if (s < 60) return `${(ms / 1000).toFixed(1)}s`;
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

const fmtScore = (v) => (v == null ? "–" : v.toFixed(3));

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function bar(fraction, state, extraClass = "") {
  const track = el("div", `fp-bar ${extraClass}`);
  const fill = el("div", `fp-fill fp-${state}`);
  fill.style.width = `${(fraction * 100).toFixed(1)}%`;
  track.appendChild(fill);
  return track;
}

// Status of one fit, as shown in its tooltip.
function fitStatus(node, score, scored) {
  if (!node) return { text: "Waiting to start", kind: "muted" };
  if (scored && score == null) return { text: "Failed: the fit raised an error, so it has no score", kind: "stop" };
  if (node.state === "stopped") return { text: "Stopped before it finished", kind: "stop" };
  const it = iterationNode(node);
  if (node.state === "running") {
    if (it) return { text: `Running · iteration ${iterations(it)}`, kind: "run" };
    if (node.total) return { text: `Running · step ${Math.min(node.done + 1, node.total)} of ${node.total}`, kind: "run" };
    return { text: "Running", kind: "run" };
  }
  const stuck = notConverged(node);
  if (stuck) {
    const who = stuck === node ? "" : `${stuck.estimator} `;
    const limit = stuck.max_iter != null ? `max_iter=${stuck.max_iter}` : `all ${stuck.total} iterations`;
    return { text: `Did not converge: ${who}stopped at ${limit}`, kind: "warn" };
  }
  if (it) return { text: `Converged after ${iterations(it)} iterations`, kind: "done" };
  return { text: "Done", kind: "done" };
}

function render({ model, el: host }) {
  const root = el("div", "fit-progress");
  host.appendChild(root);
  const tip = el("div", "fp-tip");
  let elapsedEl = null;

  // ---- tooltip ---------------------------------------------------------
  function showTip(ev, content) {
    tip.replaceChildren(...content);
    tip.style.display = "block";
    const r = root.getBoundingClientRect();
    let x = ev.clientX - r.left + 14;
    let y = ev.clientY - r.top + 14;
    if (x + tip.offsetWidth > r.width) x = ev.clientX - r.left - tip.offsetWidth - 14;
    if (y + tip.offsetHeight > r.height) y = ev.clientY - r.top - tip.offsetHeight - 14;
    tip.style.left = `${Math.max(0, x)}px`;
    tip.style.top = `${Math.max(0, y)}px`;
  }
  const hideTip = () => { tip.style.display = "none"; };
  // The view is rebuilt on every update, so remember what is hovered (by id)
  // and re-show its tooltip with fresh data after each redraw.
  const tipMakers = new Map();
  let hovered = null; // { id, ev }
  function attachTip(target, id, makeContent) {
    tipMakers.set(id, makeContent);
    target.addEventListener("mousemove", (ev) => {
      hovered = { id, ev };
      showTip(ev, makeContent());
    });
    target.addEventListener("mouseleave", () => {
      hovered = null;
      hideTip();
    });
  }
  function tipRow(label, value, valueClass = "") {
    const row = el("div", "fp-tip-row");
    row.appendChild(el("span", "", label));
    row.appendChild(el("b", valueClass, value));
    return row;
  }

  // ---- header ----------------------------------------------------------
  function elapsedMs() {
    const started = model.get("started_ms");
    if (!started) return 0;
    const end = model.get("status") === "running" ? Date.now() : model.get("now_ms");
    return Math.max(0, end - started);
  }

  function elapsedText(fraction) {
    const ms = elapsedMs();
    let text = `${fmtDuration(ms)} elapsed`;
    if (model.get("status") === "running" && fraction > 0.03 && fraction < 1) {
      text += ` · ~${fmtDuration((ms * (1 - fraction)) / fraction)} left`;
    }
    return text;
  }

  function header(tree, search) {
    const status = model.get("status");
    const fraction = tree ? overallProgress(tree) : 0;
    const box = el("div", "fp-header");
    const line = el("div", "fp-line");
    const statusText = { running: "Running", done: "Done", error: "Stopped", idle: "Waiting" }[status] || status;
    line.appendChild(el("span", `fp-status fp-status-${status}`, statusText));
    line.appendChild(el("span", "fp-title", tree ? tree.estimator : "No fit yet"));
    line.appendChild(el("span", "fp-spacer"));
    line.appendChild(el("span", "fp-pct", tree ? `${Math.floor(fraction * 100)}%` : ""));
    box.appendChild(line);
    const barState = status === "running" ? "running" : status === "error" ? "stopped" : fraction >= 1 ? "done" : "pending";
    box.appendChild(bar(fraction, barState, "fp-bar-main"));
    const meta = el("div", "fp-meta");
    if (search) {
      const fits = search.children.filter((c) => c.state === "done").length;
      meta.appendChild(el("span", "", `${fits} / ${search.total} fits`));
    }
    elapsedEl = el("span", "", tree ? elapsedText(fraction) : "Call progress.fit(estimator, X, y) to fill this in.");
    meta.appendChild(elapsedEl);
    box.appendChild(meta);
    return box;
  }

  // ---- search grid: one row per candidate, one column per fold ----------
  function searchGrid(search) {
    const scores = model.get("scores");
    const candidates = model.get("candidates") || [];
    const nSplits = search.n_splits;
    const nCandidates = Math.ceil(search.total / nSplits);
    const cells = Array.from({ length: nCandidates }, () => Array(nSplits).fill(null));
    const rowParams = Array(nCandidates).fill(null);
    const paramNames = [];
    for (const child of search.children) {
      const cand = Math.floor(lastId(child) / nSplits);
      if (cand >= nCandidates) continue;
      cells[cand][lastId(child) % nSplits] = child;
      if (child.params && !rowParams[cand]) rowParams[cand] = child.params;
      for (const name of Object.keys(child.params || {})) {
        if (!paramNames.includes(name)) paramNames.push(name);
      }
    }
    // Candidates known up front (GridSearchCV) or from cv_results_ label rows
    // whose fits did not report their parameters (no callback support).
    for (let cand = 0; cand < nCandidates; cand++) {
      if (!rowParams[cand] && candidates[cand]) rowParams[cand] = candidates[cand];
      for (const name of Object.keys(rowParams[cand] || {})) {
        if (!paramNames.includes(name)) paramNames.push(name);
      }
    }

    // Test scores arrive per fold while the search runs (node.score); the
    // final cv_results_ (`scores`) replaces them once it is done.
    const foldScore = (cand, k) => (scores ? scores.folds[cand]?.[k] : cells[cand][k]?.score ?? undefined);
    const meanScore = (cand) => {
      if (scores) return scores.mean[cand];
      const row = cells[cand].map((node) => node?.score);
      return row.every((v) => v != null) ? row.reduce((a, b) => a + b, 0) / row.length : undefined;
    };
    const metric = scores ? scores.metric : "score";

    let lo = Infinity;
    let hi = -Infinity;
    for (let cand = 0; cand < nCandidates; cand++) {
      for (let k = 0; k < nSplits; k++) {
        const v = foldScore(cand, k);
        if (v != null) { lo = Math.min(lo, v); hi = Math.max(hi, v); }
      }
    }
    const hasScores = hi >= lo;
    const shade = (v) => (hi > lo ? (v - lo) / (hi - lo) : 1);

    const wrap = el("div", "fp-grid-wrap");
    const table = el("table", "fp-grid");
    const thead = el("thead");
    const headRow = el("tr");
    if (paramNames.length === 0) headRow.appendChild(el("th", "fp-param", "candidate"));
    for (const name of paramNames) headRow.appendChild(el("th", "fp-param", name));
    for (let k = 0; k < nSplits; k++) headRow.appendChild(el("th", "fp-fold", `fold ${k + 1}`));
    if (hasScores) headRow.appendChild(el("th", "fp-fold", `mean ${metric}`));
    thead.appendChild(headRow);
    table.appendChild(thead);

    let anyMaxed = false;
    let anyFailed = false;
    const tbody = el("tbody");
    for (let cand = 0; cand < nCandidates; cand++) {
      const tr = el("tr");
      const isBest = scores && scores.best_index === cand;
      const params = rowParams[cand];
      const prev = cand > 0 ? rowParams[cand - 1] : null;
      // Pivot-table style: a value that repeats the row above (with everything
      // to its left also repeating) is left blank, so a grid reads as groups.
      let sameSoFar = Boolean(params && prev);
      if (paramNames.length > 1 && params && prev && params[paramNames[0]] !== prev[paramNames[0]]) {
        // A thin spacer row between groups of the first parameter.
        const gap = el("tr", "fp-gap");
        const gapCell = el("td");
        gapCell.colSpan = Math.max(1, paramNames.length) + nSplits + (hasScores ? 1 : 0);
        gap.appendChild(gapCell);
        tbody.appendChild(gap);
      }
      if (isBest) tr.classList.add("fp-best");
      if (paramNames.length === 0) tr.appendChild(el("td", "fp-param", `#${cand + 1}`));
      paramNames.forEach((name, i) => {
        const known = params && name in params;
        sameSoFar = sameSoFar && known && prev[name] === params[name] && i < paramNames.length - 1;
        const text = !known ? "…" : sameSoFar ? "" : params[name];
        tr.appendChild(el("td", known ? "fp-param" : "fp-param fp-unknown", text));
      });

      for (let k = 0; k < nSplits; k++) {
        const node = cells[cand][k];
        const state = node ? node.state : "pending";
        const td = el("td", `fp-cell fp-cell-${state}`);
        const score = foldScore(cand, k);
        const maxed = node && notConverged(node);
        const failed = scores && score == null;
        if (failed) {
          anyFailed = true;
          td.classList.add("fp-failed");
          td.appendChild(el("span", "fp-num", "failed"));
        } else if (score != null) {
          td.classList.add("fp-scored");
          td.style.setProperty("--fp-shade", shade(score).toFixed(3));
          td.appendChild(el("span", "fp-num", fmtScore(score)));
        } else if (node && node.state === "done") {
          // Finished but not scored yet (or a multi-metric search, whose
          // scores only arrive at the end).
          td.appendChild(el("span", "fp-num fp-unknown", fitReadout(node)));
        } else {
          // A fit that reports no progress of its own gets a full striped bar.
          const fraction = !node ? 0 : node.total ? progress(node) : 1;
          td.appendChild(bar(fraction, state, "fp-bar-mini"));
          td.appendChild(el("span", "fp-num", fitReadout(node)));
        }
        if (maxed && !failed) {
          anyMaxed = true;
          td.classList.add("fp-maxed");
          td.appendChild(el("span", "fp-warn", "!"));
        }
        attachTip(td, `cell-${cand}-${k}`, () => cellTip(cand, k, nSplits, params, node, scores));
        tr.appendChild(td);
      }
      if (hasScores) {
        const mean = meanScore(cand);
        const td = el("td", "fp-mean", mean === undefined ? "" : fmtScore(mean));
        if (isBest) td.appendChild(el("span", "fp-badge", "best"));
        tr.appendChild(td);
      }
      tbody.appendChild(tr);
    }
    table.appendChild(tbody);
    wrap.appendChild(table);

    const out = [wrap];
    if (search.children.length) {
      const legend = el("div", "fp-legend");
      if (hasScores) {
        legend.appendChild(el("span", "fp-legend-swatch fp-legend-shade", ""));
        legend.appendChild(el("span", "", `darker = higher test ${metric}`));
      }
      if (anyMaxed) {
        legend.appendChild(el("span", "fp-legend-swatch fp-legend-warn", "!"));
        legend.appendChild(el("span", "", "stopped at max_iter before converging"));
      }
      if (anyFailed) {
        legend.appendChild(el("span", "fp-legend-swatch fp-legend-fail", ""));
        legend.appendChild(el("span", "", "fit raised an error"));
      }
      legend.appendChild(el("span", "fp-legend-hint", "hover a cell for details"));
      out.push(legend);
    }
    return out;
  }

  function cellTip(cand, fold, nSplits, params, node, scores) {
    const parts = [];
    const title = el("div", "fp-tip-title");
    if (params && Object.keys(params).length) {
      for (const [name, value] of Object.entries(params)) {
        const p = el("div", "fp-tip-param");
        p.appendChild(el("span", "", name));
        p.appendChild(el("b", "", value));
        title.appendChild(p);
      }
    } else {
      title.textContent = `candidate ${cand + 1}`;
    }
    parts.push(title);
    const score = scores ? scores.folds[cand]?.[fold] : undefined;
    const status = fitStatus(node, score, Boolean(scores));
    parts.push(el("div", `fp-tip-status fp-tip-${status.kind}`, status.text));
    parts.push(tipRow("fold", `${fold + 1} of ${nSplits}`));
    if (node) parts.push(...progressRows(node));
    const liveScore = node ? node.score : null;
    if (scores && score != null) {
      parts.push(tipRow(`fold ${scores.metric}`, score.toFixed(4)));
      parts.push(tipRow(`mean ${scores.metric}`, fmtScore(scores.mean[cand])));
      parts.push(tipRow("rank", `${scores.rank[cand]} of ${scores.mean.length}`));
    } else if (liveScore != null) {
      parts.push(tipRow("fold score", liveScore.toFixed(4)));
    }
    return parts;
  }

  // Tooltip rows for a fit: its iterations, its steps (e.g. a Pipeline's) and time.
  function progressRows(node) {
    const rows = [];
    const it = iterationNode(node);
    if (it && it === node) {
      const limit = it.max_iter != null ? ` / max_iter ${it.max_iter}` : ` / ${it.total}`;
      rows.push(tipRow("iterations", `${iterations(it)}${limit}`));
    }
    if (node.children.length) {
      rows.push(el("div", "fp-tip-section", `steps (${node.done} of ${node.total})`));
      for (const step of node.children) {
        const stepIt = iterationNode(step);
        const value = stepIt
          ? `${iterations(stepIt)} iterations`
          : step.state === "done" ? fmtDuration(fitTime(step)) : step.state;
        rows.push(tipRow(step.estimator, value, notConverged(step) ? "fp-tip-warn" : ""));
      }
    }
    if (fitTime(node) != null) rows.push(tipRow("fit time", fmtDuration(fitTime(node))));
    return rows;
  }

  // ---- refit: one bar plus the parameters it was refit with -------------
  function refitSection(node, scores) {
    const box = el("div", "fp-refit");
    const line = el("div", "fp-line");
    line.appendChild(el("span", "fp-refit-title", "Refit on all data"));
    line.appendChild(el("span", "fp-spacer"));
    const meta = el("span", "fp-meta-inline");
    if (!node) meta.textContent = "after the search";
    else if (node.state === "running") meta.textContent = fitStatus(node).text.replace("Running · ", "");
    else if (node.end_ms) meta.textContent = fmtDuration(node.end_ms - node.start_ms);
    line.appendChild(meta);
    box.appendChild(line);
    const fraction = !node ? 0 : node.total ? progress(node) : node.state === "running" ? 1 : progress(node);
    box.appendChild(bar(fraction, node ? node.state : "pending", "fp-bar-refit"));

    const params = el("div", "fp-chosen");
    // An inner estimator without callback support doesn't report its
    // parameters, so fall back to the best candidate of the search.
    const candidates = model.get("candidates") || [];
    let chosen = node && node.params && Object.keys(node.params).length ? node.params : null;
    if (!chosen && node && scores && candidates[scores.best_index]) chosen = candidates[scores.best_index];
    if (chosen) {
      for (const [name, value] of Object.entries(chosen)) {
        const chip = el("span", "fp-chip");
        chip.appendChild(el("span", "fp-chip-name", name));
        chip.appendChild(el("span", "fp-chip-value", value));
        params.appendChild(chip);
      }
      if (scores && scores.best_index >= 0) {
        params.appendChild(el("span", "fp-chosen-score", `mean ${scores.metric} ${fmtScore(scores.mean[scores.best_index])}`));
      }
    } else {
      params.appendChild(el("span", "fp-unknown", node ? "" : "best parameters appear here"));
    }
    box.appendChild(params);
    if (node) attachTip(box, "refit", () => [
      el("div", "fp-tip-title", "Refit with the best parameters"),
      el("div", `fp-tip-status fp-tip-${fitStatus(node).kind}`, fitStatus(node).text),
      ...progressRows(node),
    ]);
    return box;
  }

  // ---- anything that is not a search: nested bars -----------------------
  function treeRows(node, depth, out) {
    const row = el("div", "fp-row");
    row.style.setProperty("--fp-depth", depth);
    const label = el("div", "fp-label");
    label.appendChild(el("span", "", `${node.estimator} · ${node.task}`));
    row.appendChild(label);
    row.appendChild(bar(progress(node), node.state, "fp-bar-row"));
    const right = el("span", "fp-meta-inline");
    right.textContent = fitReadout(node);
    if (countsIterations(node) && notConverged(node)) row.classList.add("fp-maxed");
    row.appendChild(right);
    attachTip(row, `row-${keyOf(node.path)}`, () => [
      el("div", "fp-tip-title", `${node.estimator} · ${node.task}`),
      el("div", `fp-tip-status fp-tip-${fitStatus(node).kind}`, fitStatus(node).text),
      ...(node.end_ms ? [tipRow("time", fmtDuration(node.end_ms - node.start_ms))] : []),
    ]);
    out.appendChild(row);
    for (const child of node.children) treeRows(child, depth + 1, out);
  }

  function applyColor() {
    const color = model.get("color");
    if (color) root.style.setProperty("--fp-accent", color);
    else root.style.removeProperty("--fp-accent");
  }

  function draw() {
    tipMakers.clear();
    const tree = buildTree(model.get("tasks") || []);
    const search = tree && tree.children.find((c) => c.task === "search" && c.n_splits);
    root.replaceChildren(header(tree, search));
    if (tree && search) {
      root.append(...searchGrid(search));
      const refit = tree.children.find((c) => (c.source_task || c.task) === "refit-with-best-params");
      if (refit || tree.total > 1) root.appendChild(refitSection(refit, model.get("scores")));
    } else if (tree) {
      const rows = el("div", "fp-rows");
      for (const child of tree.children) treeRows(child, 0, rows);
      if (rows.childNodes.length) root.appendChild(rows);
    }
    root.appendChild(tip);
    if (hovered && tipMakers.has(hovered.id)) showTip(hovered.ev, tipMakers.get(hovered.id)());
    else hideTip();
  }

  // Keep the elapsed clock ticking between (throttled) updates from Python.
  const timer = setInterval(() => {
    if (model.get("status") !== "running" || !elapsedEl) return;
    const tree = buildTree(model.get("tasks") || []);
    elapsedEl.textContent = elapsedText(tree ? overallProgress(tree) : 0);
  }, 250);

  model.on("change:tasks", draw);
  model.on("change:scores", draw);
  model.on("change:candidates", draw);
  model.on("change:status", draw);
  model.on("change:color", applyColor);
  applyColor();
  draw();
  return () => clearInterval(timer);
}

export default { render };
