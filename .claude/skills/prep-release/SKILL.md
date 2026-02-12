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
   - `mkdocs/reference/<widget-name>.md` — create a reference doc following the pattern in existing reference pages (use `::: wigglystuff.module.ClassName` mkdocstrings directive + a synced traitlets table)
   - `mkdocs.yml` — add the widget to the `nav` Reference section
   - `mkdocs/index.md` — add to the appropriate gallery section (main gallery or 3rd party gallery)
   - `readme.md` — add to the appropriate gallery table (main gallery or 3rd party table)
   - `mkdocs/llms.txt` — add a one-line entry in the appropriate section
   - `CLAUDE.md` — add a row to the quick reference table
   - `wigglystuff/__init__.py` — verify the widget is imported and listed in `__all__`

5. **For 3rd party widgets** (those requiring non-core dependencies like neo4j, torch, wandb):
   - Place them in the "3rd party widgets" section of the galleries (not the main gallery)
   - Use a molab link for the demo instead of a local example page
   - Use `MOLAB_LINK_HERE` as a placeholder if the molab link is not yet available and tell the user they need to fill it in
   - Screenshot path should be `mkdocs/assets/gallery/<widgetname>.png` — tell the user if one is missing

6. **Verify nothing is missed**: Check the git diff to make sure all new/changed widgets have corresponding updates in all locations listed above.

7. **Report** what was done and what still needs manual action (e.g., adding screenshots, replacing molab link placeholders).
