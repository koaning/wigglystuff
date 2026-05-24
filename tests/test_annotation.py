from wigglystuff import AnnotationWidget


def test_annotation_actions_do_not_include_footer_save_by_default():
    widget = AnnotationWidget()
    assert widget.actions == ["previous", "accept", "fail", "defer"]
    assert widget.show_save is True
    assert widget.keyboard_mapping == {
        "1": "previous",
        "2": "accept",
        "3": "fail",
        "4": "defer",
        "s": "save",
        "m": "mic",
    }


def test_annotation_show_save_is_independent_from_actions():
    widget = AnnotationWidget(
        actions=["previous", "accept"],
        show_save=False,
    )
    assert widget.actions == ["previous", "accept"]
    assert widget.show_save is False

    widget.show_save = True
    assert widget.actions == ["previous", "accept"]
    assert widget.show_save is True


def test_annotation_default_keyboard_mapping_follows_actions():
    widget = AnnotationWidget(actions=["left", "middle", "right"])
    assert widget.keyboard_mapping == {
        "1": "left",
        "2": "middle",
        "3": "right",
        "s": "save",
        "m": "mic",
    }

    widget.actions = ["accept", "defer"]
    assert widget.keyboard_mapping == {
        "1": "accept",
        "2": "defer",
        "s": "save",
        "m": "mic",
    }


def test_annotation_custom_keyboard_mapping_does_not_follow_actions():
    widget = AnnotationWidget(
        actions=["left", "right"],
        keyboard_mapping={"a": "left", "d": "right"},
    )
    assert widget.keyboard_mapping == {"a": "left", "d": "right"}

    widget.actions = ["accept", "fail"]
    assert widget.keyboard_mapping == {"a": "left", "d": "right"}
