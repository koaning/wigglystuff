# EnvConfig API


 Bases: `AnyWidget`


Environment variable configuration widget for secure API key management.


Displays a UI for configuring environment variables, with password-style masking and optional validation callbacks. Useful for notebooks that need API keys configured before proceeding.


Values are stored internally and never written back to os.environ.



```
from wigglystuff import EnvConfig

# Simple usage - just check vars exist
config = EnvConfig(["OPENAI_API_KEY", "ANTHROPIC_API_KEY"])
config

# With validators
config = EnvConfig({
    "OPENAI_API_KEY": lambda k: openai.Client(api_key=k).models.list(),
    "ANTHROPIC_API_KEY": None,  # Just check existence
})

# Block until valid
config.require_valid()

# Access values
config["OPENAI_API_KEY"]
```


Create an EnvConfig widget.


  Source code in `wigglystuff/env_config.py`

```
def __init__(
    self,
    variables: Union[Sequence[str], dict[str, Optional[ValidatorFn]]],
    **kwargs: Any,
) -> None:
    """Create an EnvConfig widget.

    Args:
        variables: Either a sequence of variable names, or a dict mapping
            names to optional validator functions. Validators should raise
            an exception on failure.
        **kwargs: Forwarded to ``anywidget.AnyWidget``.
    """
    # Normalize to dict
    if isinstance(variables, (list, tuple)):
        variables = {name: None for name in variables}

    if not variables:
        raise ValueError("At least one variable name is required.")

    self._validators: dict[str, Optional[ValidatorFn]] = dict(variables)
    self._var_names: list[str] = list(variables.keys())
    self._values: dict[str, str] = {}  # Internal storage, never touches os.environ

    # Build initial state by checking current environment
    initial_vars = []
    for name in self._var_names:
        value = os.environ.get(name)
        has_validator = variables[name] is not None
        if value is not None:
            self._values[name] = value
            status = self._validate(name, value)
            # Include value for JS to display (browser masks it)
            status["value"] = value
        else:
            status = {"status": "missing", "error": None, "value": ""}
        initial_vars.append(
            {"name": name, "has_validator": has_validator, **status}
        )

    super().__init__(
        variables=initial_vars,
        all_valid=all(v["status"] == "valid" for v in initial_vars),
        **kwargs,
    )
```


## __contains__


```
__contains__(name: str) -> bool
```


Check if a variable is configured and has a value.

 Source code in `wigglystuff/env_config.py`

```
def __contains__(self, name: str) -> bool:
    """Check if a variable is configured and has a value."""
    return name in self._var_names and name in self._values
```


## __getitem__


```
__getitem__(name: str) -> str
```


Get variable value by name.




| Type | Description |
| --- | --- |
| `str` | The value (from os.environ at init time, or entered via widget). |



| Type | Description |
| --- | --- |
| `KeyError` | If the variable is not configured or not set. |

 Source code in `wigglystuff/env_config.py`

```
def __getitem__(self, name: str) -> str:
    """Get variable value by name.

    Args:
        name: The variable name.

    Returns:
        The value (from os.environ at init time, or entered via widget).

    Raises:
        KeyError: If the variable is not configured or not set.
    """
    if name not in self._var_names:
        raise KeyError(f"{name!r} is not configured in this EnvConfig")
    if name not in self._values:
        raise KeyError(f"{name!r} is not set")
    return self._values[name]
```


## get


```
get(
    name: str, default: Optional[str] = None
) -> Optional[str]
```


Get variable value by name, with optional default.




| Type | Description |
| --- | --- |
| `Optional[str]` | The value if set, otherwise the default. |

 Source code in `wigglystuff/env_config.py`

```
def get(self, name: str, default: Optional[str] = None) -> Optional[str]:
    """Get variable value by name, with optional default.

    Args:
        name: The variable name.
        default: Value to return if variable is not configured or not set.

    Returns:
        The value if set, otherwise the default.
    """
    if name not in self._var_names or name not in self._values:
        return default
    return self._values[name]
```


## require_valid


```
require_valid(
    variables: Optional[Sequence[str]] = None,
) -> None
```


Assert environment variables are valid.




| Type | Description |
| --- | --- |
| `EnvironmentError` | If any checked variable is missing or invalid. |
| `ValueError` | If a variable name is not configured in this widget. |

 Source code in `wigglystuff/env_config.py`

```
def require_valid(self, variables: Optional[Sequence[str]] = None) -> None:
    """Assert environment variables are valid.

    Args:
        variables: Optional list of variable names to check. If None,
            checks all configured variables.

    Raises:
        EnvironmentError: If any checked variable is missing or invalid.
        ValueError: If a variable name is not configured in this widget.
    """
    configured = {v["name"] for v in self.variables}
    to_check = configured if variables is None else set(variables)
    unknown = to_check - configured
    if unknown:
        raise ValueError(
            f"Variable(s) not configured in this EnvConfig: {', '.join(sorted(unknown))}"
        )

    # Filter to only checked variables
    checked_vars = [v for v in self.variables if v["name"] in to_check]

    # Early return if all checked vars are valid
    if all(v["status"] == "valid" for v in checked_vars):
        return

    missing = [v["name"] for v in checked_vars if v["status"] == "missing"]
    invalid = [
        f"{v['name']} ({v['error']})"
        for v in checked_vars
        if v["status"] == "invalid"
    ]

    msg_parts = []
    if missing:
        msg_parts.append(f"Missing: {', '.join(missing)}")
    if invalid:
        msg_parts.append(f"Invalid: {', '.join(invalid)}")

    raise EnvironmentError(
        f"Environment configuration incomplete. {'; '.join(msg_parts)}. "
        "Please set all required variables using the widget above."
    )
```


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
