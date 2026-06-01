import React from "react";
import { createRoot } from "react-dom/client";
import { Excalidraw, serializeAsJSON, loadFromBlob } from "./excalidraw-fork/packages/excalidraw/index.tsx";
import type { BinaryFiles, ExcalidrawImperativeAPI } from "./excalidraw-fork/packages/excalidraw/types.ts";
import type { ExcalidrawElement } from "./excalidraw-fork/packages/common/src/types.ts";
import type { AppState } from "./excalidraw-fork/packages/excalidraw/types.ts";

export * from "./excalidraw-fork/packages/excalidraw/index.tsx";
export { React, createRoot };

(globalThis as any).__excalidrawLib = { React, createRoot, Excalidraw };

async function render({ model, el }: { model: any; el: HTMLElement }) {
  el.style.height = "600px";

  const mount = document.createElement("div");
  mount.style.cssText = "width:100%;height:100%;display:block";
  el.appendChild(mount);

  // Prevent marimo from intercepting keyboard shortcuts (copy/paste etc.)
  mount.addEventListener("keydown", (e) => e.stopPropagation());
  mount.addEventListener("keyup", (e) => e.stopPropagation());

  const root = createRoot(mount);

  let saveTimer: ReturnType<typeof setTimeout> | null = null;
  let pending: { elements: readonly ExcalidrawElement[]; appState: AppState; files: BinaryFiles } | null = null;

  function scheduleScene(elements: readonly ExcalidrawElement[], appState: AppState, files: BinaryFiles) {
    pending = { elements, appState, files };
    if (saveTimer) return; // already scheduled
    saveTimer = setTimeout(() => {
      saveTimer = null;
      if (!pending) return;
      const scene = JSON.parse(serializeAsJSON(pending.elements, pending.appState, pending.files, "local"));
      pending = null;
      model.set("scene", scene);
      model.save_changes();
    }, 1000);
  }

  function parseContents(contents: string) {
    try { return JSON.parse(contents); } catch { return null; }
  }

  function App() {
    const apiRef = React.useRef<ExcalidrawImperativeAPI | null>(null);

    const initialContents = model.get("path")?.contents ?? "";
    const parsed = parseContents(initialContents);
    const initialData = parsed
      ? { elements: parsed.elements ?? [], appState: parsed.appState ?? {}, files: parsed.files ?? {} }
      : null;

    const onChange = React.useCallback(
      (elements: readonly ExcalidrawElement[], appState: AppState, files: BinaryFiles) => {
        scheduleScene(elements, appState, files);
      },
      [],
    );

    // Reload when path changes (e.g. user switches file)
    React.useEffect(() => {
      function onPathChange() {
        const contents = model.get("path")?.contents ?? "";
        const p = parseContents(contents);
        if (p && apiRef.current) {
          apiRef.current.updateScene({
            elements: p.elements ?? [],
            appState: p.appState ?? {},
          });
        }
      }
      model.on("change:path", onPathChange);
      return () => model.off("change:path", onPathChange);
    }, []);

    return React.createElement(Excalidraw, {
      excalidrawAPI: (api: ExcalidrawImperativeAPI) => { apiRef.current = api; },
      initialData,
      onChange,
    });
  }

  root.render(React.createElement(App));

  requestAnimationFrame(() => window.dispatchEvent(new Event("resize")));

  return () => root.unmount();
}

export default { render };
