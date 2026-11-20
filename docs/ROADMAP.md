# 路线图 / Roadmap

## 中文说明

| 阶段 | 工作与完成条件 | 状态 |
|---|---|---|
| M0 方案审阅 | 候选组件、架构、约束和验收矩阵已整理；确认组件与机型约束 | 待确认 |
| M1 局域网文件服务 | SshDaemon 真机读写、RSAF 选择器浏览与读写、视频跳转和按需下载 | 待真机验证 |
| M2 分层与恢复 | 指定热目录同步、相机单向接收、独立备份与误删恢复 | 待验证 |
| M3 异地私有访问 | 移动网络连通、Clash 共存或替代配置、权限复核及无公网映射 | 待验证 |
| M4 无人值守 | 连续 72 小时、重启、掉线、存储写满演练；记录性能、温控、能耗和恢复情况 | 待验证 |
| M5 可选适配 | 出现实际编排需求时再设计 Personal OS 薄接口，复用现有文件、同步及 VPN 服务 | 按需启动 |

## English

## M0 — Review and selection (current)
- [x] Initial set of existing component candidates documented.
- [x] Proposed architecture, constraints and test matrix drafted.
- [ ] User approves chosen components and device-specific constraints.

## M1 — Local file service proof
- [ ] SshDaemon SFTP read/write on LAN.
- [ ] RSAF document picker browse/read/write tests on primary phone.
- [ ] Video seeks and remote download behavior verified.

## M2 — Data tiering and safety
- [ ] Syncthing-Fork selected hot folders.
- [ ] Camera ingest without destructive mirroring.
- [ ] Independent recovery copy and deleted-file restore test.

## M3 — Secure remote access
- [ ] Private reachability from mobile network.
- [ ] Clash VPN conflict resolved or workaround documented.
- [ ] Access-control review and no public open port.

## M4 — Reliability / user acceptance
- [ ] 72-hour unattended power and background test.
- [ ] Reboot, network drop and storage-full drills.
- [ ] Performance, energy/thermal and recovery results recorded.

## M5 — Optional Personal OS adapter
- [ ] Only design a thin interface if real workflows require orchestration.
- [ ] No duplicate server, synchronization, browsing or VPN implementation.
