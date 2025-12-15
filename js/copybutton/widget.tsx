import * as React from "react";
import { createRender, useModelState } from "@anywidget/react";
import { CopyIcon } from "@radix-ui/react-icons";

function copyToClipboard(text: string) {
    navigator.clipboard.writeText(text);
}

function CopyToClipboardButton() {
    let [text_to_copy, setTextToCopy] = useModelState<string>("text_to_copy");
    
	return <div className="copy-button-wrapper">
        <button 
            className="copy-button"
            onClick={() => copyToClipboard(text_to_copy)}
            type="button"
        >
            <CopyIcon className="copy-button-icon" />
            Copy to Clipboard
        </button>
    </div>
}

const render = createRender(CopyToClipboardButton);

export default { render };