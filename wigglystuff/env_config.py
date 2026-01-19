"""EnvConfig widget for environment variable management."""

import os
from pathlib import Path
from typing import Any, Callable, Optional, Sequence, Union

import anywidget
import traitlets

ValidatorFn = Callable[[str], None]


class EnvConfig(anywidget.AnyWidget):
    """Environment variable configuration widget for secure API key management.

    Displays a UI for configuring environment variables, with password-style
    masking and optional validation callbacks. Useful for notebooks that need
    API keys configured before proceeding.

    Values are stored internally and never written back to os.environ.

    Examples:
        ```python
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
    """

    _esm = Path(__file__).parent / "static" / "env-config.js"
    _css = Path(__file__).parent / "static" / "env-config.css"

    # List of variable info dicts: {"name": str, "status": str, "error": str|None, "has_validator": bool}
    variables = traitlets.List(traitlets.Dict()).tag(sync=True)
    all_valid = traitlets.Bool(False).tag(sync=True)

    # JS -> Python: user entered a value
    _pending_value = traitlets.Dict({}).tag(sync=True)

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

    def _validate(self, name: str, value: str) -> dict:
        """Run validator for a variable and return status dict."""
        validator = self._validators.get(name)
        if validator is None:
            return {"status": "valid", "error": None}
        try:
            validator(value)
            return {"status": "valid", "error": None}
        except Exception as e:
            return {"status": "invalid", "error": str(e)}

    @traitlets.observe("_pending_value")
    def _on_pending_value(self, change: dict) -> None:
        """Handle value submitted from JavaScript frontend."""
        data = change["new"]
        if not data or "name" not in data:
            return

        name = data["name"]
        value = data["value"]

        # Run validation (synchronous, no need for "validating" intermediate state)
        result = self._validate(name, value)

        if result["status"] == "valid":
            # Store internally only - never touch os.environ
            self._values[name] = value

        # Update state in one go - pass the entered value so it can be displayed
        self._set_var_status(name, result["status"], result["error"], value)
        self._recalc_all_valid()

    def _set_var_status(
        self,
        name: str,
        status: str,
        error: Optional[str],
        value: Optional[str] = None,
    ) -> None:
        """Update status for a specific variable."""
        vars_copy = [dict(v) for v in self.variables]
        for v in vars_copy:
            if v["name"] == name:
                v["status"] = status
                v["error"] = error
                # Include the entered value so JS can display it (even if invalid)
                v["value"] = value if value is not None else self._values.get(name, "")
                break
        self.variables = vars_copy

    def _recalc_all_valid(self) -> None:
        """Recalculate all_valid based on current variable statuses."""
        self.all_valid = all(v["status"] == "valid" for v in self.variables)

    def require_valid(self) -> None:
        """Assert all environment variables are valid.

        Raises:
            EnvironmentError: If any variable is missing or invalid.
        """
        if self.all_valid:
            return

        missing = [v["name"] for v in self.variables if v["status"] == "missing"]
        invalid = [
            f"{v['name']} ({v['error']})"
            for v in self.variables
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

    def __contains__(self, name: str) -> bool:
        """Check if a variable is configured and has a value."""
        return name in self._var_names and name in self._values
