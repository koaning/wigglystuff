import threading

import pytest

from wigglystuff import ProgressBar


def test_concurrent_updates_with_rich():
    """Setting .value from many threads must not race the lazy rich setup."""
    pytest.importorskip("rich")
    for _ in range(100):
        bar = ProgressBar(max_value=16)
        errors = []

        def tick():
            try:
                bar.value += 1
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=tick) for _ in range(16)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        bar._stop_rich()
        assert errors == []
