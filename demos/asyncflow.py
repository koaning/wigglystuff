# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "anywidget",
#     "marimo",
#     "polars",
#     "wigglystuff==0.5.15",
# ]
# ///

import marimo

__generated_with = "0.23.14"
app = marimo.App(width="full")


@app.cell
def _():
    from pathlib import Path
    import sys

    import marimo as mo

    repo_root = Path(__file__).resolve().parents[1]
    if (repo_root / "wigglystuff").exists():
        sys.path.insert(0, str(repo_root))

    from wigglystuff import AsyncFlow

    return AsyncFlow, mo


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## AsyncFlow

    `await AsyncFlow.trace(main())` runs a coroutine on the notebook's own event
    loop and streams its task activity into a **live swimlane timeline** — one
    lane per task, solid bars running, hatched bars suspended at an `await`. The
    bars fill in *as the run happens* (watch worker **D** linger while A, B, C
    finish early). Requires Python 3.12+ (`sys.monitoring`).
    """)
    return


@app.cell
def _():
    import random 
    import asyncio

    async def worker(name, delay):
        await asyncio.sleep(delay)
        return name

    async def multi_worker(name, delay): 
        await asyncio.sleep(delay + 2)
        return await asyncio.gather(
            worker(name, delay + random.random()),
            worker(name, delay + random.random()),
        )

    async def main():
        out = await asyncio.gather(
            multi_worker("A", 0.3),
            worker("B", 1.1),
            worker("C", 0.2),
            worker("D", 2.0),
        )
        await asyncio.sleep(1)

    return (main,)


@app.cell
async def _(AsyncFlow, main):
    flow = await AsyncFlow.trace(main())
    return (flow,)


@app.cell
def _(flow):
    import polars as pl 

    pl.DataFrame(flow.events)
    return


@app.cell
def _(flow, mo):
    mo.md(f"""
    **Result:** `{flow.result}` — {len(flow.events)} events captured
    """)
    return


if __name__ == "__main__":
    app.run()
