import {
  AmbientLight,
  AxesHelper,
  Box3,
  BufferGeometry,
  Color,
  DirectionalLight,
  Float32BufferAttribute,
  GridHelper,
  PerspectiveCamera,
  Points,
  PointsMaterial,
  Scene,
  Vector3,
  WebGLRenderer
} from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";

function render({ model, el }) {
  el.classList.add("three-widget-root");
  const container = document.createElement("div");
  container.className = "three-widget-container";
  container.style.position = "relative";
  el.appendChild(container);

  let darkMode = model.get("dark_mode");

  const scene = new Scene();
  scene.background = new Color(darkMode ? 1710618 : 16777215);

  const camera = new PerspectiveCamera(75, 1, 0.1, 1e3);
  camera.position.set(4, 4, 4);

  const renderer = new WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(window.devicePixelRatio || 1);
  container.appendChild(renderer.domElement);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.05;
  controls.autoRotate = model.get("auto_rotate");
  controls.autoRotateSpeed = model.get("auto_rotate_speed");

  let userHasInteracted = false;
  controls.addEventListener("start", () => {
    userHasInteracted = true;
    controls.autoRotate = false;
    model.set("auto_rotate", false);
    model.save_changes();
  });

  const ambientLight = new AmbientLight(16777215, darkMode ? 0.4 : 0.6);
  scene.add(ambientLight);

  const directionalLight = new DirectionalLight(16777215, darkMode ? 0.6 : 0.8);
  directionalLight.position.set(10, 10, 10);
  scene.add(directionalLight);

  let gridHelper = null;
  let axesHelper = null;
  let chartObjects = [];
  let points = null;
  let geometry = null;
  let material = null;
  let updateAnimationId = null;
  let currentPositions = null;
  let currentColors = null;
  let currentSizes = null;
  let containerWidth = 1;
  let containerHeight = 1;
  let axisLabelsVisible = false;
  let axisLabels = [];

  const plotBounds = new Box3(new Vector3(-1, -1, -1), new Vector3(1, 1, 1));
  const plotCenter = new Vector3();
  const plotSize = new Vector3(2, 2, 2);
  const axisOrigin = new Vector3();
  const axisLengths = new Vector3(1, 1, 1);
  const labelTargets = {
    x: new Vector3(),
    y: new Vector3(),
    z: new Vector3()
  };
  const labelProjector = new Vector3();
  const cameraOffset = new Vector3(1, 1, 1).normalize();
  const axisLabelElements = {
    x: null,
    y: null,
    z: null
  };

  function disposeHelper(helper) {
    if (!helper) {
      return;
    }

    scene.remove(helper);

    if (helper.geometry) {
      helper.geometry.dispose();
    }

    if (helper.material) {
      if (Array.isArray(helper.material)) {
        helper.material.forEach((material) => material.dispose());
      } else {
        helper.material.dispose();
      }
    }
  }

  function updateSizing() {
    const width = model.get("width");
    const height = model.get("height");

    container.style.width = `${width}px`;
    container.style.height = `${height}px`;
    containerWidth = width;
    containerHeight = height;

    camera.aspect = width / height;
    camera.updateProjectionMatrix();

    renderer.setSize(width, height);
    updateAxisLabelPositions();
  }

  function updateGrid() {
    const showGrid = model.get("show_grid");

    if (!showGrid) {
      disposeHelper(gridHelper);
      gridHelper = null;
      return;
    }

    disposeHelper(gridHelper);

    const gridSize = Math.max(plotSize.x, plotSize.z, 1);
    const divisions = 10;

    gridHelper = new GridHelper(
      gridSize,
      divisions,
      darkMode ? 6710886 : 8947848,
      darkMode ? 3355443 : 13421772
    );
    gridHelper.position.set(
      axisOrigin.x + plotSize.x / 2,
      axisOrigin.y,
      axisOrigin.z + plotSize.z / 2
    );
    scene.add(gridHelper);
  }

  function updateAxes() {
    const showAxes = model.get("show_axes");

    if (!showAxes) {
      disposeHelper(axesHelper);
      axesHelper = null;
      updateAxisLabels();
      return;
    }

    disposeHelper(axesHelper);

    const axisLength = Math.max(plotSize.x, plotSize.y, plotSize.z, 1);

    axesHelper = new AxesHelper(axisLength);
    axesHelper.scale.set(
      plotSize.x / axisLength,
      plotSize.y / axisLength,
      plotSize.z / axisLength
    );
    axesHelper.position.copy(axisOrigin);
    scene.add(axesHelper);
    updateAxisLabels();
  }

  function ensureAxisLabelElements() {
    if (axisLabelElements.x) {
      return;
    }

    const createLabel = (axis) => {
      const label = document.createElement("div");
      label.className = `three-widget-axis-label axis-${axis}`;
      container.appendChild(label);
      return label;
    };

    axisLabelElements.x = createLabel("x");
    axisLabelElements.y = createLabel("y");
    axisLabelElements.z = createLabel("z");
  }

  function updateAxisLabels() {
    axisLabels = model.get("axis_labels") || [];
    const showAxes = model.get("show_axes");
    const shouldShow = showAxes && axisLabels.length >= 3;

    axisLabelsVisible = shouldShow;

    if (!shouldShow) {
      Object.values(axisLabelElements).forEach((label) => {
        if (label) {
          label.style.display = "none";
        }
      });
      return;
    }

    ensureAxisLabelElements();

    axisLabelElements.x.textContent = axisLabels[0];
    axisLabelElements.y.textContent = axisLabels[1];
    axisLabelElements.z.textContent = axisLabels[2];

    Object.values(axisLabelElements).forEach((label) => {
      label.style.display = "block";
    });
  }

  function updateAxisLabelPositions() {
    if (!axisLabelsVisible || !axisLabelElements.x) {
      return;
    }

    const xOffset = axisLengths.x * 1.05;
    const yOffset = axisLengths.y * 1.05;
    const zOffset = axisLengths.z * 1.05;

    labelTargets.x.set(axisOrigin.x + xOffset, axisOrigin.y, axisOrigin.z);
    labelTargets.y.set(axisOrigin.x, axisOrigin.y + yOffset, axisOrigin.z);
    labelTargets.z.set(axisOrigin.x, axisOrigin.y, axisOrigin.z + zOffset);

    const placeLabel = (element, target) => {
      labelProjector.copy(target).project(camera);
      const x = (labelProjector.x * 0.5 + 0.5) * containerWidth;
      const y = (-labelProjector.y * 0.5 + 0.5) * containerHeight;
      element.style.transform = `translate(-50%, -50%) translate(${x}px, ${y}px)`;
    };

    placeLabel(axisLabelElements.x, labelTargets.x);
    placeLabel(axisLabelElements.y, labelTargets.y);
    placeLabel(axisLabelElements.z, labelTargets.z);
  }

  function updateTheme() {
    darkMode = model.get("dark_mode");

    scene.background = new Color(darkMode ? 1710618 : 16777215);
    ambientLight.intensity = darkMode ? 0.4 : 0.6;
    directionalLight.intensity = darkMode ? 0.6 : 0.8;

    updateGrid();
  }

  function frameCameraToBounds() {
    const maxDim = Math.max(plotSize.x, plotSize.y, plotSize.z, 1);
    const radius =
      0.5 *
      Math.sqrt(plotSize.x * plotSize.x + plotSize.y * plotSize.y + plotSize.z * plotSize.z);
    const fov = (camera.fov * Math.PI) / 180;
    const distance = (radius / Math.sin(fov / 2)) * 1.2;
    const safeDistance = Math.max(distance, maxDim * 0.9);

    camera.position.copy(plotCenter).add(cameraOffset.clone().multiplyScalar(safeDistance));
    camera.near = Math.max(safeDistance / 100, 0.01);
    camera.far = safeDistance * 10;
    camera.updateProjectionMatrix();

    controls.target.copy(plotCenter);
    controls.update();
  }

  function clearChart() {
    if (updateAnimationId) {
      cancelAnimationFrame(updateAnimationId);
      updateAnimationId = null;
    }

    chartObjects.forEach((obj) => {
      scene.remove(obj);

      if (obj.geometry) {
        obj.geometry.dispose();
      }

      if (obj.material) {
        obj.material.dispose();
      }
    });

    chartObjects = [];
    points = null;
    geometry = null;
    material = null;
    currentPositions = null;
    currentColors = null;
    currentSizes = null;
  }

  function applyBuffers(positionArray, colorArray, sizeArray) {
    if (!geometry) {
      return;
    }

    const positionAttr = geometry.getAttribute("position");

    if (!positionAttr || positionAttr.array.length !== positionArray.length) {
      geometry.setAttribute("position", new Float32BufferAttribute(positionArray, 3));
    } else {
      positionAttr.array.set(positionArray);
      positionAttr.needsUpdate = true;
    }

    const colorAttr = geometry.getAttribute("color");

    if (!colorAttr || colorAttr.array.length !== colorArray.length) {
      geometry.setAttribute("color", new Float32BufferAttribute(colorArray, 3));
    } else {
      colorAttr.array.set(colorArray);
      colorAttr.needsUpdate = true;
    }

    const sizeAttr = geometry.getAttribute("size");

    if (!sizeAttr || sizeAttr.array.length !== sizeArray.length) {
      geometry.setAttribute("size", new Float32BufferAttribute(sizeArray, 1));
    } else {
      sizeAttr.array.set(sizeArray);
      sizeAttr.needsUpdate = true;
    }
  }

  function updateChart() {
    const data = model.get("data");
    const positions = [];
    const colors = [];
    const sizes = [];

    let minX = Infinity;
    let minY = Infinity;
    let minZ = Infinity;
    let maxX = -Infinity;
    let maxY = -Infinity;
    let maxZ = -Infinity;

    data.forEach((point) => {
      const rawX = Number(point.x);
      const rawY = Number(point.y);
      const rawZ = Number(point.z);
      const x = Number.isFinite(rawX) ? rawX : 0;
      const y = Number.isFinite(rawY) ? rawY : 0;
      const z = Number.isFinite(rawZ) ? rawZ : 0;

      positions.push(x, y, z);

      minX = Math.min(minX, x);
      minY = Math.min(minY, y);
      minZ = Math.min(minZ, z);

      maxX = Math.max(maxX, x);
      maxY = Math.max(maxY, y);
      maxZ = Math.max(maxZ, z);

      const color = new Color(point.color || "#00ff00");
      colors.push(color.r, color.g, color.b);

      sizes.push(point.size !== void 0 ? point.size : 0.1);
    });

    if (minX === Infinity) {
      minX = -1;
      maxX = 1;
      minY = -1;
      maxY = 1;
      minZ = -1;
      maxZ = 1;
    }

    if (minX === maxX) {
      minX -= 0.5;
      maxX += 0.5;
    }

    if (minY === maxY) {
      minY -= 0.5;
      maxY += 0.5;
    }

    if (minZ === maxZ) {
      minZ -= 0.5;
      maxZ += 0.5;
    }

    plotBounds.min.set(minX, minY, minZ);
    plotBounds.max.set(maxX, maxY, maxZ);
    plotBounds.getSize(plotSize);
    plotBounds.getCenter(plotCenter);

    axisOrigin.copy(plotBounds.min);
    axisLengths.set(plotSize.x, plotSize.y, plotSize.z);

    updateGrid();
    updateAxes();
    updateAxisLabelPositions();

    if (!userHasInteracted) {
      frameCameraToBounds();
    }

    const nextPositions = new Float32Array(positions);
    const nextColors = new Float32Array(colors);
    const nextSizes = new Float32Array(sizes);

    if (
      !points ||
      !geometry ||
      !material ||
      !currentPositions ||
      currentPositions.length !== nextPositions.length
    ) {
      clearChart();

      geometry = new BufferGeometry();
      geometry.setAttribute("position", new Float32BufferAttribute(nextPositions, 3));
      geometry.setAttribute("color", new Float32BufferAttribute(nextColors, 3));
      geometry.setAttribute("size", new Float32BufferAttribute(nextSizes, 1));

      material = new PointsMaterial({
        vertexColors: true,
        sizeAttenuation: true
      });
      material.onBeforeCompile = (shader) => {
        shader.vertexShader = shader.vertexShader.replace(
          "uniform float size;",
          "attribute float size;"
        );
      };

      points = new Points(geometry, material);
      scene.add(points);
      chartObjects.push(points);

      currentPositions = nextPositions;
      currentColors = nextColors;
      currentSizes = nextSizes;

      return;
    }

    const shouldAnimate = model.get("animate_updates");
    const duration = Math.max(0, model.get("animation_duration_ms") || 400);

    if (!shouldAnimate || duration === 0) {
      applyBuffers(nextPositions, nextColors, nextSizes);
      currentPositions = nextPositions;
      currentColors = nextColors;
      currentSizes = nextSizes;
      return;
    }

    if (updateAnimationId) {
      cancelAnimationFrame(updateAnimationId);
      updateAnimationId = null;
    }

    const startPositions = new Float32Array(geometry.getAttribute("position").array);
    const startColors = new Float32Array(geometry.getAttribute("color").array);
    const startSizes = new Float32Array(geometry.getAttribute("size").array);
    const positionAttr = geometry.getAttribute("position");
    const colorAttr = geometry.getAttribute("color");
    const sizeAttr = geometry.getAttribute("size");
    const startTime = performance.now();

    const animateUpdate = (now) => {
      const progress = Math.min((now - startTime) / duration, 1);
      const eased = progress * (2 - progress);

      for (let i = 0; i < positionAttr.array.length; i++) {
        positionAttr.array[i] = startPositions[i] + (nextPositions[i] - startPositions[i]) * eased;
      }

      for (let i = 0; i < colorAttr.array.length; i++) {
        colorAttr.array[i] = startColors[i] + (nextColors[i] - startColors[i]) * eased;
      }

      for (let i = 0; i < sizeAttr.array.length; i++) {
        sizeAttr.array[i] = startSizes[i] + (nextSizes[i] - startSizes[i]) * eased;
      }

      positionAttr.needsUpdate = true;
      colorAttr.needsUpdate = true;
      sizeAttr.needsUpdate = true;

      if (progress < 1) {
        updateAnimationId = requestAnimationFrame(animateUpdate);
      } else {
        updateAnimationId = null;
        currentPositions = nextPositions;
        currentColors = nextColors;
        currentSizes = nextSizes;
      }
    };

    updateAnimationId = requestAnimationFrame(animateUpdate);
  }

  updateSizing();
  updateGrid();
  updateAxes();
  updateChart();

  model.on("change:data", updateChart);
  model.on("change:width", updateSizing);
  model.on("change:height", updateSizing);
  model.on("change:show_grid", updateGrid);
  model.on("change:show_axes", updateAxes);
  model.on("change:dark_mode", updateTheme);
  model.on("change:axis_labels", () => {
    updateAxisLabels();
    updateAxisLabelPositions();
  });
  model.on("change:auto_rotate", () => {
    const shouldRotate = model.get("auto_rotate");
    if (shouldRotate) {
      controls.autoRotate = true;
    }
  });
  model.on("change:auto_rotate_speed", () => {
    controls.autoRotateSpeed = model.get("auto_rotate_speed");
  });

  let animationId;

  function animate() {
    animationId = requestAnimationFrame(animate);
    controls.update();
    updateAxisLabelPositions();
    renderer.render(scene, camera);
  }

  animate();

  return () => {
    cancelAnimationFrame(animationId);
    clearChart();
    disposeHelper(gridHelper);
    disposeHelper(axesHelper);
    renderer.dispose();
    controls.dispose();
  };
}

export default { render };
