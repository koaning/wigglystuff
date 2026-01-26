function render({ model, el }) {
  const container = document.createElement("div");
  container.style.position = "relative";
  container.style.display = "inline-block";

  const canvas = document.createElement("canvas");
  canvas.width = model.get("width");
  canvas.height = model.get("height");
  canvas.style.display = "block";
  canvas.style.cursor = "crosshair";

  container.appendChild(canvas);
  el.appendChild(container);

  const ctx = canvas.getContext("2d");
  const chartImage = new Image();
  let imageLoaded = false;
  let isDragging = false;
  let dragIndex = -1; // Which puck is being dragged

  function pixelToData(pixelX, pixelY) {
    const [xMin, xMax] = model.get("x_bounds");
    const [yMin, yMax] = model.get("y_bounds");
    const [left, top, right, bottom] = model.get("axes_pixel_bounds");

    // Clamp to axes area
    pixelX = Math.max(left, Math.min(right, pixelX));
    pixelY = Math.max(top, Math.min(bottom, pixelY));

    // Map (Y inverted because canvas Y goes down, data Y goes up)
    let dataX = xMin + ((pixelX - left) / (right - left)) * (xMax - xMin);
    let dataY = yMin + ((bottom - pixelY) / (bottom - top)) * (yMax - yMin);

    // Apply optional drag constraints in data space
    const dragXBounds = model.get("drag_x_bounds");
    const dragYBounds = model.get("drag_y_bounds");

    if (dragXBounds) {
      dataX = Math.max(dragXBounds[0], Math.min(dragXBounds[1], dataX));
    }
    if (dragYBounds) {
      dataY = Math.max(dragYBounds[0], Math.min(dragYBounds[1], dataY));
    }

    return { x: dataX, y: dataY };
  }

  function dataToPixel(dataX, dataY) {
    const [xMin, xMax] = model.get("x_bounds");
    const [yMin, yMax] = model.get("y_bounds");
    const [left, top, right, bottom] = model.get("axes_pixel_bounds");

    const pixelX = left + ((dataX - xMin) / (xMax - xMin)) * (right - left);
    const pixelY = bottom - ((dataY - yMin) / (yMax - yMin)) * (bottom - top);
    return { x: pixelX, y: pixelY };
  }

  function drawPuck(pixelX, pixelY, radius, color) {
    ctx.beginPath();
    ctx.arc(pixelX, pixelY, radius, 0, 2 * Math.PI);
    ctx.fillStyle = color;
    ctx.fill();

    // Draw white border for visibility
    ctx.strokeStyle = "white";
    ctx.lineWidth = 2;
    ctx.stroke();

    // Draw outer black border
    ctx.strokeStyle = "rgba(0, 0, 0, 0.3)";
    ctx.lineWidth = 1;
    ctx.stroke();
  }

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw chart image as background
    if (imageLoaded) {
      ctx.drawImage(chartImage, 0, 0);
    }

    // Draw all pucks
    const xs = model.get("x");
    const ys = model.get("y");
    const radius = model.get("puck_radius");
    const color = model.get("puck_color");

    for (let i = 0; i < xs.length; i++) {
      const puckPos = dataToPixel(xs[i], ys[i]);
      drawPuck(puckPos.x, puckPos.y, radius, color);
    }
  }

  function getCanvasCoords(event) {
    const rect = canvas.getBoundingClientRect();
    return {
      x: event.clientX - rect.left,
      y: event.clientY - rect.top,
    };
  }

  function findClosestPuck(pixelX, pixelY) {
    const xs = model.get("x");
    const ys = model.get("y");
    let closestIndex = 0;
    let closestDist = Infinity;

    for (let i = 0; i < xs.length; i++) {
      const puckPos = dataToPixel(xs[i], ys[i]);
      const dist = Math.hypot(puckPos.x - pixelX, puckPos.y - pixelY);
      if (dist < closestDist) {
        closestDist = dist;
        closestIndex = i;
      }
    }

    return closestIndex;
  }

  function handleStart(event) {
    event.preventDefault();

    let coords;
    if (event.touches) {
      coords = {
        x: event.touches[0].clientX - canvas.getBoundingClientRect().left,
        y: event.touches[0].clientY - canvas.getBoundingClientRect().top,
      };
    } else {
      coords = getCanvasCoords(event);
    }

    dragIndex = findClosestPuck(coords.x, coords.y);
    isDragging = true;
    handleMove(event);
  }

  function handleMove(event) {
    if (!isDragging || dragIndex < 0) return;
    event.preventDefault();

    let coords;
    if (event.touches) {
      coords = {
        x: event.touches[0].clientX - canvas.getBoundingClientRect().left,
        y: event.touches[0].clientY - canvas.getBoundingClientRect().top,
      };
    } else {
      coords = getCanvasCoords(event);
    }

    const data = pixelToData(coords.x, coords.y);

    // Update the dragged puck's position
    const xs = [...model.get("x")];
    const ys = [...model.get("y")];
    xs[dragIndex] = data.x;
    ys[dragIndex] = data.y;

    model.set("x", xs);
    model.set("y", ys);
    model.save_changes();
    draw();
  }

  function handleEnd() {
    isDragging = false;
    dragIndex = -1;
  }

  // Mouse events
  canvas.addEventListener("mousedown", handleStart);
  canvas.addEventListener("mousemove", handleMove);
  document.addEventListener("mouseup", handleEnd);

  // Touch events
  canvas.addEventListener("touchstart", handleStart);
  canvas.addEventListener("touchmove", handleMove);
  document.addEventListener("touchend", handleEnd);

  // Load chart image
  chartImage.onload = function () {
    imageLoaded = true;
    draw();
  };
  chartImage.src = model.get("chart_base64");

  // Sync from model changes
  model.on("change:x", draw);
  model.on("change:y", draw);
  model.on("change:puck_radius", draw);
  model.on("change:puck_color", draw);
  model.on("change:chart_base64", function () {
    chartImage.src = model.get("chart_base64");
  });

  // Initial draw
  draw();
}

export default { render };
