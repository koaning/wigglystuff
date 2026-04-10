// Simple Python syntax highlighter for code blocks in docstrings.
// No dependencies — just regex-based token coloring.
const PY_KEYWORDS = new Set([
  "False", "None", "True", "and", "as", "assert", "async", "await",
  "break", "class", "continue", "def", "del", "elif", "else", "except",
  "finally", "for", "from", "global", "if", "import", "in", "is",
  "lambda", "nonlocal", "not", "or", "pass", "raise", "return", "try",
  "while", "with", "yield",
]);

const PY_BUILTINS = new Set([
  "print", "len", "range", "int", "str", "float", "list", "dict", "set",
  "tuple", "bool", "type", "isinstance", "super", "property", "classmethod",
  "staticmethod", "enumerate", "zip", "map", "filter", "sorted", "reversed",
  "open", "hasattr", "getattr", "setattr", "repr", "iter", "next", "self",
]);

function highlightPython(code) {
  // Tokenize with a single regex, then wrap matches in spans.
  // Order matters: strings before comments before keywords.
  const pattern = /("""[\s\S]*?"""|'''[\s\S]*?'''|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')|(#[^\n]*)|\b(\d+(?:\.\d+)?)\b|(\b[A-Za-z_]\w*\b)/g;
  let result = "";
  let last = 0;
  let match;
  while ((match = pattern.exec(code)) !== null) {
    // Append text between matches (escaped)
    result += escapeHtml(code.slice(last, match.index));
    last = match.index + match[0].length;

    if (match[1]) {
      // String
      result += '<span class="ad-hl-str">' + escapeHtml(match[1]) + "</span>";
    } else if (match[2]) {
      // Comment
      result += '<span class="ad-hl-comment">' + escapeHtml(match[2]) + "</span>";
    } else if (match[3]) {
      // Number
      result += '<span class="ad-hl-num">' + escapeHtml(match[3]) + "</span>";
    } else if (match[4]) {
      // Identifier — check if keyword or builtin
      if (PY_KEYWORDS.has(match[4])) {
        result += '<span class="ad-hl-kw">' + escapeHtml(match[4]) + "</span>";
      } else if (PY_BUILTINS.has(match[4])) {
        result += '<span class="ad-hl-builtin">' + escapeHtml(match[4]) + "</span>";
      } else {
        result += escapeHtml(match[4]);
      }
    }
  }
  result += escapeHtml(code.slice(last));
  return result;
}

function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function buildParamTable(params) {
  if (!params || params.length === 0) return null;

  const table = document.createElement("table");
  table.className = "ad-param-table";

  const thead = document.createElement("thead");
  const headerRow = document.createElement("tr");
  for (const col of ["Name", "Type", "Default"]) {
    const th = document.createElement("th");
    th.textContent = col;
    headerRow.appendChild(th);
  }
  thead.appendChild(headerRow);
  table.appendChild(thead);

  const tbody = document.createElement("tbody");
  for (const p of params) {
    const tr = document.createElement("tr");
    const tdName = document.createElement("td");
    const nameCode = document.createElement("code");
    nameCode.textContent = p.name;
    tdName.appendChild(nameCode);
    tr.appendChild(tdName);

    const tdType = document.createElement("td");
    if (p.annotation) {
      const typeCode = document.createElement("code");
      typeCode.textContent = p.annotation;
      tdType.appendChild(typeCode);
    }
    tr.appendChild(tdType);

    const tdDefault = document.createElement("td");
    if (p.default) {
      const defCode = document.createElement("code");
      defCode.textContent = p.default;
      tdDefault.appendChild(defCode);
    }
    tr.appendChild(tdDefault);

    tbody.appendChild(tr);
  }
  table.appendChild(tbody);
  return table;
}

// Parse docstring text into a mix of plain text and fenced code blocks.
// Returns an array of {type: "text"|"code", content, lang?} segments.
function parseDocstring(text) {
  if (!text) return [];
  const segments = [];
  // Match fenced code blocks with optional leading whitespace
  const fencePattern = /^[ \t]*```(\w*)\s*\n([\s\S]*?)^[ \t]*```\s*$/gm;
  let last = 0;
  let match;
  while ((match = fencePattern.exec(text)) !== null) {
    if (match.index > last) {
      const before = text.slice(last, match.index).replace(/\n+$/, "");
      if (before) segments.push({ type: "text", content: before });
    }
    // Dedent the code content: strip common leading whitespace
    let code = match[2];
    const lines = code.split("\n");
    const indents = lines.filter(l => l.trim()).map(l => l.match(/^(\s*)/)[1].length);
    const minIndent = indents.length > 0 ? Math.min(...indents) : 0;
    if (minIndent > 0) {
      code = lines.map(l => l.slice(minIndent)).join("\n");
    }
    // Trim trailing whitespace from code
    code = code.replace(/\s+$/, "");
    segments.push({ type: "code", content: code, lang: match[1] || "python" });
    last = match.index + match[0].length;
  }
  if (last < text.length) {
    const after = text.slice(last).replace(/^\n+/, "");
    if (after) segments.push({ type: "text", content: after });
  }
  return segments;
}

// Render inline markdown: **bold** and `code`
function renderInlineMarkdown(text, parent) {
  const pattern = /(\*\*(.+?)\*\*)|(`([^`]+)`)/g;
  let last = 0;
  let match;
  while ((match = pattern.exec(text)) !== null) {
    if (match.index > last) {
      parent.appendChild(document.createTextNode(text.slice(last, match.index)));
    }
    if (match[1]) {
      const bold = document.createElement("strong");
      bold.textContent = match[2];
      parent.appendChild(bold);
    } else if (match[3]) {
      const code = document.createElement("code");
      code.className = "ad-inline-code";
      code.textContent = match[4];
      parent.appendChild(code);
    }
    last = match.index + match[0].length;
  }
  if (last < text.length) {
    parent.appendChild(document.createTextNode(text.slice(last)));
  }
}

function buildDocstring(text) {
  if (!text) return null;
  const segments = parseDocstring(text);
  const wrapper = document.createElement("div");
  wrapper.className = "ad-docstring";
  for (const seg of segments) {
    if (seg.type === "text") {
      const span = document.createElement("span");
      renderInlineMarkdown(seg.content, span);
      wrapper.appendChild(span);
    } else {
      const codeWrapper = document.createElement("div");
      codeWrapper.className = "ad-code-wrapper";

      const pre = document.createElement("pre");
      pre.className = "ad-code-block";
      const code = document.createElement("code");
      if (seg.lang === "python" || seg.lang === "py" || seg.lang === "") {
        code.innerHTML = highlightPython(seg.content);
      } else {
        code.textContent = seg.content;
      }
      pre.appendChild(code);

      const copyBtn = document.createElement("button");
      copyBtn.className = "ad-copy-btn";
      copyBtn.textContent = "Copy";
      copyBtn.addEventListener("click", () => {
        navigator.clipboard.writeText(seg.content).then(() => {
          copyBtn.textContent = "Copied!";
          setTimeout(() => { copyBtn.textContent = "Copy"; }, 1500);
        });
      });

      codeWrapper.appendChild(pre);
      codeWrapper.appendChild(copyBtn);
      wrapper.appendChild(codeWrapper);
    }
  }
  return wrapper;
}

function buildMethodBlock(method) {
  const block = document.createElement("div");
  block.className = "ad-method-block";

  const header = document.createElement("div");
  header.className = "ad-method-header";

  const toggle = document.createElement("span");
  toggle.className = "ad-toggle";
  toggle.textContent = "\u25B6";
  header.appendChild(toggle);

  const heading = document.createElement("span");
  heading.className = "ad-method-heading";
  heading.textContent = method.name + (method.signature || "()");
  header.appendChild(heading);

  if (method.decorator) {
    const badge = document.createElement("span");
    badge.className = "ad-badge ad-badge-" + method.decorator;
    badge.textContent = method.decorator;
    header.appendChild(badge);
  }

  block.appendChild(header);

  // Collapsible body
  const body = document.createElement("div");
  body.className = "ad-method-body collapsed";

  const docEl = buildDocstring(method.docstring);
  if (docEl) body.appendChild(docEl);

  const tableEl = buildParamTable(method.parameters);
  if (tableEl) body.appendChild(tableEl);

  block.appendChild(body);

  header.addEventListener("click", () => {
    body.classList.toggle("collapsed");
    toggle.classList.toggle("expanded");
  });

  return block;
}

function buildPropertyBlock(prop) {
  const block = document.createElement("div");
  block.className = "ad-method-block";

  const header = document.createElement("div");
  header.className = "ad-method-header";

  const toggle = document.createElement("span");
  toggle.className = "ad-toggle";
  toggle.textContent = "\u25B6";
  header.appendChild(toggle);

  const heading = document.createElement("span");
  heading.className = "ad-property-heading";
  heading.textContent = prop.name;
  header.appendChild(heading);

  const badge = document.createElement("span");
  badge.className = "ad-badge ad-badge-property";
  badge.textContent = "property";
  header.appendChild(badge);

  block.appendChild(header);

  const body = document.createElement("div");
  body.className = "ad-method-body collapsed";

  const docEl = buildDocstring(prop.docstring);
  if (docEl) body.appendChild(docEl);

  block.appendChild(body);

  header.addEventListener("click", () => {
    body.classList.toggle("collapsed");
    toggle.classList.toggle("expanded");
  });

  return block;
}

function render({ model, el }) {
  el.classList.add("api-doc-root");

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
    const doc = model.get("doc");
    const width = model.get("width") || 700;
    container.style.maxWidth = width + "px";

    if (!doc || !doc.name) return;

    // Title: module.Name
    const title = document.createElement("h2");
    title.className = "ad-title";
    if (doc.module) {
      const moduleSpan = document.createElement("span");
      moduleSpan.className = "ad-module";
      moduleSpan.textContent = doc.module + ".";
      title.appendChild(moduleSpan);
    }
    const nameText = document.createTextNode(doc.name);
    title.appendChild(nameText);

    // Kind badge
    const kindBadge = document.createElement("span");
    kindBadge.className = "ad-kind ad-kind-" + doc.kind;
    kindBadge.textContent = doc.kind;
    title.appendChild(kindBadge);

    container.appendChild(title);

    // Bases line (class only)
    if (doc.bases && doc.bases.length > 0) {
      const basesDiv = document.createElement("div");
      basesDiv.className = "ad-bases";
      basesDiv.appendChild(document.createTextNode("Bases: "));
      for (let i = 0; i < doc.bases.length; i++) {
        if (i > 0) basesDiv.appendChild(document.createTextNode(", "));
        const code = document.createElement("code");
        code.textContent = doc.bases[i];
        basesDiv.appendChild(code);
      }
      container.appendChild(basesDiv);
    }

    // Constructor / function signature
    if (doc.signature) {
      const sigDiv = document.createElement("div");
      sigDiv.className = "ad-signature";
      sigDiv.innerHTML = highlightPython(doc.name + doc.signature);
      container.appendChild(sigDiv);
    }

    // Parameter table
    const paramTable = buildParamTable(doc.parameters);
    if (paramTable) container.appendChild(paramTable);

    // Docstring
    const docEl = buildDocstring(doc.docstring);
    if (docEl) container.appendChild(docEl);

    // Methods section (class only)
    if (doc.methods && doc.methods.length > 0) {
      const methodsHeading = document.createElement("h3");
      methodsHeading.className = "ad-section-heading";
      methodsHeading.textContent = "Methods";
      container.appendChild(methodsHeading);

      for (const method of doc.methods) {
        container.appendChild(buildMethodBlock(method));
      }
    }

    // Properties section (class only)
    if (doc.properties && doc.properties.length > 0) {
      const propsHeading = document.createElement("h3");
      propsHeading.className = "ad-section-heading";
      propsHeading.textContent = "Properties";
      container.appendChild(propsHeading);

      for (const prop of doc.properties) {
        container.appendChild(buildPropertyBlock(prop));
      }
    }
  }

  draw();
  model.on("change:doc", draw);
  model.on("change:width", draw);

  return () => {
    observer.disconnect();
  };
}

export default { render };
