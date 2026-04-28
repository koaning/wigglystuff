import marimo

__generated_with = "0.23.3"
app = marimo.App(width="medium")


@app.cell
def _():
    import importlib.util
    import marimo as mo
    from pathlib import Path

    module_path = Path.cwd() / "wigglystuff" / "env_config.py"
    spec = importlib.util.spec_from_file_location("env_config_under_test", module_path)
    env_config = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(env_config)

    config = mo.ui.anywidget(env_config.EnvConfig(["WIGGLYSTUFF_EXPORT_SECRET"]))
    config
    return


if __name__ == "__main__":
    app.run()
