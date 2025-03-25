import * as React from "react";
import { createRender, useModelState } from "@anywidget/react";

import { Tldraw, TLUiComponents } from 'tldraw'
import 'tldraw/tldraw.css'

function Counter() {
	let [value, setValue] = useModelState<number>("value");
	return <>
      <button onClick={() => setValue(value + 1)}>count is {value}</button>
      <div className="tldraw__editor" style={ { height: 500, width: 500 } } >
        <Tldraw
          persistenceKey="my-unique-persistence-key"
          store={undefined}
        />
		</div>
  </>
}

const render = createRender(Counter);

export default { render };