# ModuleTreeWidget API

::: wigglystuff.module_tree.ModuleTreeWidget

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `tree` | `dict` | JSON-serializable tree extracted from a PyTorch `nn.Module`. |
| `initial_expand_depth` | `int` | Number of tree levels to expand on first render (default: 1). |
