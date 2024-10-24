function render({ model, el }) {
  const canvas = document.createElement("canvas");
  canvas.setAttribute("id", "sliderCanvas");
  canvas.setAttribute("width", model.get("width").toString());
  canvas.setAttribute("height", model.get("height").toString());
  canvas.setAttribute("style", "border: 1px solid #ccc; background: #eee;");
  
  const sliderValuesDiv = document.createElement("div");
  sliderValuesDiv.setAttribute("id", "sliderValues");
  
  el.appendChild(canvas);
  el.appendChild(sliderValuesDiv);

  const ctx = canvas.getContext('2d');

  const centerX = canvas.width / 2;
  const centerY = canvas.height / 2;
  const radius = Math.min(centerX, centerY) - 20;

  let isDragging = false;
  let currentX = 0;
  let currentY = 0;

  // Add min/max attributes for x and y
  const minX = model.get('min_x');
  const maxX = model.get('max_x');
  const minY = model.get('min_y');
  const maxY = model.get('max_y');

  console.log(minX, maxX, minY, maxY);

  function drawSlider() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      ctx.beginPath();
      ctx.arc(centerX + currentX, centerY + currentY, 10, 0, 2 * Math.PI);
      ctx.fillStyle = '#eee';
      ctx.strokeStyle = "#666";
      ctx.lineWidth = 2;
      ctx.fill();
      ctx.stroke();

      // Update normalization to use min/max values
      const normalizedX = minX + (currentX / radius + 1) * (maxX - minX) / 2;
      const normalizedY = maxY - (currentY / radius + 1) * (maxY - minY) / 2;
      sliderValuesDiv.textContent = `X: ${normalizedX.toFixed(2)}, Y: ${normalizedY.toFixed(2)}`;
      model.set('x', normalizedX);
      model.set('y', normalizedY);
      model.save_changes();
  }

  function handleMouseDown(event) {
      isDragging = true;
      updateSliderPosition(event);
  }

  function handleMouseMove(event) {
      if (isDragging) {
          updateSliderPosition(event);
      }
  }

  function updateSliderPosition(event) {
      currentX = event.offsetX - centerX;
      currentY = event.offsetY - centerY;
      currentX = Math.max(-radius, Math.min(radius, currentX));
      currentY = Math.max(-radius, Math.min(radius, currentY));
      drawSlider();
  }

  function handleMouseUp() {
      isDragging = false;
  }

  canvas.addEventListener('mousedown', handleMouseDown);
  canvas.addEventListener('mousemove', handleMouseMove);
  canvas.addEventListener('mouseup', handleMouseUp);

  drawSlider();
}

export default { render };
