// WebGL2 renderer for AttractorWidget.
//
// Pipeline adapted from Ricky Reusser's "Clifford and de Jong Attractors:
// Revised coloring" (https://observablehq.com/@rreusser/clifford-and-de-jong-attractors-revised-coloring).
//
//   1. State ping-pong: RGBA32F textures hold per-particle (x, y, dist, 0).
//      `dist` is the length of the most recent iteration step, used as the
//      per-particle color input.
//   2. Particle draw: gl.POINTS of N vertices. The VS samples the state
//      texture by gl_VertexID, projects to clip space, and evaluates the
//      Reusser phase colorscale at `dist * color_speed`. The FS outputs
//      vec4(1, color) so that the additive RGBA32F accumulator stores
//      (count, sum_r, sum_g, sum_b).
//   3. Tonemap: density = accum.r / normalisation; average color =
//      accum.gba / accum.r; combine in YUV space with log-density
//      luminance and saturation falling off near black / white.

import { parse, toGLSL } from "./parser.js";
import { buildLUT, NAMED_LUTS } from "./colormaps.js";

const QUAD_VS = `#version 300 es
in vec2 a_pos;
out vec2 v_uv;
void main() {
  v_uv = a_pos * 0.5 + 0.5;
  gl_Position = vec4(a_pos, 0.0, 1.0);
}`;

const POINT_FS = `#version 300 es
precision highp float;
in vec3 v_color;
out vec4 frag;
void main() { frag = vec4(1.0, v_color); }`;

function compile(gl, type, src) {
  const sh = gl.createShader(type);
  gl.shaderSource(sh, src);
  gl.compileShader(sh);
  if (!gl.getShaderParameter(sh, gl.COMPILE_STATUS)) {
    const log = gl.getShaderInfoLog(sh);
    gl.deleteShader(sh);
    throw new Error("Shader compile error:\n" + log + "\nSource:\n" + src);
  }
  return sh;
}

function program(gl, vsSrc, fsSrc) {
  const vs = compile(gl, gl.VERTEX_SHADER, vsSrc);
  const fs = compile(gl, gl.FRAGMENT_SHADER, fsSrc);
  const p = gl.createProgram();
  gl.attachShader(p, vs);
  gl.attachShader(p, fs);
  gl.linkProgram(p);
  if (!gl.getProgramParameter(p, gl.LINK_STATUS)) {
    const log = gl.getProgramInfoLog(p);
    gl.deleteProgram(p);
    throw new Error("Program link error:\n" + log);
  }
  gl.deleteShader(vs);
  gl.deleteShader(fs);
  return p;
}

export function tryCreateGPU(canvas) {
  const gl = canvas.getContext("webgl2", { preserveDrawingBuffer: false, antialias: false });
  if (!gl) return null;
  const ext = gl.getExtension("EXT_color_buffer_float");
  if (!ext) return null;
  return gl;
}

export class GPURenderer {
  constructor(canvas, gl) {
    this.canvas = canvas;
    this.gl = gl;
    this.view = [-2.5, 2.5, -2.5, 2.5];
    this.params = {};
    this.xExpr = "sin(a*y) + c*cos(a*x)";
    this.yExpr = "sin(b*x) + d*cos(b*y)";
    this.n = 0;
    this.gridSize = 0;
    this.iterationsPerFrame = 1;
    this.colormap = "phase";
    this.colorSpeed = 0.22;
    this.colorPhase = 180.0; // degrees
    this.background = "black";
    this.totalSamples = 0;

    this._quadVAO = null;
    this._quadBuf = null;
    this._pointVAO = null;
    this._stateA = null;
    this._stateB = null;
    this._stateFBO_A = null;
    this._stateFBO_B = null;
    this._accumTex = null;
    this._accumFBO = null;
    this._lutTex = null;
    this._iterProg = null;
    this._pointProg = null;
    this._tonemapPhaseProg = null;
    this._tonemapDensityProg = null;
    this._lastParamNames = "";

    this._rafId = null;

    this._initStaticGL();
    this.resize(canvas.width, canvas.height);
  }

  _initStaticGL() {
    const gl = this.gl;
    this._quadBuf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, this._quadBuf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([
      -1, -1, 1, -1, -1, 1, -1, 1, 1, -1, 1, 1,
    ]), gl.STATIC_DRAW);

    this._quadVAO = gl.createVertexArray();
    gl.bindVertexArray(this._quadVAO);
    gl.bindBuffer(gl.ARRAY_BUFFER, this._quadBuf);
    gl.enableVertexAttribArray(0);
    gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);
    gl.bindVertexArray(null);

    this._pointVAO = gl.createVertexArray();

    this._buildTonemapPrograms();
  }

  _buildTonemapPrograms() {
    const gl = this.gl;

    // Shared helpers go in every fragment shader.
    const COMMON = `
vec3 rgb2yuv(vec3 rgb) {
  float y = 0.299 * rgb.r + 0.587 * rgb.g + 0.114 * rgb.b;
  return vec3(y, 0.493 * (rgb.b - y), 0.877 * (rgb.r - y));
}
vec3 yuv2rgb(vec3 yuv) {
  return vec3(
    yuv.x + (1.0 / 0.877) * yuv.z,
    yuv.x - 0.39393 * yuv.y - 0.58081 * yuv.z,
    yuv.x + (1.0 / 0.493) * yuv.y
  );
}
float smoothLimit(float x, float k) {
  x = 2.0 * x - 1.0;
  float a = pow(abs(x), 1.0 / k);
  return sign(x) * pow(a / (a + 1.0), k) * 0.5 + 0.5;
}
float densityValue(float count, float scale, float brightness, float contrast,
                   float dynamicRange, float bg) {
  float density = count / max(scale, 1e-6);
  float v = density == 0.0 ? -20.0 : log(density) / log(1000.0);
  float value = contrast * v + brightness;
  value = smoothLimit(value, dynamicRange);
  if (bg > 0.5) value = 1.0 - value;
  return value;
}`;

    // Phase mode: average chrominance from accum.gba/accum.r, density-based
    // luminance. Reusser's recipe.
    const phaseFS = `#version 300 es
precision highp float;
in vec2 v_uv;
out vec4 frag;
uniform sampler2D u_accum;
uniform float u_scale, u_brightness, u_contrast, u_gamma;
uniform float u_saturation, u_dynamicRange, u_bg;
${COMMON}
void main() {
  vec4 state = texture(u_accum, v_uv);
  float value = densityValue(state.r, u_scale, u_brightness, u_contrast, u_dynamicRange, u_bg);
  vec3 rgb = state.gba / max(state.r, 1.0);
  vec3 yuv = rgb2yuv(rgb);
  yuv.x = value;
  yuv.yz *= u_saturation * value * (1.0 - value) * 4.0;
  rgb = yuv2rgb(yuv);
  rgb = clamp(rgb, 0.0, 1.0);
  frag = vec4(pow(rgb, vec3(1.0 / u_gamma)), 1.0);
}`;

    // Density mode: ignore chrominance, look up LUT by smooth-limited density.
    const densityFS = `#version 300 es
precision highp float;
in vec2 v_uv;
out vec4 frag;
uniform sampler2D u_accum;
uniform sampler2D u_lut;
uniform float u_scale, u_brightness, u_contrast, u_gamma;
uniform float u_dynamicRange, u_bg;
${COMMON}
void main() {
  float count = texture(u_accum, v_uv).r;
  float value = densityValue(count, u_scale, u_brightness, u_contrast, u_dynamicRange, u_bg);
  vec3 rgb = texture(u_lut, vec2(value, 0.5)).rgb;
  rgb = clamp(rgb, 0.0, 1.0);
  frag = vec4(pow(rgb, vec3(1.0 / u_gamma)), 1.0);
}`;

    this._tonemapPhaseProg = program(gl, QUAD_VS, phaseFS);
    gl.useProgram(this._tonemapPhaseProg);
    gl.uniform1i(gl.getUniformLocation(this._tonemapPhaseProg, "u_accum"), 0);

    this._tonemapDensityProg = program(gl, QUAD_VS, densityFS);
    gl.useProgram(this._tonemapDensityProg);
    gl.uniform1i(gl.getUniformLocation(this._tonemapDensityProg, "u_accum"), 0);
    gl.uniform1i(gl.getUniformLocation(this._tonemapDensityProg, "u_lut"), 1);
  }

  _ensureLUT(name) {
    if (name === "phase") return;
    const gl = this.gl;
    if (this._lutTex) gl.deleteTexture(this._lutTex);
    const data = buildLUT(name);
    this._lutTex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, this._lutTex);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 256, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, data);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
  }

  _buildFormulaPrograms() {
    const gl = this.gl;
    const names = Object.keys(this.params);

    let xGLSL, yGLSL;
    try {
      xGLSL = toGLSL(parse(this.xExpr), names);
      yGLSL = toGLSL(parse(this.yExpr), names);
    } catch (e) {
      console.error("Failed to compile attractor formula:", e);
      return;
    }

    const uniforms = names.map((n) => `uniform float u_${n};`).join("\n");

    // Iteration shader writes (new_x, new_y, dist, 0) where dist is the
    // distance travelled by the most recent step.
    const iterFS = `#version 300 es
precision highp float;
in vec2 v_uv;
out vec4 frag;
uniform sampler2D u_state;
${uniforms}
void main() {
  vec2 p_in = texture(u_state, v_uv).xy;
  vec2 p_out;
  p_out.x = ${xGLSL};
  p_out.y = ${yGLSL};
  float dist = length(p_out - p_in);
  frag = vec4(p_out, dist, 0.0);
}`;

    // Point draw VS pulls the (x, y, dist) for each particle and evaluates
    // the phase colorscale.
    const pointVS = `#version 300 es
precision highp float;
uniform sampler2D u_state;
uniform vec4 u_view;     // xmin, xmax, ymin, ymax
uniform int u_gridSize;
uniform float u_colorSpeed;
uniform float u_colorPhase;   // radians
out vec3 v_color;

vec3 colorscale(float t) {
  const float PI2 = 6.28318530717958647692;
  return 0.5 + 0.5 * vec3(
    cos(PI2 * t - u_colorPhase),
    cos(PI2 * (t - 1.0 / 3.0) - u_colorPhase),
    cos(PI2 * (t - 2.0 / 3.0) - u_colorPhase)
  );
}

void main() {
  int idx = gl_VertexID;
  int gx = idx % u_gridSize;
  int gy = idx / u_gridSize;
  vec2 uv = (vec2(gx, gy) + 0.5) / float(u_gridSize);
  vec3 s = texture(u_state, uv).xyz;
  vec2 p = s.xy;
  float dist = s.z;
  v_color = colorscale(dist * u_colorSpeed);
  float nx = (p.x - u_view.x) / (u_view.y - u_view.x);
  float ny = (p.y - u_view.z) / (u_view.w - u_view.z);
  gl_Position = vec4(nx * 2.0 - 1.0, ny * 2.0 - 1.0, 0.0, 1.0);
  gl_PointSize = 1.0;
}`;

    if (this._iterProg) gl.deleteProgram(this._iterProg);
    if (this._pointProg) gl.deleteProgram(this._pointProg);
    this._iterProg = program(gl, QUAD_VS, iterFS);
    this._pointProg = program(gl, pointVS, POINT_FS);

    gl.useProgram(this._iterProg);
    gl.uniform1i(gl.getUniformLocation(this._iterProg, "u_state"), 0);
    this._setIterUniforms();

    gl.useProgram(this._pointProg);
    gl.uniform1i(gl.getUniformLocation(this._pointProg, "u_state"), 0);
  }

  _setIterUniforms() {
    const gl = this.gl;
    if (!this._iterProg) return;
    gl.useProgram(this._iterProg);
    for (const [name, val] of Object.entries(this.params)) {
      const loc = gl.getUniformLocation(this._iterProg, `u_${name}`);
      if (loc) gl.uniform1f(loc, val);
    }
  }

  _createStateTexture(grid, init) {
    const gl = this.gl;
    const tex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, tex);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA32F, grid, grid, 0, gl.RGBA, gl.FLOAT, init);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    return tex;
  }

  _createFBO(tex) {
    const gl = this.gl;
    const fbo = gl.createFramebuffer();
    gl.bindFramebuffer(gl.FRAMEBUFFER, fbo);
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0);
    return fbo;
  }

  _allocStates() {
    const gl = this.gl;
    let g = Math.ceil(Math.sqrt(this.n));
    if (g < 1) g = 1;
    this.gridSize = g;
    const total = g * g;
    const init = new Float32Array(total * 4);
    const [xmin, xmax, ymin, ymax] = this.view;
    const dx = xmax - xmin;
    const dy = ymax - ymin;
    for (let i = 0; i < total; i++) {
      init[i * 4 + 0] = xmin + Math.random() * dx;
      init[i * 4 + 1] = ymin + Math.random() * dy;
      // .z (dist) initialised to 0; first frame's color will be base hue
    }
    if (this._stateA) gl.deleteTexture(this._stateA);
    if (this._stateB) gl.deleteTexture(this._stateB);
    if (this._stateFBO_A) gl.deleteFramebuffer(this._stateFBO_A);
    if (this._stateFBO_B) gl.deleteFramebuffer(this._stateFBO_B);
    this._stateA = this._createStateTexture(g, init);
    this._stateB = this._createStateTexture(g, init);
    this._stateFBO_A = this._createFBO(this._stateA);
    this._stateFBO_B = this._createFBO(this._stateB);
  }

  _allocAccum(w, h) {
    const gl = this.gl;
    if (this._accumTex) gl.deleteTexture(this._accumTex);
    if (this._accumFBO) gl.deleteFramebuffer(this._accumFBO);
    this._accumTex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, this._accumTex);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA32F, w, h, 0, gl.RGBA, gl.FLOAT, null);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    this._accumFBO = this._createFBO(this._accumTex);
    this._clearAccum();
  }

  _clearAccum() {
    const gl = this.gl;
    gl.bindFramebuffer(gl.FRAMEBUFFER, this._accumFBO);
    gl.viewport(0, 0, this.canvas.width, this.canvas.height);
    gl.clearColor(0, 0, 0, 0);
    gl.clear(gl.COLOR_BUFFER_BIT);
    this.totalSamples = 0;
  }

  resize(w, h) {
    this.canvas.width = w;
    this.canvas.height = h;
    this._allocAccum(w, h);
  }

  setExprs(xExpr, yExpr) {
    this.xExpr = xExpr;
    this.yExpr = yExpr;
    this._buildFormulaPrograms();
    this._allocStates();
    this._clearAccum();
  }

  setParams(params) {
    this.params = { ...params };
    const sig = Object.keys(params).sort().join(",");
    if (!this._iterProg || this._lastParamNames !== sig) {
      this._lastParamNames = sig;
      this._buildFormulaPrograms();
    } else {
      this._setIterUniforms();
    }
    this._allocStates();
    this._clearAccum();
  }

  setView(view) {
    this.view = view.slice();
    this._allocStates();
    this._clearAccum();
  }

  setNPoints(n) {
    this.n = n;
    this._allocStates();
    this._clearAccum();
  }

  setColorSpeed(v) { this.colorSpeed = v; this._clearAccum(); }
  setColorPhase(deg) { this.colorPhase = deg; this._clearAccum(); }
  setColormap(name) {
    this.colormap = name;
    this._ensureLUT(name);
  }
  setBackground(bg) { this.background = bg; }
  setIterationsPerFrame(k) { this.iterationsPerFrame = Math.max(1, k | 0); }

  clear() {
    this._allocStates();
    this._clearAccum();
  }

  start() {
    if (this._rafId != null) return;
    const loop = () => {
      this._rafId = requestAnimationFrame(loop);
      this._frame();
    };
    this._rafId = requestAnimationFrame(loop);
  }

  stop() {
    if (this._rafId != null) cancelAnimationFrame(this._rafId);
    this._rafId = null;
  }

  dispose() {
    this.stop();
    const gl = this.gl;
    if (this._stateA) gl.deleteTexture(this._stateA);
    if (this._stateB) gl.deleteTexture(this._stateB);
    if (this._accumTex) gl.deleteTexture(this._accumTex);
    if (this._lutTex) gl.deleteTexture(this._lutTex);
    if (this._stateFBO_A) gl.deleteFramebuffer(this._stateFBO_A);
    if (this._stateFBO_B) gl.deleteFramebuffer(this._stateFBO_B);
    if (this._accumFBO) gl.deleteFramebuffer(this._accumFBO);
    if (this._quadBuf) gl.deleteBuffer(this._quadBuf);
    if (this._quadVAO) gl.deleteVertexArray(this._quadVAO);
    if (this._pointVAO) gl.deleteVertexArray(this._pointVAO);
    if (this._iterProg) gl.deleteProgram(this._iterProg);
    if (this._pointProg) gl.deleteProgram(this._pointProg);
    if (this._tonemapPhaseProg) gl.deleteProgram(this._tonemapPhaseProg);
    if (this._tonemapDensityProg) gl.deleteProgram(this._tonemapDensityProg);
  }

  _frame() {
    const gl = this.gl;
    if (!this._iterProg || !this._pointProg || !this._stateA || this.n === 0) return;

    for (let pass = 0; pass < this.iterationsPerFrame; pass++) {
      // 1. Iteration: stateA -> stateB
      gl.useProgram(this._iterProg);
      gl.bindVertexArray(this._quadVAO);
      gl.activeTexture(gl.TEXTURE0);
      gl.bindTexture(gl.TEXTURE_2D, this._stateA);
      gl.bindFramebuffer(gl.FRAMEBUFFER, this._stateFBO_B);
      gl.viewport(0, 0, this.gridSize, this.gridSize);
      gl.disable(gl.BLEND);
      gl.drawArrays(gl.TRIANGLES, 0, 6);

      // 2. Draw colored points from stateB into accumulation FBO.
      gl.useProgram(this._pointProg);
      gl.bindVertexArray(this._pointVAO);
      gl.activeTexture(gl.TEXTURE0);
      gl.bindTexture(gl.TEXTURE_2D, this._stateB);
      gl.uniform4f(
        gl.getUniformLocation(this._pointProg, "u_view"),
        this.view[0], this.view[1], this.view[2], this.view[3]
      );
      gl.uniform1i(gl.getUniformLocation(this._pointProg, "u_gridSize"), this.gridSize);
      gl.uniform1f(gl.getUniformLocation(this._pointProg, "u_colorSpeed"), this.colorSpeed);
      gl.uniform1f(
        gl.getUniformLocation(this._pointProg, "u_colorPhase"),
        this.colorPhase * Math.PI / 180.0,
      );
      gl.bindFramebuffer(gl.FRAMEBUFFER, this._accumFBO);
      gl.viewport(0, 0, this.canvas.width, this.canvas.height);
      gl.enable(gl.BLEND);
      gl.blendFunc(gl.ONE, gl.ONE);
      gl.drawArrays(gl.POINTS, 0, this.n);

      this.totalSamples += this.n;

      [this._stateA, this._stateB] = [this._stateB, this._stateA];
      [this._stateFBO_A, this._stateFBO_B] = [this._stateFBO_B, this._stateFBO_A];
    }

    // 3. Tonemap to default framebuffer.
    const usePhase = this.colormap === "phase";
    const prog = usePhase ? this._tonemapPhaseProg : this._tonemapDensityProg;
    gl.useProgram(prog);
    gl.bindVertexArray(this._quadVAO);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, this._accumTex);
    if (!usePhase) {
      gl.activeTexture(gl.TEXTURE1);
      gl.bindTexture(gl.TEXTURE_2D, this._lutTex);
    }
    const w = this.canvas.width;
    const h = this.canvas.height;
    // Reusser's "scale" uniform: expected count per pixel.
    const scale = this.totalSamples / (w * h);
    gl.uniform1f(gl.getUniformLocation(prog, "u_scale"), Math.max(scale, 1e-6));
    // Brightness uses Reusser's invert convention: for white-bg we want
    // empty pixels to map to 1 (paper), for black-bg to 0 (canvas). The
    // shader applies `if (bg > 0.5) value = 1.0 - value`, so we pass the
    // raw brightness (0.3) regardless of background; the inversion is
    // handled inside the shader.
    gl.uniform1f(gl.getUniformLocation(prog, "u_brightness"), 0.3);
    gl.uniform1f(gl.getUniformLocation(prog, "u_contrast"), 1.0);
    gl.uniform1f(gl.getUniformLocation(prog, "u_gamma"), 2.2);
    gl.uniform1f(gl.getUniformLocation(prog, "u_dynamicRange"), 0.2);
    if (usePhase) gl.uniform1f(gl.getUniformLocation(prog, "u_saturation"), 0.8);
    gl.uniform1f(
      gl.getUniformLocation(prog, "u_bg"),
      this.background === "white" ? 1 : 0,
    );
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    gl.viewport(0, 0, w, h);
    gl.disable(gl.BLEND);
    gl.drawArrays(gl.TRIANGLES, 0, 6);
  }
}
