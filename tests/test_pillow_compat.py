"""Offline regression tests for the plugin's real Pillow rendering paths."""

import asyncio
import ast
import importlib.util
import tomllib
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

import pytest
from packaging.requirements import Requirement
from PIL import Image, ImageFont, __version__ as pillow_version


ROOT = Path(__file__).resolve().parents[1]
# Avoid registering NoneBot matchers or requiring a running bot during image tests.
spec = importlib.util.spec_from_file_location(
    "imgexploration_under_test", ROOT / "nonebot_plugin_imgexploration/imgexploration.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def image_bytes(size=(320, 240), mode="RGB", format="PNG"):
    with BytesIO() as output:
        Image.new(mode, size).save(output, format=format)
        return output.getvalue()


@pytest.fixture
def search(monkeypatch):
    # Use Pillow's bundled FreeType font, not locally installed HarmonyOS fonts.
    # Keep setFront itself exercised, including its requested font sizes.
    fonts = {size: ImageFont.load_default(size=size) for size in (15, 20, 25)}
    monkeypatch.setattr(
        module.ImageFont, "truetype",
        lambda name, size: fonts[size],
    )
    return module.Imgexploration("https://example.invalid/image", None, None, "", None)


def test_pillow_security_floor():
    assert int(pillow_version.split(".")[0]) >= 13


def test_dependency_declarations_exclude_vulnerable_pillow():
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    requirements = ["Pillow" + config["tool"]["poetry"]["dependencies"]["pillow"]]
    requirements.extend(
        line for line in (ROOT / "requirements.txt").read_text().splitlines()
        if line.lower().startswith("pillow")
    )
    setup = ast.parse((ROOT / "setup.py").read_text(encoding="utf-8"))
    setup_call = next(node for node in ast.walk(setup)
                      if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                      and node.func.attr == "setup")
    install_requires = next(kw.value for kw in setup_call.keywords if kw.arg == "install_requires")
    requirements.extend(req for req in ast.literal_eval(install_requires)
                        if req.lower().startswith("pillow"))
    assert len(requirements) == 3
    for requirement in requirements:
        versions = Requirement(requirement).specifier
        assert "12.3.0" not in versions
        assert "13.0.0" in versions


def test_lockfile_excludes_vulnerable_pillow():
    lock = tomllib.loads((ROOT / "poetry.lock").read_text(encoding="utf-8"))
    pillow = next(package for package in lock["package"] if package["name"].lower() == "pillow")
    assert int(pillow["version"].split(".")[0]) >= 13
    assert pillow["files"]


@pytest.mark.parametrize(
    "size,mode,format",
    [((2400, 1200), "RGB", "JPEG"), ((1, 3000), "RGBA", "PNG"),
     ((3000, 1), "L", "PNG"), ((320, 240), "P", "PNG")],
)
def test_download_and_resize(search, size, mode, format):
    content = image_bytes(size, mode, format)

    async def get(**kwargs):
        return SimpleNamespace(content=content)

    search.client = SimpleNamespace(get=get)
    asyncio.run(search._Imgexploration__getImgbytes())
    result = search._Imgexploration__pic_bytes
    with Image.open(BytesIO(result)) as image:
        image.load()
        if max(size) > 2000:
            scale = max(size) // 1000
            assert image.size == tuple(max(1, int(n / scale)) for n in size)
            assert image.mode == "RGB"
            assert image.format == "JPEG"
        else:
            assert result == content


@pytest.mark.parametrize("source", ["saucenao", "ascii2d", "Google", "Yandex"])
@pytest.mark.parametrize("thumbnail", ["wide", "tall", "rgba", "palette", "invalid", "missing"])
def test_render_results(search, source, thumbnail):
    item = {
        "source": source, "title": "Long title " * 100,
        "description": "Long description " * 100, "similarity": 98.5,
        "domain": "example.invalid", "url": "https://example.invalid/" + "x" * 500,
    }
    thumbnails = {
        "wide": lambda: image_bytes((1000, 100)),
        "tall": lambda: image_bytes((1, 1000)),
        "rgba": lambda: image_bytes(mode="RGBA"),
        "palette": lambda: image_bytes(mode="P"),
        "invalid": lambda: b"not an image",
    }
    if thumbnail != "missing":
        item["thumbnail_bytes"] = thumbnails[thumbnail]()
    search._Imgexploration__result_info = [item, {**item, "title": "", "url": ""}]
    result = asyncio.run(search._Imgexploration__draw())
    with Image.open(BytesIO(result)) as image:
        image.load()
        assert image.format == "PNG"
        assert image.mode == "RGB"
        assert image.size == (900, 400)


def test_render_empty_results(search):
    search._Imgexploration__result_info = []
    with Image.open(BytesIO(asyncio.run(search._Imgexploration__draw()))) as image:
        image.load()
        assert image.size == (900, 10)
