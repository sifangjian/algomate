import sys
import types

try:
    import _overlapped
except OSError:
    sys.modules["_overlapped"] = types.ModuleType("_overlapped")
    import asyncio

    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
