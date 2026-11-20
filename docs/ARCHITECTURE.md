# 架构与威胁模型 / Architecture and threat model

## 中文说明

| 数据 | 存放与流向 |
|---|---|
| 冷数据 | 原始文件、视频和归档保存在家庭节点，按需读取 |
| 热数据 | 白名单内的小目录同步至主力机，可离线使用 |
| 相机文件 | 主力机发送副本，家庭节点接收并独立留存快照或归档 |
| 恢复副本 | 单独保存，避免双向同步传播误删后失去恢复来源 |

条件允许时将 SFTP 限于可信局域网或私有 tailnet，默认关闭公网映射。服务端支持时使用专用账户和 SSH 密钥，关闭多余服务。记录开放端口、凭据轮换周期和应用版本，凭据值保存在仓库外。

| 故障 | 检查或恢复措施 |
|---|---|
| 息屏或 Doze 导致服务退出 | 检测中断、恢复并测量恢复耗时 |
| 家庭 Wi-Fi 掉线 | 验证重连和文件完整性 |
| 重启或断电 | 检查恢复服务是否需要人工解锁或启动 |
| VPN 冲突 | 验证系统支持的配置，不预设两个 Android VPN 可同时工作 |
| 同步传播误删 | 从保留版本、快照或独立备份恢复 |
| 充电异常 | 使用支持的充电限制并保持通风，异常发热或鼓包时停止运行 |

本项目负责设备部署和标准协议服务。Personal OS 可作为客户端或编排端接入，详见[适配接口](PERSONAL_OS_ADAPTER.md)。

## English

## Data roles
- **Cold data:** server-only video, archive, original files.
- **Hot data:** small whitelisted folders synced to primary device.
- **Camera ingest:** primary sends copies; server receives and snapshots/archives independently.
- **Recovery copy:** separately stored backup, not merely a two-way Syncthing mirror.

## Paths and isolation
- SFTP service listens only on trusted LAN/private tailnet when feasible.
- No public router port forwarding by default.
- Use unique service account and SSH keys when supported; disable unnecessary services.
- Maintain an inventory of exposed ports, credentials lifecycle and app versions (no secrets committed).

## Failure states
- Screen-off and Doze kill server: detect/recover and measure recovery time.
- Home Wi-Fi drop: reconnect; no silent file corruption.
- Phone reboot/power loss: check whether service resumes without manual action.
- VPN client conflicts: use a supported VPN configuration, never assume two Android VPN services coexist.
- Accidental delete propagated by sync: retention/snapshot or separate backup prevents permanent loss.
- Charger/battery thermal issue: prioritize safe charge limits and ventilation; stop at abnormal heat/swelling.

## Personal OS boundary
Current project owns device-level deployment and existing protocols. Personal OS remains an optional client/orchestrator, not an implementation dependency. See PERSONAL_OS_ADAPTER.md.
