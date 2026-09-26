"""Checks the safety net in conftest.py itself: tests must never reach the internet.

An earlier version only patched socket.socket.connect, and an unmocked Jev
call still reached api.typesafe.ai because async clients resolve the host
with getaddrinfo and connect via asyncio (ConnectEx on Windows).
"""

import asyncio
import socket

import httpx2
import pytest
from fastapi import HTTPException

from app.rubric import DEFAULT_MODE
from app.services import jev_scorer
from tests.conftest import NetworkAccessBlocked


def caused_by_block(exc: BaseException | None) -> bool:
    if exc is None:
        return False
    if isinstance(exc, NetworkAccessBlocked):
        return True
    if isinstance(exc, BaseExceptionGroup) and any(caused_by_block(e) for e in exc.exceptions):
        return True
    return caused_by_block(exc.__cause__ or exc.__context__)


def test_blocking_connect_is_blocked():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        with pytest.raises(NetworkAccessBlocked):
            s.connect(("93.184.215.14", 443))


def test_hostname_resolution_is_blocked():
    with pytest.raises(NetworkAccessBlocked):
        socket.getaddrinfo("api.typesafe.ai", 443)


@pytest.mark.parametrize("url", ["https://api.typesafe.ai/", "https://1.1.1.1/"])
def test_async_http_client_is_blocked(url):
    async def fetch():
        async with httpx2.AsyncClient() as client:
            await client.get(url)

    with pytest.raises(Exception) as excinfo:
        asyncio.run(fetch())
    assert caused_by_block(excinfo.value)


def test_unmocked_jev_call_never_leaves_the_machine():
    # Without the fake client this must fail as a connection error, not an
    # authentication error (which would mean the request reached TypeSafe).
    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(jev_scorer.score_with_jev("text", DEFAULT_MODE))

    assert excinfo.value.status_code == 502
    assert "接続に失敗" in excinfo.value.detail
    assert caused_by_block(excinfo.value)


def test_real_api_keys_are_replaced_with_dummies():
    from app.config import get_settings

    settings = get_settings()
    assert settings.anthropic_api_key == "test-anthropic-key"
    assert settings.openai_api_key == "test-openai-key"
    assert settings.typesafe_api_key == "test-typesafe-key"
