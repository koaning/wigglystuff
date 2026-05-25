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
    assert widget.gamepad_mapping == {
        "0": "previous",
        "1": "accept",
        "2": "fail",
        "3": "defer",
        "4": "save",
        "5": "mic",
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
    assert widget.gamepad_mapping == {
        "0": "left",
        "1": "middle",
        "2": "right",
        "3": "save",
        "4": "mic",
    }


def test_annotation_custom_keyboard_mapping_does_not_follow_actions():
    widget = AnnotationWidget(
        actions=["left", "right"],
        keyboard_mapping={"a": "left", "d": "right"},
    )
    assert widget.keyboard_mapping == {"a": "left", "d": "right"}

    widget.actions = ["accept", "fail"]
    assert widget.keyboard_mapping == {"a": "left", "d": "right"}


def test_annotation_custom_gamepad_mapping_does_not_follow_actions():
    widget = AnnotationWidget(
        actions=["left", "right"],
        gamepad_mapping={"0": "left", "1": "right"},
    )
    assert widget.gamepad_mapping == {"0": "left", "1": "right"}

    widget.actions = ["accept", "fail"]
    assert widget.gamepad_mapping == {"0": "left", "1": "right"}


def test_annotation_empty_values_are_explicit():
    widget = AnnotationWidget(
        actions=[],
        keyboard_mapping={},
        gamepad_mapping={},
    )
    assert widget.actions == []
    assert widget.keyboard_mapping == {}
    assert widget.gamepad_mapping == {}
