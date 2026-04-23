var P=`
.wiggly-nested-table {
  --bg: transparent;
  --fg: #1f2328;
  --muted: #6b7280;
  --row-border: #e5e7eb;
  --hover: rgba(15, 23, 42, 0.04);
  --header-bg: rgba(15, 23, 42, 0.025);
  --selected-bg: rgba(59, 130, 246, 0.1);
  --selected-accent: #3b82f6;
  color-scheme: light dark;
  color: var(--fg);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", sans-serif;
  font-size: 13px;
}
:host([data-theme="dark"]) .wiggly-nested-table,
.dark .wiggly-nested-table,
.dark-theme .wiggly-nested-table {
  --fg: #e6e6e6;
  --muted: #9ca3af;
  --row-border: #2a2d33;
  --hover: rgba(255, 255, 255, 0.05);
  --header-bg: rgba(255, 255, 255, 0.03);
  --selected-bg: rgba(96, 165, 250, 0.18);
  --selected-accent: #60a5fa;
}
.wiggly-nested-table table {
  width: 100%;
  border-collapse: collapse;
  background-color: var(--bg);
  font-variant-numeric: tabular-nums;
}
.wiggly-nested-table thead th {
  text-align: left;
  font-weight: 500;
  font-size: 11px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--muted);
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid var(--row-border);
  background-color: var(--header-bg);
  position: sticky;
  top: 0;
}
.wiggly-nested-table thead th.num { text-align: right; }
.wiggly-nested-table tbody td {
  padding: 0.35rem 0.75rem;
  vertical-align: middle;
  border-bottom: 1px solid var(--row-border);
  transition: background-color 0.15s ease-out;
}
.wiggly-nested-table tbody tr:last-child td { border-bottom: none; }
.wiggly-nested-table tbody tr:hover td { background-color: var(--hover); }
.wiggly-nested-table tbody tr.-selected td { background-color: var(--selected-bg); }
.wiggly-nested-table tbody tr.-selected td:first-child {
  box-shadow: inset 2px 0 0 var(--selected-accent);
}
.wiggly-nested-table td.num { text-align: right; font-variant-numeric: tabular-nums; }
.wiggly-nested-table td.pct { color: var(--muted); text-align: right; font-size: 12px; }
.wiggly-nested-table td.name-cell.-clickable { cursor: pointer; }
.wiggly-nested-table .row-name {
  user-select: none;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}
.wiggly-nested-table .chev {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 14px;
  height: 14px;
  color: var(--muted);
  flex-shrink: 0;
}
.wiggly-nested-table .chev.-empty { visibility: hidden; }
.wiggly-nested-table .chev svg {
  transition: transform 0.15s ease-out;
}
.wiggly-nested-table .chev.-open svg { transform: rotate(90deg); }
.wiggly-nested-table .name-label { font-weight: 500; }
`,R='<svg width="10" height="10" viewBox="0 0 10 10"><path d="M3.5 2 L6.5 5 L3.5 8" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>';function U(e){return e==null||Number.isNaN(e)?"":Number.isInteger(e)?String(e):(Math.round(e*100)/100).toFixed(2)}function j(e,i){if(e==null)return null;if(typeof e=="number")return i==="value"||!i?e:null;if(typeof e=="object"){let c=e[i];return typeof c=="number"?c:null}return null}function W(e,i){let c=e.display;if(c&&typeof c=="object"&&c[i]!==void 0)return c[i];let w=j(e.value,i);return U(w)}function Y(e){return e==="value"?"Value":e}function m(e){return e.join("\0")}function q({model:e,el:i}){let c=document.createElement("div");c.className="wiggly-nested-table";let w=document.createElement("style");w.textContent=P,c.appendChild(w);let k=document.createElement("table"),_=document.createElement("thead"),N=document.createElement("tbody");k.appendChild(_),k.appendChild(N),c.appendChild(k),i.appendChild(c);let o=new Set,v=new Map,p=null;function K(){let t=e.get("columns")||[];return t.length?t:["value"]}function B(){let t=e.get("data"),n=e.get("initial_expand_depth")||0,s=e.get("expanded_paths")||[];if(s.length){o=new Set(s.map(d=>m(d)));return}o=new Set;function l(d,u,r){if(r>=n||!d.children)return;let a=u.concat(d.name);o.add(m(a));for(let g of d.children)l(g,a,r+1)}t&&t.name&&l(t,[],0)}function I(){let t=[];for(let n of o)t.push(n.split("\0"));e.set("expanded_paths",t),e.save_changes()}function z(t){if(p!==t){if(p){let n=v.get(p);n&&n.classList.remove("-selected")}if(p=t,t){let n=v.get(t);n&&n.classList.add("-selected")}}}function L(){c.style.width=e.get("width")||"100%",B();let t=e.get("selected_path")||[];p=t.length?m(t):null,b()}function b(){let t=e.get("data"),n=K(),s=new Set(e.get("show_percent")||[]);if(_.innerHTML="",N.innerHTML="",v.clear(),!t||!t.name)return;let l=document.createElement("tr"),d=document.createElement("th");d.textContent="Name",l.appendChild(d);for(let r of n){let a=document.createElement("th");if(a.className="num",a.textContent=Y(r),l.appendChild(a),s.has(r)){let g=document.createElement("th");g.className="num",g.textContent="%",l.appendChild(g)}}_.appendChild(l);let u={};for(let r of n){let a=j(t.value,r);u[r]=a&&a!==0?a:1}F(t,[],0,u,n,s)}function F(t,n,s,l,d,u){let r=n.concat(t.name),a=m(r),g=o.has(a),x=!!(t.children&&t.children.length),f=document.createElement("tr");a===p&&f.classList.add("-selected"),v.set(a,f);let y=document.createElement("td");y.className="name-cell"+(x?" -clickable":""),y.style.paddingLeft=.75+s*1.2+"rem";let C=document.createElement("div");C.className="row-name";let S=document.createElement("span");S.className="chev"+(x?g?" -open":"":" -empty"),S.innerHTML=R,C.appendChild(S);let T=document.createElement("span");T.className="name-label",T.textContent=t.name,C.appendChild(T),y.addEventListener("click",h=>{h.stopPropagation(),z(a),e.set("selected_path",r),e.save_changes(),x&&(g?o.delete(a):o.add(a),I(),b())}),y.appendChild(C),f.appendChild(y);for(let h of d){let M=document.createElement("td");if(M.className="num",M.textContent=W(t,h),f.appendChild(M),u.has(h)){let E=document.createElement("td");E.className="pct";let H=j(t.value,h);if(H!==null&&l[h]){let G=H/l[h]*100;E.textContent=(Math.round(G*10)/10).toFixed(1)+"%"}else E.textContent="";f.appendChild(E)}}if(N.appendChild(f),x&&g)for(let h of t.children)F(h,r,s+1,l,d,u)}e.on("change:data",L),e.on("change:columns",b),e.on("change:show_percent",b),e.on("change:initial_expand_depth",L),e.on("change:width",()=>{c.style.width=e.get("width")||"100%"}),e.on("change:expanded_paths",()=>{let t=e.get("expanded_paths")||[],n=new Set(t.map(s=>m(s)));(n.size!==o.size||[...n].some(s=>!o.has(s)))&&(o=n,b())}),e.on("change:selected_path",()=>{let t=e.get("selected_path")||[];z(t.length?m(t):null)}),L()}var A={render:q};export{A as default};
