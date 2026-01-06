---
allowed-tools: Bash(uvx marimo check:*), Edit()
description: Check a marimo notebook
color: purple
---

## Context

This is the output of the "uvx marimo check --fix $ARGUMENTS" command:

!`uvx marimo check --fix $ARGUMENTS || true`

## Your task

Only (!) if the context suggests we need to edit the notebook, read the file $ARGUMENTS, then fix any warnings or errors shown in the output above. Do not make edits or read the file if there are no issues.
