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

  function drawSlider() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      ctx.beginPath();
      ctx.arc(centerX + currentX, centerY + currentY, 10, 0, 2 * Math.PI);
      ctx.fillStyle = '#eee';
      ctx.strokeStyle = "#666";
      ctx.lineWidth = 2;
      ctx.fill();
      ctx.stroke();

      const [x_min, x_max] = model.get("x_bounds");
      const [y_min, y_max] = model.get("y_bounds");

      const mappedX = x_min + ((currentX / radius) + 1) / 2 * (x_max - x_min);
      const mappedY = y_min + ((-currentY / radius) + 1) / 2 * (y_max - y_min); // Y is inverted

      sliderValuesDiv.textContent = `X: ${mappedX.toFixed(2)}, Y: ${mappedY.toFixed(2)}`;
      model.set('x', mappedX);
      model.set('y', mappedY);
      model.save_changes();
  }

  function syncFromModel() {
      const [x_min, x_max] = model.get("x_bounds");
      const [y_min, y_max] = model.get("y_bounds");
      const modelX = model.get('x');
      const modelY = model.get('y');

      // Inverse mapping from user coordinates to pixel coordinates
      currentX = radius * (2 * (modelX - x_min) / (x_max - x_min) - 1);
      currentY = -radius * (2 * (modelY - y_min) / (y_max - y_min) - 1); // Y is inverted
      
      if (!isDragging) {
        drawSlider();
      }
  }

  function handleMouseDown(event) {
      isDragging = true;
      handleMouseMove(event);
  }

  function handleMouseMove(event) {
      if (isDragging) {
          currentX = event.offsetX - centerX;
          currentY = event.offsetY - centerY;
          currentX = Math.max(-radius, Math.min(radius, currentX));
          currentY = Math.max(-radius, Math.min(radius, currentY));
          drawSlider();
      }
  }

  function handleMouseUp() {
      isDragging = false;
  }

  canvas.addEventListener('mousedown', handleMouseDown);
  canvas.addEventListener('mousemove', handleMouseMove);
  document.addEventListener('mouseup', handleMouseUp);

  model.on("change:x", syncFromModel);
  model.on("change:y", syncFromModel);
  model.on("change:x_bounds", syncFromModel);
  model.on("change:y_bounds", syncFromModel);
  
  syncFromModel();
}

export default { render };
