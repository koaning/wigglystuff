import * as d3 from "../d3.min.js";

const CYPHER_KEYWORDS = [
    "MATCH", "OPTIONAL MATCH", "WHERE", "RETURN", "WITH", "ORDER BY",
    "LIMIT", "SKIP", "CREATE", "MERGE", "DELETE", "DETACH DELETE",
    "SET", "REMOVE", "UNWIND", "CALL", "YIELD", "AS", "AND", "OR",
    "NOT", "IN", "IS NULL", "IS NOT NULL", "DISTINCT", "COUNT", "COLLECT",
    "EXISTS", "CASE", "WHEN", "THEN", "ELSE", "END",
];

function render({ model, el }) {
    let requestCounter = 0;

    // --- DOM structure ---
    const container = document.createElement("div");
    container.classList.add("neo4j-widget");
    el.appendChild(container);

    // Query bar
    const queryBar = document.createElement("div");
    queryBar.classList.add("neo4j-query-bar");
    container.appendChild(queryBar);

    const inputWrapper = document.createElement("div");
    inputWrapper.classList.add("neo4j-input-wrapper");
    queryBar.appendChild(inputWrapper);

    const textarea = document.createElement("textarea");
    textarea.classList.add("neo4j-query-input");
    textarea.placeholder = "Enter Cypher query... (Ctrl+Enter to run)";
    textarea.rows = 3;
    inputWrapper.appendChild(textarea);

    const dropdown = document.createElement("div");
    dropdown.classList.add("neo4j-autocomplete-dropdown");
    dropdown.style.display = "none";
    inputWrapper.appendChild(dropdown);

    const runBtn = document.createElement("button");
    runBtn.classList.add("neo4j-run-btn");
    runBtn.textContent = "Run";
    queryBar.appendChild(runBtn);

    // Error bar
    const errorBar = document.createElement("div");
    errorBar.classList.add("neo4j-error-bar");
    errorBar.style.display = "none";
    container.appendChild(errorBar);

    // Color scale for node labels
    const colorScale = d3.scaleOrdinal(d3.schemeTableau10);

    // Schema bar
    const schemaBar = document.createElement("div");
    schemaBar.classList.add("neo4j-schema-bar");
    container.appendChild(schemaBar);

    function renderSchema() {
        const schema = model.get("schema") || {};
        const labels = schema.labels || [];
        const relTypes = schema.relationship_types || [];
        schemaBar.innerHTML = "";

        if (labels.length === 0 && relTypes.length === 0) {
            schemaBar.style.display = "none";
            return;
        }
        schemaBar.style.display = "flex";

        labels.forEach(label => {
            const chip = document.createElement("span");
            chip.classList.add("neo4j-schema-chip", "neo4j-schema-label");
            chip.style.backgroundColor = colorScale(label);
            chip.textContent = label;
            chip.addEventListener("click", () => {
                textarea.value = `MATCH (n:${label}) RETURN n LIMIT 25`;
                textarea.focus();
            });
            schemaBar.appendChild(chip);
        });

        relTypes.forEach(type => {
            const chip = document.createElement("span");
            chip.classList.add("neo4j-schema-chip", "neo4j-schema-rel");
            chip.textContent = type;
            chip.addEventListener("click", () => {
                textarea.value = `MATCH (a)-[r:${type}]->(b) RETURN a, r, b LIMIT 25`;
                textarea.focus();
            });
            schemaBar.appendChild(chip);
        });
    }

    renderSchema();

    // SVG graph
    const width = model.get("width");
    const height = model.get("height");
    const svgEl = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svgEl.setAttribute("width", width);
    svgEl.setAttribute("height", height);
    svgEl.classList.add("neo4j-graph");
    container.appendChild(svgEl);

    const svg = d3.select(svgEl);

    // Arrowhead marker
    svg.append("defs").append("marker")
        .attr("id", "neo4j-arrowhead")
        .attr("viewBox", "-0 -5 10 10")
        .attr("refX", 20)
        .attr("refY", 0)
        .attr("orient", "auto")
        .attr("markerWidth", 6)
        .attr("markerHeight", 6)
        .append("path")
        .attr("d", "M0,-5L10,0L0,5")
        .attr("class", "neo4j-arrow");

    // Zoom container wraps all graph elements
    const zoomGroup = svg.append("g").attr("class", "neo4j-zoom-group");

    svg.call(d3.zoom()
        .scaleExtent([0.1, 5])
        .on("zoom", (event) => {
            zoomGroup.attr("transform", event.transform);
        }));

    const linkGroup = zoomGroup.append("g").attr("class", "neo4j-links");
    const nodeGroup = zoomGroup.append("g").attr("class", "neo4j-nodes");

    // Tooltip
    const tooltip = document.createElement("div");
    tooltip.classList.add("neo4j-tooltip");
    tooltip.style.display = "none";
    container.appendChild(tooltip);

    // --- D3 force simulation ---
    let simNodes = [];
    let simLinks = [];
    let selectedNodeIds = new Set();
    let selectedRelIds = new Set();

    const simulation = d3.forceSimulation()
        .force("link", d3.forceLink().id(d => d.element_id).distance(120))
        .force("charge", d3.forceManyBody().strength(-300))
        .force("center", d3.forceCenter(width / 2, height / 2))
        .force("collide", d3.forceCollide().radius(35))
        .on("tick", ticked);

    simulation.stop();

    function ticked() {
        linkGroup.selectAll(".neo4j-link")
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);

        linkGroup.selectAll(".neo4j-link-label")
            .attr("x", d => (d.source.x + d.target.x) / 2)
            .attr("y", d => (d.source.y + d.target.y) / 2);

        nodeGroup.selectAll(".neo4j-node-group")
            .attr("transform", d => `translate(${d.x},${d.y})`);
    }

    function rebuildGraph() {
        const nodes = model.get("nodes") || [];
        const rels = model.get("relationships") || [];

        const nodeMap = new Map(nodes.map(n => [n.element_id, n]));

        // Preserve positions of existing nodes
        const oldPositions = new Map();
        simNodes.forEach(n => {
            oldPositions.set(n.element_id, { x: n.x, y: n.y, vx: n.vx, vy: n.vy });
        });

        simNodes = nodes.map(n => {
            const old = oldPositions.get(n.element_id);
            if (old) return { ...n, ...old };
            // New nodes get random position near center
            return {
                ...n,
                x: width / 2 + (Math.random() - 0.5) * 100,
                y: height / 2 + (Math.random() - 0.5) * 100,
            };
        });

        simLinks = rels
            .filter(r => nodeMap.has(r.start_node_element_id) && nodeMap.has(r.end_node_element_id))
            .map(r => ({
                ...r,
                source: r.start_node_element_id,
                target: r.end_node_element_id,
            }));

        simulation.nodes(simNodes);
        simulation.force("link").links(simLinks);
        simulation.alpha(0.3).restart();

        updateVisuals();
    }

    function updateVisuals() {
        // Links
        const linkSel = linkGroup.selectAll(".neo4j-link")
            .data(simLinks, d => d.element_id);

        linkSel.exit().remove();

        linkSel.enter()
            .append("line")
            .attr("class", "neo4j-link")
            .attr("marker-end", "url(#neo4j-arrowhead)")
            .on("click", handleRelClick)
            .on("mouseenter", (event, d) => showTooltip(event, formatProps(d.type, d.properties)))
            .on("mouseleave", hideTooltip)
            .merge(linkSel)
            .classed("neo4j-selected", d => selectedRelIds.has(d.element_id));

        // Link labels
        const linkLabelSel = linkGroup.selectAll(".neo4j-link-label")
            .data(simLinks, d => d.element_id);

        linkLabelSel.exit().remove();

        linkLabelSel.enter()
            .append("text")
            .attr("class", "neo4j-link-label")
            .merge(linkLabelSel)
            .text(d => d.type);

        // Node groups
        const nodeGSel = nodeGroup.selectAll(".neo4j-node-group")
            .data(simNodes, d => d.element_id);

        nodeGSel.exit().remove();

        const nodeEnter = nodeGSel.enter()
            .append("g")
            .attr("class", "neo4j-node-group")
            .call(d3.drag()
                .on("start", dragStarted)
                .on("drag", dragged)
                .on("end", dragEnded))
            .on("click", handleNodeClick)
            .on("dblclick", handleNodeDblClick)
            .on("mouseenter", (event, d) => showTooltip(event, formatProps(d.labels.join(":"), d.properties)))
            .on("mouseleave", hideTooltip);

        nodeEnter.append("circle")
            .attr("class", "neo4j-node")
            .attr("r", 14)
            .attr("fill", d => colorScale(d.labels[0] || ""));

        nodeEnter.append("text")
            .attr("class", "neo4j-node-label")
            .attr("dy", 28)
            .attr("text-anchor", "middle");

        // Update all (enter + update)
        const merged = nodeEnter.merge(nodeGSel);

        merged.select(".neo4j-node")
            .attr("fill", d => colorScale(d.labels[0] || ""))
            .classed("neo4j-selected", d => selectedNodeIds.has(d.element_id));

        merged.select(".neo4j-node-label")
            .text(d => d.display);
    }

    // --- Drag ---
    function dragStarted(event, d) {
        if (!event.active) simulation.alphaTarget(0.1).restart();
        d.fx = d.x;
        d.fy = d.y;
    }

    function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }

    function dragEnded(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }

    // --- Interactions ---
    function handleNodeClick(event, d) {
        event.stopPropagation();
        if (event.ctrlKey || event.metaKey) {
            // Multi-select toggle
            if (selectedNodeIds.has(d.element_id)) {
                selectedNodeIds.delete(d.element_id);
            } else {
                selectedNodeIds.add(d.element_id);
            }
        } else {
            // Single select
            if (selectedNodeIds.has(d.element_id) && selectedNodeIds.size === 1) {
                selectedNodeIds.clear();
            } else {
                selectedNodeIds.clear();
                selectedNodeIds.add(d.element_id);
            }
            selectedRelIds.clear();
        }
        syncSelection();
        updateVisuals();
    }

    function handleNodeDblClick(event, d) {
        event.stopPropagation();
        event.preventDefault();
        model.set("_expand_request", {
            element_id: d.element_id,
            request_id: ++requestCounter,
        });
        model.save_changes();
    }

    function handleRelClick(event, d) {
        event.stopPropagation();
        if (event.ctrlKey || event.metaKey) {
            if (selectedRelIds.has(d.element_id)) {
                selectedRelIds.delete(d.element_id);
            } else {
                selectedRelIds.add(d.element_id);
            }
        } else {
            if (selectedRelIds.has(d.element_id) && selectedRelIds.size === 1) {
                selectedRelIds.clear();
            } else {
                selectedRelIds.clear();
                selectedRelIds.add(d.element_id);
            }
            selectedNodeIds.clear();
        }
        syncSelection();
        updateVisuals();
    }

    // Click background to deselect (only if not panning)
    svgEl.addEventListener("click", (e) => {
        if (e.target === svgEl) {
            selectedNodeIds.clear();
            selectedRelIds.clear();
            syncSelection();
            updateVisuals();
        }
    });

    function syncSelection() {
        model.set("selected_nodes", Array.from(selectedNodeIds));
        model.set("selected_relationships", Array.from(selectedRelIds));
        model.save_changes();
    }

    // --- Tooltip ---
    function formatProps(header, props) {
        let html = `<strong>${header}</strong>`;
        for (const [k, v] of Object.entries(props || {})) {
            html += `<br><span class="neo4j-tooltip-key">${k}:</span> ${v}`;
        }
        return html;
    }

    function showTooltip(event, html) {
        tooltip.innerHTML = html;
        tooltip.style.display = "block";
        const rect = container.getBoundingClientRect();
        tooltip.style.left = (event.clientX - rect.left + 12) + "px";
        tooltip.style.top = (event.clientY - rect.top + 12) + "px";
    }

    function hideTooltip() {
        tooltip.style.display = "none";
    }

    // --- Query execution ---
    function runQuery() {
        const query = textarea.value.trim();
        if (!query) return;
        model.set("_query_request", {
            query: query,
            request_id: ++requestCounter,
        });
        model.save_changes();
    }

    runBtn.addEventListener("click", runQuery);

    textarea.addEventListener("keydown", (e) => {
        if (dropdown.style.display !== "none" && (e.key === "ArrowDown" || e.key === "ArrowUp" || e.key === "Tab" || e.key === "Enter")) {
            handleAutocompleteNav(e);
            return;
        }
        if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
            e.preventDefault();
            runQuery();
        }
    });

    // --- Autocomplete ---
    let acItems = [];
    let acIndex = -1;

    textarea.addEventListener("input", () => {
        const val = textarea.value;
        const pos = textarea.selectionStart;
        const before = val.slice(0, pos);

        const schema = model.get("schema") || {};
        let suggestions = [];
        let replaceFrom = pos;

        // After : or (: -> suggest labels
        const labelMatch = before.match(/[:(\s]:?\s*(\w*)$/);
        if (labelMatch) {
            const partial = labelMatch[1].toLowerCase();
            replaceFrom = pos - labelMatch[1].length;
            suggestions = (schema.labels || []).filter(l => l.toLowerCase().startsWith(partial));
        }

        // After [: -> suggest relationship types
        const relMatch = before.match(/\[\s*:?\s*(\w*)$/);
        if (relMatch) {
            const partial = relMatch[1].toLowerCase();
            replaceFrom = pos - relMatch[1].length;
            suggestions = (schema.relationship_types || []).filter(t => t.toLowerCase().startsWith(partial));
        }

        // At word boundary -> suggest keywords
        if (suggestions.length === 0) {
            const wordMatch = before.match(/(?:^|\s)(\w+)$/);
            if (wordMatch && wordMatch[1].length >= 2) {
                const partial = wordMatch[1].toUpperCase();
                replaceFrom = pos - wordMatch[1].length;
                suggestions = CYPHER_KEYWORDS.filter(k => k.startsWith(partial) && k !== partial);
            }
        }

        if (suggestions.length > 0 && suggestions.length <= 12) {
            showAutocomplete(suggestions, replaceFrom);
        } else {
            hideAutocomplete();
        }
    });

    function showAutocomplete(items, replaceFrom) {
        acItems = items;
        acIndex = -1;
        dropdown.innerHTML = "";
        items.forEach((item, i) => {
            const div = document.createElement("div");
            div.classList.add("neo4j-ac-item");
            div.textContent = item;
            div.addEventListener("mousedown", (e) => {
                e.preventDefault();
                acceptAutocomplete(item, replaceFrom);
            });
            dropdown.appendChild(div);
        });
        dropdown.style.display = "block";
        dropdown._replaceFrom = replaceFrom;
    }

    function hideAutocomplete() {
        dropdown.style.display = "none";
        acItems = [];
        acIndex = -1;
    }

    function handleAutocompleteNav(e) {
        if (e.key === "ArrowDown") {
            e.preventDefault();
            acIndex = Math.min(acIndex + 1, acItems.length - 1);
        } else if (e.key === "ArrowUp") {
            e.preventDefault();
            acIndex = Math.max(acIndex - 1, 0);
        } else if (e.key === "Tab" || e.key === "Enter") {
            e.preventDefault();
            if (acIndex >= 0 && acIndex < acItems.length) {
                acceptAutocomplete(acItems[acIndex], dropdown._replaceFrom);
            }
            return;
        }
        const children = dropdown.children;
        for (let i = 0; i < children.length; i++) {
            children[i].classList.toggle("neo4j-ac-active", i === acIndex);
        }
    }

    function acceptAutocomplete(item, replaceFrom) {
        const val = textarea.value;
        const pos = textarea.selectionStart;
        textarea.value = val.slice(0, replaceFrom) + item + val.slice(pos);
        textarea.selectionStart = textarea.selectionEnd = replaceFrom + item.length;
        hideAutocomplete();
        textarea.focus();
    }

    textarea.addEventListener("blur", () => {
        setTimeout(hideAutocomplete, 150);
    });

    // --- Observe model changes ---
    model.on("change:nodes", rebuildGraph);
    model.on("change:relationships", rebuildGraph);

    model.on("change:error", () => {
        const err = model.get("error");
        if (err) {
            errorBar.textContent = err;
            errorBar.style.display = "block";
        } else {
            errorBar.style.display = "none";
        }
    });

    model.on("change:query_running", () => {
        const running = model.get("query_running");
        runBtn.textContent = running ? "..." : "Run";
        runBtn.disabled = running;
    });

    // Initial render if data already present
    if ((model.get("nodes") || []).length > 0) {
        rebuildGraph();
    }
}

export default { render };
