import { createRender, useModelState } from "@anywidget/react";
import React, { useRef, useState, useEffect } from 'react';

const MAX_UNDO_STEPS = 20;

function Component() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [color, setColor] = useState('#000000');
  const [tool, setTool] = useState('brush');
  let [base64, setBase64] = useModelState<string>("base64");
  let [height] = useModelState<number>("height");
  let [width] = useModelState<number>("width");
  let [storeBackground] = useModelState<boolean>("store_background");

  const originalImageRef = useRef<string>("");
  const lastLoadedBase64Ref = useRef<string>("");
  const isLoadingRef = useRef(false);
  const [exportTrigger, setExportTrigger] = useState(0);
  const undoStackRef = useRef<ImageData[]>([]);
  const [undoCount, setUndoCount] = useState(0);

  // Capture the original base64 once on mount
  useEffect(() => {
    originalImageRef.current = base64;
  }, []);

  const getContext = () => canvasRef.current?.getContext('2d') ?? null;

  // Clear undo stack when dimensions change
  useEffect(() => {
    undoStackRef.current = [];
    setUndoCount(0);
  }, [width, height]);

  // Touch events
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const touchStart = (e: TouchEvent) => {
      e.preventDefault();
      const t = e.touches[0];
      const r = canvas.getBoundingClientRect();
      startDrawingAt(t.clientX - r.left, t.clientY - r.top);
    };
    const touchMove = (e: TouchEvent) => {
      e.preventDefault();
      const t = e.touches[0];
      const r = canvas.getBoundingClientRect();
      drawAt(t.clientX - r.left, t.clientY - r.top);
    };
    const touchEnd = (e: TouchEvent) => {
      e.preventDefault();
      stopDrawing();
    };

    canvas.addEventListener('touchstart', touchStart, { passive: false });
    canvas.addEventListener('touchmove', touchMove, { passive: false });
    canvas.addEventListener('touchend', touchEnd, { passive: false });

    return () => {
      canvas.removeEventListener('touchstart', touchStart);
      canvas.removeEventListener('touchmove', touchMove);
      canvas.removeEventListener('touchend', touchEnd);
    };
  }, []);

  // Load initial/updated image
  useEffect(() => {
    const ctx = getContext();
    if (!ctx || !canvasRef.current || !base64) return;
    if (width === 0 || height === 0) return;

    if (base64 === lastLoadedBase64Ref.current) {
      const canvas = canvasRef.current;
      if (canvas.width > 0 && canvas.height > 0) {
        try {
          const data = ctx.getImageData(0, 0, canvas.width, canvas.height);
          if (data.data.some(p => p !== 0)) return;
        } catch {}
      }
    }

    isLoadingRef.current = true;
    const img = new Image();
    img.onload = () => {
      ctx.clearRect(0, 0, canvasRef.current!.width, canvasRef.current!.height);
      ctx.drawImage(img, 0, 0, canvasRef.current!.width, canvasRef.current!.height);
      lastLoadedBase64Ref.current = base64;
      isLoadingRef.current = false;
    };
    img.onerror = () => { isLoadingRef.current = false; };
    img.src = `data:image/png;base64,${base64}`;
  }, [base64, width, height]);

  // Export on trigger
  useEffect(() => {
    if (!canvasRef.current || exportTrigger === 0 || isLoadingRef.current) return;

    const exportCanvas = document.createElement('canvas');
    exportCanvas.width = canvasRef.current.width;
    exportCanvas.height = canvasRef.current.height;
    const exportCtx = exportCanvas.getContext('2d', { alpha: true });
    if (!exportCtx) return;

    exportCtx.clearRect(0, 0, exportCanvas.width, exportCanvas.height);

    if (storeBackground) {
      exportCtx.fillStyle = '#FFFFFF';
      exportCtx.fillRect(0, 0, exportCanvas.width, exportCanvas.height);
    }

    exportCtx.globalCompositeOperation = 'source-over';
    exportCtx.drawImage(canvasRef.current, 0, 0);

    try {
      const dataUrl = exportCanvas.toDataURL('image/png');
      setBase64(dataUrl.split(',')[1]);
    } catch {}
  }, [storeBackground, width, height, exportTrigger]);

  // Save undo snapshot before a stroke
  const saveUndoSnapshot = () => {
    const ctx = getContext();
    const canvas = canvasRef.current;
    if (!ctx || !canvas || canvas.width === 0 || canvas.height === 0) return;

    const snapshot = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const stack = undoStackRef.current;
    if (stack.length >= MAX_UNDO_STEPS) stack.shift();
    stack.push(snapshot);
    setUndoCount(stack.length);
  };

  const handleUndo = () => {
    const ctx = getContext();
    const canvas = canvasRef.current;
    if (!ctx || !canvas) return;

    const snapshot = undoStackRef.current.pop();
    if (!snapshot) return;

    ctx.putImageData(snapshot, 0, 0);
    setUndoCount(undoStackRef.current.length);
    setExportTrigger(prev => prev + 1);
  };

  const handleClear = () => {
    const ctx = getContext();
    const canvas = canvasRef.current;
    if (!ctx || !canvas) return;

    // Save current state so clear is undoable
    saveUndoSnapshot();
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (originalImageRef.current) {
      isLoadingRef.current = true;
      const img = new Image();
      img.onload = () => {
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        isLoadingRef.current = false;
        setExportTrigger(prev => prev + 1);
      };
      img.onerror = () => {
        isLoadingRef.current = false;
        setExportTrigger(prev => prev + 1);
      };
      img.src = `data:image/png;base64,${originalImageRef.current}`;
    } else {
      setExportTrigger(prev => prev + 1);
    }
  };

  const startDrawingAt = (x: number, y: number) => {
    const ctx = getContext();
    if (!ctx) return;
    saveUndoSnapshot();
    ctx.beginPath();
    ctx.moveTo(x, y);
    setIsDrawing(true);
  };

  const drawAt = (x: number, y: number) => {
    if (!isDrawing) return;
    const ctx = getContext();
    if (!ctx) return;

    ctx.lineTo(x, y);

    if (tool === 'eraser') {
      ctx.save();
      ctx.globalCompositeOperation = 'destination-out';
      ctx.strokeStyle = '#000000';
      ctx.lineWidth = 20;
      ctx.lineCap = 'round';
      ctx.stroke();
      ctx.restore();
    } else {
      ctx.strokeStyle = color;
      ctx.lineWidth = tool === 'marker' ? 8 : 2;
      ctx.lineCap = 'round';
      ctx.stroke();
    }
  };

  const stopDrawing = () => {
    if (!isDrawing) return;
    setExportTrigger(prev => prev + 1);
    setIsDrawing(false);
  };

  const onMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const r = e.currentTarget.getBoundingClientRect();
    startDrawingAt(e.clientX - r.left, e.clientY - r.top);
  };

  const onMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const r = e.currentTarget.getBoundingClientRect();
    drawAt(e.clientX - r.left, e.clientY - r.top);
  };

  const canvasBg = storeBackground
    ? '#ffffff'
    : 'repeating-conic-gradient(#d0d0d0 0% 25%, #f0f0f0 0% 50%) 0 0 / 16px 16px';

  return (
    <div className="paint-container" style={{ width: `${width}px` }}>
      <div className="paint-toolbar">
        <div className="paint-tool-group">
          <button
            className={tool === 'brush' ? 'active' : ''}
            onClick={() => setTool('brush')}
            title="Brush (thin)"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="m21.174 6.812-3.524-3.524-2.197 2.197 3.524 3.524z"/>
              <path d="m14.264 6.674-8.884 8.886a1.5 1.5 0 0 0-.398.725L3.5 22.5l6.215-1.482a1.5 1.5 0 0 0 .725-.398l8.884-8.886"/>
            </svg>
          </button>
          <button
            className={tool === 'marker' ? 'active' : ''}
            onClick={() => setTool('marker')}
            title="Marker (thick)"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M15.707 4.293a1 1 0 0 1 1.414 0l2.586 2.586a1 1 0 0 1 0 1.414L8.414 19.586a2 2 0 0 1-.829.525l-5.085 1.695 1.695-5.085a2 2 0 0 1 .525-.829z"/>
              <path d="m13 6 5 5"/>
            </svg>
          </button>
          <button
            className={tool === 'eraser' ? 'active' : ''}
            onClick={() => setTool('eraser')}
            title="Eraser"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="m7 21-4.3-4.3c-1-1-1-2.5 0-3.4l9.6-9.6c1-1 2.5-1 3.4 0l5.6 5.6c1 1 1 2.5 0 3.4L13 21"/>
              <path d="M22 21H7"/>
              <path d="m5 11 9 9"/>
            </svg>
          </button>
        </div>

        <div className="paint-divider" />

        <div className="paint-action-group">
          <button
            onClick={handleUndo}
            disabled={undoCount === 0}
            title="Undo"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 7v6h6"/>
              <path d="M21 17a9 9 0 0 0-9-9 9 9 0 0 0-6 2.3L3 13"/>
            </svg>
          </button>
          <button onClick={handleClear} title="Clear">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 6h18"/>
              <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/>
              <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
            </svg>
          </button>
        </div>

        <div className="paint-divider" />

        <input
          type="color"
          value={color}
          onChange={e => setColor(e.target.value)}
          title="Color"
        />
      </div>

      <div className="paint-canvas-area" style={{ background: canvasBg }}>
        <canvas
          ref={canvasRef}
          width={width}
          height={height}
          onMouseDown={onMouseDown}
          onMouseMove={onMouseMove}
          onMouseUp={stopDrawing}
          onMouseLeave={stopDrawing}
        />
      </div>
    </div>
  );
}

const render = createRender(Component);

export default { render };
