import{ad as r,ae as n,af as t,ag as a,ah as e,ai as i,y as u,aj as o,z as f}from"./index-BhlMW1u9.js";import{a as s}from"./_baseEach-Bn-Ll0SB.js";import{b as c}from"./_baseMap-DO0U0y1X.js";function l(n,t){if(n!==t){var a=void 0!==n,e=null===n,i=n==n,u=r(n),o=void 0!==t,f=null===t,s=t==t,c=r(t);if(!f&&!c&&!u&&n>t||u&&o&&s&&!f&&!c||e&&o&&s||!a&&s||!i)return 1;if(!e&&!u&&!c&&n<t||c&&a&&i&&!e&&!u||f&&a&&i||!o&&i||!s)return-1}return 0}function v(r,u,o){u=u.length?n(u,(function(r){return t(r)?function(n){return a(n,1===r.length?r[0]:r)}:r})):[e];var f=-1;return u=n(u,i(s)),function(r,n){var t=r.length;for(r.sort(n);t--;)r[t]=r[t].value;return r}(c(r,(function(r,t,a){return{criteria:n(u,(function(n){return n(r)})),index:++f,value:r}})),(function(r,n){return function(r,n,t){for(var a=-1,e=r.criteria,i=n.criteria,u=e.length,o=t.length;++a<u;){var f=l(e[a],i[a]);if(f)return a>=o?f:f*("desc"==t[a]?-1:1)}return r.index-n.index}(r,n,o)}))}var d=u((function(r,n){if(null==r)return[];var t=n.length;return t>1&&o(r,n[0],n[1])?n=[]:t>2&&o(n[0],n[1],n[2])&&(n=[n[0]]),v(r,f(n),[])}));export{d as s};