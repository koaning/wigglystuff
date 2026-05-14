var y=`
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  border: 1px solid #d1d5db;
  border-radius: 10px;
  padding: 16px;
  max-width: 360px;
  background: #ffffff;
  display: flex;
  flex-direction: column;
  gap: 8px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
`,p=`
  border: 2px dashed #a7f3d0;
  border-radius: 8px;
  padding: 20px;
  min-height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-family: "JetBrains Mono", ui-monospace, SFMono-Regular, SFMono, Consolas, "Liberation Mono";
  cursor: pointer;
  transition: border-color 0.2s ease, background-color 0.2s ease;
  outline: none;
`;function u(o){if(!o||!o.key)return"Click here and press any key combination\u2026";let n=[];return o.ctrlKey&&n.push("Ctrl"),o.shiftKey&&n.push("Shift"),o.altKey&&n.push("Alt"),o.metaKey&&n.push("Meta"),`${n.length?`${n.join(" + ")} + `:""}${o.key}`}function f({model:o,el:n}){let s=document.createElement("div");s.style.cssText=y;let a=document.createElement("div");a.textContent="Keyboard shortcut listener",a.style.fontWeight="600",a.style.color="#065f46";let i=document.createElement("div");i.style.fontSize="14px",i.style.color="#4b5563",i.textContent="Click the panel below and press any shortcut.";let e=document.createElement("div");e.setAttribute("role","button"),e.setAttribute("aria-label","Capture keyboard shortcut"),e.tabIndex=0,e.style.cssText=p,e.textContent="Click here and press any key combination\u2026";let r=document.createElement("div");r.style.fontSize="13px",r.style.color="#6b7280",r.style.fontFamily='"JetBrains Mono", ui-monospace, SFMono-Regular, SFMono, Consolas, "Liberation Mono"',s.appendChild(a),s.appendChild(i),s.appendChild(e),s.appendChild(r),n.appendChild(s);let c=()=>{e.style.backgroundColor="#ecfdf5",e.style.borderColor="#34d399",setTimeout(()=>{e.style.backgroundColor="transparent",e.style.borderColor="#a7f3d0"},200)},l=t=>{e.textContent=u(t),t&&t.code?r.innerHTML=`
        Code: ${t.code}<br>
        Timestamp: ${t.timestamp||"\u2014"}
      `:r.textContent="No keystrokes recorded yet."};e.addEventListener("click",()=>e.focus()),e.addEventListener("focus",()=>{e.style.borderColor="#34d399",e.style.backgroundColor="#f0fdf4"}),e.addEventListener("blur",()=>{e.style.borderColor="#a7f3d0",e.style.backgroundColor="transparent"}),e.addEventListener("keydown",t=>{t.preventDefault(),t.stopPropagation();let d={key:t.key,code:t.code,ctrlKey:t.ctrlKey,shiftKey:t.shiftKey,altKey:t.altKey,metaKey:t.metaKey,timestamp:Date.now()};o.set("last_key",d),o.save_changes(),l(d),c()}),o.on("change:last_key",()=>l(o.get("last_key"))),l(o.get("last_key"))}var m={render:f};export{m as default};
