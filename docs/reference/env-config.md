---
title: "EnvConfig: API key input for notebooks"
description: EnvConfig collects API keys in a Colab or marimo notebook with masked inputs and optional per-key validators, keeping the values out of os.environ.
image: envconfig
image_alt: EnvConfig widget showing three masked API key fields with valid and invalid status icons
---

# EnvConfig API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="envconfig" data-demo-title="EnvConfig live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/envconfig.webp" alt="EnvConfig widget showing three masked API key fields with valid and invalid status icons" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

`EnvConfig` renders one masked input per environment variable so a notebook can ask for
API keys instead of having them pasted into a cell. Pass a list of names for a plain
existence check, or a dict mapping names to validator callables — a validator that raises
marks that row invalid and shows the message. Anything already set in `os.environ` is
picked up as a starting value, but the widget never writes back to it and never syncs the
values to the browser; you read them with `config["KEY"]`, and `require_valid()` raises
when something is still missing so the rest of the notebook stops early.

See also: [CellTour](cell-tour.md) for walking a first-time reader through setup,
[CopyToClipboard](copy-to-clipboard.md) for handing a generated value back to them, and
[ApiDoc](api-doc.md) for documenting the client you just configured.

::: wigglystuff.env_config.EnvConfig

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `variables` | `list` | List of variable info dicts with name, status, error, and has_validator. Secret values are not synced. |
| `all_valid` | `bool` | True when all variables are valid. |

## Helper methods

| Method | Description |
| --- | --- |
| `require_valid()` | Raises `EnvironmentError` if any variable is missing/invalid. |
| `config["KEY"]` | Dictionary-style access to stored values. |
| `"KEY" in config` | Check if a variable is configured and has a value. |
