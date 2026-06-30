# Release Preparation

Prepare a new wigglystuff release. Follow these steps:

## Instructions

1. **Determine the new version**: Read `pyproject.toml` for the current version and the latest entry in `CHANGELOG.md`. If the version has already been bumped, use that. Otherwise, bump the patch version (e.g., 0.2.24 -> 0.2.25).

2. **Bump version** in `pyproject.toml` (if not already done).

3. **Add a changelog entry** at the top of `CHANGELOG.md` following the existing format:
   - Use `## [x.y.z] - YYYY-MM-DD` header with today's date
   - Add `### Added`, `### Changed`, `### Fixed`, or `### Removed` subsections as appropriate
   - Look at the git diff against `main` to determine what changed

4. **Update all documentation locations** for any new widgets:
   - `docs/reference/<widget-name>.md` — create a reference doc following the pattern in existing reference pages (use `::: wigglystuff.module.ClassName` mkdocstrings directive + a synced traitlets table)
   - `zensical.toml` — add the widget to the `nav` Reference section
   - `docs/index.md` — add to the appropriate gallery section (main gallery or 3rd party gallery)
   - `readme.md` — add to the appropriate gallery table (main gallery or 3rd party table)
   - `docs/llms.txt` — add a one-line entry in the appropriate section
   - `CLAUDE.md` — add a row to the quick reference table
   - `wigglystuff/__init__.py` — verify the widget is imported and listed in `__all__`

5. **For 3rd party widgets** (those requiring non-core dependencies like neo4j, torch, wandb):
   - Place them in the "3rd party widgets" section of the galleries (not the main gallery)
   - Use a molab link for the demo instead of a local example page
   - Use `MOLAB_LINK_HERE` as a placeholder if the molab link is not yet available and tell the user they need to fill it in
   - Screenshot path should be `docs/assets/gallery/<widgetname>.webp` — tell the user if one is missing (run `uv run python scripts/png_to_webp.py` if a PNG was added)

6. **Check dependencies**: Read `pyproject.toml` and verify that no 3rd party widget dependency (neo4j, torch, wandb, etc.) has been added to core `[project] dependencies`. These must only appear under `[project.optional-dependencies]` as extras. Core dependencies should only include packages needed by all widgets (anywidget, numpy, pillow, python-dotenv). If a 3rd party dep has leaked into core dependencies, remove it.

7. **Bump demo `wigglystuff==X.Y.Z` pins**: Every `demos/*.py` notebook has a PEP 723 `# /// script` header pinning a published `wigglystuff` version. For any demo that was added or modified in this release (anything in `git diff origin/main -- demos/` since the previous tag), update its pin to the new version. Otherwise `uv run demos/<name>.py` will fetch the old release and the new feature will be missing. Grep `demos/ -l "wigglystuff=="` to find pins; you do not need to bump untouched demos.

8. **Verify nothing is missed**: Check the git diff to make sure all new/changed widgets have corresponding updates in all locations listed above.

9. **Ship it — commit, push, and merge.** "Prepare a release" means the release actually lands on `main`; do NOT stop after the edits to ask whether to commit or merge. Run the mechanics without confirmation: commit the release changes, push the branch, open a PR against `main` (`gh pr create --base main`), and merge it (`gh pr merge`). Only pause if there's a genuine blocker (failing tests, merge conflicts, ambiguous diff) — not for the commit/PR/merge steps themselves.

10. **Report** what was done and what still needs manual action (e.g., adding screenshots, replacing molab link placeholders).
