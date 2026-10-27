"""Offline checks for the upgraded HTTP dependency chain and search integrations."""

import ast
import asyncio
import tomllib
from importlib.metadata import version
from types import SimpleNamespace

import h11
import httpx
import pytest
from packaging.requirements import Requirement
from packaging.version import Version

from test_pillow_compat import ROOT, image_bytes, module, search


def test_http_dependency_security_floor():
    assert Version(version("h11")) >= Version("0.16.0")
    assert Version(version("httpcore")) >= Version("1.0.9")
    assert Version(version("httpx")) >= Version("0.28.1")
    lock = tomllib.loads((ROOT / "poetry.lock").read_text(encoding="utf-8"))
    locked = {package["name"].lower(): package["version"] for package in lock["package"]}
    for name, floor in {"h11": "0.16.0", "httpcore": "1.0.9", "httpx": "0.28.1",
                        "picimagesearch": "3.12.11"}.items():
        assert Version(locked[name]) >= Version(floor)


def test_all_install_paths_enforce_safe_http_dependencies():
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    poetry = {name.lower(): Requirement(name + constraint).specifier
              for name, constraint in config["tool"]["poetry"]["dependencies"].items()
              if name.lower() in {"h11", "httpx", "picimagesearch", "lxml"}}
    requirements = {Requirement(line).name.lower(): Requirement(line).specifier
                    for line in (ROOT / "requirements.txt").read_text().splitlines() if line.strip()}
    tree = ast.parse((ROOT / "setup.py").read_text(encoding="utf-8"))
    node = next(node for node in ast.walk(tree) if isinstance(node, ast.keyword)
                and node.arg == "install_requires")
    setup = {Requirement(req).name.lower(): Requirement(req).specifier
             for req in ast.literal_eval(node.value)}
    for manifest in (poetry, requirements, setup):
        for name, bad, safe in [("h11", "0.14.0", "0.16.0"),
                                ("httpx", "0.23.3", "0.28.1"),
                                ("picimagesearch", "3.9.0", "3.12.11"),
                                ("lxml", "4.9.4", "5.4.0")]:
            assert bad not in manifest[name]
            assert safe in manifest[name]


@pytest.mark.parametrize("terminator", [b"XX", b"\n\n", b"\rX"])
def test_h11_rejects_invalid_chunk_terminators(terminator):
    connection = h11.Connection(h11.SERVER)
    connection.receive_data(b"POST / HTTP/1.1\r\nHost: example.invalid\r\n"
                            b"Transfer-Encoding: chunked\r\n\r\n5\r\nhello" + terminator + b"0\r\n\r\n")
    with pytest.raises(h11.RemoteProtocolError):
        for _ in range(10):
            connection.next_event()


def test_h11_accepts_valid_chunks():
    connection = h11.Connection(h11.SERVER)
    connection.receive_data(b"POST / HTTP/1.1\r\nHost: example.invalid\r\n"
                            b"Transfer-Encoding: chunked\r\n\r\n5\r\nhello\r\n0\r\n\r\n")
    assert isinstance(connection.next_event(), h11.Request)
    assert connection.next_event().data == b"hello"
    assert isinstance(connection.next_event(), h11.EndOfMessage)


@pytest.mark.parametrize("proxy", [None, "http://127.0.0.1:7890"])
def test_proxy_constructors(proxy, monkeypatch):
    for key in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY"):
        monkeypatch.delenv(key, raising=False)
        monkeypatch.delenv(key.lower(), raising=False)
    async def run():
        async with httpx.AsyncClient(proxy=proxy, trust_env=False):
            pass
        # PicImageSearch still exposes `proxies`, mapping it to HTTPX's `proxy`.
        async with module.Network(proxies=proxy, timeout=20) as client:
            assert isinstance(client, httpx.AsyncClient)
    asyncio.run(run())


@pytest.mark.parametrize("engine", ["saucenao", "ascii2d"])
def test_search_builders_with_real_parsers(search, monkeypatch, engine):
    calls = []
    picture = image_bytes()
    html = '<html><body><div class="row item-box"><img src="https://example.invalid/thumb.png"><div class="external"><a href="https://example.invalid/art">Test artwork</a></div></div></body></html>'

    def handler(request):
        calls.append(request)
        if request.url.host == "saucenao.com":
            return httpx.Response(200, json={"header": {"status": 0}, "results": [{
                "header": {"similarity": "99", "thumbnail": "https://example.invalid/thumb.png",
                           "index_id": 5, "index_name": "Test"},
                "data": {"title": "Test artwork", "ext_urls": ["https://example.invalid/art"]},
            }]})
        if request.url.host == "ascii2d.net":
            return httpx.Response(200, text=html)
        return httpx.Response(200, content=picture)

    def network(**kwargs):
        return httpx.AsyncClient(transport=httpx.MockTransport(handler))

    monkeypatch.setattr(module, "Network", network)
    search._Imgexploration__imgopsUrl = "https://example.invalid/input.png"

    async def run():
        async with network() as client:
            search.client = client
            method = getattr(search, f"_Imgexploration__{engine}_build_result")
            return await method()

    results = asyncio.run(run())
    assert results
    assert results[0]["url"] == "https://example.invalid/art"
    assert results[0]["thumbnail_bytes"] == picture
    assert results[0]["source"] == engine
    if engine == "ascii2d":
        assert sum(request.url.host == "ascii2d.net" for request in calls) == 3


def test_google_uses_client_cookies_without_deprecated_request_api(search):
    requests = []

    def handler(request):
        requests.append(request)
        if request.url.path == "/uploadbyurl":
            return httpx.Response(302, headers={"location": "https://lens.google.com/results"})
        return httpx.Response(200, text="<html><body>No exact matches</body></html>")

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            search.client = client
            search._Imgexploration__imgopsUrl = "https://example.invalid/input.png"
            search._Imgexploration__google_cookies = SimpleNamespace(
                cookies=httpx.Cookies({"test_session": "offline"}), update=lambda headers: None,
            )
            assert await search._Imgexploration__google_build_result() == []

    asyncio.run(run())
    assert len(requests) == 2
    assert all("test_session=offline" in request.headers["cookie"] for request in requests)
