import { createRender, useModelState } from "@anywidget/react";
import React, { useRef, useState, useEffect } from 'react';

const Button = React.forwardRef<
  HTMLButtonElement,
  React.ButtonHTMLAttributes<HTMLButtonElement> & {
    variant?: 'default' | 'ghost'
  }
>(({ className = '', variant = 'default', ...props }, ref) => {
  const baseStyles = 'inline-flex items-center justify-center rounded-md text-sm font-medium focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50';
  const variantStyles = {
    default: 'bg-gray-200 active:bg-gray-300',
    ghost: 'active:bg-gray-100/50'
  };
  
  return (
    <button
      ref={ref}
      className={`${baseStyles} ${variantStyles[variant]} ${className}`}
      {...props}
    />
  );
});
Button.displayName = 'Button';

const colors = [
  '#000000', '#FFFFFF', '#C0C0C0', '#FF0000', '#FFFF00', '#00FF00', '#00FFFF', '#0000FF', '#FF00FF', '#FFFF80', '#00FF80', '#80FFFF', '#8080FF', '#FF0080'
];

// Constants for canvas settings
const MAX_CANVAS_DIMENSION = 4096; // Most browsers support up to 4096x4096

function Component() {
  const drawingCanvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [color, setColor] = useState('#000000');
  const [tool, setTool] = useState('brush');
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  let [base64, setBase64] = useModelState<string>("base64");
  let [height, setHeight] = useModelState<number>("height");
  let [storeBackground, setStoreBackground] = useModelState<boolean>("store_background");
  
  const [canvasSize, setCanvasSize] = useState({ width: 0, height: 0 });

  // Utility function to ensure canvas context is available
  const getContext = () => {
    const drawingContext = drawingCanvasRef.current?.getContext('2d');
    return drawingContext;
  };

  // Utility function to ensure canvas sizes are in sync
  const syncCanvasSizes = (width: number, height: number) => {
    const drawingContext = getContext();
    if (!drawingContext) return false;

    // Scale down if dimensions are too large
    const scale = Math.min(1, MAX_CANVAS_DIMENSION / Math.max(width, height));
    const finalWidth = Math.floor(width * scale);
    const finalHeight = Math.floor(height * scale);

    try {
      // Store the current drawing
      const drawingData = drawingCanvasRef.current?.toDataURL();

      // Set canvas dimensions
      drawingCanvasRef.current!.width = finalWidth;
      drawingCanvasRef.current!.height = finalHeight;

      // Restore the drawing if we had one
      if (drawingData) {
        const img = new Image();
        img.onload = () => {
          drawingContext.drawImage(img, 0, 0);
        };
        img.src = drawingData;
      }

      return true;
    } catch (e) {
      console.error('Failed to resize canvases:', e);
      setError('Failed to resize canvas. Try reducing the window size.');
      return false;
    }
  };

  // Handle window resize with debouncing
  useEffect(() => {
    let resizeTimeout: number;
    
    const resizeCanvas = () => {
      const container = drawingCanvasRef.current?.parentElement;
      if (!container) return;

      let newWidth = container.clientWidth;
      let newHeight = container.clientHeight;
      
      // If we have an original image, use its dimensions to maintain aspect ratio
      // and prevent scaling distortion
      if (originalImageRef.current) {
        // For images, we want to maintain the original dimensions
        // Width can be responsive to container, but height should match image proportions
        const img = new Image();
        img.onload = () => {
          const imageAspectRatio = img.width / img.height;
          const containerAspectRatio = newWidth / newHeight;
          
          // Preserve original image dimensions - don't scale the image
          // Instead, adjust canvas to accommodate the image
          newWidth = Math.min(newWidth, img.width);
          newHeight = img.height;
          
          if (syncCanvasSizes(newWidth, newHeight)) {
            setCanvasSize({ width: newWidth, height: newHeight });
          }
        };
        img.src = `data:image/png;base64,${originalImageRef.current}`;
      } else {
        // No original image, use container dimensions as before
        if (syncCanvasSizes(newWidth, newHeight)) {
          setCanvasSize({ width: newWidth, height: newHeight });
        }
      }
    };

    const debouncedResize = () => {
      clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(resizeCanvas, 250);
    };

    window.addEventListener('resize', debouncedResize);
    resizeCanvas(); // Initial sizing

    return () => {
      window.removeEventListener('resize', debouncedResize);
      clearTimeout(resizeTimeout);
    };
  }, []); // Empty dependency - resize logic handles original image internally

  // Effect to handle touch events
  useEffect(() => {
    const drawingCanvas = drawingCanvasRef.current;
    if (!drawingCanvas) return;

    const touchStart = (e: TouchEvent) => {
      e.preventDefault();
      const touch = e.touches[0];
      const rect = drawingCanvas.getBoundingClientRect();
      startDrawingAt(touch.clientX - rect.left, touch.clientY - rect.top);
    };

    const touchMove = (e: TouchEvent) => {
      e.preventDefault();
      const touch = e.touches[0];
      const rect = drawingCanvas.getBoundingClientRect();
      drawAt(touch.clientX - rect.left, touch.clientY - rect.top);
    };

    const touchEnd = (e: TouchEvent) => {
      e.preventDefault();
      stopDrawing();
    };

    drawingCanvas.addEventListener('touchstart', touchStart);
    drawingCanvas.addEventListener('touchmove', touchMove);
    drawingCanvas.addEventListener('touchend', touchEnd);

    return () => {
      drawingCanvas.removeEventListener('touchstart', touchStart);
      drawingCanvas.removeEventListener('touchmove', touchMove);
      drawingCanvas.removeEventListener('touchend', touchEnd);
    };
  }, []);

  // Track the last loaded base64 to detect changes
  const lastLoadedBase64Ref = useRef<string>("");
  // Track if we're in the process of loading an initial image
  const isLoadingInitialImageRef = useRef(false);
  // Store the original base64 image for reset operations (captured on first render only)
  const originalImageRef = useRef<string>("");
  // Track drawing changes to trigger exports
  const [exportTrigger, setExportTrigger] = useState(0);

  // Capture the original base64 ONCE on component mount (before any user drawings)
  useEffect(() => {
    originalImageRef.current = base64;
  }, []); // Empty deps = runs only once on mount

  // Drawing functions - defined before effects that use them
  const startDrawingAt = (x: number, y: number) => {
    const drawingContext = getContext();
    if (!drawingContext) return;

    try {
      drawingContext.beginPath();
      drawingContext.moveTo(x, y);
      setIsDrawing(true);
    } catch (e) {
      console.error('Failed to start drawing:', e);
      setError('Failed to start drawing. Try refreshing the page.');
    }
  };

  const drawAt = (x: number, y: number) => {
    if (!isDrawing) return;

    const drawingContext = getContext();
    if (!drawingContext) return;

    try {
      drawingContext.lineTo(x, y);
      
      if (tool === 'eraser') {
        // Save the current state
        drawingContext.save();
        // Set composite operation to clear the pixels
        drawingContext.globalCompositeOperation = 'destination-out';
        drawingContext.strokeStyle = '#000000';  // Color doesn't matter for eraser
        drawingContext.lineWidth = 20;
        drawingContext.lineCap = 'round';
        drawingContext.stroke();
        // Restore the previous state
        drawingContext.restore();
      } else {
        // Normal drawing
        drawingContext.strokeStyle = color;
        drawingContext.lineWidth = tool === 'marker' ? 8 : 2;
        drawingContext.lineCap = 'round';
        drawingContext.stroke();
      }
    } catch (e) {
      console.error('Failed to draw:', e);
      setError('Failed to draw. Try refreshing the page.');
      setIsDrawing(false);
    }
  };

  const stopDrawing = () => {
    if (!isDrawing) return;
    
    try {
      // Trigger export after drawing
      setExportTrigger(prev => prev + 1);
    } catch (e) {
      console.error('Failed to complete drawing:', e);
      setError('Failed to complete drawing. Try refreshing the page.');
    }
    
    setIsDrawing(false);
  };

  // Effect to load initial image when base64 is available and canvas is ready
  useEffect(() => {
    const drawingContext = getContext();

    // Skip if no context, canvas, or base64
    if (!drawingContext || !drawingCanvasRef.current || !base64) {
      return;
    }
    
    // Skip if we already loaded this exact base64, BUT only if canvas still has content
    if (base64 === lastLoadedBase64Ref.current) {
      // Check if canvas actually has the image content
      const canvas = drawingCanvasRef.current;
      if (canvas && canvas.width > 0 && canvas.height > 0) {
        try {
          const imageData = drawingContext.getImageData(0, 0, canvas.width, canvas.height);
          const hasContent = imageData.data.some(pixel => pixel !== 0);
          if (hasContent) {
            return;
          }
        } catch (e) {
          // Could not check canvas content, proceed with reload
        }
      }
    }
    
    const canvas = drawingCanvasRef.current;
    // Only proceed if canvas has proper dimensions
    if (canvas.width === 0 || canvas.height === 0) {
      return;
    }
    
    isLoadingInitialImageRef.current = true;

    // Load the initial image
    const img = new Image();
    img.onload = () => {
      drawingContext.clearRect(0, 0, canvas.width, canvas.height);
      
      // Draw image at original size (no scaling) - preserve image dimensions
      drawingContext.drawImage(img, 0, 0, img.width, img.height);
      
      lastLoadedBase64Ref.current = base64;
      isLoadingInitialImageRef.current = false;
    };
    img.onerror = (e) => {
      console.error('Failed to load image:', e);
      isLoadingInitialImageRef.current = false;
    };
    img.src = `data:image/png;base64,${base64}`;
  }, [base64, canvasSize.width, canvasSize.height]);

  // Effect to handle export updates
  useEffect(() => {
    if (!drawingCanvasRef.current) return;
    
    // Don't export on initial render (when exportTrigger is 0)
    if (exportTrigger === 0) {
      return;
    }
    
    // Don't export while we're loading an initial image
    if (isLoadingInitialImageRef.current) {
      return;
    }
    
    const exportCanvas = document.createElement('canvas');
    exportCanvas.width = drawingCanvasRef.current.width;
    exportCanvas.height = drawingCanvasRef.current.height;
    const exportContext = exportCanvas.getContext('2d', { alpha: true });
    if (!exportContext) return;

    // Start fresh with a transparent canvas
    exportContext.clearRect(0, 0, exportCanvas.width, exportCanvas.height);
    
    // Layer 1: Background (if enabled)
    if (storeBackground) {
      exportContext.fillStyle = '#FFFFFF';
      exportContext.fillRect(0, 0, exportCanvas.width, exportCanvas.height);
    }
    
    // Layer 2: Drawing content (always preserve original alpha)
    exportContext.globalCompositeOperation = 'source-over';
    exportContext.drawImage(drawingCanvasRef.current, 0, 0);

    // Update base64 output
    try {
      const dataUrl = exportCanvas.toDataURL('image/png');
      setBase64(dataUrl.split(',')[1]);
    } catch (e) {
      console.error('Failed to export canvas:', e);
      setError('Failed to export canvas. Try refreshing the page.');
    }
  }, [storeBackground, canvasSize, exportTrigger]);

  const startDrawing = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    startDrawingAt(e.clientX - rect.left, e.clientY - rect.top);
  };

  const draw = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    drawAt(e.clientX - rect.left, e.clientY - rect.top);
  };

  const startDragging = (e: React.MouseEvent<HTMLDivElement>) => {
    setDragging(true);
    setPosition({
      x: e.clientX - (containerRef.current?.offsetLeft || 0),
      y: e.clientY - (containerRef.current?.offsetTop || 0)
    });
  };

  const onDrag = (e: React.MouseEvent<HTMLDivElement>) => {
    if (dragging) {
      const left = e.clientX - position.x;
      const top = e.clientY - position.y;
      if (containerRef.current) {
        containerRef.current.style.left = `${left}px`;
        containerRef.current.style.top = `${top}px`;
      }
    }
  };

  const stopDragging = () => {
    setDragging(false);
  };

  const BackgroundIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
      <rect x="7" y="7" width="10" height="10" rx="1" ry="1" fill="currentColor" fillOpacity="0.2"></rect>
    </svg>
  );

  return (
    <div className="bg-teal-600 w-full overflow-hidden" style={{ height: `${height}px` }}>
      {error && (
        <div className="absolute top-0 left-0 right-0 bg-red-500 text-white p-2 text-center">
          {error}
          <button 
            className="ml-2 underline"
            onClick={() => setError(null)}
          >
            Dismiss
          </button>
        </div>
      )}
      <div 
        ref={containerRef}
        className="absolute bg-white border-2 border-gray-200 shadow-md flex flex-col" 
        style={{ 
          width: '90%', 
          height: '90%', 
          left: '50%', 
          top: '50%', 
          transform: 'translate(-50%, -50%)',
          minWidth: '400px',
          minHeight: '300px'
        }}
      >
        {/* Title bar */}
        <div 
          className="bg-blue-900 text-white px-2 py-1 flex justify-between items-center cursor-move"
          onMouseDown={startDragging}
          onMouseMove={onDrag}
          onMouseUp={stopDragging}
          onMouseLeave={stopDragging}
        >
          <span className="text-white">untitled - Paint</span>
          <div className="flex gap-1">
            <Button variant="ghost" className="h-5 w-5 p-0 min-w-0 text-white hover:bg-blue-700">_</Button>
            <Button variant="ghost" className="h-5 w-5 p-0 min-w-0 text-white hover:bg-blue-700">□</Button>
            <Button variant="ghost" className="h-5 w-5 p-0 min-w-0 text-white hover:bg-blue-700">×</Button>
          </div>
        </div>

        {/* Menu bar */}
        <div className="bg-gray-300 px-2 py-1 text-sm text-black">
          <span className="mr-4 text-black">File</span>
          <span className="mr-4 text-black">Edit</span>
          <span className="mr-4 text-black">View</span>
          <span className="mr-4 text-black">Image</span>
          <span className="mr-4 text-black">Options</span>
          <span className="text-black">Help</span>
        </div>

        {/* Main content area */}
        <div className="flex flex-1 min-h-0">
          {/* Left toolbar */}
          <div className="w-8 bg-gray-300 p-0.5 border-r border-gray-400">
            <Button
              variant="ghost"
              className={`w-7 h-7 p-0 min-w-0 mb-0.5 ${tool === 'brush' ? 'bg-gray-300 border border-gray-400 shadow-inner' : ''}`}
              onClick={() => setTool('brush')}
              title="Brush"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5 text-black">
                <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z" />
              </svg>
            </Button>
            <Button
              variant="ghost"
              className={`w-7 h-7 p-0 min-w-0 mb-0.5 ${tool === 'marker' ? 'bg-gray-300 border border-gray-400 shadow-inner' : ''}`}
              onClick={() => setTool('marker')}
              title="Thick Marker"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5 text-black">
                <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z" />
              </svg>
            </Button>
            <Button
              variant="ghost"
              className={`w-7 h-7 p-0 min-w-0 mb-0.5 ${tool === 'eraser' ? 'bg-gray-300 border border-gray-400 shadow-inner' : ''}`}
              onClick={() => setTool('eraser')}
              title="Eraser"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6 text-black">
                <path d="M7 21h10"/>
                <path d="M5.5 13.5L13 6c.83-.83 2.17-.83 3 0l2 2c.83.83.83 2.17 0 3l-7.5 7.5c-.83.83-2.17.83-3 0l-2-2c-.83-.83-.83-2.17 0-3z"/>
              </svg>
            </Button>
            <div className="w-7 h-0.5 bg-gray-400 my-1"></div>
            <Button
              variant="ghost"
              className={`w-7 h-7 p-0 min-w-0 mb-0.5 ${storeBackground ? 'bg-gray-300 border border-gray-400 shadow-inner' : ''}`}
              onClick={() => setStoreBackground(!storeBackground)}
              title="Store White Background"
            >
              <BackgroundIcon />
            </Button>
            <div className="w-7 h-0.5 bg-gray-400 my-1"></div>
            <Button
              variant="ghost"
              className="w-7 h-7 p-0 min-w-0 mb-0.5"
              onClick={() => {
                const drawingCanvas = drawingCanvasRef.current;
                if (drawingCanvas) {
                  const drawingContext = drawingCanvas.getContext('2d');
                  if (drawingContext) {
                    // Clear the entire canvas first
                    drawingContext.clearRect(0, 0, drawingCanvas.width, drawingCanvas.height);

                    // If we have an original image, restore it
                    if (originalImageRef.current) {
                      // Set loading flag to prevent premature exports
                      isLoadingInitialImageRef.current = true;

                      const img = new Image();
                      img.onload = () => {
                        // Draw image at original size (no scaling)
                        drawingContext.drawImage(img, 0, 0, img.width, img.height);
                        // Clear loading flag
                        isLoadingInitialImageRef.current = false;
                        // Trigger export after restoring
                        setExportTrigger(prev => prev + 1);
                      };
                      img.onerror = () => {
                        // Clear loading flag even on error
                        isLoadingInitialImageRef.current = false;
                        // Trigger export of empty canvas
                        setExportTrigger(prev => prev + 1);
                      };
                      img.src = `data:image/png;base64,${originalImageRef.current}`;
                    } else {
                      // No original image, just clear and trigger export
                      setExportTrigger(prev => prev + 1);
                    }
                  }
                }
              }}
              title="Clear Canvas"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5 text-black">
                <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>
                <path d="M21 3v5h-5"/>
                <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>
                <path d="M8 16H3v5"/>
              </svg>
            </Button>
          </div>

          {/* Canvas area */}
          <div className="flex-grow overflow-hidden border border-gray-400 relative">
            {/* Drawing canvas */}
            <canvas
              ref={drawingCanvasRef}
              width={canvasSize.width}
              height={canvasSize.height}
              style={{
                width: '100%',
                height: '100%',
                background: 'transparent'
              }}
              onMouseDown={startDrawing}
              onMouseMove={draw}
              onMouseUp={stopDrawing}
              onMouseLeave={stopDrawing}
            />
          </div>
        </div>

        {/* Bottom color picker */}
        <div className="flex bg-gray-300 p-1 border-t border-gray-400">
          <div className="flex flex-wrap gap-1">
            {colors.map((c) => (
              <Button
                key={c}
                variant="ghost"
                className={`w-6 h-6 p-0 min-w-0 ${color === c ? 'ring-1 ring-gray-600' : ''}`}
                style={{ backgroundColor: c }}
                onClick={() => setColor(c)}
              />
            ))}
          </div>
        </div>

        {/* Status bar */}
        <div className="bg-gray-300 px-2 py-1 text-xs border-t border-gray-400 text-black">
          For Help, click Help Topics on the Help Menu.
        </div>
      </div>
    </div>
  );
}

const render = createRender(Component);

export default { render };
