import * as d3 from "./d3.min.js";

function render({model, el}){

    const container = document.createElement('div');
    container.classList.add("matrix-container");
    el.appendChild(container);

    // Sample nodes
    const nodes = model.get("names").map((name) => ({ id: name, x: 100, y: 100 }));

    let links = [];
    let selectedNode = null;

    // Set up the SVG
    const width = 600;
    const height = 400;
    const svg = d3.select(container)
        .append("svg")
        .attr("width", width)
        .attr("height", height);

    // Define arrow marker
    svg.append("defs").append("marker")
        .attr("id", "arrowhead")
        .attr("viewBox", "-0 -5 10 10")
        .attr("refX", 13)
        .attr("refY", 0)
        .attr("orient", "auto")
        .attr("markerWidth", 6)
        .attr("markerHeight", 6)
        .append("path")
        .attr("d", "M0,-5L10,0L0,5")
        .attr("class", "arrow");

    // Force simulation with gentler forces
    const simulation = d3.forceSimulation(nodes)
        .force("link", d3.forceLink(links).id(d => d.id).distance(100))
        .force("charge", d3.forceManyBody().strength(-50))
        .force("center", d3.forceCenter(width / 2, height / 2))
        .force("collide", d3.forceCollide().radius(30))
        .on("tick", ticked);

    // Create the link group and node group
    const linkGroup = svg.append("g");
    const nodeGroup = svg.append("g");

    // Draw nodes
    const node = nodeGroup.selectAll(".node")
        .data(nodes)
        .join("circle")
        .attr("class", "node")
        .attr("r", 10)
        .attr("fill", "#69b3a2")
        .on("click", handleNodeClick);

    // Add label backgrounds
    const labelBackgrounds = nodeGroup.selectAll(".label-background")
        .data(nodes)
        .join("rect")
        .attr("class", "label-background")
        .attr("rx", 3)
        .attr("ry", 3);

    // Add labels
    const labels = nodeGroup.selectAll(".label")
        .data(nodes)
        .join("text")
        .attr("class", "label")
        .attr("dx", 15)
        .attr("dy", 4)
        .text(d => d.id);
        
    // Size the background rectangles to fit the text
    labels.each(function(d) {
        const bbox = this.getBBox();
        const rect = labelBackgrounds.filter(r => r === d);
        rect
            .attr("x", bbox.x - 2)
            .attr("y", bbox.y - 1)
            .attr("width", bbox.width + 4)
            .attr("height", bbox.height + 2);
    });

    function handleNodeClick(event, d) {
        if (!selectedNode) {
            // First click - select node
            selectedNode = d;
            node.classed("selected", n => n === selectedNode);
        } else if (selectedNode === d) {
            // Clicked same node - deselect
            selectedNode = null;
            node.classed("selected", false);
        } else {
            // Second click - create link
            // Check if a link already exists in either direction
            const existingForwardLink = links.find(l => 
                (l.source === selectedNode && l.target === d) ||
                (l.source.id === selectedNode.id && l.target.id === d.id)
            );
            const existingReverseLink = links.find(l => 
                (l.source === d && l.target === selectedNode) ||
                (l.source.id === d.id && l.target.id === selectedNode.id)
            );
            
            // Remove existing reverse link if present
            if (existingReverseLink) {
                links = links.filter(l => l !== existingReverseLink);
            }
            
            // Add new link if no forward link exists
            if (!existingForwardLink) {
                links.push({source: selectedNode, target: d});
            }
            
            simulation.force("link").links(links);
            selectedNode = null;
            node.classed("selected", false);
            updateLinks();
        }
        model.set("links", links.map(l => ({source: l.source.id, target: l.target.id})));
        console.log(links.map(l => ({source: l.source.id, target: l.target.id})));
        model.save_changes();
    }

    function updateLinks() {
        const link = linkGroup.selectAll(".link")
            .data(links)
            .join("path")
            .attr("class", "link")
            .attr("marker-end", "url(#arrowhead)")
            .attr("d", d => {
                const dx = d.target.x - d.source.x;
                const dy = d.target.y - d.source.y;
                return `M${d.source.x},${d.source.y}L${d.target.x},${d.target.y}`;
            })
            .on("click", function(event, d) {
                event.stopPropagation();
                // Remove link on click
                links = links.filter(l => l !== d);
                simulation.force("link").links(links);
                updateLinks();
                model.set("links", links.map(l => ({source: l.source.id, target: l.target.id})));
                console.log(links.map(l => ({source: l.source.id, target: l.target.id})));
                model.save_changes();
            });
    }

    function ticked() {
        // Update node positions
        node
            .attr("cx", d => d.x = Math.max(15, Math.min(width - 15, d.x)))
            .attr("cy", d => d.y = Math.max(15, Math.min(height - 15, d.y)));

        labels
            .attr("x", d => d.x)
            .attr("y", d => d.y);

        // Update link positions
        updateLinks();
    }

    // Add drag behavior just for repositioning
    const drag = d3.drag()
        .on("drag", function(event, d) {
            d.x = event.x;
            d.y = event.y;
            simulation.alpha(0.1).restart();
        });

    node.call(drag);
};

export default { render };