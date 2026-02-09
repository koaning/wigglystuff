# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "anywidget",
#     "wandb",
#     "traitlets",
#     "marimo>=0.19.9",
# ]
# ///

import marimo

__generated_with = "0.19.9"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Live wandb data via anywidget

    This demo starts a real wandb run, logs metrics in a background thread,
    and the widget polls the wandb GraphQL API from JavaScript to show data
    appearing in real time. No iframe, no cookies needed.
    """)
    return


@app.cell
def _():
    import anywidget
    import traitlets

    class WandbLiveWidget(anywidget.AnyWidget):
        _api_key = traitlets.Unicode().tag(sync=True)
        _entity = traitlets.Unicode().tag(sync=True)
        _project = traitlets.Unicode().tag(sync=True)
        _run_name = traitlets.Unicode().tag(sync=True)
        _keys = traitlets.List(traitlets.Unicode()).tag(sync=True)
        _poll_seconds = traitlets.Int(5).tag(sync=True)

        _esm = """
        async function fetchHistory(apiKey, entity, project, runName, keys, minStep) {
            const query = `
                query RunSampledHistory($project: String!, $entity: String!, $name: String!, $specs: [JSONString!]!) {
                    project(name: $project, entityName: $entity) {
                        run(name: $name) {
                            sampledHistory(specs: $specs)
                        }
                    }
                }
            `;
            const specObj = { keys: [...keys, "_step"], samples: 500 };
            if (minStep > 0) specObj.minStep = minStep;
            const variables = { entity, project, name: runName, specs: [JSON.stringify(specObj)] };
            const creds = btoa("api:" + apiKey);

            const resp = await fetch("https://api.wandb.ai/graphql", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": "Basic " + creds,
                },
                body: JSON.stringify({ query, variables }),
            });

            if (!resp.ok) throw new Error("HTTP " + resp.status);
            const data = await resp.json();
            if (data.errors) throw new Error(data.errors.map(e => e.message).join(", "));
            return data.data.project.run.sampledHistory[0] || [];
        }

        async function fetchRunState(apiKey, entity, project, runName) {
            const query = `
                query RunState($project: String!, $entity: String!, $name: String!) {
                    project(name: $project, entityName: $entity) {
                        run(name: $name) {
                            state
                        }
                    }
                }
            `;
            const variables = { entity, project, name: runName };
            const creds = btoa("api:" + apiKey);

            const resp = await fetch("https://api.wandb.ai/graphql", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": "Basic " + creds,
                },
                body: JSON.stringify({ query, variables }),
            });

            if (!resp.ok) throw new Error("HTTP " + resp.status);
            const data = await resp.json();
            if (data.errors) throw new Error(data.errors.map(e => e.message).join(", "));
            return data.data.project.run.state;
        }

        function render({ model, el }) {
            const allRows = [];
            let maxStepSeen = -1;

            const container = document.createElement("div");
            container.style.fontFamily = "system-ui, sans-serif";
            container.style.padding = "12px";

            const statusEl = document.createElement("div");
            statusEl.style.marginBottom = "8px";
            statusEl.style.color = "#666";
            statusEl.style.fontSize = "13px";

            const tableEl = document.createElement("pre");
            tableEl.style.fontSize = "13px";
            tableEl.style.background = "#f5f5f5";
            tableEl.style.padding = "12px";
            tableEl.style.borderRadius = "6px";
            tableEl.style.overflow = "auto";
            tableEl.style.maxHeight = "400px";

            container.appendChild(statusEl);
            container.appendChild(tableEl);
            el.appendChild(container);

            function renderTable() {
                if (allRows.length === 0) {
                    tableEl.textContent = "(no data yet — waiting for metrics)";
                    return;
                }
                const cols = Object.keys(allRows[0]);
                const header = cols.map(c => c.padStart(14)).join(" | ");
                const sep = cols.map(() => "-".repeat(14)).join("-+-");
                const body = allRows.map(row =>
                    cols.map(c => {
                        const v = row[c];
                        return (typeof v === "number" ? v.toFixed(6) : String(v)).padStart(14);
                    }).join(" | ")
                ).join("\\n");
                tableEl.textContent = header + "\\n" + sep + "\\n" + body;
            }

            async function poll() {
                const apiKey = model.get("_api_key");
                const entity = model.get("_entity");
                const project = model.get("_project");
                const runName = model.get("_run_name");
                const keys = model.get("_keys");

                if (!apiKey || !runName) {
                    statusEl.textContent = "Waiting for run to start...";
                    return;
                }

                try {
                    const [newRows, state] = await Promise.all([
                        fetchHistory(apiKey, entity, project, runName, keys, maxStepSeen + 1),
                        fetchRunState(apiKey, entity, project, runName),
                    ]);
                    const now = new Date().toLocaleTimeString();

                    if (newRows.length > 0) {
                        allRows.push(...newRows);
                        const newMax = Math.max(...newRows.map(r => r._step));
                        maxStepSeen = Math.max(maxStepSeen, newMax);
                        statusEl.textContent = "+" + newRows.length + " new rows (total: " + allRows.length + ") at " + now;
                    } else {
                        statusEl.textContent = "no new data, total: " + allRows.length + " rows (checked " + now + ")";
                    }

                    renderTable();

                    if (state !== "running") {
                        clearInterval(interval);
                        statusEl.textContent += " — run " + state + ", polling stopped.";
                    }
                } catch (err) {
                    statusEl.textContent = "Error: " + err.message;
                    statusEl.style.color = "red";
                }
            }

            poll();
            const interval = setInterval(poll, (model.get("_poll_seconds") || 5) * 1000);
            return () => clearInterval(interval);
        }

        export default { render };
        """

    return (WandbLiveWidget,)


@app.cell
def _():
    import wandb
    import math

    api = wandb.Api()
    api_key = api.api_key

    # Start a real run that we'll log to
    run = wandb.init(project="jupyter-projo", name="anywidget-demo")
    print(f"Run: {run.name} ({run.id})")
    print(f"Entity: {run.entity}, Project: {run.project}")
    return api_key, math, run


@app.cell(hide_code=True)
def _(WandbLiveWidget, api_key, run):
    widget = WandbLiveWidget(
        _api_key=api_key,
        _entity=run.entity,
        _project=run.project,
        _run_name=run.id,
        _keys=["loss", "acc"],
        _poll_seconds=10,
    )
    widget
    return (widget,)


@app.cell
def _(math, run, widget):
    import time

    widget

    # Simulate training: log metrics slowly so you can watch the widget update
    for step in range(60):
        t = step / 59
        loss = math.exp(-3 * t) + 0.01
        acc = 1 - math.exp(-3 * t)
        run.log({"loss": loss, "acc": acc})
        time.sleep(2)

    run.finish()
    print("Training done!")
    return


if __name__ == "__main__":
    app.run()
