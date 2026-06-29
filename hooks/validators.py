"""Output-based validator registry for infrastructure checks.

Shell exit codes are unreliable — pipes, subshells, and || masks mask failures.
Each check gets a validator function that parses stdout and returns (passed, detail).
"""
from __future__ import annotations
import re


def _empty_output(stdout: str) -> tuple[bool, str]:
    clean = stdout.strip()
    return (clean == "", clean if clean else "clean")


def _not_empty(stdout: str) -> tuple[bool, str]:
    clean = stdout.strip()
    return (clean != "", clean if clean else "empty")


def _contains(expected: str, stdout: str) -> tuple[bool, str]:
    found = expected.lower() in stdout.lower()
    return (found, stdout.strip()[:200])


def _equals(expected: str, stdout: str) -> tuple[bool, str]:
    return (stdout.strip() == expected, stdout.strip()[:200])


def _regex(pattern: str, stdout: str) -> tuple[bool, str]:
    match = re.search(pattern, stdout)
    return (match is not None, match.group(0) if match else stdout.strip()[:200])


VALIDATORS: dict[str, callable] = {
    "empty_output": _empty_output,
    "not_empty": _not_empty,
}


def get_validator(spec: str) -> callable:
    """Return a validator function for the given spec string.

    Supported formats:
        "empty_output"       — pass if stdout is empty
        "not_empty"          — pass if stdout is non-empty
        "contains:text"      — pass if stdout contains text (case-insensitive)
        "equals:text"        — pass if stdout exactly equals text (stripped)
        "regex:pattern"      — pass if regex matches anywhere in stdout
    """
    if spec in VALIDATORS:
        return VALIDATORS[spec]

    if ":" in spec:
        kind, arg = spec.split(":", 1)
        if kind == "contains":
            return lambda stdout: _contains(arg, stdout)
        if kind == "equals":
            return lambda stdout: _equals(arg, stdout)
        if kind == "regex":
            return lambda stdout: _regex(arg, stdout)

    return lambda stdout: (True, f"no validator for '{spec}', defaulting to pass")


def validate_exit_code(returncode: int, stdout: str) -> tuple[bool, str]:
    """Fallback validator when no spec is configured."""
    return (returncode == 0, stdout.strip()[:200])
