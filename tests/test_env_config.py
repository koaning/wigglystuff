import os

import pytest

from wigglystuff import EnvConfig


def test_init_with_list():
    config = EnvConfig(["VAR_A", "VAR_B"])
    assert len(config.variables) == 2
    assert config.variables[0]["name"] == "VAR_A"
    assert config.variables[1]["name"] == "VAR_B"


def test_init_with_dict():
    config = EnvConfig({"VAR_A": None, "VAR_B": None})
    assert len(config.variables) == 2


def test_init_with_validator():
    validator_called = []

    def my_validator(value):
        validator_called.append(value)

    # Set env var so validator gets called at init
    os.environ["TEST_VAR"] = "test_value"
    try:
        config = EnvConfig({"TEST_VAR": my_validator})
        assert "test_value" in validator_called
        assert config.variables[0]["status"] == "valid"
    finally:
        del os.environ["TEST_VAR"]


def test_init_empty_raises():
    with pytest.raises(ValueError, match="At least one variable"):
        EnvConfig([])

    with pytest.raises(ValueError, match="At least one variable"):
        EnvConfig({})


def test_getitem_configured():
    os.environ["GETITEM_TEST"] = "hello"
    try:
        config = EnvConfig(["GETITEM_TEST"])
        assert config["GETITEM_TEST"] == "hello"
    finally:
        del os.environ["GETITEM_TEST"]


def test_getitem_unconfigured_key():
    config = EnvConfig(["SOME_VAR"])
    with pytest.raises(KeyError, match="not configured"):
        _ = config["OTHER_VAR"]


def test_getitem_missing_value():
    # Ensure var is not set
    os.environ.pop("MISSING_VAR", None)
    config = EnvConfig(["MISSING_VAR"])
    with pytest.raises(KeyError, match="not set"):
        _ = config["MISSING_VAR"]


def test_contains_configured_and_set():
    os.environ["CONTAINS_TEST"] = "value"
    try:
        config = EnvConfig(["CONTAINS_TEST"])
        assert "CONTAINS_TEST" in config
    finally:
        del os.environ["CONTAINS_TEST"]


def test_contains_configured_but_missing():
    os.environ.pop("MISSING_CONTAINS", None)
    config = EnvConfig(["MISSING_CONTAINS"])
    assert "MISSING_CONTAINS" not in config


def test_contains_not_configured():
    config = EnvConfig(["SOME_VAR"])
    assert "OTHER_VAR" not in config


def test_require_valid_when_all_valid():
    os.environ["VALID_VAR"] = "value"
    try:
        config = EnvConfig(["VALID_VAR"])
        # Should not raise
        config.require_valid()
    finally:
        del os.environ["VALID_VAR"]


def test_require_valid_when_missing():
    os.environ.pop("MISSING_REQUIRED", None)
    config = EnvConfig(["MISSING_REQUIRED"])
    with pytest.raises(EnvironmentError, match="Missing"):
        config.require_valid()


def test_require_valid_when_invalid():
    def failing_validator(value):
        raise ValueError("Invalid key format")

    os.environ["INVALID_VAR"] = "bad_value"
    try:
        config = EnvConfig({"INVALID_VAR": failing_validator})
        assert config.variables[0]["status"] == "invalid"
        with pytest.raises(EnvironmentError, match="Invalid"):
            config.require_valid()
    finally:
        del os.environ["INVALID_VAR"]


def test_validator_exception_captured():
    def validator_with_error(value):
        raise RuntimeError("Custom error message")

    os.environ["ERROR_VAR"] = "value"
    try:
        config = EnvConfig({"ERROR_VAR": validator_with_error})
        assert config.variables[0]["status"] == "invalid"
        assert "Custom error message" in config.variables[0]["error"]
    finally:
        del os.environ["ERROR_VAR"]


def test_preexisting_env_vars_detected():
    os.environ["PREEXIST_A"] = "value_a"
    os.environ["PREEXIST_B"] = "value_b"
    os.environ.pop("PREEXIST_C", None)
    try:
        config = EnvConfig(["PREEXIST_A", "PREEXIST_B", "PREEXIST_C"])
        assert config.variables[0]["status"] == "valid"
        assert config.variables[1]["status"] == "valid"
        assert config.variables[2]["status"] == "missing"
        assert config["PREEXIST_A"] == "value_a"
        assert config["PREEXIST_B"] == "value_b"
    finally:
        del os.environ["PREEXIST_A"]
        del os.environ["PREEXIST_B"]


def test_all_valid_trait():
    os.environ["ALL_VALID_A"] = "a"
    os.environ["ALL_VALID_B"] = "b"
    os.environ.pop("ALL_VALID_C", None)
    try:
        # All set - should be valid
        config_all = EnvConfig(["ALL_VALID_A", "ALL_VALID_B"])
        assert config_all.all_valid is True

        # One missing - should not be valid
        config_partial = EnvConfig(["ALL_VALID_A", "ALL_VALID_C"])
        assert config_partial.all_valid is False
    finally:
        del os.environ["ALL_VALID_A"]
        del os.environ["ALL_VALID_B"]


def test_has_validator_flag():
    def my_validator(v):
        pass

    config = EnvConfig({"WITH_VALIDATOR": my_validator, "WITHOUT_VALIDATOR": None})
    vars_by_name = {v["name"]: v for v in config.variables}
    assert vars_by_name["WITH_VALIDATOR"]["has_validator"] is True
    assert vars_by_name["WITHOUT_VALIDATOR"]["has_validator"] is False


def test_require_valid_with_subset():
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("SUBSET_A", "value_a")
        mp.delenv("SUBSET_B", raising=False)
        config = EnvConfig({"SUBSET_A": None, "SUBSET_B": None})
        config.require_valid(["SUBSET_A"])  # Should pass
        config.require_valid([])  # Empty list should pass
        with pytest.raises(EnvironmentError, match="Missing"):
            config.require_valid(["SUBSET_B"])
        with pytest.raises(ValueError, match="not configured"):
            config.require_valid(["UNKNOWN_VAR"])


@pytest.mark.parametrize("name,default,expected", [
    ("GET_VAR", None, "value"),  # configured and set
    ("GET_VAR", "fallback", "value"),  # set ignores default
    ("MISSING_VAR", None, None),  # configured but missing
    ("MISSING_VAR", "fallback", "fallback"),  # missing uses default
    ("UNKNOWN", None, None),  # not configured
    ("UNKNOWN", "fallback", "fallback"),  # not configured uses default
])
def test_get(name, default, expected):
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("GET_VAR", "value")
        mp.delenv("MISSING_VAR", raising=False)
        config = EnvConfig({"GET_VAR": None, "MISSING_VAR": None})
        assert config.get(name, default) == expected
