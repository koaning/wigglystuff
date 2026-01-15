# EnvConfig API

::: wigglystuff.env_config.EnvConfig

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `variables` | `list` | List of variable info dicts with name, status, error, has_validator, value. |
| `all_valid` | `bool` | True when all variables are valid. |

## Helper methods

| Method | Description |
| --- | --- |
| `require_valid()` | Raises `EnvironmentError` if any variable is missing/invalid. |
| `config["KEY"]` | Dictionary-style access to stored values. |
| `"KEY" in config` | Check if a variable is configured and has a value. |
