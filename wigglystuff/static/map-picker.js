/**
 * MapPicker anywidget - Interactive map for picking coordinates
 * Uses OpenStreetMap tiles
 */

const TILE_SIZE = 256;

// Web Mercator utilities
function lon2tile(lon, zoom) {
    return ((lon + 180) / 360) * Math.pow(2, zoom);
}

function lat2tile(lat, zoom) {
    return (
        ((1 -
            Math.log(
                Math.tan((lat * Math.PI) / 180) +
                    1 / Math.cos((lat * Math.PI) / 180)
            ) /
                Math.PI) /
            2) *
        Math.pow(2, zoom)
    );
}

function tile2lon(x, zoom) {
    return (x / Math.pow(2, zoom)) * 360 - 180;
}

function tile2lat(y, zoom) {
    const n = Math.PI - (2 * Math.PI * y) / Math.pow(2, zoom);
    return (180 / Math.PI) * Math.atan(0.5 * (Math.exp(n) - Math.exp(-n)));
}

function render({ model, el }) {
    // Container
    const container = document.createElement("div");
    container.className = "map-picker-container";
    container.style.width = "100%";
    container.style.height = "100%";
    container.style.minHeight = "300px";
    container.style.borderRadius = "12px";
    container.style.overflow = "hidden";
    container.style.boxShadow = "0 4px 12px rgba(0, 0, 0, 0.15)";
    container.style.position = "relative";
    container.style.background = "#ddd";

    // Canvas
    const canvas = document.createElement("canvas");
    canvas.style.display = "block";
    canvas.style.width = "100%";
    canvas.style.height = "100%";
    canvas.style.cursor = "grab";
    container.appendChild(canvas);

    const ctx = canvas.getContext("2d");

    // Floor shadow (for marker)
    const shadow = document.createElement("div");
    shadow.className = "picker-shadow";
    shadow.style.cssText = `
        position: absolute;
        top: 50%;
        left: 50%;
        width: 8px;
        height: 4px;
        background: rgba(0, 0, 0, 0.3);
        border-radius: 50%;
        transform: translate(-50%, -50%);
        z-index: 10;
        pointer-events: none;
        transition: transform 0.2s, opacity 0.2s;
        display: none;
    `;
    container.appendChild(shadow);

    // Pin (marker)
    const markerColor = model.get("marker_color") || "#3b82f6";
    const pin = document.createElement("div");
    pin.className = "picker-pin";
    pin.style.cssText = `
        position: absolute;
        top: 50%;
        left: 50%;
        width: 36px;
        height: 36px;
        transform: translate(-50%, -100%);
        z-index: 20;
        pointer-events: none;
        transition: transform 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        display: none;
    `;
    pin.innerHTML = `
        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="width: 100%; height: 100%; fill: ${markerColor}; stroke: #ffffff; stroke-width: 2px; filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));">
            <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
            <circle cx="12" cy="9" r="2.5" fill="white" stroke="none"/>
        </svg>
    `;
    container.appendChild(pin);

    // Show/hide marker based on model
    function updateMarkerVisibility() {
        const show = model.get("show_marker");
        pin.style.display = show ? "block" : "none";
        shadow.style.display = show ? "block" : "none";
    }
    updateMarkerVisibility();

    // Minimal attribution
    const attribution = document.createElement("div");
    attribution.style.cssText = `
        position: absolute;
        bottom: 4px;
        right: 6px;
        font-size: 8px;
        color: rgba(0, 0, 0, 0.5);
        pointer-events: none;
        font-family: sans-serif;
    `;
    attribution.textContent = "\u00A9 OSM";
    container.appendChild(attribution);

    el.appendChild(container);

    // State
    let state = {
        lat: model.get("lat"),
        lon: model.get("lon"),
        zoom: model.get("zoom"),
        targetZoom: model.get("zoom"),
        width: 400,
        height: 300,
    };

    const tileCache = new Map();
    let isDragging = false;
    let lastX, lastY;
    let animationId = null;

    function getTileImage(key, z, x, y) {
        if (tileCache.has(key)) return tileCache.get(key);

        const img = new Image();
        img.crossOrigin = "Anonymous";
        img.src = `https://tile.openstreetmap.org/${z}/${x}/${y}.png`;
        img.onload = () => requestAnimationFrame(renderMap);

        tileCache.set(key, img);

        if (tileCache.size > 150) {
            const first = tileCache.keys().next().value;
            tileCache.delete(first);
        }
        return img;
    }

    function renderMap() {
        // Animation physics
        const lerpSpeed = 0.1;
        const diff = state.targetZoom - state.zoom;

        if (Math.abs(diff) > 0.001) {
            state.zoom += diff * lerpSpeed;
            animationId = requestAnimationFrame(renderMap);
        } else {
            state.zoom = state.targetZoom;
            animationId = null;
        }

        // Fractional zoom
        const intZoom = Math.floor(state.zoom);
        const zoomFraction = state.zoom - intZoom;
        const scale = Math.pow(2, zoomFraction);
        const displayedTileSize = TILE_SIZE * scale;

        // Clear
        ctx.fillStyle = "#e5e5e5";
        ctx.fillRect(0, 0, state.width, state.height);

        // Center in world pixels
        const centerTileX = lon2tile(state.lon, intZoom);
        const centerTileY = lat2tile(state.lat, intZoom);
        const centerPixelX = centerTileX * displayedTileSize;
        const centerPixelY = centerTileY * displayedTileSize;

        // Viewport
        const halfW = state.width / 2;
        const halfH = state.height / 2;
        const leftWorldPixel = centerPixelX - halfW;
        const topWorldPixel = centerPixelY - halfH;

        // Visible tile range
        const startCol = Math.floor(leftWorldPixel / displayedTileSize);
        const endCol = Math.floor((leftWorldPixel + state.width) / displayedTileSize) + 1;
        const startRow = Math.floor(topWorldPixel / displayedTileSize);
        const endRow = Math.floor((topWorldPixel + state.height) / displayedTileSize) + 1;

        // Draw tiles
        for (let x = startCol; x < endCol; x++) {
            for (let y = startRow; y < endRow; y++) {
                const maxTiles = Math.pow(2, intZoom);
                const wrappedX = ((x % maxTiles) + maxTiles) % maxTiles;

                if (y < 0 || y >= maxTiles) continue;

                const tileKey = `${intZoom}/${wrappedX}/${y}`;
                const drawX = x * displayedTileSize - leftWorldPixel;
                const drawY = y * displayedTileSize - topWorldPixel;

                const img = getTileImage(tileKey, intZoom, wrappedX, y);

                if (img.complete && img.naturalWidth !== 0) {
                    ctx.drawImage(img, drawX, drawY, displayedTileSize, displayedTileSize);
                } else {
                    ctx.strokeStyle = "#ddd";
                    ctx.strokeRect(drawX, drawY, displayedTileSize, displayedTileSize);
                }
            }
        }
    }

    function computeBbox() {
        const halfW = state.width / 2;
        const halfH = state.height / 2;
        
        const centerTileX = lon2tile(state.lon, state.zoom);
        const centerTileY = lat2tile(state.lat, state.zoom);
        
        const tilesPerPixel = 1 / TILE_SIZE;
        
        const westTile = centerTileX - halfW * tilesPerPixel;
        const eastTile = centerTileX + halfW * tilesPerPixel;
        const northTile = centerTileY - halfH * tilesPerPixel;
        const southTile = centerTileY + halfH * tilesPerPixel;
        
        return [
            tile2lon(westTile, state.zoom),
            tile2lat(southTile, state.zoom),
            tile2lon(eastTile, state.zoom),
            tile2lat(northTile, state.zoom)
        ];
    }

    function syncToModel() {
        model.set("lat", state.lat);
        model.set("lon", state.lon);
        model.set("zoom", state.zoom);
        model.set("bbox", computeBbox());
        model.save_changes();
    }

    function resize() {
        const rect = container.getBoundingClientRect();
        if (rect.width > 0 && rect.height > 0) {
            state.width = rect.width;
            state.height = rect.height;
            canvas.width = rect.width;
            canvas.height = rect.height;
            syncToModel();
            renderMap();
        }
    }

    // Event handlers
    canvas.addEventListener("mousedown", (e) => {
        isDragging = true;
        lastX = e.clientX;
        lastY = e.clientY;
        canvas.style.cursor = "grabbing";
        if (model.get("show_marker")) {
            pin.style.transform = "translate(-50%, -130%)";
            shadow.style.opacity = "0.6";
            shadow.style.transform = "translate(-50%, -50%) scale(0.8)";
        }
    });

    window.addEventListener("mouseup", () => {
        if (isDragging) {
            isDragging = false;
            canvas.style.cursor = "grab";
            if (model.get("show_marker")) {
                pin.style.transform = "translate(-50%, -100%)";
                shadow.style.opacity = "1";
                shadow.style.transform = "translate(-50%, -50%)";
            }
            syncToModel();
        }
    });

    window.addEventListener("mousemove", (e) => {
        if (!isDragging) return;

        const dx = e.clientX - lastX;
        const dy = e.clientY - lastY;

        const centerTileX = lon2tile(state.lon, state.zoom);
        const centerTileY = lat2tile(state.lat, state.zoom);

        const newTileX = centerTileX - dx / TILE_SIZE;
        const newTileY = centerTileY - dy / TILE_SIZE;

        state.lon = tile2lon(newTileX, state.zoom);
        state.lat = tile2lat(newTileY, state.zoom);

        // Clamp values
        state.lat = Math.max(-85, Math.min(85, state.lat));
        state.lon = ((state.lon + 180) % 360 + 360) % 360 - 180;

        lastX = e.clientX;
        lastY = e.clientY;

        syncToModel();
        requestAnimationFrame(renderMap);
    });

    // Double-click to zoom
    canvas.addEventListener("dblclick", (e) => {
        e.preventDefault();
        if (e.shiftKey) {
            state.targetZoom = Math.max(state.targetZoom - 1, 2);
        } else {
            state.targetZoom = Math.min(state.targetZoom + 1, 19);
        }
        syncToModel();
        if (!animationId) animationId = requestAnimationFrame(renderMap);
    });

    // Wheel zoom
    function handleWheel(e) {
        e.preventDefault();
        e.stopImmediatePropagation();
        
        const sensitivity = 0.1;
        if (e.deltaY < 0) {
            state.targetZoom = Math.min(state.targetZoom + sensitivity, 19);
        } else {
            state.targetZoom = Math.max(state.targetZoom - sensitivity, 2);
        }
        
        state.zoom = state.targetZoom;

        syncToModel();
        renderMap();
        
        return false;
    }
    
    el.onwheel = handleWheel;
    container.onwheel = handleWheel;
    canvas.onwheel = handleWheel;

    // Model change handlers
    model.on("change:lat", () => {
        if (!isDragging) {
            state.lat = model.get("lat");
            requestAnimationFrame(renderMap);
        }
    });

    model.on("change:lon", () => {
        if (!isDragging) {
            state.lon = model.get("lon");
            requestAnimationFrame(renderMap);
        }
    });

    model.on("change:zoom", () => {
        if (!isDragging) {
            state.targetZoom = model.get("zoom");
            state.zoom = model.get("zoom");
            requestAnimationFrame(renderMap);
        }
    });

    model.on("change:show_marker", updateMarkerVisibility);
    
    model.on("change:marker_color", () => {
        const color = model.get("marker_color");
        pin.querySelector("svg").style.fill = color;
    });

    // ResizeObserver
    const resizeObserver = new ResizeObserver(() => {
        resize();
    });
    resizeObserver.observe(container);

    setTimeout(resize, 0);

    return () => {
        if (animationId) {
            cancelAnimationFrame(animationId);
        }
        resizeObserver.disconnect();
    };
}

export default { render };
