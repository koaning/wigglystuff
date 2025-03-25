import * as React from "react";
import { createRender, useModelState } from "@anywidget/react";

function copyToClipboard(text: string) {
    navigator.clipboard.writeText(text);
}

function CopyToClipboardButton() {
    let [text_to_copy, setTextToCopy] = useModelState<string>("text_to_copy");
	return <>
      <button onClick={() => copyToClipboard(text_to_copy)}>Copy to Clipboard</button>
  </>
}

const render = createRender(CopyToClipboardButton);

export default { render };