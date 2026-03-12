function hexToRgba(hex, alpha) {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r},${g},${b},${alpha})`;
}

function hasOverlap(entities, start, end, excludeIndex) {
    return entities.some(
        (ent, i) => i !== excludeIndex && start < ent.end && end > ent.start
    );
}

/**
 * Split text into word-level tokens, preserving character offsets.
 * Returns array of { text, start, end, isSpace } objects.
 */
function tokenize(text, baseOffset) {
    const tokens = [];
    const re = /(\S+|\s+)/g;
    let m;
    while ((m = re.exec(text)) !== null) {
        tokens.push({
            text: m[0],
            start: baseOffset + m.index,
            end: baseOffset + m.index + m[0].length,
            isSpace: /^\s+$/.test(m[0]),
        });
    }
    return tokens;
}

function buildSegments(text, entities) {
    if (entities.length === 0) {
        return [{ start: 0, end: text.length, entityIndices: [] }];
    }
    const sorted = entities
        .map((e, i) => ({ ...e, _idx: i }))
        .sort((a, b) => a.start - b.start);
    const segments = [];
    let pos = 0;
    for (const ent of sorted) {
        if (ent.start > pos) {
            segments.push({ start: pos, end: ent.start, entityIndices: [] });
        }
        segments.push({
            start: ent.start,
            end: ent.end,
            entityIndices: [ent._idx],
        });
        pos = ent.end;
    }
    if (pos < text.length) {
        segments.push({ start: pos, end: text.length, entityIndices: [] });
    }
    return segments;
}

function buildOverlapSegments(text, entities) {
    if (entities.length === 0) {
        return [{ start: 0, end: text.length, entityIndices: [] }];
    }
    const points = new Set([0, text.length]);
    for (const ent of entities) {
        points.add(ent.start);
        points.add(ent.end);
    }
    const sorted = [...points].sort((a, b) => a - b);
    const segments = [];
    for (let i = 0; i < sorted.length - 1; i++) {
        const s = sorted[i];
        const e = sorted[i + 1];
        const covering = [];
        entities.forEach((ent, idx) => {
            if (ent.start <= s && ent.end >= e) {
                covering.push(idx);
            }
        });
        segments.push({ start: s, end: e, entityIndices: covering });
    }
    return segments;
}

/**
 * Render a plain-text segment. In token mode, each word is its own span
 * so we can detect mousedown/mouseup targets without any selection API.
 * In character mode, one span covers the whole segment.
 */
function renderPlainSegment(text, seg, selectionMode, textArea) {
    const content = text.slice(seg.start, seg.end);
    if (selectionMode === "token") {
        const tokens = tokenize(content, seg.start);
        for (const tok of tokens) {
            const span = document.createElement("span");
            span.className = tok.isSpace ? "th-space" : "th-word";
            span.textContent = tok.text;
            span.dataset.start = tok.start;
            span.dataset.end = tok.end;
            textArea.appendChild(span);
        }
    } else {
        // Character mode: one span per character for precise selection
        for (let i = 0; i < content.length; i++) {
            const span = document.createElement("span");
            span.className = "th-char";
            span.textContent = content[i];
            span.dataset.start = seg.start + i;
            span.dataset.end = seg.start + i + 1;
            textArea.appendChild(span);
        }
    }
}

function renderWidget(model, el) {
    const text = model.get("text");
    const entities = model.get("entities") || [];
    const colorMap = model.get("color_map") || {};
    const labels = model.get("labels") || [];
    const editable = model.get("editable");
    const allowOverlap = model.get("allow_overlap");
    const activeLabel = model.get("active_label");
    const selectedEntity = model.get("selected_entity");
    const selectionMode = model.get("selection_mode");

    el.innerHTML = "";

    const container = document.createElement("div");
    container.className = "th-container";

    // Toolbar (only when editable)
    if (editable) {
        const toolbar = document.createElement("div");
        toolbar.className = "th-toolbar";

        const toolbarLabel = document.createElement("span");
        toolbarLabel.className = "th-toolbar-label";
        toolbarLabel.textContent = "Labels:";
        toolbar.appendChild(toolbarLabel);

        for (const label of labels) {
            const btn = document.createElement("button");
            btn.className = "th-label-btn";
            if (label === activeLabel) btn.classList.add("th-label-active");

            const color = colorMap[label] || "#999";
            btn.style.setProperty("--th-label-color", color);
            btn.style.setProperty(
                "--th-label-color-bg",
                hexToRgba(color, 0.15)
            );

            const dot = document.createElement("span");
            dot.className = "th-label-dot";
            dot.style.background = color;
            btn.appendChild(dot);

            btn.appendChild(document.createTextNode(label));

            btn.addEventListener("click", (e) => {
                e.stopPropagation();
                const current = model.get("active_label");
                model.set("active_label", current === label ? "" : label);
                model.save_changes();
            });

            toolbar.appendChild(btn);
        }

        container.appendChild(toolbar);
    }

    // Text area
    const textArea = document.createElement("div");
    textArea.className = "th-text-area";

    // Set drag highlight color to match active label
    if (activeLabel && colorMap[activeLabel]) {
        textArea.style.setProperty(
            "--th-drag-bg",
            hexToRgba(colorMap[activeLabel], 0.25)
        );
    }

    const segments = allowOverlap
        ? buildOverlapSegments(text, entities)
        : buildSegments(text, entities);

    for (const seg of segments) {
        const content = text.slice(seg.start, seg.end);
        if (content.length === 0) continue;

        if (seg.entityIndices.length === 0) {
            renderPlainSegment(text, seg, selectionMode, textArea);
        } else if (seg.entityIndices.length === 1 && !allowOverlap) {
            const entIdx = seg.entityIndices[0];
            const ent = entities[entIdx];
            const color = colorMap[ent.label] || "#999";

            const span = document.createElement("span");
            span.className = "th-entity";
            if (entIdx === selectedEntity)
                span.classList.add("th-entity-selected");
            span.style.backgroundColor = hexToRgba(color, 0.25);
            span.dataset.start = seg.start;
            span.dataset.end = seg.end;
            span.dataset.entityIndex = entIdx;

            span.appendChild(document.createTextNode(content));

            if (seg.end === ent.end) {
                const tag = document.createElement("span");
                tag.className = "th-entity-tag";
                tag.style.backgroundColor = color;
                tag.textContent = ent.label;
                span.appendChild(tag);

                if (editable) {
                    const del = document.createElement("button");
                    del.className = "th-delete-btn";
                    del.textContent = "\u00d7";
                    del.addEventListener("click", (e) => {
                        e.stopPropagation();
                        const ents = [...model.get("entities")];
                        ents.splice(entIdx, 1);
                        model.set("entities", ents);
                        model.set("selected_entity", -1);
                        model.save_changes();
                    });
                    span.appendChild(del);
                }
            }

            span.addEventListener("click", (e) => {
                e.stopPropagation();
                const current = model.get("selected_entity");
                model.set(
                    "selected_entity",
                    current === entIdx ? -1 : entIdx
                );
                model.save_changes();
            });

            textArea.appendChild(span);
        } else {
            // Overlap mode: underlines only
            const span = document.createElement("span");
            span.className = "th-entity-underline";
            span.dataset.start = seg.start;
            span.dataset.end = seg.end;

            const shadows = seg.entityIndices.map((idx, i) => {
                const c = colorMap[entities[idx].label] || "#999";
                const offset = 2 + i * 4;
                return `inset 0 -${offset}px 0 0 ${c}`;
            });
            span.style.boxShadow = shadows.join(", ");
            span.style.paddingBottom = seg.entityIndices.length * 4 + "px";

            span.appendChild(document.createTextNode(content));

            for (const entIdx of seg.entityIndices) {
                const ent = entities[entIdx];
                if (seg.end === ent.end) {
                    const tag = document.createElement("span");
                    tag.className = "th-entity-tag";
                    tag.style.backgroundColor =
                        colorMap[ent.label] || "#999";
                    tag.textContent = ent.label;
                    span.appendChild(tag);
                }
            }

            span.addEventListener("click", (e) => {
                e.stopPropagation();
                const current = model.get("selected_entity");
                const entIdx = seg.entityIndices[0];
                model.set(
                    "selected_entity",
                    current === entIdx ? -1 : entIdx
                );
                model.save_changes();
            });

            textArea.appendChild(span);
        }
    }

    // ── Drag-to-select: purely DOM-based, no selection API needed ──
    if (editable) {
        let anchorSpan = null;

        // Find the nearest span with data-start from an event target
        function findWordSpan(target) {
            if (!target || target === textArea) return null;
            const span = target.closest("[data-start]");
            // Make sure it's inside our textArea
            if (span && textArea.contains(span)) return span;
            return null;
        }

        // Collect all word/segment/entity spans in document order
        function getAllSpans() {
            return Array.from(
                textArea.querySelectorAll("[data-start]")
            );
        }

        // Highlight spans between anchor and current
        function updateDragHighlight(fromSpan, toSpan) {
            const allSpans = getAllSpans();
            const fromIdx = allSpans.indexOf(fromSpan);
            const toIdx = allSpans.indexOf(toSpan);
            if (fromIdx === -1 || toIdx === -1) return;
            const lo = Math.min(fromIdx, toIdx);
            const hi = Math.max(fromIdx, toIdx);
            for (let i = 0; i < allSpans.length; i++) {
                allSpans[i].classList.toggle("th-drag-highlight", i >= lo && i <= hi);
            }
        }

        function clearDragHighlight() {
            const allSpans = getAllSpans();
            for (const s of allSpans) {
                s.classList.remove("th-drag-highlight");
            }
        }

        textArea.addEventListener("mousedown", (e) => {
            anchorSpan = findWordSpan(e.target);
            if (anchorSpan) {
                clearDragHighlight();
                anchorSpan.classList.add("th-drag-highlight");
            }
        });

        textArea.addEventListener("mousemove", (e) => {
            if (!anchorSpan || !(e.buttons & 1)) {
                // Mouse button released outside, or no drag
                if (anchorSpan) {
                    clearDragHighlight();
                    anchorSpan = null;
                }
                return;
            }
            const hoverSpan = findWordSpan(e.target);
            if (hoverSpan) {
                updateDragHighlight(anchorSpan, hoverSpan);
            }
        });

        textArea.addEventListener("mouseup", (e) => {
            clearDragHighlight();

            const label = model.get("active_label");
            if (!label || !anchorSpan) {
                anchorSpan = null;
                return;
            }

            const focusSpan = findWordSpan(e.target);
            if (!focusSpan) {
                anchorSpan = null;
                return;
            }

            // Compute range from the two spans
            const s1 = parseInt(anchorSpan.dataset.start);
            const e1 = parseInt(anchorSpan.dataset.end);
            const s2 = parseInt(focusSpan.dataset.start);
            const e2 = parseInt(focusSpan.dataset.end);

            let start = Math.min(s1, s2);
            let end = Math.max(e1, e2);

            anchorSpan = null;

            const currentText = model.get("text");

            // Trim leading/trailing whitespace from the selection
            while (start < end && /\s/.test(currentText[start])) start++;
            while (end > start && /\s/.test(currentText[end - 1])) end--;

            if (start >= end) return;

            // Check overlap
            const currentEntities = model.get("entities") || [];
            if (
                !model.get("allow_overlap") &&
                hasOverlap(currentEntities, start, end, -1)
            ) {
                return;
            }

            const newEntity = {
                text: currentText.slice(start, end),
                label: label,
                start: start,
                end: end,
            };

            model.set("entities", [...currentEntities, newEntity]);
            model.save_changes();
        });
    }

    // Click outside entities deselects
    container.addEventListener("click", () => {
        if (model.get("selected_entity") !== -1) {
            model.set("selected_entity", -1);
            model.save_changes();
        }
    });

    // Keyboard: Delete/Backspace removes selected entity
    container.setAttribute("tabindex", "0");
    container.addEventListener("keydown", (e) => {
        if (!editable) return;
        const idx = model.get("selected_entity");
        if (idx >= 0 && (e.key === "Delete" || e.key === "Backspace")) {
            e.preventDefault();
            const ents = [...model.get("entities")];
            ents.splice(idx, 1);
            model.set("entities", ents);
            model.set("selected_entity", -1);
            model.save_changes();
        }
    });

    container.appendChild(textArea);

    // Status bar
    if (editable) {
        const status = document.createElement("div");
        status.className = "th-status";
        if (!activeLabel) {
            status.textContent =
                "Select a label above, then highlight text to add entities.";
        } else {
            status.textContent = `Active label: ${activeLabel}. Select text to annotate.`;
        }
        container.appendChild(status);
    }

    el.appendChild(container);
}

export default {
    render({ model, el }) {
        const rerender = () => renderWidget(model, el);
        rerender();
        model.on("change:text", rerender);
        model.on("change:entities", rerender);
        model.on("change:labels", rerender);
        model.on("change:color_map", rerender);
        model.on("change:allow_overlap", rerender);
        model.on("change:selection_mode", rerender);
        model.on("change:editable", rerender);
        model.on("change:active_label", rerender);
        model.on("change:selected_entity", rerender);
    },
};
