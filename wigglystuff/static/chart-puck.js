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

  function pixelToData(pixelX, pixelY) {
    const [xMin, xMax] = model.get("x_bounds");
    const [yMin, yMax] = model.get("y_bounds");
    const [left, top, right, bottom] = model.get("axes_pixel_bounds");

    // Clamp to axes area
    pixelX = Math.max(left, Math.min(right, pixelX));
    pixelY = Math.max(top, Math.min(bottom, pixelY));

    // Map (Y inverted because canvas Y goes down, data Y goes up)
    const dataX = xMin + ((pixelX - left) / (right - left)) * (xMax - xMin);
    const dataY = yMin + ((bottom - pixelY) / (bottom - top)) * (yMax - yMin);
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

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw chart image as background
    if (imageLoaded) {
      ctx.drawImage(chartImage, 0, 0);
    }

    // Draw puck
    const puckPos = dataToPixel(model.get("x"), model.get("y"));
    const radius = model.get("puck_radius");
    const color = model.get("puck_color");

    ctx.beginPath();
    ctx.arc(puckPos.x, puckPos.y, radius, 0, 2 * Math.PI);
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

  function getCanvasCoords(event) {
    const rect = canvas.getBoundingClientRect();
    return {
      x: event.clientX - rect.left,
      y: event.clientY - rect.top,
    };
  }

  function handleStart(event) {
    event.preventDefault();
    isDragging = true;
    handleMove(event);
  }

  function handleMove(event) {
    if (!isDragging) return;
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
    model.set("x", data.x);
    model.set("y", data.y);
    model.save_changes();
    draw();
  }

  function handleEnd() {
    isDragging = false;
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
