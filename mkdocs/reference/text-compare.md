# TextCompare API

::: wigglystuff.text_compare.TextCompare

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `text_a` | `str` | First text to compare. |
| `text_b` | `str` | Second text to compare. |
| `matches` | `list` | List of detected matches, each with start_a, end_a, start_b, end_b, text, and word_count. |
| `selected_match` | `int` | Index of the currently hovered match (-1 if none). |
| `min_match_words` | `int` | Minimum consecutive words to consider a match (default: 3). |
