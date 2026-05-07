import sys
import types

_overlapped = types.ModuleType('_overlapped')
_overlapped.CreateIoCompletionPort = lambda *a, **kw: 1
_overlapped.GetQueuedCompletionStatus = lambda *a, **kw: (0, 0, 0)
_overlapped.PostQueuedCompletionStatus = lambda *a, **kw: True
_overlapped.OVERLAPPED = type('OVERLAPPED', (), {'__init__': lambda self: None})
_overlapped.NULL = 0
_overlapped.INVALID_HANDLE_VALUE = -1
sys.modules['_overlapped'] = _overlapped

import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import pytest
sys.exit(pytest.main())
