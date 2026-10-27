# Pillow 13 升级记录

## 范围

- 处理用户提供的 Dependabot #24：ImagingJpegDecode 堆缓冲区溢出，受影响版本 <=12.3.0，修复版本 13.0.0。
- 基线提交：`23a6bba5f747092ea3bea7fb391b8f64bf281913`。
- 修复分支：`codex/pillow-13-compat`；提交与推送按用户授权执行，不发布，项目版本保持 0.4.4。
- 告警私有页面直接访问返回 404，告警细节来自用户提供的内容；未声称 GitHub 告警已关闭。

## 修改

1. 将 `pyproject.toml`、`requirements.txt`、`setup.py` 的 Pillow 下限统一为 `>=13.0.0`。
2. 由 Poetry 2.5.1 实际解析生成 `poetry.lock`（格式 2.1），锁定 Pillow 13.0.0 及发行文件 SHA256，供可复现安装和 Dependabot 分析。
3. Pillow 13 不再支持 Python 3.10：Poetry 和 setuptools 元数据同步要求 Python >=3.11,<4，移除 Python 3.10 分类并更新安装说明。
4. 原图和缩略图缩放明确使用 `Image.Resampling.LANCZOS`，同时避免极窄/极高图片的缩放尺寸被取整为 0。
5. PNG 保存不再传入只对 JPEG 等有意义的 `quality` 参数；保留 RGB 转换、字体 `getlength()`、文本锚点、裁剪、粘贴和高斯模糊等仍受支持的 API。

本项目没有使用本次移除的 `Image._show`、`get_child_images()` 等接口，不进行无必要的接口替换。
升级 Pillow 本身才是原生解码器安全修复；更换缩放参数或限制 `formats=["JPEG"]` 不能替代它。

官方变更说明：<https://pillow.readthedocs.io/en/stable/releasenotes/13.0.0.html>。

## 验证

实际环境：Windows x64、Python 3.11.16、Pillow 13.0.0。

- 使用全新 `.venv-locked311`，从 `poetry.lock` 执行 `poetry install` 成功。
- `.venv-locked311\Scripts\python.exe -W error::DeprecationWarning -m pytest -q`：**32 passed**。
- `.venv-locked311\Scripts\python.exe -m pip check`：**No broken requirements found**。
- 使用 NoneBot 的 HTTPX driver 初始化并加载插件成功；默认 FastAPI driver 需由宿主机器人另外安装其可选依赖。
- `.venv311\Scripts\python.exe -m poetry check --lock` 成功；仅有原有 `[tool.poetry]` 元数据格式弃用提示。
- `.venv311\Scripts\python.exe -m build --no-isolation`：wheel 和 sdist 构建成功。
- `git diff --check` 通过。

测试覆盖三个依赖入口、锁文件的安全版本、JPEG/RGB、PNG/RGBA/调色板/灰度、原图缩放、极窄图、长文本、无效或缺失缩略图、四个搜索来源、空结果和多结果绘制。
字体测试使用 Pillow 内置 FreeType 字体；生产环境仍要求原 README 中的 HarmonyOS 字体。
没有联网执行外部搜图服务，也没有构造或运行堆溢出利用样本。

## 已有的非 Pillow 问题（本次未扩大修改）

仓库原本三个依赖入口的其他约束不一致。Poetry 原有 `httpx = "^0.23.0"` 会锁定 HTTPX 0.23.3、PicImageSearch 3.9.0，
但插件入口已有 `httpx.AsyncClient(proxy=...)`，与该旧版 HTTPX 的构造参数不一致。
本次图片绘制和插件导入验证通过，不等于外部搜图全链路已验证；如需修复该历史问题，应另行统一 HTTPX/PicImageSearch 约束和代理 API，并进行联网集成测试。
旧的 lxml 4.x 在 Python 3.13 上也可能缺少可用 wheel；本次完整验证使用 Python 3.11。

## 备份与回滚

修改前的原始仓库快照（不含 Git 历史）：
`C:\Users\rby20\Desktop\nonebot_plugin_imgexploration-pillow13-20261027-095719-backup\original.zip`。

建议将此备份解压到另一个新目录比较或恢复，保留当前修复目录以免覆盖后续工作。
原始内容也可从上面的基线提交恢复。回滚会重新允许有漏洞的 Pillow，不建议部署旧版本。

GitHub 告警需要将修复（包含 `poetry.lock`）合入默认分支后由 Dependabot 重新评估；推送修复分支不代表告警已关闭。
