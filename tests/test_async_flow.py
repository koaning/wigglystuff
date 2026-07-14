import asyncio
import sys

import pytest

from wigglystuff.async_flow import AsyncFlowLogger


@pytest.fixture
def occupied_profiler_slot():
    """Hold the PROFILER slot with a fake tool, freeing it on teardown."""
    profiler_id = sys.monitoring.PROFILER_ID
    sys.monitoring.use_tool_id(profiler_id, "pretend-profiler")
    yield profiler_id
    if sys.monitoring.get_tool(profiler_id) == "pretend-profiler":
        sys.monitoring.free_tool_id(profiler_id)


@pytest.mark.skipif(sys.version_info < (3, 12), reason="needs sys.monitoring")
def test_logger_does_not_evict_an_active_profiler(occupied_profiler_slot):
    async def go():
        async with AsyncFlowLogger(files=[__file__]):
            pass

    asyncio.run(go())
    # The pre-existing profiler/coverage tool must survive the logger's run.
    assert sys.monitoring.get_tool(occupied_profiler_slot) == "pretend-profiler"
