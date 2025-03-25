import * as React from "react";
import { createRender, useModelState } from "@anywidget/react";
import { CopyIcon } from "@radix-ui/react-icons";
import "@radix-ui/themes/styles.css";
import { Theme, Button, ThemePanel } from "@radix-ui/themes";
import { Tldraw } from 'tldraw'
import { Editor } from '@tldraw/editor'
import 'tldraw/tldraw.css'


const blobToBase64 = blob => {
  const reader = new FileReader();
  reader.readAsDataURL(blob);
  return new Promise(resolve => {
    reader.onloadend = () => {
      resolve(reader.result);
    };
  });
};

function App() {
  let [width, setWidth] = useModelState<number>("width");
  let [height, setHeight] = useModelState<number>("height")
  let [base64, setBase64] = useModelState<string>("base64")
  const handleMount = (editor: Editor) => {
    editor.setCurrentTool('draw');
    
    let timeoutId = null;
    editor.sideEffects.registerAfterCreateHandler('shape', async (shape) => {
      // Clear any existing timeout
      if (timeoutId) clearTimeout(timeoutId);
      
      // Set new timeout to emit after 1s of no drawing
      timeoutId = setTimeout(async () => {
        
        const shapeIds = editor.getCurrentPageShapeIds()
        if (shapeIds.size === 0) return alert('No shapes on the canvas')
          const { blob } = await editor.toImage([...shapeIds], { format: 'png', background: false })
        const base64 = await blobToBase64(blob);
        setBase64(base64 as string);
        
      }, 1000);
    });
  }
  
  return (
    <div style={{ height: height, width: width }} className="tldraw__editor">
      <Tldraw onMount={handleMount} />
    </div>
  )
}

const render = createRender(App);

export default { render };
