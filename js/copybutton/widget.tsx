import * as React from "react";
import { createRender, useModelState } from "@anywidget/react";
import { CopyIcon } from "@radix-ui/react-icons";
import "@radix-ui/themes/styles.css";
import { Theme, Button } from "@radix-ui/themes";


function copyToClipboard(text: string) {
    navigator.clipboard.writeText(text);
}

function CopyToClipboardButton() {
    let [text_to_copy, setTextToCopy] = useModelState<string>("text_to_copy");
	return <>
      <Theme accentColor="gray" grayColor="sand" radius="large">
        <Button onClick={() => copyToClipboard(text_to_copy)}>
            <CopyIcon /> Copy to Clipboard
        </Button>
      </Theme>
  </>
}

const render = createRender(CopyToClipboardButton);

export default { render };