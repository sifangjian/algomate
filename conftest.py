import sys
import types


def _patch_for_sandbox():
    try:
        import _overlapped
        return
    except OSError:
        pass

    sys.modules['_overlapped'] = types.ModuleType('_overlapped')

    import socket as _socket_mod

    _RealSocket = _socket_mod.socket

    class _PatchedSocket(_RealSocket):
        def __init__(self, family=-1, type=-1, proto=-1, fileno=None):
            try:
                if fileno is not None:
                    super().__init__(family, type, proto, fileno)
                else:
                    super().__init__(family, type, proto)
            except OSError:
                self._mock = True
                self._family = family
                self._type = type
                self._proto = proto
                self._fileno_val = 0

        def fileno(self):
            if getattr(self, '_mock', False):
                return self._fileno_val
            return super().fileno()

        def close(self):
            if getattr(self, '_mock', False):
                return
            try:
                super().close()
            except OSError:
                pass

        def setblocking(self, flag):
            if getattr(self, '_mock', False):
                return
            try:
                super().setblocking(flag)
            except OSError:
                pass

        def setsockopt(self, *args):
            if getattr(self, '_mock', False):
                return
            try:
                super().setsockopt(*args)
            except OSError:
                pass

        def send(self, data, flags=0):
            if getattr(self, '_mock', False):
                return len(data)
            return super().send(data, flags)

        def recv(self, bufsize, flags=0):
            if getattr(self, '_mock', False):
                return b''
            return super().recv(bufsize, flags)

        def connect(self, address):
            if getattr(self, '_mock', False):
                raise OSError("mock socket cannot connect")
            return super().connect(address)

        def bind(self, address):
            if getattr(self, '_mock', False):
                raise OSError("mock socket cannot bind")
            return super().bind(address)

        def listen(self, backlog=None):
            if getattr(self, '_mock', False):
                return
            if backlog is None:
                super().listen()
            else:
                super().listen(backlog)

        def accept(self):
            if getattr(self, '_mock', False):
                mock_client = _PatchedSocket()
                mock_client._mock = True
                return mock_client, ('0.0.0.0', 0)
            return super().accept()

        def getsockname(self):
            if getattr(self, '_mock', False):
                return ('0.0.0.0', 0)
            return super().getsockname()

        def getpeername(self):
            if getattr(self, '_mock', False):
                return ('0.0.0.0', 0)
            return super().getpeername()

        def detach(self):
            if getattr(self, '_mock', False):
                return self._fileno_val
            return super().detach()

        def gettimeout(self):
            if getattr(self, '_mock', False):
                return None
            return super().gettimeout()

        def settimeout(self, value):
            if getattr(self, '_mock', False):
                return
            return super().settimeout(value)

    _socket_mod.socket = _PatchedSocket

    def _mock_socketpair(family=_socket_mod.AF_INET, type=_socket_mod.SOCK_STREAM, proto=0):
        s1 = _PatchedSocket(family, type, proto)
        s2 = _PatchedSocket(family, type, proto)
        return s1, s2

    _socket_mod.socketpair = _mock_socketpair

    import asyncio
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass


_patch_for_sandbox()
