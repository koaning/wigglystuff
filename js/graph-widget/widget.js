import { drag } from "d3-drag";
import { forceCenter, forceCollide, forceLink, forceManyBody, forceSimulation } from "d3-force";
import { scaleOrdinal } from "d3-scale";
import { schemeTableau10 } from "d3-scale-chromatic";
import { select } from "d3-selection";
import { zoom } from "d3-zoom";

let widgetCounter = 0;

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function numberOr(value, fallback) {
    const num = Number(value);
    return Number.isFinite(num) ? num : fallback;
}

function render({ model, el }) {
    const instanceId = ++widgetCounter;
    const arrowId = `graph-widget-arrow-${instanceId}`;
    const colorScale = scaleOrdinal(schemeTableau10);

    const container = document.createElement("div");
    container.classList.add("graph-widget");
    el.appendChild(container);

    const svgEl = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svgEl.classList.add("graph-widget-svg");
    container.appendChild(svgEl);

    const tooltip = document.createElement("div");
    tooltip.classList.add("graph-widget-tooltip");
    tooltip.style.display = "none";
    container.appendChild(tooltip);

    const svg = select(svgEl);
    svg.append("defs").append("marker")
        .attr("id", arrowId)
        .attr("viewBox", "-0 -5 10 10")
        .attr("refX", 9)
        .attr("refY", 0)
        .attr("orient", "auto")
        .attr("markerWidth", 6)
        .attr("markerHeight", 6)
        .append("path")
        .attr("d", "M0,-5L10,0L0,5")
        .attr("class", "graph-widget-arrow");

    const zoomGroup = svg.append("g").attr("class", "graph-widget-zoom");
    const edgeGroup = zoomGroup.append("g").attr("class", "graph-widget-edges");
    const edgeLabelGroup = zoomGroup.append("g").attr("class", "graph-widget-edge-labels");
    const nodeGroup = zoomGroup.append("g").attr("class", "graph-widget-nodes");

    const zoomBehavior = zoom()
        .scaleExtent([0.1, 5])
        .on("zoom", (event) => {
            zoomGroup.attr("transform", event.transform);
        });
    svg.call(zoomBehavior);

    let height = numberOr(model.get("height"), 400);
    let effectiveWidth = numberOr(model.get("width"), container.clientWidth || 600);
    let simNodes = [];
    let simEdges = [];
    let selectedNodes = new Set(model.get("selected_nodes") || []);
    let selectedEdges = new Set(model.get("selected_edges") || []);
    let resizeObserver = null;

    const simulation = forceSimulation()
        .force("link", forceLink().id((d) => d.id).distance(95).strength(0.9))
        .force("charge", forceManyBody().strength(-220))
        .force("center", forceCenter(effectiveWidth / 2, height / 2))
        .force("collide", forceCollide().radius((d) => nodeRadius(d) + 8))
        .on("tick", ticked);

    simulation.stop();

    function nodeRadius(d) {
        return Math.max(4, numberOr(d.size, 14));
    }

    function edgeWidth(d) {
        return Math.max(1, numberOr(d.width ?? d.size, 1.7));
    }

    function edgeKey(d) {
        return d.id;
    }

    function applySize() {
        svgEl.setAttribute("width", effectiveWidth);
        svgEl.setAttribute("height", height);
        svgEl.setAttribute("viewBox", `0 0 ${effectiveWidth} ${height}`);
        simulation.force("center", forceCenter(effectiveWidth / 2, height / 2));
        simulation.alpha(0.2).restart();
    }

    function resize() {
        const rawWidth = model.get("width");
        const explicitWidth = Number.isFinite(Number(rawWidth)) ? Number(rawWidth) : null;
        height = numberOr(model.get("height"), 400);

        if (explicitWidth !== null) {
            if (resizeObserver) {
                resizeObserver.disconnect();
                resizeObserver = null;
            }
            container.style.display = "";
            container.style.width = "";
            effectiveWidth = explicitWidth;
        } else {
            container.style.display = "block";
            container.style.width = "100%";
            const measured = el.clientWidth || container.clientWidth;
            effectiveWidth = measured || effectiveWidth || 600;
            if (!resizeObserver && typeof ResizeObserver !== "undefined") {
                resizeObserver = new ResizeObserver(() => {
                    const next = el.clientWidth || container.clientWidth;
                    if (!next || next === effectiveWidth) return;
                    effectiveWidth = next;
                    applySize();
                });
                resizeObserver.observe(el);
            }
        }
        applySize();
    }

    function restartSimulation() {
        simulation.alpha(0.2).restart();
    }

    function syncSelected() {
        model.set("selected_nodes", Array.from(selectedNodes));
        model.set("selected_edges", Array.from(selectedEdges));
        model.save_changes();
    }

    function showTooltip(event, d, kind) {
        const title = d.name || d.id || kind;
        let html = `<strong>${escapeHtml(title)}</strong>`;
        if (kind === "node") {
            html += `<br><span class="graph-widget-tooltip-key">id:</span> ${escapeHtml(d.id)}`;
        } else {
            html += `<br><span class="graph-widget-tooltip-key">source:</span> ${escapeHtml(d.source.id || d.source)}`;
            html += `<br><span class="graph-widget-tooltip-key">target:</span> ${escapeHtml(d.target.id || d.target)}`;
        }
        if (d.data && typeof d.data === "object") {
            for (const [key, value] of Object.entries(d.data)) {
                html += `<br><span class="graph-widget-tooltip-key">${escapeHtml(key)}:</span> ${escapeHtml(value)}`;
            }
        }
        tooltip.innerHTML = html;
        tooltip.style.display = "block";
        const rect = container.getBoundingClientRect();
        tooltip.style.left = `${event.clientX - rect.left + 12}px`;
        tooltip.style.top = `${event.clientY - rect.top + 12}px`;
    }

    function hideTooltip() {
        tooltip.style.display = "none";
    }

    function rebuildGraph() {
        const nodes = model.get("nodes") || [];
        const edges = model.get("edges") || [];
        const nodeMap = new Map(nodes.map((node) => [node.id, node]));
        const oldPositions = new Map();
        simNodes.forEach((node) => {
            oldPositions.set(node.id, {
                x: node.x,
                y: node.y,
                vx: node.vx,
                vy: node.vy,
                fx: node.fx,
                fy: node.fy,
            });
        });

        function newNodePosition(node, index) {
            if (Number.isFinite(Number(node.x)) && Number.isFinite(Number(node.y))) {
                return { x: Number(node.x), y: Number(node.y) };
            }

            const edgeIndex = edges.findIndex((edge) => {
                return (
                    (edge.source === node.id && oldPositions.has(edge.target)) ||
                    (edge.target === node.id && oldPositions.has(edge.source))
                );
            });
            if (edgeIndex >= 0) {
                const edge = edges[edgeIndex];
                const sourceIsOld = oldPositions.has(edge.source);
                const anchor = oldPositions.get(sourceIsOld ? edge.source : edge.target);
                const direction = sourceIsOld ? 1 : -1;
                const lane = (edgeIndex % 5) - 2;
                return {
                    x: anchor.x + direction * 80,
                    y: anchor.y + lane * 28,
                };
            }

            const angle = index * 2.399963229728653;
            const radius = 24 + index * 3;
            return {
                x: effectiveWidth / 2 + Math.cos(angle) * radius,
                y: height / 2 + Math.sin(angle) * radius,
            };
        }

        simNodes = nodes.map((node, index) => {
            const old = oldPositions.get(node.id);
            if (old) return { ...node, ...old };
            return {
                ...node,
                ...newNodePosition(node, index),
            };
        });

        simEdges = edges
            .filter((edge) => nodeMap.has(edge.source) && nodeMap.has(edge.target))
            .map((edge) => ({
                ...edge,
                source: edge.source,
                target: edge.target,
            }));

        selectedNodes = new Set((model.get("selected_nodes") || []).filter((id) => nodeMap.has(id)));
        selectedEdges = new Set((model.get("selected_edges") || []).filter((id) => simEdges.some((edge) => edge.id === id)));

        simulation.nodes(simNodes);
        simulation.force("link").links(simEdges);
        simulation.alpha(oldPositions.size ? 0.16 : 0.35).restart();
        updateVisuals();
    }

    function updateVisuals() {
        const directed = model.get("directed");

        const edgeSelection = edgeGroup.selectAll(".graph-widget-edge")
            .data(simEdges, edgeKey);
        edgeSelection.exit().remove();
        edgeSelection.enter()
            .append("path")
            .attr("class", "graph-widget-edge")
            .on("click", handleEdgeClick)
            .on("mouseenter", (event, d) => showTooltip(event, d, "edge"))
            .on("mouseleave", hideTooltip)
            .merge(edgeSelection)
            .attr("stroke", (d) => d.color || "var(--graph-edge)")
            .attr("stroke-width", edgeWidth)
            .attr("marker-end", directed ? `url(#${arrowId})` : null)
            .classed("is-selected", (d) => selectedEdges.has(d.id));

        const edgeLabelSelection = edgeLabelGroup.selectAll(".graph-widget-edge-label")
            .data(simEdges.filter((edge) => edge.name), edgeKey);
        edgeLabelSelection.exit().remove();
        edgeLabelSelection.enter()
            .append("text")
            .attr("class", "graph-widget-edge-label")
            .merge(edgeLabelSelection)
            .text((d) => d.name || "");

        const nodeSelection = nodeGroup.selectAll(".graph-widget-node-group")
            .data(simNodes, (d) => d.id);
        nodeSelection.exit().remove();

        const nodeEnter = nodeSelection.enter()
            .append("g")
            .attr("class", "graph-widget-node-group")
            .call(drag()
                .on("start", dragStarted)
                .on("drag", dragged)
                .on("end", dragEnded))
            .on("click", handleNodeClick)
            .on("mouseenter", (event, d) => {
                showTooltip(event, d, "node");
                model.set("hovered_node", d.id);
                model.save_changes();
            })
            .on("mouseleave", (event, d) => {
                hideTooltip();
                model.set("hovered_node", null);
                model.save_changes();
            });

        nodeEnter.append("circle").attr("class", "graph-widget-node");
        nodeEnter.append("text")
            .attr("class", "graph-widget-node-name")
            .attr("text-anchor", "middle");

        const mergedNodes = nodeEnter.merge(nodeSelection);
        mergedNodes.select(".graph-widget-node")
            .attr("r", nodeRadius)
            .attr("fill", (d) => d.color || colorScale(d.id))
            .classed("is-selected", (d) => selectedNodes.has(d.id));
        mergedNodes.select(".graph-widget-node-name")
            .attr("dy", (d) => nodeRadius(d) + 14)
            .text((d) => d.name || "");
    }

    function ticked() {
        if (model.get("bounded") ?? true) {
            const padding = 18;
            simNodes.forEach((node) => {
                const radius = nodeRadius(node);
                node.x = Math.max(padding + radius, Math.min(effectiveWidth - padding - radius, node.x));
                node.y = Math.max(padding + radius, Math.min(height - padding - radius, node.y));
            });
        }

        edgeGroup.selectAll(".graph-widget-edge")
            .attr("d", edgePath);

        edgeLabelGroup.selectAll(".graph-widget-edge-label")
            .attr("x", (d) => (d.source.x + d.target.x) / 2)
            .attr("y", (d) => (d.source.y + d.target.y) / 2 - 5);

        nodeGroup.selectAll(".graph-widget-node-group")
            .attr("transform", (d) => `translate(${d.x},${d.y})`);
    }

    function dragStarted(event, d) {
        if (!event.active) simulation.alphaTarget(0.2).restart();
        d.fx = d.x;
        d.fy = d.y;
    }

    function edgePath(d) {
        const sourceRadius = nodeRadius(d.source);
        const targetRadius = nodeRadius(d.target);
        const dx = d.target.x - d.source.x;
        const dy = d.target.y - d.source.y;
        const distance = Math.hypot(dx, dy) || 1;
        const ux = dx / distance;
        const uy = dy / distance;
        const startX = d.source.x + ux * (sourceRadius + 2);
        const startY = d.source.y + uy * (sourceRadius + 2);
        const endX = d.target.x - ux * (targetRadius + 9);
        const endY = d.target.y - uy * (targetRadius + 9);
        return `M${startX},${startY}L${endX},${endY}`;
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

    function handleNodeClick(event, d) {
        event.stopPropagation();
        if (event.ctrlKey || event.metaKey) {
            if (selectedNodes.has(d.id)) selectedNodes.delete(d.id);
            else selectedNodes.add(d.id);
        } else if (selectedNodes.has(d.id) && selectedNodes.size === 1) {
            selectedNodes.clear();
        } else {
            selectedNodes.clear();
            selectedEdges.clear();
            selectedNodes.add(d.id);
        }
        syncSelected();
        updateVisuals();
    }

    function handleEdgeClick(event, d) {
        event.stopPropagation();
        if (event.ctrlKey || event.metaKey) {
            if (selectedEdges.has(d.id)) selectedEdges.delete(d.id);
            else selectedEdges.add(d.id);
        } else if (selectedEdges.has(d.id) && selectedEdges.size === 1) {
            selectedEdges.clear();
        } else {
            selectedEdges.clear();
            selectedNodes.clear();
            selectedEdges.add(d.id);
        }
        syncSelected();
        updateVisuals();
    }

    svgEl.addEventListener("click", (event) => {
        if (event.target === svgEl) {
            selectedNodes.clear();
            selectedEdges.clear();
            syncSelected();
            updateVisuals();
        }
    });

    function syncFromModelSelection() {
        selectedNodes = new Set(model.get("selected_nodes") || []);
        selectedEdges = new Set(model.get("selected_edges") || []);
        updateVisuals();
    }

    model.on("change:nodes", rebuildGraph);
    model.on("change:edges", rebuildGraph);
    model.on("change:directed", updateVisuals);
    model.on("change:bounded", restartSimulation);
    model.on("change:selected_nodes", syncFromModelSelection);
    model.on("change:selected_edges", syncFromModelSelection);
    model.on("change:width", resize);
    model.on("change:height", resize);

    resize();
    rebuildGraph();

    return () => {
        simulation.stop();
        if (resizeObserver) {
            resizeObserver.disconnect();
            resizeObserver = null;
        }
        model.off("change:nodes", rebuildGraph);
        model.off("change:edges", rebuildGraph);
        model.off("change:directed", updateVisuals);
        model.off("change:bounded", restartSimulation);
        model.off("change:selected_nodes", syncFromModelSelection);
        model.off("change:selected_edges", syncFromModelSelection);
        model.off("change:width", resize);
        model.off("change:height", resize);
    };
}

export default { render };
