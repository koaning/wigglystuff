"""TextCompare widget for side-by-side text comparison with match highlighting."""

import difflib
from pathlib import Path
from typing import Any, List

import anywidget
import traitlets


class TextCompare(anywidget.AnyWidget):
    """Side-by-side text comparison widget with hover-based match highlighting.

    Compares two texts and highlights matching word sequences, useful for
    plagiarism detection or finding shared passages between documents.

    Examples:
        ```python
        compare = TextCompare(
            text_a="The quick brown fox jumps over the lazy dog.",
            text_b="A quick brown fox leaps over a lazy dog."
        )
        compare
        ```
    """

    _esm = Path(__file__).parent / "static" / "text-compare.js"
    _css = Path(__file__).parent / "static" / "text-compare.css"

    text_a = traitlets.Unicode("").tag(sync=True)
    text_b = traitlets.Unicode("").tag(sync=True)
    matches = traitlets.List([]).tag(sync=True)
    selected_match = traitlets.Int(-1).tag(sync=True)
    min_match_words = traitlets.Int(3).tag(sync=True)

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

    @traitlets.observe("min_match_words")
    def _on_threshold_change(self, change: Any) -> None:
        """Recompute matches when threshold changes."""
        self._compute_matches()

    def _compute_matches(self) -> None:
        """Compute matching word sequences between the two texts."""
        if not self.text_a or not self.text_b:
            self.matches = []
            return

        words_a = self.text_a.split()
        words_b = self.text_b.split()

        matcher = difflib.SequenceMatcher(None, words_a, words_b)
        matches: List[dict] = []

        for block in matcher.get_matching_blocks():
            if block.size >= self.min_match_words:
                matches.append({
                    "start_a": block.a,
                    "end_a": block.a + block.size,
                    "start_b": block.b,
                    "end_b": block.b + block.size,
                    "text": " ".join(words_a[block.a:block.a + block.size]),
                    "word_count": block.size,
                })

        self.matches = matches

    @traitlets.validate("min_match_words")
    def _validate_min_match_words(self, proposal: dict[str, Any]) -> int:
        """Ensure min_match_words is at least 1."""
        value = proposal["value"]
        if value < 1:
            raise traitlets.TraitError("min_match_words must be at least 1.")
        return value
