# Personal OS 可选适配接口 / Optional Personal OS adapter — boundary contract

## 中文说明

Personal OS 可通过独立适配器使用已有协议。本仓库可单独部署。

| 能力 | 实现与授权边界 |
|---|---|
| `storage.list`、`storage.stat`、`storage.read` | 复用 SFTP/WebDAV 客户端库 |
| `storage.write` | 限定授权路径，自动化场景默认关闭写入 |
| `device.health` | 确有需求时在服务端部署状态采集器；SFTP 本身不提供设备健康数据 |
| `sync.status` | 在版本支持且已授权时使用 Syncthing API |

对远程 AI 代理仅开放白名单路径和必要权限，避免暴露文件系统根目录。敏感日志与凭据保存在仓库外。业务逻辑与具体 Android 服务端解耦，优先使用 CLI 或常规服务 API。自动删除、归档和传输须有明确策略和恢复机制。

## English

This repository operates independently of Personal OS. Any integration should use a separate adapter consuming established protocols.

## Suggested read capabilities
- `storage.list` / `storage.stat` / `storage.read`: SFTP/WebDAV via existing client library.
- `storage.write`: controlled path and authorization; default off for automation.
- `device.health`: explicit status collector on server if justified, never assumed available from SFTP.
- `sync.status`: use Syncthing's supported existing API if available and authorized.

## Rules
- Do not expose filesystem roots directly to remote AI agents.
- Whitelist paths and permission scopes; keep sensitive logs/credentials outside source control.
- Do not couple app business logic to a particular Android server implementation.
- Prefer a CLI or conventional service API over a custom persistent agent where it adds no value.
- No autonomous deletion, archival or transfer without deliberate policy and recovery capability.
