Find and fix issue #$ARGUMENTS. Follow these steps: 

Ultrathink and use the `gh` cli to pull in as much relevant context as necessary.

1. Understand the issue described in the ticket (comments, associated PRs, etc)
2. Locate the relevant code in our codebase
3. Come up with a plan to create a test to reproduce the error (Test Driven Development) if it is possible and stop to check in with me
4. Implement a solution that addresses the root cause
5. Come up with a plan for testing if one was not already created and stop to check in with me
6. Add appropriate tests (if confirmed by me)
7. Prepare a concise PR description in `commit.md` (follow style of .claude/commands/write-commit.md)
