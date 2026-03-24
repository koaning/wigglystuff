function render({ model, el }) {
  const wrapper = document.createElement("div");
  wrapper.classList.add("hover-zoom-wrapper");

  const sourceContainer = document.createElement("div");
  sourceContainer.classList.add("hover-zoom-source");

  const img = document.createElement("img");
  img.classList.add("hover-zoom-img");
  img.draggable = false;

  const rect = document.createElement("div");
  rect.classList.add("hover-zoom-rect");

  const zoomPanel = document.createElement("div");
  zoomPanel.classList.add("hover-zoom-panel");

  sourceContainer.appendChild(img);
  sourceContainer.appendChild(rect);
  wrapper.appendChild(sourceContainer);
  wrapper.appendChild(zoomPanel);
  el.appendChild(wrapper);

  let pinned = false;

  function updateImage() {
    const src = model.get("image");
    img.src = src || "";
    zoomPanel.style.backgroundImage = src ? `url(${src})` : "none";
  }

  function updateSize() {
    const w = model.get("width");
    const h = model.get("height");
    img.style.width = w + "px";
    img.style.height = h > 0 ? h + "px" : "auto";
    sourceContainer.style.width = w + "px";
  }

  function updateZoom() {
    const zf = model.get("zoom_factor");
    const imgW = img.naturalWidth || img.offsetWidth;
    const imgH = img.naturalHeight || img.offsetHeight;
    zoomPanel.style.backgroundSize = (imgW * zf) + "px " + (imgH * zf) + "px";
  }

  function layoutPanel() {
    const displayH = img.offsetHeight || img.naturalHeight || 300;
    zoomPanel.style.width = displayH + "px";
    zoomPanel.style.height = displayH + "px";
    updateZoom();
  }

  function positionZoom(mouseX, mouseY) {
    const bounds = img.getBoundingClientRect();
    const imgW = bounds.width;
    const imgH = bounds.height;

    const zf = model.get("zoom_factor");
    const panelW = zoomPanel.offsetWidth;
    const panelH = zoomPanel.offsetHeight;

    const rectW = panelW / zf;
    const rectH = panelH / zf;

    let rectLeft = mouseX - rectW / 2;
    let rectTop = mouseY - rectH / 2;
    rectLeft = Math.max(0, Math.min(rectLeft, imgW - rectW));
    rectTop = Math.max(0, Math.min(rectTop, imgH - rectH));

    rect.style.width = rectW + "px";
    rect.style.height = rectH + "px";
    rect.style.left = rectLeft + "px";
    rect.style.top = rectTop + "px";

    const ratioX = rectLeft / imgW;
    const ratioY = rectTop / imgH;
    const ratioW = rectW / imgW;
    const ratioH = rectH / imgH;
    const bgW = imgW * zf;
    const bgH = imgH * zf;

    zoomPanel.style.backgroundPosition = -(ratioX * bgW) + "px " + -(ratioY * bgH) + "px";
    zoomPanel.style.backgroundSize = bgW + "px " + bgH + "px";

    // Sync crop region to Python as [x0, y0, x1, y1] ratios
    model.set("_crop", [ratioX, ratioY, ratioX + ratioW, ratioY + ratioH]);
    model.save_changes();
  }

  function showZoom() {
    rect.style.display = "block";
    zoomPanel.style.display = "block";
    layoutPanel();
  }

  function hideZoom() {
    rect.style.display = "none";
    zoomPanel.style.display = "none";
  }

  img.onload = function () {
    layoutPanel();
  };

  sourceContainer.addEventListener("mouseenter", function () {
    showZoom();
  });

  sourceContainer.addEventListener("mouseleave", function () {
    if (!pinned) {
      hideZoom();
    }
  });

  sourceContainer.addEventListener("mousemove", function (e) {
    if (pinned) return;
    const bounds = img.getBoundingClientRect();
    positionZoom(e.clientX - bounds.left, e.clientY - bounds.top);
  });

  // Double-click to pin the zoom at the current position
  sourceContainer.addEventListener("dblclick", function (e) {
    e.preventDefault();
    pinned = true;
    rect.classList.add("hover-zoom-rect--pinned");
    showZoom();
    const bounds = img.getBoundingClientRect();
    positionZoom(e.clientX - bounds.left, e.clientY - bounds.top);
  });

  // Single click to unpin and resume following
  sourceContainer.addEventListener("click", function (e) {
    if (!pinned) return;
    pinned = false;
    rect.classList.remove("hover-zoom-rect--pinned");
  });

  updateImage();
  updateSize();

  model.on("change:image", updateImage);
  model.on("change:width", function () { updateSize(); layoutPanel(); });
  model.on("change:height", function () { updateSize(); layoutPanel(); });
  model.on("change:zoom_factor", updateZoom);
}

export default { render };
