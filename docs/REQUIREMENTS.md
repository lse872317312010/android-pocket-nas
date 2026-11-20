# 需求与约束 / Requirements and constraints

## 中文说明

| 设备 | 用途与约束 |
|---|---|
| 家庭节点 | 骁龙 7+ Gen 系列，1 TB 内部存储，常驻家中 |
| 主力手机 | 骁龙 8 Elite 级别，256 GB 存储，日常携带 |

确切机型和系统版本待确认，默认按两机均无 Root 设计。

**功能需求**：主力机可浏览远程目录、按需打开兼容文件、流式播放长视频并跳转位置。指定目录双向同步，相机文件单向上传到接收和归档端。局域网和移动网络均应支持私密访问。家庭节点应能在息屏和网络变化后持续服务。

**运行约束**：尽量减少新增代码和月度费用。优先保证数据完整、可恢复和电池健康。为主力机缓存设定上限，确保离线文件可用；唯一的照片备份不能承担镜像删除风险。

**待调查**：Tailscale 与 Clash 对 Android VPN 的占用、厂商后台管理、前台服务、重启恢复、分区存储、SAF 兼容性以及长期充电温控。异地性能取决于家庭上行、移动网络下行、延迟和中继路径。

按[验收清单](../checklists/ACCEPTANCE.md)记录机型、系统构建号、应用版本、步骤、时间、网络条件、结果和脱敏日志或截图。

## English

## Hardware
- **Home node:** Snapdragon 7+ Gen-series Android phone, 1 TB internal storage; exact model/OS to confirm.
- **Primary:** Snapdragon 8 Elite-class Android phone, 256 GB storage; exact model/OS to confirm.
- Both devices assumed non-rooted until confirmed otherwise.

## Functional requirements
- Browsing remote directories, opening compatible files on demand from the primary phone.
- Streaming long videos without full pre-download, with seeking.
- Bi-directional sync for explicitly selected folders and one-way camera upload to a receiving/archiving destination.
- Secure LAN and mobile-data access with no unsolicited public exposure.
- Unattended home-node operations after screen off and connectivity changes.

## Nonfunctional requirements
- Minimal new code and minimal monthly cost.
- Prioritize security, battery health, recovery and data integrity over features.
- No accidental destructive mirror sync of the sole photo backup.
- Clear cache size limits on primary phone; offline hot files remain usable.

## Acceptance evidence
See ../checklists/ACCEPTANCE.md. Record phone model, OS build, app versions, setup steps, test timestamps, actual outcomes, screenshots/logs and connectivity conditions.

## Constraints to investigate
- Android single-VPN limitation (Tailscale vs Clash VPN mode).
- OEM power management, foreground service availability and reboot behavior.
- Android scoped-storage and SAF application compatibility.
- Android background server behavior; thermal and charge management.
- WAN throughput limited by home uplink, mobile downlink, latency and possible relay routing.
