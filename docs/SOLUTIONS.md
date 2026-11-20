# 现有组件评估 / Reuse-first solution evaluation

## 中文说明

以下均为候选方案。安装前检查发布版本、维护情况、许可证及系统支持。

| 组件 | 用途与优势 | 重点验证 |
|---|---|---|
| SshDaemon | 原生 SSH/SFTP，配置较少 | 后台存活、共享存储权限、安全设置 |
| Primitive FTPd | 带 Android 界面的 FTP/SFTP 备选服务 | 启动行为、目标系统上的 SFTP 性能 |
| Termux + OpenSSH | 可用脚本配置及扩展 | 后台退出、存储授权、维护成本 |
| RSAF | 基于 rclone 的 SAF 文档提供器 | 各应用读写、随机访问与缓存 |
| Syncthing-Fork | 去中心化同步，保留离线副本 | 删除传播、空间、电量和后台生命周期 |
| Tailscale | 私有加密访问，通常无需端口映射 | Clash 共存及中继性能 |
| copyparty | 浏览器文件管理和传输 | Termux 部署、认证、对外暴露范围 |
| OpenList | 统一访问多个存储后端 | 移动版成熟度与后端支持 |
| Homedroid | 一体化手机服务器，可能简化配置 | 测试版成熟度、来源、运行与安全性 |
| NOVA Video Player | 网络媒体播放 | 目标机型和文件格式上的 SFTP 播放与跳转 |

依次验证局域网 SFTP、RSAF 文件选择与随机读取、指定目录同步与误删恢复、异地 VPN 与 Clash 冲突。按需单独试用可选服务。选型优先看运行稳定性，再看暴露面和维护方可信度、数据正确性与恢复、客户端兼容性、维护成本及未来接入 Personal OS 的便利性。

## English

Status is **research**, not practical validation. Before installation, independently check releases, maintainers, licensing and platform support.

| Component | Role | Strength | Key question / limitation |
|---|---|---|---|
| SshDaemon | Native Android SSH/SFTP server | Small service surface, minimal setup | Background longevity, SAF/shared-storage permissions, security settings |
| Primitive FTPd | Native FTP/SFTP service | Alternative with Android UI | Startup behavior, SFTP and performance on target OS |
| Termux + OpenSSH | Scriptable SSH/SFTP server | Flexible and extensible | Doze/OEM kills, storage permission, maintenance burden |
| RSAF | SAF document provider backed by rclone | Can open remote files in SAF-compatible apps | App-specific compatibility, random access, write semantics, cache |
| Syncthing-Fork | Hot-file syncing | Decentralized syncing and offline copies | Delete propagation, storage/battery use, platform lifecycle |
| Tailscale | Encrypted private reachability | No router port forwarding in normal design | VPN coexistence with Clash, relay performance |
| copyparty | Web file server | Web browser interface, advanced transfers | Complexity, Termux runtime, auth and exposure hardening |
| OpenList | Consolidated web file frontend | Multi-backend access | Mobile edition maturity and provider details |
| Homedroid | All-in-one Android server | Potential rapid setup | Beta maturity, app provenance, operations/security validation |
| NOVA Video Player | Network media client | Network-streaming media usage | Actual SFTP playback/seek on phone and file types |

## Evaluation order
1. SshDaemon + local SFTP test.
2. RSAF + SFTP on LAN (SAF and random-seek tests).
3. Syncthing-Fork restricted-directory transfer and deletion recovery.
4. Tailscale remote network / Clash conflict.
5. Only if needed: OpenList, copyparty or Homedroid. Do not install all servers at once.

## Decision criteria
- Operational stability (most important)
- Minimal attack surface and trusted maintenance
- Data correctness and recovery
- SAF client compatibility
- Setup and ongoing maintenance cost
- Optional Personal OS extensibility
