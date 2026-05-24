from wigglystuff import AnnotationWidget


def test_annotation_actions_do_not_include_footer_save_by_default():
    widget = AnnotationWidget()
    assert widget.actions == ["previous", "accept", "fail", "defer"]
    assert widget.show_save is True


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
