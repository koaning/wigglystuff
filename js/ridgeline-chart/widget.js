import { select } from "d3-selection";
import { min, max } from "d3-array";
import { scaleLinear, scaleBand } from "d3-scale";
import { axisBottom, axisLeft } from "d3-axis";
import { line, area } from "d3-shape";

function render({ model, el }) {
    // Create container
    const container = document.createElement("div");
    container.classList.add("ridgeline-chart-container");
    el.appendChild(container);

    // Get initial values
    let data = model.get("data") || [];
    let xValues = model.get("x_values") || [];
    const width = model.get("width");
    const height = model.get("height");
    let overlap = model.get("overlap");
    let strokeWidth = model.get("stroke_width");
    let fillOpacity = model.get("fill_opacity");
    let peakScale = model.get("peak_scale") || 1.0;
    let selectedIndex = model.get("selected_index");
    const xLabel = model.get("x_label") || "";
    const yLabel = model.get("y_label") || "";

    // Helper to create selected_row with x,y pairs
    function createSelectedRow(values) {
        return values.map((y, i) => ({
            x: xValues[i] !== undefined ? xValues[i] : i,
            y: y
        }));
    }

    // Margins for axes
    const margin = { top: 20, right: 20, bottom: 40, left: 60 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    // Create SVG
    const svg = select(container)
        .append("svg")
        .attr("width", width)
        .attr("height", height)
        .attr("class", "ridgeline-chart-svg");

    // Create main group with margins
    const g = svg
        .append("g")
        .attr("transform", `translate(${margin.left}, ${margin.top})`);

    // Add clip path to prevent peaks from extending beyond chart area
    // We'll update the clip height dynamically based on the computed row height
    const clipId = `ridgeline-clip-${Math.random().toString(36).substr(2, 9)}`;
    const clipRect = svg.append("defs")
        .append("clipPath")
        .attr("id", clipId)
        .append("rect")
        .attr("x", 0)
        .attr("y", 0)
        .attr("width", innerWidth)
        .attr("height", innerHeight);

    // Create groups for different elements
    const rowsGroup = g.append("g")
        .attr("class", "ridgeline-rows")
        .attr("clip-path", `url(#${clipId})`);
    const yAxisGroup = g.append("g").attr("class", "ridgeline-y-axis");
    const xAxisGroup = g
        .append("g")
        .attr("class", "ridgeline-x-axis")
        .attr("transform", `translate(0, ${innerHeight})`);

    // X-axis label
    const xLabelText = svg
        .append("text")
        .attr("class", "ridgeline-axis-label ridgeline-x-label")
        .attr("x", margin.left + innerWidth / 2)
        .attr("y", height - 5)
        .attr("text-anchor", "middle")
        .text(xLabel);

    // Y-axis label
    const yLabelText = svg
        .append("text")
        .attr("class", "ridgeline-axis-label ridgeline-y-label")
        .attr("transform", "rotate(-90)")
        .attr("x", -(margin.top + innerHeight / 2))
        .attr("y", 15)
        .attr("text-anchor", "middle")
        .text(yLabel);

    function computeScales() {
        const numRows = data.length;
        if (numRows === 0) return { x: null, y: null, yBand: null };

        // Find the max points per row
        const maxPoints = Math.max(...data.map((d) => d.values.length));

        // X scale: horizontal position based on point index
        const x = scaleLinear().domain([0, maxPoints - 1]).range([0, innerWidth]);

        // Y band scale for row positioning (maps row indices to vertical positions)
        const rowIndices = data.map((d) => d.index);
        const yBand = scaleBand()
            .domain(rowIndices)
            .range([innerHeight, 0])
            .padding(0);

        // Calculate row height based on overlap
        const baseRowHeight = innerHeight / numRows;
        const rowHeight = baseRowHeight * (1 + overlap);

        // Y scale: for amplitude within each row
        const allValues = data.flatMap((d) => d.values);
        const minVal = min(allValues) || 0;
        const maxVal = max(allValues) || 1;
        const range = maxVal - minVal || 1;

        // Y scale maps amplitude to displacement within the row
        // peakScale controls how tall the peaks can be (1.0 = 40% of row height, 2.0 = 80%, etc.)
        const amplitudeRange = rowHeight * 0.4 * peakScale;
        const yAmplitude = scaleLinear()
            .domain([minVal - range * 0.1, maxVal + range * 0.1])
            .range([amplitudeRange, -amplitudeRange]);

        return { x, yBand, yAmplitude, rowHeight, numRows };
    }

    function drawChart() {
        const scales = computeScales();
        if (!scales.x) {
            rowsGroup.selectAll("*").remove();
            yAxisGroup.selectAll("*").remove();
            xAxisGroup.selectAll("*").remove();
            return;
        }

        const { x, yBand, yAmplitude, rowHeight } = scales;

        // Update clip path to extend below the chart to show the bottom row fully
        // The bottom row's fill area extends down by rowHeight * 0.5, peaks can extend rowHeight
        clipRect.attr("height", innerHeight + rowHeight);

        // Draw Y-axis with row indices
        // Position ticks at the baseline of each waveform (where y=0 maps to)
        const baselineOffset = yAmplitude(0);  // Where the baseline sits within the row
        const yAxis = axisLeft(yBand).tickSize(0).tickPadding(10);
        yAxisGroup.call(yAxis);
        yAxisGroup.select(".domain").remove();

        // Adjust tick positions to align with waveform baselines
        yAxisGroup.selectAll(".tick")
            .attr("transform", d => {
                const yPos = yBand(d) + yBand.bandwidth() / 2 + baselineOffset;
                return `translate(0, ${yPos})`;
            });

        // Draw X-axis with ticks (no axis line)
        // Move x-axis down to accommodate the bottom row's waveform
        const xAxisOffset = rowHeight * 0.5;
        xAxisGroup.attr("transform", `translate(0, ${innerHeight + xAxisOffset})`);
        xAxisGroup.selectAll("*").remove();
        const xAxis = axisBottom(x).ticks(10);
        xAxisGroup.call(xAxis);
        xAxisGroup.select(".domain").remove();

        // Also move the x-axis label down
        xLabelText.attr("y", margin.top + innerHeight + xAxisOffset + 35);

        // Expand SVG height to fit the extended content
        svg.attr("height", height + xAxisOffset);

        // Line generator
        const lineGen = line()
            .defined((d) => !isNaN(d))
            .x((d, i) => x(i))
            .y((d) => yAmplitude(d));

        // Area generator (for fill beneath line)
        const areaGen = area()
            .defined((d) => !isNaN(d))
            .x((d, i) => x(i))
            .y0(rowHeight * 0.5)
            .y1((d) => yAmplitude(d));

        // Draw rows in reverse order: higher indices (back/top) rendered first,
        // lower indices (front/bottom) rendered last so they appear on top
        const sortedData = [...data].reverse();
        const rows = rowsGroup
            .selectAll(".ridgeline-row")
            .data(sortedData, (d) => d.index)
            .join(
                (enter) => {
                    const g = enter
                        .append("g")
                        .attr("class", "ridgeline-row")
                        .attr("transform", (d) => {
                            const yPos = yBand(d.index) + yBand.bandwidth() / 2;
                            return `translate(0, ${yPos})`;
                        });

                    // Add area (fill) - no pointer events
                    g.append("path")
                        .attr("class", "ridgeline-area")
                        .attr("d", (d) => areaGen(d.values))
                        .style("opacity", fillOpacity);

                    // Add invisible thick stroke for easier click targeting
                    g.append("path")
                        .attr("class", "ridgeline-line-hitbox")
                        .attr("d", (d) => lineGen(d.values));

                    // Add visible line (stroke)
                    g.append("path")
                        .attr("class", "ridgeline-line")
                        .attr("d", (d) => lineGen(d.values))
                        .style("stroke-width", strokeWidth);

                    return g;
                },
                (update) =>
                    update
                        .attr("transform", (d) => {
                            const yPos = yBand(d.index) + yBand.bandwidth() / 2;
                            return `translate(0, ${yPos})`;
                        })
                        .call((g) => {
                            g.select(".ridgeline-area")
                                .attr("d", (d) => areaGen(d.values))
                                .style("opacity", fillOpacity);
                            g.select(".ridgeline-line-hitbox")
                                .attr("d", (d) => lineGen(d.values));
                            g.select(".ridgeline-line")
                                .attr("d", (d) => lineGen(d.values))
                                .style("stroke-width", strokeWidth);
                        }),
                (exit) => exit.remove()
            );

        // Add interaction handlers to the hitbox paths (not the row groups)
        rows.selectAll(".ridgeline-line-hitbox")
            .on("mouseenter", handleMouseEnter)
            .on("mouseleave", handleMouseLeave)
            .on("click", handleClick);

        // Update selection highlighting
        updateSelection();
    }

    function handleMouseEnter(event, d) {
        // Navigate to parent row group and add hover class
        select(this.parentNode).classed("ridgeline-row-hover", true);
        // Highlight corresponding y-axis label
        yAxisGroup.selectAll(".tick text")
            .classed("ridgeline-y-label-hover", (tickData) => tickData === d.index);
    }

    function handleMouseLeave(event, d) {
        // Navigate to parent row group and remove hover class
        select(this.parentNode).classed("ridgeline-row-hover", false);
        // Remove highlight from y-axis label
        yAxisGroup.selectAll(".tick text")
            .classed("ridgeline-y-label-hover", false);
    }

    function handleClick(event, d) {
        const clickedIndex = d.index;

        // Toggle selection: if already selected, deselect
        if (selectedIndex === clickedIndex) {
            selectedIndex = null;
            model.set("selected_index", null);
            model.set("selected_row", []);
        } else {
            selectedIndex = clickedIndex;
            model.set("selected_index", clickedIndex);
            model.set("selected_row", createSelectedRow(d.values));
        }
        model.save_changes();
        updateSelection();
    }

    function updateSelection() {
        rowsGroup
            .selectAll(".ridgeline-row")
            .classed("ridgeline-row-selected", (d) => d.index === selectedIndex);

        // Also highlight the selected y-axis label
        yAxisGroup.selectAll(".tick text")
            .classed("ridgeline-y-label-selected", (tickData) => tickData === selectedIndex);
    }

    // Initial draw
    drawChart();

    // Listen for changes from Python
    model.on("change:data", () => {
        data = model.get("data") || [];
        drawChart();
    });

    model.on("change:overlap", () => {
        overlap = model.get("overlap");
        drawChart();
    });

    model.on("change:stroke_width", () => {
        strokeWidth = model.get("stroke_width");
        drawChart();
    });

    model.on("change:fill_opacity", () => {
        fillOpacity = model.get("fill_opacity");
        drawChart();
    });

    model.on("change:peak_scale", () => {
        peakScale = model.get("peak_scale") || 1.0;
        drawChart();
    });

    model.on("change:selected_index", () => {
        selectedIndex = model.get("selected_index");
        // Update selected_row if index changed from Python
        if (selectedIndex !== null) {
            const row = data.find((d) => d.index === selectedIndex);
            if (row) {
                model.set("selected_row", createSelectedRow(row.values));
                model.save_changes();
            }
        }
        updateSelection();
    });

    model.on("change:x_values", () => {
        xValues = model.get("x_values") || [];
    });
}

export default { render };
