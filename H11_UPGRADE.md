# h11 安全升级记录

## 原因与修复

原来的 `httpx ^0.23.0` 和 PicImageSearch 3.9.0 将 httpcore/h11 限制在旧版本，
导致 Dependabot 无法自动升级到修复版本 h11 0.16.0。
上游公告：[GHSA-vqfr-h8mv-ghfj](https://github.com/python-hyper/h11/security/advisories/GHSA-vqfr-h8mv-ghfj)。

三个依赖入口（`pyproject.toml`、`requirements.txt`、`setup.py`）同步采用：

- `httpx>=0.28.1,<0.29`
- `PicImageSearch>=3.12.11,<4`
- `h11>=0.16.0,<1`：显式安全下限，防止安装入口重新允许旧版。
- `lxml>=5.4.0,<6`：满足新版 PicImageSearch 的依赖约束。
- 保留上一轮修复的 `Pillow>=13.0.0`，项目版本仍为 0.4.4。

Poetry 实际重新解析的版本为：

| 依赖 | 原锁定版本 | 新锁定版本 |
| --- | --- | --- |
| h11 | 0.14.0 | 0.16.0 |
| httpcore | 0.16.3 | 1.0.9 |
| httpx | 0.23.3 | 0.28.1 |
| PicImageSearch | 3.9.0 | 3.12.11 |
| lxml | 4.9.4 | 5.4.0 |
| Pillow | 13.0.0 | 13.0.0 |

## API 兼容

- 独立运行示例的 `httpx.AsyncClient(proxies=...)` 改为 `proxy=...`。
- 插件入口原有 `proxy=` 参数现在与 HTTPX 版本要求一致。
- Google 请求改用客户端 Cookie jar，避免已弃用的请求级 `cookies=` 参数。
- PicImageSearch 自身的 `Network(proxies=...)` 仍是有效的公开 API，保留不改；
  检查上游发行包确认其内部转交给 HTTPX 的 `proxy=`。

## 验证

- Python 3.11.16：`python -W error::DeprecationWarning -m pytest -q`，**43 passed**。
- 新建 Python 3.13.14 环境，从 `poetry.lock` 完整安装后运行同样测试，**43 passed**。
- 两个测试环境 `pip check` 均无依赖冲突。
- 锁文件一致性检查 `poetry check --lock` 通过，仅有原有 Poetry 元数据格式弃用提示。
- `pip install --dry-run -r requirements.txt` 解析成功。
- NoneBot HTTPX driver 初始化和插件加载成功。
- wheel 和 sdist 构建成功，`git diff --check` 通过。

新增 11 项 HTTP 回归测试：依赖入口与锁文件安全下限、合法分块解码、三类非法分块终止符拒绝、
有/无代理构造、真实 SauceNAO/Ascii2D 解析器与插件结果构建、Google Cookie 请求兼容。
搜索响应和图片下载由 MockTransport 提供，不访问真实搜索服务、不使用真实密钥或 Cookie。

## 备份与发布边界

修改前基线：`c44bf7a`。
修改前源码快照：`C:\Users\rby20\Desktop\nonebot_plugin_imgexploration-pillow13-20261027-095719-backup\before-h11-fix.zip`。
如需比较或回滚，优先将备份解压到新目录；回滚会重新引入不安全的依赖约束，不建议部署。

按用户授权提交并推送至 `codex/pillow-13-compat`，不合并默认分支、不发布版本。
默认分支上的 Dependabot 告警需要合入修复后重新评估，推送修复分支本身不代表告警已关闭。
