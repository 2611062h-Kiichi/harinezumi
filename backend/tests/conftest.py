"""Shared test setup: no real network access and no real API keys.

Every test runs with dummy API keys (so the developer's real keys in the OS
environment or backend/.env are never used) and with outbound connections
blocked, so a missing mock fails loudly instead of calling a paid API.
"""

import asyncio.base_events
import asyncio.proactor_events
import socket

import pytest

from app.config import get_settings

DUMMY_KEYS = {
    "ANTHROPIC_API_KEY": "test-anthropic-key",
    "OPENAI_API_KEY": "test-openai-key",
    "TYPESAFE_API_KEY": "test-typesafe-key",
}

LOCAL_HOSTS = {"127.0.0.1", "::1", "localhost"}


class NetworkAccessBlocked(ConnectionError):
    """A ConnectionError so client libraries treat it like being offline."""


def _refuse_unless_local(address) -> None:
    host = address[0] if isinstance(address, tuple) else address
    if isinstance(host, bytes):
        host = host.decode()
    if host not in LOCAL_HOSTS:
        raise NetworkAccessBlocked(f"テスト中の外部通信は禁止されています: {address!r}")


@pytest.fixture(autouse=True)
def block_network(monkeypatch):
    # Guard every path out: name resolution (async HTTP clients resolve first),
    # blocking connect, and asyncio's sock_connect, which on Windows uses
    # ConnectEx and never calls socket.connect. asyncio on Windows also opens a
    # localhost socketpair internally, so local destinations stay allowed.
    real_getaddrinfo = socket.getaddrinfo
    real_connect = socket.socket.connect

    def guarded_getaddrinfo(host, *args, **kwargs):
        _refuse_unless_local((host,))
        return real_getaddrinfo(host, *args, **kwargs)

    def guarded_connect(self, address):
        _refuse_unless_local(address)
        return real_connect(self, address)

    monkeypatch.setattr(socket, "getaddrinfo", guarded_getaddrinfo)
    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    for loop_cls in (asyncio.base_events.BaseEventLoop, asyncio.proactor_events.BaseProactorEventLoop):
        real_sock_connect = loop_cls.sock_connect

        async def guarded_sock_connect(self, sock, address, _real=real_sock_connect):
            _refuse_unless_local(address)
            return await _real(self, sock, address)

        monkeypatch.setattr(loop_cls, "sock_connect", guarded_sock_connect)


@pytest.fixture(autouse=True)
def dummy_settings(monkeypatch):
    for name, value in DUMMY_KEYS.items():
        monkeypatch.setenv(name, value)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
