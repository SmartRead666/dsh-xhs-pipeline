# dsh-xhs-pipeline

小红书多账号内容流水线插件包（Host 半边）。

- 注册 skill `xiaohongshu-pipeline`
- 注册工具 `xhs_render` / `xhs_publish` / `xhs_monitor`
- 提供面板：`http://127.0.0.1:<DSH端口>/xhs-pipeline/`

## 配置

`~/.dsh/xhs-pipeline.json`：

```json
{
  "home": "D:/xhs-workspace",
  "python": "C:/path/to/python.exe",
  "update": { "npm": "dsh-xhs-pipeline" }
}
```

`update` 支持四种写法：

| 写法 | 含义 |
|---|---|
| `{ "npm": "包名" }` | 从 npm registry 查 latest |
| `{ "url": "https://.../version.json" }` | 任意 HTTP 地址，返回 `{"version":"x.y.z","url":"更新说明"}` |
| `{ "file": "D:/.../version.json" }` | 本地 / 内网文件 |
| `{ "enabled": false }` | 关闭检查 |

检查结果缓存 12 小时，失败不打扰（静默）。

## 更新

插件**不会自动升级**。面板顶部会提示「有新版本」，升级执行：

```
plugin_manager remove_bundle dsh-xhs-pipeline
plugin_manager install_bundle file:<解压后的新版本目录>
```

升级前建议先确认 `package.json` 的 `engines.dsh` 覆盖你当前的 DSH 版本。
