function Y({model:e,el:H}){let f=e.get("current_button_press"),o=e.get("current_timestamp"),i=e.get("previous_timestamp"),d=e.get("axes"),g=e.get("dpad_up"),x=e.get("dpad_down"),m=e.get("dpad_left"),h=e.get("dpad_right"),k=!1,r=document.createElement("div");r.style.cssText=`
            font-family: system-ui, -apple-system, sans-serif;
            padding: 16px;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            background: #f9fafb;
            max-width: 400px;
            transition: all 0.3s ease;
        `;let p=document.createElement("div");p.style.cssText="position: relative; display: flex; justify-content: center; align-items: center; margin-bottom: 12px;";let L=document.createElement("h3");L.textContent="\u{1F3AE} Mopad Widget",L.style.cssText="margin: 0; color: #374151; text-align: center;";let s=document.createElement("button");s.textContent="\u2212",s.style.cssText=`
            position: absolute;
            right: 0;
            top: 50%;
            transform: translateY(-50%);
            background: #6b7280;
            color: white;
            border: none;
            border-radius: 4px;
            width: 24px;
            height: 24px;
            cursor: pointer;
            font-size: 16px;
            line-height: 1;
            display: flex;
            align-items: center;
            justify-content: center;
        `,s.onmouseover=()=>s.style.background="#4b5563",s.onmouseout=()=>s.style.background="#6b7280";let a=document.createElement("div"),c=document.createElement("div");c.style.cssText=`
            padding: 8px 12px;
            border-radius: 6px;
            margin-bottom: 12px;
            font-weight: 500;
        `;let _=document.createElement("div");_.style.cssText="font-size: 14px; color: #6b7280; margin-bottom: 12px;";let C=document.createElement("div");C.style.cssText=`
            font-size: 14px;
            color: #374151;
            padding: 4px 0;
            font-family: monospace;
        `;let w=document.createElement("div");w.style.cssText=`
            font-size: 16px;
            color: #374151;
            padding: 4px 0;
        `;let M=document.createElement("div");M.style.cssText=`
            font-size: 14px;
            color: #374151;
            padding: 4px 0;
            font-family: monospace;
        `;let v=document.createElement("div");v.style.cssText=`
            font-size: 14px;
            color: #374151;
            padding: 4px 0;
            font-family: monospace;
        `,p.appendChild(L),p.appendChild(s),a.appendChild(c),a.appendChild(_),a.appendChild(w),a.appendChild(M),a.appendChild(v),a.appendChild(C),r.appendChild(p),r.appendChild(a),H.appendChild(r),s.addEventListener("click",()=>{k=!k,k?(a.style.display="none",r.style.padding="16px",s.textContent="+",p.style.cssText="position: relative; display: flex; justify-content: center; align-items: center;"):(a.style.display="block",r.style.padding="16px",s.textContent="\u2212",p.style.cssText="position: relative; display: flex; justify-content: center; align-items: center; margin-bottom: 12px;")});let S=window.mozRequestAnimationFrame||window.requestAnimationFrame,b=!1,A=null;function y(t,n=null){t?(c.style.cssText+="background: #dcfce7; color: #166534; border: 1px solid #bbf7d0;",c.textContent=`\u2705 Gamepad Connected: ${n?.id||"Unknown"}`,_.textContent="Press any button on the gamepad to interact.",b=!0):(c.style.cssText+="background: #fef2f2; color: #dc2626; border: 1px solid #fecaca;",c.textContent="\u274C No Gamepad Detected",_.innerHTML=`
                    To connect your gamepad:<br>
                    1. Connect your gamepad to your computer<br>
                    2. Press any button on the gamepad<br>
                    3. The widget will automatically detect it
                `,b=!1)}function $(){f>=0?w.textContent=`Current button press: ${f}`:w.textContent="No button pressed yet"}function z(){let t=[];g&&t.push("\u2191"),x&&t.push("\u2193"),m&&t.push("\u2190"),h&&t.push("\u2192"),M.textContent=t.length>0?`D-pad: ${t.join(" ")}`:"D-pad: \u2014"}function F(){if(d&&d.length>=4){let[t,n,u,D]=d;v.innerHTML=`
                    Left stick: (${t.toFixed(2)}, ${n.toFixed(2)})<br>
                    Right stick: (${u.toFixed(2)}, ${D.toFixed(2)})
                `}else v.textContent="Sticks: No data"}function T(){if(o>0){let t=new Date(o).toLocaleTimeString(),n=i>0?new Date(i).toLocaleTimeString():"None",u=i>0?((o-i)/1e3).toFixed(3):"N/A";C.innerHTML=`
                    Current: ${t}<br>
                    Previous: ${n}<br>
                    Time diff: ${u}s
                `}else C.textContent="No button presses recorded"}function U(){let t=navigator.getGamepads(),n=t[0]||t[1]||t[2]||t[3];return n&&n.connected?(b||y(!0,n),n):(b&&y(!1),null)}function j(){let t=U();if(t&&b){let n=!1,u=t.buttons.map(l=>l.pressed).join("");if(u!==A&&t.buttons.forEach((l,N)=>{l.pressed&&(i=o,o=Date.now(),f=N,e.set("current_button_press",f),e.set("current_timestamp",o),e.set("previous_timestamp",i),e.save_changes(),$(),T(),n=!0)}),t.axes&&t.axes.length>=4){let l=[Math.round((t.axes[0]||0)*100)/100,Math.round((t.axes[1]||0)*100)/100,Math.round((t.axes[2]||0)*100)/100,Math.round((t.axes[3]||0)*100)/100],N=.05,B=!1;for(let E=0;E<4;E++)if(Math.abs(l[E]-d[E])>N){B=!0;break}B&&(d=l,e.set("axes",d),e.save_changes(),F())}let D=t.buttons[12]?t.buttons[12].pressed:!1,G=t.buttons[13]?t.buttons[13].pressed:!1,P=t.buttons[14]?t.buttons[14].pressed:!1,R=t.buttons[15]?t.buttons[15].pressed:!1;(D!==g||G!==x||P!==m||R!==h)&&(g=D,x=G,m=P,h=R,e.set("dpad_up",g),e.set("dpad_down",x),e.set("dpad_left",m),e.set("dpad_right",h),e.save_changes(),z()),A=u,setTimeout(()=>S(j),n?200:50)}else setTimeout(()=>S(j),100)}window.addEventListener("gamepadconnected",t=>{y(!0,t.gamepad)}),window.addEventListener("gamepaddisconnected",()=>{y(!1)}),y(!1),$(),z(),F(),T(),e.on("change:current_button_press",()=>{f=e.get("current_button_press"),$()}),e.on("change:current_timestamp",()=>{o=e.get("current_timestamp"),T()}),e.on("change:previous_timestamp",()=>{i=e.get("previous_timestamp"),T()}),e.on("change:axes",()=>{d=e.get("axes"),F()}),e.on("change:dpad_up change:dpad_down change:dpad_left change:dpad_right",()=>{g=e.get("dpad_up"),x=e.get("dpad_down"),m=e.get("dpad_left"),h=e.get("dpad_right"),z()}),j()}var q={render:Y};export{q as default};
