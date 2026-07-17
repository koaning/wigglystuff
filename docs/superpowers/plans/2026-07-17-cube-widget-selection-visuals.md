# CubeWidget Selection Visuals Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply the approved strong-focus cube selection treatment, compact colored sliders, and smaller point without changing CubeWidget behavior or Python state.

**Architecture:** Keep all rendering dependency-free in the existing SVG module. Express selection state through stable SVG classes and CSS variables so Playwright can verify the visible contract without coupling to projection coordinates. Keep theme handling and model synchronization unchanged.

**Tech Stack:** AnyWidget, vanilla JavaScript, SVG, scoped CSS, pytest, Playwright, marimo.

## Global Constraints

- Do not add Python or JavaScript dependencies.
- Preserve axis clicking, ordered plane → line → point locking, smooth sliders, reset behavior, and synchronized Python outputs.
- Render all selected geometry after the cube and axes.
- In selected state, every structural cube line is gray, dashed, and equally faded; the three colored axes remain solid over surface-colored cutouts.
- Use a 5.5 px point and do not progressively fade earlier selection layers.
- Use `#e74c3c`, `#27ae60`, and `#3498db` consistently for X, Y, and Z.
- Support light and dark notebook themes with widget-scoped CSS variables.

---

### Task 1: Lock the visual contract with a failing browser test

**Files:**
- Modify: `tests/test_e2e/test_cube_widget_browser.py`

**Interfaces:**
- Consumes: the existing marimo CubeWidget fixture and `.cube-widget-root` selectors.
- Produces: assertions for `.has-selection`, `.axis-cutout`, `.axis-line`, `.selection-cutout`, `.selection-mark`, slider CSS variables, and point radius.

- [ ] **Step 1: Add selected-state assertions after the first lock**

```python
expect(root.locator(".cube-svg")).to_have_class(re.compile(r"has-selection"))
expect(root.locator(".wireframe line").first).to_have_css(
    "stroke-dasharray", "4px, 5px"
)
expect(root.locator(".axis-cutout")).to_have_count(3)
expect(root.locator(".axis-line")).to_have_count(3)
```

- [ ] **Step 2: Add selection ordering and geometry assertions after all locks**

```python
expect(root.locator(".selection-line .selection-cutout")).to_have_count(1)
expect(root.locator(".selection-line .selection-mark")).to_have_count(1)
expect(root.locator(".selection-point circle")).to_have_attribute("r", "5.5")
assert root.locator(".cube-svg").evaluate(
    "svg => [...svg.children].map(node => node.getAttribute('class'))"
) == [
    "wireframe",
    "axis axis-x",
    "axis axis-y",
    "axis axis-z",
    "selection-plane",
    "selection-line",
    "selection-point",
]
```

- [ ] **Step 3: Add slider and reset assertions**

```python
expect(x_row.locator("input")).to_have_css(
    "background-image", re.compile(r"linear-gradient")
)
assert x_row.locator("input").evaluate(
    "slider => getComputedStyle(slider).getPropertyValue('--slider-color').trim()"
) == "#e74c3c"
root.locator(".reset-button").click()
expect(root.locator(".cube-svg")).not_to_have_class(re.compile(r"has-selection"))
expect(root.locator(".wireframe line").first).to_have_css(
    "stroke-dasharray", "none"
)
```

- [ ] **Step 4: Run the focused test and verify RED**

Run: `uv run pytest tests/test_e2e/test_cube_widget_browser.py -q`

Expected: FAIL because the selected-state classes, cutouts, filled slider background, and 5.5 px point do not exist yet.

---

### Task 2: Implement the SVG selection hierarchy and compact controls

**Files:**
- Modify: `wigglystuff/static/cube-widget.js`
- Modify: `wigglystuff/static/cube-widget.css`
- Test: `tests/test_e2e/test_cube_widget_browser.py`

**Interfaces:**
- Consumes: `locked_order`, `axis_values`, axis configuration traits, and existing render/update callbacks.
- Produces: stable SVG layer classes and CSS variables while preserving the AnyWidget model interface.

- [ ] **Step 1: Add explicit structural-edge classes and selection state**

In `drawWireframe`, add `wireframe-edge` plus `front-edge` or `back-edge` to every line. In `renderSVG`, toggle selection state before appending layers:

```javascript
svg.classList.toggle("has-selection", lockedOrder.length > 0);
```

Use CSS to normalize every structural edge during selection:

```css
.cube-svg.has-selection .wireframe {
  opacity: 0.14;
}

.cube-svg.has-selection .wireframe line {
  stroke-opacity: 1;
  stroke-dasharray: 4 5;
}
```

- [ ] **Step 2: Add clean solid axis layers**

In `drawAxis`, append a surface-colored line before the colored axis line:

```javascript
const cutout = document.createElementNS("http://www.w3.org/2000/svg", "line");
cutout.setAttribute("class", "axis-cutout");
cutout.setAttribute("stroke", "var(--color-surface)");
cutout.setAttribute("stroke-width", lockIndex >= 0 ? "7" : "6");
```

Give the colored line class `axis-line` and arrow class `axis-arrow`. Fade those marks without applying any dash pattern:

```css
.cube-svg.has-selection .axis-line,
.cube-svg.has-selection .axis-arrow {
  opacity: 0.24;
}
```

- [ ] **Step 3: Render selection cutouts and the smaller point**

Append a surface-colored cutout before the selected line and distinguish the colored mark:

```javascript
cutout.setAttribute("class", "selection-cutout");
cutout.setAttribute("stroke", "var(--color-surface)");
cutout.setAttribute("stroke-width", "10");
line.setAttribute("class", "selection-mark");
```

Set the plane fill opacity to `0.5`, point radius to `5.5`, and point stroke to `var(--color-surface)`.

- [ ] **Step 4: Make the control panel compact and give sliders colored fills**

Move the reset button into a `.cube-toolbar`, keep `.cube-controls` as a floating card, and set its visibility from `lockedOrder.length`. For each slider, update:

```javascript
slider.style.setProperty("--slider-color", AXIS_COLORS[axis]);
slider.style.setProperty(
  "--slider-progress",
  `${((slider.value - min) / (max - min)) * 100}%`,
);
```

Use a CSS gradient for the filled track and `var(--slider-color)` for both browser thumb implementations.

- [ ] **Step 5: Run the focused test and verify GREEN**

Run: `uv run pytest tests/test_e2e/test_cube_widget_browser.py -q`

Expected: `1 passed`.

---

### Task 3: Verify the complete CubeWidget port

**Files:**
- Verify: `wigglystuff/cube_widget.py`
- Verify: `demos/cube_widget.py`
- Verify: `tests/test_cube_widget.py`
- Verify: `tests/test_e2e/test_cube_widget_browser.py`

**Interfaces:**
- Consumes: the completed CubeWidget implementation and approved visual behavior.
- Produces: fresh verification evidence for Python, browser, marimo, demo runtime, and full regression coverage.

- [ ] **Step 1: Run the import and traitlet smoke test**

Run:

```bash
uv run python -c "from wigglystuff import CubeWidget; w = CubeWidget(); w.lock_axis('x', 0.75); assert w.plane == {'axis': 'X', 'value': 0.75}; w.reset(); assert w.locked_order == []"
```

Expected: exit code 0.

- [ ] **Step 2: Run focused Python and browser tests**

Run: `uv run pytest tests/test_cube_widget.py tests/test_e2e/test_cube_widget_browser.py -q`

Expected: all tests pass.

- [ ] **Step 3: Validate and execute the marimo demo**

Run: `uv run marimo check demos/cube_widget.py`

Expected: check succeeds.

Run: `uv run demos/cube_widget.py`

Expected: exit code 0 with no runtime error.

- [ ] **Step 4: Run the full test suite**

Run: `uv run pytest`

Expected: all tests pass.

- [ ] **Step 5: Review the final diff and prepare branch handoff**

Run: `git diff origin/main... --check` and `git status --short`.

Expected: no whitespace errors; only the CubeWidget port, approved design/plan, demo, exports, and tests are in scope.
