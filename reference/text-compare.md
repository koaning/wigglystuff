# TextCompare API


 Bases: `AnyWidget`


Side-by-side text comparison widget with hover-based match highlighting.


Compares two texts and highlights matching word sequences, useful for plagiarism detection or finding shared passages between documents.



```
from wigglystuff import TextCompare

compare = TextCompare(
    text_a="The quick brown fox jumps over the lazy dog.",
    text_b="A quick brown fox leaps over a lazy dog."
)
compare
```


Create a TextCompare widget.


  Source code in `wigglystuff/text_compare.py`

```
def __init__(
    self,
    text_a: str = "",
    text_b: str = "",
    min_match_words: int = 3,
    **kwargs: Any,
) -> None:
    """Create a TextCompare widget.

    Args:
        text_a: First text to compare.
        text_b: Second text to compare.
        min_match_words: Minimum number of consecutive words to consider a match.
        **kwargs: Forwarded to ``anywidget.AnyWidget``.
    """
    super().__init__(
        text_a=text_a,
        text_b=text_b,
        min_match_words=min_match_words,
        **kwargs,
    )
    self._compute_matches()
```


## Synced traitlets


| Traitlet | Type | Notes |
| --- | --- | --- |
| `text_a` | `str` | First text to compare. |
| `text_b` | `str` | Second text to compare. |
| `matches` | `list` | List of detected matches, each with start_a, end_a, start_b, end_b, text, and word_count. |
| `selected_match` | `int` | Index of the currently hovered match (-1 if none). |
| `min_match_words` | `int` | Minimum consecutive words to consider a match (default: 3). |
