function render({ model, el }) {
  const root = document.createElement("div");
  root.className = "webcam-capture";

  const header = document.createElement("div");
  header.className = "webcam-capture__header";

  const title = document.createElement("div");
  title.className = "webcam-capture__title";
  title.textContent = "Webcam";

  const status = document.createElement("div");
  status.className = "webcam-capture__status";

  header.appendChild(title);
  header.appendChild(status);

  const videoWrap = document.createElement("div");
  videoWrap.className = "webcam-capture__video";

  const video = document.createElement("video");
  video.autoplay = true;
  video.playsInline = true;
  video.muted = true;
  videoWrap.appendChild(video);

  const controls = document.createElement("div");
  controls.className = "webcam-capture__controls";

  const captureButton = document.createElement("button");
  captureButton.type = "button";
  captureButton.className = "webcam-capture__button";
  captureButton.textContent = "Capture";

  const toggleWrap = document.createElement("label");
  toggleWrap.className = "webcam-capture__toggle";

  const toggleInput = document.createElement("input");
  toggleInput.type = "checkbox";

  const toggleLabel = document.createElement("span");
  toggleLabel.textContent = "Auto-capture";

  toggleWrap.appendChild(toggleInput);
  toggleWrap.appendChild(toggleLabel);

  controls.appendChild(captureButton);
  controls.appendChild(toggleWrap);

  root.appendChild(header);
  root.appendChild(videoWrap);
  root.appendChild(controls);
  el.appendChild(root);

  let stream = null;
  let intervalId = null;
  let streamRequestId = 0;

  const setStatus = (text, tone) => {
    status.textContent = text;
    status.dataset.tone = tone || "neutral";
  };

  const stopInterval = () => {
    if (intervalId) {
      clearInterval(intervalId);
      intervalId = null;
    }
  };

  const applyCapturingState = () => {
    const isCapturing = model.get("capturing");
    toggleInput.checked = Boolean(isCapturing);
    stopInterval();
    if (isCapturing) {
      const intervalMs = Math.max(0, model.get("interval_ms") || 1000);
      intervalId = setInterval(() => {
        captureFrame(false);
      }, intervalMs);
      setStatus(`Auto-capture on`, "active");
    } else if (model.get("error")) {
      setStatus(model.get("error"), "error");
    } else if (model.get("ready")) {
      setStatus("Preview ready", "ready");
    }
  };

  const captureFrame = (manual) => {
    if (!stream || video.videoWidth === 0 || video.videoHeight === 0) {
      return;
    }
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) {
      return;
    }
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const dataUrl = canvas.toDataURL("image/png");
    model.set("image_base64", dataUrl);
    model.save_changes();
    if (manual && model.get("capturing")) {
      model.set("capturing", false);
      model.save_changes();
      stopInterval();
    }
  };

  const stopStream = () => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      stream = null;
    }
  };

  const invalidateStreamRequest = () => {
    streamRequestId += 1;
    return streamRequestId;
  };

  const startStream = async () => {
    const requestId = invalidateStreamRequest();
    stopStream();
    setStatus("Requesting access...", "pending");
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error("Webcam access is not available in this environment.");
      }
      const facingMode = model.get("facing_mode") || "user";
      const constraints = {
        video: { facingMode: { ideal: facingMode } },
        audio: false,
      };
      const nextStream = await navigator.mediaDevices.getUserMedia(constraints);
      if (requestId !== streamRequestId) {
        nextStream.getTracks().forEach((track) => track.stop());
        return;
      }
      stream = nextStream;
      video.srcObject = stream;
      model.set("ready", true);
      model.set("error", "");
      model.save_changes();
      setStatus("Preview ready", "ready");
      applyCapturingState();
    } catch (err) {
      if (requestId !== streamRequestId) {
        return;
      }
      const message = err && err.message ? err.message : "Unable to access webcam.";
      model.set("ready", false);
      model.set("error", message);
      model.save_changes();
      setStatus(message, "error");
    }
  };

  captureButton.addEventListener("click", () => captureFrame(true));

  toggleInput.addEventListener("change", () => {
    model.set("capturing", toggleInput.checked);
    model.save_changes();
    applyCapturingState();
  });

  const onCapturingChange = () => applyCapturingState();
  const onIntervalChange = () => {
    if (model.get("capturing")) {
      applyCapturingState();
    }
  };
  const onFacingChange = () => {
    startStream();
  };
  const onErrorChange = () => {
    if (!model.get("capturing") && model.get("error")) {
      setStatus(model.get("error"), "error");
    }
  };

  model.on("change:capturing", onCapturingChange);
  model.on("change:interval_ms", onIntervalChange);
  model.on("change:facing_mode", onFacingChange);
  model.on("change:error", onErrorChange);

  setStatus("Starting preview...", "pending");
  startStream();

  return () => {
    stopInterval();
    invalidateStreamRequest();
    stopStream();
    model.off("change:capturing", onCapturingChange);
    model.off("change:interval_ms", onIntervalChange);
    model.off("change:facing_mode", onFacingChange);
    model.off("change:error", onErrorChange);
  };
}

export default { render };
