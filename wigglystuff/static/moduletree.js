function formatCount(n) {
  if (n >= 1_000_000_000) return (n / 1_000_000_000).toFixed(1) + "B";
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + "M";
  if (n >= 1_000) return (n / 1_000).toFixed(1) + "K";
  return String(n);
}

function densityColor(paramCount, rootTotal) {
  if (rootTotal === 0) return "hsl(210, 10%, 70%)";
  const ratio = paramCount / rootTotal;
  const hue = 210 * (1 - ratio);
  const saturation = 30 + 50 * ratio;
  const lightness = 60 - 15 * ratio;
  return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
}

function formatShape(shape) {
  return "[" + shape.join(", ") + "]";
}

function buildNode(node, depth, initialExpandDepth, rootTotal) {
  const el = document.createElement("div");
  el.className = "mt-node";

  const hasChildren = node.children && node.children.length > 0;
  const hasParams = node.params && node.params.length > 0;
  const isLeaf = !hasChildren && !hasParams;
  const startExpanded = depth < initialExpandDepth;

  // Header
  const header = document.createElement("div");
  header.className = "mt-header";

  // Toggle icon
  const toggle = document.createElement("span");
  toggle.className = "mt-toggle" + (isLeaf ? " leaf" : "") + (startExpanded ? " expanded" : "");
  toggle.textContent = "\u25B6"; // right triangle
  header.appendChild(toggle);

  // Module name
  const name = document.createElement("span");
  name.className = "mt-name";
  name.textContent = node.name || node.type;
  header.appendChild(name);

  // Type badge (only if name is present, otherwise type is already shown as name)
  if (node.name) {
    const type = document.createElement("span");
    type.className = "mt-type";
    type.textContent = node.type;
    header.appendChild(type);
  }

  // Param count
  if (node.total_param_count > 0) {
    const count = document.createElement("span");
    count.className = "mt-count";
    count.textContent = formatCount(node.total_param_count) + " params";
    header.appendChild(count);

    // Density dot
    const dot = document.createElement("span");
    dot.className = "mt-density";
    dot.style.background = densityColor(node.total_param_count, rootTotal);
    header.appendChild(dot);
  }

  el.appendChild(header);

  // Body (collapsible)
  if (!isLeaf) {
    const body = document.createElement("div");
    body.className = "mt-body" + (startExpanded ? "" : " collapsed");

    // Parameters
    if (hasParams) {
      const paramsDiv = document.createElement("div");
      paramsDiv.className = "mt-params";
      for (const p of node.params) {
        const row = document.createElement("div");
        row.className = "mt-param";

        const pname = document.createElement("span");
        pname.className = "mt-param-name";
        pname.textContent = p.name;
        row.appendChild(pname);

        const shape = document.createElement("span");
        shape.className = "mt-param-shape";
        shape.textContent = formatShape(p.shape);
        row.appendChild(shape);

        const numel = document.createElement("span");
        numel.className = "mt-param-numel";
        numel.textContent = p.numel.toLocaleString();
        row.appendChild(numel);

        const badge = document.createElement("span");
        if (p.is_buffer) {
          badge.className = "mt-param-badge buffer";
          badge.textContent = "buffer";
        } else if (p.trainable) {
          badge.className = "mt-param-badge trainable";
          badge.textContent = "train";
        } else {
          badge.className = "mt-param-badge frozen";
          badge.textContent = "frozen";
        }
        row.appendChild(badge);

        paramsDiv.appendChild(row);
      }
      body.appendChild(paramsDiv);
    }

    // Children
    if (hasChildren) {
      for (const child of node.children) {
        body.appendChild(buildNode(child, depth + 1, initialExpandDepth, rootTotal));
      }
    }

    el.appendChild(body);

    // Toggle click
    header.addEventListener("click", () => {
      const isExpanded = !body.classList.contains("collapsed");
      body.classList.toggle("collapsed");
      toggle.classList.toggle("expanded");
    });
  }

  return el;
}

function render({ model, el }) {
  el.classList.add("module-tree-root");

  // Theme detection
  function detectTheme() {
    const html = document.documentElement;
    const body = document.body;
    const isDark =
      html.classList.contains("dark") ||
      body.classList.contains("dark") ||
      html.getAttribute("data-theme") === "dark" ||
      body.getAttribute("data-theme") === "dark" ||
      html.getAttribute("data-color-mode") === "dark" ||
      body.getAttribute("data-color-mode") === "dark";
    if (isDark) {
      el.classList.add("dark-mode");
    } else {
      el.classList.remove("dark-mode");
    }
  }
  detectTheme();

  const observer = new MutationObserver(detectTheme);
  observer.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ["class", "data-theme", "data-color-mode"],
  });
  observer.observe(document.body, {
    attributes: true,
    attributeFilter: ["class", "data-theme", "data-color-mode"],
  });

  const container = document.createElement("div");
  el.appendChild(container);

  function draw() {
    container.innerHTML = "";
    const tree = model.get("tree");
    const initialDepth = model.get("initial_expand_depth") || 1;

    if (!tree || !tree.type) return;

    // Summary bar
    const summary = document.createElement("div");
    summary.className = "mt-summary";

    const totalSpan = document.createElement("span");
    totalSpan.innerHTML = `Total: <span class="mt-summary-value">${formatCount(tree.total_param_count)}</span>`;
    summary.appendChild(totalSpan);

    const trainSpan = document.createElement("span");
    trainSpan.innerHTML = `Trainable: <span class="mt-summary-value">${formatCount(tree.total_trainable_count)}</span>`;
    summary.appendChild(trainSpan);

    const frozenCount = tree.total_param_count - tree.total_trainable_count;
    if (frozenCount > 0) {
      const frozenSpan = document.createElement("span");
      frozenSpan.innerHTML = `Frozen: <span class="mt-summary-value">${formatCount(frozenCount)}</span>`;
      summary.appendChild(frozenSpan);
    }

    container.appendChild(summary);
    container.appendChild(buildNode(tree, 0, initialDepth, tree.total_param_count));
  }

  draw();
  model.on("change:tree", draw);
  model.on("change:initial_expand_depth", draw);

  return () => {
    observer.disconnect();
  };
}

export default { render };
