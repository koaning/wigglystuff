import pytest

from wigglystuff import TextCompare


def test_basic_match_detection():
    widget = TextCompare(
        text_a="the quick brown fox jumps over the lazy dog",
        text_b="a quick brown fox leaps over a lazy dog",
    )

    # Should find "quick brown fox" as a match (3 words)
    assert len(widget.matches) >= 1
    match_texts = [m["text"] for m in widget.matches]
    assert "quick brown fox" in match_texts


def test_empty_texts():
    widget = TextCompare(text_a="", text_b="")
    assert widget.matches == []


def test_no_matches():
    widget = TextCompare(
        text_a="hello world",
        text_b="goodbye universe",
        min_match_words=2,
    )
    assert widget.matches == []


def test_single_word_no_match_by_default():
    # Default min_match_words is 3, so single words shouldn't match
    widget = TextCompare(
        text_a="hello",
        text_b="hello",
    )
    assert widget.matches == []


def test_min_match_words_respected():
    widget = TextCompare(
        text_a="one two",
        text_b="one two",
        min_match_words=2,
    )
    assert len(widget.matches) == 1
    assert widget.matches[0]["word_count"] == 2


def test_min_match_words_validation():
    with pytest.raises(Exception):
        TextCompare(text_a="test", text_b="test", min_match_words=0)


def test_match_positions():
    widget = TextCompare(
        text_a="start match here end",
        text_b="begin match here finish",
        min_match_words=2,
    )

    assert len(widget.matches) == 1
    match = widget.matches[0]
    assert match["start_a"] == 1  # "match" is at index 1 in text_a
    assert match["end_a"] == 3    # "here" ends at index 3
    assert match["start_b"] == 1  # "match" is at index 1 in text_b
    assert match["end_b"] == 3


def test_recompute_on_threshold_change():
    widget = TextCompare(
        text_a="one two three four",
        text_b="one two three four",
        min_match_words=2,
    )
    assert len(widget.matches) == 1
    assert widget.matches[0]["word_count"] == 4

    # Raising threshold should filter out the match
    widget.min_match_words = 5
    assert widget.matches == []

    # Lowering threshold should bring it back
    widget.min_match_words = 3
    assert len(widget.matches) == 1


def test_multiple_matches():
    widget = TextCompare(
        text_a="the quick brown fox and the lazy dog sleep",
        text_b="a quick brown fox runs while a lazy dog rests",
        min_match_words=2,
    )

    # Should find at least "quick brown fox" and "lazy dog"
    match_texts = [m["text"] for m in widget.matches]
    assert any("quick brown fox" in t for t in match_texts)
    assert any("lazy dog" in t for t in match_texts)
