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
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" fill="currentColor">
              <path d="m63.688 6c-0.56641 0.089844-1.0664 0.42188-1.375 0.90625l-34 52c-0.20703 0.32812-0.31641 0.70703-0.3125 1.0938v7.4375l-6.7188 11.531c-0.1875 0.3125-0.28125 0.66797-0.28125 1.0312v12c0.003906 0.67578 0.35156 1.3008 0.91797 1.6641 0.56641 0.36719 1.2773 0.42188 1.8945 0.14844l11-5c0.39844-0.17969 0.73047-0.48828 0.9375-0.875l6.8125-12.625 5.7188-4.7812c0.21094-0.17969 0.37891-0.40625 0.5-0.65625l19.156-39c0.25781-0.48047 0.30859-1.043 0.14062-1.5625-0.16797-0.51562-0.53906-0.94531-1.0273-1.1836-0.48828-0.23828-1.0547-0.26562-1.5664-0.078125-0.50781 0.1875-0.92188 0.57422-1.1406 1.0742l-18.219 37.125-13.25-6.9688 27.062-41.375 14.469 8.8438-12.219 25.375c-0.23047 0.48047-0.25781 1.0352-0.082031 1.5352 0.17969 0.50391 0.55078 0.91406 1.0312 1.1445 0.48438 0.22656 1.0352 0.25391 1.5391 0.074218 0.5-0.17969 0.91016-0.55078 1.1367-1.0352l13-27c0.43359-0.92969 0.097656-2.0352-0.78125-2.5625l-5.25-3.2188 3-6.1875c0.46094-0.92969 0.13281-2.0547-0.75-2.5938l-10-6c-0.40234-0.25-0.875-0.34766-1.3438-0.28125zm0.96875 4.6875 6.75 4.0625-2.0625 4.2188-7.2188-4.4062zm-32.656 52.625 11.406 6.0312-2.625 2.2188-8.7812-4.7812zm-1.25 7.375 7.5312 4.125-5.7188 10.625-7.5625 3.4375v-8.3438zm8.0625 19.312c-0.53125 0.023438-1.0312 0.25781-1.3867 0.65234-0.35938 0.39062-0.54297 0.91016-0.51953 1.4414s0.25781 1.0312 0.65234 1.3867c0.39062 0.35938 0.91016 0.54297 1.4414 0.51953h38c0.53516 0.007812 1.0508-0.19922 1.4336-0.57422 0.37891-0.37891 0.59375-0.89062 0.59375-1.4258s-0.21484-1.0469-0.59375-1.4258c-0.38281-0.375-0.89844-0.58203-1.4336-0.57422h-38c-0.0625-0.003906-0.125-0.003906-0.1875 0z"/>
            </svg>
          </button>
          <button
            className={tool === 'marker' ? 'active' : ''}
            onClick={() => setTool('marker')}
            title="Marker (thick)"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" fill="currentColor">
              <path d="m60.844 7c-0.58594 0.042969-1.1211 0.33984-1.4688 0.8125l-33 46c-0.22266 0.3125-0.35547 0.67969-0.375 1.0625l-1 19c-0.042969 0.77734 0.375 1.5117 1.0625 1.875l0.4375 0.25-8.2188 13.969c-0.37109 0.61719-0.38281 1.3906-0.027344 2.0195 0.35547 0.625 1.0234 1.0117 1.7461 1.0117h10c0.66797-0.007812 1.2891-0.34766 1.6562-0.90625l6.5312-9.8125 0.875 0.46875c0.62891 0.33984 1.3906 0.3125 2-0.0625l16-10c0.32422-0.20312 0.58594-0.49609 0.75-0.84375l24-51c0.44922-0.94531 0.09375-2.0742-0.8125-2.5938l-19-11c-0.35156-0.19922-0.75391-0.28516-1.1562-0.25zm0.71875 4.625 15.844 9.1562-22.312 47.375-24.156-13.812zm0.90625 9.375c-2.3789-0.054688-4.707 1.1719-5.9688 3.375l-10.594 18.5c-1.832 3.2031-0.71875 7.3594 2.4688 9.2188s7.3242 0.76562 9.1562-2.4375l10.562-18.5c1.832-3.2031 0.75-7.3906-2.4375-9.25-0.99609-0.58203-2.1055-0.88281-3.1875-0.90625zm-0.34375 4c0.51953-0.035156 1.0352 0.085938 1.5312 0.375 1.3242 0.77344 1.7734 2.3984 1 3.75l-10.594 18.5c-0.77344 1.3516-2.3633 1.7734-3.6875 1s-1.7734-2.3984-1-3.75l10.562-18.469c0.48438-0.84375 1.3242-1.3477 2.1875-1.4062zm-32.281 33.344 22.25 12.688-12.188 7.625-10.844-5.8438zm0.1875 19.531 4.6562 2.5-5.75 8.625h-5.4688zm8.7812 11.125c-0.53125 0.023438-1.0312 0.25781-1.3867 0.65234-0.35938 0.39062-0.54297 0.91016-0.51953 1.4414s0.25781 1.0312 0.65234 1.3867c0.39062 0.35938 0.91016 0.54297 1.4414 0.51953h28c0.53516 0.007812 1.0508-0.19922 1.4336-0.57422 0.37891-0.37891 0.59375-0.89062 0.59375-1.4258s-0.21484-1.0469-0.59375-1.4258c-0.38281-0.375-0.89844-0.58203-1.4336-0.57422h-28c-0.0625-0.003906-0.125-0.003906-0.1875 0z"/>
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
